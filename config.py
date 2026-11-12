"""
config.py - every important dimension of the TV wall mount, in one place.

Edit numbers here, then re-run the build scripts. Nothing else in the project
should contain a hard-coded dimension.

Units: millimetres, degrees, kilograms, newtons, megapascals.

Axes (same in every part and in the assembly):
    X = left / right along the wall
    Y = out from the wall, towards the TV (wall surface is Y = 0)
    Z = up (Z = 0 is the centre of the VESA pattern)

Run `python config.py` to print all values and sanity-check them.
"""

import math

# ---------------------------------------------------------------------------
# 1. Television (DESIGN.md assumptions A1, A2, A4, A5)
# ---------------------------------------------------------------------------
TV_DIAGONAL_INCH = 32
TV_WIDTH = 730.0            # overall width of a typical 32" TV
TV_HEIGHT = 430.0           # overall height without stand
TV_DEPTH = 60.0             # maximum panel depth
TV_MASS_MAX_KG = 8.0        # rated maximum TV mass for this mount

# ---------------------------------------------------------------------------
# 2. VESA interface (TV plate to TV)
# ---------------------------------------------------------------------------
VESA_X = 100.0              # hole spacing, horizontal
VESA_Z = 100.0              # hole spacing, vertical
VESA_SCREW = "M4"
VESA_SCREW_LENGTH = 16.0    # plate thickness + ~10 mm thread engagement
VESA_HEAD_DIA = 7.0         # M4 socket cap head
VESA_HEAD_HEIGHT = 4.0      # head sits proud in the air gap behind the TV plate

# ---------------------------------------------------------------------------
# 3. Standard screw clearance holes (ISO 273, medium fit)
# ---------------------------------------------------------------------------
CLEARANCE_HOLE = {"M3": 3.4, "M4": 4.5, "M5": 5.5, "M6": 6.6}
PRINTED_HOLE_COMP = 0.2     # added to diameters: FDM holes print undersize

# ---------------------------------------------------------------------------
# 4. Wall screws (wall plate to wall, assumption A3)
# ---------------------------------------------------------------------------
WALL_SCREW_DIA = 5.0        # 5 mm countersunk wood screw
WALL_SCREW_LENGTH = 50.0
WALL_SCREW_CLEARANCE = 5.5
WALL_SCREW_HEAD_DIA = 10.0  # countersink top diameter
WALL_SCREW_CSK_ANGLE = 90.0 # included angle of the countersink
WALL_SCREW_SPACING_X = 120.0  # close to the cleat: keeps plate bending low
WALL_SCREW_SPACING_Z = 90.0

# ---------------------------------------------------------------------------
# 5. Plates
# ---------------------------------------------------------------------------
PLATE_THICKNESS = 6.0       # base thickness of both plates (Y direction)

TV_PLATE_WIDTH = 140.0      # X
TV_PLATE_HEIGHT = 140.0     # Z

WALL_PLATE_WIDTH = 160.0    # X
WALL_PLATE_HEIGHT = 130.0   # Z

CORNER_RADIUS = 10.0        # outer corners of both plates
EDGE_FILLET = 1.5           # fillet on the exposed (non-bed) face perimeter
FEATURE_FILLET = 2.0        # corners of bosses, rails and tabs

# ---------------------------------------------------------------------------
# 6. French cleat (the load-carrying joint)
#
#    Side view (wall on the left, TV on the right):
#
#        wall |      /| hook (on TV plate, points down)
#       plate |     / |
#             |\   /  | TV plate
#             | \ /   |
#             |  \    |
#        rail |___\   |      rail is on the wall plate, points up
# ---------------------------------------------------------------------------
CLEAT_ANGLE = 45.0          # slope from horizontal; 45 = prints without supports
CLEAT_DEPTH = 12.0          # air gap between the plates = cleat thickness (Y)
CLEAT_ROOT = 14.0           # height of rail / hook where it joins its plate (Z).
                            # Sized by the strength calculation (strength.py).
CLEAT_LENGTH = 80.0         # along X; must fit between the VESA screw heads
CLEAT_APEX_Z = 49.0         # Z where the slope meets the TV plate's back face
CLEAT_CLEARANCE = 0.3       # gap between a cleat's flat face and the other plate
CLEAT_TIP_FLAT = 2.4        # knife edges are cut back to a flat this wide (= MIN_WALL)
CLEAT_ROOT_FILLET = 1.0     # fillet in the V groove, to lower stress there

# ---------------------------------------------------------------------------
# 7. Lower rail on the wall plate
#    Two blocks that (a) act as a bumper so the TV plate hangs parallel to the
#    wall, (b) stop the lock clip, and (c) hold the cable clips.
# ---------------------------------------------------------------------------
LOWER_RAIL_Z = -60.0        # centre height
LOWER_RAIL_HEIGHT = 8.0     # Z
LOWER_RAIL_SPAN = 120.0     # overall X extent, outer edge to outer edge
LOWER_RAIL_NOTCH = 34.0     # central gap the lock clip passes through

# ---------------------------------------------------------------------------
# 8. Lock tab (on the TV plate) and lock clip (separate snap-fit part)
#    The clip's two arms pass up either side of the tab and snap over its top.
#    If the TV is knocked upwards, the tab lifts the clip, and the clip's stop
#    posts hit the underside of the lower rail.
# ---------------------------------------------------------------------------
LOCK_TAB_WIDTH = 16.0       # X
LOCK_TAB_HEIGHT = 6.0       # Z
LOCK_TAB_DEPTH = 10.0       # how far it projects from the TV plate (Y)
LOCK_TAB_TOP_Z = -54.0

SNAP_CLEARANCE = 0.2        # gap per face on all snap-fit features
SNAP_LEAD_ANGLE = 30.0      # insertion ramp, measured from the push direction
SNAP_RETURN_ANGLE = 45.0    # release ramp; 90 would be permanent
SNAP_BARB_FLAT = 0.5        # flat land on the tip of each barb

LOCK_CLIP_DEPTH = 8.0       # Y thickness of the clip (its print height)
LOCK_CLIP_ARM_THICKNESS = 2.4
LOCK_CLIP_ARM_LENGTH = 18.0 # long arms keep bending strain low (see DESIGN.md)
LOCK_CLIP_BARB = 1.2        # how far each barb overlaps the tab
LOCK_CLIP_WIDTH = 50.0      # base bar, X
LOCK_CLIP_BASE_HEIGHT = 5.0
LOCK_CLIP_POST_WIDTH = 7.0  # stop posts at each end of the base bar
LOCK_CLIP_PULL_WIDTH = 20.0 # finger pull tab
LOCK_CLIP_PULL_HEIGHT = 16.0
LOCK_CLIP_PULL_HOLE = 10.0

# ---------------------------------------------------------------------------
# 9. Cable clips (separate snap-fit parts, pushed up into the lower rail)
# ---------------------------------------------------------------------------
CABLE_CLIP_COUNT = 2
CABLE_CLIP_SPACING = 90.0   # centre-to-centre along X
CABLE_CLIP_BORE = 12.0      # fits an HDMI + power lead bundle
CABLE_CLIP_WALL = 2.4
CABLE_CLIP_OPENING = 9.0    # slot the cables are pressed through (faces the TV)
CABLE_CLIP_HEIGHT = 10.0    # Z height of the ring
CABLE_CLIP_CORNER = 1.5     # larger radii thin out the lips beside the opening
CABLE_CLIP_NECK_WIDTH = 12.0
CABLE_CLIP_BARB = 0.8
CABLE_CLIP_SLIT = 2.4       # gap between the two prongs
CABLE_CLIP_SLIT_DEPTH = 6.0 # how far the slit runs down into the neck
CABLE_TUNNEL_WIDTH = 8.0    # slot through the lower rail (X); also a bridge span
CABLE_TUNNEL_DEPTH = 5.0    # (Y)
CABLE_CLIP_DROP = 2.6       # gap between the TV plate's bottom edge and the ring.
                            # Also sets the solid web left under the slit:
                            # raise both together or the web gets too thin.

# ---------------------------------------------------------------------------
# 10. Cable window and vents (cut through both plates)
# ---------------------------------------------------------------------------
CABLE_WINDOW_WIDTH = 70.0   # X
CABLE_WINDOW_HEIGHT = 40.0  # Z; kept short to leave room for the cleat root
CABLE_WINDOW_RADIUS = 8.0

VENT_SLOT_WIDTH = 6.0
VENT_RIB_WIDTH = 3.0        # solid rib left between neighbouring slots
VENT_SLOT_LENGTH = 30.0     # Z
VENT_SLOTS_PER_SIDE = 3
VENT_WINDOW_MARGIN = 5.0    # solid material between the window and first slot

# ---------------------------------------------------------------------------
# 11. FDM print rules (used by the validation script)
# ---------------------------------------------------------------------------
NOZZLE_DIA = 0.4
LAYER_HEIGHT = 0.2
MIN_WALL = 2.4              # 6 nozzle widths; applies to the two plates
MIN_SNAP_WALL = 1.6         # 4 nozzle widths; applies to the small snap-fit clips
MIN_RIB = 3.0
MAX_OVERHANG_ANGLE = 45.0   # from vertical, printable without supports
MAX_BRIDGE = 10.0
PRINT_BED_X = 220.0         # assumption A6
PRINT_BED_Y = 220.0
PRINT_BED_Z = 150.0
GENERAL_TOLERANCE = 0.2

# ---------------------------------------------------------------------------
# 12. Material and loads (used by the strength calculation)
# ---------------------------------------------------------------------------
MATERIAL = "PETG"
PETG_MODULUS = 2000.0         # MPa, printed
PETG_YIELD_INPLANE = 40.0     # MPa, printed, along the layers
PETG_YIELD_INTERLAYER = 20.0  # MPa, between layers
PETG_CREEP_ALLOWABLE = 8.0    # MPa, long-term sustained stress limit
PETG_DENSITY = 1.27e-6        # kg per mm^3
TARGET_SAFETY_FACTOR = 5.0
GRAVITY = 9.81
DESIGN_LOAD_N = TV_MASS_MAX_KG * GRAVITY
LOAD_OFFSET_FROM_WALL = 50.0  # where the TV's weight acts, measured from the wall

# ---------------------------------------------------------------------------
# 13. Output folders
# ---------------------------------------------------------------------------
OUT_STEP = "output/step"
OUT_STL = "output/stl"
OUT_RENDERS = "output/renders"


# ===========================================================================
# Derived values - calculated from the numbers above. Do not edit directly.
# ===========================================================================
Y_WALL_PLATE_FRONT = PLATE_THICKNESS                    # front face of wall plate
Y_TV_PLATE_BACK = PLATE_THICKNESS + CLEAT_DEPTH         # wall-side face of TV plate
STACK_DEPTH = Y_TV_PLATE_BACK + PLATE_THICKNESS         # wall to back of TV

# Vertical rise of the cleat slope across the air gap.
CLEAT_RISE = CLEAT_DEPTH * math.tan(math.radians(CLEAT_ANGLE))

LOWER_RAIL_TOP_Z = LOWER_RAIL_Z + LOWER_RAIL_HEIGHT / 2
LOWER_RAIL_BOTTOM_Z = LOWER_RAIL_Z - LOWER_RAIL_HEIGHT / 2
LOCK_TAB_BOTTOM_Z = LOCK_TAB_TOP_Z - LOCK_TAB_HEIGHT
TV_PLATE_BOTTOM_Z = -TV_PLATE_HEIGHT / 2
WALL_PLATE_BOTTOM_Z = -WALL_PLATE_HEIGHT / 2


def hole_dia(screw: str) -> float:
    """Printed clearance-hole diameter for a metric screw name such as 'M4'."""
    return CLEARANCE_HOLE[screw] + PRINTED_HOLE_COMP


def vent_slot_centres_x() -> list[float]:
    """X centres of every vent slot (both sides of the cable window)."""
    first = CABLE_WINDOW_WIDTH / 2 + VENT_WINDOW_MARGIN + VENT_SLOT_WIDTH / 2
    pitch = VENT_SLOT_WIDTH + VENT_RIB_WIDTH
    right = [first + i * pitch for i in range(VENT_SLOTS_PER_SIDE)]
    return [-x for x in reversed(right)] + right


def cable_clip_centres_x() -> list[float]:
    """X centres of the cable clips, spread evenly about the middle."""
    n = CABLE_CLIP_COUNT
    return [(i - (n - 1) / 2) * CABLE_CLIP_SPACING for i in range(n)]


def sanity_checks() -> list[tuple[str, bool, str]]:
    """Cheap checks that the numbers above are consistent with each other.

    Returns a list of (description, passed, detail). This catches typos in the
    config before any CAD is built; the full model checks live in validate.py.
    """
    edge_margin_x = (TV_PLATE_WIDTH - VESA_X) / 2 - hole_dia(VESA_SCREW) / 2
    edge_margin_z = (TV_PLATE_HEIGHT - VESA_Z) / 2 - hole_dia(VESA_SCREW) / 2
    wall_margin_x = (WALL_PLATE_WIDTH - WALL_SCREW_SPACING_X) / 2 - WALL_SCREW_HEAD_DIA / 2
    wall_margin_z = (WALL_PLATE_HEIGHT - WALL_SCREW_SPACING_Z) / 2 - WALL_SCREW_HEAD_DIA / 2
    window_to_vesa = (VESA_X - CABLE_WINDOW_WIDTH) / 2 - hole_dia(VESA_SCREW) / 2
    largest_part = max(WALL_PLATE_WIDTH, WALL_PLATE_HEIGHT, TV_PLATE_WIDTH, TV_PLATE_HEIGHT)

    # Cleat layout
    cleat_to_vesa_head = VESA_X / 2 - VESA_HEAD_DIA / 2 - CLEAT_LENGTH / 2
    rail_bottom = CLEAT_APEX_Z - CLEAT_RISE - CLEAT_ROOT
    hook_top = CLEAT_APEX_Z + CLEAT_ROOT
    rail_to_window = rail_bottom - CABLE_WINDOW_HEIGHT / 2

    # Vents
    outer_vent_edge = max(vent_slot_centres_x()) + VENT_SLOT_WIDTH / 2
    vent_edge_margin = TV_PLATE_WIDTH / 2 - outer_vent_edge

    # Lower rail vs VESA screw heads (both live in the air gap)
    rail_to_head = (-VESA_Z / 2 - VESA_HEAD_DIA / 2) - LOWER_RAIL_TOP_Z
    rail_block = (LOWER_RAIL_SPAN - LOWER_RAIL_NOTCH) / 2
    clip_in_block = (min(abs(x) for x in cable_clip_centres_x()) - CABLE_TUNNEL_WIDTH / 2
                     - LOWER_RAIL_NOTCH / 2)

    # Snap-fit bending strain, cantilever formula: strain = 1.5 * t * y / L^2
    lock_strain = 1.5 * LOCK_CLIP_ARM_THICKNESS * LOCK_CLIP_BARB / LOCK_CLIP_ARM_LENGTH ** 2
    prong = (CABLE_TUNNEL_WIDTH - 2 * SNAP_CLEARANCE - CABLE_CLIP_SLIT) / 2
    prong_len = LOWER_RAIL_HEIGHT + 2 * SNAP_CLEARANCE + CABLE_CLIP_SLIT_DEPTH
    cable_strain = 1.5 * prong * CABLE_CLIP_BARB / prong_len ** 2

    ring_front = (Y_WALL_PLATE_FRONT + SNAP_CLEARANCE + 2 * CABLE_CLIP_WALL + CABLE_CLIP_BORE)

    return [
        ("VESA hole edge margin >= 2x min wall",
         min(edge_margin_x, edge_margin_z) >= 2 * MIN_WALL,
         f"{min(edge_margin_x, edge_margin_z):.1f} mm"),
        ("Wall screw edge margin >= min wall",
         min(wall_margin_x, wall_margin_z) >= MIN_WALL,
         f"{min(wall_margin_x, wall_margin_z):.1f} mm"),
        ("Cable window clears the VESA holes by >= min wall",
         window_to_vesa >= MIN_WALL,
         f"{window_to_vesa:.1f} mm"),
        ("Cleat fits between the VESA screw heads",
         cleat_to_vesa_head >= 2.0,
         f"{cleat_to_vesa_head:.1f} mm clear each side"),
        ("Cleat rail sits above the cable window",
         rail_to_window >= MIN_RIB,
         f"{rail_to_window:.1f} mm"),
        ("Cleat hook stays inside both plates",
         hook_top <= min(TV_PLATE_HEIGHT, WALL_PLATE_HEIGHT) / 2 - EDGE_FILLET,
         f"hook top at Z = {hook_top:.1f} mm"),
        ("Cleat angle is printable without supports",
         CLEAT_ANGLE >= 90 - MAX_OVERHANG_ANGLE,
         f"{CLEAT_ANGLE:.0f} deg"),
        ("Cleat tip flat is wide enough to clear the root fillet",
         CLEAT_TIP_FLAT >= 2 * CLEAT_ROOT_FILLET,
         f"{CLEAT_TIP_FLAT:.1f} mm flat, {CLEAT_ROOT_FILLET:.1f} mm fillet"),
        ("Lower rail clears the VESA screw heads",
         rail_to_head >= 1.0,
         f"{rail_to_head:.1f} mm"),
        ("Cable clip tunnels sit inside the lower rail blocks",
         clip_in_block >= MIN_WALL and rail_block > CABLE_TUNNEL_WIDTH + 2 * MIN_WALL,
         f"{clip_in_block:.1f} mm from the notch"),
        ("Cable tunnel is bridgeable",
         CABLE_TUNNEL_WIDTH <= MAX_BRIDGE,
         f"{CABLE_TUNNEL_WIDTH:.1f} mm"),
        ("Cable clip ring fits between the wall plate face and the TV",
         ring_front <= STACK_DEPTH - 0.5,
         f"front at Y = {ring_front:.1f} mm, TV back at {STACK_DEPTH:.1f} mm"),
        ("Lock clip arm strain <= 2 percent",
         lock_strain <= 0.02,
         f"{lock_strain * 100:.2f} percent"),
        ("Cable clip prong strain <= 2 percent",
         cable_strain <= 0.02,
         f"{cable_strain * 100:.2f} percent"),
        ("Lock clip arms fit through the lower rail notch",
         LOWER_RAIL_NOTCH / 2 >= LOCK_TAB_WIDTH / 2 + SNAP_CLEARANCE
         + LOCK_CLIP_ARM_THICKNESS + LOCK_CLIP_BARB + 1.0,
         f"{LOWER_RAIL_NOTCH:.0f} mm notch"),
        ("Vent rib >= minimum rib",
         VENT_RIB_WIDTH >= MIN_RIB,
         f"{VENT_RIB_WIDTH:.1f} mm"),
        ("Vent slots stay inside the TV plate",
         vent_edge_margin >= MIN_WALL,
         f"{vent_edge_margin:.1f} mm to the edge"),
        ("Vent slot is bridgeable",
         VENT_SLOT_WIDTH <= MAX_BRIDGE,
         f"{VENT_SLOT_WIDTH:.1f} mm"),
        ("Largest part fits the print bed",
         largest_part <= min(PRINT_BED_X, PRINT_BED_Y),
         f"{largest_part:.0f} mm vs {min(PRINT_BED_X, PRINT_BED_Y):.0f} mm bed"),
        ("Mount is hidden behind the TV",
         WALL_PLATE_WIDTH < TV_WIDTH and WALL_PLATE_HEIGHT < TV_HEIGHT,
         f"{WALL_PLATE_WIDTH:.0f} x {WALL_PLATE_HEIGHT:.0f} mm vs {TV_WIDTH:.0f} x {TV_HEIGHT:.0f} mm"),
    ]


if __name__ == "__main__":
    print("TV wall mount - parameters")
    print("-" * 60)
    for name, value in sorted(globals().items()):
        if name.isupper():
            print(f"{name:28s} {value}")
    print()
    print("Config sanity checks")
    print("-" * 60)
    results = sanity_checks()
    for text, ok, detail in results:
        print(f"[{'PASS' if ok else 'FAIL'}] {text}  ({detail})")
    failed = sum(not ok for _, ok, _ in results)
    print("-" * 60)
    print("ALL PASS" if failed == 0 else f"{failed} FAILED")
    raise SystemExit(1 if failed else 0)
