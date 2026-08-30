---
title: decoder
page_type: implementation
topics:
  - decoder
  - micropython
  - pulse-timing
  - selections
confidence: high
updated: 2026-08-29 America/Chicago
---

# Seeburg Pulse Decoder

The Pico 2 W firmware in [`main.py`](../../main.py) is the working LIVE
decoder for the serial-25050 Seeburg 3W-1. The hardware rectifies the
approximately 25 VAC selection signal without smoothing it. The Pico captures
the resulting rapid GPIO transitions and groups them into the slower electrical
envelopes produced by the Wallbox mechanism.

## Capture and envelope formation

The optocoupler output is connected to GP15, physical pin 20. `main.py` arms a
GPIO interrupt for both rising and falling edges. The interrupt handler records
timestamps and pin states in a fixed-size buffer, then returns quickly; it does
not perform networking or decoding.

After the signal has been quiet for 1,200 ms, the capture is processed. Edges
separated by at least 20 ms begin a new electrical envelope. An envelope is
countable when its duration is between 10 ms and 100 ms. A capture overflow is
rejected before decoding.

The measured raw waveform commonly contains intervals around 7–8 ms and 1–2
ms. Those are the full-wave-rectified AC transitions, not individual mechanical
Wallbox pulses. The firmware therefore decodes envelopes rather than counting
raw edges directly.

## Two-group decode

The Wallbox produces two groups of electrical envelopes separated by a gap of
approximately 200 ms. The second group contains one through five countable
envelopes and identifies the letter pair:

| Second-group count | Letter pair |
|---:|:---|
| 1 | A/B |
| 2 | C/D |
| 3 | E/F |
| 4 | G/H |
| 5 | J/K |

The first group identifies the number and which letter in that pair was
selected:

- On the right-side decode, the first-group count normally identifies the
  number. A measured 100–145 ms number-landmark gap can provide the number
  directly; the decoder verifies it against the observed count.
- On the left-side decode, a long active envelope of at least 500 ms identifies
  the left signaling pattern. The count before it and the gap immediately
  before it determine the number. The measured long envelope is approximately
  865–870 ms.

The calibrated timing ranges in `main.py` are:

| Feature | Firmware range or threshold |
|---|---:|
| Envelope break | 20 ms minimum gap |
| Countable envelope | 10–100 ms |
| Long envelope | 500 ms minimum |
| Group separator | 150–300 ms |
| Number landmark | 100–145 ms |
| Left pre-long offset | 100 ms minimum |
| Left direct pre-long gap | 85 ms maximum |

The observed working values are approximately 40–47 ms per envelope, 35–44 ms
between normal envelopes, 200–206 ms for the group separator, and 120–125 ms
for the right-side number landmark.

## Selection and playlist position

The decoder produces a Wallbox code using the letter sequence
`A B C D E F G H J K` and number 1 through 10. It converts that code to a
one-based playlist position with the same formula as:

```python
LETTERS = ["A", "B", "C", "D", "E", "F", "G", "H", "J", "K"]
playlist_number = LETTERS.index(letter) * 10 + number
```

Thus `B3` becomes position 13 and `F5` becomes position 55. The Pico does not
contain track metadata or filenames. Now Playing resolves the position against
the saved `Seeburg Playlist`.

## Validation and rejection

The decoder rejects captures with:

- no electrical envelopes;
- more than one long active envelope;
- no valid group separator;
- ambiguous separators;
- invalid group counts;
- inconsistent number landmarks;
- ambiguous left-side timing; or
- capture-buffer overflow.

Rejected captures are logged on the diagnostic page and over the serial console.
They do not make an API request and cannot change playback.

## LIVE API request

For a validated selection, the Pico sends an authenticated request directly to
Now Playing:

```http
POST /integrations/seeburg/selection
Host: 10.0.0.4:3101
Content-Type: application/json
X-Track-Key: <TRACK_KEY>

{"number": 13}
```

The firmware is LIVE-only. It has no RECORD or DRY_RUN runtime mode. Use the
Pico diagnostic page for capture evidence and the Now Playing API's explicit
`dryRun` request from a separate commissioning client when a non-mutating API
test is required.

## Diagnostics

The Pico hosts a small diagnostic page on port 80. It reports Wi-Fi status,
capture count, raw edge count, envelope durations, decoded Wallbox code,
playlist number, and the most recent API result. The page is served from the
same `main.py` process and refreshes every two seconds.

## Related documentation

- [As-built wiring](as-built-wiring.md)
- [Parts list](parts-list.md)
- [Software integration](software-integration.md)
- [Now Playing project](https://github.com/teacherguy2020/now-playing)
