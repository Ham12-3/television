"""
electrical.py - the system-level electrical design of the television.

It holds the power rails, what draws from them, and every internal connector's
pinout. From that it:
    - prints the power budget and checks each rail has enough margin
    - writes ELECTRICAL.md (block diagram, power tree, pinouts, board notes)
    - writes output/bom.csv (bill of materials, from tv/board_data.py)

This is a reference design at block level. There are no circuit schematics
and no PCB layouts. See the limits section in ELECTRICAL.md.

Run:  python electrical.py
"""

import csv
from collections import Counter
from pathlib import Path

import config as cfg
from tv.board_data import BOARDS, MAIN
from tv.netlist import KIND_TITLE, NETS, net_members

ROOT = Path(__file__).parent

# ---------------------------------------------------------------------------
# Loads on the 12 V rail.
# (name, watts at the load, fed through an on-board converter?, note)
# ---------------------------------------------------------------------------
LOADS_12V = [
    ("SoC, DDR3 and eMMC", 5.0, True, "1.1 V core, 1.5 V memory, 3.3 V I/O"),
    ("Tuner, Wi-Fi/Bluetooth, Ethernet, logic", 2.5, True, "3.3 V and 5 V"),
    ("USB ports, 2 x 500 mA at 5 V", 5.0, True, "both ports fully loaded"),
    ("HDMI +5 V outputs, 2 x 55 mA", 0.55, True, ""),
    ("Audio amplifier", cfg.SPEAKER_POWER_W, False,
     "half of 2 x 8 W rated output, at 85 percent efficiency"),
    ("T-con and LCD panel logic", 5.0, False, "12 V direct to the T-con"),
    ("IR receiver, standby LED, standby logic", 0.2, False, ""),
]
AUDIO_EFFICIENCY = 0.85
POWER_FACTOR = 0.55          # typical for a small supply with no PFC stage
STANDBY_TARGET_W = 0.5


def budget() -> dict:
    """Work out the current on each rail and the mains input power."""
    r = {"rows": []}
    total = 0.0
    for name, watts, converted, note in LOADS_12V:
        if name == "Audio amplifier":
            at_rail = watts / AUDIO_EFFICIENCY        # 8 W out = half of 16 W rated
        elif converted:
            at_rail = watts / cfg.BUCK_EFFICIENCY
        else:
            at_rail = watts
        total += at_rail
        r["rows"].append((name, watts, at_rail, note))
    r["p12"] = total
    r["i12"] = total / 12.0
    r["margin12"] = 1 - r["i12"] / cfg.RAIL_12V_RATED_A

    r["led_power"] = cfg.LED_POWER_W
    r["p36"] = cfg.LED_POWER_W / cfg.LED_DRIVER_EFFICIENCY
    r["i36"] = r["p36"] / 36.0
    r["margin36"] = 1 - r["i36"] / cfg.RAIL_36V_RATED_A
    r["boost_duty"] = 1 - 36.0 / cfg.LED_STRING_VOLTAGE

    r["p_dc"] = r["p12"] + r["p36"]
    r["p_ac"] = r["p_dc"] / cfg.PSU_EFFICIENCY
    r["loss_psu"] = r["p_ac"] - r["p_dc"]
    r["i_ac_max"] = r["p_ac"] / (cfg.MAINS_VOLTAGE[0] * POWER_FACTOR)
    r["fuse_ratio"] = cfg.FUSE_RATING_A / r["i_ac_max"]
    return r


def checks(r: dict = None) -> list[tuple[str, bool, str]]:
    r = r or budget()
    need = cfg.MIN_RAIL_MARGIN
    return [
        (f"12 V rail has at least {need:.0%} spare",
         r["margin12"] >= need,
         f"{r['i12']:.2f} A of {cfg.RAIL_12V_RATED_A:.1f} A, {r['margin12']:.0%} spare"),
        (f"36 V rail has at least {need:.0%} spare",
         r["margin36"] >= need,
         f"{r['i36']:.2f} A of {cfg.RAIL_36V_RATED_A:.1f} A, {r['margin36']:.0%} spare"),
        (f"Mains input stays under {cfg.PFC_THRESHOLD_W:.0f} W (no PFC stage fitted)",
         r["p_ac"] < cfg.PFC_THRESHOLD_W, f"{r['p_ac']:.1f} W"),
        ("Fuse is rated 1.5 to 3 times the highest input current",
         1.5 <= r["fuse_ratio"] <= 3.0,
         f"{cfg.FUSE_RATING_A} A fuse, {r['i_ac_max']:.2f} A at {cfg.MAINS_VOLTAGE[0]:.0f} V"),
        ("LED string voltage is above the 36 V rail (a boost converter can drive it)",
         cfg.LED_STRING_VOLTAGE > 36.0 * 1.2,
         f"{cfg.LED_COUNT} LEDs x {cfg.LED_FORWARD_VOLTAGE} V = {cfg.LED_STRING_VOLTAGE:.1f} V"),
        ("LED string voltage is under the 100 V rating of the output capacitor",
         cfg.LED_STRING_VOLTAGE <= 0.8 * 100,
         f"{cfg.LED_STRING_VOLTAGE:.1f} V vs 80 V (80 percent of 100 V)"),
    ]


# ---------------------------------------------------------------------------
# Internal connectors: (from board, ref) -> (to board, ref), cable, pins
# ---------------------------------------------------------------------------
HARNESS = [
    ("Mains inlet", "-", "PSU", "CN1", "2-core mains lead", "Live, neutral (class II: no earth)"),
    ("PSU", "CN2", "Main board", "CN1", "12-way wire harness", "12 V, ground, standby and backlight control"),
    ("PSU", "CN3", "LED driver", "CN1", "6-way wire harness", "36 V, ground, enable, dimming"),
    ("LED driver", "CN2", "LED strips", "-", "4-way wire harness", "LED string + and -, through the chassis"),
    ("Main board", "CN2", "T-con", "CN1", "51-way 0.5 mm FFC", "Dual-link LVDS video and panel power"),
    ("T-con", "CN2", "Source board A", "-", "60-way 0.5 mm FFC", "mini-LVDS column data, gamma, power"),
    ("T-con", "CN3", "Source board B", "-", "60-way 0.5 mm FFC", "mini-LVDS column data, gamma, power"),
    ("Main board", "CN3", "Speakers", "-", "2 x twin lead", "Left and right speaker outputs"),
    ("Main board", "CN4", "IR / LED / key board", "CN1", "6-way wire harness", "IR data, LED, key, 3.3 V standby"),
    ("Main board", "CN5", "Wi-Fi / Bluetooth module", "CN1", "4-way wire harness", "USB 2.0"),
]

PINOUTS = {
    "PSU CN2 to main board CN1 (12-pin)": [
        ("1-3", "+12V", "Main supply, 3.5 A total"),
        ("4-7", "GND", "Return"),
        ("8", "PS_ON", "From main board: high = leave standby"),
        ("9", "BL_ON", "From main board: high = backlight on (passed to the LED driver)"),
        ("10", "DIM", "From main board: PWM 100 Hz to 20 kHz, backlight brightness"),
        ("11", "+12V_STBY", "Always on, 100 mA, feeds the standby regulator"),
        ("12", "GND", "Return"),
    ],
    "PSU CN3 to LED driver CN1 (6-pin)": [
        ("1-2", "+36V", "Backlight supply, 1 A"),
        ("3-4", "GND", "Return"),
        ("5", "BL_ON", "High = driver enabled"),
        ("6", "DIM", "PWM brightness"),
    ],
    "LED driver CN2 to LED strips (4-pin)": [
        ("1-2", "LED+", f"Up to {cfg.LED_STRING_VOLTAGE:.0f} V at {cfg.LED_CURRENT * 1000:.0f} mA, constant current"),
        ("3-4", "LED-", "Return through the current-sense resistors"),
    ],
    "Main board CN2 to T-con CN1 (51-pin FFC)": [
        ("1-4", "VDD_PANEL", "+12 V panel supply, switched by the main board"),
        ("5-8", "GND", "Return"),
        ("9-18", "LVDS A0+/- to A3+/-, ACLK+/-", "Odd-pixel link: 4 data pairs and clock"),
        ("19-28", "LVDS B0+/- to B3+/-, BCLK+/-", "Even-pixel link: 4 data pairs and clock"),
        ("29-40", "GND", "Shield grounds between pairs"),
        ("41", "SDA", "I2C data (panel EEPROM, PMIC)"),
        ("42", "SCL", "I2C clock"),
        ("43", "WP", "EEPROM write protect"),
        ("44", "LVDS_SEL", "Colour mapping select (VESA / JEIDA)"),
        ("45", "BIT_SEL", "8-bit / 10-bit select"),
        ("46-51", "NC / GND", "Not used"),
    ],
    "Main board CN3 to speakers (4-pin)": [
        ("1", "SPK_L+", "Left speaker, 8 ohm"),
        ("2", "SPK_L-", ""),
        ("3", "SPK_R-", "Right speaker, 8 ohm"),
        ("4", "SPK_R+", ""),
    ],
    "Main board CN4 to IR / LED / key board CN1 (6-pin)": [
        ("1", "+3V3_STBY", "Always on"),
        ("2", "IR_RX", "Demodulated infrared data, active low"),
        ("3", "LED_STBY", "Standby indicator drive"),
        ("4", "KEY_ADC", "Key input (resistor ladder to one ADC pin)"),
        ("5", "GND", ""),
        ("6", "NC", ""),
    ],
    "Main board CN5 to Wi-Fi / Bluetooth module CN1 (4-pin)": [
        ("1", "+5V", "Module supply, 500 mA"),
        ("2", "USB_D-", ""),
        ("3", "USB_D+", ""),
        ("4", "GND", ""),
    ],
    "Main board CN6 service header (4-pin)": [
        ("1", "+3V3", "Reference only"),
        ("2", "UART_TX", "115200 baud console"),
        ("3", "UART_RX", ""),
        ("4", "GND", ""),
    ],
}

MAIN_RAILS = [
    ("+12V", "PSU", "Audio amplifier, T-con / panel, inputs of all converters"),
    ("+5V", "U8 buck, 3 A", "USB ports, HDMI +5 V, Wi-Fi module, tuner"),
    ("+3V3", "U9 buck, 2 A", "SoC I/O, flash, Ethernet, logic"),
    ("+1V1", "U10 buck, 3 A", "SoC core"),
    ("+1V5", "U14 linear regulator from 3.3 V", "DDR3 memory"),
    ("+3V3_STBY", "Standby regulator from +12V_STBY", "IR receiver, standby logic, key input"),
]


# ---------------------------------------------------------------------------
# Bill of materials
# ---------------------------------------------------------------------------
def bom_rows() -> list[dict]:
    """One row per distinct part on each board, with quantity and references."""
    rows = []
    for board in BOARDS:
        counts, refs = Counter(), {}
        for part in board["parts"]:
            if part["ref"].endswith("b"):          # second body of one part (switch plunger)
                continue
            key = (part["desc"], part["kind"])
            counts[key] += 1
            refs.setdefault(key, []).append(part["ref"])
        rows.append({"board": board["title"], "refs": "PCB", "qty": 1, "kind": "pcb",
                     "description": f"{board['size'][0]:.0f} x {board['size'][1]:.0f} mm, "
                                    f"{board['layers']}-layer, 1.6 mm"})
        for (desc, kind), qty in counts.items():
            rows.append({"board": board["title"], "refs": " ".join(refs[(desc, kind)]),
                         "qty": qty, "kind": kind, "description": desc})
    mech = [
        ("Enclosure", "Front bezel, ABS, injection moulded", 1),
        ("Enclosure", "Rear cover, ABS, injection moulded", 1),
        ("Enclosure", "IR window, smoked polycarbonate", 1),
        ("Enclosure", "Rear cover screw M3 x 8 pan head", len(cfg.COVER_BOSSES)),
        ("Panel", f"LCD cell {cfg.TV_DIAGONAL_INCH} inch class, {cfg.RESOLUTION[0]} x {cfg.RESOLUTION[1]}", 1),
        ("Panel", "Source driver board with chip-on-film drivers", 2),
        ("Panel", "Mould frame, plastic", 1),
        ("Backlight", "Prism sheet", 2),
        ("Backlight", "Diffuser sheet", 1),
        ("Backlight", f"Diffuser plate {cfg.DIFFUSER_THICKNESS} mm", 1),
        ("Backlight", "Reflector sheet", 1),
        ("Backlight", "Diffuser support pin", len(cfg.support_pin_centres())),
        ("Backlight", f"LED strip, {cfg.LEDS_PER_STRIP} LEDs with lenses, aluminium PCB", cfg.LED_STRIPS),
        ("Chassis", f"Back chassis, steel {cfg.TRAY_THICKNESS} mm, with pillars", 1),
        ("Audio", f"Speaker {cfg.SPEAKER_POWER_W:.0f} W 8 ohm, enclosed", 2),
        ("Power", "Mains inlet, 2-pin (IEC C8 style)", 1),
        ("Fixings", "Board screw M3 x 6 pan head", sum(len(b["holes"]) for b in BOARDS)),
        ("Accessories", "Stand foot", 2),
        ("Accessories", "Infrared remote control with 2 x AAA cells", 1),
        ("Accessories", "Wall mount, 3D printed PETG (4 parts, 5 pieces)", 1),
    ]
    for area, desc, qty in mech:
        rows.append({"board": area, "refs": "-", "qty": qty, "kind": "mechanical", "description": desc})
    for a, ar, b, br, cable, _ in HARNESS:
        rows.append({"board": "Cables", "refs": "-", "qty": 1, "kind": "cable",
                     "description": f"{cable}: {a} to {b}"})
    return rows


def write_bom(path: Path) -> int:
    rows = bom_rows()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["board", "refs", "qty", "kind", "description"])
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


# ---------------------------------------------------------------------------
# ELECTRICAL.md
# ---------------------------------------------------------------------------
def table(headers, rows) -> str:
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    lines += ["| " + " | ".join(str(c) for c in row) + " |" for row in rows]
    return "\n".join(lines)


def write_doc(path: Path) -> None:
    r = budget()
    members = net_members()
    ports = [(p["ref"], p["desc"]) for p in MAIN["parts"] if p["kind"] == "port"]
    counts = {b["title"]: len(b["parts"]) for b in BOARDS}
    doc = f"""# Electrical design: 32 inch LED television

Generated by `python electrical.py` from `config.py` and `tv/board_data.py`.
Do not edit by hand; change the source and regenerate.

**Level of detail.** This is a system-level reference design: what the blocks
are, how they connect, what power they need and where the parts sit on each
board. It contains no circuit schematics and no PCB layouts. Read section 10
before using any of it.

## 1. Block diagram

```mermaid
flowchart LR
    AC[Mains inlet<br>100-240 V] --> PSU[Power supply board<br>flyback, isolated]
    PSU -- 12 V --> MB[Main board<br>SoC, memory, tuner, audio]
    PSU -- 36 V --> LD[LED driver board<br>boost, constant current]
    MB -- PS_ON, BL_ON, DIM --> PSU
    PSU -- BL_ON, DIM --> LD
    LD -- {cfg.LED_STRING_VOLTAGE:.0f} V / {cfg.LED_CURRENT * 1000:.0f} mA --> LED[LED strips<br>{cfg.LED_COUNT} LEDs in series]
    MB -- LVDS + 12 V --> TC[T-con board]
    TC -- mini-LVDS --> SRC[Source boards A and B<br>column drivers on film]
    SRC --> LCD[LCD cell<br>{cfg.RESOLUTION[0]} x {cfg.RESOLUTION[1]}]
    LED -. light .-> LCD
    MB -- audio --> SPK[Speakers 2 x {cfg.SPEAKER_POWER_W:.0f} W]
    MB -- USB --> WIFI[Wi-Fi / Bluetooth module]
    IR[IR / LED / key board] -- IR data, key --> MB
    REM[Remote control] -. infrared .-> IR
    EXT[HDMI, USB, antenna, AV,<br>Ethernet, optical, headphone] <--> MB
```

## 2. Power tree

```mermaid
flowchart TD
    AC[Mains 100-240 V AC] --> F[Fuse {cfg.FUSE_RATING_A} A, varistor, inrush limiter]
    F --> EMI[EMI filter: 2 chokes, 2 X capacitors]
    EMI --> BR[Bridge rectifier + 100 uF 400 V]
    BR --> FLY[Flyback converter<br>reinforced isolation]
    FLY --> R12[+12 V, {cfg.RAIL_12V_RATED_A} A]
    FLY --> R36[+36 V, {cfg.RAIL_36V_RATED_A} A]
    R36 --> BOOST[LED boost driver] --> LEDS[LED string {cfg.LED_STRING_VOLTAGE:.0f} V]
    R12 --> B5[Buck 5 V] --> USB[USB, HDMI 5 V, Wi-Fi, tuner]
    R12 --> B33[Buck 3.3 V] --> IO[SoC I/O, flash, logic]
    B33 --> LDO[LDO 1.5 V] --> DDR[DDR3]
    R12 --> B11[Buck 1.1 V] --> CORE[SoC core]
    R12 --> AMP[Audio amplifier]
    R12 --> TCON[T-con: AVDD, VGH, VGL, VCOM]
```

## 3. Power budget

### 12 V rail

{table(["Load", "Power at the load", "Power from the 12 V rail", "Note"],
       [(n, f"{w:.2f} W", f"{a:.2f} W", note) for n, w, a, note in r["rows"]]
       + [("**Total**", "", f"**{r['p12']:.1f} W = {r['i12']:.2f} A**",
           f"rated {cfg.RAIL_12V_RATED_A} A, {r['margin12']:.0%} spare")])}

Loads fed through an on-board buck converter are divided by
{cfg.BUCK_EFFICIENCY:.0%} converter efficiency. The audio line is 8 W of
output, which is half the amplifier's 2 x 8 W rating: music and speech average
well under full power. At full sine-wave output on both channels the 12 V rail
would be overloaded, so the amplifier's power limit must be set accordingly.

### 36 V rail (backlight)

{table(["Item", "Value"], [
    ("LEDs", f"{cfg.LED_COUNT} ({cfg.LED_STRIPS} strips of {cfg.LEDS_PER_STRIP}), all in series"),
    ("String voltage", f"{cfg.LED_COUNT} x {cfg.LED_FORWARD_VOLTAGE} V = {cfg.LED_STRING_VOLTAGE:.1f} V"),
    ("String current", f"{cfg.LED_CURRENT * 1000:.0f} mA, constant"),
    ("LED power", f"{r['led_power']:.1f} W"),
    ("Driver input", f"{r['p36']:.1f} W at {cfg.LED_DRIVER_EFFICIENCY:.0%} = {r['i36']:.2f} A at 36 V"),
    ("Rail rating", f"{cfg.RAIL_36V_RATED_A} A, {r['margin36']:.0%} spare"),
    ("Boost duty cycle", f"{r['boost_duty']:.0%} at full brightness"),
])}

### Mains input

{table(["Item", "Value"], [
    ("Total DC output", f"{r['p_dc']:.1f} W"),
    ("Supply efficiency assumed", f"{cfg.PSU_EFFICIENCY:.0%}"),
    ("Mains input power", f"{r['p_ac']:.1f} W"),
    ("Heat in the power supply", f"{r['loss_psu']:.1f} W"),
    ("Highest input current", f"{r['i_ac_max']:.2f} A at {cfg.MAINS_VOLTAGE[0]:.0f} V, power factor {POWER_FACTOR}"),
    ("Fuse", f"T{cfg.FUSE_RATING_A} A, {cfg.FUSE_RATING_A / r['i_ac_max']:.1f} times the highest input current"),
    ("Standby target", f"under {STANDBY_TARGET_W} W"),
])}

Input power is under {cfg.PFC_THRESHOLD_W:.0f} W, so no power-factor-correction
stage is fitted. That threshold comes from the harmonic-current limits for this
class of equipment (EN 61000-3-2 class D).

## 4. The boards

{table(["Board", "Size", "Layers", "Parts placed", "Job"], [
    (b["title"], f"{b['size'][0]:.0f} x {b['size'][1]:.0f} mm", b["layers"], counts[b["title"]], job)
    for b, job in zip(BOARDS, [
        "Runs the TV: decodes video, drives the panel link, audio, tuner, all ports",
        "Turns mains into isolated 12 V and 36 V",
        "Converts LVDS video into the timing and column data the LCD needs; makes the panel's bias voltages",
        "Boosts 36 V to the LED string voltage and holds the current constant",
        "2.4 / 5 GHz Wi-Fi and Bluetooth radio, on USB",
        "Infrared receiver, standby LED and the one control button",
    ])])}

Two more boards belong to the panel: source boards A and B, each
{cfg.SOURCE_PCB[1]:.0f} x {cfg.SOURCE_PCB[2]:.0f} mm, bonded to the bottom edge
of the glass through {len(cfg.COF_X)} chip-on-film column drivers each. Row
drivers are built into the glass (gate-on-array), so there are no gate boards.

## 5. Main board in detail

{cfg.BOARD_MAIN[2]:.0f} x {cfg.BOARD_MAIN[3]:.0f} mm, 4 layers
(signal, ground, power, signal), {counts["Main board"]} parts placed.

### Functional blocks

{table(["Block", "Parts", "What it does"], [
    ("Processor", "U1 under heatsink HS1", "Quad-core ARM SoC with video decoder, HDMI receivers, LVDS transmitter, USB and Ethernet controllers"),
    ("Memory", "U2, U3", "2 x 512 MB DDR3, routed as a matched-length point-to-point bus"),
    ("Storage", "U4, U5", "8 GB eMMC for the operating system; SPI flash for the boot loader"),
    ("Clock", "Y1", "24 MHz crystal"),
    ("Tuner", "TU1, J10", "Silicon tuner and demodulator under a shield can, next to the RF input"),
    ("Audio", "U7, L1-L4, C1, C2", "Class-D amplifier, 2 x 8 W, with an LC output filter per speaker wire"),
    ("Power", "U8-U10, L5-L7, U14", "Three buck converters and one linear regulator (table below)"),
    ("Port protection", "U11, U12, U13", "USB current-limit switch; ESD arrays on both HDMI inputs"),
])}

### On-board supply rails

{table(["Rail", "Made by", "Feeds"], MAIN_RAILS)}

Power-up order: +3V3_STBY is always present. When the standby logic raises
PS_ON, +12V comes up, then 3.3 V, 1.5 V, 1.1 V, then reset is released. The
panel supply (VDD_PANEL) is switched on before LVDS starts, and the backlight
(BL_ON) last, so the screen never shows an unpowered or unsynchronised panel.

### External ports (top to bottom on the side connector panel)

{table(["Ref", "Port"], ports)}

### Layout notes

- Ports sit on one edge so they line up with the recess in the rear cover.
- The RF input and tuner are at the opposite end of that edge from HDMI and
  USB, to keep the tuner away from fast digital signals.
- The buck converters and the audio amplifier are on the edge nearest the
  power connector, so high currents do not cross the processor area.
- Decoupling capacitors ring the SoC and the memory.

## 6. Internal connections

{table(["From", "Ref", "To", "Ref", "Cable", "Carries"], HARNESS)}

## 7. Connector pinouts

Representative pin assignments. A real design would follow the chosen panel's
and modules' datasheets.

""" + "\n\n".join(f"### {name}\n\n" + table(["Pin", "Signal", "Notes"], pins)
                  for name, pins in PINOUTS.items()) + f"""

## 8. Protection and safety features in the design

{table(["Feature", "Where", "Purpose"], [
    ("Fuse", "PSU F1", "Clears a fault on the mains side"),
    ("Varistor", "PSU RV1", "Absorbs mains surges"),
    ("Inrush limiter", "PSU NTC1", "Limits the charging current of the bulk capacitor"),
    ("EMI filter", "PSU LF1, LF2, CX1, CX2, CY1", "Keeps switching noise off the mains"),
    ("Isolation barrier", "PSU T1, U2, CY1 and a routed slot", "Separates mains from everything a user can touch; 8 mm kept clear across it"),
    ("Double insulation", "Whole set", "Class II: plastic enclosure, 2-pin inlet, no earth"),
    ("Constant-current LED drive", "LED driver U1, R1, R2", "Open-string and short-string protection; current cannot run away"),
    ("USB current limit", "Main board U11", "A shorted USB device cannot pull down the 5 V rail"),
    ("ESD protection", "Main board U12, U13", "Protects the HDMI inputs"),
    ("Heatsinks", "Main board HS1; PSU HS1, HS2", "SoC, switching transistor, output rectifiers"),
    ("Venting", "Rear cover", "Intake slots low, exhaust slots along the top"),
])}

## 9. Net list

`tv/netlist.py` records which nets every component touches and what the
component is for. The viewer uses it: click a part to see its connections, or
pick a net to light up everything on it. It is connectivity at block level
(which parts share a rail or a signal bundle), not a pin-by-pin schematic.

{table(["Net", "Type", "Level", "What it is", "Parts on it"],
       [(f"`{name}`", KIND_TITLE[kind], level, about, len(members[name]))
        for name, (kind, level, _, about) in NETS.items()])}

## 10. Limits: what this is not

1. **Not a buildable design.** There are no schematics, netlists, PCB layouts
   or firmware. Component positions are a plausible arrangement, not a routed
   board.
2. **Mains power is dangerous.** The power supply board is described at block
   level only. Do not build a mains supply from this. A real one needs proper
   transformer design, creepage and clearance checks, and safety testing.
3. **No compliance work.** Nothing here has been checked against product-safety
   (IEC 62368-1), EMC or radio rules. A real TV needs certification before sale.
4. **Typical values, not datasheet values.** Efficiencies, LED voltage and load
   powers are representative figures for this class of set.
5. **No thermal analysis.** Heatsinks and vents are sized by eye. About
   {r['loss_psu']:.0f} W of heat in the supply and {r['led_power']:.0f} W in the
   backlight would need a thermal simulation or measurement.
6. **No signal-integrity work.** HDMI, DDR3 and LVDS all need controlled
   impedance and length matching, which only a real layout can provide.
7. **Parts are generic.** The bill of materials describes kinds of part, not
   orderable part numbers.

## 11. Bill of materials

`output/bom.csv`, written by this script: {len(bom_rows())} lines covering every
board, the mechanical parts, the cables and the accessories.
"""
    path.write_text(doc, encoding="utf-8")


def main() -> int:
    r = budget()
    print("Television power budget")
    print("-" * 70)
    for name, watts, at_rail, _ in r["rows"]:
        print(f"  {name:44s} {watts:6.2f} W -> {at_rail:6.2f} W at 12 V")
    print(f"  12 V rail: {r['p12']:.1f} W, {r['i12']:.2f} A")
    print(f"  36 V rail: {r['p36']:.1f} W, {r['i36']:.2f} A  (LEDs {r['led_power']:.1f} W)")
    print(f"  Mains input: {r['p_ac']:.1f} W")
    print()
    failed = 0
    for text, ok, detail in checks(r):
        failed += not ok
        print(f"[{'PASS' if ok else 'FAIL'}] {text}  ({detail})")
    write_doc(ROOT / "ELECTRICAL.md")
    lines = write_bom(ROOT / "output" / "bom.csv")
    print("-" * 70)
    print(f"wrote ELECTRICAL.md and output/bom.csv ({lines} lines)")
    print("ALL PASS" if failed == 0 else f"{failed} FAILED")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
