"""Seeburg 3W-1 LIVE decoder.

Hardware:
    Seeburg signal -> DB107 bridge -> 10k resistor -> EL817 -> Pico GP15

Behavior:
    - captures both GPIO edges
    - collapses AC chatter into logical electrical envelopes
    - decodes A1-K10
    - maps selection to playlist number 1-100
    - POSTs {"number": N} to Now Playing
    - provides a diagnostic web page

LIVE MODE:
    Valid decodes are sent immediately to Now Playing.
    Uncertain waveforms are rejected and send NO API request.
"""

from machine import Pin
import time
import gc

MODE = "LIVE"
SIGNAL_PIN = 15
MAX_TIMESTAMPS = 512
RECORD_COMPLETE_MS = 1200
ENVELOPE_BREAK_MS = 20
LONG_ENVELOPE_MIN_MS = 500
COUNTABLE_ENVELOPE_MIN_MS = 10
COUNTABLE_ENVELOPE_MAX_MS = 100
GROUP_GAP_MIN_MS = 150
GROUP_GAP_MAX_MS = 300
GROUP_GAP_TARGET_MS = 200
NUMBER_LANDMARK_GAP_MIN_MS = 100
NUMBER_LANDMARK_GAP_MAX_MS = 145
RIGHT_PREAMBLE_GAP_MIN_MS = 300
LEFT_OFFSET_GAP_MIN_MS = 100
LEFT_DIRECT_GAP_MAX_MS = 85
WEB_PORT = 80
WEB_REFRESH_SECONDS = 2
WIFI_RETRY_MS = 10000
API_HOST = "10.0.0.4"
API_PORT = 3101
API_PATH = "/integrations/seeburg/selection"
API_TIMEOUT_SECONDS = 5

LETTER_PAIRS = {
    1: ("A", "B"),
    2: ("C", "D"),
    3: ("E", "F"),
    4: ("G", "H"),
    5: ("J", "K"),
}

LETTERS = ["A","B","C","D","E","F","G","H","J","K"]

edge_times = [0] * MAX_TIMESTAMPS
edge_states = [0] * MAX_TIMESTAMPS
edge_count = 0
last_irq_ms = 0
capture_active = False
capture_overflow = False

latest_capture_sequence = 0
latest_capture_times = []
latest_capture_states = []
latest_capture_duration_ms = 0
latest_capture_overflow = False
latest_envelopes = []
latest_gaps = []
latest_long_envelope_number = None
latest_group_gap_after = None
latest_group_gap_ms = None
latest_number_landmark_gap_ms = None
latest_pre_long_gap_ms = None
latest_group1 = None
latest_group2 = None
latest_side = None
latest_wallbox_code = None
latest_playlist_number = None
latest_decode_valid = False
latest_decode_reason = None
latest_api_attempted = False
latest_api_ok = False
latest_api_status = None
latest_api_body = None
latest_api_error = None
latest_status = "Waiting for first Wallbox activity"


def edge_irq(pin):
    global edge_count, last_irq_ms, capture_active, capture_overflow
    now = time.ticks_ms()
    last_irq_ms = now
    capture_active = True
    if edge_count < MAX_TIMESTAMPS:
        edge_times[edge_count] = now
        edge_states[edge_count] = pin.value()
        edge_count += 1
    else:
        capture_overflow = True


def arm_signal(signal):
    signal.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=edge_irq)


def ticks_delta(newer, older):
    return time.ticks_diff(newer, older)


def capture_duration(times):
    if len(times) < 2:
        return 0
    return ticks_delta(times[-1], times[0])


def get_intervals(times):
    return [ticks_delta(times[i], times[i - 1]) for i in range(1, len(times))]


def make_envelope(times, states, start_index, end_index):
    start_ms = times[start_index]
    end_ms = times[end_index]
    return {
        "start_index": start_index,
        "end_index": end_index,
        "start_ms": start_ms,
        "end_ms": end_ms,
        "duration_ms": ticks_delta(end_ms, start_ms),
        "edges": end_index - start_index + 1,
        "start_state": states[start_index],
        "end_state": states[end_index],
    }


def analyze_envelopes(times, states):
    if not times:
        return [], []
    envelopes = []
    start_index = 0
    for i in range(1, len(times)):
        gap_ms = ticks_delta(times[i], times[i - 1])
        if gap_ms >= ENVELOPE_BREAK_MS:
            envelopes.append(make_envelope(times, states, start_index, i - 1))
            start_index = i
    envelopes.append(make_envelope(times, states, start_index, len(times) - 1))
    gaps = []
    for i in range(len(envelopes) - 1):
        gap_ms = ticks_delta(envelopes[i + 1]["start_ms"], envelopes[i]["end_ms"])
        gaps.append({
            "after_envelope": i + 1,
            "before_envelope": i + 2,
            "duration_ms": gap_ms,
        })
    return envelopes, gaps


def is_countable_envelope(envelope):
    d = envelope["duration_ms"]
    return COUNTABLE_ENVELOPE_MIN_MS <= d <= COUNTABLE_ENVELOPE_MAX_MS


def gap_is_group_separator(gap_ms):
    return GROUP_GAP_MIN_MS <= gap_ms <= GROUP_GAP_MAX_MS


def gap_is_number_landmark(gap_ms):
    return NUMBER_LANDMARK_GAP_MIN_MS <= gap_ms <= NUMBER_LANDMARK_GAP_MAX_MS


def decode_left_number(envelopes, gaps, long_index):
    result = {"valid": False, "number": None, "pre_long_gap_ms": None, "reason": None}
    pre_count = sum(1 for e in envelopes[:long_index] if is_countable_envelope(e))
    if long_index == 0:
        result.update(valid=True, number=1, reason="long envelope begins capture")
        return result
    pre_gap = gaps[long_index - 1]["duration_ms"]
    result["pre_long_gap_ms"] = pre_gap
    if pre_gap >= LEFT_OFFSET_GAP_MIN_MS:
        number = pre_count + 1
    elif pre_gap <= LEFT_DIRECT_GAP_MAX_MS:
        number = max(1, pre_count)
    else:
        result["reason"] = "ambiguous LEFT pre-long gap: {} ms".format(pre_gap)
        return result
    if not 1 <= number <= 10:
        result["reason"] = "LEFT number outside 1..10: {}".format(number)
        return result
    result.update(valid=True, number=number, reason="LEFT number decoded")
    return result


def right_group_start_index(gaps, separator_after):
    """Return zero-based envelope index where the real RIGHT first group starts.

    Some captures begin with short startup/noise envelopes before the actual
    Wallbox pulse train. If a large gap appears before the true group separator,
    everything before that gap is treated as preamble.

    Example from D6:
        3 ms envelope
        10 ms envelope
        353 ms gap
        [real first group begins]
    """
    start_index = 0

    for gap in gaps:
        if gap["after_envelope"] >= separator_after:
            break
        if gap["duration_ms"] >= RIGHT_PREAMBLE_GAP_MIN_MS:
            # after_envelope is 1-based and also equals the zero-based index
            # of the next envelope.
            start_index = gap["after_envelope"]

    return start_index


def decode_right_number(envelopes, gaps, separator_after):
    result = {
        "valid": False,
        "number": None,
        "observed_count": None,
        "landmark_gap_ms": None,
        "reason": None,
    }

    start_index = right_group_start_index(gaps, separator_after)
    first_group = envelopes[start_index:separator_after]

    observed_count = sum(
        1 for e in first_group
        if is_countable_envelope(e)
    )
    result["observed_count"] = observed_count

    landmarks = []

    for gap in gaps:
        if gap["after_envelope"] >= separator_after:
            break

        # Ignore gaps that belong to discarded preamble.
        if gap["after_envelope"] <= start_index:
            continue

        if gap_is_number_landmark(gap["duration_ms"]):
            landmarks.append(gap)

    if len(landmarks) > 1:
        result["reason"] = "multiple RIGHT number landmarks"
        return result

    if len(landmarks) == 1:
        landmark = landmarks[0]
        result["landmark_gap_ms"] = landmark["duration_ms"]

        # Count only valid envelopes from the real first-group start to the
        # landmark. This avoids raw envelope-number errors when startup junk
        # is present before the actual selection train.
        count_before_landmark = sum(
            1
            for e in envelopes[start_index:landmark["after_envelope"]]
            if is_countable_envelope(e)
        )

        number = count_before_landmark + 1

        if not 1 <= number <= 10:
            result["reason"] = "RIGHT landmark number outside 1..10: {}".format(number)
            return result

        expected = number + 10
        if observed_count not in (expected, expected + 1):
            result["reason"] = (
                "RIGHT landmark/count disagreement: landmark says {}, observed {}"
                .format(number, observed_count)
            )
            return result
    else:
        number = observed_count - 10
        if not 1 <= number <= 10:
            result["reason"] = "RIGHT first-group count outside calibrated range: {}".format(observed_count)
            return result

    result.update(valid=True, number=number, reason="RIGHT number decoded")
    return result


def decode_waveform(envelopes, gaps):
    result = {
        "valid": False,
        "reason": None,
        "side": None,
        "long_envelope_number": None,
        "group_gap_after": None,
        "group_gap_ms": None,
        "number_landmark_gap_ms": None,
        "pre_long_gap_ms": None,
        "group1": None,
        "group2": None,
        "selection": None,
        "playlist_number": None,
    }
    if not envelopes:
        result["reason"] = "no electrical envelopes"
        return result

    long_indexes = [i for i,e in enumerate(envelopes) if e["duration_ms"] >= LONG_ENVELOPE_MIN_MS]
    if len(long_indexes) > 1:
        result["reason"] = "multiple long active envelopes"
        return result

    if len(long_indexes) == 1:
        long_index = long_indexes[0]
        result["side"] = "LEFT"
        result["long_envelope_number"] = long_index + 1
        if long_index >= len(gaps):
            result["reason"] = "no gap after long envelope"
            return result
        group_gap = gaps[long_index]
        if not gap_is_group_separator(group_gap["duration_ms"]):
            result["reason"] = "gap after long envelope not valid group separator: {} ms".format(group_gap["duration_ms"])
            return result
        result["group_gap_after"] = long_index + 1
        result["group_gap_ms"] = group_gap["duration_ms"]
        left_number = decode_left_number(envelopes, gaps, long_index)
        result["pre_long_gap_ms"] = left_number["pre_long_gap_ms"]
        if not left_number["valid"]:
            result["reason"] = left_number["reason"]
            return result
        number = left_number["number"]
        result["group1"] = number + 1
        second_group = envelopes[long_index + 1:]
        group2_count = sum(1 for e in second_group if is_countable_envelope(e))
        result["group2"] = group2_count
        if group2_count not in LETTER_PAIRS:
            result["reason"] = "group 2 outside 1..5: {}".format(group2_count)
            return result
        letter = LETTER_PAIRS[group2_count][0]

    else:
        result["side"] = "RIGHT"
        candidates = []
        for gap in gaps:
            if not gap_is_group_separator(gap["duration_ms"]):
                continue
            separator_after = gap["after_envelope"]
            second_group = envelopes[separator_after:]
            group2_count = sum(1 for e in second_group if is_countable_envelope(e))
            if not 1 <= group2_count <= 5:
                continue
            right_number = decode_right_number(envelopes, gaps, separator_after)
            if not right_number["valid"]:
                continue
            candidates.append({
                "gap": gap,
                "group2": group2_count,
                "number": right_number["number"],
                "landmark_gap_ms": right_number["landmark_gap_ms"],
                "distance": abs(gap["duration_ms"] - GROUP_GAP_TARGET_MS),
            })
        if not candidates:
            result["reason"] = "no valid RIGHT-side group separator"
            return result
        candidates.sort(key=lambda x: x["distance"])
        if len(candidates) > 1 and candidates[0]["distance"] == candidates[1]["distance"]:
            result["reason"] = "ambiguous RIGHT-side separators"
            return result
        best = candidates[0]
        number = best["number"]
        group2_count = best["group2"]
        result["group_gap_after"] = best["gap"]["after_envelope"]
        result["group_gap_ms"] = best["gap"]["duration_ms"]
        result["number_landmark_gap_ms"] = best["landmark_gap_ms"]
        result["group1"] = number + 11
        result["group2"] = group2_count
        letter = LETTER_PAIRS[group2_count][1]

    wallbox_code = "{}{}".format(letter, number)
    playlist_number = LETTERS.index(letter) * 10 + number
    result["selection"] = wallbox_code
    result["playlist_number"] = playlist_number
    result["valid"] = True
    result["reason"] = "validated LIVE decode"
    return result


def post_live_selection(playlist_number):
    import socket
    import ujson
    from secrets import TRACK_KEY

    result = {"attempted": True, "ok": False, "status": None, "body": None, "error": None}
    body = ujson.dumps({"number": playlist_number})
    request = (
        "POST {} HTTP/1.1\r\n"
        "Host: {}:{}\r\n"
        "Content-Type: application/json\r\n"
        "X-Track-Key: {}\r\n"
        "Content-Length: {}\r\n"
        "Connection: close\r\n\r\n{}"
    ).format(API_PATH, API_HOST, API_PORT, TRACK_KEY, len(body), body)

    sock = None
    try:
        addr = socket.getaddrinfo(API_HOST, API_PORT)[0][-1]
        sock = socket.socket()
        try:
            sock.settimeout(API_TIMEOUT_SECONDS)
        except Exception:
            pass
        sock.connect(addr)
        sock.send(request.encode())
        chunks = []
        while True:
            try:
                chunk = sock.recv(512)
            except Exception:
                break
            if not chunk:
                break
            chunks.append(chunk)
        response = b"".join(chunks).decode("utf-8", "replace")
        if "\r\n\r\n" in response:
            header_text, response_body = response.split("\r\n\r\n", 1)
        else:
            header_text, response_body = response, ""
        status_line = header_text.split("\r\n", 1)[0]
        try:
            status_code = int(status_line.split()[1])
        except Exception:
            status_code = None
        result["status"] = status_code
        result["body"] = response_body
        if status_code is not None and 200 <= status_code < 300:
            result["ok"] = True
    except Exception as error:
        result["error"] = repr(error)
    finally:
        if sock is not None:
            try:
                sock.close()
            except Exception:
                pass
    return result


def process_capture(times, states, overflow):
    global latest_capture_sequence, latest_capture_times, latest_capture_states
    global latest_capture_duration_ms, latest_capture_overflow
    global latest_envelopes, latest_gaps, latest_long_envelope_number
    global latest_group_gap_after, latest_group_gap_ms
    global latest_number_landmark_gap_ms, latest_pre_long_gap_ms
    global latest_group1, latest_group2, latest_side
    global latest_wallbox_code, latest_playlist_number
    global latest_decode_valid, latest_decode_reason
    global latest_api_attempted, latest_api_ok, latest_api_status, latest_api_body, latest_api_error
    global latest_status

    latest_capture_sequence += 1
    latest_capture_times = times
    latest_capture_states = states
    latest_capture_overflow = overflow
    latest_capture_duration_ms = capture_duration(times)
    envelopes, gaps = analyze_envelopes(times, states)
    latest_envelopes = envelopes
    latest_gaps = gaps
    decoded = decode_waveform(envelopes, gaps)
    latest_decode_valid = decoded["valid"]
    latest_decode_reason = decoded["reason"]
    latest_side = decoded["side"]
    latest_long_envelope_number = decoded["long_envelope_number"]
    latest_group_gap_after = decoded["group_gap_after"]
    latest_group_gap_ms = decoded["group_gap_ms"]
    latest_number_landmark_gap_ms = decoded["number_landmark_gap_ms"]
    latest_pre_long_gap_ms = decoded["pre_long_gap_ms"]
    latest_group1 = decoded["group1"]
    latest_group2 = decoded["group2"]
    latest_wallbox_code = decoded["selection"]
    latest_playlist_number = decoded["playlist_number"]

    latest_api_attempted = False
    latest_api_ok = False
    latest_api_status = None
    latest_api_body = None
    latest_api_error = None

    if overflow:
        latest_status = "Capture overflow â decode/API skipped"
        return

    if not decoded["valid"]:
        latest_status = "Decode rejected: {}".format(latest_decode_reason)
        print("\nSEEBURG DECODE REJECTED:", latest_decode_reason)
        return

    latest_status = "Decoded {} â sending LIVE selection".format(latest_wallbox_code)
    print("\nSEEBURG LIVE")
    print("Decoded:", latest_wallbox_code)
    print("Playlist #:", latest_playlist_number)
    print("Side:", latest_side)
    print("Group 1:", latest_group1)
    print("Group 2:", latest_group2)
    print("Group gap:", latest_group_gap_ms)
    if latest_number_landmark_gap_ms is not None:
        print("Number landmark gap:", latest_number_landmark_gap_ms)
    if latest_pre_long_gap_ms is not None:
        print("Pre-long gap:", latest_pre_long_gap_ms)

    api_result = post_live_selection(latest_playlist_number)
    latest_api_attempted = api_result["attempted"]
    latest_api_ok = api_result["ok"]
    latest_api_status = api_result["status"]
    latest_api_body = api_result["body"]
    latest_api_error = api_result["error"]
    latest_status = (
        "LIVE SUCCESS: {}".format(latest_wallbox_code)
        if latest_api_ok
        else "LIVE API ERROR: {}".format(latest_wallbox_code)
    )
    gc.collect()


def connect_wifi():
    import network
    from secrets import WIFI_SSID, WIFI_PASSWORD
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if wlan.isconnected():
        return wlan
    print("Connecting to Wi-Fi...")
    try:
        wlan.disconnect()
    except Exception:
        pass
    wlan.connect(WIFI_SSID, WIFI_PASSWORD)
    remaining = 20
    while not wlan.isconnected() and remaining:
        time.sleep(1)
        remaining -= 1
    print("Wi-Fi connected:", wlan.ifconfig()[0] if wlan.isconnected() else "FAILED")
    return wlan


def html_escape(value):
    if value is None:
        return "-"
    return str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def state_name(value):
    return "HIGH" if value else "LOW"


def build_status_page(wlan, signal):
    if wlan.isconnected():
        wifi_status = "CONNECTED"
        ip_address = wlan.ifconfig()[0]
    else:
        wifi_status = "DISCONNECTED"
        ip_address = "unavailable"

    parts = [
        "<!doctype html><html><head><meta charset='utf-8'>",
        "<meta name='viewport' content='width=device-width,initial-scale=1'>",
        "<meta http-equiv='refresh' content='{}'>".format(WEB_REFRESH_SECONDS),
        "<title>Seeburg 3W-1</title>",
        """<style>
        body{font-family:-apple-system,BlinkMacSystemFont,Arial,sans-serif;margin:18px;background:#111;color:#eee}
        h1{margin-bottom:2px} h2{margin-top:28px}
        .box{background:#222;padding:14px;margin-top:10px;border-radius:8px}
        .decode{font-size:34px;font-weight:bold;margin:6px 0}
        .good{color:#8ee59b}.warn{color:#ffd166}.bad{color:#ff8a8a}
        .mono{font-family:Menlo,Monaco,Consolas,monospace;white-space:pre-wrap;word-break:break-word;font-size:13px}
        table{width:100%;border-collapse:collapse}th,td{text-align:left;padding:6px;border-bottom:1px solid #444}
        </style></head><body>""",
        "<h1>Seeburg 3W-1</h1><div>Decoder / LIVE Queue Integration</div>",
        "<h2>Status</h2><div class='box'>",
        "<b>Mode:</b> LIVE<br>",
        "<b>Wi-Fi:</b> {}<br>".format(wifi_status),
        "<b>IP:</b> {}<br>".format(ip_address),
        "<b>GP15:</b> {}<br>".format(state_name(signal.value())),
        "<b>Capture active:</b> {}<br>".format("YES" if capture_active else "NO"),
        "<b>Current raw edges:</b> {}<br>".format(edge_count),
        "<b>Status:</b> {}</div>".format(html_escape(latest_status)),
        "<h2>Decode</h2><div class='box'>",
    ]

    if latest_capture_sequence == 0:
        parts.append("No capture yet.")
    elif latest_decode_valid:
        parts.extend([
            "<div class='decode good'>{}</div>".format(html_escape(latest_wallbox_code)),
            "<b>Playlist #:</b> {}<br>".format(latest_playlist_number),
            "<b>Side:</b> {}<br>".format(latest_side),
            "<b>Group 1:</b> {}<br>".format(latest_group1),
            "<b>Group 2:</b> {}<br>".format(latest_group2),
            "<b>Group gap:</b> {} ms<br>".format(latest_group_gap_ms),
        ])
        if latest_number_landmark_gap_ms is not None:
            parts.append("<b>Number landmark gap:</b> {} ms<br>".format(latest_number_landmark_gap_ms))
        if latest_pre_long_gap_ms is not None:
            parts.append("<b>Pre-long gap:</b> {} ms<br>".format(latest_pre_long_gap_ms))
        if latest_long_envelope_number is not None:
            parts.append("<b>Long active envelope:</b> #{}<br>".format(latest_long_envelope_number))
    else:
        parts.append("<div class='bad'><b>Decode rejected</b></div><br>{}".format(html_escape(latest_decode_reason)))
    parts.append("</div>")

    parts.append("<h2>Now Playing API</h2><div class='box'>")
    if not latest_api_attempted:
        parts.append("No API request for latest capture.")
    else:
        parts.append("<div class='{}'><b>{}</b></div><br>".format("good" if latest_api_ok else "bad", "LIVE SUCCESS" if latest_api_ok else "LIVE FAILED"))
        parts.append("<b>HTTP status:</b> {}<br>".format(html_escape(latest_api_status)))
        if latest_api_body is not None:
            parts.append("<br><b>Response:</b><div class='mono'>{}</div>".format(html_escape(latest_api_body)))
        if latest_api_error:
            parts.append("<br><b>Error:</b><div class='mono'>{}</div>".format(html_escape(latest_api_error)))
    parts.append("<br><span class='warn'>LIVE â valid decoded selections are sent to Now Playing.</span></div>")

    parts.append("<h2>Latest Capture</h2><div class='box'>")
    if latest_capture_sequence == 0:
        parts.append("No capture yet.")
    else:
        parts.append("<b>Capture #:</b> {}<br><b>Raw edges:</b> {}<br><b>Duration:</b> {} ms<br><b>Electrical envelopes:</b> {}<br><b>Overflow:</b> {}".format(
            latest_capture_sequence, len(latest_capture_times), latest_capture_duration_ms, len(latest_envelopes), "YES" if latest_capture_overflow else "NO"))
    parts.append("</div>")

    if latest_envelopes:
        parts.append("<h2>Electrical Envelopes</h2><div class='box'><table><tr><th>#</th><th>Duration</th><th>Edges</th><th>Gap after</th></tr>")
        for i, envelope in enumerate(latest_envelopes):
            gap_after = "-" if i >= len(latest_gaps) else "{} ms".format(latest_gaps[i]["duration_ms"])
            parts.append("<tr><td>{}</td><td>{} ms</td><td>{}</td><td>{}</td></tr>".format(i + 1, envelope["duration_ms"], envelope["edges"], gap_after))
        parts.append("</table></div>")

    if latest_capture_times:
        parts.append("<h2>Raw Intervals</h2><div class='box mono'>{}</div>".format(html_escape(", ".join(str(v) for v in get_intervals(latest_capture_times)))))

    parts.append("<p style='color:#888;margin-top:28px'>Auto-refresh every {} seconds. LIVE mode.</p></body></html>".format(WEB_REFRESH_SECONDS))
    return "".join(parts)


def start_web_server():
    import socket
    server = socket.socket()
    try:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    except Exception:
        pass
    server.bind(("0.0.0.0", WEB_PORT))
    server.listen(2)
    try:
        server.setblocking(False)
    except Exception:
        server.settimeout(0)
    print("Diagnostic web server listening on port", WEB_PORT)
    return server


def service_web_server(server, wlan, signal):
    if server is None:
        return
    client = None
    try:
        client, _ = server.accept()
    except Exception:
        return
    try:
        try:
            client.settimeout(0.5)
        except Exception:
            pass
        try:
            client.recv(512)
        except Exception:
            pass
        page = build_status_page(wlan, signal)
        header = "HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=utf-8\r\nCache-Control: no-store\r\nConnection: close\r\n\r\n"
        client.send(header.encode())
        data = page.encode()
        offset = 0
        while offset < len(data):
            sent = client.send(data[offset:offset + 1024])
            if not sent:
                break
            offset += sent
    except Exception as error:
        print("WEB ERROR:", error)
    finally:
        if client is not None:
            try:
                client.close()
            except Exception:
                pass


print()
print("Seeburg 3W-1 LIVE Decoder")
print("Mode: LIVE")

wlan = connect_wifi()
if wlan.isconnected():
    print("\nOpen on the iPad:")
    print("http://{}/".format(wlan.ifconfig()[0]))

web_server = None
if wlan.isconnected():
    try:
        web_server = start_web_server()
    except Exception as error:
        print("Unable to start web server:", error)

signal = Pin(SIGNAL_PIN, Pin.IN, Pin.PULL_UP)
arm_signal(signal)
print("\nWaiting for Wallbox selections...")
last_wifi_retry_ms = time.ticks_ms()

while True:
    if capture_active and edge_count:
        quiet_ms = ticks_delta(time.ticks_ms(), last_irq_ms)
        if quiet_ms >= RECORD_COMPLETE_MS:
            signal.irq(handler=None)
            count = edge_count
            captured_times = edge_times[:count]
            captured_states = edge_states[:count]
            overflow = capture_overflow
            edge_count = 0
            capture_active = False
            capture_overflow = False
            arm_signal(signal)
            process_capture(captured_times, captured_states, overflow)

    service_web_server(web_server, wlan, signal)

    now = time.ticks_ms()
    if ticks_delta(now, last_wifi_retry_ms) >= WIFI_RETRY_MS:
        last_wifi_retry_ms = now
        if not wlan.isconnected():
            latest_status = "Wi-Fi disconnected â reconnecting"
            wlan = connect_wifi()
            if wlan.isconnected():
                latest_status = "Wi-Fi reconnected"
                if web_server is not None:
                    try:
                        web_server.close()
                    except Exception:
                        pass
                try:
                    web_server = start_web_server()
                except Exception as error:
                    web_server = None
                    print("Unable to restart web server:", error)

    time.sleep_ms(10)