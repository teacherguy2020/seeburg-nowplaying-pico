"""Seeburg 3W-1 pulse recorder/decoder for Raspberry Pi Pico 2 W.

Commissioning modes:
  RECORD  Capture and print raw timing only.
  DRY_RUN Decode and call Now Playing with dryRun=true.
  LIVE    Decode and append the selected track to the MPD queue.

The pulse interrupt intentionally does no printing, decoding, or networking.
"""

from machine import Pin
import time


# -----------------------------------------------------------------------------
# CONFIGURATION
# -----------------------------------------------------------------------------

MODE = "RECORD"  # RECORD, DRY_RUN, LIVE

SIGNAL_PIN = 15  # PC817 output -> GP15; expected active edge is falling

API_URL = "http://10.0.0.4:3101/integrations/seeburg/selection"

# These are provisional until traces from the real Wallbox are measured.
MIN_PULSE_GAP_MS = 10
GROUP_SPLIT_MS = 100
SELECTION_COMPLETE_MS = 350
EXPECTED_PULSE_MIN_MS = 20
EXPECTED_PULSE_MAX_MS = 80
EXPECTED_GROUP_GAP_MIN_MS = 100
EXPECTED_GROUP_GAP_MAX_MS = 300

MAX_TIMESTAMPS = 64
HTTP_TIMEOUT_S = 8
HTTP_RETRIES = 1
DUPLICATE_SUPPRESSION_MS = 2000


# -----------------------------------------------------------------------------
# CAPTURE STATE
# -----------------------------------------------------------------------------

edge_times = [0] * MAX_TIMESTAMPS
edge_states = [0] * MAX_TIMESTAMPS
edge_count = 0
pulse_times = [0] * MAX_TIMESTAMPS
pulse_count = 0
last_irq_ms = 0
capture_active = False
capture_overflow = False

last_submitted_number = None
last_submitted_ms = 0


# -----------------------------------------------------------------------------
# GPIO INTERRUPT
# -----------------------------------------------------------------------------

def pulse_irq(pin):
    """Record one GPIO edge; keep this handler short and allocation-free."""

    global edge_count, pulse_count, last_irq_ms, capture_active
    global capture_overflow

    now = time.ticks_ms()

    # RECORD is intentionally unfiltered so the raw PC817 waveform is visible.
    if MODE != "RECORD" and pulse_count > 0:
        delta = time.ticks_diff(now, last_irq_ms)
        if delta < MIN_PULSE_GAP_MS:
            return

    last_irq_ms = now
    capture_active = True

    if MODE == "RECORD":
        if edge_count < MAX_TIMESTAMPS:
            edge_times[edge_count] = now
            edge_states[edge_count] = pin.value()
            edge_count += 1
        else:
            capture_overflow = True
    else:
        if pulse_count < MAX_TIMESTAMPS:
            pulse_times[pulse_count] = now
            pulse_count += 1
        else:
            capture_overflow = True


def arm_signal(signal):
    if MODE == "RECORD":
        signal.irq(
            trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING,
            handler=pulse_irq,
        )
    else:
        signal.irq(trigger=Pin.IRQ_FALLING, handler=pulse_irq)


# -----------------------------------------------------------------------------
# CAPTURE PROCESSING
# -----------------------------------------------------------------------------

def get_intervals(times):
    return [time.ticks_diff(times[i], times[i - 1])
            for i in range(1, len(times))]


def split_groups(times):
    """Split at the first large gap; return None if no split exists."""

    if len(times) < 3:
        return None

    for index, gap in enumerate(get_intervals(times)):
        if gap >= GROUP_SPLIT_MS:
            return times[:index + 1], times[index + 1:]

    return None


def validate_timing(times, group1, group2):
    """Reject traces that are structurally or temporally implausible."""

    if len(times) > MAX_TIMESTAMPS:
        return "capture buffer overflow"

    if not 2 <= len(group1) <= 21:
        return "group 1 pulse count must be 2..21"

    if not 1 <= len(group2) <= 5:
        return "group 2 pulse count must be 1..5"

    group_gap = time.ticks_diff(group2[0], group1[-1])
    if not EXPECTED_GROUP_GAP_MIN_MS <= group_gap <= EXPECTED_GROUP_GAP_MAX_MS:
        return "group gap is outside provisional timing range"

    # Exclude the inter-group gap from intra-group timing checks.
    for gap in get_intervals(group1) + get_intervals(group2):
        if not EXPECTED_PULSE_MIN_MS <= gap <= EXPECTED_PULSE_MAX_MS:
            return "intra-group pulse spacing is outside provisional range"

    return None


# -----------------------------------------------------------------------------
# WALLBOX DECODER (PROVISIONAL)
# -----------------------------------------------------------------------------

LETTER_PAIRS = {
    1: ("A", "B"),
    2: ("C", "D"),
    3: ("E", "F"),
    4: ("G", "H"),
    5: ("J", "K"),
}

LETTERS = ["A", "B", "C", "D", "E", "F", "G", "H", "J", "K"]


def decode_selection(group1_count, group2_count):
    if group2_count not in LETTER_PAIRS:
        return None

    first_letter, second_letter = LETTER_PAIRS[group2_count]

    if 2 <= group1_count <= 11:
        letter = first_letter
        number = group1_count - 1
    elif 12 <= group1_count <= 21:
        letter = second_letter
        number = group1_count - 11
    else:
        return None

    playlist_number = LETTERS.index(letter) * 10 + number
    return {
        "letter": letter,
        "button_number": number,
        "wallbox_code": "{}{}".format(letter, number),
        "playlist_number": playlist_number,
    }


# -----------------------------------------------------------------------------
# NOW PLAYING HTTP CLIENT
# -----------------------------------------------------------------------------

def connect_wifi():
    import network
    from secrets import WIFI_SSID, WIFI_PASSWORD

    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    if wlan.isconnected():
        return wlan

    print("Connecting to Wi-Fi...")
    wlan.connect(WIFI_SSID, WIFI_PASSWORD)

    remaining = 20
    while not wlan.isconnected() and remaining:
        time.sleep(1)
        remaining -= 1

    if wlan.isconnected():
        print("Wi-Fi connected:", wlan.ifconfig()[0])
    else:
        print("Wi-Fi connection failed")

    return wlan


def send_to_now_playing(wlan, number, dry_run):
    """POST one selection; return True only for a successful API response."""

    import socket
    import ujson
    import urequests
    from secrets import TRACK_KEY

    global last_submitted_number, last_submitted_ms

    if not wlan.isconnected():
        wlan = connect_wifi()
    if not wlan.isconnected():
        print("API ERROR: Wi-Fi is unavailable")
        return False

    now = time.ticks_ms()
    if (last_submitted_number == number and
            time.ticks_diff(now, last_submitted_ms) < DUPLICATE_SUPPRESSION_MS):
        print("Duplicate suppressed for playlist #{}".format(number))
        return False

    payload = {"number": number}
    if dry_run:
        payload["dryRun"] = True

    headers = {
        "Content-Type": "application/json",
        "X-Track-Key": TRACK_KEY,
    }

    set_default_timeout = getattr(socket, "setdefaulttimeout", None)
    if set_default_timeout is None:
        print("WARNING: this MicroPython build has no socket default timeout")

    for attempt in range(HTTP_RETRIES + 1):
        response = None
        try:
            # urequests has no portable per-request timeout. A socket default
            # protects the Pico from waiting indefinitely on a dead Pi.
            if set_default_timeout is not None:
                set_default_timeout(HTTP_TIMEOUT_S)
            response = urequests.post(
                API_URL,
                data=ujson.dumps(payload),
                headers=headers,
            )
            status = response.status_code
            print("HTTP:", status)
            try:
                print("API:", response.json())
            except Exception:
                print("API response:", response.text)

            if 200 <= status < 300:
                last_submitted_number = number
                last_submitted_ms = time.ticks_ms()
                return True

            print("API rejected selection")
        except Exception as error:
            print("API ERROR (attempt {}): {}".format(attempt + 1, error))
            if attempt < HTTP_RETRIES:
                wlan = connect_wifi()
        finally:
            if response is not None:
                response.close()
            if set_default_timeout is not None:
                try:
                    set_default_timeout(None)
                except Exception:
                    pass

    return False


# -----------------------------------------------------------------------------
# SELECTION PROCESSING
# -----------------------------------------------------------------------------

def print_raw_capture(times, overflow, states=None):
    print()
    print("================================")
    print("RAW SEEBURG CAPTURE")
    print("================================")
    print("Edges:" if states is not None else "Pulses:", len(times))
    print("Intervals ms:", get_intervals(times))
    if states is not None:
        print("Edges (time_ms, state):")
        for timestamp, state in zip(times, states):
            print("  {}, {}".format(timestamp, "HIGH" if state else "LOW"))
    if overflow:
        print("WARNING: capture buffer overflowed")


def process_capture(times, overflow, wlan, states=None):
    print_raw_capture(times, overflow, states)

    if MODE == "RECORD":
        print("MODE: RECORD — both edges, raw timing/state only; no filtering/API")
        return

    if overflow:
        print("INVALID: capture buffer overflow")
        return

    groups = split_groups(times)
    if groups is None:
        print("INVALID: could not identify two pulse groups")
        return

    group1, group2 = groups
    timing_error = validate_timing(times, group1, group2)
    if timing_error:
        print("INVALID TIMING:", timing_error)
        return

    print("Group 1:", len(group1))
    print("Group 2:", len(group2))
    print("Group gap:", time.ticks_diff(group2[0], group1[-1]), "ms")

    decoded = decode_selection(len(group1), len(group2))
    if decoded is None:
        print("INVALID WALLBOX CODE")
        return

    print("Decoded:", decoded["wallbox_code"])
    print("Playlist #:", decoded["playlist_number"])

    if MODE == "DRY_RUN":
        print("POSTING DRY RUN")
        send_to_now_playing(wlan, decoded["playlist_number"], True)
    elif MODE == "LIVE":
        print("POSTING LIVE")
        send_to_now_playing(wlan, decoded["playlist_number"], False)


# -----------------------------------------------------------------------------
# MAIN LOOP
# -----------------------------------------------------------------------------

if MODE not in ("RECORD", "DRY_RUN", "LIVE"):
    raise ValueError("MODE must be RECORD, DRY_RUN, or LIVE")

print("\nSeeburg 3W-1 Pico Decoder")
print("Mode:", MODE)

wlan = None
if MODE in ("DRY_RUN", "LIVE"):
    wlan = connect_wifi()

signal = Pin(SIGNAL_PIN, Pin.IN, Pin.PULL_UP)
arm_signal(signal)
print("Waiting for Wallbox selections...")

while True:
    active_count = edge_count if MODE == "RECORD" else pulse_count
    if capture_active and active_count:
        quiet_ms = time.ticks_diff(time.ticks_ms(), last_irq_ms)
        if quiet_ms >= SELECTION_COMPLETE_MS:
            # Copy and clear first, then re-arm before doing slow work. A new
            # selection can therefore be captured while this one is printed
            # or sent over Wi-Fi.
            signal.irq(handler=None)
            count = edge_count if MODE == "RECORD" else pulse_count
            captured = (edge_times[:count] if MODE == "RECORD"
                        else pulse_times[:count])
            states = (edge_states[:count] if MODE == "RECORD" else None)
            overflow = capture_overflow
            edge_count = 0
            pulse_count = 0
            capture_active = False
            capture_overflow = False
            arm_signal(signal)

            process_capture(captured, overflow, wlan, states)

    time.sleep_ms(10)
