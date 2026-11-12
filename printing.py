"""
printing.py - how each part sits on the print bed, and a printability check.

The parts are modelled in assembly coordinates (Y = out from the wall). For
printing, each one is turned so its flat face is on the bed and Z is up, then
checked for:
  - overhangs steeper than MAX_OVERHANG_ANGLE (would need supports)
  - flat "ceilings" wider than MAX_BRIDGE (would sag)
  - fit on the print bed

Use from other scripts:
    from printing import orient_for_print, check_printability

Run directly for a report:
    python printing.py
"""

import math
import tempfile
from pathlib import Path

import numpy as np
import trimesh
from build123d import Pos, Rot, export_stl

import config as cfg

# Rotation about the X axis, in degrees, that puts each part on the bed.
#   +90 : the wall-side face (low Y) goes down
#   -90 : the TV-side face (high Y) goes down
PRINT_ROTATION_X = {
    "wall_plate": 90,    # wall face on the bed, cleat rail pointing up
    "tv_plate": -90,     # TV face on the bed, cleat hook pointing up
    "lock_clip": 90,     # flat on its side, layers run along the arms
    "cable_clip": 90,    # flat back on the bed, ring opening facing up
}

# Mesh fineness used for every STL in the project.
STL_TOLERANCE = 0.02          # mm, max gap between the mesh and the true surface
STL_ANGULAR_TOLERANCE = 0.2   # radians


def base_name(name: str) -> str:
    """'cable_clip_2' -> 'cable_clip'."""
    return name.rstrip("_0123456789")


def orient_for_print(name: str, part):
    """Return a copy of the part rotated onto the bed, centred, sitting at Z = 0."""
    turned = Rot(X=PRINT_ROTATION_X[base_name(name)]) * part
    box = turned.bounding_box()
    centre = box.center()
    return Pos(-centre.X, -centre.Y, -box.min.Z) * turned


def to_mesh(part) -> trimesh.Trimesh:
    """Triangulate a CAD part (via a temporary STL) for mesh-based checks."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "part.stl"
        export_stl(part, str(path), tolerance=STL_TOLERANCE,
                   angular_tolerance=STL_ANGULAR_TOLERANCE)
        return trimesh.load_mesh(str(path))


def _patches(mesh: trimesh.Trimesh, face_ids: np.ndarray) -> list[np.ndarray]:
    """Group the given faces into connected patches (faces sharing an edge)."""
    if len(face_ids) == 0:
        return []
    wanted = np.zeros(len(mesh.faces), dtype=bool)
    wanted[face_ids] = True
    adjacency = mesh.face_adjacency
    keep = wanted[adjacency[:, 0]] & wanted[adjacency[:, 1]]
    return trimesh.graph.connected_components(
        adjacency[keep], nodes=face_ids, min_len=1, engine="scipy")


def check_printability(mesh: trimesh.Trimesh) -> dict:
    """Analyse a mesh that is already in print orientation (Z up, bed at Z = 0).

    Returns a dict with:
      steep_area   - mm^2 of surface steeper than the overhang limit (not flat)
      steepest     - worst overhang angle found, degrees from vertical
      bridges      - list of (span_mm, length_mm, height_mm) for flat ceilings
      worst_bridge - widest ceiling span, mm
      size         - (x, y, z) printed size
      fits_bed     - True if it fits the configured bed
    """
    normals = mesh.face_normals
    areas = mesh.area_faces
    face_z = mesh.triangles_center[:, 2]

    # How far each face leans past vertical: 0 = vertical wall, 90 = flat ceiling.
    lean = np.degrees(np.arcsin(np.clip(-normals[:, 2], -1, 1)))
    off_bed = face_z > cfg.LAYER_HEIGHT / 2          # faces on the bed are fine
    tiny = 1.0                                       # degrees of meshing noise

    ceiling = off_bed & (lean > 90 - tiny)
    steep = off_bed & (lean > cfg.MAX_OVERHANG_ANGLE + tiny) & ~ceiling

    bridges = []
    for patch in _patches(mesh, np.nonzero(ceiling)[0]):
        if areas[patch].sum() < 0.5:
            continue                                 # slivers from meshing
        points = mesh.triangles[patch].reshape(-1, 3)
        extent = points.max(axis=0) - points.min(axis=0)
        span, length = sorted(extent[:2])
        bridges.append((float(span), float(length), float(points[:, 2].mean())))

    size = mesh.bounds[1] - mesh.bounds[0]
    fits = (min(size[0], size[1]) <= min(cfg.PRINT_BED_X, cfg.PRINT_BED_Y)
            and max(size[0], size[1]) <= max(cfg.PRINT_BED_X, cfg.PRINT_BED_Y)
            and size[2] <= cfg.PRINT_BED_Z)

    return {
        "steep_area": float(areas[steep].sum()),
        "steepest": float(lean[off_bed & ~ceiling].max()) if (off_bed & ~ceiling).any() else 0.0,
        "bridges": bridges,
        "worst_bridge": max((b[0] for b in bridges), default=0.0),
        "size": tuple(float(s) for s in size),
        "fits_bed": bool(fits),
    }


def main() -> int:
    from assembly import build_parts

    print("Printability report (parts in print orientation)")
    print("-" * 72)
    failed = 0
    for name, part in build_parts().items():
        if name.endswith("_2"):
            continue                                 # identical to cable_clip_1
        result = check_printability(to_mesh(orient_for_print(name, part)))
        sx, sy, sz = result["size"]
        checks = [
            (f"fits the {cfg.PRINT_BED_X:.0f} x {cfg.PRINT_BED_Y:.0f} x {cfg.PRINT_BED_Z:.0f} mm bed",
             result["fits_bed"], f"{sx:.1f} x {sy:.1f} x {sz:.1f} mm"),
            (f"no overhang steeper than {cfg.MAX_OVERHANG_ANGLE:.0f} deg",
             result["steep_area"] < 1.0,
             f"steepest {result['steepest']:.1f} deg, {result['steep_area']:.1f} mm2 over the limit"),
            (f"no bridge wider than {cfg.MAX_BRIDGE:.0f} mm",
             result["worst_bridge"] <= cfg.MAX_BRIDGE,
             f"{len(result['bridges'])} bridge(s), widest {result['worst_bridge']:.1f} mm"),
        ]
        print(base_name(name))
        for text, ok, detail in checks:
            failed += not ok
            print(f"  [{'PASS' if ok else 'FAIL'}] {text}  ({detail})")
    print("-" * 72)
    print("ALL PASS" if failed == 0 else f"{failed} FAILED")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
