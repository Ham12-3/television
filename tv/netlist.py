"""
tv/netlist.py - how the components are connected electrically.

A "net" is one electrical connection: a power rail, a ground, or a signal (or
a bundle of related signals such as an HDMI link). This file lists every net
and says which nets each component touches and what the component is for.

The viewer uses it to label parts, to show what a clicked part connects to,
to draw copper traces on the boards and to highlight a whole net.

It is connectivity at block level: which parts share a rail or a signal
bundle. It is not a pin-by-pin schematic.
"""

from tv.board_data import BOARDS, footprint, height
from tv.boards import CATEGORY

# name: (kind, voltage or signal type, display colour, what it is)
NETS = {
    # --- mains side (dangerous) ---------------------------------------------
    "AC_L": ("mains", "100-240 V AC", "#e5484d", "Mains live, from the inlet through the fuse and filter"),
    "AC_N": ("mains", "100-240 V AC", "#f2994a", "Mains neutral"),
    "HV_DC": ("mains", "140-340 V DC", "#d6336c", "Rectified mains on the bulk capacitor"),
    "PRI_SW": ("mains", "switching, up to 600 V", "#c2255c", "Flyback switch node: transformer primary to the MOSFET"),
    "PGND": ("mains", "primary ground (live)", "#a61e4d", "Return on the mains side. Not safe to touch"),
    # --- isolated power rails -------------------------------------------------
    "+36V": ("power", "36 V", "#f59f00", "Backlight supply from the PSU to the LED driver"),
    "+12V": ("power", "12 V", "#fab005", "Main supply: audio, panel and all on-board converters"),
    "+5V": ("power", "5 V", "#ff922b", "USB ports, HDMI +5 V, Wi-Fi module, tuner"),
    "+3V3": ("power", "3.3 V", "#fcc419", "Logic and input/output supply"),
    "+1V5": ("power", "1.5 V", "#ffd43b", "DDR3 memory supply"),
    "+1V1": ("power", "1.1 V", "#ffe066", "Processor core supply"),
    "+3V3_STBY": ("power", "3.3 V always on", "#e8590c", "Standby supply: keeps the IR receiver alive when the TV is off"),
    "PANEL_BIAS": ("power", "AVDD 16 V, VGH 28 V, VGL -6 V", "#e67700", "Bias voltages the LCD needs, made on the T-con"),
    "LED+": ("power", "up to 74 V", "#ff6b6b", "Top of the LED string"),
    "LED-": ("power", "current sense", "#fa5252", "Bottom of the LED string, back through the sense resistors"),
    "LED_SW": ("power", "switching, up to 80 V", "#f03e3e", "Boost converter switch node"),
    "GND": ("ground", "0 V", "#868e96", "Isolated ground: the reference for everything a user can touch"),
    # --- control ------------------------------------------------------------
    "PS_ON": ("control", "logic", "#12b886", "Main board tells the PSU to leave standby"),
    "BL_ON": ("control", "logic", "#20c997", "Backlight enable"),
    "DIM": ("control", "PWM", "#38d9a9", "Backlight brightness"),
    "FB": ("control", "analogue", "#0ca678", "Output-voltage feedback across the isolation barrier"),
    "I2C": ("control", "I2C bus", "#099268", "Configuration bus: tuner, panel EEPROM, power-management IC"),
    "IR_RX": ("control", "logic", "#63e6be", "Decoded infrared from the remote"),
    "KEY": ("control", "analogue", "#96f2d7", "The button on the set"),
    "LED_STBY": ("control", "logic", "#087f5b", "Standby indicator drive"),
    "UART": ("control", "serial", "#2b8a3e", "Service console"),
    "XTAL": ("control", "24 MHz", "#51cf66", "Processor clock"),
    # --- video --------------------------------------------------------------
    "HDMI1": ("video", "TMDS, 4 pairs + DDC", "#339af0", "HDMI input 1"),
    "HDMI2": ("video", "TMDS, 4 pairs + DDC", "#4dabf7", "HDMI input 2"),
    "CVBS": ("video", "analogue video", "#74c0fc", "Composite video input"),
    "RF": ("video", "RF 45-860 MHz", "#1c7ed6", "Antenna signal into the tuner"),
    "TS": ("video", "transport stream", "#1971c2", "Demodulated broadcast data, tuner to processor"),
    "LVDS": ("video", "LVDS, 10 pairs", "#5c7cfa", "Picture data, main board to T-con"),
    "MINI_LVDS": ("video", "mini-LVDS", "#748ffc", "Column data, T-con to the source drivers"),
    "GAMMA": ("video", "analogue references", "#91a7ff", "Gamma reference voltages for the column drivers"),
    "GATE_CLK": ("video", "level-shifted clocks", "#bac8ff", "Row-scan clocks for the gate drivers in the glass"),
    # --- audio --------------------------------------------------------------
    "I2S": ("audio", "digital audio", "#cc5de8", "Processor to the audio amplifier"),
    "SPK_L": ("audio", "8 ohm speaker drive", "#da77f2", "Left speaker"),
    "SPK_R": ("audio", "8 ohm speaker drive", "#e599f7", "Right speaker"),
    "SPDIF": ("audio", "digital audio", "#be4bdb", "Optical audio output"),
    "HP_AUDIO": ("audio", "analogue audio", "#ae3ec9", "Headphone output"),
    "AUDIO_IN": ("audio", "analogue audio", "#9c36b5", "Stereo audio input"),
    # --- data ---------------------------------------------------------------
    "DDR": ("data", "DDR3 bus", "#22b8cf", "Memory bus, processor to RAM"),
    "EMMC": ("data", "eMMC bus", "#3bc9db", "Storage bus"),
    "SPI": ("data", "SPI bus", "#66d9e8", "Boot flash"),
    "USB1": ("data", "USB 2.0", "#15aabf", "USB port 1"),
    "USB2": ("data", "USB 2.0", "#1098ad", "USB port 2"),
    "USB_WIFI": ("data", "USB 2.0", "#0c8599", "Wi-Fi / Bluetooth module link"),
    "ETH": ("data", "100BASE-TX", "#0b7285", "Ethernet"),
}

KIND_ORDER = ["mains", "power", "ground", "control", "video", "audio", "data"]
KIND_TITLE = {"mains": "Mains (dangerous)", "power": "Power rails", "ground": "Ground",
              "control": "Control", "video": "Video", "audio": "Audio", "data": "Data"}

_PWR = ["+12V", "GND", "PS_ON", "BL_ON", "DIM", "+3V3_STBY"]
_LVDS = ["LVDS", "+12V", "GND", "I2C"]
_SRC = ["MINI_LVDS", "GAMMA", "PANEL_BIAS", "GATE_CLK", "GND"]
_IRB = ["IR_RX", "LED_STBY", "KEY", "+3V3_STBY", "GND"]

# board name -> {ref: (what it does, [nets])}
CONNECTIONS = {
    "mainboard": {
        "J1": ("Takes video and sound from a set-top box, console or player", ["HDMI1", "+5V", "GND"]),
        "J2": ("Second HDMI input; also sends TV sound back to a soundbar (ARC)", ["HDMI2", "+5V", "GND"]),
        "J3": ("USB socket for memory sticks and accessories", ["USB1", "+5V", "GND"]),
        "J4": ("Second USB socket", ["USB2", "+5V", "GND"]),
        "J5": ("Sends digital sound to an amplifier over an optical fibre", ["SPDIF", "+3V3", "GND"]),
        "J6": ("Headphone socket", ["HP_AUDIO", "GND"]),
        "J7": ("Analogue video in from older equipment", ["CVBS", "GND"]),
        "J8": ("Analogue sound in, left channel", ["AUDIO_IN", "GND"]),
        "J9": ("Analogue sound in, right channel", ["AUDIO_IN", "GND"]),
        "J10": ("Aerial or cable socket", ["RF", "GND"]),
        "J11": ("Wired network socket", ["ETH", "+3V3", "GND"]),
        "U1": ("The processor. Decodes video, runs the smart-TV software and controls every other board",
               ["+1V1", "+3V3", "+1V5", "GND", "DDR", "EMMC", "SPI", "XTAL", "HDMI1", "HDMI2", "CVBS", "TS",
                "LVDS", "I2S", "SPDIF", "HP_AUDIO", "AUDIO_IN", "USB1", "USB2", "USB_WIFI", "ETH", "I2C",
                "IR_RX", "KEY", "LED_STBY", "PS_ON", "BL_ON", "DIM", "UART"]),
        "HS1": ("Carries heat away from the processor", []),
        "U2": ("Working memory (RAM)", ["DDR", "+1V5", "GND"]),
        "U3": ("Working memory (RAM)", ["DDR", "+1V5", "GND"]),
        "U4": ("Storage for the operating system and apps", ["EMMC", "+3V3", "GND"]),
        "U5": ("Holds the boot loader that starts the processor", ["SPI", "+3V3", "GND"]),
        "Y1": ("Sets the processor's clock frequency", ["XTAL"]),
        "TU1": ("Picks one broadcast channel out of the aerial signal and turns it into data",
                ["RF", "TS", "I2C", "+3V3", "+5V", "GND"]),
        "U7": ("Audio power amplifier: drives both speakers", ["I2S", "+12V", "GND", "SPK_L", "SPK_R"]),
        "L1": ("Smooths the amplifier's switching output", ["SPK_L"]),
        "L2": ("Smooths the amplifier's switching output", ["SPK_L"]),
        "L3": ("Smooths the amplifier's switching output", ["SPK_R"]),
        "L4": ("Smooths the amplifier's switching output", ["SPK_R"]),
        "C1": ("Energy reserve for loud bass", ["+12V", "GND"]),
        "C2": ("Energy reserve for loud bass", ["+12V", "GND"]),
        "U8": ("Steps 12 V down to 5 V", ["+12V", "+5V", "GND"]),
        "L5": ("Energy-storage coil of the 5 V converter", ["+5V"]),
        "U9": ("Steps 12 V down to 3.3 V", ["+12V", "+3V3", "GND"]),
        "L6": ("Energy-storage coil of the 3.3 V converter", ["+3V3"]),
        "U10": ("Steps 12 V down to 1.1 V for the processor core", ["+12V", "+1V1", "GND"]),
        "L7": ("Energy-storage coil of the 1.1 V converter", ["+1V1"]),
        "U14": ("Makes a quiet 1.5 V for the memory", ["+3V3", "+1V5", "GND"]),
        "C3": ("Smooths the 5 V rail", ["+5V", "GND"]),
        "C4": ("Smooths the 5 V rail", ["+5V", "GND"]),
        "U11": ("Cuts USB power if a device draws too much", ["+5V", "USB1", "USB2", "GND"]),
        "U12": ("Protects the HDMI input from static discharge", ["HDMI1", "GND"]),
        "U13": ("Protects the HDMI input from static discharge", ["HDMI2", "GND"]),
        "CN1": ("Power and control link to the power supply", _PWR),
        "CN2": ("Picture data out to the T-con board", _LVDS),
        "CN3": ("Speaker outputs", ["SPK_L", "SPK_R"]),
        "CN4": ("Link to the IR receiver, standby light and button", _IRB),
        "CN5": ("USB link to the Wi-Fi / Bluetooth module", ["USB_WIFI", "+5V", "GND"]),
        "CN6": ("Service console for factory test and repair", ["UART", "+3V3", "GND"]),
    },
    "psu_board": {
        "CN1": ("Mains comes in here", ["AC_L", "AC_N"]),
        "F1": ("Blows to disconnect the mains if something fails", ["AC_L"]),
        "RV1": ("Absorbs voltage spikes from the mains", ["AC_L", "AC_N"]),
        "NTC1": ("Limits the surge when the set is plugged in", ["AC_L"]),
        "CX1": ("Filters interference so it does not get back onto the mains", ["AC_L", "AC_N"]),
        "CX2": ("Filters interference so it does not get back onto the mains", ["AC_L", "AC_N"]),
        "LF1": ("Blocks interference on both mains wires at once", ["AC_L", "AC_N"]),
        "LF2": ("Blocks interference on both mains wires at once", ["AC_L", "AC_N"]),
        "BD1": ("Turns AC mains into DC", ["AC_L", "AC_N", "HV_DC", "PGND"]),
        "C1": ("Stores the rectified mains between cycles", ["HV_DC", "PGND"]),
        "U1": ("Controls the switching transistor to hold the outputs steady", ["PRI_SW", "FB", "HV_DC", "PGND"]),
        "R1": ("Starts the controller from the high-voltage rail", ["HV_DC"]),
        "R2": ("Starts the controller from the high-voltage rail", ["HV_DC"]),
        "HS1": ("Cools the switching transistor", []),
        "Q1": ("Switches the transformer about 65,000 times a second", ["PRI_SW", "PGND"]),
        "T1": ("Passes energy across the safety barrier and sets the output voltages",
               ["HV_DC", "PRI_SW", "+12V", "+36V", "GND"]),
        "U2": ("Sends the feedback signal across the safety barrier using light", ["FB", "+12V", "GND"]),
        "CY1": ("Returns interference currents across the barrier safely", ["PGND", "GND"]),
        "HS2": ("Cools the output rectifiers", []),
        "D1": ("Rectifies the 12 V output", ["+12V"]),
        "D2": ("Rectifies the 36 V output", ["+36V"]),
        "C2": ("Smooths the 12 V output", ["+12V", "GND"]),
        "C3": ("Smooths the 12 V output", ["+12V", "GND"]),
        "L1": ("Removes switching ripple from the 12 V output", ["+12V"]),
        "C4": ("Final smoothing of the 12 V output", ["+12V", "GND"]),
        "C5": ("Smooths the 36 V output", ["+36V", "GND"]),
        "C6": ("Smooths the 36 V output", ["+36V", "GND"]),
        "L2": ("Removes switching ripple from the 36 V output", ["+36V"]),
        "U3": ("Precise voltage reference that the 12 V output is compared with", ["FB", "+12V", "GND"]),
        "CN2": ("Power and control link to the main board", _PWR),
        "CN3": ("Backlight power to the LED driver", ["+36V", "GND", "BL_ON", "DIM"]),
    },
    "tcon_board": {
        "U1": ("Timing controller: turns the picture data into exactly timed column and row signals",
               ["LVDS", "MINI_LVDS", "GATE_CLK", "+3V3", "GND", "I2C"]),
        "U2": ("Makes the special voltages the LCD glass needs", ["+12V", "PANEL_BIAS", "GND", "I2C"]),
        "U3": ("Supplies the reference voltages that set the picture's tone curve", ["GAMMA", "PANEL_BIAS", "GND"]),
        "U4": ("Stores this panel's timing settings", ["I2C", "+3V3", "GND"]),
        "U5": ("Raises the row-scan clocks to the high voltage the glass needs", ["GATE_CLK", "PANEL_BIAS", "GND"]),
        "L1": ("Coil of the boost converter that makes AVDD", ["+12V", "PANEL_BIAS"]),
        "L2": ("Coil of the 3.3 V logic converter", ["+12V", "+3V3"]),
        "C1": ("Smooths the panel bias supply", ["PANEL_BIAS", "GND"]),
        "C2": ("Smooths the 12 V input", ["+12V", "GND"]),
        "CN1": ("Picture data in from the main board", _LVDS),
        "CN2": ("Column data out to source board A", _SRC),
        "CN3": ("Column data out to source board B", _SRC),
    },
    "led_driver_board": {
        "CN1": ("Backlight power and control in from the PSU", ["+36V", "GND", "BL_ON", "DIM"]),
        "C1": ("Smooths the 36 V input", ["+36V", "GND"]),
        "L1": ("Stores energy to boost the voltage", ["+36V", "LED_SW"]),
        "Q1": ("Switches the boost coil", ["LED_SW", "GND"]),
        "D1": ("Passes the boosted voltage on to the LEDs", ["LED_SW", "LED+"]),
        "U1": ("Holds the LED current constant and dims the backlight", ["BL_ON", "DIM", "LED-", "+36V", "GND"]),
        "C2": ("Smooths the LED supply", ["LED+", "GND"]),
        "R1": ("Measures the LED current", ["LED-", "GND"]),
        "R2": ("Measures the LED current", ["LED-", "GND"]),
        "CN2": ("Out to the LED strips", ["LED+", "LED-"]),
    },
    "wifi_board": {
        "U1": ("Wi-Fi and Bluetooth radio", ["USB_WIFI", "+5V", "GND"]),
        "CN1": ("USB link to the main board", ["USB_WIFI", "+5V", "GND"]),
        "Y1": ("Sets the radio's frequency accurately", []),
    },
    "ir_board": {
        "U1": ("Receives the infrared flashes from the remote", ["IR_RX", "+3V3_STBY", "GND"]),
        "LED1": ("Glows when the TV is in standby", ["LED_STBY", "GND"]),
        "SW1": ("The one button on the set: power and menu", ["KEY", "GND"]),
        "SW1b": ("The part of the button you press", []),
        "CN1": ("Link to the main board", _IRB),
    },
}

# Rows of small parts share one description.
ROW_RULES = {
    "mainboard": [
        (("C", 10, 19), ("Keeps the processor core supply steady", ["+1V1", "GND"])),
        (("C", 20, 29), ("Keeps the 3.3 V supply steady", ["+3V3", "GND"])),
        (("C", 30, 36), ("Keeps the memory supply steady", ["+1V5", "GND"])),
        (("R", 1, 4), ("Pull-up resistors for the configuration bus", ["I2C", "+3V3"])),
        (("R", 5, 8), ("Pull-up resistors for the HDMI identification lines", ["HDMI1", "HDMI2", "+5V"])),
    ],
}

# Nets carried by things that are not on a board (viewer item name -> nets).
ITEM_NETS = {
    "cable_psu_to_main": _PWR,
    "cable_psu_to_led_driver": ["+36V", "GND", "BL_ON", "DIM"],
    "cable_led_strips": ["LED+", "LED-"],
    "cable_mains": ["AC_L", "AC_N"],
    "ffc_lvds": _LVDS,
    "ffc_source_a": _SRC,
    "ffc_source_b": _SRC,
    "cable_speaker_right": ["SPK_R"],
    "cable_speaker_left": ["SPK_L"],
    "cable_ir_board": _IRB,
    "cable_wifi": ["USB_WIFI", "+5V", "GND"],
    "mains_inlet": ["AC_L", "AC_N"],
    "speakers": ["SPK_L", "SPK_R"],
    "led_strips": ["LED+", "LED-"],
    "led_chips": ["LED+", "LED-"],
    "source_boards": _SRC,
    "source_sockets": _SRC,
    "source_cofs": _SRC,
}
ITEM_ROLE = {
    "rear_cover": "Plastic back of the set: vents, connector recess, holes for the wall mount",
    "front_bezel": "Plastic frame round the screen",
    "lcd_cell": "The liquid-crystal glass that forms the picture. Each pixel is a tiny light valve",
    "mould_frame": "Plastic frame the glass rests on",
    "prism_sheet_upper": "Bends light towards the viewer, making the picture brighter",
    "prism_sheet_lower": "Bends light towards the viewer, making the picture brighter",
    "diffuser_sheet": "Evens out the light",
    "diffuser_plate": "Hides the individual LEDs so the screen is evenly lit",
    "support_pins": "Stop the diffuser plate sagging",
    "reflector_sheet": "Sends stray light forward",
    "led_lenses": "Spread each LED's light sideways",
    "led_chips": "The 24 white LEDs that light the screen",
    "led_strips": "Aluminium boards carrying the LEDs; the metal carries their heat away",
    "back_chassis": "Steel tray: the backbone everything bolts to",
    "source_boards": "Feed picture data to the column drivers",
    "source_cofs": "Flexible strips, each carrying a column-driver chip, bonded to the edge of the glass",
    "speakers": "Two 8 W speakers firing downwards",
    "mains_inlet": "Where the mains lead plugs in",
    "stand_feet": "Tabletop feet. Not fitted when the TV is on the wall mount",
}


def package(part: dict) -> str:
    """Guess how a component should look from its description."""
    d, kind, shape = part["desc"].lower(), part["kind"], part["shape"]
    if kind == "port":
        for word, pkg in (("hdmi", "hdmi"), ("usb", "usb"), ("toslink", "toslink"), ("3.5 mm", "jack"),
                          ("rca", "rca"), ("coaxial", "coax"), ("rj45", "rj45")):
            if word in d:
                return pkg
    rules = [
        ("ffc socket", "ffc"), ("2.54 mm", "header"), ("wafer", "wafer"), ("1.25 mm", "wafer"),
        ("3.96 mm", "wafer"),
        ("finned", "fins"), ("heatsink plate", "plate"),
        ("to-220", "to220"), ("bridge rectifier", "bridge"), ("optocoupler", "dip"),
        ("to-92", "to92"), ("dpak", "dpak"), ("smc", "smd_diode"),
        ("bga", "bga"), ("qfn", "qfn"), ("qfp", "qfp"),
        ("soic", "soic"), ("tssop", "soic"), ("sot", "sot"),
        ("usb power switch", "sot"), ("esd", "sot"), ("buck converter", "qfn"),
        ("transformer", "transformer"), ("common-mode", "toroid"),
        ("electrolytic", "ecap"), ("x2 film", "boxcap"), ("y1 safety", "disc"),
        ("varistor", "disc"), ("ntc", "disc"), ("fuse", "fuse"), ("tantalum", "tantalum"),
        ("crystal", "crystal"), ("shield", "can"),
        ("2512", "chip_r"), ("1206", "chip_r"), ("resistor", "chip_r"), ("ceramic", "chip_c"),
        ("infrared receiver", "ir"), ("indicator led", "led"), ("tactile", "switch"),
        ("plunger", "plunger"),
    ]
    for word, pkg in rules:
        if word in d:
            return pkg
    if kind == "magnetic":
        return "drum" if shape == "cyl" else "inductor"
    return "box"


def lookup(board_name: str, ref: str):
    """(role, nets) for one component, or None if it is not in the net list."""
    table = CONNECTIONS.get(board_name, {})
    if ref in table:
        return table[ref]
    for (prefix, first, last), info in ROW_RULES.get(board_name, []):
        if ref.startswith(prefix) and ref[len(prefix):].isdigit() and first <= int(ref[len(prefix):]) <= last:
            return info
    return None


def problems() -> list[str]:
    """Components with no entry, unknown net names, and nets with only one member."""
    found, members = [], {name: 0 for name in NETS}
    for board in BOARDS:
        for part in board["parts"]:
            info = lookup(board["name"], part["ref"])
            if info is None:
                found.append(f"{board['name']} {part['ref']} is not in the net list")
                continue
            for net in info[1]:
                if net not in NETS:
                    found.append(f"{board['name']} {part['ref']} uses unknown net {net}")
                else:
                    members[net] += 1
    for nets in ITEM_NETS.values():
        for net in nets:
            if net not in NETS:
                found.append(f"unknown net {net} on a cable")
            else:
                members[net] += 1
    found += [f"net {net} has only {n} connection" for net, n in members.items() if n < 2]
    return found


def net_members() -> dict:
    """net -> list of 'Board REF' strings, for the documentation."""
    out = {name: [] for name in NETS}
    for board in BOARDS:
        for part in board["parts"]:
            info = lookup(board["name"], part["ref"])
            for net in (info[1] if info else []):
                out[net].append(f"{board['title']} {part['ref']}")
    return out


def export() -> dict:
    """Everything the viewer needs to draw the boards and explain them."""
    from tv.boards import surface_w
    import config as cfg

    boards = []
    for board in BOARDS:
        surface, other, direction = surface_w(board)
        parts = []
        for part in board["parts"]:
            role, nets = lookup(board["name"], part["ref"]) or ("", [])
            u0, u1, v0, v1 = footprint(part)
            parts.append({
                "ref": part["ref"], "kind": part["kind"], "category": CATEGORY[part["kind"]][0],
                "pkg": package(part), "desc": part["desc"], "role": role, "nets": nets,
                "u": part["u"], "v": part["v"], "su": round(u1 - u0, 3), "sv": round(v1 - v0, 3),
                "h": round(height(part) - part.get("lift", 0.0), 3), "lift": part.get("lift", 0.0),
                "shape": part["shape"],
            })
        boards.append({
            "name": board["name"], "title": board["title"], "layers": board["layers"],
            "centre": list(board["centre"]), "size": list(board["size"]),
            "y_surface": cfg.STACK_DEPTH + surface, "direction": direction,
            "thickness": cfg.PCB_THICKNESS, "colour": list(board["colour"]),
            "holes": [list(h) for h in board["holes"]], "slots": [list(s) for s in board["slots"]],
            "parts": parts,
        })
    nets = [{"name": name, "kind": kind, "level": level, "colour": colour, "about": about}
            for name, (kind, level, colour, about) in NETS.items()]
    return {"boards": boards, "nets": nets,
            "kinds": [{"kind": k, "title": KIND_TITLE[k]} for k in KIND_ORDER],
            "item_nets": ITEM_NETS, "item_role": ITEM_ROLE}
