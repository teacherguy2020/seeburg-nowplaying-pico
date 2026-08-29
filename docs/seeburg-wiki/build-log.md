---
title: build-log
page_type: log
topics:
  - experiments
  - measurements
  - decisions
confidence: low
updated: 2026-08-28 America/Chicago
---

# Build Log

## 2026-08-26

- Created the separate `seeburg-wallbox/` project directory.
- Established a provisional architecture: isolated contact sensing, real-time decoding, and Now Playing queue append.
- No Wallbox electrical claims have been confirmed yet.
- Reviewed `/Users/brianwis/Public/3w1.pdf`, the 33-page Type 3W-1 service manual.
- Confirmed the 25 VAC three-wire interface, motor-driven grounded selector wiper, two pulse groups, approximate pulse timing, 24 RPM nominal motor speed, and serial-dependent circuit variants.
- Revised the decoder plan: capture and decode a pulse trace rather than expecting the Wallbox contacts to expose a literal `B3` signal.
- Photograph `/Users/brianwis/Public/wallbox-serial.jpg` confirms the chassis stamp `25050`; classify the unit as the above-16645 three-blade variant.

## 2026-08-28

- Created and deployed `POST /integrations/seeburg/selection` on the Now Playing Pi at `10.0.0.4:3101`.
- The endpoint accepts a one-based playlist number and uses `Seeburg Playlist` order. It clears and starts the selected track when stopped/paused, or appends without interrupting active playback.
- Added `dryRun` support and `GET /integrations/seeburg/playlist` for commissioning and number-to-file verification.
- Confirmed the playlist currently contains 36 tracks and tested both dry-run resolution and a real append/cleanup cycle.
- Revised the architecture so the Pico 2W sends the playlist number directly to the Now Playing API.

## 2026-08-29

- Reviewed the final Pico 2 W LIVE firmware and confirmed its diagnostic page is reachable at `10.0.0.118`.
- Confirmed the firmware contract: valid selections are decoded locally and sent as `{"number": N}` with `X-Track-Key`; invalid or overflowed captures make no API request.
- Clarified that RECORD and DRY_RUN are commissioning documentation/API capabilities, not runtime modes in the final Pico `main.py`.

Last updated: 2026-08-29 America/Chicago
