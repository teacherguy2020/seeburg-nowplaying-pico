---
title: selection-catalog
page_type: data-model
topics:
 - catalog
 - mapping
 - selections
confidence: high
updated: 2026-08-29 America/Chicago
---

# Selection Catalog

The Seeburg 3W-1 has **100 selections**: ten letter groups, each with ten numbered selections.

The letters used by the Wall-O-Matic are:

`A B C D E F G H J K`

There is no `I` selection.

Each physical Wallbox selection maps directly to a **one-based playlist position from 1 through 100**. The mapping is fixed and does not require a separate JSON catalog.

## Wallbox code to playlist position

The playlist is arranged letter-major:

| Wallbox selections | Playlist positions |
|---|---:|
| A1-A10 | 1-10 |
| B1-B10 | 11-20 |
| C1-C10 | 21-30 |
| D1-D10 | 31-40 |
| E1-E10 | 41-50 |
| F1-F10 | 51-60 |
| G1-G10 | 61-70 |
| H1-H10 | 71-80 |
| J1-J10 | 81-90 |
| K1-K10 | 91-100 |

Examples:

- `A1` → playlist position `1`
- `A10` → playlist position `10`
- `B1` → playlist position `11`
- `B5` → playlist position `15`
- `F5` → playlist position `55`
- `K10` → playlist position `100`

The conversion used by the Pico is equivalent to:

```python
LETTERS = ["A", "B", "C", "D", "E", "F", "G", "H", "J", "K"]

playlist_number = LETTERS.index(letter) * 10 + number
```

For example, `F5` is the sixth letter group. Its zero-based group index is 5, so:

```text
(5 × 10) + 5 = 55
```

## What the Pico sends

The Pico first decodes the Wallbox pulse train into a selection such as `F5`.

It then converts that code to the corresponding numeric playlist position and sends the number to Now Playing:

```json
{
 "number": 55
}
```

The Pico does **not** need to know the song title, artist, album, or filesystem path associated with that position.

## The actual music catalog

The saved moOde/MPD playlist named **`Seeburg Playlist`** is the music catalog.

Its order determines what each Wallbox selection plays.

For example, if track 55 in `Seeburg Playlist` is a Miles Davis recording, pressing `F5` selects that track. Moving a different track into playlist position 55 changes what `F5` selects without requiring any change to the Pico firmware.

The complete path is:

```text
Seeburg button
 ↓
Wallbox code (for example F5)
 ↓
playlist position (55)
 ↓
Now Playing API
 ↓
track 55 in "Seeburg Playlist"
 ↓
MPD / moOde
```

This separation is intentional. The Pico is responsible for decoding the physical Wallbox. Now Playing is responsible for translating the resulting playlist position into an actual music file.

## Playlist length

The Wallbox and decoder support positions **1 through 100**, regardless of how many tracks are currently populated in `Seeburg Playlist`.

If the Pico sends a valid Wallbox position that is beyond the current length of the playlist, Now Playing rejects the request rather than selecting a different track.

For example, if the playlist currently contains only 36 tracks:

```text
A1 → position 1 → valid
D6 → position 36 → valid
D7 → position 37 → outside current playlist
F5 → position 55 → outside current playlist
K10 → position 100 → outside current playlist
```

`F5` still correctly means **position 55**. It simply cannot be played until `Seeburg Playlist` contains at least 55 tracks.

This distinction is important: the playlist's current length does not change the Wallbox mapping.

## Queue and playback behavior

The Now Playing service, not the Pico, owns playback and queue policy.

For a valid playlist position:

- If music is already playing, the selected track is appended to the queue.
- If music is not playing, Now Playing can clear the existing queue, add the selected track, and start playback.
- If the requested position is beyond the current playlist length, the request is rejected.
- An invalid selection is never silently substituted with another track.

This keeps the responsibilities clean:

**Pico**

```text
Read Wallbox signal
→ decode selection
→ calculate position 1-100
→ send position to Now Playing
```

**Now Playing**

```text
Receive position
→ look up that position in "Seeburg Playlist"
→ apply queue/playback rules
→ send track to MPD
```

The Pico therefore remains independent of the actual music assigned to the Wallbox. The contents and order of `Seeburg Playlist` can be changed at any time without reprogramming the Pico.
