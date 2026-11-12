"""
wall_plate.py - the plate that screws to the wall.

Features, back to front:
  - flat plate against the wall (Y = 0 to PLATE_THICKNESS)
  - cleat rail near the top, sloped face pointing up and towards the wall
  - two lower rail blocks: bumper for the TV plate, stop for the lock clip,
    and a tunnel in each for a cable clip
  - cable window, vent slots, four countersunk wall-screw holes

Print orientation: flat on its back (the wall face on the bed). The cleat slope
is 45 degrees and the cable tunnels are short bridges, so no supports needed.
"""

import math

from build123d import Axis, Cone, GridLocations, Pos, RectangleRounded, Rot, SlotOverall, fillet

import config as cfg
from parts.common import (
    box, edges_along_x_at, extrude_xz, extrude_yz, hole_along_y, round_y_edges, try_fillet,
)


def cleat_rail():
    """The upward-pointing half of the French cleat, as a (Y, Z) profile along X."""
    y_in = cfg.Y_WALL_PLATE_FRONT                       # where it joins the plate
    y_out = cfg.Y_TV_PLATE_BACK - cfg.CLEAT_CLEARANCE   # just short of the TV plate
    slope = math.tan(math.radians(cfg.CLEAT_ANGLE))

    def slope_z(y):
        """Height of the shared 45 degree contact plane at distance y."""
        return cfg.CLEAT_APEX_Z - (cfg.Y_TV_PLATE_BACK - y) * slope

    z_bottom = slope_z(y_in) - cfg.CLEAT_ROOT
    y_flat = y_out - cfg.CLEAT_TIP_FLAT                 # knife edge cut back to a flat
    points = [
        (y_in, z_bottom),
        (y_out, z_bottom),
        (y_out, slope_z(y_flat)),
        (y_flat, slope_z(y_flat)),
        (y_in, slope_z(y_in)),                          # bottom of the V groove
    ]
    return extrude_yz(points, -cfg.CLEAT_LENGTH / 2, cfg.CLEAT_LENGTH / 2)


def lower_rail_blocks():
    """Two blocks either side of the central notch, each with a cable-clip tunnel."""
    y0 = cfg.Y_WALL_PLATE_FRONT
    y1 = cfg.Y_TV_PLATE_BACK - cfg.CLEAT_CLEARANCE
    blocks = None
    for side in (-1, 1):
        x_inner = side * cfg.LOWER_RAIL_NOTCH / 2
        x_outer = side * cfg.LOWER_RAIL_SPAN / 2
        block = box(min(x_inner, x_outer), max(x_inner, x_outer), y0, y1,
                    cfg.LOWER_RAIL_BOTTOM_Z, cfg.LOWER_RAIL_TOP_Z)
        block = round_y_edges(block, cfg.FEATURE_FILLET)
        blocks = block if blocks is None else blocks + block
    return blocks


def cable_tunnels():
    """Vertical slots through the lower rail that the cable clips snap into."""
    tools = None
    for x in cfg.cable_clip_centres_x():
        tool = box(x - cfg.CABLE_TUNNEL_WIDTH / 2, x + cfg.CABLE_TUNNEL_WIDTH / 2,
                   cfg.Y_WALL_PLATE_FRONT, cfg.Y_WALL_PLATE_FRONT + cfg.CABLE_TUNNEL_DEPTH,
                   cfg.LOWER_RAIL_BOTTOM_Z - 1, cfg.LOWER_RAIL_TOP_Z + 1)
        tools = tool if tools is None else tools + tool
    return tools


def wall_screw_holes():
    """Four clearance holes with countersinks on the front face."""
    t = cfg.PLATE_THICKNESS
    head_r = cfg.WALL_SCREW_HEAD_DIA / 2
    hole_r = (cfg.WALL_SCREW_CLEARANCE + cfg.PRINTED_HOLE_COMP) / 2
    csk_depth = (head_r - hole_r) / math.tan(math.radians(cfg.WALL_SCREW_CSK_ANGLE / 2))
    tools = None
    for sx in (-1, 1):
        for sz in (-1, 1):
            x = sx * cfg.WALL_SCREW_SPACING_X / 2
            z = sz * cfg.WALL_SCREW_SPACING_Z / 2
            shank = hole_along_y(x, z, 2 * hole_r, -1, t + 1)
            # Rot(X=90) lays the cone along Y with its wide end towards +Y.
            csk = Pos(x, t - csk_depth / 2, z) * Rot(X=90) * Cone(head_r, hole_r, csk_depth)
            tool = shank + csk
            tools = tool if tools is None else tools + tool
    return tools


def window_and_vents(y0: float, y1: float):
    """Cable window plus vent slots. Shared with the TV plate so they line up."""
    window = extrude_xz(
        RectangleRounded(cfg.CABLE_WINDOW_WIDTH, cfg.CABLE_WINDOW_HEIGHT, cfg.CABLE_WINDOW_RADIUS),
        y0, y1)
    tools = window
    for x in cfg.vent_slot_centres_x():
        slot = Pos(x, 0) * SlotOverall(cfg.VENT_SLOT_LENGTH, cfg.VENT_SLOT_WIDTH, rotation=90)
        tools = tools + extrude_xz(slot, y0, y1)
    return tools


def build():
    t = cfg.PLATE_THICKNESS

    # 1. Base plate, with the exposed front perimeter rounded off. The back
    #    edge stays sharp because it sits on the print bed.
    plate = extrude_xz(
        RectangleRounded(cfg.WALL_PLATE_WIDTH, cfg.WALL_PLATE_HEIGHT, cfg.CORNER_RADIUS), 0, t)
    plate = fillet(plate.edges().group_by(Axis.Y)[-1], cfg.EDGE_FILLET)

    # 2. Add the load-carrying features.
    part = plate + cleat_rail() + lower_rail_blocks()

    # 3. Cut everything that goes through the plate.
    part = part - window_and_vents(-1, t + 1) - wall_screw_holes() - cable_tunnels()

    # 4. Round the bottom of the V groove, where bending stress peaks.
    slope = math.tan(math.radians(cfg.CLEAT_ANGLE))
    groove_z = cfg.CLEAT_APEX_Z - cfg.CLEAT_DEPTH * slope
    part = try_fillet(part, edges_along_x_at(part, t, groove_z),
                      cfg.CLEAT_ROOT_FILLET, "wall plate cleat groove")

    part.label = "wall_plate"
    return part
