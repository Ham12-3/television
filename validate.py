"""
validate.py - checks the finished model and prints a pass / fail report.

It rebuilds the parts from config.py and also reads the exported STL files, so
it catches both design mistakes and stale exports.

Sections of the report:
  1. Solids and meshes    - valid single solids, watertight STLs, exports up to date
  2. Wall thickness       - thinnest material in each part vs the minimum
  3. Screw holes          - hole count, position and diameter vs the stated screws
  4. Fit to the TV        - VESA pattern, overall size, screw length
  5. Assembly behaviour   - nothing overlaps; cleat supports; lock clip locks
  6. Printability         - overhangs, bridges, bed size
  7. Strength             - safety factor of each load path (hand calculation)

Run:  python export.py     (first, so the STL files exist)
      python validate.py

Exit code is 0 if everything passes, 1 otherwise.
"""

import math
from pathlib import Path

import numpy as np
import trimesh
from build123d import GeomType, Pos

import config as cfg
import strength
from assembly import build_hardware, build_parts, check_interference, overlap_volume
from printing import base_name, check_printability, orient_for_print, to_mesh

ROOT = Path(__file__).parent
STL_DIR = ROOT / cfg.OUT_STL
PRINT_DIR = ROOT / "output" / "stl_print"

THICKNESS_SAMPLES = 4000     # random surface points tested per part
MEASURE_TOLERANCE = 0.05     # mm, allowance for mesh and rounding error


# ---------------------------------------------------------------------------
# Report plumbing
# ---------------------------------------------------------------------------
class Report:
    """Collects check results and prints them grouped by section."""

    def __init__(self):
        self.sections = []          # [(title, [(text, ok, detail), ...])]

    def section(self, title: str):
        self.sections.append((title, []))

    def check(self, text: str, ok: bool, detail: str = ""):
        self.sections[-1][1].append((text, bool(ok), detail))

    def print(self) -> int:
        failed = 0
        total = 0
        print("=" * 78)
        print("TELEVISION AND WALL MOUNT - VALIDATION REPORT")
        print("=" * 78)
        for title, checks in self.sections:
            print()
            print(title)
            print("-" * 78)
            for text, ok, detail in checks:
                total += 1
                failed += not ok
                tail = f"  ({detail})" if detail else ""
                print(f"  [{'PASS' if ok else 'FAIL'}] {text}{tail}")
        print()
        print("=" * 78)
        if failed:
            print(f"RESULT: FAIL - {failed} of {total} checks failed")
        else:
            print(f"RESULT: PASS - all {total} checks passed")
        print("=" * 78)
        return failed


# ---------------------------------------------------------------------------
# Wall thickness
# ---------------------------------------------------------------------------
def wall_thickness(mesh: trimesh.Trimesh, samples: int = THICKNESS_SAMPLES):
    """Measure material thickness at random points on the surface.

    From each point a ray is fired straight into the part (opposite to the
    surface normal). The distance to where it comes out the other side is the
    local thickness. Returns (thicknesses, points).

    Plain numpy ray / triangle intersection (Moller-Trumbore), so it needs no
    extra libraries. A fixed random seed makes the result repeatable.
    """
    points, face_ids = trimesh.sample.sample_surface(mesh, samples, seed=1)
    directions = -mesh.face_normals[face_ids]
    origins = points + directions * 1e-4            # start just under the skin

    v0 = mesh.triangles[:, 0]
    edge1 = mesh.triangles[:, 1] - v0
    edge2 = mesh.triangles[:, 2] - v0
    eps = 1e-9
    result = np.full(len(points), np.inf)

    chunk = 100                                     # rays per batch, limits memory
    for start in range(0, len(points), chunk):
        o = origins[start:start + chunk, None, :]
        d = directions[start:start + chunk, None, :]
        p = np.cross(d, edge2[None])
        det = np.einsum("ij,nij->ni", edge1, p)
        ok = np.abs(det) > eps
        inv = np.where(ok, 1.0 / np.where(ok, det, 1.0), 0.0)
        t_vec = o - v0[None]
        u = np.einsum("nij,nij->ni", t_vec, p) * inv
        q = np.cross(t_vec, edge1[None])
        v = np.einsum("nij,nij->ni", np.broadcast_to(d, q.shape), q) * inv
        t = np.einsum("ij,nij->ni", edge2, q) * inv
        hit = ok & (u >= -1e-6) & (v >= -1e-6) & (u + v <= 1 + 1e-6) & (t > 1e-3)
        result[start:start + chunk] = np.where(hit, t, np.inf).min(axis=1)
    return result, points


# ---------------------------------------------------------------------------
# Screw holes
# ---------------------------------------------------------------------------
def round_holes_along_y(part):
    """Find full circles whose axis is along Y. Returns {(x, z): set of diameters}.

    Looks at the CAD edges, not the mesh, so the diameters are exact. Arcs
    (fillets, slot ends) are skipped because they are not full circles.
    """
    holes = {}
    for edge in part.edges().filter_by(GeomType.CIRCLE):
        radius = edge.radius
        if abs(edge.length - 2 * math.pi * radius) > 1e-3:
            continue                                # an arc, not a full circle
        # Sample three points round the circle; if they share one Y value the
        # circle lies in an X-Z plane, so its axis is along Y. (Bounding boxes
        # are not used here: they grow slightly once a part has been meshed.)
        ys = [edge.position_at(t).Y for t in (0.0, 0.3, 0.6)]
        if max(ys) - min(ys) > 1e-4:
            continue
        c = edge.arc_center
        key = (round(c.X, 2), round(c.Z, 2))
        holes.setdefault(key, set()).add(round(2 * radius, 3))
    return holes


def check_hole_pattern(report, label, holes, spacing_x, spacing_z, expected_dia, screw_dia):
    """Check four holes on a rectangular pattern, with the right clearance."""
    expected = {(sx * spacing_x / 2, sz * spacing_z / 2) for sx in (-1, 1) for sz in (-1, 1)}
    found = {pos for pos, dias in holes.items()
             if any(abs(d - expected_dia) < MEASURE_TOLERANCE for d in dias)}
    report.check(f"{label}: 4 holes of {expected_dia:.1f} mm found",
                 len(found) == 4, f"found {len(found)}")
    report.check(f"{label}: holes are on the {spacing_x:.0f} x {spacing_z:.0f} mm pattern",
                 found == expected,
                 ", ".join(f"({x:+.0f},{z:+.0f})" for x, z in sorted(found)))
    clearance = expected_dia - screw_dia
    report.check(f"{label}: {screw_dia:.0f} mm screw passes with 0.3 to 1.0 mm clearance",
                 0.3 <= clearance <= 1.0, f"{clearance:.1f} mm on diameter")
    return found


# ---------------------------------------------------------------------------
# The checks
# ---------------------------------------------------------------------------
def check_solids_and_meshes(report, parts):
    report.section("1. Solids and meshes")
    for name, part in parts.items():
        report.check(f"{name}: CAD model is one valid solid",
                     part.is_valid and len(part.solids()) == 1,
                     f"{len(part.solids())} solid(s)")
        path = STL_DIR / f"{name}.stl"
        if not path.exists():
            report.check(f"{name}: STL file exists", False, "run python export.py")
            continue
        mesh = trimesh.load_mesh(str(path))
        report.check(f"{name}: STL is watertight with consistent normals",
                     mesh.is_watertight and mesh.is_winding_consistent and mesh.volume > 0,
                     f"{len(mesh.faces)} triangles")
        drift = abs(mesh.volume - part.volume) / part.volume
        report.check(f"{name}: STL on disk matches the current design",
                     drift < 0.005,
                     f"volume differs by {drift * 100:.2f} percent"
                     + ("" if drift < 0.005 else " - re-run python export.py"))
    for kind in sorted({base_name(n) for n in parts}):
        path = PRINT_DIR / f"{kind}.stl"
        ok = path.exists() and trimesh.load_mesh(str(path)).is_watertight
        report.check(f"{kind}: print-ready STL exists and is watertight", ok)


def check_wall_thickness(report, parts):
    report.section("2. Wall thickness")
    for name, part in parts.items():
        if name.endswith("_2"):
            continue                                # identical to cable_clip_1
        # Plates are structural; the clips are small snap-fit parts with
        # deliberately thin flexing arms, so they get the lower limit.
        structural = base_name(name) in ("wall_plate", "tv_plate")
        limit = cfg.MIN_WALL if structural else cfg.MIN_SNAP_WALL
        thickness, points = wall_thickness(to_mesh(part))
        thinnest = float(thickness.min())
        where = points[int(thickness.argmin())]
        report.check(
            f"{base_name(name)}: thinnest section >= {limit:.1f} mm",
            thinnest >= limit - MEASURE_TOLERANCE,
            f"{thinnest:.2f} mm at X={where[0]:.0f} Y={where[1]:.0f} Z={where[2]:.0f}, "
            f"{len(thickness)} points sampled")


def check_screw_holes(report, parts):
    report.section("3. Screw holes")
    vesa_dia = cfg.hole_dia(cfg.VESA_SCREW)
    screw_dia = float(cfg.VESA_SCREW[1:])
    check_hole_pattern(report, f"VESA {cfg.VESA_SCREW}", round_holes_along_y(parts["tv_plate"]),
                       cfg.VESA_X, cfg.VESA_Z, vesa_dia, screw_dia)
    report.check(f"VESA {cfg.VESA_SCREW}: clearance is the ISO 273 medium fit plus print allowance",
                 abs(vesa_dia - (cfg.CLEARANCE_HOLE[cfg.VESA_SCREW] + cfg.PRINTED_HOLE_COMP)) < 1e-6,
                 f"{cfg.CLEARANCE_HOLE[cfg.VESA_SCREW]:.1f} + {cfg.PRINTED_HOLE_COMP:.1f} mm")

    wall_holes = round_holes_along_y(parts["wall_plate"])
    wall_dia = cfg.WALL_SCREW_CLEARANCE + cfg.PRINTED_HOLE_COMP
    found = check_hole_pattern(report, "Wall screws", wall_holes,
                               cfg.WALL_SCREW_SPACING_X, cfg.WALL_SCREW_SPACING_Z,
                               wall_dia, cfg.WALL_SCREW_DIA)
    countersunk = sum(1 for pos in found
                      if any(abs(d - cfg.WALL_SCREW_HEAD_DIA) < MEASURE_TOLERANCE
                             for d in wall_holes[pos]))
    report.check(f"Wall screws: each hole has a {cfg.WALL_SCREW_HEAD_DIA:.0f} mm countersink",
                 countersunk == 4, f"{countersunk} of 4")


def check_fit_to_tv(report, parts):
    report.section(f"4. Fit to the TV ({cfg.TV_DIAGONAL_INCH} inch, "
                   f"VESA {cfg.VESA_X:.0f} x {cfg.VESA_Z:.0f})")
    low = np.min([[p.bounding_box().min.X, p.bounding_box().min.Y, p.bounding_box().min.Z]
                  for p in parts.values()], axis=0)
    high = np.max([[p.bounding_box().max.X, p.bounding_box().max.Y, p.bounding_box().max.Z]
                   for p in parts.values()], axis=0)
    size = high - low

    report.check("VESA pattern is a standard size for the screw",
                 (cfg.VESA_X, cfg.VESA_Z, cfg.VESA_SCREW) in
                 [(75, 75, "M4"), (100, 100, "M4"), (200, 100, "M4"), (200, 200, "M6"),
                  (300, 300, "M6"), (400, 400, "M6")],
                 f"{cfg.VESA_X:.0f} x {cfg.VESA_Z:.0f} with {cfg.VESA_SCREW}")
    # The VESA pattern is assumed to be centred on the TV (assumption A5).
    margin_x = cfg.TV_WIDTH / 2 - max(abs(low[0]), abs(high[0]))
    margin_top = cfg.TV_HEIGHT / 2 - high[2]
    margin_bottom = low[2] + cfg.TV_HEIGHT / 2
    report.check("Mount is hidden behind the TV, left and right",
                 margin_x >= 20, f"{margin_x:.0f} mm spare each side")
    report.check("Mount is hidden behind the TV, top",
                 margin_top >= 20, f"{margin_top:.0f} mm spare")
    report.check("Mount is hidden behind the TV, bottom (including clips)",
                 margin_bottom >= 20, f"{margin_bottom:.0f} mm spare")
    report.check("Nothing sticks into the wall or the TV",
                 low[1] >= -1e-6 and high[1] <= cfg.STACK_DEPTH + 1e-6,
                 f"Y from {low[1]:.1f} to {high[1]:.1f} mm, TV back at {cfg.STACK_DEPTH:.1f} mm")
    report.check("Stand-off from the wall matches the design",
                 abs(size[1] - cfg.STACK_DEPTH) < MEASURE_TOLERANCE, f"{size[1]:.1f} mm")
    tv_box = parts["tv_plate"].bounding_box()
    report.check("TV plate sits flush against the TV's back",
                 abs(tv_box.max.Y - cfg.STACK_DEPTH) < 1e-6, f"face at Y = {tv_box.max.Y:.1f} mm")
    engagement = cfg.VESA_SCREW_LENGTH - cfg.PLATE_THICKNESS
    screw_dia = float(cfg.VESA_SCREW[1:])
    report.check("VESA screw thread engagement is 1.5 to 3 screw diameters",
                 1.5 * screw_dia <= engagement <= 3 * screw_dia,
                 f"{engagement:.0f} mm in the TV with a {cfg.VESA_SCREW_LENGTH:.0f} mm screw")
    mass = sum(p.volume for p in parts.values()) * cfg.PETG_DENSITY
    report.check("Mount weighs less than 10 percent of the rated TV",
                 mass <= 0.1 * cfg.TV_MASS_MAX_KG, f"{mass * 1000:.0f} g vs {cfg.TV_MASS_MAX_KG:.0f} kg")


def check_assembly_behaviour(report, parts):
    report.section("5. Assembly behaviour")
    tv, wall, clip = parts["tv_plate"], parts["wall_plate"], parts["lock_clip"]

    clashes = check_interference({**parts, **build_hardware()})
    report.check("No parts or screws overlap", not clashes,
                 "; ".join(f"{a}/{b} {v:.1f} mm3" for a, b, v in clashes) or "0 clashes")

    gap = tv.distance(wall)
    report.check("Cleat hook rests on the cleat rail", gap < 0.01, f"gap {gap:.3f} mm")

    drop = overlap_volume(Pos(0, 0, -0.5) * tv, wall)
    report.check("Cleat stops the TV plate dropping", drop > 1.0,
                 f"a 0.5 mm drop would overlap the wall plate by {drop:.0f} mm3")

    lift = cfg.CLEAT_RISE + 1.0
    free = overlap_volume(Pos(0, 0, lift) * tv, wall)
    report.check("TV plate lifts clear of the rail for hanging and removal", free < 0.01,
                 f"lifted {lift:.0f} mm, overlap {free:.2f} mm3")

    blocked = overlap_volume(Pos(0, 0, 1.5) * tv, clip)
    report.check("Lock clip catches the lock tab when the TV is lifted", blocked > 0.1,
                 f"a 1.5 mm lift would overlap the clip by {blocked:.1f} mm3")

    stopped = overlap_volume(Pos(0, 0, 0.5) * clip, wall)
    report.check("Lower rail stops the lock clip rising", stopped > 0.1,
                 f"a 0.5 mm rise would overlap the wall plate by {stopped:.1f} mm3")

    for name in (n for n in parts if n.startswith("cable_clip")):
        down = overlap_volume(Pos(0, 0, -1.0) * parts[name], wall)
        report.check(f"{name}: barbs hold it in the lower rail", down > 0.05,
                     f"a 1 mm pull-down would overlap the rail by {down:.1f} mm3")


def check_printability_all(report, parts):
    report.section("6. Printability (FDM, no supports)")
    for name, part in parts.items():
        if name.endswith("_2"):
            continue
        kind = base_name(name)
        result = check_printability(to_mesh(orient_for_print(name, part)))
        sx, sy, sz = result["size"]
        report.check(f"{kind}: fits the print bed", result["fits_bed"],
                     f"{sx:.0f} x {sy:.0f} x {sz:.0f} mm")
        report.check(f"{kind}: no overhang steeper than {cfg.MAX_OVERHANG_ANGLE:.0f} deg",
                     result["steep_area"] < 1.0, f"steepest {max(result['steepest'], 0):.0f} deg")
        report.check(f"{kind}: no bridge wider than {cfg.MAX_BRIDGE:.0f} mm",
                     result["worst_bridge"] <= cfg.MAX_BRIDGE,
                     f"widest {result['worst_bridge']:.1f} mm")


def check_television(report):
    """Checks on the complete TV: layout, fit, clashes, mass and electrical budget."""
    import json

    from build123d import Pos as Move

    import electrical
    from tv.board_data import BOARDS, height, layout_problems
    from tv_assembly import all_shapes, build_tv, find_clashes, mass_properties

    report.section("8. Television: boards and stack-up")
    for board in BOARDS:
        problems = layout_problems(board)
        report.check(f"{board['title']}: no overlapping parts, none over a mounting hole",
                     not problems, "; ".join(problems[:3]) or f"{len(board['parts'])} parts")
    tallest = max((height(p), f"{b['title']} {p['ref']}") for b in BOARDS
                  if not b.get("faces_front") for p in b["parts"])
    report.check("Tallest component clears the rear cover",
                 tallest[0] <= cfg.MAX_COMPONENT_HEIGHT,
                 f"{tallest[1]} is {tallest[0]:.0f} mm, limit {cfg.MAX_COMPONENT_HEIGHT:.1f} mm")
    stack = [cfg.W_FRONT, cfg.W_LIP_BACK, cfg.W_CELL_FRONT, cfg.W_CELL_BACK, cfg.W_FRAME_LIP_BACK,
             cfg.W_FILMS_FRONT, cfg.W_FILMS_BACK, cfg.W_DIFFUSER_BACK, cfg.W_STRIP_TOP,
             cfg.W_TRAY_FLOOR, cfg.W_TRAY_BACK, cfg.W_PCB_FRONT, cfg.W_PCB_BACK, cfg.ENCLOSURE_WALL, 0.0]
    report.check("Layers are in order from front to back with no overlap",
                 all(a > b for a, b in zip(stack, stack[1:])),
                 f"{len(stack)} levels from {stack[0]:.1f} to {stack[-1]:.1f} mm")
    report.check("Optical cavity (LED to diffuser) is 20 to 35 mm",
                 20 <= cfg.OPTICAL_CAVITY <= 35, f"{cfg.OPTICAL_CAVITY:.1f} mm")
    led_pitch = cfg.LED_STRIP_LENGTH / cfg.LEDS_PER_STRIP
    report.check("LED spacing is no more than 4 times the cavity depth (even light)",
                 led_pitch <= 4 * cfg.OPTICAL_CAVITY,
                 f"{led_pitch:.0f} mm pitch, {cfg.OPTICAL_CAVITY:.1f} mm cavity")
    diag = math.hypot(cfg.ACTIVE_WIDTH, cfg.ACTIVE_HEIGHT) / 25.4
    report.check("Picture diagonal matches the stated size class",
                 abs(diag - cfg.TV_DIAGONAL_INCH) <= 0.6, f"{diag:.1f} inch")

    report.section("9. Television: 3D model")
    print("Building the television ...")
    items = build_tv()
    fitted = [i for i in items if i.fitted]
    bad = [i.name for i in items if not i.shape.is_valid]
    report.check("Every item is valid geometry", not bad, ", ".join(bad) or f"{len(items)} items")

    manifest_path = STL_DIR / "manifest.json"
    listed = {p["name"] for p in json.loads(manifest_path.read_text())["parts"]} if manifest_path.exists() else set()
    missing = [i.name for i in items if i.name not in listed or not (STL_DIR / f"{i.name}.stl").exists()]
    report.check("Every item has been exported for the viewer", not missing,
                 ", ".join(missing[:4]) or f"{len(items)} STL files")
    leaky = [i.name for i in items if (STL_DIR / f"{i.name}.stl").exists()
             and not trimesh.load_mesh(str(STL_DIR / f"{i.name}.stl")).is_watertight]
    report.check("Every exported mesh is watertight", not leaky, ", ".join(leaky[:4]) or "all closed")

    # Envelope. Small, deliberate protrusions are allowed for: screw heads at
    # the back, the button under the bezel, the badge on the front.
    half_x, half_z = cfg.TV_WIDTH / 2, cfg.TV_HEIGHT / 2
    y_back, y_front = cfg.STACK_DEPTH, cfg.STACK_DEPTH + cfg.TV_DEPTH
    outside = []
    for item in fitted:
        b = item.shape.bounding_box()
        if (b.min.X < -half_x - 0.01 or b.max.X > half_x + 0.01
                or b.min.Z < -half_z - 2.0 or b.max.Z > half_z + 0.01
                or b.min.Y < y_back - 2.01 or b.max.Y > y_front + 1.0):
            outside.append(item.name)
    report.check("Everything fitted sits inside the TV's outline", not outside,
                 ", ".join(outside) or f"{cfg.TV_WIDTH:.0f} x {cfg.TV_HEIGHT:.0f} x {cfg.TV_DEPTH:.0f} mm")

    shapes = all_shapes(items)
    print("Checking the television for clashes ...")
    clashes = find_clashes(shapes)
    report.check("No two items overlap (TV, wall mount and screws)", not clashes,
                 "; ".join(f"{a}/{b} {v:.1f} mm3" for a, b, v in clashes[:4])
                 or f"{len(shapes)} items compared")
    # Prove the clash check can fail: push the speakers 5 mm into the cover.
    planted = {"speakers": Move(0, 0, -5) * shapes["speakers"], "rear_cover": shapes["rear_cover"]}
    report.check("Clash check detects a deliberately planted overlap",
                 bool(find_clashes(planted)), "speakers moved 5 mm into the rear cover")

    report.section("10. Television: fit to the wall mount")
    report.check("Chassis pillars are on the same pattern as the mount's VESA holes",
                 True, f"both built from VESA_X = {cfg.VESA_X:.0f}, VESA_Z = {cfg.VESA_Z:.0f}")
    grip = cfg.VESA_SCREW_LENGTH - cfg.PLATE_THICKNESS - cfg.ENCLOSURE_WALL
    screw = float(cfg.VESA_SCREW[1:])
    report.check("Mount screws reach at least 1.5 diameters into the steel pillars",
                 grip >= 1.5 * screw, f"{grip:.1f} mm of thread in the pillar")
    gap = shapes["tv_plate"].distance(shapes["rear_cover"])
    report.check("Mount's TV plate sits flat on the rear cover", gap < 0.01, f"gap {gap:.3f} mm")
    mass, centre = mass_properties(items)
    report.check("TV is lighter than the mount's rated load",
                 mass <= cfg.TV_MASS_MAX_KG, f"{mass:.2f} kg estimated vs {cfg.TV_MASS_MAX_KG:.0f} kg rated")
    report.check("TV's centre of mass is no further out than the mount calculation assumes",
                 centre[1] <= cfg.LOAD_OFFSET_FROM_WALL,
                 f"{centre[1]:.1f} mm from the wall vs {cfg.LOAD_OFFSET_FROM_WALL:.0f} mm assumed")
    report.check("TV is balanced left to right on the mount",
                 abs(centre[0]) <= 15, f"centre of mass {centre[0]:+.1f} mm from the middle")

    report.section("11. Television: electrical budget (see electrical.py)")
    for text, ok, detail in electrical.checks():
        report.check(text, ok, detail)

    from tv import netlist
    gaps = netlist.problems()
    parts_total = sum(len(b["parts"]) for b in BOARDS)
    report.check("Every component is in the net list, and every net joins at least two things",
                 not gaps, "; ".join(gaps[:3]) or f"{parts_total} components, {len(netlist.NETS)} nets")
    boards_file = STL_DIR / "boards.json"
    exported = (sum(len(b["parts"]) for b in json.loads(boards_file.read_text())["boards"])
                if boards_file.exists() else -1)
    report.check("Board and net data exported for the viewer matches the design",
                 exported == parts_total, f"{exported} components in boards.json")


def main() -> int:
    print("Building parts from config.py ...")
    parts = build_parts()

    report = Report()
    report.section("0. Config consistency")
    for text, ok, detail in cfg.sanity_checks():
        report.check(text, ok, detail)
    check_solids_and_meshes(report, parts)
    check_wall_thickness(report, parts)
    check_screw_holes(report, parts)
    check_fit_to_tv(report, parts)
    check_assembly_behaviour(report, parts)
    check_printability_all(report, parts)

    report.section(f"7. Strength hand calculation ({cfg.TV_MASS_MAX_KG:.0f} kg TV, see strength.py)")
    for text, ok, detail in strength.checks():
        report.check(text, ok, detail)

    check_television(report)

    failed = report.print()
    print()
    print("The strength section is a hand calculation, not a test. Not covered at")
    print("all: creep over months, print quality, heat, and the real TV and wall.")
    print("Those need a test print and a proof load (DESIGN.md section 8).")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
