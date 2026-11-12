r"""
cable_clip.py - snap-in cable holder that hangs below the wall plate.

Two pieces fused into one part:
  - a split "arrow" tongue (flat outline in X, Z) that pushes up through a
    tunnel in the wall plate's lower rail; its two barbs spring out above it
  - a C-shaped ring below, whose opening faces the TV so cables press in

Front view of the tongue:        Top view of the ring:

        /\  /\    <- barbs            ___   ___
        || ||     <- two prongs      |   \_/   |   <- opening (faces the TV)
       _||_||_    <- shoulder        |  (   )  |
      |_______|   <- neck            |_________|   <- flat back (on the bed)

Print orientation: on its flat back (the wall-side face on the bed), so the
layers run along the prongs.
"""

import math

from build123d import Circle, Polygon, Pos, Rectangle, RectangleRounded

import config as cfg
from parts.common import extrude_xy, extrude_xz


def tongue_points(z_ring_top: float):
    """Closed (X, Z) outline of the tongue and neck, centred on X = 0."""
    z_shoulder = cfg.LOWER_RAIL_BOTTOM_Z - cfg.SNAP_CLEARANCE   # sits under the rail
    z_catch = cfg.LOWER_RAIL_TOP_Z + cfg.SNAP_CLEARANCE         # barbs sit over the rail
    z_slit = z_shoulder - cfg.CABLE_CLIP_SLIT_DEPTH

    barb = cfg.CABLE_CLIP_BARB
    z_return_top = z_catch + barb / math.tan(math.radians(cfg.SNAP_RETURN_ANGLE))
    z_land_top = z_return_top + cfg.SNAP_BARB_FLAT
    # The lead-in ramp tapers the tip to a little narrower than the tunnel.
    taper = barb + 0.4
    z_tip = z_land_top + taper / math.tan(math.radians(cfg.SNAP_LEAD_ANGLE))

    x_prong = cfg.CABLE_TUNNEL_WIDTH / 2 - cfg.SNAP_CLEARANCE
    x_slit = cfg.CABLE_CLIP_SLIT / 2
    x_neck = cfg.CABLE_CLIP_NECK_WIDTH / 2

    right = [
        (x_slit, z_slit),                 # bottom of the slit
        (x_slit, z_tip),
        (x_prong + barb - taper, z_tip),  # narrow tip
        (x_prong + barb, z_land_top),     # lead-in ramp
        (x_prong + barb, z_return_top),
        (x_prong, z_catch),               # release ramp
        (x_prong, z_shoulder),
        (x_neck, z_shoulder),
        (x_neck, z_ring_top),
    ]
    left = [(-x, z) for x, z in reversed(right)]
    return right + left


def build(x_centre: float = 0.0):
    """One cable clip, positioned at x_centre along the lower rail."""
    y_back = cfg.Y_WALL_PLATE_FRONT + cfg.SNAP_CLEARANCE
    tongue_depth = cfg.CABLE_TUNNEL_DEPTH - 2 * cfg.SNAP_CLEARANCE

    # The ring hangs just below the TV plate's bottom edge so they cannot touch.
    z_ring_top = cfg.TV_PLATE_BOTTOM_Z - cfg.CABLE_CLIP_DROP
    z_ring_bottom = z_ring_top - cfg.CABLE_CLIP_HEIGHT

    # 1. Tongue and neck.
    tongue = extrude_xz(Polygon(*tongue_points(z_ring_top), align=None),
                        y_back, y_back + tongue_depth)

    # 2. Ring: rounded square, round bore, slot through the front wall.
    outer = cfg.CABLE_CLIP_BORE + 2 * cfg.CABLE_CLIP_WALL
    y_centre = y_back + outer / 2
    #    Only the front corners are rounded. Rounded back corners would curl
    #    away from the print bed and need supports.
    ring_2d = (
        Pos(0, y_centre) * RectangleRounded(outer, outer, cfg.CABLE_CLIP_CORNER)
        + Pos(0, y_back + outer / 4) * Rectangle(outer, outer / 2)
        - Pos(0, y_centre) * Circle(cfg.CABLE_CLIP_BORE / 2)
        - Pos(0, y_centre + outer / 2) * Rectangle(cfg.CABLE_CLIP_OPENING, outer)
    )
    ring = extrude_xy(ring_2d, z_ring_bottom, z_ring_top)

    part = Pos(x_centre, 0, 0) * (tongue + ring)
    part.label = "cable_clip"
    return part
