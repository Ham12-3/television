"""
tv_assembly.py - builds the complete television as a list of items.

An "item" is one part or one set of like parts (for example "all the chips on
the main board"), with a colour, a material for the mass estimate, the group
it belongs to in the viewer, and how far it moves in the exploded view.

Use from other scripts:
    from tv_assembly import build_tv

Run directly for a summary, layout checks and a clash check:
    python tv_assembly.py            (add --no-clash to skip the slow check)
"""

import sys

import numpy as np
from build123d import CenterOf

import config as cfg
from tv import enclosure, hardware, panel, remote
from tv.board_data import BOARDS, MAIN, layout_problems
from tv.boards import CATEGORY, build_board, port_openings, standoff_points
from tv.common import Item

# Display colours.
BLACK_PLASTIC = (0.09, 0.09, 0.10)
DARK_PLASTIC = (0.16, 0.16, 0.18)
STEEL = (0.62, 0.64, 0.67)
WHITE = (0.96, 0.96, 0.94)
CABLE_GREY = (0.55, 0.55, 0.58)
FFC = (0.85, 0.85, 0.80)

CATEGORY_BY_NAME = {name: (colour, material) for name, colour, material in CATEGORY.values()}


def back(y):
    """Explode vector: move this far out from the wall (towards the viewer)."""
    return (0.0, float(y), 0.0)


def build_tv() -> list[Item]:
    items = []

    def add(name, group, shape, colour, material, explode, **more):
        items.append(Item(name, group, shape, colour, material, explode, **more))

    # --- Enclosure -----------------------------------------------------------
    add("rear_cover", "Enclosure", enclosure.rear_cover(port_openings(MAIN)),
        DARK_PLASTIC, "abs", back(70))
    add("cover_screws", "Enclosure", hardware.cover_screws(), STEEL, "screw", back(45))
    add("front_bezel", "Enclosure", enclosure.front_bezel(), BLACK_PLASTIC, "abs", back(520))
    add("ir_window", "Enclosure", enclosure.ir_window_lens(), (0.30, 0.05, 0.06), "pc", back(540))
    add("brand_badge", "Enclosure", enclosure.brand_badge(), (0.75, 0.76, 0.78), "abs", back(540))

    # --- Panel and backlight (front to back) -----------------------------------
    add("lcd_cell", "Panel and backlight", panel.lcd_cell(), (0.04, 0.06, 0.11), "glass_cell",
        back(480), opacity=0.92)
    add("mould_frame", "Panel and backlight", panel.mould_frame(), (0.22, 0.22, 0.24), "abs", back(450))
    names = ("prism_sheet_upper", "prism_sheet_lower", "diffuser_sheet")
    for i, sheet in enumerate(reversed(panel.optical_films())):
        add(names[i], "Panel and backlight", sheet, (0.86, 0.90, 0.96), "pet_film",
            back(425 - i * 12), opacity=0.55)
    add("diffuser_plate", "Panel and backlight", panel.diffuser_plate(), (0.97, 0.97, 0.95),
        "ps_diffuser", back(385), opacity=0.85)
    add("support_pins", "Panel and backlight", panel.support_pins(), WHITE, "abs", back(350))
    add("reflector_sheet", "Panel and backlight", panel.reflector(), WHITE, "pet_film", back(335))
    strips, leds, lenses = panel.led_backlight()
    add("led_lenses", "Panel and backlight", lenses, (0.80, 0.90, 1.00), "pc", back(320), opacity=0.6)
    add("led_chips", "Panel and backlight", leds, (1.00, 0.88, 0.25), "ic", back(310))
    add("led_strips", "Panel and backlight", strips, (0.88, 0.88, 0.85), "aluminium", back(310))
    pcbs, sockets, cofs = panel.source_boards()
    add("source_boards", "Panel and backlight", pcbs, (0.05, 0.38, 0.16), "fr4", back(265))
    add("source_sockets", "Panel and backlight", sockets, (0.92, 0.90, 0.82), "connector", back(265))
    add("source_cofs", "Panel and backlight", cofs, (0.80, 0.52, 0.15), "pet_film", back(265))

    # --- Chassis -----------------------------------------------------------------
    add("back_chassis", "Chassis", panel.back_chassis(standoff_points()), STEEL, "steel", back(280))

    # --- Circuit boards ------------------------------------------------------------
    for board in BOARDS:
        front = board.get("faces_front")
        base = 500 if front else 170
        for category, shape in build_board(board).items():
            if category == "pcb":
                colour, material, lift = board["colour"], "fr4", 0
            else:
                colour, material = CATEGORY_BY_NAME[category]
                lift = 18 if front else -18          # parts lift off their board
            add(f"{board['name']}_{category}", board["title"], shape, colour, material,
                back(base + lift))

    # --- Speakers, mains inlet, cables ---------------------------------------------
    add("speakers", "Speakers and mains", hardware.speakers(), BLACK_PLASTIC, "speaker", back(120))
    add("mains_inlet", "Speakers and mains", hardware.ac_inlet(), BLACK_PLASTIC, "abs", back(120))
    for name, shape in hardware.cables().items():
        colour = FFC if name.startswith("ffc") else CABLE_GREY
        add(name, "Cables", shape, colour, "cable", back(135))

    # --- Accessories ---------------------------------------------------------------
    add("stand_feet", "Stand feet", hardware.stand_feet(), BLACK_PLASTIC, "abs", (0, 0, -70),
        fitted=False, note="Not fitted when the TV is on the wall mount")
    lifts = {"remote_top_shell": 60, "remote_keypad": 40, "remote_electronics": 20,
             "remote_batteries": -15, "remote_battery_door": -50, "remote_bottom_shell": -30}
    looks = {"remote_top_shell": (BLACK_PLASTIC, "abs"), "remote_keypad": ((0.35, 0.36, 0.40), "rubber"),
             "remote_electronics": ((0.05, 0.38, 0.16), "fr4"), "remote_batteries": ((0.80, 0.62, 0.15), "battery"),
             "remote_battery_door": (DARK_PLASTIC, "abs"), "remote_bottom_shell": (DARK_PLASTIC, "abs")}
    for name, shape in remote.build().items():
        colour, material = looks[name]
        add(name, "Remote control", shape, colour, material, (0, 0, lifts[name]), fitted=False,
            note="Accessory: shown on the table in front of the TV")
    return items


# ---------------------------------------------------------------------------
# Mass, centre of mass, clashes
# ---------------------------------------------------------------------------
def mass_properties(items) -> tuple[float, np.ndarray]:
    """Total mass (kg) and centre of mass (X, Y, Z) of the fitted TV items."""
    total, moment = 0.0, np.zeros(3)
    for item in items:
        if not item.fitted:
            continue
        density = cfg.DENSITY[item.material] / 1000.0          # g per mm3
        for solid in item.solids():
            m = solid.volume * density
            c = solid.center(CenterOf.MASS)
            total += m
            moment += m * np.array([c.X, c.Y, c.Z])
    return total / 1000.0, moment / total


def _boxes_touch(a, b, gap=0.0):
    return not (a.max.X < b.min.X - gap or b.max.X < a.min.X - gap
                or a.max.Y < b.min.Y - gap or b.max.Y < a.min.Y - gap
                or a.max.Z < b.min.Z - gap or b.max.Z < a.min.Z - gap)


def find_clashes(shapes: dict, tolerance: float = 0.05, progress: bool = False) -> list:
    """Overlap volume between every pair of named shapes.

    Works solid by solid, and skips pairs whose bounding boxes are apart, so
    only the handful of solids that are really close get the slow exact test.
    """
    solids = {name: [(s, s.bounding_box()) for s in shape.solids()] for name, shape in shapes.items()}
    boxes = {name: shape.bounding_box() for name, shape in shapes.items()}
    names = list(shapes)
    clashes = []
    for i, a in enumerate(names):
        if progress:
            print(f"  checking {a} ({i + 1}/{len(names)})", flush=True)
        for b in names[i + 1:]:
            if not _boxes_touch(boxes[a], boxes[b]):
                continue
            volume = 0.0
            for sa, ba in solids[a]:
                for sb, bb in solids[b]:
                    if not _boxes_touch(ba, bb):
                        continue
                    try:
                        common = sa & sb
                    except Exception:
                        volume = float("nan")
                        continue
                    if common is None:
                        continue
                    try:
                        volume += float(common.volume)
                    except AttributeError:
                        volume += float(sum(s.volume for s in common))
            if not volume <= tolerance:
                clashes.append((a, b, volume))
    return clashes


def all_shapes(items, include_unfitted=False) -> dict:
    """TV items plus the wall mount and its screws, for a full clash check."""
    from assembly import build_hardware, build_parts
    shapes = {**build_parts(), **build_hardware()}
    shapes.update({i.name: i.shape for i in items if i.fitted or include_unfitted})
    return shapes


def main() -> int:
    print("Checking board layouts ...")
    problems = [f"{b['name']}: {p}" for b in BOARDS for p in layout_problems(b)]
    for p in problems:
        print("  PROBLEM", p)
    if not problems:
        print(f"  {sum(len(b['parts']) for b in BOARDS)} components on {len(BOARDS)} boards, no overlaps")

    print("Building the television ...")
    items = build_tv()

    print()
    print(f"{'Item':32s} {'Group':24s} {'Solids':>6s} {'Mass':>9s}")
    print("-" * 76)
    invalid = 0
    for item in items:
        ok = item.shape.is_valid
        invalid += not ok
        print(f"{item.name:32s} {item.group:24s} {len(item.solids()):6d} {item.mass_g():8.1f}g"
              f"{'' if ok else '  INVALID'}{'' if item.fitted else '  (accessory)'}")
    print("-" * 76)
    mass, centre = mass_properties(items)
    print(f"Television mass (estimate): {mass:.2f} kg   rated limit of the mount: {cfg.TV_MASS_MAX_KG:.0f} kg")
    print(f"Centre of mass: {centre[1]:.1f} mm from the wall "
          f"(mount calculation assumes {cfg.LOAD_OFFSET_FROM_WALL:.0f} mm), "
          f"X {centre[0]:+.1f}, Z {centre[2]:+.1f}")

    clashes = []
    if "--no-clash" not in sys.argv:
        print()
        print("Clash check: television, wall mount and screws ...")
        clashes = find_clashes(all_shapes(items), progress="--verbose" in sys.argv)
        for a, b, volume in clashes:
            print(f"  CLASH  {a} / {b}: {volume:.2f} mm3")
        if not clashes:
            print("  No two items overlap.")

    ok = not problems and not invalid and not clashes
    print()
    print("RESULT: PASS" if ok else "RESULT: FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
