"""
tv/enclosure.py - the plastic shell: front bezel and rear cover.

Both are injection-moulded ABS. The rear cover carries the vents, the side
connector recess, the mains inlet opening, the speaker grilles, the slots for
the stand feet and the holes for the VESA and cover screws.
"""

from build123d import Axis, RectangleRounded, extrude, fillet

import config as cfg
from parts.common import xz_plane
from tv.common import cut_all, cyl_w, cyl_z, gy, tbox

HALF_X, HALF_Z = cfg.TV_WIDTH / 2, cfg.TV_HEIGHT / 2
WALL = cfg.ENCLOSURE_WALL


def _outline(inset: float):
    """Rounded TV outline, shrunk by `inset` on every side."""
    return RectangleRounded(cfg.TV_WIDTH - 2 * inset, cfg.TV_HEIGHT - 2 * inset,
                            cfg.TV_CORNER_RADIUS - inset)


# ---------------------------------------------------------------------------
# Front bezel
# ---------------------------------------------------------------------------
def ir_board_posts():
    """(X, Z) of the two bezel posts the IR board is held against."""
    cx, cz, width, _ = cfg.BOARD_IR
    return [(cx - (width / 2 - 2.5), cz), (cx + (width / 2 - 2.5), cz)]


IR_WINDOW_OFFSET = -4.0     # IR receiver position relative to the IR board centre
LED_WINDOW_OFFSET = 6.0     # standby LED
BUTTON_OFFSET = -15.0       # power / menu button
IR_BOARD_FRONT_W = 62.0     # depth of the IR board's component face


def front_bezel():
    split, front = cfg.ENCLOSURE_SPLIT_W, cfg.W_FRONT
    body = extrude(xz_plane(gy(split)) * _outline(0), amount=front - split, dir=(0, 1, 0))
    body = fillet(body.edges().group_by(Axis.Y)[-1], 1.5)          # soften the front edge
    cavity = extrude(xz_plane(gy(split - 1)) * _outline(WALL),
                     amount=cfg.W_LIP_BACK - split + 1, dir=(0, 1, 0))
    opening = tbox(-cfg.ACTIVE_WIDTH / 2 - 0.5, cfg.ACTIVE_WIDTH / 2 + 0.5,
                   cfg.SCREEN_Z - cfg.ACTIVE_HEIGHT / 2 - 0.5,
                   cfg.SCREEN_Z + cfg.ACTIVE_HEIGHT / 2 + 0.5,
                   cfg.W_LIP_BACK - 1, front + 1)
    bezel = body - cavity - opening

    cx, cz, _, _ = cfg.BOARD_IR
    cuts = [
        cyl_w(cx + IR_WINDOW_OFFSET, cz, 6.0, cfg.W_LIP_BACK - 1, front + 1),    # IR window
        cyl_w(cx + LED_WINDOW_OFFSET, cz, 2.0, cfg.W_LIP_BACK - 1, front + 1),   # standby LED
        cyl_z(cx + BUTTON_OFFSET, -HALF_Z - 1, -HALF_Z + WALL + 1, 64.0, 4.5),   # button
    ]
    bezel = cut_all(bezel, cuts)
    for x, z in ir_board_posts():
        bezel += cyl_w(x, z, 4.0, IR_BOARD_FRONT_W, cfg.W_LIP_BACK + 0.1)
    return bezel


def ir_window_lens():
    """Smoked polycarbonate plug that the remote's infrared passes through."""
    cx, cz, _, _ = cfg.BOARD_IR
    return cyl_w(cx + IR_WINDOW_OFFSET, cz, 6.0, cfg.W_LIP_BACK, cfg.W_FRONT)


def brand_badge():
    """Plain badge on the bottom bezel. No logo: this is not any real brand."""
    z = -HALF_Z + cfg.BEZEL_BOTTOM / 2
    return tbox(-22, 22, z - 3.5, z + 3.5, cfg.W_FRONT, cfg.W_FRONT + 0.6)


# ---------------------------------------------------------------------------
# Rear cover
# ---------------------------------------------------------------------------
def vent_positions():
    """(X, Z) centres of every rear-cover vent slot."""
    px, pz = cfg.VENT_TV_PITCH
    spots = []
    # Exhaust band along the top (warm air leaves here).
    for row in range(7):
        for col in range(-8, 9):
            spots.append((col * px, 150.0 + row * pz))
    # Intake bands low down on each side.
    for row in range(3):
        for col in range(4):
            for side in (-1, 1):
                spots.append((side * (182.0 + col * px), -172.0 + row * pz))
    return spots


def speaker_grille_x():
    """X centres of the grille slots under both speakers."""
    return [side * cfg.SPEAKER_X + (i - 7.5) * 5.0 for side in (-1, 1) for i in range(16)]


def jack_recess_boxes():
    """(outer block, open void) of the side recess that holds the connectors."""
    x_wall = cfg.JACK_RECESS_X - WALL
    half = cfg.JACK_RECESS_HALF_Z
    outer = tbox(x_wall, HALF_X + 1, -half - WALL, half + WALL, -1, cfg.JACK_RECESS_W + WALL)
    void = tbox(cfg.JACK_RECESS_X, HALF_X + 2, -half, half, -2, cfg.JACK_RECESS_W)
    return outer, void


def rear_cover(port_openings):
    """port_openings: list of (z0, z1, w0, w1) holes in the connector panel."""
    split = cfg.ENCLOSURE_SPLIT_W
    plane = xz_plane(gy(split))
    try:
        outer = extrude(plane * _outline(0), amount=split, dir=(0, -1, 0), taper=cfg.ENCLOSURE_DRAFT)
        inner = extrude(plane * _outline(WALL), amount=split - WALL, dir=(0, -1, 0),
                        taper=cfg.ENCLOSURE_DRAFT)
    except Exception as err:
        print(f"  note: draft on the rear cover failed ({type(err).__name__}); built without draft")
        outer = extrude(plane * _outline(0), amount=split, dir=(0, -1, 0))
        inner = extrude(plane * _outline(WALL), amount=split - WALL, dir=(0, -1, 0))
    outer = fillet(outer.edges().group_by(Axis.Y)[0], 2.0)        # round the back edge
    cover = outer - inner

    # Side recess: remove a block, then add back a thin-walled pocket.
    block, void = jack_recess_boxes()
    cover = cover - block + ((block - void) & outer)

    cuts = []
    slot_len, slot_w = cfg.VENT_TV_SLOT
    for x, z in vent_positions():
        cuts.append(tbox(x - slot_len / 2, x + slot_len / 2, z - slot_w / 2, z + slot_w / 2, -1, WALL + 1))
    for x in speaker_grille_x():                                   # grilles in the bottom wall
        cuts.append(tbox(x - 1.25, x + 1.25, -HALF_Z - 1, -HALF_Z + WALL + 2, 9, 23))
    for side in (-1, 1):                                           # stand-foot slots
        cuts.append(tbox(side * cfg.FOOT_X - 10.5, side * cfg.FOOT_X + 10.5,
                         -HALF_Z - 1, -HALF_Z + WALL + 2, 19.5, 28.5))
    for sx in (-1, 1):                                             # VESA screw holes
        for sz in (-1, 1):
            cuts.append(cyl_w(sx * cfg.VESA_X / 2, sz * cfg.VESA_Z / 2,
                              cfg.VESA_COVER_HOLE, -1, WALL + 1))
    for x, z in cfg.COVER_BOSSES:                                  # cover screw holes
        cuts.append(cyl_w(x, z, cfg.COVER_SCREW_HOLE, -1, WALL + 1))
    depth, along_z, along_w = cfg.AC_INLET_SIZE                    # mains inlet, -X side wall
    cuts.append(tbox(-HALF_X - 1, -HALF_X + WALL + 2,
                     cfg.AC_INLET_Z - along_z / 2 - 0.4, cfg.AC_INLET_Z + along_z / 2 + 0.4,
                     cfg.AC_INLET_W - along_w / 2 - 0.4, cfg.AC_INLET_W + along_w / 2 + 0.4))
    for z0, z1, w0, w1 in port_openings:                           # connector panel
        cuts.append(tbox(cfg.JACK_RECESS_X - WALL - 1, cfg.JACK_RECESS_X + 1, z0, z1, w0, w1))
    return cut_all(cover, cuts)
