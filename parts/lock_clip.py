"""
lock_clip.py - snap-in clip that stops the TV being lifted off the cleat.

Front view (looking at the wall), clip pushed up from below:

            |tab|              <- lock tab on the TV plate
          >|     |<            <- barbs snap over the top of the tab
           |     |             <- two flexible arms
   [block] |     | [block]     <- lower rail blocks on the wall plate
      ||   |     |   ||        <- stop posts sit just under the blocks
      ================         <- base bar
            | O |              <- finger pull

If the TV is knocked upwards, the tab pulls the barbs, the clip rises a
fraction of a millimetre and the stop posts hit the rail blocks.

It is one flat outline in (X, Z), extruded along Y. Print it lying flat so the
layers run along the arms; printed upright the arms would snap.
"""

import math

from build123d import Circle, Polygon, Pos

import config as cfg
from parts.common import edges_along_x_at, extrude_xz, hole_along_y
from build123d import Axis, fillet


def outline_points():
    """Closed (X, Z) outline of the clip. Built for X > 0, then mirrored."""
    # Heights, bottom to top
    z_catch = cfg.LOCK_TAB_TOP_Z + cfg.SNAP_CLEARANCE          # underside of barb
    z_base_top = z_catch - cfg.LOCK_CLIP_ARM_LENGTH
    z_base_bottom = z_base_top - cfg.LOCK_CLIP_BASE_HEIGHT
    z_pull_bottom = z_base_bottom - cfg.LOCK_CLIP_PULL_HEIGHT
    z_post_top = cfg.LOWER_RAIL_BOTTOM_Z - cfg.SNAP_CLEARANCE

    # Barb ramps
    barb = cfg.LOCK_CLIP_BARB
    z_return_top = z_catch + barb / math.tan(math.radians(cfg.SNAP_RETURN_ANGLE))
    z_land_top = z_return_top + cfg.SNAP_BARB_FLAT
    z_tip = z_land_top + barb / math.tan(math.radians(cfg.SNAP_LEAD_ANGLE))

    # Widths
    x_arm_in = cfg.LOCK_TAB_WIDTH / 2 + cfg.SNAP_CLEARANCE
    x_arm_out = x_arm_in + cfg.LOCK_CLIP_ARM_THICKNESS
    x_barb = x_arm_in - barb
    x_base = cfg.LOCK_CLIP_WIDTH / 2
    x_post_in = x_base - cfg.LOCK_CLIP_POST_WIDTH
    x_pull = cfg.LOCK_CLIP_PULL_WIDTH / 2

    right = [
        (x_arm_in, z_base_top),     # inside root of the arm
        (x_arm_in, z_catch),
        (x_barb, z_return_top),     # release ramp
        (x_barb, z_land_top),
        (x_arm_in, z_tip),          # lead-in ramp
        (x_arm_out, z_tip),
        (x_arm_out, z_base_top),    # outside root of the arm
        (x_post_in, z_base_top),
        (x_post_in, z_post_top),    # stop post
        (x_base, z_post_top),
        (x_base, z_base_bottom),
        (x_pull, z_base_bottom),
        (x_pull, z_pull_bottom),    # finger pull
    ]
    left = [(-x, z) for x, z in reversed(right)]
    return right + left, (z_base_top, z_base_bottom, z_pull_bottom, x_arm_in, x_arm_out)


def build():
    points, (z_base_top, z_base_bottom, z_pull_bottom, x_arm_in, x_arm_out) = outline_points()

    # Centre the clip in the air gap between the two plates.
    y0 = cfg.Y_WALL_PLATE_FRONT + (cfg.CLEAT_DEPTH - cfg.LOCK_CLIP_DEPTH) / 2
    y1 = y0 + cfg.LOCK_CLIP_DEPTH

    part = extrude_xz(Polygon(*points, align=None), y0, y1)

    # Finger hole in the pull tab.
    z_hole = (z_base_bottom + z_pull_bottom) / 2
    part = part - hole_along_y(0, z_hole, cfg.LOCK_CLIP_PULL_HOLE, y0 - 1, y1 + 1)

    # Round the four arm roots. Sharp inside corners there would crack first.
    roots = [e for e in part.edges().filter_by(Axis.Y)
             if abs(e.center().Z - z_base_top) < 0.05
             and any(abs(abs(e.center().X) - x) < 0.05 for x in (x_arm_in, x_arm_out))]
    try:
        part = fillet(roots, 1.2)
    except Exception as err:
        print(f"  note: lock clip arm-root fillet failed ({type(err).__name__}); left sharp")

    part.label = "lock_clip"
    return part
