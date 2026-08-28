---
title: architecture
page_type: concept
topics:
  - architecture
  - integration
  - queue
confidence: low
updated: 2026-08-28 America/Chicago
---

# Architecture

## Components

### Wallbox

The original selector mechanism and contacts. The mechanism must be kept electrically isolated from the computer and preferably connected through a removable adapter harness.

### Input interface

An isolated interface converts the Wallbox contact circuit into safe logic-level signals. The design depends on whether the source is AC or DC and on the voltage/current used by the particular Wallbox.

### Real-time decoder

A Raspberry Pi Pico or ESP32 is the preferred first decoder. It can handle contact bounce, timing, edge capture, and state transitions deterministically.

### Pico 2W API client

The Pico owns pulse capture, decoding, selection validation, and the network request. After decoding a selection such as `B3`, it converts the selection to the corresponding one-based playlist number and sends that number directly to the Now Playing API. The request uses the existing `X-Track-Key` authentication header:

```json
{
  "number": 13
}
```

### Now Playing integration

The live route is `POST /integrations/seeburg/selection` on the Now Playing Pi at `10.0.0.4:3101`. It accepts a playlist number from 1 through 100, resolves that position against the saved `Seeburg Playlist`, and appends the selected file without starting playback. The current commissioning playlist contains 36 tracks, so positions 1 through 36 are currently available. `dryRun: true` resolves the selection without changing the queue. `GET /integrations/seeburg/playlist` exposes the current number-to-file mapping.

The Now Playing API remains the queue authority and requires the existing Now Playing track key. The Seeburg project uses that existing service rather than an independent MPD controller.

## Non-goals

- Direct GPIO connection without isolation
- Direct MPD control from the Wallbox decoder
- Replacing the existing Now Playing queue authority
- Assuming all Seeburg Wallboxes share one wiring scheme

