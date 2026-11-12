"""
smoke_test.py - proves the CAD toolchain works on this machine.

Builds a plain TV-plate blank from config.py (rounded rectangle with the four
VESA holes), exports it to STEP and STL in a temporary folder, reads both back
and compares them. It writes nothing into output/. The real parts arrive in
step 3.

Run:  python smoke_test.py
"""

import math
import tempfile
from pathlib import Path

import trimesh
from build123d import (
    BuildPart, BuildSketch, Circle, GridLocations, Mode, Plane,
    RectangleRounded, export_step, export_stl, extrude, import_step,
)

import config as cfg


def tv_plate_blank():
    """Rounded plate standing in the XZ plane, thickness along +Y, VESA holes."""
    with BuildPart() as part:
        # Outline. Plane.XZ's normal points to -Y, so a negative extrude
        # amount grows the plate towards +Y (away from the wall).
        with BuildSketch(Plane.XZ):
            RectangleRounded(cfg.TV_PLATE_WIDTH, cfg.TV_PLATE_HEIGHT, cfg.CORNER_RADIUS)
        extrude(amount=-cfg.PLATE_THICKNESS)

        # Four VESA clearance holes, cut straight through.
        with BuildSketch(Plane.XZ):
            with GridLocations(cfg.VESA_X, cfg.VESA_Z, 2, 2):
                Circle(cfg.hole_dia(cfg.VESA_SCREW) / 2)
        extrude(amount=-cfg.PLATE_THICKNESS, mode=Mode.SUBTRACT)
    return part.part


def expected_volume() -> float:
    """Hand-calculated volume of the blank, to compare with the CAD kernel."""
    w, h, r, t = cfg.TV_PLATE_WIDTH, cfg.TV_PLATE_HEIGHT, cfg.CORNER_RADIUS, cfg.PLATE_THICKNESS
    outline = w * h - (4 - math.pi) * r * r
    holes = 4 * math.pi * (cfg.hole_dia(cfg.VESA_SCREW) / 2) ** 2
    return (outline - holes) * t


def main() -> int:
    results = []  # (description, passed, detail)

    plate = tv_plate_blank()
    size = plate.bounding_box().size
    results.append((
        "Plate builds with the configured size",
        abs(size.X - cfg.TV_PLATE_WIDTH) < 1e-6
        and abs(size.Y - cfg.PLATE_THICKNESS) < 1e-6
        and abs(size.Z - cfg.TV_PLATE_HEIGHT) < 1e-6,
        f"{size.X:.1f} x {size.Y:.1f} x {size.Z:.1f} mm",
    ))
    results.append((
        "Plate grows towards +Y from the wall plane",
        abs(plate.bounding_box().min.Y) < 1e-6,
        f"Y from {plate.bounding_box().min.Y:.1f} to {plate.bounding_box().max.Y:.1f} mm",
    ))
    results.append((
        "CAD volume matches the hand calculation",
        abs(plate.volume - expected_volume()) < 1.0,
        f"{plate.volume:.0f} vs {expected_volume():.0f} mm^3",
    ))

    with tempfile.TemporaryDirectory() as tmp:
        step_path = Path(tmp) / "blank.step"
        stl_path = Path(tmp) / "blank.stl"
        export_step(plate, str(step_path))
        export_stl(plate, str(stl_path))

        reloaded = import_step(str(step_path))
        results.append((
            "STEP export reads back with the same volume",
            abs(reloaded.volume - plate.volume) < 1.0,
            f"{reloaded.volume:.0f} mm^3",
        ))

        mesh = trimesh.load_mesh(str(stl_path))
        results.append((
            "STL export is a watertight mesh",
            bool(mesh.is_watertight),
            f"{len(mesh.faces)} triangles",
        ))
        results.append((
            "STL volume is within 0.5 percent of the CAD volume",
            abs(mesh.volume - plate.volume) / plate.volume < 0.005,
            f"{mesh.volume:.0f} mm^3",
        ))

    print("Toolchain smoke test")
    print("-" * 60)
    for text, ok, detail in results:
        print(f"[{'PASS' if ok else 'FAIL'}] {text}  ({detail})")
    failed = sum(not ok for _, ok, _ in results)
    print("-" * 60)
    print("ALL PASS" if failed == 0 else f"{failed} FAILED")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
