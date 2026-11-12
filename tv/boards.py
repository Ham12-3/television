"""
tv/boards.py - builds 3D circuit boards from the tables in board_data.py.

Each board becomes several shapes, grouped by what the parts are, so the
viewer can colour them differently: the bare PCB, chips, capacitors,
connectors, magnetics (inductors and transformers), heatsinks, small passives
and the mounting screws.

Boards sit on standoffs behind the steel chassis with their components facing
the rear cover. The IR board is the exception: it sits behind the bottom
bezel and faces the front.
"""

import config as cfg
from tv.board_data import BOARDS, find, footprint, height
from tv.common import cut_all, cyl_w, cyl_x, cyl_z, group, tbox
from tv.enclosure import IR_BOARD_FRONT_W

# kind -> (category name, display colour, material for the mass estimate)
CATEGORY = {
    "ic": ("chips", (0.10, 0.10, 0.11), "ic"),
    "cap": ("capacitors", (0.15, 0.22, 0.42), "capacitor"),
    "connector": ("connectors", (0.92, 0.90, 0.82), "connector"),
    "port": ("ports", (0.70, 0.71, 0.73), "connector"),
    "magnetic": ("magnetics", (0.55, 0.38, 0.12), "magnetic"),
    "heatsink": ("heatsinks", (0.78, 0.79, 0.80), "aluminium"),
    "passive": ("passives", (0.32, 0.26, 0.20), "ic"),
    "shield": ("shields", (0.80, 0.80, 0.76), "steel"),
    "screw": ("screws", (0.60, 0.60, 0.62), "screw"),
}


def surface_w(board: dict) -> tuple[float, float, int]:
    """(component-side depth, other-side depth, direction components grow in)."""
    if board.get("faces_front"):
        return IR_BOARD_FRONT_W, IR_BOARD_FRONT_W - cfg.PCB_THICKNESS, +1
    return cfg.W_PCB_BACK, cfg.W_PCB_FRONT, -1


def part_span_w(board: dict, part: dict) -> tuple[float, float]:
    """Depth range a component occupies."""
    surface, _, direction = surface_w(board)
    a = surface + direction * part.get("lift", 0.0)
    b = surface + direction * height(part)
    return min(a, b), max(a, b)


def part_centre(board: dict, part: dict) -> tuple[float, float]:
    """Global (X, Z) of a component's centre."""
    return board["centre"][0] + part["u"], board["centre"][1] + part["v"]


def _solid(board: dict, part: dict):
    cx, cz = part_centre(board, part)
    w0, w1 = part_span_w(board, part)
    u0, u1, v0, v1 = footprint(part)
    x0, x1 = board["centre"][0] + u0, board["centre"][0] + u1
    z0, z1 = board["centre"][1] + v0, board["centre"][1] + v1
    shape = part["shape"]
    if shape == "cyl":
        return cyl_w(cx, cz, part["size"][0], w0, w1)
    if shape == "cyl_u":
        return cyl_x(x0, x1, cz, (w0 + w1) / 2, part["size"][0])
    if shape == "cyl_v":
        return cyl_z(cx, z0, z1, (w0 + w1) / 2, part["size"][0])
    if shape == "fins":
        # Finned heatsink: a base plate with fins standing on it.
        _, _, direction = surface_w(board)
        base = 2.0
        w_base = w1 - base if direction < 0 else w0 + base
        solid = tbox(x0, x1, z0, z1, w1 if direction < 0 else w0, w_base)
        fins = 9
        pitch = (x1 - x0 - 1.5) / (fins - 1)
        for i in range(fins):
            fx = x0 + i * pitch
            solid += tbox(fx, fx + 1.5, z0, z1, w_base, w0 if direction < 0 else w1)
        return solid
    return tbox(x0, x1, z0, z1, w0, w1)


def build_board(board: dict) -> dict:
    """Return {category: shape} for one board, including 'pcb'."""
    cx, cz = board["centre"]
    sx, sz = board["size"]
    surface, other, direction = surface_w(board)

    pcb = tbox(cx - sx / 2, cx + sx / 2, cz - sz / 2, cz + sz / 2, surface, other)
    cuts = [cyl_w(cx + hu, cz + hv, 3.2, min(surface, other) - 1, max(surface, other) + 1)
            for hu, hv in board["holes"]]
    cuts += [tbox(cx + u - su / 2, cx + u + su / 2, cz + v - sv / 2, cz + v + sv / 2,
                  min(surface, other) - 1, max(surface, other) + 1)
             for u, v, su, sv in board["slots"]]
    shapes = {"pcb": cut_all(pcb, cuts)}

    by_category = {}
    for part in board["parts"]:
        by_category.setdefault(CATEGORY[part["kind"]][0], []).append(_solid(board, part))
    # One pan-head M3 screw on every mounting hole.
    if board["holes"]:
        by_category["screws"] = [
            cyl_w(cx + hu, cz + hv, 5.5, surface + direction * 2.0, surface)
            + cyl_w(cx + hu, cz + hv, 3.0, surface, cfg.W_TRAY_FLOOR)
            for hu, hv in board["holes"]]
    for category, solids in by_category.items():
        shapes[category] = group(solids)
    return shapes


def standoff_points() -> list[tuple[float, float]]:
    """Global (X, Z) of every board mounting hole, for the chassis."""
    return [(b["centre"][0] + hu, b["centre"][1] + hv) for b in BOARDS for hu, hv in b["holes"]]


def port_openings(board: dict, clearance: float = 0.4) -> list[tuple[float, float, float, float]]:
    """(z0, z1, w0, w1) of the hole each external port needs in the connector panel."""
    openings = []
    for part in board["parts"]:
        if part["kind"] != "port":
            continue
        _, _, v0, v1 = footprint(part)
        w0, w1 = part_span_w(board, part)
        openings.append((board["centre"][1] + v0 - clearance, board["centre"][1] + v1 + clearance,
                         w0 - clearance, w1 + clearance))
    return openings


def connector_top(board: dict, ref: str) -> tuple[float, float, float]:
    """Global (X, Z, w) of the centre of a connector's mating face, for cables."""
    part = find(board, ref)
    x, z = part_centre(board, part)
    w0, w1 = part_span_w(board, part)
    _, _, direction = surface_w(board)
    return x, z, (w0 if direction < 0 else w1)
