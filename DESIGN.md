# Design brief: 3D-printed fixed TV wall mount (32", VESA 100x100)

Status: **complete as a design, unproven as a product** (step 8). `validate.py`
passes all 91 checks, including the strength hand calculation in section 8
(lowest safety factor 6.2). Nothing has been printed or load-tested. Every number below is a named parameter in `config.py`. Anything marked **[A#]** is an assumption
I made because it was not specified; see the assumptions table.

## 1. Purpose

A low-profile, fixed (no tilt, no swivel) wall mount for a 32 inch television,
printed in PETG on an FDM printer. It must:

- carry the TV's weight on the wall with a large safety margin,
- let the TV be hung and removed **without tools** once the two plates are installed,
- leave a path for cables and keep them tidy,
- keep an air gap behind the TV and not block its rear vents,
- look minimal: rounded corners, plain faces, printed in matte black.

## 2. Concept

A two-plate **French cleat** mount. A 45 degree rail on the wall plate points up;
a matching 45 degree hook on the TV plate points down. Gravity pulls the TV plate
down and in towards the wall, so the joint tightens under load.

| # | Part | Qty | Role |
|---|------|-----|------|
| 1 | `wall_plate` | 1 | Screws to the wall. Carries the upward-facing cleat rail. |
| 2 | `tv_plate` | 1 | Bolts to the TV's VESA holes. Carries the downward-facing cleat hook. |
| 3 | `lock_clip` | 1 | Snap-in clip at the bottom that stops the TV being lifted off the cleat by accident. |
| 4 | `cable_clip` | 2 | Snap up into tunnels in the wall plate's lower rail and hold cables below it. |

The wall plate also carries a **lower rail**: two blocks near its bottom edge.
They act as a bumper so the TV plate hangs parallel to the wall, they stop the
lock clip, and each has a tunnel that a cable clip pushes into.

### How the lock clip works

The TV plate has a small **lock tab** near its bottom. The clip is pushed up
from below; its two arms pass either side of the tab and their barbs snap over
the top of it. If the TV is knocked upwards, the tab lifts the clip and the
clip's two stop posts hit the underside of the lower rail blocks.

The barbs have a 45 degree release ramp, so the clip comes out with a firm pull
on its finger tab. Estimated forces (cantilever snap-fit formulas, friction
coefficient 0.3, E = 2000 MPa): about 24 N to push in and about 42 N to pull
out. So lifting the TV off by accident needs its own weight plus roughly 42 N.
These are estimates; printed snap-fits vary a lot. The clip is a guard against
knocks, **not** a load-bearing or anti-theft part.

Bought hardware (shown as simple dummies in the assembly, not printed):
4x M4 machine screws into the TV, 4x wall screws with plugs suited to the wall.

### What "tool-free snap-fit" means here

Snap-fits are used only where a failure is harmless: the lock clip, the cable
clips, and hanging the TV on the cleat. The two structural joints stay screwed:

- **TV plate to TV**: VESA holes are threaded inserts, so M4 screws are the only correct fastener.
- **Wall plate to wall**: screws into studs or wall plugs. A snap-fit or adhesive here would be unsafe.

## 3. Key dimensions

Coordinates: X = left/right, Z = up, Y = out from the wall.

| Parameter | Value | Note |
|-----------|-------|------|
| VESA pattern | 100 x 100 mm | Per VESA FDMI MIS-D |
| VESA screw | M4, clearance hole 4.5 mm | ISO 273 medium fit is 4.5 mm |
| VESA screw length | 16 mm | 6 mm plate + about 10 mm in the TV **[A4]** |
| TV plate outline | 140 x 140 mm | 20 mm edge margin around the VESA holes |
| Wall plate outline | 160 x 130 mm | Narrowed from 180 mm when the wall screws moved inwards (section 8.6) |
| Plate base thickness | 6 mm | Both plates |
| Cleat angle | 45 degrees | Self-supporting when printed, self-tightening in use |
| Cleat depth | 12 mm | Rail and hook each fill the gap between the plates |
| Cleat vertical overlap | 12 mm | Follows from depth and angle; 6.6 mm of that is in contact after the tip flats |
| Cleat root height | 14 mm | Where the rail and hook join their plates. Sized by the strength calculation |
| Cleat length | 80 mm | Along X. Shortened from 120 mm so a screwdriver can reach the VESA screws |
| Cleat tip flat / groove fillet | 2.4 mm / 1 mm | No knife edges; the flat equals the minimum wall. Rounded groove lowers stress |
| Lower rail blocks | 2x, 43 x 8 mm, 34 mm notch between | Bumper, clip stop and cable-clip mounts |
| Wall-to-TV stack | 24 mm | 6 mm plate + 12 mm air gap + 6 mm plate |
| Wall screw holes | 4x, 5.5 mm clearance, countersunk | For 5 mm wood screws **[A3]** |
| Wall screw spacing | 120 x 90 mm | Close to the cleat to limit plate bending. Hidden behind the TV plate once the TV is hung |
| Cable window | 70 x 40 mm, through both plates | Centred, corners rounded to 8 mm |
| Vent slots | 6 mm wide, 3 mm ribs between | In the non-loaded areas of both plates only |
| Outer corner radius | 10 mm | |
| Edge fillet | 1.5 mm | On all exposed edges |
| Cable clip bore | 12 mm, 9 mm opening | Opening faces the TV, 1 mm short of the TV's back |
| Overall envelope | 160 x 163 x 24 mm | Plates are 160 x 140; the clips hang 23 mm below. Hidden behind a 32" TV (about 730 x 430 mm) **[A5]** |
| Printed mass | About 317 g at 100 percent infill | Wall plate 160 g, TV plate 144 g, clips 13 g |

## 4. Tolerances and print settings

| Item | Value |
|------|-------|
| General FDM tolerance assumed | +/- 0.2 mm |
| Cleat mating clearance | 0.3 mm per face |
| Snap-fit clearance (clips) | 0.2 mm per face |
| Screw clearance holes | Nominal clearance diameter + 0.2 mm printed-hole compensation |
| Minimum wall thickness | 2.4 mm (6 passes of a 0.4 mm nozzle) |
| Minimum rib between vent slots | 3.0 mm |
| Nozzle / layer height | 0.4 mm / 0.2 mm |
| Structural parts (both plates) | At least 5 perimeters, 60 percent or more gyroid infill |
| Maximum overhang | 45 degrees from vertical, no supports needed |
| Maximum unsupported bridge | 10 mm |
| Printer bed needed | 220 x 220 mm or larger **[A6]** |

### Print orientation (matters for strength)

FDM parts are much weaker between layers than along them, so orientation is a
design decision, not a slicer detail.

| Part | Orientation | Why |
|------|-------------|-----|
| `wall_plate` | Flat, wall face on the bed | Cleat slope is a 45 degree overhang; cable tunnels are 8 mm bridges |
| `tv_plate` | Flat, TV face on the bed, hook up | Same 45 degree slope; all holes are vertical |
| `lock_clip` | Flat on its side (8 mm tall) | Layers run along the flexing arms. Upright, the arms would snap |
| `cable_clip` | On its flat back | Layers run along the prongs; the ring's opening faces up |

**Changed from the step 1 draft.** I first recommended printing the plates on
edge so no load crosses a layer line. That is not needed: with the cleat root
sized in section 8 (80 x 14 mm), the stress there is 0.64 MPa against a
4.0 MPa between-layer allowable. On-edge printing would also turn the cable
window and vent slots into long unsupported bridges. Flat printing is therefore
the recommended orientation, and section 8 uses the between-layer strength for
the cleat.

### Design-for-manufacture details in the model

| Detail | Where | Value |
|--------|-------|-------|
| No supports needed | All parts | Steepest overhang is 45 degrees; checked by `printing.py` |
| Bridges | Cable-clip tunnels in the wall plate | 8 mm span, under the 10 mm limit |
| No draft angles | All parts | Draft is for moulding; FDM does not need it |
| Bed-side edges left sharp | Both plates, cable clip back | A fillet touching the bed curls and prints badly |
| Exposed perimeter fillet | Both plates | 1.5 mm, on the face away from the bed |
| Stress-relief fillets | Cleat grooves (1 mm), lock clip arm roots (1.2 mm) | Sharp inside corners crack first |
| Cleat tip flats | Rail and hook | 2.4 mm, so no knife edges and room for the groove fillet |
| Minimum wall | Plates 2.4 mm; snap-fit clips 1.6 mm | Measured by `validate.py`: plates 2.40 mm, lock clip 2.40 mm, cable clip 2.23 mm |
| Screw clearance | VESA M4: 4.7 mm; wall screws: 5.7 mm | ISO 273 medium fit plus 0.2 mm for printed-hole shrinkage |
| Countersinks | Wall screws | 90 degrees, 10 mm head, flush with the plate's front face |
| Snap-fit strain | Lock clip arms 1.33 percent, cable clip prongs 1.50 percent | Under a 2 percent limit for PETG |
| Mesh quality | All STLs | 0.02 mm chord tolerance, watertight |

## 5. Load and fit assumptions

| Item | Value |
|------|-------|
| Typical 32" TV mass | 4 to 6 kg |
| **Rated maximum TV mass** | **8 kg** **[A1]** |
| Design load | 8 kg x 9.81 = 78.5 N, static, vertical |
| Load offset from the wall | About 50 mm (bracket depth plus half the TV depth) **[A2]** |
| PETG tensile yield, in-plane, printed | 40 MPa (datasheet values run 45 to 50 MPa) |
| PETG strength between layers | 20 MPa (about 50 percent of in-plane) |
| Long-term (creep) allowable stress | 8 MPa, about 20 percent of yield |
| Target safety factor | 5 or more on the creep allowable for every load path |
| Service temperature | Under 50 degrees C at the TV back (PETG softens near 75 to 80 degrees C) |

The full hand calculation (cleat bending and shear, plate bending, bearing at
the screws, wall screw pull-out) is in section 8, with the safety factor for
each load path.

### Known limits, stated up front

- PETG **creeps**: a part that holds on day one can sag over months. The mount is
  for a light 32" TV only. It is not suitable for larger or heavier sets.
- Printed strength depends heavily on the printer, filament, moisture and
  settings. Hand calculations cannot capture that.
- Before trusting it: proof-load the installed mount with 3x the TV mass
  (about 15 to 24 kg of sandbags or water bottles) for 48 hours and inspect for
  cracks, whitening or sag. This is flagged again in the step 8 section.
- Not for use above a bed, cot or seating without a secondary safety tether.
- A proper FEA with orthotropic material data is recommended if this is ever
  made for anyone other than yourself.

## 6. How it attaches

1. Screw `wall_plate` to the wall with 4 screws, cleat rail pointing up, checked with a level.
2. Bolt `tv_plate` to the TV's VESA holes with 4x M4 screws, hook pointing down.
3. Plug in the cables and feed them through the cable window.
4. Lift the TV, lower the hook onto the rail. The 45 degree faces pull it to the wall.
5. Push `lock_clip` up from below until it clicks over the lock tab.
6. Push the two `cable_clip`s up into the lower rail (easier before step 4) and
   press the cables into them.

To remove: pull the lock clip down by its finger tab, lift the TV about 15 mm,
and pull it away.

**Access limit.** The lock clip sits about 120 mm above the bottom edge of a
32" TV, in a 24 mm gap. That is reachable with fingers but not comfortable; if
it proves awkward, lengthen `LOCK_CLIP_PULL_HEIGHT` in `config.py`.

## 7. Assumptions to confirm

| ID | Assumption | Why it matters | How to check |
|----|------------|----------------|--------------|
| A1 | TV weighs 8 kg or less without its stand | Sets every strength result | TV manual or spec sheet |
| A2 | TV is under 60 mm deep, centre of mass about 50 mm from the wall | Sets the overturning moment on the wall screws | Measure the TV |
| A3 | Wall takes 5 mm wood screws: timber stud, or masonry with plugs | Plain plasterboard alone is **not** acceptable for the upper screws | Find the studs or wall type |
| A4 | VESA threads are M4 with at least 10 mm usable depth, and the TV back is flat around the holes | Wrong screw length can damage the TV or leave the plate loose | TV manual; measure hole depth |
| A5 | No ports or vents sit directly behind the 140 x 140 mm TV plate area | The plate would block them | Look at the back of the TV |
| A6 | Printer bed is at least 220 x 220 mm | The 160 mm wall plate must fit in one piece (parts are only 18 mm tall when printed) | Printer spec |
| A7 | Matte black PETG, no post-processing | Cosmetic only | n/a |

## 8. Strength hand calculation

The same calculation is coded in `strength.py`, so the numbers below can be
regenerated after any change with `python strength.py`. Values here are for the
configuration as built: 8 kg TV, 80 mm cleat, 14 mm cleat root.

**Result: the lowest safety factor is 6.2, at the cleat root, against a target
of 5.** That figure is only as good as the assumptions and limits listed at the
end of this section.

### 8.1 Allowable stresses

PETG creeps, so the limit is a long-term stress, not the short-term strength.

| Direction | Short-term strength | Long-term allowable (20 percent) |
|-----------|--------------------|----------------------------------|
| Along the layers | 40 MPa | 8.0 MPa |
| Between layers | 20 MPa | 4.0 MPa |
| Shear | half of the above | 4.0 / 2.0 MPa |

These are typical printed-PETG figures, not measurements of your filament.

### 8.2 Loads

- Weight: W = 8 kg x 9.81 = **78.5 N**, straight down, 50 mm from the wall.
- Cleat, treated as a frictionless 45 degree wedge (worst case for the cleat):
  vertical V = 78.5 N, horizontal H = V / tan 45 = 78.5 N,
  normal force on the slope N = 111 N.
- Overturning: the weight acts 38 mm in front of the cleat contact, and the
  lower rail is 103 mm below it, so the lower rail pushes back with
  B = 78.5 x 38 / 103 = **29.0 N**. The same 29.0 N is the net pull on the wall
  at the cleat.

### 8.3 Load paths

| # | Load path | Working | Stress | Allowable | Safety factor |
|---|-----------|---------|--------|-----------|---------------|
| 1 | Bearing on the cleat slope | 111 N over 9.3 x 80 = 747 mm2 | 0.15 MPa | 8.0 | 54 |
| 2 | **Cleat root, bending + tension** | M = 78.5 x 6 + 78.5 x 13 = 1491 N.mm; Z = 80 x 14^2 / 6 = 2613 mm3; 0.57 + 78.5 / 1120 | **0.64 MPa** | 4.0 (between layers) | **6.2** |
| 3 | Cleat root, shear | 78.5 N over 80 x 14 = 1120 mm2 | 0.07 MPa | 2.0 | 29 |
| 4 | Wall plate bending at the end of the rail | M = 29.0 / 2 x 20 = 290 N.mm; Z = 45 x 6^2 / 6 = 270 mm3 | 1.07 MPa | 8.0 | 7.5 |
| 5 | VESA hole bearing, 4 screws sharing | 19.6 N over 4 x 6 = 24 mm2 | 0.82 MPa | 8.0 | 9.8 |
| 6 | VESA screw head on the plate | 10.2 N tension per top screw over 21 mm2 | 0.48 MPa | 8.0 | 17 |
| 7 | Wall screw hole bearing, 4 sharing | 19.6 N over 5 x 6 = 30 mm2 | 0.65 MPa | 8.0 | 12 |
| 8 | Wall screw head in the countersink | 17.3 N pull-out per top screw over 53 mm2 | 0.33 MPa | 8.0 | 25 |

Notes on the rows:

- **Row 2** applies to both the rail (wall plate) and the hook (TV plate); they
  are mirror images. Printed flat, the root is a layer plane, so the weaker
  between-layer allowable is used.
- **Row 4** treats the strip of plate above the cable window (45 mm tall) as a
  beam between the two top wall screws. The rail stiffens the middle, so the
  critical section is where the rail ends, 20 mm from the screws.
- **Rows 5 and 7** assume the screws share the load equally.

### 8.4 Pessimistic cases

| Case | Stress | Compared with | Factor |
|------|--------|---------------|--------|
| Only 2 of the 4 VESA screws carry the weight | 1.64 MPa | 8.0 MPa long-term | 4.9 |
| Cleat root peak stress, with an assumed stress concentration of 2.5 at the 1 mm groove fillet | 1.60 MPa | 20 MPa short-term, between layers | 12.5 |

The two-screw case falls just under 5. In practice the clamping friction under
tightened screws carries most of this load, but that is not relied on here.

### 8.5 Wall fixings

Each top wall screw sees about 19.6 N in shear and 17.3 N in pull-out. A 5 mm
wood screw with 30 mm or more in a timber stud, or a 6 mm plug in solid
masonry, holds many times that. **A plain plug in plasterboard does not have a
dependable margin**; use the studs or proper cavity anchors. The wall fixing is
outside what this calculation can verify.

### 8.6 What changed because of this calculation

The first version of the design did **not** pass. Two load paths were under the
target, and the design was changed:

| Load path | Before | Change | After |
|-----------|--------|--------|-------|
| Cleat root | 3.6 | Root height 10 mm to 14 mm; cable window shortened from 50 mm to 40 mm to make room | 6.2 |
| Wall plate bending | 3.9 | Wall screws moved in from 150 mm to 120 mm spacing; plate narrowed from 180 mm to 160 mm | 7.5 |

An earlier note in this document said the cleat root saw "well under 1 MPa"
with a 10 mm root. That was wrong: it left out the horizontal wedge force.

### 8.7 Limits: what this does not tell you

1. **It is a hand calculation.** Simple beam and bearing formulas, uniform load
   sharing, and an assumed stress concentration factor. Real stress fields at
   the cleat groove and around the holes are more complex.
2. **Material values are typical, not measured.** Printed PETG strength varies
   by a factor of two with filament brand, moisture, temperature, layer
   adhesion and infill. Between-layer strength is the least predictable.
3. **Creep is covered only by the 20 percent rule of thumb.** No creep data was
   used. A part can pass on day one and sag over months.
4. **Heat is not included.** PETG loses stiffness well below its 75 to 80
   degree C softening point. Behind a warm TV, or on a sunlit wall, margins
   shrink.
5. **Static load only.** No allowance for someone leaning on or bumping the TV,
   for vibration, or for impact.
6. **The wall is not checked.**
7. **Rated for 8 kg and a centre of mass within 50 mm of the wall.** A heavier
   or deeper TV scales the stresses up directly.

### 8.8 What must be checked by real testing or FEA

| Check | How | Pass criterion |
|-------|-----|----------------|
| **Proof load (do this before hanging a TV)** | Mount both plates as intended, hang 24 kg (3 x rated) from the TV plate at about 50 mm from the wall, leave for 48 hours | No cracks, whitening, layer separation or visible sag; plates still parallel |
| Creep | Leave 8 to 10 kg hanging for 2 weeks, measure the gap at the bottom of the plates at the start and end | Change under 0.5 mm |
| Cleat groove stress | FEA with orthotropic (layered) material properties, contact at the slope | Peak stress within the between-layer allowable |
| Snap-fit clips | Insert and remove each clip 20 times | No whitening or cracks at the arm roots; clip still clicks |
| Fit | Test-print the cleat section only (about 20 mm wide) before the full plates | Hook seats fully, 0.3 mm clearance not binding |
| Periodic inspection | Look at the cleat and screw areas after 1 week, 1 month, then yearly | No change |

Until the proof load is done, treat this mount as unproven. Do not use it above
a bed, cot or seating, and consider a secondary safety tether in any case.
