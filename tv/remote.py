"""
tv/remote.py - infrared remote control.

A two-part clamshell with a battery door, a rubber keypad, a small PCB with a
microcontroller and an infrared LED, and two AAA cells.

Modelled in its own local frame (x = length, y = width, z = thickness from
the underside) and then placed at cfg.REMOTE_POSITION, lying on the table in
front of the TV.
"""

from build123d import Axis, Cylinder, Pos, Rot, fillet

import config as cfg
from parts.common import box
from tv.common import cut_all, group

LENGTH, WIDTH, THICK = cfg.REMOTE_SIZE
WALL = cfg.REMOTE_WALL
HL, HW = LENGTH / 2, WIDTH / 2
SPLIT = 11.0              # height where the two shells meet
CORNER = 6.0
Z_PCB = 13.5              # underside of the PCB
Z_KEYPAD = Z_PCB + 1.0    # underside of the rubber mat
Z_BUTTON_TOP = THICK + 1.2

# (kind, x, y, size): "round" size = diameter; "bar" size = (length, width)
BUTTONS = [
    ("round", 66, 0, 8),                       # power
    ("round", 34, 0, 30),                      # navigation ring
    ("round", 6, -13, 8), ("round", 6, 0, 8), ("round", 6, 13, 8),   # back / home / menu
    ("bar", -18, -11, (22, 9)), ("bar", -18, 11, (22, 9)),           # volume, channel
    ("bar", -44, -10, (12, 8)), ("bar", -44, 10, (12, 8)),           # app keys
    ("bar", -60, -10, (12, 8)), ("bar", -60, 10, (12, 8)),
]
BATTERY = (10.5, 44.5)    # AAA cell: diameter, length
DOOR = (-76.0, -24.0, 14.0)   # battery door: x from, x to, half width


def _rounded_block(hl, hw, z0, z1, radius):
    block = box(-hl, hl, -hw, hw, z0, z1)
    return fillet(block.edges().filter_by(Axis.Z), radius)


def _button(kind, x, y, size, z0, z1, grow=0.0):
    if kind == "round":
        return Pos(x, y, (z0 + z1) / 2) * Cylinder(size / 2 + grow, z1 - z0)
    length, width = size
    return box(x - length / 2 - grow, x + length / 2 + grow,
               y - width / 2 - grow, y + width / 2 + grow, z0, z1)


def _ir_led_hole():
    return Pos(HL - 1, 0, SPLIT) * Rot(Y=90) * Cylinder(2.7, 6)


def bottom_shell():
    shell = _rounded_block(HL, HW, 0, SPLIT, CORNER)
    shell = fillet(shell.edges().group_by(Axis.Z)[0], 2.5)        # soft underside edge
    shell -= _rounded_block(HL - WALL, HW - WALL, WALL, SPLIT + 1, CORNER - WALL)
    x0, x1, half = DOOR
    shell -= box(x0, x1, -half, half, -1, WALL + 0.01)
    return shell - _ir_led_hole()


def battery_door():
    x0, x1, half = DOOR
    return box(x0, x1, -half, half, 0, WALL)


def top_shell():
    shell = _rounded_block(HL, HW, SPLIT, THICK, CORNER)
    shell = fillet(shell.edges().group_by(Axis.Z)[-1], 2.5)       # soft top edge
    shell -= _rounded_block(HL - WALL, HW - WALL, SPLIT - 1, THICK - WALL, CORNER - WALL)
    holes = [_button(kind, x, y, size, THICK - WALL - 1, THICK + 1, grow=0.3)
             for kind, x, y, size in BUTTONS]
    return cut_all(shell, holes) - _ir_led_hole()


def keypad():
    """Rubber mat with every button standing up through the top shell."""
    mat = box(-75, 75, -19, 19, Z_KEYPAD, Z_KEYPAD + 1.0)
    for kind, x, y, size in BUTTONS:
        mat += _button(kind, x, y, size, Z_KEYPAD + 1.0, Z_BUTTON_TOP)
    return mat


def electronics():
    """PCB, microcontroller and the infrared LED that points out of the front."""
    pcb = box(-75, 75, -19, 19, Z_PCB, Z_PCB + 1.0)
    mcu = box(40, 46, -3, 3, Z_PCB - 1.7, Z_PCB)
    led = Pos(78.5, 0, SPLIT) * Rot(Y=90) * Cylinder(2.5, 7)
    return group([pcb, mcu, led])


def batteries():
    dia, length = BATTERY
    z = WALL + 0.3 + dia / 2
    x_mid = (DOOR[0] + DOOR[1]) / 2
    return group(Pos(x_mid, side * (dia / 2 + 0.5), z) * Rot(Y=90) * Cylinder(dia / 2, length)
                 for side in (-1, 1))


def place(shape):
    """Move a remote part from its local frame to where it is shown."""
    return Pos(*cfg.REMOTE_POSITION) * shape


def build() -> dict:
    """All remote parts by name, already placed."""
    parts = {
        "remote_top_shell": top_shell(),
        "remote_keypad": keypad(),
        "remote_electronics": electronics(),
        "remote_batteries": batteries(),
        "remote_battery_door": battery_door(),
        "remote_bottom_shell": bottom_shell(),
    }
    return {name: place(shape) for name, shape in parts.items()}
