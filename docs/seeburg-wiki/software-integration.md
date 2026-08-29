---
title: software-integration
page_type: integration
topics:
  - raspberry-pi
  - api
  - now-playing
  - mpd
confidence: high
updated: 2026-08-29 America/Chicago
---

# Software Integration

## Final event flow

```text
contact trace → decoder event → Wallbox code → playlist number → authenticated API request → catalog lookup → queue append
```

## Working implementation plan

The deployed software/hardware path is:

```text
Data Sync Wallbox terminals
  → removable parallel breakout
  → DB107 bridge → 10 kΩ series resistor → EL817 module
  → low-voltage Pico input
  → raw pulse recorder / decoder
  → authenticated Now Playing API
  → append or play-next in the current MPD queue
```

The Data Sync terminals are the observation point, not a direct breadboard logic input. The Wallbox-side conductors may carry approximately 25 VAC, so the breadboard begins on the isolated, low-voltage side of the interface.

The current `main.py` is LIVE-only firmware. It captures, decodes, validates,
and submits selections. RECORD and DRY_RUN are commissioning procedures, not
runtime modes in the firmware: use the Pico diagnostic page for evidence and
send an explicit `dryRun` request from a separate commissioning client.

The final live operation depends on playback state: when MPD is stopped or
paused, the endpoint clears the live queue, adds the resolved track, and starts
playback. When MPD is already playing, it appends the resolved track to the end
of the queue without interrupting the current track.

The decoder boundary should remain explicit: the hardware initially produces a timestamped pulse trace, and a protocol/state-machine layer converts that trace into a normalized Wallbox code such as `B3`. The current working legend maps the second group to `A/B`, `C/D`, `E/F`, `G/H`, or `J/K`; the first group maps `2–11` to numbers `1–10` on the pair's first letter and `12–21` to numbers `1–10` on its second letter. Thus `B3` is first-group `14` (`11 + 3`), second-group `1`, and playlist slot `13`. Confirm this with recorded selections before finalizing the decoder. The manual does not describe a self-contained digital code output from the Wallbox.

The first decoder test should measure pulse counts and timing for known button pairs. It should verify the two-group structure, approximately 40 ms intra-group spacing, and approximately 200 ms inter-group gap. Motor speed and contact condition are part of the measurement, not merely mechanical maintenance details.

The first GPIO program should initially be intentionally simple: timestamp edges
and print the timing over USB/serial. It should not attempt final decoding or
playback control until traces from the serial-25050 Wallbox are understood. The
three modes provide a controlled progression from electrical observation to
queue integration.

## Pico 2W pulse-decoder program

The Pico 2W is the real-time pulse recorder / decoder and direct Now Playing API client. The current device is reachable at DHCP address `10.0.0.118`; its firmware entry point is [`main.py`](../../main.py). The project `main.py` implements GPIO capture, decoding, validation, and the authenticated LIVE API request.

The program should keep pulse timing and decoding on the Pico while the Now Playing API handles catalog lookup, authentication validation, queueing, and playback control:

```text
isolated optocoupler output
  → Pico GPIO interrupt
  → timestamped edge capture
  → pulse-group state machine
  → validated Wallbox code, such as B3
  → playlist number, such as 13
  → authenticated HTTP POST
  → Now Playing API
  → playlist lookup
  → MPD
```

### Pulse capture

The EL817 module output is connected to GP15. Configure the GPIO interrupt on
the active signal edges. The interrupt handler records monotonic timestamps and
returns; it does not perform Wi-Fi or other slow operations. The decoder groups
the rectified-AC transitions into envelopes rather than treating each raw edge
as a mechanical pulse.

### Grouping and state machine

The decoder should recognize the two expected groups:

```text
first group:  2–21 pulses
               approximately 200 ms gap
second group: 1–5 pulses
```

Pulses within a group are expected to be approximately 40 ms apart. A state machine should track `IDLE`, `GROUP_ONE`, `GROUP_GAP`, `GROUP_TWO`, `COMPLETE`, and `ERROR`. A quiet-period timeout completes a candidate selection; impossible counts, missing groups, or invalid timing should be rejected and logged.

### Working decode rule

The second group identifies the letter pair:

| Pulses | Letter pair |
|---:|:---|
| 1 | A/B |
| 2 | C/D |
| 3 | E/F |
| 4 | G/H |
| 5 | J/K |

The first group identifies the letter within that pair and the number. Counts `2–11` mean numbers `1–10` on the pair's first letter; counts `12–21` mean numbers `1–10` on its second letter. For example, first-group count `14` and second-group count `1` decode to `B3`. This legend remains provisional until known button selections are recorded from the actual serial-25050 Wallbox.

During development, each completed attempt should log both raw evidence and the result:

```json
{
  "group1": 14,
  "group2": 1,
  "selection": "B3",
  "intraGroupMs": [38, 41, 40],
  "groupGapMs": 198,
  "valid": true
}
```

The final operational mode is `LIVE`: the Pico captures and validates a
selection, converts it to a playlist number, and submits that number as a
normal request. Use the Pico diagnostic page for capture/decode evidence. For a
non-mutating commissioning check, use the API's explicit `dryRun` request from
a separate client; the current Pico firmware does not implement RECORD or
DRY_RUN switches.

## Live Now Playing selection API

```http
POST /integrations/seeburg/selection
Content-Type: application/json
X-Track-Key: <existing Now Playing track key>

{"number":36}
```

The endpoint is implemented by the Now Playing API running on the local Pi at
`10.0.0.4:3101`. The Pico (or a commissioning client) sends the selection
number directly to the API, which reads the saved moOde/MPD playlist and
performs the queue operation.

The request must include the existing Now Playing track key in the
`X-Track-Key` header. The JSON `number` must be an integer from `1` through
`100`. The API then applies the playlist-length check as well: with the current
36-track commissioning playlist, selections `1` through `36` are valid, while
`37` through `100` return an out-of-range error until more tracks are added.

On a normal request, the API resolves the number against `Seeburg Playlist` in
playlist order. If playback is stopped or paused, it clears the live MPD queue,
adds the selected file, and starts playback. If playback is active, it appends
the selected file to the end of the queue without interrupting playback. The
playlist name defaults to `Seeburg Playlist` and can be changed with the
`SEEBURG_PLAYLIST_NAME` environment setting. Playlist order is therefore the
catalog: number 1 is the first saved track, number 2 the second, and so on.

Use dry-run mode while commissioning the decoder:

```json
{"number":36,"dryRun":true}
```

With `dryRun: true`, the API resolves and reports the track without changing
the queue. A successful response includes the selected number, playlist name,
playlist length, resolved file, and `dryRun: true`. A normal successful append
also reports `queued: true`, the resulting queue length, and
`playbackStarted: false`.

The read-only mapping endpoint is:

```http
GET /integrations/seeburg/playlist
```

It returns the current number-to-file mapping, with each track carrying its
one-based `number`. Both this endpoint and the POST endpoint require the same
track-key header. On 2026-08-28 it reported 36 tracks. Selection 36 was tested
in dry-run mode and a real append test was completed and cleaned up afterward.

The Pico should send only the playlist number rather than a filename. This
keeps the catalog in moOde, allows tracks to be reordered without code changes,
and avoids giving the input device direct MPD control. The current endpoint
supports a numeric JSON body as well, but the object form shown above is the
canonical wire format because it also supports `dryRun`.

The firmware uses MicroPython's `urequests` and `ujson` modules, supplies the
`X-Track-Key` from the untracked `secrets.py`, applies a socket timeout, retries
one failed request after reconnecting Wi-Fi, and suppresses an identical
selection received within a short configurable commissioning window. The GPIO
interrupt is re-armed before decoding or networking so slow API operations do
not unnecessarily block edge capture.

## Operational requirements

- serial/raw decoder logging during commissioning
- persistent API/queue-event logging on Now Playing
- replayable raw contact traces during development
- configurable duplicate suppression
- Wi-Fi reconnect and HTTP failure handling
- clear diagnostic/error indication

An HTTP health endpoint or heartbeat is a version-2 enhancement rather than a
version-1 requirement. The Pico should not write every event indefinitely to
onboard flash. During commissioning it can log heavily over USB/serial; after
deployment, it can retain recent diagnostics in RAM and print them when a
terminal is attached, while the Now Playing service maintains the permanent
API and queue-event audit trail.

## Source

- [Seeburg Wall-O-Matic Type 3W-1 Service Manual](/Users/brianwis/Public/3w1.pdf), pp. 3–5 and 7.

Last updated: 2026-08-29 America/Chicago
