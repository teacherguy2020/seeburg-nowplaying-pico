# Seeburg Now Playing Pico

MicroPython firmware for the Raspberry Pi Pico 2 W used as the Seeburg
Wallbox pulse recorder/decoder and direct Now Playing API client.

## Current status

The current firmware establishes a Wi-Fi connection and reports the Pico's IP
address. Pulse capture, Wallbox-code decoding, and the authenticated request to
the Now Playing API will be added as the electronics are commissioned.

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
`secrets.py` is ignored by Git and must not be committed.
