"""
tv/hardware.py - speakers, mains inlet, screws, stand feet and all cables.

Cables are drawn as straight box segments along the routes they take. They
show what connects to what and where it runs; they are not harness drawings.
"""

from build123d import Axis, fillet

import config as cfg
from parts.common import box
from tv.board_data import IR, LED_DRIVER, MAIN, PSU, TCON, WIFI
from tv.boards import connector_top
from tv.common import cyl_w, fuse, group, tbox
from tv.common import ribbon as _ribbon
from tv.common import wire as _wire
from tv.panel import source_socket_top_w, source_socket_z

HALF_X, HALF_Z = cfg.TV_WIDTH / 2, cfg.TV_HEIGHT / 2


def speakers():
    """Two down-firing full-range speaker boxes at the bottom corners."""
    sx, sz, sd = cfg.SPEAKER_SIZE
    z0, w0 = cfg.SPEAKER_BOTTOM_Z, cfg.SPEAKER_BACK_W
    units = []
    for side in (-1, 1):
        x = side * cfg.SPEAKER_X
        enclosure = tbox(x - sx / 2, x + sx / 2, z0, z0 + sz, w0, w0 + sd)
        enclosure = fillet(enclosure.edges().filter_by(Axis.X), 3.0)       # rounded long edges
        driver = tbox(x - 40, x + 40, z0 - 1.5, z0 + 1.0, w0 + 4, w0 + sd - 8)   # faces the grille
        units.append(enclosure + driver)
    return group(units)


def ac_inlet():
    """Two-pin mains inlet (IEC C8 style) in the side wall next to the PSU."""
    depth, along_z, along_w = cfg.AC_INLET_SIZE
    return tbox(-HALF_X, -HALF_X + depth,
                cfg.AC_INLET_Z - along_z / 2, cfg.AC_INLET_Z + along_z / 2,
                cfg.AC_INLET_W - along_w / 2, cfg.AC_INLET_W + along_w / 2)


def cover_screws():
    """M3 pan-head screws holding the rear cover to the chassis pillars."""
    return group(cyl_w(x, z, 5.6, -2.0, 0.0) + cyl_w(x, z, 3.0, 0.0, 9.0)
                 for x, z in cfg.COVER_BOSSES)


def stand_feet():
    """Tabletop feet. Not fitted when the TV hangs on the wall mount."""
    width, length, tall = cfg.FOOT_SIZE
    y_mid = cfg.STACK_DEPTH + cfg.TV_DEPTH / 2
    feet = []
    for side in (-1, 1):
        x = side * cfg.FOOT_X
        bar = box(x - width / 2, x + width / 2, y_mid - length / 2, y_mid + length / 2,
                  -HALF_Z - tall, -HALF_Z)
        bar = fillet(bar.edges().filter_by(Axis.Z), 8.0)       # rounded ends
        bar = fillet(bar.edges().group_by(Axis.Z)[-1], 3.0)    # soft top edge
        tongue = tbox(x - 10, x + 10, -HALF_Z, -HALF_Z + 25, 20, 28)    # slots into the cover
        feet.append(bar + tongue)
    return group(feet)


def cables() -> dict:
    """Every internal cable, by name."""
    out = {}
    harness_t = 2.5
    specs = []          # the route of each cable, in the order they are made

    # Local wrappers that remember each route, so the viewer can draw the
    # cables as round wires and ribbons instead of the plain CAD boxes.
    def wire(points, size):
        specs.append({"kind": "wire", "points": [list(p) for p in points],
                      "width": size[0], "thick": size[1]})
        return _wire(points, size)

    def ribbon(points, width):
        specs.append({"kind": "ribbon", "points": [list(p) for p in points],
                      "width": width, "thick": 0.3})
        return _ribbon(points, width)

    # PSU -> main board: 12 V, ground, standby and backlight control.
    xa, za, wa = connector_top(PSU, "CN2")
    xb, zb, wb = connector_top(MAIN, "CN1")
    out["cable_psu_to_main"] = wire([(xa, za, wa - harness_t / 2), (xb, zb, wb - harness_t / 2)],
                                    (12, harness_t))

    # PSU -> LED driver: 36 V, ground, enable, dimming.
    xa, za, wa = connector_top(PSU, "CN3")
    xb, zb, wb = connector_top(LED_DRIVER, "CN1")
    w = wa - harness_t / 2
    x_turn = xa + 12
    out["cable_psu_to_led_driver"] = wire(
        [(xa, za, w), (x_turn, za, w), (x_turn, zb, w), (xb, zb, w)], (8, harness_t))

    # LED driver -> LED strips, through the hole in the tray floor.
    xa, za, wa = connector_top(LED_DRIVER, "CN2")
    hx, hz, _ = cfg.LED_HARNESS_HOLE
    w = wa - 3.0
    out["cable_led_strips"] = wire([(xa, za, w), (hx, hz, w), (hx, hz, cfg.W_TRAY_FLOOR - 3.0)], (6, 6))

    # Mains inlet -> PSU.
    xb, zb, wb = connector_top(PSU, "CN1")
    x_inlet = -HALF_X + cfg.AC_INLET_SIZE[0] + 3.0
    out["cable_mains"] = wire([(x_inlet, zb, wb - harness_t / 2), (xb, zb, wb - harness_t / 2)],
                              (6, harness_t))

    # Main board -> T-con: LVDS video on a flat flexible cable.
    xa, za, wa = connector_top(MAIN, "CN2")
    xb, zb, wb = connector_top(TCON, "CN1")
    w = wa - 0.15
    out["ffc_lvds"] = ribbon([(xa, za, w), (xa, zb, w), (xb, zb, w)], 26)

    # T-con -> source boards: two flat flexible cables.
    w_low = source_socket_top_w() - 0.15
    z_sock = source_socket_z()
    for name, ref, x_sock in (("ffc_source_a", "CN2", cfg.SOURCE_CONNECTOR_X[0]),
                              ("ffc_source_b", "CN3", cfg.SOURCE_CONNECTOR_X[1])):
        xa, za, wa = connector_top(TCON, ref)
        w = wa - 0.15
        z_drop = cfg.BOARD_TCON[1] - cfg.BOARD_TCON[3] / 2 - 7.5      # just below the T-con
        points = [(xa, za, w), (xa, z_drop, w), (xa, z_drop, w_low)]
        if abs(x_sock - xa) > 1:                                       # needs a sideways run
            z_run = z_drop - 11
            points += [(xa, z_run, w_low), (x_sock, z_run, w_low)]
        points.append((x_sock if abs(x_sock - xa) > 1 else xa, z_sock, w_low))
        out[name] = ribbon(points, 30)

    # Main board -> speakers.
    xa, za, wa = connector_top(MAIN, "CN3")
    w = wa - 1.5
    z_spk_top = cfg.SPEAKER_BOTTOM_Z + cfg.SPEAKER_SIZE[1]
    x_spk_edge = cfg.SPEAKER_X + cfg.SPEAKER_SIZE[0] / 2
    z_mid = cfg.SPEAKER_BOTTOM_Z + cfg.SPEAKER_SIZE[1] / 2
    out["cable_speaker_right"] = wire(
        [(xa + 2, za, w), (xa + 2, z_mid, w), (x_spk_edge + 1.5, z_mid, w)], (3, 3))
    z_run = z_spk_top + 4
    out["cable_speaker_left"] = wire(
        [(xa - 2, za, w), (xa - 2, z_run, w), (-cfg.SPEAKER_X, z_run, w),
         (-cfg.SPEAKER_X, z_spk_top + 1.5, w)], (3, 3))

    # Main board -> IR / LED / key board, round the bottom of the chassis.
    xa, za, wa = connector_top(MAIN, "CN4")
    xb, zb, wb = connector_top(IR, "CN1")
    w_gap = 33.2                                   # between the speakers and the source boards
    z_low = cfg.BOARD_IR[1] + 1.25
    w_ir_back = wb - 4.5 - cfg.PCB_THICKNESS       # back face of the IR board
    out["cable_ir_board"] = wire(
        [(xa, za, wa - 1), (xa, za - 9, wa - 1), (xa, za - 9, w_gap), (xa, z_low, w_gap),
         (xb, z_low, w_gap), (xb, z_low, w_ir_back - 1)], (2, 2))

    # Main board -> Wi-Fi module (USB).
    xa, za, wa = connector_top(MAIN, "CN5")
    xb, zb, wb = connector_top(WIFI, "CN1")
    out["cable_wifi"] = wire([(xb, za, wa - 1), (xb, zb, wb - 1)], (2, 2))

    ROUTES.clear()
    ROUTES.update(zip(out.keys(), specs))       # one route per cable, same order
    return out


# name -> {"kind", "points" [(X, Z, w)], "width", "thick"}; filled by cables().
ROUTES = {}


def cable_routes() -> dict:
    """The path of every cable, for the viewer."""
    if not ROUTES:
        cables()
    return ROUTES
