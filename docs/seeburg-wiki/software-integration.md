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

## Current event flow

```text
Wallbox signal
  → Pico GPIO edge capture
  → electrical envelopes
  → validated Wallbox code
  → playlist number 1–100
  → authenticated HTTP request
  → Now Playing playlist lookup
  → MPD queue/playback
```

The Pico 2 W runs the LIVE MicroPython firmware in [`main.py`](../../main.py).
It captures and decodes the serial-25050 Wallbox waveform, converts a valid
selection such as `B3` to its one-based playlist position, and sends that
number to Now Playing. The Pico does not control MPD directly and does not
contain the music catalog.

## Pico responsibilities

- Capture both GPIO edges from the isolated optocoupler output on GP15.
- Group the rectified-AC transitions into electrical envelopes.
- Validate the two-group waveform and decode the Wallbox selection.
- Convert `A1`–`K10` (excluding `I`) to playlist positions 1–100.
- Send valid selections over Wi-Fi with the `X-Track-Key` header.
- Reject invalid or overflowing captures without making an API request.
- Provide the local diagnostic page with capture, decode, and API status.

The firmware reconnects Wi-Fi when needed, applies a socket timeout to the API
request, and keeps the GPIO interrupt path short so networking does not occur
inside the edge handler. Credentials are kept in the untracked `secrets.py`.

## Now Playing responsibilities

The live endpoint is:

```http
POST http://10.0.0.4:3101/integrations/seeburg/selection
Content-Type: application/json
X-Track-Key: <existing Now Playing track key>

{"number": 13}
```

Now Playing validates the number, resolves it against the saved moOde/MPD
playlist `Seeburg Playlist`, and owns queue/playback policy:

- when playback is stopped or paused, it clears the live queue, adds the
  selected track, and starts playback;
- when playback is already active, it appends the selected track without
  interrupting playback; and
- when the number is beyond the current playlist length, it rejects the request
  without selecting another track.

The playlist order is the catalog. Reordering or adding tracks changes what a
Wallbox position plays without requiring a Pico firmware change. The playlist
name defaults to `Seeburg Playlist` and is configurable on the Now Playing
host with `SEEBURG_PLAYLIST_NAME`.

## Commissioning and diagnostics

The Pico firmware is LIVE-only; RECORD and DRY_RUN are not firmware modes. Use
the Pico diagnostic page for raw capture and decode evidence. For a non-mutating
API test, a separate commissioning client can send:

```json
{"number": 13, "dryRun": true}
```

The read-only mapping endpoint is:

```http
GET /integrations/seeburg/playlist
```

Both API routes require the same track-key header. These tools verify the
current number-to-file mapping without embedding filenames or track metadata in
the Pico.

## Related documentation

- [Decoder](decoder.md)
- [As-built wiring](as-built-wiring.md)
- [Architecture](architecture.md)
- [Now Playing project](https://github.com/teacherguy2020/now-playing)

Last updated: 2026-08-29 America/Chicago
