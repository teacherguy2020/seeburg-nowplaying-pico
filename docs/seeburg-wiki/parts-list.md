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

This is the hardware used for the working Seeburg 3W-1 → Raspberry Pi Pico 2 W interface.

The interface converts the approximately 25 VAC Seeburg selection signal into an optically isolated 3.3 V logic signal that can safely be read by the Pico.

## Required hardware

| Qty | Part | Purpose |
| ---: | --- | --- |
| 1 | Seeburg Wall-O-Matic 3W-1 | Source of the selection pulse train |
| 1 | Raspberry Pi Pico 2 W | Captures, decodes, and transmits Wallbox selections over Wi-Fi |
| 1 | DB107 full-wave bridge rectifier | Full-wave rectifies the Seeburg selection signal |
| 1 | EL817/PC817-type optocoupler module | Electrically isolates the Seeburg circuitry from the Pico |
| 1 | 10 kΩ, 1/2 W resistor | External current-limiting resistor for the optocoupler input |
| 1 | USB power supply | Powers the Pico 2 W |
| — | Hook-up wire / jumpers | Connections between components |

## Optocoupler module

The module used in the working prototype is an EL817/PC817-type optocoupler board with:

**Input side**

```text
+ INPUT -
```

**Output side**

```text
VCC OUT GND
```

Measurements of this particular module showed approximately:

| Component | Measured value |
| --- | ---: |
| Module input resistor | ~470 Ω |
| Module output pull-up | ~10 kΩ |

These values are important because inexpensive EL817/PC817 modules are not necessarily all constructed the same way.

The external **10 kΩ, 1/2 W resistor** was added in series with the module input because the module's built-in ~470 Ω resistor alone is not appropriate for the Seeburg's approximately 25 VAC signal.

## Electrical interface

The working signal path is:

```text
Seeburg SIGNAL
 │
 ├──────────────→ DB107 ~
 │
Seeburg COMMON
 │
 └──────────────→ DB107 ~

DB107 +
 │
 └── 10 kΩ / 1/2 W ──→ Optocoupler INPUT+

DB107 -
 │
 └───────────────────→ Optocoupler INPUT-
```

The isolated output side of the optocoupler connects to the Pico:

```text
Optocoupler VCC ──→ Pico 3V3(OUT)
 physical pin 36

Optocoupler OUT ──→ Pico GP15
 physical pin 20

Optocoupler GND ──→ Pico GND
 physical pin 38
```

## Isolation

The optocoupler provides the electrical isolation between the vintage Seeburg circuitry and the Pico.

```text
 SEEBURG SIDE PICO SIDE

SIGNAL ─┐
 ├─ DB107 ─ 10k ─ EL817 ║ VCC ── 3V3
COMMON ─┘ LED ║ OUT ── GP15
 ║ GND ── Pico GND
 ║
 optical isolation
```

**Do not connect Seeburg COMMON to Pico GND.**

There should be no direct electrical connection across the isolation barrier.

## No smoothing capacitor required

The working interface does **not** use a smoothing capacitor after the DB107.

Because the Seeburg signal is AC, the optocoupler output contains multiple fast transitions during each mechanical Wallbox pulse. The Pico captures those transitions and the decoder software groups them into electrical envelopes.

Measured timing from the working 3W-1 showed approximately:

| Signal feature | Typical measurement |
| --- | ---: |
| Normal electrical envelope | ~40–47 ms |
| Normal gap between envelopes | ~35–44 ms |
| Group separator | ~200–206 ms |
| Long left-side active envelope | ~865–870 ms |
| Right-side number landmark | ~120–125 ms |

Software filtering therefore replaces additional analog pulse-conditioning hardware in this implementation.

## Development / test equipment

These items were useful during development but are **not part of the finished interface**:

| Item | Use |
| --- | --- |
| Digital multimeter | Measuring Wallbox voltage, resistor values, and checking connections |
| Solderless breadboard | Temporary prototype wiring |
| Jumper wires | Prototype connections |
| Computer with USB | Installing MicroPython and programming/debugging the Pico |
| VS Code with MicroPico | Pico development environment |

## Optional permanent-installation hardware

The prototype can be made more permanent with:

- Small insulated enclosure
- Perfboard or other suitable circuit board
- Screw terminals or removable connectors
- Strain relief for incoming cables
- Heat-shrink tubing
- Wire labels

These are construction choices rather than electrical requirements of the decoder.

## Important reproduction note

This circuit was developed and tested with one particular Seeburg 3W-1 and one particular EL817/PC817 module.

Before reproducing it, verify:

1. The Wallbox signal voltage.
2. The optocoupler module's input resistor.
3. The optocoupler module's output pull-up.
4. The module terminal labels and polarity.
5. The value and power rating of the external current-limiting resistor.

Do not assume every inexpensive EL817/PC817 module has the same internal resistor values or terminal arrangement.

The essential working interface is simply:

```text
Seeburg SIGNAL + COMMON
 ↓
 DB107
 ↓
 external 10 kΩ / 1/2 W
 ↓
 EL817/PC817 optocoupler
 ↓
 Pico GP15
```

with the Seeburg and Pico sides remaining electrically isolated.
