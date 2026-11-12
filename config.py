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
TV_DEPTH = 70.0             # front of bezel to back of rear cover
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
WALL_SCREW_SPACING_X = 110.0  # close to the cleat: keeps plate bending low
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
LOAD_OFFSET_FROM_WALL = 70.0  # where the TV's weight acts, measured from the wall.
                              # validate.py checks the modelled TV's centre of
                              # mass is no further out than this.

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


# ===========================================================================
# TELEVISION (the complete set: enclosure, panel, backlight, chassis, boards)
#
# Inside the TV a second depth coordinate is used:
#     w = distance forward from the TV's back surface (w = 0 is the rear cover's
#         outer face, w = TV_DEPTH is the front of the bezel).
#     Global Y = STACK_DEPTH + w.   X and Z are unchanged.
# ===========================================================================

# --- T1. Screen ------------------------------------------------------------
ACTIVE_WIDTH = 698.0        # lit picture area (31.5 inch diagonal, 16:9)
ACTIVE_HEIGHT = 393.0
BEZEL_TOP = 14.0            # the bottom bezel takes whatever height is left
RESOLUTION = (1920, 1080)

# --- T2. Enclosure (injection-moulded ABS) ---------------------------------
TV_CORNER_RADIUS = 8.0
ENCLOSURE_WALL = 2.2
ENCLOSURE_SPLIT_W = 56.0    # rear cover is w = 0..this; front bezel is the rest
ENCLOSURE_DRAFT = 1.0       # degrees of mould draft on the rear cover walls
BEZEL_LIP = 2.0             # thickness of the bezel face that overlaps the glass
VESA_COVER_HOLE = 5.0       # hole in the rear cover for each M4 mount screw
COVER_SCREW_HOLE = 3.4      # M3 clearance
VENT_TV_SLOT = (30.0, 3.0)  # rear cover vent slot, length x width
VENT_TV_PITCH = (36.0, 7.0)

# --- T3. Panel stack, front to back (thicknesses) --------------------------
CELL_GAP = 0.2              # foam gap between bezel lip and glass
CELL_THICKNESS = 1.6        # LCD cell: two glass sheets plus polarisers
CELL_MARGIN = 6.0           # glass extends this far past the picture each side
FRAME_LIP = 1.2             # mould frame lip the glass rests on
FRAME_WALL = 2.0
FRAME_SKIRT = 12.0          # how far the frame wraps back over the chassis wall
FILM_GAP = 0.1
FILM_THICKNESS = 0.25
FILM_COUNT = 3              # diffuser sheet + two prism sheets
FILM_MARGIN = 4.0           # films and diffuser extend this far past the picture
DIFFUSER_THICKNESS = 1.5

# --- T4. Back chassis (pressed steel tray) and backlight -------------------
TRAY_DEPTH = 26.0           # sets the optical cavity (LED to diffuser distance)
TRAY_THICKNESS = 0.6
TRAY_CLEARANCE = 1.0        # gap between diffuser edge and tray wall
TRAY_FLANGE = 3.0           # inward lip the diffuser rests on
LED_STRIPS = 3
LEDS_PER_STRIP = 8
LED_STRIP_LENGTH = 640.0
LED_STRIP_WIDTH = 16.0
LED_STRIP_THICKNESS = 1.0   # aluminium-core PCB
LED_SIZE = (3.0, 3.0, 0.8)  # 3030 package
LED_LENS_DIA = 15.0
LED_LENS_HEIGHT = 5.5
LED_FORWARD_VOLTAGE = 3.1   # volts each, at the drive current
LED_CURRENT = 0.35          # amps, all LEDs in one series string
REFLECTOR_THICKNESS = 0.3
SUPPORT_PINS_X = (-175.0, 0.0, 175.0)   # diffuser support pins

# --- T5. Circuit boards ----------------------------------------------------
PCB_THICKNESS = 1.6
BOARD_STANDOFF = 6.0        # boards stand this far off the chassis
STANDOFF_DIA = 6.0
BOSS_VESA_DIA = 10.0        # threaded steel pillars that carry the wall mount
BOSS_COVER_DIA = 7.0        # pillars the rear cover screws into
COMPONENT_CLEARANCE = 1.5   # minimum gap from tallest component to rear cover

#                 centre X, centre Z, width X, height Z
BOARD_PSU = (-200.0, 20.0, 170.0, 130.0)
BOARD_MAIN = (253.0, 0.0, 170.0, 190.0)
BOARD_TCON = (115.0, -120.0, 130.0, 45.0)
BOARD_LED_DRIVER = (-60.0, -110.0, 90.0, 50.0)
BOARD_WIFI = (250.0, 150.0, 40.0, 26.0)
BOARD_IR = (120.0, -207.25, 54.0, 8.5)        # behind the bottom bezel, faces front
SOURCE_PCB = (170.0, 330.0, 18.0)             # |centre X|, length, height (two boards)
COF_X = (45.0, 125.0, 205.0, 285.0)           # chip-on-film positions per side
COF_WIDTH = 30.0
SOURCE_CONNECTOR_X = (158.0, -85.0)           # FFC sockets on the two source boards

COVER_BOSSES = ((-320.0, 150.0), (320.0, 150.0), (-320.0, -150.0), (320.0, -150.0),
                (0.0, 202.0), (-125.0, -165.0), (125.0, -165.0))
LED_HARNESS_HOLE = (-60.0, -72.0, 10.0)       # X, Z, diameter: hole in the tray floor

# --- T6. Connector panel, speakers, mains inlet, feet ----------------------
JACK_RECESS_X = 344.0       # side recess in the rear cover where the ports sit
JACK_RECESS_HALF_Z = 90.0
JACK_RECESS_W = 34.0
PORT_PROTRUSION = 1.0       # how far each port sticks through the jack panel
SPEAKER_X = 230.0           # |centre X| of the two speakers
SPEAKER_SIZE = (110.0, 32.0, 26.0)   # X, Z, depth
SPEAKER_BOTTOM_Z = -210.0
SPEAKER_BACK_W = 5.0
SPEAKER_POWER_W = 8.0       # rated watts each
AC_INLET_Z = 20.0
AC_INLET_W = 20.0
AC_INLET_SIZE = (20.0, 23.0, 14.0)   # depth into the TV, along Z, along w
FOOT_X = 320.0
FOOT_SIZE = (25.0, 200.0, 12.0)      # X, front-to-back, height

# --- T7. Remote control ----------------------------------------------------
REMOTE_SIZE = (165.0, 44.0, 20.0)    # length, width, thickness
REMOTE_WALL = 1.6
REMOTE_POSITION = (0.0, 300.0, -227.0)   # where it is shown: on the table in front

# --- T8. Electrical ratings (system level; see ELECTRICAL.md) ---------------
MAINS_VOLTAGE = (100.0, 240.0)       # universal input, 50 / 60 Hz
PSU_EFFICIENCY = 0.87
RAIL_12V_RATED_A = 3.5
RAIL_36V_RATED_A = 1.0
LED_DRIVER_EFFICIENCY = 0.92
BUCK_EFFICIENCY = 0.88
FUSE_RATING_A = 2.5
MIN_RAIL_MARGIN = 0.20               # every rail keeps at least 20 percent spare
PFC_THRESHOLD_W = 75.0               # above this input power a PFC stage is needed

# --- T9. Materials: density in g/cm3, used for the mass estimate ------------
DENSITY = {
    "abs": 1.05, "pc": 1.20, "glass_cell": 2.20, "pet_film": 1.38, "ps_diffuser": 1.05,
    "steel": 7.85, "aluminium": 2.70, "fr4": 1.85, "ic": 2.0, "capacitor": 1.5,
    "connector": 0.9, "magnetic": 4.0, "speaker": 0.9, "cable": 1.5, "rubber": 1.2,
    "battery": 2.3, "petg": 1.27, "screw": 7.85,
}

# --- Derived TV values: do not edit ----------------------------------------
BEZEL_BOTTOM = TV_HEIGHT - ACTIVE_HEIGHT - BEZEL_TOP
SCREEN_Z = (BEZEL_BOTTOM - BEZEL_TOP) / 2          # picture centre above TV centre

W_FRONT = TV_DEPTH
W_LIP_BACK = W_FRONT - BEZEL_LIP
W_CELL_FRONT = W_LIP_BACK - CELL_GAP
W_CELL_BACK = W_CELL_FRONT - CELL_THICKNESS
W_FRAME_LIP_BACK = W_CELL_BACK - FRAME_LIP
W_FILMS_FRONT = W_FRAME_LIP_BACK - FILM_GAP
W_FILMS_BACK = W_FILMS_FRONT - FILM_COUNT * FILM_THICKNESS
W_DIFFUSER_BACK = W_FILMS_BACK - DIFFUSER_THICKNESS
W_TRAY_FRONT = W_DIFFUSER_BACK                      # diffuser rests on the tray flange
W_TRAY_BACK = W_TRAY_FRONT - TRAY_DEPTH
W_TRAY_FLOOR = W_TRAY_BACK + TRAY_THICKNESS         # inside face of the tray floor
W_STRIP_TOP = W_TRAY_FLOOR + LED_STRIP_THICKNESS
W_PCB_FRONT = W_TRAY_BACK - BOARD_STANDOFF          # board face nearest the chassis
W_PCB_BACK = W_PCB_FRONT - PCB_THICKNESS            # component side, faces the rear
MAX_COMPONENT_HEIGHT = W_PCB_BACK - ENCLOSURE_WALL - COMPONENT_CLEARANCE
OPTICAL_CAVITY = W_DIFFUSER_BACK - (W_STRIP_TOP + REFLECTOR_THICKNESS)

HALF_FILM = (ACTIVE_WIDTH / 2 + FILM_MARGIN, ACTIVE_HEIGHT / 2 + FILM_MARGIN)
HALF_CELL = (ACTIVE_WIDTH / 2 + CELL_MARGIN, ACTIVE_HEIGHT / 2 + CELL_MARGIN)
HALF_TRAY_IN = (HALF_FILM[0] + TRAY_CLEARANCE, HALF_FILM[1] + TRAY_CLEARANCE)
HALF_TRAY_OUT = (HALF_TRAY_IN[0] + TRAY_THICKNESS, HALF_TRAY_IN[1] + TRAY_THICKNESS)
TRAY_BOTTOM_Z = SCREEN_Z - HALF_TRAY_OUT[1]
LED_COUNT = LED_STRIPS * LEDS_PER_STRIP
LED_STRING_VOLTAGE = LED_COUNT * LED_FORWARD_VOLTAGE
LED_POWER_W = LED_STRING_VOLTAGE * LED_CURRENT


def led_strip_centres_z() -> list[float]:
    """Z centre of each LED strip, spread evenly over the picture height."""
    pitch = ACTIVE_HEIGHT / LED_STRIPS
    return [SCREEN_Z + (i - (LED_STRIPS - 1) / 2) * pitch for i in range(LED_STRIPS)]


def led_centres_x() -> list[float]:
    """X centre of each LED along a strip."""
    pitch = LED_STRIP_LENGTH / LEDS_PER_STRIP
    return [(i - (LEDS_PER_STRIP - 1) / 2) * pitch for i in range(LEDS_PER_STRIP)]


def support_pin_centres() -> list[tuple[float, float]]:
    """(X, Z) of each diffuser support pin: midway between LED strips."""
    zs = led_strip_centres_z()
    mids = [(a + b) / 2 for a, b in zip(zs, zs[1:])]
    return [(x, z) for z in mids for x in SUPPORT_PINS_X]


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
