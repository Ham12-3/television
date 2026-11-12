"""
export.py - writes all CAD and mesh files into output/.

    output/step/<part>.step              wall-mount parts (for Fusion 360 etc.)
    output/step/tv_wall_mount.step       wall-mount assembly with dummy screws
    output/step/tv/<item>.step           every television item
    output/step/television_complete.step the whole set: TV, mount, remote, feet
    output/stl/<name>.stl                meshes in assembly position (for the viewer)
    output/stl_print/<part>.stl          wall-mount parts laid on the bed, for a slicer
    output/stl/manifest.json             what the viewer shows: names, groups, colours

Run:  python export.py              everything
      python export.py --mount      only the wall mount (fast)
"""

import json
import sys
from pathlib import Path

import trimesh
from build123d import Color, Compound, export_step, export_stl

import config as cfg
from assembly import COLOURS, build_assembly, build_hardware, build_parts
from printing import (
    PRINT_ROTATION_X, STL_ANGULAR_TOLERANCE, STL_TOLERANCE, base_name, orient_for_print,
)

ROOT = Path(__file__).parent
STEP_DIR = ROOT / cfg.OUT_STEP
STL_DIR = ROOT / cfg.OUT_STL
PRINT_DIR = ROOT / "output" / "stl_print"
TV_STEP_DIR = STEP_DIR / "tv"

# The TV has far more geometry than the mount and is only looked at, never
# printed, so its meshes can be coarser.
TV_STL_TOLERANCE = 0.08
TV_STL_ANGULAR_TOLERANCE = 0.35

# Exploded-view movement of the wall-mount parts (x, y, z) in mm.
MOUNT_EXPLODE = {
    "wall_plate": (0, 0, 0),
    "tv_plate": (0, 30, 0),
    "lock_clip": (0, 12, -45),
    "cable_clip": (0, 12, -45),
}


def write_stl(part, path: Path, tolerance=STL_TOLERANCE, angular=STL_ANGULAR_TOLERANCE):
    """Write a binary STL and read it back so we report what is really on disk."""
    export_stl(part, str(path), tolerance=tolerance, angular_tolerance=angular)
    return trimesh.load_mesh(str(path))


def export_mount(manifest: dict) -> int:
    """Wall-mount parts: STEP, viewer STL and print-ready STL. Returns problem count."""
    parts = build_parts()
    problems = 0
    print(f"{'Wall-mount part':18s} {'STEP':>8s} {'STL':>8s} {'Triangles':>10s}  Watertight")
    print("-" * 62)
    for name, part in parts.items():
        step_path = STEP_DIR / f"{name}.step"
        stl_path = STL_DIR / f"{name}.stl"
        export_step(part, str(step_path))
        mesh = write_stl(part, stl_path)
        problems += not mesh.is_watertight

        # Print-ready copy. The two cable clips are identical, so only one
        # print file is written; print it CABLE_CLIP_COUNT times.
        kind = base_name(name)
        if not name.endswith(tuple(f"_{i}" for i in range(2, 10))):
            print_mesh = write_stl(orient_for_print(name, part), PRINT_DIR / f"{kind}.stl")
            problems += not print_mesh.is_watertight

        box = part.bounding_box()
        manifest["parts"].append({
            "name": name,
            "group": "Wall mount",
            "file": f"{name}.stl",
            "colour": [round(c, 3) for c in COLOURS[kind]],
            "opacity": 1.0,
            "explode": list(MOUNT_EXPLODE[kind]),
            "visible": True,
            "size_mm": [round(box.size.X, 2), round(box.size.Y, 2), round(box.size.Z, 2)],
            "mass_g": round(part.volume * cfg.PETG_DENSITY * 1000, 1),
            "note": "3D printed PETG",
            "print_file": f"../stl_print/{kind}.stl",
            "print_rotation_x_deg": PRINT_ROTATION_X[kind],
        })
        print(f"{name:18s} {step_path.stat().st_size / 1024:6.0f}kB {stl_path.stat().st_size / 1024:6.0f}kB "
              f"{len(mesh.faces):10d}  {'yes' if mesh.is_watertight else 'NO'}")
    export_step(build_assembly(include_hardware=True), str(STEP_DIR / "tv_wall_mount.step"))
    print("-" * 62)
    return problems


def export_tv(manifest: dict) -> int:
    """Every television item: STEP and viewer STL. Returns problem count."""
    from tv_assembly import build_tv, mass_properties

    print("Building the television ...")
    items = build_tv()
    mass, centre = mass_properties(items)
    manifest["tv"] = {
        "diagonal_inch": cfg.TV_DIAGONAL_INCH,
        "size_mm": [cfg.TV_WIDTH, cfg.TV_DEPTH, cfg.TV_HEIGHT],
        "mass_kg": round(mass, 2),
        "centre_of_mass_from_wall_mm": round(float(centre[1]), 1),
    }

    # Board and net data: the viewer draws the circuit boards from this, part
    # by part, so every component can be clicked and explained.
    from tv import netlist
    electrical = netlist.export()
    (STL_DIR / "boards.json").write_text(json.dumps(electrical))
    board_titles = {b["title"] for b in electrical["boards"]}

    problems, triangles = 0, 0
    children = []
    print(f"{'Television item':32s} {'Solids':>6s} {'Triangles':>10s}  Watertight")
    print("-" * 62)
    for item in items:
        stl_path = STL_DIR / f"{item.name}.stl"
        export_step(item.shape, str(TV_STEP_DIR / f"{item.name}.step"))
        mesh = write_stl(item.shape, stl_path, TV_STL_TOLERANCE, TV_STL_ANGULAR_TOLERANCE)
        problems += not mesh.is_watertight
        triangles += len(mesh.faces)

        box = item.shape.bounding_box()
        manifest["parts"].append({
            "name": item.name,
            "group": item.group,
            "file": f"{item.name}.stl",
            "colour": [round(c, 3) for c in item.colour],
            "opacity": item.opacity,
            "explode": list(item.explode),
            "visible": item.fitted or item.group == "Remote control",
            "size_mm": [round(box.size.X, 2), round(box.size.Y, 2), round(box.size.Z, 2)],
            "mass_g": round(item.mass_g(), 1),
            "count": len(item.solids()),
            "note": item.note,
            # Circuit boards are drawn in detail by the viewer from boards.json;
            # their STL files are still written for other tools.
            "procedural": item.group in board_titles,
            "nets": electrical["item_nets"].get(item.name, []),
            "role": electrical["item_role"].get(item.name, ""),
        })
        item.shape.label = item.name
        item.shape.color = Color(*item.colour, item.opacity)
        children.append(item.shape)
        print(f"{item.name:32s} {len(item.solids()):6d} {len(mesh.faces):10d}  "
              f"{'yes' if mesh.is_watertight else 'NO'}")
    print("-" * 62)
    print(f"{len(items)} items, {triangles} triangles in total")

    # One STEP file with everything in it.
    mount = list(build_parts().values()) + list(build_hardware().values())
    complete = STEP_DIR / "television_complete.step"
    export_step(Compound(label="television_complete", children=mount + children), str(complete))
    print(f"Complete assembly: {complete.relative_to(ROOT)} ({complete.stat().st_size / 1e6:.1f} MB)")
    return problems


def main() -> int:
    for folder in (STEP_DIR, STL_DIR, PRINT_DIR, TV_STEP_DIR):
        folder.mkdir(parents=True, exist_ok=True)

    manifest = {"units": "mm", "up_axis": "Z", "parts": []}
    problems = export_mount(manifest)

    if "--mount" in sys.argv:
        # Keep the television entries from the last full export.
        old = STL_DIR / "manifest.json"
        if old.exists():
            previous = json.loads(old.read_text())
            manifest["parts"] += [p for p in previous["parts"] if p.get("group") != "Wall mount"]
            if "tv" in previous:
                manifest["tv"] = previous["tv"]
    else:
        print()
        problems += export_tv(manifest)

    (STL_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print()
    print(f"Viewer manifest: {(STL_DIR / 'manifest.json').relative_to(ROOT)} "
          f"({len(manifest['parts'])} entries)")
    print("RESULT: PASS" if problems == 0 else f"RESULT: FAIL ({problems} mesh problem(s))")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
