---
title: parts-list
page_type: bill-of-materials
topics:
  - hardware
  - interface
  - decoder
confidence: high
updated: 2026-08-29 America/Chicago
---

# Parts List

This is the bill of materials for the as-built serial-25050 interface. The
electrical values below reflect the measured installation; verify the exact
optocoupler module and Wallbox signal before reproducing it.

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
| 1 | EL817/PC817-type optocoupler module | Isolated signal detection; input `+ INPUT -`, output `VCC OUT GND` | As built; verify module values |
| 1 | DB107 full-wave bridge rectifier | Rectifies Wallbox `SIGNAL`/`COMMON` AC | As built; no isolation by itself |
| 1 | 10 kΩ, 1/2 W resistor | External series current limiting on bridge `+` → module `INPUT+` | As built |
| 1 | Module input resistor, approximately 470 Ω | Part of purchased optocoupler module | Measured; verify before reproduction |
| 1 | Module output pull-up, approximately 10 kΩ | Module output-side pull-up | Measured; verify before reproduction |
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

## As-built one-channel interface

The following is the concrete first-pass set discussed for one sensing channel:

| Qty | Part | Connection/order | Notes |
| ---: | --- | --- | --- |
| 1 | DB107 full-wave bridge rectifier (or equivalent) | Wallbox `SIGNAL` and `COMMON` → bridge `~`, `~` | Bridge only rectifies; it does not isolate |
| 1 | EL817/PC817-type optocoupler module | `INPUT+` from external resistor, `INPUT−` to DB107 `−`; output side to Pico | Do not assume module internals |
| 1 | External 10 kΩ, 1/2 W resistor | DB107 `+` → module `INPUT+` | Required as installed |
| 1 | Pico 2 W | Module `VCC` → physical pin 36; `OUT` → GP15 / physical pin 20; `GND` → physical pin 38 | Logic side only |
| 1 | Enclosure / barrier terminals | Keep Seeburg-side circuit covered and separated | Required for safe installation |

The older 3.3 kΩ pair / bare-PC817 arrangement was a provisional prototype and is not the final installed wiring. The final circuit uses the purchased module's measured approximately 470 Ω input resistor plus the external 10 kΩ, 1/2-watt series resistor. The bridge and module input remain on the Seeburg side; the module output is the only signal crossing to the Pico logic side.

## Important qualification

The as-built values are specific to this 3W-1 installation and this optocoupler module. Verify the Wallbox voltage, module input resistor, output pull-up, terminal labels, insulation, and resistor dissipation before reproducing the circuit. Do not connect Seeburg COMMON to Pico GND.
