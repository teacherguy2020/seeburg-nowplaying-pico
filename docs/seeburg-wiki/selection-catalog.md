---
title: selection-catalog
page_type: data-model
topics:
  - catalog
  - mapping
  - selections
confidence: low
updated: 2026-08-28 America/Chicago
---

# Selection Catalog

The Wallbox code and the music file path are separate concepts. The live
catalog is the saved moOde/MPD playlist named `Seeburg Playlist`; playlist order
is the numeric catalog sent to the Now Playing endpoint. A decoded Wallbox code
such as `B3` becomes playlist position 13 under the current 100-selection
layout. A local JSON representation is still useful for documenting the
physical code mapping:

```json
{
  "B3": {
    "title": "Example Song",
    "artist": "Example Artist",
    "album": "Example Album",
  "playlistNumber": 13,
  "file": "Music/Example Artist/Example Album/03 - Example Song.flac",
    "enabled": true
  }
}
```

## Rules

- Codes are normalized consistently, for example uppercase `B3`.
- Every enabled code resolves to exactly one one-based playlist number.
- Unknown codes are logged and rejected without changing the queue.
- The endpoint clears the live queue, adds the selected track, and starts playback
  when audio is stopped or paused; while audio is already playing, it appends the
  selected track without interruption.
- Catalog positions should be validated against the current Now Playing/moOde playlist before live use.

The canonical catalog source is Now Playing's saved `Seeburg Playlist`. The
playlist currently contains 36 tracks and can grow to the planned 100 tracks;
positions beyond the current playlist length are rejected.
