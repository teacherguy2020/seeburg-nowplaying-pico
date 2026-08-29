---
title: wiring-build-procedure
page_type: procedure
topics:
  - hardware
  - wiring
  - safety
  - prototype
confidence: high
updated: 2026-08-29 America/Chicago
---

# Wiring Build Procedure

This procedure records the validated wiring for the Seeburg 3W-1 Wallbox, serial 25050. It is specific to the measured installation and the EL817/PC817-type module used here. See [As-built wiring](as-built-wiring.md) for the authoritative final circuit and safety boundary.

## Final signal path

```text
Seeburg Wallbox
  → 3-position terminal block
  → fuse and isolated sensing channels
  → Pico 2 W GPIO inputs on breadboard
  → Wi-Fi selection event
  → POST /integrations/seeburg/selection
  → Seeburg Playlist lookup and Now Playing append
```

See the [components and wiring diagram](components-wiring.svg), [interface schematic](interface-schematic.svg), and [as-built wiring record](as-built-wiring.md). The as-built record governs the final component values and pin connections.

## Rules before wiring

- Keep the Wallbox conductors out of the solderless breadboard.
- Do not connect the Wallbox directly to Pico GPIO, Raspberry Pi GPIO, USB, or ground.
- Do not assume the blue, green, and orange wires are safe logic-level signals. The manual describes a 25 VAC system, but the actual sensing point and current must be verified.
- Use a covered, strain-relieved interface enclosure for the Wallbox cable, fuse, terminals, and isolation components.
- Disconnect power before changing wiring. Photograph and label every original connection before disturbing it.
- Treat the final component values as specific to this installation; verify the optocoupler module's measured resistor values and terminal labels before reproducing it.

## Stage 1 — Document the Wallbox

1. Record the model and serial number. This project unit is marked `25050`, placing it in the later three-blade 3W-1 variant.
2. Photograph the connector, terminal strip, selector plate, contact stack, motor, latch assembly, and wire colors.
3. Label the three external conductors at the proposed interface end as `W-BLUE`, `W-GREEN`, and `W-ORANGE`. Do not rely on color alone after the cable enters the unit.
4. Draw the original connections before removing or adding anything.

## Stage 2 — Map the unpowered contacts

1. Leave the Wallbox disconnected from any jukebox or external supply.
2. Set a multimeter to continuity or resistance mode.
3. Identify which contacts close when a letter and number selection is made.
4. Rotate or operate the mechanism by hand only as appropriate for the service manual; do not force the selector.
5. Record common/return paths, normally open contacts, normally closed contacts, and any latch, motor, home, or selection-complete contact.
6. Create a table of observed contact transitions for several known selections. Do not yet assign them to Pico pins.

## Stage 3 — Measure the electrical behavior

1. Build the interface enclosure mechanically first: keyed connector, terminal block `TB1`, strain relief, fuse holder `F1`, and a physical barrier between Wallbox wiring and logic wiring.
2. Use the service documentation to identify the intended test points for the serial-25050 variant.
3. With the Wallbox disconnected from the Pico and Raspberry Pi, measure open-circuit voltage across the candidate conductors using an appropriately rated meter.
4. Determine whether the signal is AC, DC, or a switched relay/contact path. Record frequency, polarity if DC, and approximate current during a selection.
5. For this installation, the signal measured approximately 25 VAC while a selection was transmitted. Confirm that measurement for any different Wallbox or interface module.

## Stage 4 — Build the isolated input board

1. Install `TB1` so the Wallbox cable can be removed without disturbing the rest of the prototype.
2. Install the selected fuse and current-limiting network on the Wallbox side of the isolation boundary.
3. Install one isolated sensing channel per verified signal. Candidate parts are H11AA1 AC optocouplers or an appropriately rated alternative.
4. Route each optocoupler output to a separate low-voltage terminal, for example `ISO-A`, `ISO-B`, and `ISO-C`.
5. Keep input and output wiring physically separated. No Wallbox conductor should share a copper trace, breadboard row, or ground connection with the Pico side.
6. Label every terminal and photograph the completed board before applying power.

### Validated one-channel bridge/EL817 module order

For the concrete parts installed in this project, the wiring order is:

1. Terminate the parallel Data Sync tap as `WB_SIGNAL` and `WB_COMMON` on a removable screw terminal.
2. Wire those terminals to the two DB107 terminals marked `~`.
3. Wire DB107 `+` through the external `10 kΩ, 1/2 W` resistor to the module `INPUT+` terminal.
4. Wire the module `INPUT−` terminal back to DB107 `−`.
5. Keep the DB107 and module input loop entirely on the Wallbox side of the isolation boundary.
6. On the Pico side, connect module `VCC` to Pico physical pin 36 (`3V3(OUT)`), `OUT` to GP15 / physical pin 20, and `GND` to Pico GND / physical pin 38.
7. Do not connect Seeburg COMMON to Pico GND.
8. Test the Pico-side logic with the Wallbox disconnected before making the first live Wallbox test.

The module input resistor measured approximately 470 Ω and its output pull-up approximately 10 kΩ. Verify those values on the actual module before reproducing the circuit. No smoothing capacitor is used; the Pico decodes the rectified-AC transitions in software.

## Stage 5 — Wire the logic-side breadboard

1. Mount the Pico 2 W on its breakout board across the breadboard center gap.
2. Connect the regulated 5 V supply to the appropriate Pico power input and breadboard power rails according to the Pico board documentation. Verify the board’s expected input voltage before connecting USB power.
3. Connect the isolated module output `OUT` to Pico GP15 (physical pin 20); its `VCC` and `GND` go to Pico physical pins 36 and 38.
5. Add indicator LEDs only on the logic side, each with its own current-limiting resistor.
6. Do not add a smoothing capacitor to the validated circuit. The raw rectified-AC structure is part of the decoder's input and is intentionally interpreted in software.
7. Connect the Pico to the Now Playing API over Wi-Fi. The API receives the decoded playlist number; it does not need a shared ground with the Wallbox.

## Stage 6 — Test without the Wallbox

1. Leave `TB1` disconnected from the Wallbox.
2. Use switches or a safe signal generator on the isolated-interface output side to simulate clean pulses.
3. Confirm that the Pico detects edges, debounces them, separates the two pulse groups, and reports a selection such as `B3`.
4. Test malformed input: too few pulses, too many pulses, missing group, excessive gap, rapid repeat, and contact bounce.
5. Confirm that invalid decoded selections are rejected and reported without adding an unknown track.

## Stage 7 — First Wallbox test

1. Inspect the complete wiring against the photographs, terminal labels, and schematic. Check for shorts with power removed.
2. Connect the Wallbox to `TB1` with the logic equipment still unpowered.
3. Apply only the verified, current-limited Wallbox-side power arrangement. Stop immediately if the fuse opens, wiring heats, or the motor behaves unexpectedly.
4. Observe the isolated outputs with a meter or logic analyzer before enabling queue integration.
5. Make several known selections and compare captured pulse groups with the expected letter and number counts.
6. Only after the traces are repeatable should the Pico decoder be allowed to submit playlist numbers to the Now Playing API.

## Stage 8 — Connect to Now Playing

1. Configure the Pico with the authenticated Now Playing endpoint `http://10.0.0.4:3101/integrations/seeburg/selection` and the existing `X-Track-Key`.
2. Convert each decoded code to its one-based position in the fixed-order `Seeburg Playlist`.
3. The live API clears and starts the selected track when stopped/paused, and appends without interruption when already playing.
4. Use `{"number": 13, "dryRun": true}` first: log `B3 → playlist slot → track path` without changing the queue.
5. Test unknown and unavailable playlist entries. The API should report the problem and leave the existing cue unchanged.

## Sign-off checklist

- [ ] Serial-25050 wiring variant verified against the manual.
- [ ] All Wallbox wires photographed and labeled.
- [ ] Contact map and voltage/current measurements recorded.
- [ ] Fuse, resistor values, optocouplers, and channel count selected from measurements.
- [ ] Wallbox circuit is isolated from Pico and Raspberry Pi grounds.
- [ ] Breadboard contains logic-side wiring only.
- [ ] Simulated pulses decode correctly.
- [ ] Real Wallbox pulses are repeatable across several selections.
- [ ] Seeburg Playlist has a validated mapping for the available choices.
- [ ] Direct API dry-run tested.
- [ ] Direct API behavior tested in both stopped/paused (clear and start) and active (append without interruption) states.

## Sources and related pages

- [Hardware reverse engineering](hardware-reverse-engineering.md)
- [Parts list](parts-list.md)
- [Interface schematic](interface-schematic.svg)
- [As-built wiring](as-built-wiring.md)
- [Components and wiring graphic](components-wiring.svg)
- [Software integration](software-integration.md)
- [Seeburg Wall-O-Matic Type 3W-1 Service Manual](/Users/brianwis/Public/3w1.pdf), pp. 2–11, Figures 2 and 15–17.
