---
title: open-questions
page_type: questions
topics:
  - hardware
  - design
  - decisions
confidence: low
updated: 2026-08-28 America/Chicago
---

# Open Questions

- What jukebox model and original voltage does it expect?
- What exact contact waveform and pulse polarity will the isolated input produce?
- Is there a distinct selection-complete contact?
- Should the Wallbox operate independently, or remain electrically connected to a jukebox?
- Is a nearby confirmation display or audible acknowledgment desirable?

## Resolved software decisions

- The Pico 2W performs pulse capture and decoding, then sends the one-based
  playlist number directly to `POST /integrations/seeburg/selection` at
  `10.0.0.4:3101`.
- The Now Playing API owns authentication, playlist lookup, and MPD queueing;
  no separate intermediary application is required.
- `Seeburg Playlist` order is the canonical catalog. The endpoint currently has
  36 available positions and is intended to support up to 100.
- Normal selections append to the queue without starting playback. `dryRun`
  mode is available for commissioning.

