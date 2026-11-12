"""
tv_plate.py - the plate that bolts to the back of the TV.

Features, from the TV towards the wall:
  - flat plate against the TV (Y = Y_TV_PLATE_BACK to STACK_DEPTH)
  - cleat hook near the top, pointing down and towards the wall
  - lock tab near the bottom, which the lock clip snaps over
  - cable window, vent slots, four M4 VESA clearance holes

Print orientation: flat, TV-side face on the bed, hook pointing up. The hook's
slope is 45 degrees, so no supports needed.
"""

import math

from build123d import Axis, RectangleRounded, fillet

import config as cfg
from parts.common import (
    box, edges_along_x_at, extrude_xz, extrude_yz, hole_along_y, round_y_edges, try_fillet,
)
from parts.wall_plate import window_and_vents


def cleat_hook():
    """The downward-pointing half of the French cleat, as a (Y, Z) profile along X."""
    y_out = cfg.Y_TV_PLATE_BACK                            # where it joins the TV plate
    y_in = cfg.Y_WALL_PLATE_FRONT + cfg.CLEAT_CLEARANCE    # just short of the wall plate
    slope = math.tan(math.radians(cfg.CLEAT_ANGLE))

    def slope_z(y):
        """Height of the shared 45 degree contact plane at distance y."""
        return cfg.CLEAT_APEX_Z - (cfg.Y_TV_PLATE_BACK - y) * slope

    z_top = cfg.CLEAT_APEX_Z + cfg.CLEAT_ROOT
    y_flat = y_in + cfg.CLEAT_TIP_FLAT                     # knife edge cut back to a flat
    points = [
        (y_out, slope_z(y_out)),                           # top of the V groove
        (y_flat, slope_z(y_flat)),
        (y_in, slope_z(y_flat)),
        (y_in, z_top),
        (y_out, z_top),
    ]
    return extrude_yz(points, -cfg.CLEAT_LENGTH / 2, cfg.CLEAT_LENGTH / 2)


def lock_tab():
    """Small boss the lock clip's barbs snap over."""
    tab = box(-cfg.LOCK_TAB_WIDTH / 2, cfg.LOCK_TAB_WIDTH / 2,
              cfg.Y_TV_PLATE_BACK - cfg.LOCK_TAB_DEPTH, cfg.Y_TV_PLATE_BACK,
              cfg.LOCK_TAB_BOTTOM_Z, cfg.LOCK_TAB_TOP_Z)
    # A small radius only: the barbs need a crisp top edge to catch on.
    return round_y_edges(tab, 0.5)


def vesa_holes():
    """Four M4 clearance holes on the VESA pattern."""
    dia = cfg.hole_dia(cfg.VESA_SCREW)
    tools = None
    for sx in (-1, 1):
        for sz in (-1, 1):
            tool = hole_along_y(sx * cfg.VESA_X / 2, sz * cfg.VESA_Z / 2, dia,
                                cfg.Y_TV_PLATE_BACK - 1, cfg.STACK_DEPTH + 1)
            tools = tool if tools is None else tools + tool
    return tools


def build():
    y0, y1 = cfg.Y_TV_PLATE_BACK, cfg.STACK_DEPTH

    # 1. Base plate. The wall-side perimeter is rounded; the TV-side edge stays
    #    sharp because it sits on the print bed.
    plate = extrude_xz(
        RectangleRounded(cfg.TV_PLATE_WIDTH, cfg.TV_PLATE_HEIGHT, cfg.CORNER_RADIUS), y0, y1)
    plate = fillet(plate.edges().group_by(Axis.Y)[0], cfg.EDGE_FILLET)

    # 2. Add the hook and the lock tab.
    part = plate + cleat_hook() + lock_tab()

    # 3. Cut the window, vents and VESA holes.
    part = part - window_and_vents(y0 - 1, y1 + 1) - vesa_holes()

    # 4. Round the top of the V groove, where bending stress peaks.
    part = try_fillet(part, edges_along_x_at(part, y0, cfg.CLEAT_APEX_Z),
                      cfg.CLEAT_ROOT_FILLET, "TV plate cleat groove")

    part.label = "tv_plate"
    return part
