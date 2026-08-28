---
title: datasync-adaptation
page_type: integration
topics:
  - datasync
  - wallbox-to-ipod
  - signal-tap
  - raspberry-pi
confidence: medium
updated: 2026-08-28 America/Chicago
---

# Data Sync Wallbox to iPod Adapter

## What the manual confirms

The Data Sync Engineering **Wallbox to iPod Adapter / WiPod II** explicitly supports the Seeburg Wall-O-Matic 3W1. It expects the Wallbox to be powered by a separate 25–30 VAC transformer and connects to the Wallbox with a two-wire signal/common pair. The adapter supplies the playlist translation and playback behavior internally.

For a 3W1, its playlist documentation describes the 100-selection order as:

```text
A1..A10 = playlist positions 1..10
B1..B10 = playlist positions 11..20
...
K1..K10 = playlist positions 91..100
```

Thus, under this numbering, `B3` is playlist position 13. The exact title-strip order should still be checked against the physical strips installed in this Wallbox.

Source: [`wallboxtoiPod.pdf`](/Users/brianwis/Public/wallboxtoiPod.pdf), pp. 1–5 and 9–11.

## Can it be adapted?

Yes, but the useful adaptation is to **share the Wallbox signal**, not to modify the Data Sync box or intercept its iPod audio.

```text
                         existing path
Wallbox 25 VAC signal ───────────────→ Data Sync adapter → iPod
       │
       └── isolated high-impedance tap → Pico decoder → Now Playing API
```

The manual does not document a digital output, serial port, diagnostic connector, or selection-event API on the Data Sync adapter. Its documented outputs are the iPod 30-pin connection and line-level RCA audio. Therefore, opening the adapter and trying to extract an internal decoded number is unnecessary and would require reverse engineering.

## Could the 30-pin port connect to the Pico?

Possibly, but not as a simple “song number” output.

The 30-pin socket is an iPod accessory interface. The adapter is probably acting as an iPod accessory/controller and exchanging commands and status with the iPod over one of the legacy accessory communication channels. The manual only says that it connects to the 30-pin dock connector; it does **not** document the pinout, voltage levels, message format, or whether the adapter uses the older serial accessory protocol, USB, or another Apple-specific mechanism.

That means there are two different concepts:

```text
Data Sync adapter → iPod: commands/status using an Apple accessory protocol
Data Sync adapter → Pico: not currently a documented interface
```

The adapter may send enough information to make the iPod select playlist item 13, but the Pico would need to passively decode those messages. Alternatively, the Pico could impersonate an iPod and receive the adapter’s commands, but then it would need to implement enough of the accessory handshake and status responses to keep the adapter operating. Neither approach is plug-and-play.

### How to investigate safely

Use a 30-pin breakout or sacrificial extension cable and a logic analyzer, not direct Pico wiring. First identify which pins are active while the adapter boots and while a Wallbox selection is made. Measure logic levels before connecting any GPIO. The connector also carries charging and power lines, including potentially hazardous-to-the-Pico 5 V/12 V rails.

Capture these sessions:

1. Adapter boot with an iPod attached.
2. One known Wallbox selection, such as `A1`.
3. A second selection, such as `B3`.
4. The same selections with the adapter’s debug playlist option enabled, if available.

If the captures contain a repeatable selection or playlist-position message, a Pico-based protocol decoder/client may be practical. If the adapter only sends opaque UI/navigation commands, or requires a full iPod authentication/handshake, the parallel Wallbox signal decoder remains much simpler and more robust.

The 30-pin experiment should therefore be treated as a separate reverse-engineering branch. Do not connect the port directly to a Pico until its active pins and voltage levels are known.

## Recommended prototype

1. Leave the working Data Sync wiring untouched.
2. Identify the two Wallbox signal wires at the existing connection point. Confirm that they are the 3W1 `SIGNAL` and `COMMON` pair, not the 25 VAC motor/lighting pair.
3. Add a removable parallel branch using a covered terminal block or Y-breakout.
4. Feed that branch into the isolated AC input stage described in the [interface schematic](interface-schematic.md). Use a bridge rectifier or AC-rated optocoupler as appropriate for the measured waveform.
5. Feed the isolated pulse output to the Pico. The Pico should decode the two pulse groups and emit the normalized selection, such as `B3` or slot `13`.
6. Compare the Pico’s decoded slot with the song selected by the Data Sync adapter. Use the Data Sync unit as a convenient known-good reference during commissioning.
7. Once the mapping is verified, have the Pico submit the playlist number directly to `POST /integrations/seeburg/selection` on `10.0.0.4:3101`. Use the endpoint's `dryRun` mode during commissioning; normal requests append the selected track without starting playback.

## Preferred physical tap point

The existing Data Sync wiring gives us the most useful practical discovery from this manual: the two wires already connected to the adapter’s labeled **Wallbox Connection** are the place to observe the Wallbox selection signal. For this 3W1 installation, those wires should correspond to `SIGNAL` and `COMMON`.

This avoids disturbing the selector mechanism or guessing at internal contact points. Add the new decoder as a parallel branch at that connection, preferably through a small removable terminal block. Verify the conductor identities against the Wallbox wiring and measure before energizing the decoder. The new branch must be a high-impedance, galvanically isolated input so the existing Data Sync adapter continues to see the same signal.

## Important electrical caution

The manual’s “2-wire Wallbox connection” does not mean the line is safe logic-level voltage. It states that the Wallbox signal is 25 VAC and recommends a 25–30 VAC, 2 A transformer, with an inline 1 A fuse. Measure the actual voltage and waveform at the signal/common pair before selecting resistor values or an optocoupler. Do not connect either Wallbox wire directly to Pico, Raspberry Pi, breadboard ground, USB ground, or an unisolated GPIO input.

The tap must be high impedance and electrically isolated so it cannot alter the current available to the existing Data Sync adapter or the Wallbox selector. Make the branch disconnectable, fuse the Wallbox supply as documented, and test with the Data Sync adapter disconnected before attaching the new decoder.

## Practical alternatives

### Parallel decoder tap — preferred first experiment

Advantages:

- preserves the existing working system
- does not require opening the Data Sync box
- gives us a known-good playback reference
- lets the new Now Playing path be tested independently

Limitations:

- both systems must observe the same Wallbox selection
- the tap must be designed so it does not load or distort the signal
- the Data Sync adapter remains a separate system until the new path is proven

### Internal Data Sync reverse engineering — later option

This could potentially expose an already-decoded selection, but it is not documented by the manual and may involve proprietary, fragile circuitry. It should only be considered if a parallel electrical tap cannot reliably decode the signal. Photographing connectors and identifying test points can come later; do not probe an energized unit casually.

### Use the Data Sync adapter as the permanent decoder — unlikely

Because its documented interface is audio playback to an iPod, it does not provide the track path or selection event needed by Now Playing. It can remain a useful fallback player and test oracle, but it is not presently a clean control-plane component.

## Next measurement

With the existing system powered and operating normally, identify where the two yellow adapter wires join the Wallbox signal/common pair. With an appropriately rated isolated meter or oscilloscope probe, record:

- idle voltage
- voltage during one known selection
- pulse polarity and duration
- whether the signal returns to zero between pulses
- whether the Data Sync adapter and the Wallbox share any other electrical connection

Do not cut the existing cable for this measurement. Use a temporary breakout or probe clips with insulated covers.

## Source

- [Data Sync Engineering Wallbox to iPod Adapter manual](/Users/brianwis/Public/wallboxtoiPod.pdf), pp. 1–5, 9–11.
- [3W-1 service manual](/Users/brianwis/Public/3w1.pdf), pp. 2–11.

