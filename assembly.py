"""
assembly.py - builds every part and puts them together.

All parts are modelled in assembly coordinates, so "assembling" is just
collecting them. This file also adds simple dummy screws (for the STEP
assembly only) and checks that no two parts occupy the same space.

Use from other scripts:
    from assembly import build_parts, build_assembly

Run directly for a summary:
    python assembly.py
"""

import math

from build123d import Color, Compound, Cone, Cylinder, Pos, Rot

import config as cfg
from parts import cable_clip, lock_clip, tv_plate, wall_plate

# Display colours (R, G, B). The real parts are all matte black PETG; the
# different greys just make the parts easy to tell apart on screen.
COLOURS = {
    "wall_plate": (0.16, 0.16, 0.18),
    "tv_plate": (0.30, 0.30, 0.33),
    "lock_clip": (0.90, 0.45, 0.10),
    "cable_clip": (0.20, 0.50, 0.80),
    "hardware": (0.75, 0.75, 0.78),
}


def build_parts() -> dict:
    """Return the printed parts by name. Cable clips are numbered left to right."""
    parts = {
        "wall_plate": wall_plate.build(),
        "tv_plate": tv_plate.build(),
        "lock_clip": lock_clip.build(),
    }
    for i, x in enumerate(cfg.cable_clip_centres_x(), start=1):
        clip = cable_clip.build(x)
        clip.label = f"cable_clip_{i}"
        parts[clip.label] = clip
    for name, part in parts.items():
        part.color = Color(*COLOURS[name.rstrip("_0123456789")])
    return parts


def build_hardware() -> dict:
    """Dummy screws for visual reference. Bought, not printed."""
    hardware = {}

    # M4 socket cap screws: head in the air gap, thread going into the TV.
    n = 0
    for sx in (-1, 1):
        for sz in (-1, 1):
            n += 1
            x, z = sx * cfg.VESA_X / 2, sz * cfg.VESA_Z / 2
            y_seat = cfg.Y_TV_PLATE_BACK
            head = (Pos(x, y_seat - cfg.VESA_HEAD_HEIGHT / 2, z) * Rot(X=90)
                    * Cylinder(cfg.VESA_HEAD_DIA / 2, cfg.VESA_HEAD_HEIGHT))
            shank = (Pos(x, y_seat + cfg.VESA_SCREW_LENGTH / 2, z) * Rot(X=90)
                     * Cylinder(4.0 / 2, cfg.VESA_SCREW_LENGTH))
            screw = head + shank
            screw.label = f"vesa_screw_{n}"
            hardware[screw.label] = screw

    # Countersunk wall screws: head flush with the wall plate's front face.
    head_r = cfg.WALL_SCREW_HEAD_DIA / 2
    shank_r = cfg.WALL_SCREW_DIA / 2
    head_h = (head_r - shank_r) / math.tan(math.radians(cfg.WALL_SCREW_CSK_ANGLE / 2))
    n = 0
    for sx in (-1, 1):
        for sz in (-1, 1):
            n += 1
            x, z = sx * cfg.WALL_SCREW_SPACING_X / 2, sz * cfg.WALL_SCREW_SPACING_Z / 2
            y_top = cfg.Y_WALL_PLATE_FRONT
            head = Pos(x, y_top - head_h / 2, z) * Rot(X=90) * Cone(head_r, shank_r, head_h)
            shank = (Pos(x, y_top - cfg.WALL_SCREW_LENGTH / 2, z) * Rot(X=90)
                     * Cylinder(shank_r, cfg.WALL_SCREW_LENGTH))
            screw = head + shank
            screw.label = f"wall_screw_{n}"
            hardware[screw.label] = screw

    for screw in hardware.values():
        screw.color = Color(*COLOURS["hardware"])
    return hardware


def build_assembly(include_hardware: bool = True) -> Compound:
    """Everything as one labelled assembly, ready for STEP export."""
    children = list(build_parts().values())
    if include_hardware:
        children += list(build_hardware().values())
    return Compound(label="tv_wall_mount", children=children)


def overlap_volume(a, b) -> float:
    """Volume shared by two solids in mm^3 (0 if they only touch or are apart)."""
    try:
        common = a & b
    except Exception:
        return float("nan")
    if common is None:
        return 0.0
    try:
        return float(common.volume)
    except AttributeError:
        return float(sum(s.volume for s in common))


def check_interference(shapes: dict, tolerance: float = 0.01) -> list:
    """Compare every pair. Returns (name_a, name_b, overlap_mm3) for clashes."""
    names = list(shapes)
    clashes = []
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            box_a, box_b = shapes[a].bounding_box(), shapes[b].bounding_box()
            apart = (box_a.max.X < box_b.min.X or box_b.max.X < box_a.min.X
                     or box_a.max.Y < box_b.min.Y or box_b.max.Y < box_a.min.Y
                     or box_a.max.Z < box_b.min.Z or box_b.max.Z < box_a.min.Z)
            if apart:
                continue  # bounding boxes do not even touch; skip the slow check
            volume = overlap_volume(shapes[a], shapes[b])
            if not volume <= tolerance:  # also catches NaN
                clashes.append((a, b, volume))
    return clashes


def main() -> int:
    print("Building parts ...")
    parts = build_parts()
    hardware = build_hardware()

    print()
    print(f"{'Part':15s} {'X':>7s} {'Y':>7s} {'Z':>7s}  {'Volume':>10s} {'Mass':>7s}  Solid")
    print("-" * 68)
    total_mass = 0.0
    all_valid = True
    for name, part in parts.items():
        size = part.bounding_box().size
        mass_g = part.volume * cfg.PETG_DENSITY * 1000
        total_mass += mass_g
        one_solid = len(part.solids()) == 1 and part.is_valid
        all_valid &= one_solid
        print(f"{name:15s} {size.X:7.1f} {size.Y:7.1f} {size.Z:7.1f}  "
              f"{part.volume:8.0f}mm3 {mass_g:6.1f}g  {'ok' if one_solid else 'PROBLEM'}")
    print("-" * 68)
    print(f"Printed mass at 100 percent infill: {total_mass:.0f} g of {cfg.MATERIAL}")

    whole = Compound(children=list(parts.values()))
    box = whole.bounding_box()
    print(f"Printed envelope: {box.size.X:.1f} x {box.size.Y:.1f} x {box.size.Z:.1f} mm "
          f"(Y from {box.min.Y:.1f} to {box.max.Y:.1f}, Z from {box.min.Z:.1f} to {box.max.Z:.1f})")

    print()
    print("Interference check (printed parts and screws) ...")
    clashes = check_interference({**parts, **hardware})
    if clashes:
        for a, b, volume in clashes:
            print(f"  CLASH  {a} / {b}: {volume:.2f} mm3")
    else:
        print("  No two parts overlap.")

    ok = all_valid and not clashes
    print()
    print("RESULT: PASS" if ok else "RESULT: FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
