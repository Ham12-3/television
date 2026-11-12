# Design brief: 32 inch direct-lit LED television

This covers the television's mechanical design. The electrical design is in
[ELECTRICAL.md](ELECTRICAL.md); the wall mount is in [DESIGN.md](DESIGN.md).

**What this is.** A complete, code-driven 3D model of a 32 inch LED LCD
television: enclosure, LCD panel, backlight, steel chassis, six circuit boards
with their components, speakers, cables, stand feet, wall mount and remote
control. Every dimension is a named parameter in `config.py`; every component
on every board is a row in `tv/board_data.py`.

**What this is not.** It is a reference design to look at, learn from and build
on. It is not a real product, not copied from any manufacturer's set, and not
something a factory could build from. See "Limits" at the end.

## 1. Specification

| Item | Value |
|------|-------|
| Screen | 31.5 inch (32 inch class), 16:9, 1920 x 1080, picture area 698 x 393 mm |
| Technology | LCD with direct-lit LED backlight: 24 LEDs on 3 strips behind the panel |
| Outside size | 730 x 430 x 70 mm without feet |
| Bezel | 16 mm sides, 14 mm top, 23 mm bottom |
| Mass | About 5.7 kg (estimated from the model and typical material densities) |
| Mounting | VESA 100 x 100, M4, into four steel pillars on the chassis; or two stand feet |
| Inputs | 2 HDMI, 2 USB, antenna, composite video + stereo audio, Ethernet, Wi-Fi, Bluetooth |
| Outputs | 2 x 8 W speakers, optical digital audio, headphone |
| Power | 100-240 V AC, about 66 W maximum, under 0.5 W standby (target) |

## 2. How it is put together

From the front of the set to the back. Depth `w` is measured forward from the
rear cover's outer surface, so the front of the bezel is at w = 70 mm.

| Layer | From w | To w | Material | Job |
|-------|--------|------|----------|-----|
| Front bezel lip | 68.0 | 70.0 | ABS | Frames the screen, holds the glass in |
| LCD cell | 66.2 | 67.8 | Glass + polarisers | Forms the picture |
| Mould frame lip | 65.0 | 66.2 | Plastic | The glass rests on this |
| Optical films (3) | 64.15 | 64.9 | PET | Two prism sheets and a diffuser sheet: brighten and smooth the light |
| Diffuser plate | 62.65 | 64.15 | Polystyrene | Hides the individual LEDs |
| Optical cavity | 38.55 | 62.65 | Air | 24.1 mm for the light to spread |
| Reflector sheet | 38.25 | 38.55 | White PET | Sends stray light forward |
| LED strips | 37.25 | 38.25 | Aluminium PCB | 8 LEDs each, with a lens over every LED |
| Chassis floor | 36.65 | 37.25 | Steel 0.6 mm | The structural back of the panel; everything bolts to it |
| Board standoffs | 30.65 | 36.65 | Steel | 6 mm gap behind every board |
| Circuit boards | 29.05 | 30.65 | FR-4 1.6 mm | Components face the rear cover |
| Component space | 3.7 | 29.05 | Air | Tallest part allowed: 25.3 mm (tallest fitted: 22 mm) |
| Rear cover | 0.0 | 2.2 | ABS | Vents, connector recess, VESA holes |

## 3. What is behind the rear cover

Seen from the back, as in the `tv_inside.png` render:

| Item | Where | Size | Notes |
|------|-------|------|-------|
| Power supply board | Left of centre | 170 x 130 mm | Mains side nearest the inlet, outputs towards the main board |
| Main board | Right | 170 x 190 mm | Ports along the outside edge, in a recess in the rear cover |
| T-con board | Bottom, right of centre | 130 x 45 mm | Close to the source boards it feeds |
| LED driver board | Bottom, left of centre | 90 x 50 mm | Next to the hole where its harness enters the chassis |
| Wi-Fi / Bluetooth module | Top right | 40 x 26 mm | Away from the power supply |
| Source boards (2) | Along the bottom edge | 330 x 18 mm | Flat against the chassis, joined to the glass by 8 chip-on-film strips |
| Speakers (2) | Bottom corners | 110 x 32 x 26 mm | Fire downwards through grilles in the rear cover |
| IR / LED / key board | Behind the bottom bezel | 54 x 8.5 mm | The only board that faces the front |
| Mains inlet | Left side wall | 2-pin | Faces sideways so the plug clears the wall |
| VESA pillars (4) | Centre, 100 x 100 mm | 10 mm diameter | Carry the wall mount's load straight into the chassis |
| Cover pillars (7) | Round the edge | 7 mm diameter | The rear cover screws into these |

The centre of the back is kept clear of boards so the VESA pillars and the wall
mount have room.

## 4. Design decisions

- **Direct-lit backlight.** LEDs sit behind the panel, not along an edge. It
  needs a deeper set (the 24 mm cavity) but few LEDs and no light-guide plate.
- **Steel chassis as the backbone.** The panel stack sits in it, the boards
  stand off it, and the wall mount bolts to it. The plastic enclosure carries
  no load from the mount: the rear cover is only clamped between the mount
  plate and the pillars.
- **Side-facing connectors and mains inlet.** With the wall mount the back of
  the TV is 24 mm from the wall, so rear-facing plugs would not fit.
- **Draft on the rear cover.** Its side walls taper by 1 degree so the moulding
  can leave its tool. The front bezel is shallow and is modelled without draft.
- **Vents.** Intake slots low on each side of the rear cover, exhaust slots
  along the top, so warm air from the power supply and main board rises out.
- **Mains isolation.** The power supply board keeps 8 mm clear between its
  mains side and its output side, with a routed slot through the board.

## 5. The remote control

A 165 x 44 x 20 mm infrared remote: two shell halves, a battery door, a rubber
keypad with 11 keys, a PCB with a microcontroller, an infrared LED pointing out
of the front end, and two AAA cells. It talks to the IR receiver behind the
TV's bottom bezel. In the viewer it lies on the table in front of the set.

## 6. The stand feet

Two feet slot into the bottom of the rear cover for tabletop use. They are
200 mm front to back, so they cannot be fitted while the TV is on the wall
mount (they would pass through the wall). They are modelled, exported and
selectable in the viewer, but hidden by default and left out of the clash check.

## 7. Assumptions

| ID | Assumption |
|----|------------|
| T1 | Material densities are typical values, so the 5.7 kg mass is an estimate (a real 32 inch set of this type is usually 4 to 6 kg) |
| T2 | The LCD cell is one block of "glass"; its internal layers are not modelled |
| T3 | Row drivers are built into the glass (gate-on-array), so there are no gate boards |
| T4 | LED forward voltage 3.1 V at 350 mA; all 24 LEDs in one series string |
| T5 | Board component positions are a sensible arrangement, not a routed PCB |

## 8. Simplifications in the 3D model

- In the CAD files (STEP, STL) components are plain boxes and cylinders of the
  right size. The web viewer draws them in more detail (legs, cans, sockets,
  windings) and paints traces and silkscreen on the boards. Trace paths are
  illustrative: they join the right parts, but they are not a routed layout.
- Screw threads are not modelled. Threaded holes are drawn at the screw's
  nominal diameter.
- Cables are straight box segments along their routes; real ones curve.
- The wiring between LED strips inside the chassis is not drawn. The harness is
  shown as far as the hole where it enters.
- The speakers and the IR board are placed but their fixing clips are not drawn
  (the IR board rests against two posts on the bezel).
- The rear cover has no internal ribs, and the enclosure halves have no snap
  hooks along their join.
- The badge on the bezel is blank. This is not any real brand.

## 9. Limits

1. **Reference design only.** No tolerance analysis, no mould-flow, no drop,
   vibration or thermal testing has been done.
2. **The electrical side is block level.** No schematics or PCB layouts exist;
   see ELECTRICAL.md section 10. Do not build the mains power supply from this.
3. **No compliance work.** A real television must pass product-safety, EMC and
   radio certification.
4. **The mass and centre of mass feed the wall-mount calculation.** If you
   change the TV, re-run `python validate.py`; it checks the mount is still
   rated for the TV as modelled.
