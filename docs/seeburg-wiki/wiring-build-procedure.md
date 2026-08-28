---
title: wiring-build-procedure
page_type: procedure
topics:
  - hardware
  - wiring
  - safety
  - prototype
confidence: low
updated: 2026-08-28 America/Chicago
---

# Wiring Build Procedure

This procedure describes the staged prototype wiring for the Seeburg 3W-1 Wallbox, serial 25050. It is a build plan, not permission to connect an unverified Wallbox circuit to a Raspberry Pi. The Wallbox wiring and sensing values must be measured first.

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

See the [photorealistic breadboard reference](components-wiring.html) and the [components and wiring flowchart](components-wiring.html) for the physical arrangement. The flowchart is conceptual; the steps below govern the actual build.

## Rules before wiring

- Keep the Wallbox conductors out of the solderless breadboard.
- Do not connect the Wallbox directly to Pico GPIO, Raspberry Pi GPIO, USB, or ground.
- Do not assume the blue, green, and orange wires are safe logic-level signals. The manual describes a 25 VAC system, but the actual sensing point and current must be verified.
- Use a covered, strain-relieved interface enclosure for the Wallbox cable, fuse, terminals, and isolation components.
- Disconnect power before changing wiring. Photograph and label every original connection before disturbing it.
- Treat the optocoupler channel count, resistor values, fuse rating, and GPIO assignments as provisional until measurements are recorded.

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
5. Do not choose `H11AA1`, resistor values, or a DC rectifier arrangement until these measurements are known.

## Stage 4 — Build the isolated input board

1. Install `TB1` so the Wallbox cable can be removed without disturbing the rest of the prototype.
2. Install the selected fuse and current-limiting network on the Wallbox side of the isolation boundary.
3. Install one isolated sensing channel per verified signal. Candidate parts are H11AA1 AC optocouplers or an appropriately rated alternative.
4. Route each optocoupler output to a separate low-voltage terminal, for example `ISO-A`, `ISO-B`, and `ISO-C`.
5. Keep input and output wiring physically separated. No Wallbox conductor should share a copper trace, breadboard row, or ground connection with the Pico side.
6. Label every terminal and photograph the completed board before applying power.

### One-channel bridge/PC817 prototype order

For the concrete parts currently being considered, the wiring order is:

1. Terminate the parallel Data Sync tap as `WB_SIGNAL` and `WB_COMMON` on a removable screw terminal.
2. Wire those terminals to the two DB107 terminals marked `~`.
3. Wire DB107 `+` through two series `3.3 kΩ, 0.5 W` resistors to the PC817 LED anode.
4. Wire the PC817 LED cathode back to DB107 `−`.
5. Keep this entire bridge/resistor/LED loop on the Wallbox side of the isolation boundary.
6. On the Pico breadboard, wire PC817 collector to a GPIO and emitter to Pico `GND`.
7. Wire a `10 kΩ` pull-up from Pico `3V3` to the collector/GPIO junction.
8. Test the Pico-side logic with the Wallbox disconnected before making the first live Wallbox test.

The 3.3 kΩ resistors must be 3.3 kilohms (`3K3`), not 3.3 ohms. The values are provisional: measure the actual signal and confirm optocoupler current, bridge loading, pulse shape, and resistor dissipation before finalizing the design.

## Stage 5 — Wire the logic-side breadboard

1. Mount the Pico 2 W on its breakout board across the breadboard center gap.
2. Connect the regulated 5 V supply to the appropriate Pico power input and breadboard power rails according to the Pico board documentation. Verify the board’s expected input voltage before connecting USB power.
3. Connect the isolated interface outputs `ISO-A`, `ISO-B`, and `ISO-C` to three Pico GPIO inputs.
4. Add the planned logic-side pull-up resistors to the Pico logic supply. Use one resistor per optocoupler output.
5. Add indicator LEDs only on the logic side, each with its own current-limiting resistor.
6. Add optional 100 nF capacitors only after observing the real pulse shape; excessive filtering can distort the approximately 40 ms pulse timing.
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
3. Default to `append`, which adds the selected track to the end of the cue.
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
- [ ] Direct API append tested without starting playback.

## Sources and related pages

- [Hardware reverse engineering](hardware-reverse-engineering.md)
- [Parts list](parts-list.md)
- [Provisional interface schematic](interface-schematic.html)
- [Components and wiring graphic](components-wiring.html)
- [Software integration](software-integration.md)
- [Seeburg Wall-O-Matic Type 3W-1 Service Manual](/Users/brianwis/Public/3w1.pdf), pp. 2–11, Figures 2 and 15–17.

