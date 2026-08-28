# Seeburg Now Playing Pico

MicroPython firmware for the Raspberry Pi Pico 2 W used as the Seeburg
Wallbox pulse recorder/decoder and direct Now Playing API client.

## Current status

`main.py` now implements three commissioning modes:

- `RECORD` captures both GPIO edges, their timestamps, and sampled HIGH/LOW
  states over USB/serial only. It intentionally applies no minimum-gap filter.
- `DRY_RUN` validates and decodes a capture, then calls the Now Playing API with
  `dryRun: true` without changing the queue.
- `LIVE` validates and decodes a capture, then appends the selected track.

The Wallbox legend and timing thresholds remain provisional until measurements
from the actual serial-25050 Wallbox confirm them.

## Hardware and service

- Device: Raspberry Pi Pico 2 W
- Current DHCP address: `10.0.0.118`
- Now Playing API: `POST /integrations/seeburg/selection`
- API payload: `{"number": 1}` through `{"number": 100}`

The Pico sends a playlist number. The Now Playing API validates the request,
looks up that position in the `Seeburg Playlist`, and appends the resolved
track to MPD without starting playback.

## Local setup

Copy `secrets.example.py` to `secrets.py` and fill in the Wi-Fi credentials.
Also fill in `TRACK_KEY` with the existing Now Playing API key. `secrets.py` is
ignored by Git and must not be committed.

Start with `MODE = "RECORD"`. Once traces are understood, change to
`DRY_RUN`, and use `LIVE` only after the number mapping has been verified.
