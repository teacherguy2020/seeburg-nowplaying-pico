# Seeburg Now Playing Pico

MicroPython firmware for the Raspberry Pi Pico 2 W used as the Seeburg
Wallbox pulse recorder/decoder and direct Now Playing API client.

## Current status

`main.py` is now the deployed LIVE firmware. It captures both GPIO edges,
collapses them into electrical envelopes, validates and decodes a selection,
then sends the resulting playlist number to Now Playing. Invalid or overflowed
captures are rejected without making an API request.

RECORD and DRY_RUN were commissioning plans; they are not runtime modes in the
current file. Use the Pico diagnostic page and the Now Playing API's explicit
`dryRun` request from a separate commissioning client when a non-mutating test
is needed.

## Hardware and service

- Device: Raspberry Pi Pico 2 W
- Current DHCP address: `10.0.0.118`
- Now Playing API: `POST /integrations/seeburg/selection`
- API payload: `{"number": 1}` through `{"number": 100}`

The Pico sends a playlist number. The Now Playing API validates the request and
looks up that position in the `Seeburg Playlist`. If playback is stopped or
paused, the API clears the live queue, adds the selected track, and starts it;
if playback is already active, it appends the selected track without
interrupting playback.

## Final hardware wiring

The Seeburg's approximately 25 VAC selection signal is isolated from the Pico
through a DB107 full-wave bridge and an EL817/PC817-type optocoupler module.
The as-built circuit uses an external 10 kΩ, 1/2-watt series resistor on the
module input and connects the isolated output to GP15. See the
[as-built wiring record](docs/seeburg-wiki/as-built-wiring.md) for the exact
terminal and physical-pin connections. **Never connect Seeburg COMMON to Pico
GND.**

## Local setup

Copy `secrets.example.py` to `secrets.py` and fill in the Wi-Fi credentials.
Also fill in `TRACK_KEY` with the existing Now Playing API key. `secrets.py` is
ignored by Git and must not be committed.

The firmware is configured with `MODE = "LIVE"`. Before connecting the
Wallbox, verify the playlist mapping with `GET /integrations/seeburg/playlist`
or a `dryRun` API request. A valid physical selection then changes playback
according to the stopped-versus-playing behavior above.
