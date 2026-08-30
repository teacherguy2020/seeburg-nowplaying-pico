---
title: architecture
page_type: concept
topics:
  - architecture
  - integration
  - queue
confidence: high
updated: 2026-08-29 America/Chicago
---

# Architecture

## Components

### Wallbox

The original selector mechanism and contacts. The mechanism must be kept electrically isolated from the computer and preferably connected through a removable adapter harness.

### Input interface

The final isolated interface is specific to the measured serial-25050 Wallbox:
`SIGNAL/COMMON → DB107 ~/~ → DB107 + → 10 kΩ, 1/2 W → EL817 module`.
The module output connects to Pico 3V3(OUT), GP15, and Pico GND. See
[As-built wiring](as-built-wiring.md) for the complete circuit and safety boundary.

### Pico 2 W decoder and API client

The Pico 2 W API client owns pulse capture, envelope decoding, selection
validation, and the network request. After decoding a selection such as `B3`,
it converts the selection to the corresponding one-based playlist number and
sends that number directly to the Now Playing API. The request uses the
existing `X-Track-Key` authentication header:

```json
{
  "number": 13
}
```

### Now Playing integration

The live route is `POST /integrations/seeburg/selection` on the Now Playing Pi at `10.0.0.4:3101`. It accepts a playlist number from 1 through 100 and resolves that position against the saved `Seeburg Playlist`. If MPD is not playing, the route clears the live queue, adds the selected file, and starts playback. If MPD is already playing, it appends the selected file and leaves playback uninterrupted. `dryRun: true` resolves the selection without changing the queue. `GET /integrations/seeburg/playlist` exposes the current number-to-file mapping.

The Now Playing API remains the queue authority and requires the existing Now Playing track key. The Seeburg project uses that existing service rather than an independent MPD controller.

## Non-goals

- Direct GPIO connection without isolation
- Direct MPD control from the Wallbox decoder
- Replacing the existing Now Playing queue authority
- Assuming all Seeburg Wallboxes share one wiring scheme

Last updated: 2026-08-29 America/Chicago
