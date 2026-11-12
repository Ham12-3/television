"""
tv/panel.py - everything that makes the picture, plus the steel chassis.

Front to back:
    LCD cell            the glass sandwich that forms the image
    mould frame         plastic frame the glass rests on
    optical films       diffuser sheet and two prism sheets
    diffuser plate      evens out the light
    (optical cavity)    air gap where light from the LEDs spreads
    support pins        stop the diffuser sagging
    reflector sheet     white sheet that sends stray light forward
    LED strips          aluminium PCBs with LEDs and lenses
    back chassis        pressed steel tray; everything else bolts to it
    source PCBs + COFs  drive the columns of the LCD, folded round the bottom
"""

from build123d import Axis, fillet

import config as cfg
from tv.common import centred, cone_w, cut_all, cyl_w, fuse, group, tbox

SZ = cfg.SCREEN_Z   # panel centre height


def lcd_cell():
    return centred(cfg.HALF_CELL[0], cfg.HALF_CELL[1], cfg.W_CELL_BACK, cfg.W_CELL_FRONT, SZ)


def optical_films():
    """Three thin sheets; returned separately so the viewer can fan them out."""
    sheets = []
    for i in range(cfg.FILM_COUNT):
        w0 = cfg.W_FILMS_BACK + i * cfg.FILM_THICKNESS
        sheets.append(centred(cfg.HALF_FILM[0], cfg.HALF_FILM[1], w0, w0 + cfg.FILM_THICKNESS, SZ))
    return sheets


def diffuser_plate():
    return centred(cfg.HALF_FILM[0], cfg.HALF_FILM[1], cfg.W_DIFFUSER_BACK, cfg.W_FILMS_BACK, SZ)


def mould_frame():
    """Plastic frame: a skirt round the tray wall plus a lip the glass sits on."""
    gap = 0.2
    in_x, in_z = cfg.HALF_TRAY_OUT[0] + gap, cfg.HALF_TRAY_OUT[1] + gap
    out_x, out_z = in_x + cfg.FRAME_WALL, in_z + cfg.FRAME_WALL
    w_skirt = cfg.W_TRAY_FRONT - cfg.FRAME_SKIRT
    solid = centred(out_x, out_z, w_skirt, cfg.W_CELL_BACK, SZ)
    pocket = centred(in_x, in_z, w_skirt - 1, cfg.W_FRAME_LIP_BACK, SZ)
    opening = centred(cfg.ACTIVE_WIDTH / 2 + 2, cfg.ACTIVE_HEIGHT / 2 + 2,
                      w_skirt - 1, cfg.W_CELL_BACK + 1, SZ)
    return solid - pocket - opening


def frame_outer_bottom_z() -> float:
    return SZ - (cfg.HALF_TRAY_OUT[1] + 0.2 + cfg.FRAME_WALL)


def back_chassis(standoffs):
    """Steel tray with every pillar that is pressed or riveted into it.

    standoffs: list of (X, Z) board mounting points.
    """
    t = cfg.TRAY_THICKNESS
    tray = centred(cfg.HALF_TRAY_OUT[0], cfg.HALF_TRAY_OUT[1], cfg.W_TRAY_BACK, cfg.W_TRAY_FRONT, SZ)
    tray -= centred(cfg.HALF_TRAY_IN[0], cfg.HALF_TRAY_IN[1], cfg.W_TRAY_FLOOR, cfg.W_TRAY_FRONT - t, SZ)
    tray -= centred(cfg.HALF_TRAY_IN[0] - cfg.TRAY_FLANGE, cfg.HALF_TRAY_IN[1] - cfg.TRAY_FLANGE,
                    cfg.W_TRAY_FRONT - t - 1, cfg.W_TRAY_FRONT + 1, SZ)

    pillars, holes = [], []
    # Board standoffs: short pillars with an M3 thread.
    for x, z in standoffs:
        pillars.append(cyl_w(x, z, cfg.STANDOFF_DIA, cfg.W_PCB_FRONT, cfg.W_TRAY_BACK + 0.1))
        holes.append(cyl_w(x, z, 3.0, cfg.W_PCB_FRONT - 1, cfg.W_TRAY_FLOOR + 1))
    # VESA pillars: reach the rear cover and take the wall-mount screws.
    # Threads are not modelled; holes are drawn at the screw's nominal diameter.
    for sx in (-1, 1):
        for sz in (-1, 1):
            x, z = sx * cfg.VESA_X / 2, sz * cfg.VESA_Z / 2
            pillars.append(cyl_w(x, z, cfg.BOSS_VESA_DIA, cfg.ENCLOSURE_WALL, cfg.W_TRAY_BACK + 0.1))
            holes.append(cyl_w(x, z, 4.0, cfg.ENCLOSURE_WALL - 1, cfg.ENCLOSURE_WALL + 14))
    # Rear-cover pillars: the cover screws go into these.
    for x, z in cfg.COVER_BOSSES:
        pillars.append(cyl_w(x, z, cfg.BOSS_COVER_DIA, cfg.ENCLOSURE_WALL, cfg.W_TRAY_BACK + 0.1))
        holes.append(cyl_w(x, z, 3.0, cfg.ENCLOSURE_WALL - 1, cfg.ENCLOSURE_WALL + 10))
    # Hole for the LED harness to pass from the driver board into the tray.
    hx, hz, hd = cfg.LED_HARNESS_HOLE
    holes.append(cyl_w(hx, hz, hd, cfg.W_TRAY_BACK - 1, cfg.W_TRAY_FLOOR + 1))

    return cut_all(fuse([tray] + pillars), holes)


def led_backlight():
    """Returns (strip PCBs, LED packages, lenses) as three grouped shapes."""
    half_len, half_w = cfg.LED_STRIP_LENGTH / 2, cfg.LED_STRIP_WIDTH / 2
    lx, lz, lh = cfg.LED_SIZE

    # One lens, then copies. A domed cap with a pocket that clears the LED.
    lens = cyl_w(0, 0, cfg.LED_LENS_DIA, cfg.W_STRIP_TOP, cfg.W_STRIP_TOP + cfg.LED_LENS_HEIGHT)
    lens = fillet(lens.edges().group_by(Axis.Y)[-1], cfg.LED_LENS_HEIGHT * 0.7)
    lens -= tbox(-lx / 2 - 0.3, lx / 2 + 0.3, -lz / 2 - 0.3, lz / 2 + 0.3,
                 cfg.W_STRIP_TOP - 1, cfg.W_STRIP_TOP + lh + 0.3)

    from build123d import Pos
    strips, leds, lenses = [], [], []
    for z in cfg.led_strip_centres_z():
        strips.append(tbox(-half_len, half_len, z - half_w, z + half_w,
                           cfg.W_TRAY_FLOOR, cfg.W_STRIP_TOP))
        for x in cfg.led_centres_x():
            leds.append(tbox(x - lx / 2, x + lx / 2, z - lz / 2, z + lz / 2,
                             cfg.W_STRIP_TOP, cfg.W_STRIP_TOP + lh))
            lenses.append(Pos(x, 0, z) * lens)
    return group(strips), group(leds), group(lenses)


def reflector():
    """White sheet lying on the strips, with a hole for every lens and pin."""
    w0 = cfg.W_STRIP_TOP
    sheet = centred(cfg.HALF_FILM[0], cfg.HALF_FILM[1], w0, w0 + cfg.REFLECTOR_THICKNESS, SZ)
    holes = [cyl_w(x, z, cfg.LED_LENS_DIA + 1, w0 - 1, w0 + 1)
             for z in cfg.led_strip_centres_z() for x in cfg.led_centres_x()]
    holes += [cyl_w(x, z, 9.0, w0 - 1, w0 + 1) for x, z in cfg.support_pin_centres()]
    return cut_all(sheet, holes)


def support_pins():
    """Tapered plastic pins from the tray floor up to the diffuser."""
    return group(cone_w(x, z, 8.0, 2.0, cfg.W_TRAY_FLOOR, cfg.W_DIFFUSER_BACK)
                 for x, z in cfg.support_pin_centres())


def source_boards():
    """The two long, narrow PCBs that feed the LCD's column drivers.

    Returns (PCBs, connectors, COFs). Each chip-on-film (COF) is a flexible
    strip bonded to the bottom edge of the glass that wraps round the frame
    and chassis to reach its PCB on the back of the tray.
    """
    centre, length, height = cfg.SOURCE_PCB
    w_front = cfg.W_TRAY_BACK - 0.2          # insulating gap to the steel
    w_back = w_front - 1.0
    z_top = cfg.TRAY_BOTTOM_Z + 1.6 + height
    z_bot = z_top - height

    pcbs = [tbox(s * centre - length / 2, s * centre + length / 2, z_bot, z_top, w_back, w_front)
            for s in (-1, 1)]
    sockets = [tbox(x - 17, x + 17, z_top - 5.5, z_top - 0.5, w_back - 2.0, w_back)
               for x in cfg.SOURCE_CONNECTOR_X]

    film = 0.2
    z_cell = SZ - cfg.HALF_CELL[1]                   # bottom edge of the glass
    z_run = frame_outer_bottom_z() - 0.4             # passes just under the frame
    cofs = []
    for s in (-1, 1):
        for x in cfg.COF_X:
            x0, x1 = s * x - cfg.COF_WIDTH / 2, s * x + cfg.COF_WIDTH / 2
            cofs.append(fuse([
                tbox(x0, x1, z_run - film, z_cell, cfg.W_CELL_BACK + 0.1, cfg.W_CELL_BACK + 0.1 + film),
                tbox(x0, x1, z_run - film, z_run, w_back - film, cfg.W_CELL_BACK + 0.1 + film),
                tbox(x0, x1, z_run - film, z_bot + 10, w_back - film, w_back),
            ]))
    return group(pcbs), group(sockets), group(cofs)


def source_socket_top_w() -> float:
    """Depth of the top face of the source-board FFC sockets (for cable routing)."""
    return cfg.W_TRAY_BACK - 0.2 - 1.0 - 2.0


def source_socket_z() -> float:
    return cfg.TRAY_BOTTOM_Z + 1.6 + cfg.SOURCE_PCB[2] - 3.0
