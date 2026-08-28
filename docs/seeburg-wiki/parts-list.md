---
title: parts-list
page_type: bill-of-materials
topics:
  - hardware
  - interface
  - decoder
confidence: low
updated: 2026-08-28 America/Chicago
---

# Parts List

This is a planning bill of materials for serial 25050. The interface values are intentionally not final until the Wallbox connector and contact waveforms are measured.

## Core hardware

| Qty | Part | Purpose | Status |
| ---: | --- | --- | --- |
| 1 | Raspberry Pi Pico 2 W | Deterministic contact capture and decoder | Recommended |
| 1 | Existing Now Playing Pi (`10.0.0.4`) | Hosts the deployed Seeburg selection endpoint and MPD integration | Already available |
| 1 | 5 V, 2 A UL-listed USB supply | Pico/interface power | Required |
| 1 | Small ventilated ABS enclosure | Isolated interface and decoder | Required |
| 1 | DIN/barrier terminal block set | Removable Wallbox harness | Required |
| 1 | 3-pin keyed connector and spare plug | Reversible connection to Wallbox | Required |
| 1 | 1 A slow-blow fuse holder and fuse | Protects the external Wallbox supply branch | Candidate |

## Isolation and sensing

| Qty | Part | Purpose | Status |
| ---: | --- | --- | --- |
| 1 | H11AA1 AC-input optocoupler, or approved equivalent | Sense the Data Sync two-wire signal/common pair | First prototype; validate waveform and current first |
| 2 | Flameproof resistor(s), initially around 4.7 kΩ, 0.5 W | Optocoupler AC-side current limiting | Value and arrangement TBD by measurement |
| 1 | Bridge rectifier plus standard optocoupler | Alternative to an AC-input optocoupler | Use one approach, not both |
| 1 | 10 kΩ pull-up resistor | Logic-side optocoupler output | Candidate; 3.3 V Pico logic |
| 1 | 100 nF capacitor | Optional logic-side noise filter | Fit only after timing tests |
| 1 | 4-channel or 8-channel logic-level interface board | Convenient Pico terminal breakout | Recommended |

## Test and installation items

| Qty | Part | Purpose |
| ---: | --- | --- |
| 1 | CAT III multimeter | Resistance and voltage checks |
| 1 | USB logic analyzer with isolated/low-voltage inputs | Capture decoded pulse timing |
| 1 | Current-limited adjustable AC source or isolation transformer | Controlled bench testing; only after wiring is identified |
| 1 | Hook-up wire, ferrules, heat-shrink, labels | Reversible harness |
| 1 | Cable strain relief and grommets | Protects the Wallbox cable |

## Prototyping platform

| Qty | Part | Purpose | Guidance |
| ---: | --- | --- | --- |
| 1 | Full-size solderless breadboard with power rails | Prototype Pico and logic-side circuitry | Use only for isolated low-voltage side |
| 1 | Pico 2 W solderless breakout board | Brings Pico pins to breadboard rows | Required if using a bare Pico |
| 1 | Breadboard jumper-wire kit | Logic-side connections | Prefer short, color-coded wires |
| 1 | 3-position screw-terminal breakout | Temporary Wallbox cable termination | Keep in a separate enclosed input area |
| 1 | Small perfboard or enclosed interface board | Permanent validated interface | Use instead of breadboard for final build |

The solderless breadboard is for the Pico, pull-ups, indicator LEDs, and other logic-side tests. Do not put the Wallbox’s 25 VAC conductors or an unverified contact circuit into the breadboard. Keep the input protection, fuse, terminals, and isolation components in a physically separate covered section; move the validated interface to perfboard or a suitable enclosure before regular use.

## Current prototype shopping list

The following is the concrete first-pass set discussed for one sensing channel:

| Qty | Part | Connection/order | Notes |
| ---: | --- | --- | --- |
| 1 | DB107 full-wave bridge rectifier (or equivalent) | Wallbox `SIGNAL` and `COMMON` → bridge `~`, `~` | Bridge only rectifies; it does not isolate |
| 2 | 3.3 kΩ, 0.5 W metal-film resistors | Bridge `+` → resistor → resistor → PC817 LED anode | 6.6 kΩ total; provisional starting value |
| 1 | PC817 optocoupler | LED side on bridge output; transistor side on Pico side | Confirm pinout on the actual package |
| 1 | 10 kΩ, 0.25–0.5 W resistor | Pico `3V3` → GPIO junction | External pull-up for PC817 collector |
| 1 | Pico 2 W with breakout | GPIO junction → selected GPIO; emitter → Pico `GND` | Logic-side breadboard only |
| 1 | Breadboard | PC817 transistor side, pull-up, Pico, test LED | Do not insert Wallbox wires directly |

The 3.3 kΩ parts must be marked `3.3 kΩ`, `3,300 Ω`, or `3K3`; `3.3 Ω` parts are a different component and must not be used. The bridge, series resistors, and PC817 LED remain on the Wallbox side of the isolation boundary. Confirm the actual voltage and current before treating these values as final.

## Important qualification

Do not purchase or install the optocoupler resistor network as a final circuit yet. The manual establishes the 25 VAC Wallbox system and pulse behavior, but not the safe sensing point for this individual unit. First identify the three conductors and measure the open-circuit voltage, contact current, and polarity/waveform with the Wallbox disconnected from any jukebox.

