---
title: isolated-input-stage
page_type: hardware-interface
topics:
  - isolation
  - optocoupler
  - 25-vac
  - pico
confidence: medium
updated: 2026-08-28 America/Chicago
---

# Isolated Input Stage

The isolated input stage is the electrical boundary between the Seeburg/Data Sync Wallbox signal and the low-voltage Pico decoder.

```text
Data Sync terminals
  SIGNAL ──┐
           │  Wallbox-side circuit
  COMMON ──┘
       ↓
current-limiting resistors
       ↓
AC optocoupler
       ║  isolation barrier
       ║
Pico-side optocoupler output
       ↓
3.3 V pull-up
       ↓
Pico GPIO input
```

## First prototype

The Data Sync adapter exposes one two-wire Wallbox input, so the first prototype should use one isolated sensing channel. The Pico can distinguish the two Wallbox pulse groups by timing.

The two wires currently connected to the Data Sync adapter connect to a removable, enclosed terminal block:

- `WB_SIGNAL`
- `WB_COMMON`

This is a parallel connection. The Data Sync box remains connected and operating normally. The Wallbox wires must not be connected directly to a solderless breadboard.

## Wallbox-side circuit

The signal passes through appropriately rated resistors before reaching the optocoupler input. The resistors limit current and protect both the Wallbox circuit and the optocoupler.

The Data Sync manual indicates a nominal 25 VAC signal, approximately 35 V peak. Final resistor values must be calculated from the measured voltage and waveform. A pair of flameproof resistors in series with an AC optocoupler is a candidate topology, not a final wiring instruction.

An AC-input optocoupler such as an H11AA1 is a candidate because its antiparallel LEDs sense both halves of the AC waveform. A bridge rectifier followed by a conventional optocoupler is an alternative. Use one approach or the other, not both.

## Bridge-rectifier alternative

The two Wallbox wires may be connected to the two AC-marked `~` terminals of a suitably rated bridge rectifier:

```text
WB_SIGNAL ───────── bridge ~
WB_COMMON ───────── bridge ~

                       bridge + ── resistor network ── optocoupler LED ── bridge −
```

This is acceptable only as the **Wallbox-side portion** of the sensing circuit. The bridge does not provide isolation and must not be connected directly to Pico ground, a Pico GPIO, USB ground, or any other logic circuit. The optocoupler remains the isolation barrier.

The bridge offers two practical benefits:

- it makes the downstream LED current one-directional;
- it allows use of an ordinary optocoupler instead of an AC-input optocoupler.

It also introduces two diode drops and does not regulate the voltage. The resistor network must therefore be sized from the measured peak voltage, the bridge forward drop, the optocoupler LED current requirement, and the resistor power rating. Use a bridge with voltage and surge-current ratings comfortably above the measured Wallbox signal. Never connect the bridge `+` or `−` terminals directly to the Pico.

Because this branch is connected in parallel with the working Data Sync adapter, verify that the bridge/resistor/optocoupler branch draws little enough current that the existing adapter still operates normally. Start with the Wallbox unpowered, check for wiring errors and shorts, then test with current-limited instrumentation before normal operation.

## Concrete first-pass wiring order

For the one-channel breadboard prototype, wire in this order after the signal has been measured and the parts have been checked:

1. Put the two wires that already serve the Data Sync Wallbox input on a removable terminal block labeled `WB_SIGNAL` and `WB_COMMON`. This is a parallel tap; the Data Sync adapter stays connected.
2. Connect `WB_SIGNAL` and `WB_COMMON` to the DB107 bridge rectifier’s two terminals marked `~`. Verify the markings on the part rather than relying on its orientation.
3. Connect DB107 `+` to the first 3.3 kΩ resistor, then the second 3.3 kΩ resistor in series, then to the PC817 LED anode (pin 1 on the common DIP-4 pinout).
4. Connect the PC817 LED cathode (pin 2 on the common DIP-4 pinout) to DB107 `−`.
5. On the other side of the PC817, connect the emitter (commonly pin 3) to Pico `GND`.
6. Connect the collector (commonly pin 4) to the chosen Pico GPIO. This is one junction, not a series path.
7. Connect one lead of the 10 kΩ pull-up resistor to Pico `3V3` and its other lead to that same GPIO/collector junction.
8. Power and test only the Pico-side circuit first. The GPIO should be high when the optocoupler is off and should be pulled low while the Wallbox signal turns the optocoupler on.

```text
Wallbox SIGNAL ───── DB107 ~
Wallbox COMMON ───── DB107 ~

DB107 + ── 3.3 kΩ ── 3.3 kΩ ── PC817 LED anode
DB107 − ─────────────────────── PC817 LED cathode

Pico 3V3 ── 10 kΩ ──┬── Pico GPIO
                    └── PC817 collector
Pico GND ─────────────── PC817 emitter
```

The first four connections are Wallbox-side and must be enclosed or mounted on a separated interface board. Only the PC817 transistor, 10 kΩ pull-up, Pico GPIO, Pico ground, and optional indicator belong on the low-voltage breadboard. Never connect DB107 `+` or `−` to Pico ground or GPIO.

## Isolation barrier

The optocoupler provides the safety boundary:

- Wallbox-side wires and Pico-side ground remain electrically separate.
- Pulses are detected optically.
- No Wallbox voltage reaches the Pico.
- The Data Sync adapter is not electrically exposed to the Pico circuit.

Use suitable creepage and clearance, insulated terminals, strain relief, and a covered enclosure. Do not place the Wallbox-side wiring on the solderless breadboard.

## Pico-side circuit

If using the purchased PC817 module rather than a bare PC817 DIP, its isolated output side is typically labeled `VCC`, `GND`, and `OUT`. Connect it as follows, after confirming the module documentation says its output accepts 3.3 V:

```text
Module VCC ── Pico physical pin 36 (3V3(OUT))
Module GND ── Pico GND
Module OUT ── chosen Pico GPIO, such as GP15
```

`VCC` is the module's supply input; it does not connect to the GPIO. `OUT` is the only module signal connection to the GPIO. The module output is commonly active-low: the GPIO is high when no Wallbox pulse is present and is pulled low when the optocoupler detects a pulse. The module's output-side `GND` may connect to Pico ground because this is the logic side of the isolation barrier. Do not connect the module's input-side ground or the DB107 terminals to Pico ground.

On a standard Raspberry Pi Pico/Pico 2 W, physical pin 36 is `3V3(OUT)`. Confirm the pinout for the exact Pico board before powering the module. If the module requires more than 3.3 V on `VCC`, do not connect it to pin 36; use a separately verified supply and confirm that `OUT` is safe for a 3.3 V GPIO.

The optocoupler transistor acts as a switch:

```text
Pico 3.3 V ── 10 kΩ pull-up ── GPIO input
                              │
                    optocoupler transistor
                              │
                         Pico GND
```

When the Wallbox signal is present, the optocoupler pulls the GPIO low. When it disappears, the pull-up returns the GPIO high. There is no shared ground between the Wallbox side and Pico side.

A small capacitor may eventually suppress brief noise spikes, but heavy filtering should wait until timing tests are complete. Excessive filtering could distort the Wallbox pulses.

## Pico capture behavior

The Pico should initially record raw transitions rather than immediately trying to control playback:

1. Interrupt on each GPIO edge.
2. Timestamp every transition.
3. Group pulses separated by approximately 40 ms.
4. Recognize the approximately 200 ms gap between the two pulse groups.
5. Reject implausibly short or long pulses.
6. Save the raw trace for diagnosis.

After the traces are understood, the decoder can emit an event such as:

```json
{
  "pulseGroups": [14, 1],
  "selection": "B3",
  "playlistNumber": 13
}
```

The Pico should submit the `playlistNumber` directly to the authenticated Now
Playing endpoint:

```http
POST http://10.0.0.4:3101/integrations/seeburg/selection
X-Track-Key: <existing Now Playing track key>
Content-Type: application/json

{"number":13,"dryRun":true}
```

The API validates the number, resolves it against the saved `Seeburg Playlist`,
and appends the selected file without starting playback. The read-only
`GET /integrations/seeburg/playlist` endpoint provides the current mapping.

## Build boundary

The breadboard should contain the Pico, optocoupler output, pull-up resistor, optional indicator LED, and test headers. The Wallbox terminal, AC-side resistors, protection components, and isolation barrier belong in a covered interface section and should eventually move to perfboard or a small enclosure.

## Open electrical measurements

Do not finalize component values until these are measured at the Data Sync `SIGNAL/COMMON` terminals:

- idle voltage;
- voltage during a selection;
- AC or DC waveform and polarity;
- pulse duration and spacing;
- whether the signal returns fully to zero between pulses;
- whether adding the sensing branch changes Data Sync operation.

The nominal 25 VAC value comes from the Data Sync manual, but the actual signal at this installation must be verified before connecting the optocoupler circuit.

## Related pages

- [Data Sync adaptation](datasync-adaptation.md)
- [Interface schematic](interface-schematic.svg)
- [Parts list](parts-list.md)
- [Wiring build procedure](wiring-build-procedure.md)
