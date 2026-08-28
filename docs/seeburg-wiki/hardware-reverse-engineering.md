---
title: hardware-reverse-engineering
page_type: workflow
topics:
  - hardware
  - contacts
  - safety
confidence: medium
updated: 2026-08-26 America/Chicago
---

# Hardware Reverse Engineering

## 3W-1 manual findings

### Working pulse legend

The current working interpretation is that the first pulse group carries
both the number and which letter in a pair was selected. The second group
identifies the letter pair:

| Second group | Letter pair |
| ---: | :--- |
| 1 pulse | A/B |
| 2 pulses | C/D |
| 3 pulses | E/F |
| 4 pulses | G/H |
| 5 pulses | J/K |

For the first group, 2–11 pulses select numbers 1–10 on the pair's first
letter (`pulses - 1`), while 12–21 pulses select numbers 1–10 on its second
letter (`pulses - 11`). For example, `B3` is first-group 14 (`11 + 3`) and
second-group 1, giving playlist slot 13. This remains a working hypothesis until several
known selections are recorded from the serial-25050 Wallbox.

The Type 3W-1 is not a passive matrix keypad. Its selection buttons latch mechanically, start a 25 VAC motor, and route the motor-driven selector-plate contact sequence into the jukebox’s Selection Receiver. The receiver interprets two pulse groups:

```text
first group: 2–21 pulses
approximately 0.2 s gap
second group: 1–5 pulses
individual pulse spacing: approximately 0.04 s
```

The manual’s simplified schematic shows a three-wire interface: blue, green, and orange. It labels orange as the grounded selection-circuit conductor and shows 25 VAC lighting/motor power between the other conductors. Isolation and current limiting remain mandatory.

The manual documents three circuit variants by serial range. In particular, units above serial 16645 use a three-blade latch-bar setting/carry-over arrangement, while earlier units use a separate motor switch arrangement. The project unit is stamped serial 25050, confirming that it belongs to the later variant. Compare the actual wiring against the corresponding schematic before testing.

## Required identification

- Wallbox model and serial information
- Jukebox model for which it was intended
- Connector type and pin labels
- Internal contact-stack and selector photographs
- Original schematic or service documentation, if available

## Initial investigation

1. Photograph and label every wire before disconnecting anything.
2. Determine the contact common/return paths with the unit unpowered.
3. Use continuity measurements to map selector positions.
4. Record enough selections to verify the two-group legend and its pulse counts.
5. Identify any latch, credit, trigger, home, or selection-complete contact.
6. Only then determine the required isolated sensing circuit.

## Safety constraints

Do not apply an assumed voltage to an unidentified Wallbox. Some units depend on the jukebox's relay and lamp circuitry, and the observed contact behavior may not be meaningful when powered independently. Use current limiting and galvanic isolation; confirm AC versus DC before choosing an input board.

## Expected decoder concerns

- Mechanical bounce
- Contact oxidation and intermittent closure
- Selector movement direction
- Repeated transitions while the dial spins
- Timeout and cancellation behavior
- A second selection before the first has been submitted

## Source

- [Seeburg Wall-O-Matic Type 3W-1 Service Manual](/Users/brianwis/Public/3w1.pdf), pp. 2–11, Figures 2, 15–17.

