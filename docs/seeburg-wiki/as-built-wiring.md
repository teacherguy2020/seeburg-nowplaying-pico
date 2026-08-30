---
title: as-built-wiring
page_type: hardware-record
topics:
  - seeburg
  - wallbox
  - pico
  - isolation
  - wiring
confidence: high
updated: 2026-08-29 America/Chicago
---

# As-Built Seeburg 3W-1 → Pico 2 W Interface

This is the final wiring record for the Seeburg Wall-O-Matic 3W-1 interface used by this project. It documents the measured installation and the particular EL817/PC817-type optocoupler module used. Reproduction requires verifying the actual module resistor values and the signal at the individual Wallbox; do not treat every breakout board as equivalent.

## Safety boundary

The Seeburg selection signal is approximately 25 VAC. It must not be connected directly to the Pico. A DB107 full-wave bridge rectifier and an EL817/PC817-type optocoupler module keep the vintage Seeburg circuitry electrically isolated from the Pico's 3.3 V logic.

**Do not connect Seeburg COMMON to Pico GND.** The DB107 `~`, `+`, and `−` terminals and the optocoupler module's `INPUT+`/`INPUT−` are on the Seeburg-side circuit. Only the module's `VCC`, `OUT`, and `GND` terminals are on the Pico-side circuit.

## Components

- Seeburg Wall-O-Matic 3W-1
- Raspberry Pi Pico 2 W
- DB107 full-wave bridge rectifier
- EL817/PC817-type optocoupler module
  - input terminals: `+ INPUT -`
  - output terminals: `VCC OUT GND`
  - measured module input resistor: approximately 470 Ω
  - measured module output pull-up: approximately 10 kΩ
- External 10 kΩ, 1/2-watt resistor in series with the optocoupler input

## Wiring

```text
SEEBURG 3W-1                         ISOLATED PICO SIDE

SIGNAL ───────────── DB107 ~          Module VCC ── Pico 3V3(OUT), pin 36
COMMON ───────────── DB107 ~          Module OUT ── Pico GP15, pin 20
                         │             Module GND ── Pico GND, pin 38
                    DB107 +
                         │
                    10 kΩ, 1/2 W
                         │
                    INPUT+
                 EL817 module
                    INPUT−
                         │
                    DB107 −

              OPTICAL ISOLATION BARRIER
```

The two Seeburg wires connect to the two DB107 `~` terminals. Their orientation does not matter because the bridge handles either AC polarity. The rectified path is `DB107 + → external 10 kΩ resistor → INPUT+`; `INPUT− → DB107 −`.

No smoothing capacitor is used. That is intentional: the Pico observes the rectified AC structure and reconstructs the slower mechanical Seeburg contact pulses in software.

## Why the external 10 kΩ resistor is required

The module's input resistor measured approximately 470 Ω, which is suitable for a low-voltage input but too low to place directly across the rectified Seeburg signal. A 25 VAC RMS signal can reach approximately 35.4 V peak after rectification:

```text
25 × √2 ≈ 35.4 V
```

The external resistor makes the approximate input resistance 10,470 Ω and limits the optocoupler LED current to a few milliamps. The resistor is rated 1/2 watt as installed. Verify dissipation and module construction before reproducing the circuit.

## What GP15 receives

Without a smoothing capacitor, GP15 does not receive one clean edge per mechanical pulse. Full-wave 60 Hz rectification creates rapid transitions, typically showing raw intervals around 7–8 ms, 1–2 ms, 7–8 ms, 1–2 ms. The firmware groups those transitions into electrical envelopes corresponding to the mechanical Seeburg pulses.

Observed timing from this Wallbox was approximately:

- normal pulse/envelope: 40–46 ms
- normal spacing: 35–44 ms
- group separator: 200–206 ms
- left-side letter long energized envelope: approximately 865–870 ms

Those measurements explain why the intentionally simple `Seeburg → DB107 → 10 kΩ → EL817 → GP15` path is sufficient; no regulator, Schmitt trigger, smoothing capacitor, or additional pulse-conditioning stage was ultimately required.

## Reproduction note

This interface was developed from the measured behavior of this particular 3W-1 and EL817 module. Confirm the module's input resistor, output pull-up, terminal labels, optocoupler polarity, resistor rating, and measured Wallbox voltage before applying power. Use suitable insulation, creepage/clearance, strain relief, and an enclosure for the Seeburg-side circuit.

## Related pages

- [Architecture](architecture.md)
- [Software integration](software-integration.md)
- [Parts list](parts-list.md)
