"""
tv/board_data.py - what is on each circuit board, and where.

This is the single source for the 3D boards, the bill of materials and the
connector tables in ELECTRICAL.md.

Each component is a dict:
    ref    reference designator (U1, C3, CN2 ...)
    kind   ic / cap / connector / port / magnetic / heatsink / passive / shield
    desc   what it is (generic description, not a specific manufacturer's part)
    u, v   position of its centre on the board, mm from the board centre
           (u runs along X, v runs along Z)
    size   box:  (length along u, length along v, height)
           cyl:  (diameter, height)             standing cylinder
           cyl_u / cyl_v: (diameter, length)    cylinder lying along u or v
    shape  "box" (default), "cyl", "cyl_u", "cyl_v", "fins"
    lift   height of its underside above the board (default 0)
    over   True if it deliberately sits over another part (heatsink on a chip)

Positions are a plausible layout, not a routed PCB design.
"""

import config as cfg


def C(ref, kind, desc, u, v, size, shape="box", **more):
    return dict(ref=ref, kind=kind, desc=desc, u=u, v=v, size=size, shape=shape, **more)


def row(prefix, first, count, u, v, du, dv, size, kind, desc):
    """A line of identical small parts (decoupling capacitors and the like)."""
    return [C(f"{prefix}{first + i}", kind, desc, u + i * du, v + i * dv, size)
            for i in range(count)]


# How far each port's outer face is from the board centre: board edge, then
# through the connector panel, then PORT_PROTRUSION beyond it.
_PORT_FACE = cfg.JACK_RECESS_X + cfg.PORT_PROTRUSION - cfg.BOARD_MAIN[0]


def port(ref, desc, v, depth, width, height):
    return C(ref, "port", desc, _PORT_FACE - depth / 2, v, (depth, width, height))


# ---------------------------------------------------------------------------
# Main board ("motherboard"): 170 x 190 mm, 4-layer FR-4
# ---------------------------------------------------------------------------
MAIN = dict(
    name="mainboard", title="Main board", centre=cfg.BOARD_MAIN[:2], size=cfg.BOARD_MAIN[2:],
    colour=(0.05, 0.38, 0.16), layers=4,
    holes=[(-60, 90), (80, 90), (-60, -90), (80, -90)],
    slots=[],
    parts=[
        # --- External ports, top to bottom along the connector edge ---------
        port("J1", "HDMI 2.0 input 1 (type A receptacle)", 76.5, 12, 15, 6.2),
        port("J2", "HDMI 2.0 input 2 with ARC (type A receptacle)", 59.0, 12, 15, 6.2),
        port("J3", "USB 2.0 host 1 (type A receptacle)", 42.5, 14, 14, 7.0),
        port("J4", "USB 2.0 host 2 (type A receptacle)", 26.0, 14, 14, 7.0),
        port("J5", "Optical digital audio out (TOSLINK)", 11.5, 13, 10, 10.0),
        port("J6", "Headphone out, 3.5 mm stereo jack", 0.5, 12, 7, 6.0),
        port("J7", "Composite video in (RCA, yellow)", -10.5, 14, 10, 11.0),
        port("J8", "Audio in left (RCA, white)", -23.0, 14, 10, 11.0),
        port("J9", "Audio in right (RCA, red)", -35.5, 14, 10, 11.0),
        port("J10", "Antenna / cable RF in (IEC coaxial)", -49.0, 20, 12, 12.0),
        port("J11", "Ethernet 10/100 (RJ45 with magnetics)", -65.5, 21, 16, 13.5),

        # --- Processing core ------------------------------------------------
        C("U1", "ic", "Smart-TV system-on-chip, quad-core ARM, BGA", -10, 10, (23, 23, 1.6)),
        C("HS1", "heatsink", "Aluminium finned heatsink 40 x 40 x 10 on U1", -10, 10, (40, 40, 10),
          shape="fins", lift=1.6, over=True),
        C("U2", "ic", "DDR3 SDRAM 512 MB, FBGA", 20, 22, (8, 11, 1.1)),
        C("U3", "ic", "DDR3 SDRAM 512 MB, FBGA", 20, 6, (8, 11, 1.1)),
        C("U4", "ic", "eMMC flash 8 GB, BGA", 22, -14, (11.5, 13, 1.0)),
        C("U5", "ic", "SPI NOR flash 16 Mbit (boot loader), SOIC-8", -40, 30, (5, 6, 1.7)),
        C("Y1", "passive", "Crystal 24 MHz", -38, 21, (3.2, 2.5, 0.8)),

        # --- Tuner ----------------------------------------------------------
        C("TU1", "shield", "Silicon tuner + demodulator under shield can", 52, -49, (28, 22, 4.0)),

        # --- Audio ----------------------------------------------------------
        C("U7", "ic", "Class-D stereo audio amplifier 2 x 8 W, TSSOP", -52, -50, (10, 6.2, 1.2)),
        C("L1", "magnetic", "Audio output filter inductor 22 uH", -68, -36, (7, 7, 4.5)),
        C("L2", "magnetic", "Audio output filter inductor 22 uH", -68, -45, (7, 7, 4.5)),
        C("L3", "magnetic", "Audio output filter inductor 22 uH", -68, -54, (7, 7, 4.5)),
        C("L4", "magnetic", "Audio output filter inductor 22 uH", -68, -63, (7, 7, 4.5)),
        C("C1", "cap", "Electrolytic 470 uF 25 V (amplifier supply)", -40, -68, (8, 10), "cyl"),
        C("C2", "cap", "Electrolytic 470 uF 25 V (amplifier supply)", -28, -68, (8, 10), "cyl"),

        # --- On-board power: three buck converters and a linear regulator ----
        C("U8", "ic", "Buck converter 12 V to 5 V, 3 A", -55, 24, (3, 3, 1.0)),
        C("L5", "magnetic", "Buck inductor 4.7 uH", -64, 24, (6, 6, 4.0)),
        C("U9", "ic", "Buck converter 12 V to 3.3 V, 2 A", -55, 12, (3, 3, 1.0)),
        C("L6", "magnetic", "Buck inductor 4.7 uH", -64, 12, (6, 6, 4.0)),
        C("U10", "ic", "Buck converter 12 V to 1.1 V core, 3 A", -55, 0, (3, 3, 1.0)),
        C("L7", "magnetic", "Buck inductor 2.2 uH", -64, 0, (6, 6, 4.0)),
        C("U14", "ic", "LDO regulator 3.3 V to 1.5 V (DDR), SOT-223", 40, -5, (6.5, 7, 1.7)),
        C("C3", "cap", "Electrolytic 220 uF 16 V", 30, 48, (6.3, 8), "cyl"),
        C("C4", "cap", "Electrolytic 220 uF 16 V", 40, 48, (6.3, 8), "cyl"),

        # --- Port support ---------------------------------------------------
        C("U11", "ic", "USB power switch with current limit, SOT-23-5", 62, 34, (3, 3, 1.2)),
        C("U12", "ic", "HDMI ESD protection array", 72, 76.5, (2, 4, 0.8)),
        C("U13", "ic", "HDMI ESD protection array", 72, 59.0, (2, 4, 0.8)),

        # --- Internal connectors --------------------------------------------
        C("CN1", "connector", "Power in from PSU, 12-pin 2.0 mm wafer", -81, 62, (6, 26, 8)),
        C("CN2", "connector", "LVDS to T-con, 51-pin 0.5 mm FFC socket", -38, -89.25, (32, 5.5, 2)),
        C("CN3", "connector", "Speakers, 4-pin 2.0 mm wafer", 47, -91, (10, 6, 8)),
        C("CN4", "connector", "IR / LED / key board, 6-pin 1.25 mm", 7, -92, (9.5, 4, 4.5)),
        C("CN5", "connector", "Wi-Fi / Bluetooth module (USB), 4-pin 1.25 mm", -3, 92, (7, 4, 4.5)),
        C("CN6", "connector", "Service UART header, 4-pin 2.54 mm", -40, 85, (10, 2.5, 6)),
    ]
    # --- Decoupling capacitors and termination resistors ----------------------
    + row("C", 10, 10, -34, -8, 0, 4, (1.6, 0.8, 0.8), "passive", "Ceramic capacitor 100 nF 0603")
    + row("C", 20, 10, -28, -14, 4, 0, (0.8, 1.6, 0.8), "passive", "Ceramic capacitor 100 nF 0603")
    + row("C", 30, 7, 28, 2, 0, 4, (1.6, 0.8, 0.8), "passive", "Ceramic capacitor 100 nF 0603")
    + row("R", 1, 4, 34, -58, 0, 6, (1.6, 0.8, 0.5), "passive", "Resistor 0603")
    + row("R", 5, 4, 66, 66, 0, -6, (1.6, 0.8, 0.5), "passive", "Resistor array, HDMI DDC pull-ups"),
)

# ---------------------------------------------------------------------------
# Power supply board: 170 x 130 mm, single-sided, flyback converter
# Mains (primary) side is u < 5; isolated (secondary) side is u > 15.
# ---------------------------------------------------------------------------
PSU = dict(
    name="psu_board", title="Power supply board", centre=cfg.BOARD_PSU[:2], size=cfg.BOARD_PSU[2:],
    colour=(0.72, 0.60, 0.33), layers=1,
    holes=[(-80, 60), (80, 60), (-80, -60), (80, -60)],
    slots=[(8, 17, 2, 14)],     # isolation slot between primary and secondary
    parts=[
        # --- Mains input and EMI filter (primary) ---------------------------
        C("CN1", "connector", "AC input, 2-pin 3.96 mm header", -77, 0, (12, 10, 14)),
        C("F1", "passive", "Fuse T2.5 A 250 V, 5 x 20 mm in clips", -62, 18, (8, 22, 8)),
        C("RV1", "passive", "Varistor 275 VAC (surge protection)", -62, -14, (5, 12, 13)),
        C("NTC1", "passive", "NTC inrush limiter 5 ohm", -62, -32, (5, 10, 12)),
        C("CX1", "cap", "X2 film capacitor 0.22 uF 275 VAC", -48, 12, (8, 18, 14)),
        C("CX2", "cap", "X2 film capacitor 0.1 uF 275 VAC", -30, -14, (8, 18, 14)),
        C("LF1", "magnetic", "Common-mode choke 20 mH", -48, -14, (12, 18, 20)),
        C("LF2", "magnetic", "Common-mode choke 10 mH", -30, 12, (12, 18, 20)),
        C("BD1", "ic", "Bridge rectifier 4 A 600 V", -48, 40, (22, 4, 19)),
        C("C1", "cap", "Bulk electrolytic 100 uF 400 V", -30, -44, (18, 32), "cyl_u"),
        # --- Flyback converter ----------------------------------------------
        C("U1", "ic", "Flyback PWM controller, SOIC-8", -10, 20, (5, 6, 1.7)),
        C("R1", "passive", "Start-up resistor 1206", -4, 32, (3.2, 1.6, 0.6)),
        C("R2", "passive", "Start-up resistor 1206", -4, 28, (3.2, 1.6, 0.6)),
        C("HS1", "heatsink", "Aluminium heatsink plate (primary switch)", -16, 44, (40, 3, 22)),
        C("Q1", "ic", "Power MOSFET 650 V, TO-220F", -16, 40.2, (10, 4.5, 16)),
        C("T1", "magnetic", "Flyback transformer, reinforced insulation", 5, -8, (32, 28, 22)),
        C("U2", "ic", "Optocoupler (feedback across the isolation barrier)", 8, 30, (6.5, 4.6, 3.5)),
        C("CY1", "cap", "Y1 safety capacitor 2.2 nF", 8, 44, (4, 9, 11)),
        # --- Secondary: rectifiers, filters, regulation ---------------------
        C("HS2", "heatsink", "Aluminium heatsink plate (output rectifiers)", 40, 44, (50, 3, 22)),
        C("D1", "ic", "Schottky rectifier 20 A 60 V (12 V rail), TO-220", 28, 40.2, (10, 4.5, 16)),
        C("D2", "ic", "Ultrafast rectifier 5 A 200 V (36 V rail), TO-220", 52, 40.2, (10, 4.5, 16)),
        C("C2", "cap", "Electrolytic 1000 uF 16 V", 30, 24, (10, 16), "cyl"),
        C("C3", "cap", "Electrolytic 1000 uF 16 V", 44, 24, (10, 16), "cyl"),
        C("L1", "magnetic", "Output filter inductor 3.3 uH (12 V)", 58, 24, (8, 10), "cyl"),
        C("C4", "cap", "Electrolytic 470 uF 16 V", 70, 24, (8, 12), "cyl"),
        C("C5", "cap", "Electrolytic 220 uF 63 V", 30, 6, (10, 20), "cyl"),
        C("C6", "cap", "Electrolytic 220 uF 63 V", 44, 6, (10, 20), "cyl"),
        C("L2", "magnetic", "Output filter inductor 10 uH (36 V)", 58, 6, (8, 10), "cyl"),
        C("U3", "ic", "Shunt reference 2.5 V, TO-92", 20, 14, (4.5, 3.5, 5)),
        # --- Outputs --------------------------------------------------------
        C("CN2", "connector", "To main board, 12-pin 2.0 mm wafer", 78, 42, (6, 26, 8)),
        C("CN3", "connector", "To LED driver, 6-pin 2.0 mm wafer", 78, -40, (6, 15, 8)),
    ],
)

# ---------------------------------------------------------------------------
# Timing controller (T-con) board: 130 x 45 mm
# ---------------------------------------------------------------------------
TCON = dict(
    name="tcon_board", title="T-con board", centre=cfg.BOARD_TCON[:2], size=cfg.BOARD_TCON[2:],
    colour=(0.05, 0.38, 0.16), layers=4,
    holes=[(-61, 18.5), (61, 18.5), (-61, -18.5), (0, -18.5)],
    slots=[],
    parts=[
        C("U1", "ic", "Timing controller, LVDS in / mini-LVDS out, QFP", 10, 4, (14, 14, 1.4)),
        C("U2", "ic", "Panel power-management IC (AVDD, VGH, VGL, VCOM), QFN", -25, 6, (6, 6, 0.9)),
        C("U3", "ic", "Gamma reference buffer, TSSOP", 35, 8, (6.5, 4.4, 1.1)),
        C("U4", "ic", "EEPROM (panel timing data), SOIC-8", -10, -6, (5, 6, 1.7)),
        C("U5", "ic", "Gate-driver level shifter, QFN", 38, -6, (5, 5, 0.9)),
        C("L1", "magnetic", "Boost inductor 10 uH (AVDD)", -42, 10, (6, 6, 4.0)),
        C("L2", "magnetic", "Buck inductor 4.7 uH (logic 3.3 V)", -42, 0, (6, 6, 4.0)),
        C("C1", "cap", "Tantalum capacitor 22 uF 25 V", -25, -6, (7.3, 4.3, 2.8)),
        C("C2", "cap", "Tantalum capacitor 22 uF 25 V", -42, -10, (7.3, 4.3, 2.8)),
        C("CN1", "connector", "LVDS from main board, 51-pin 0.5 mm FFC socket", 62.25, -1, (5.5, 30, 2)),
        C("CN2", "connector", "To source board A, 60-pin 0.5 mm FFC socket", 43, -18.75, (34, 5.5, 2)),
        C("CN3", "connector", "To source board B, 60-pin 0.5 mm FFC socket", -36, -18.75, (34, 5.5, 2)),
    ],
)

# ---------------------------------------------------------------------------
# LED backlight driver board: 90 x 50 mm, boost converter, constant current
# ---------------------------------------------------------------------------
LED_DRIVER = dict(
    name="led_driver_board", title="LED driver board", centre=cfg.BOARD_LED_DRIVER[:2],
    size=cfg.BOARD_LED_DRIVER[2:], colour=(0.05, 0.38, 0.16), layers=2,
    holes=[(-41, 21), (41, 21), (-41, -21), (41, -21)],
    slots=[],
    parts=[
        C("CN1", "connector", "From PSU, 6-pin 2.0 mm wafer", -41, 0, (6, 15, 8)),
        C("C1", "cap", "Electrolytic 220 uF 50 V (input)", -28, 14, (10, 16), "cyl"),
        C("L1", "magnetic", "Boost inductor 47 uH 2 A, shielded", -20, -5, (12, 12, 8)),
        C("Q1", "ic", "Boost MOSFET 150 V, DPAK", -2, -8, (6.5, 10, 2.3)),
        C("D1", "ic", "Schottky diode 3 A 150 V, SMC", 12, -8, (6, 8, 2.4)),
        C("U1", "ic", "LED boost controller with PWM dimming, SOIC-16", 5, 8, (10, 6, 1.7)),
        C("C2", "cap", "Electrolytic 47 uF 100 V (output)", 26, 8, (10, 20), "cyl"),
        C("R1", "passive", "Current-sense resistor 0.56 ohm 2512", 26, -12, (6.4, 3.2, 0.6)),
        C("R2", "passive", "Current-sense resistor 0.56 ohm 2512", 26, -18, (6.4, 3.2, 0.6)),
        C("CN2", "connector", "To LED strips, 4-pin 2.0 mm wafer", 0, 21, (12, 6, 8)),
    ],
)

# ---------------------------------------------------------------------------
# Wi-Fi / Bluetooth module board: 40 x 26 mm, connects by USB
# ---------------------------------------------------------------------------
WIFI = dict(
    name="wifi_board", title="Wi-Fi / Bluetooth module", centre=cfg.BOARD_WIFI[:2],
    size=cfg.BOARD_WIFI[2:], colour=(0.05, 0.20, 0.42), layers=2,
    holes=[(-17, 3), (17, 3)],
    slots=[],
    parts=[
        C("U1", "shield", "Wi-Fi 5 + Bluetooth 5 radio under shield can", 0, 3, (20, 14, 2.2)),
        C("CN1", "connector", "USB to main board, 4-pin 1.25 mm", 0, -10.5, (7, 4, 4.5)),
        C("Y1", "passive", "Crystal 40 MHz", -13.5, -8, (3.2, 2.5, 0.8)),
    ],
)

# ---------------------------------------------------------------------------
# IR receiver / standby LED / key board: 54 x 8.5 mm, components face the front
# ---------------------------------------------------------------------------
IR = dict(
    name="ir_board", title="IR / LED / key board", centre=cfg.BOARD_IR[:2], size=cfg.BOARD_IR[2:],
    colour=(0.05, 0.38, 0.16), layers=1, faces_front=True,
    holes=[], slots=[],
    parts=[
        C("U1", "ic", "Infrared receiver module 38 kHz", -4, 0, (5, 6, 5.6)),
        C("LED1", "passive", "Standby indicator LED, 3 mm, red", 6, 0, (3, 5), "cyl"),
        C("SW1", "passive", "Tactile switch, right-angle (power / menu)", -15, -2.25, (7, 4, 4)),
        C("SW1b", "passive", "Switch plunger", -15, -6.75, (3, 5), "cyl_v", lift=0.5),
        C("CN1", "connector", "To main board, 6-pin 1.25 mm", 16, 0, (10, 4, 4.5)),
    ],
)

BOARDS = [MAIN, PSU, TCON, LED_DRIVER, WIFI, IR]


def find(board: dict, ref: str) -> dict:
    """Look up one component on a board by its reference designator."""
    for part in board["parts"]:
        if part["ref"] == ref:
            return part
    raise KeyError(f"{ref} not on {board['name']}")


def footprint(part: dict) -> tuple[float, float, float, float]:
    """(u0, u1, v0, v1) of the board area a component covers."""
    shape, size = part["shape"], part["size"]
    if shape == "cyl":
        su = sv = size[0]
    elif shape == "cyl_u":
        su, sv = size[1], size[0]
    elif shape == "cyl_v":
        su, sv = size[0], size[1]
    else:
        su, sv = size[0], size[1]
    return part["u"] - su / 2, part["u"] + su / 2, part["v"] - sv / 2, part["v"] + sv / 2


def height(part: dict) -> float:
    """Top of a component above the board surface."""
    shape, size = part["shape"], part["size"]
    tall = size[0] if shape in ("cyl_u", "cyl_v") else size[-1]
    return part.get("lift", 0.0) + tall


def layout_problems(board: dict) -> list[str]:
    """Overlapping footprints, parts over mounting holes, parts too tall."""
    problems = []
    parts = [p for p in board["parts"] if not p.get("over")]
    for i, a in enumerate(parts):
        a0, a1, a2, a3 = footprint(a)
        for b in parts[i + 1:]:
            b0, b1, b2, b3 = footprint(b)
            if a0 < b1 - 1e-6 and b0 < a1 - 1e-6 and a2 < b3 - 1e-6 and b2 < a3 - 1e-6:
                problems.append(f"{a['ref']} overlaps {b['ref']}")
        for hu, hv in board["holes"]:
            keep = 3.5      # screw head radius plus clearance
            if a0 < hu + keep and hu - keep < a1 and a2 < hv + keep and hv - keep < a3:
                problems.append(f"{a['ref']} is over the mounting hole at ({hu}, {hv})")
    if not board.get("faces_front"):
        for p in board["parts"]:
            if height(p) > cfg.MAX_COMPONENT_HEIGHT + 1e-6:
                problems.append(f"{p['ref']} is {height(p):.1f} mm tall, "
                                f"limit {cfg.MAX_COMPONENT_HEIGHT:.1f} mm")
    return problems
