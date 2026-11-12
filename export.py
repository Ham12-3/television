"""
export.py - writes all CAD and mesh files into output/.

    output/step/<part>.step          one STEP per printed part (for Fusion 360 etc.)
    output/step/tv_wall_mount.step   full assembly, including dummy screws
    output/stl/<part>.stl            meshes in assembly position (used by the viewer)
    output/stl_print/<part>.stl      meshes laid on the bed, ready for a slicer
    output/stl/manifest.json         part list, colours and sizes for the web viewer

Run:  python export.py
"""

import json
from pathlib import Path

import trimesh
from build123d import export_step, export_stl

import config as cfg
from assembly import COLOURS, build_assembly, build_parts
from printing import (
    PRINT_ROTATION_X, STL_ANGULAR_TOLERANCE, STL_TOLERANCE, base_name, orient_for_print,
)

ROOT = Path(__file__).parent
STEP_DIR = ROOT / cfg.OUT_STEP
STL_DIR = ROOT / cfg.OUT_STL
PRINT_DIR = ROOT / "output" / "stl_print"


def write_stl(part, path: Path) -> trimesh.Trimesh:
    """Write a binary STL and read it back so we report what is really on disk."""
    export_stl(part, str(path), tolerance=STL_TOLERANCE,
               angular_tolerance=STL_ANGULAR_TOLERANCE)
    return trimesh.load_mesh(str(path))


def main() -> int:
    for folder in (STEP_DIR, STL_DIR, PRINT_DIR):
        folder.mkdir(parents=True, exist_ok=True)

    print("Building parts ...")
    parts = build_parts()
    manifest = {"units": "mm", "up_axis": "Z", "parts": []}
    problems = 0

    print()
    print(f"{'Part':15s} {'STEP':>8s} {'STL':>8s} {'Triangles':>10s}  Watertight")
    print("-" * 60)
    for name, part in parts.items():
        step_path = STEP_DIR / f"{name}.step"
        stl_path = STL_DIR / f"{name}.stl"
        export_step(part, str(step_path))
        mesh = write_stl(part, stl_path)
        problems += not mesh.is_watertight

        # Print-ready copy. The two cable clips are identical, so only one
        # print file is written; print it CABLE_CLIP_COUNT times.
        kind = base_name(name)
        print_path = PRINT_DIR / f"{kind}.stl"
        if not name.endswith(tuple(f"_{i}" for i in range(2, 10))):
            print_mesh = write_stl(orient_for_print(name, part), print_path)
            problems += not print_mesh.is_watertight

        box = part.bounding_box()
        manifest["parts"].append({
            "name": name,
            "file": f"{name}.stl",
            "colour": [round(c, 3) for c in COLOURS[kind]],
            "size_mm": [round(box.size.X, 2), round(box.size.Y, 2), round(box.size.Z, 2)],
            "volume_mm3": round(part.volume, 1),
            "mass_g": round(part.volume * cfg.PETG_DENSITY * 1000, 1),
            "print_file": f"../stl_print/{kind}.stl",
            "print_rotation_x_deg": PRINT_ROTATION_X[kind],
        })
        print(f"{name:15s} {step_path.stat().st_size / 1024:6.0f}kB {stl_path.stat().st_size / 1024:6.0f}kB "
              f"{len(mesh.faces):10d}  {'yes' if mesh.is_watertight else 'NO'}")
    print("-" * 60)

    assembly_path = STEP_DIR / "tv_wall_mount.step"
    export_step(build_assembly(include_hardware=True), str(assembly_path))
    print(f"Assembly STEP (with dummy screws): {assembly_path.relative_to(ROOT)} "
          f"({assembly_path.stat().st_size / 1024:.0f} kB)")

    (STL_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print(f"Viewer manifest: {(STL_DIR / 'manifest.json').relative_to(ROOT)}")
    print(f"Print-ready STLs: {PRINT_DIR.relative_to(ROOT)}"
          f" ({len(list(PRINT_DIR.glob('*.stl')))} files)")

    print()
    print("RESULT: PASS" if problems == 0 else f"RESULT: FAIL ({problems} mesh problem(s))")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
