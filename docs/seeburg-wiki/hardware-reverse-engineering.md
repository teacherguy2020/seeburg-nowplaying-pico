---
title: hardware-reverse-engineering
page_type: historical-background
topics:
  - hardware
  - contacts
  - safety
confidence: high
updated: 2026-08-29 America/Chicago
---

# Hardware Reverse Engineering

This page records what was learned from the Seeburg 3W-1 service manual and
the measured serial-25050 Wallbox. It is background for the finished project;
the final component values and connections are documented in
[As-built wiring](as-built-wiring.md).

## What the manual describes

The Wall-O-Matic is not a passive matrix keypad. Its selection buttons latch
mechanically, start a 25 VAC motor, and route a motor-driven selector-plate
contact sequence into the jukebox's Selection Receiver. The receiver interprets
two pulse groups rather than receiving a literal digital `B3` value:

```text
first group: 2–21 pulses
approximately 0.2 s gap
second group: 1–5 pulses
individual pulse spacing: approximately 0.04 s
```

The second group identifies one of five letter pairs:

| Second group | Letter pair |
|---:|:---|
| 1 | A/B |
| 2 | C/D |
| 3 | E/F |
| 4 | G/H |
| 5 | J/K |

The first group carries the number and identifies which letter in the pair was
selected. The finished Pico decoder implements this interpretation using the
measured electrical envelopes and additional timing checks described in
[Decoder](decoder.md).

## Unit-specific findings

The project Wallbox is stamped serial `25050`, placing it in the later
above-16645 three-blade latch-bar variant. The manual documents different
circuit variants by serial range, so the schematic and conductor functions
must be verified for the actual unit rather than assumed from a generic
Seeburg drawing.

The working interface taps the verified `SIGNAL`/`COMMON` pair and keeps the
approximately 25 VAC Wallbox circuit isolated from the Pico. The final DB107,
external 10 kΩ resistor, and EL817 module arrangement is recorded in
[As-built wiring](as-built-wiring.md).

## Lessons from the investigation

- The Wallbox output must be treated as an electrical waveform, not as a
  pre-decoded selection code.
- Full-wave rectification without smoothing produces many rapid transitions;
  those transitions can still be grouped reliably in software.
- Motor speed, contact condition, mechanical bounce, and selector direction
  affect the timing seen by the decoder.
- The exact Wallbox variant and signal conductors must be identified before
  connecting any sensing circuit.
- Galvanic isolation and current limiting are mandatory when interfacing the
  vintage 25 VAC circuitry to 3.3 V electronics.

## Safety boundary

Do not apply an assumed voltage to another Wallbox or connect its conductors
directly to Pico GPIO, USB ground, or a computer. Confirm the model, serial
variant, signal voltage, and conductor functions first. Use the final as-built
documentation only as a reference for this measured installation.

## Source

- Seeburg Wall-O-Matic Type 3W-1 Service Manual, pp. 2–11, Figures 2 and 15–17.
