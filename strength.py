"""
strength.py - the hand calculation from DESIGN.md section 8, as code.

Every number comes from config.py, so the results follow any design change.
These are simple textbook formulas (statics, beam bending, bearing stress).
They are a sanity check, NOT a substitute for a proof load or FEA: see the
limits listed in DESIGN.md.

Sign convention and method
    W  = weight of the rated TV, acting straight down at LOAD_OFFSET_FROM_WALL.
    The 45 degree cleat is treated as frictionless. That is the worst case
    for the cleat: it makes the horizontal wedge force as large as possible.

Run:  python strength.py
"""

import math

import config as cfg

STRESS_CONCENTRATION = 2.5   # assumed Kt at the filleted cleat groove


def calculate() -> dict:
    """Return every intermediate value of the hand calculation."""
    r = {}
    W = cfg.DESIGN_LOAD_N
    slope = math.tan(math.radians(cfg.CLEAT_ANGLE))

    # Allowable long-term stresses. Between layers the same 20 percent-of-yield
    # creep rule is applied to the weaker inter-layer strength.
    r["allow_inplane"] = cfg.PETG_CREEP_ALLOWABLE
    r["allow_interlayer"] = (cfg.PETG_CREEP_ALLOWABLE
                             * cfg.PETG_YIELD_INTERLAYER / cfg.PETG_YIELD_INPLANE)
    r["allow_shear"] = 0.5 * r["allow_inplane"]
    r["W"] = W

    # --- 1. Cleat geometry -------------------------------------------------
    y_wall, y_tv = cfg.Y_WALL_PLATE_FRONT, cfg.Y_TV_PLATE_BACK
    band_y0 = y_wall + cfg.CLEAT_CLEARANCE + cfg.CLEAT_TIP_FLAT     # hook's flat ends
    band_y1 = y_tv - cfg.CLEAT_CLEARANCE - cfg.CLEAT_TIP_FLAT       # rail's flat starts
    r["band"] = band_y1 - band_y0                                   # horizontal width
    y_c = (band_y0 + band_y1) / 2                                   # centre of contact
    z_c = cfg.CLEAT_APEX_Z - (y_tv - y_c) * slope
    r["y_c"], r["z_c"] = y_c, z_c

    # --- 2. Forces on the cleat (frictionless 45 degree wedge) ---------------
    r["V"] = W                                   # vertical force on the rail
    r["H"] = W / slope                           # horizontal wedge force on the rail
    r["N"] = math.hypot(r["V"], r["H"])          # normal force on the slope

    # Overturning: the TV's weight acts in front of the cleat, so the bottom of
    # the TV plate presses on the lower rail (B) and the top pulls on the wall.
    r["B"] = W * (cfg.LOAD_OFFSET_FROM_WALL - y_c) / (z_c - cfg.LOWER_RAIL_Z)

    # --- 3. Bearing on the cleat slope --------------------------------------
    area = r["band"] / math.cos(math.radians(cfg.CLEAT_ANGLE)) * cfg.CLEAT_LENGTH
    r["slope_area"] = area
    r["slope_bearing"] = r["N"] / area

    # --- 4. Cleat root (same for the rail and the hook) ---------------------
    # The root is the section where the rail joins its plate. Printed flat,
    # that section is a layer plane, so inter-layer strength applies.
    h, b = cfg.CLEAT_ROOT, cfg.CLEAT_LENGTH
    r["root_area"] = b * h
    r["root_modulus"] = b * h ** 2 / 6
    z_groove = cfg.CLEAT_APEX_Z - cfg.CLEAT_DEPTH * slope
    arm_v = y_c - y_wall                         # V acts this far out from the root
    arm_h = z_c - (z_groove - h / 2)             # H acts this far above the root centre
    r["arm_v"], r["arm_h"] = arm_v, arm_h
    r["root_moment"] = r["V"] * arm_v + r["H"] * arm_h
    r["root_bending"] = r["root_moment"] / r["root_modulus"]
    r["root_tension"] = r["H"] / r["root_area"]
    r["root_total"] = r["root_bending"] + r["root_tension"]
    r["root_shear"] = r["V"] / r["root_area"]
    r["root_peak"] = r["root_total"] * STRESS_CONCENTRATION

    # --- 5. Wall plate bending ------------------------------------------------
    # Net pull on the wall plate at the cleat equals B (horizontal balance:
    # the hook's wedge pull is partly returned by the hook tip pressing on the
    # plate). The plate spans between the two top screws; the rail stiffens the
    # middle, so the critical section is at the end of the rail.
    r["P_net"] = r["B"]
    arm = cfg.WALL_SCREW_SPACING_X / 2 - cfg.CLEAT_LENGTH / 2
    r["plate_arm"] = arm
    r["plate_moment"] = r["P_net"] / 2 * arm
    band = cfg.WALL_PLATE_HEIGHT / 2 - cfg.CABLE_WINDOW_HEIGHT / 2   # strip above the window
    r["plate_band"] = band
    r["plate_modulus"] = band * cfg.PLATE_THICKNESS ** 2 / 6
    r["plate_bending"] = r["plate_moment"] / r["plate_modulus"]

    # --- 6. VESA screws in the TV plate ---------------------------------------
    d = float(cfg.VESA_SCREW[1:])
    r["vesa_bearing_4"] = (W / 4) / (d * cfg.PLATE_THICKNESS)
    r["vesa_bearing_2"] = (W / 2) / (d * cfg.PLATE_THICKNESS)
    # Top pair also carries tension from the TV's centre of mass being in front.
    moment = W * (cfg.LOAD_OFFSET_FROM_WALL - cfg.STACK_DEPTH)
    r["vesa_tension"] = moment / cfg.VESA_Z / 2                  # per top screw
    head_area = math.pi / 4 * (cfg.VESA_HEAD_DIA ** 2 - cfg.hole_dia(cfg.VESA_SCREW) ** 2)
    r["vesa_head_bearing"] = r["vesa_tension"] / head_area

    # --- 7. Wall screws ------------------------------------------------------
    r["wall_shear_each"] = W / 4
    r["wall_bearing"] = (W / 4) / (cfg.WALL_SCREW_DIA * cfg.PLATE_THICKNESS)
    # Pull-out: plate pivots about its bottom edge; screw tension is taken as
    # proportional to height above that edge.
    pivot = cfg.WALL_PLATE_BOTTOM_Z
    top = cfg.WALL_SCREW_SPACING_Z / 2 - pivot
    bottom = -cfg.WALL_SCREW_SPACING_Z / 2 - pivot
    overturn = W * cfg.LOAD_OFFSET_FROM_WALL
    r["wall_pullout"] = overturn * top / (2 * (top ** 2 + bottom ** 2))
    hole = cfg.WALL_SCREW_CLEARANCE + cfg.PRINTED_HOLE_COMP
    csk_area = math.pi / 4 * (cfg.WALL_SCREW_HEAD_DIA ** 2 - hole ** 2)
    r["wall_head_bearing"] = r["wall_pullout"] / csk_area

    # --- 8. Lock clip (not in the load path; snap-fit numbers only) -----------
    t, L, y = cfg.LOCK_CLIP_ARM_THICKNESS, cfg.LOCK_CLIP_ARM_LENGTH, cfg.LOCK_CLIP_BARB
    r["clip_strain"] = 1.5 * t * y / L ** 2
    deflect = cfg.PETG_MODULUS * cfg.LOCK_CLIP_DEPTH * t ** 3 * y / (4 * L ** 3)
    mu = 0.3

    def ramp(angle):
        k = math.tan(math.radians(angle))
        return 2 * deflect * (mu + k) / (1 - mu * k)             # two arms
    r["clip_push_in"] = ramp(cfg.SNAP_LEAD_ANGLE)
    r["clip_pull_out"] = ramp(cfg.SNAP_RETURN_ANGLE)
    return r


def checks(r: dict = None) -> list[tuple[str, bool, str]]:
    """Safety factor for each load path, as (description, passed, detail)."""
    r = r or calculate()
    target = cfg.TARGET_SAFETY_FACTOR
    rows = [
        # (name, stress, allowable, required factor)
        ("Cleat slope bearing", r["slope_bearing"], r["allow_inplane"], target),
        ("Cleat root, bending + tension (between layers)", r["root_total"],
         r["allow_interlayer"], target),
        ("Cleat root, shear (between layers)", r["root_shear"],
         0.5 * r["allow_interlayer"], target),
        ("Wall plate bending at the end of the rail", r["plate_bending"],
         r["allow_inplane"], target),
        ("VESA hole bearing, 4 screws sharing", r["vesa_bearing_4"], r["allow_inplane"], target),
        ("VESA screw head bearing on the plate", r["vesa_head_bearing"],
         r["allow_inplane"], target),
        ("Wall screw hole bearing, 4 screws sharing", r["wall_bearing"],
         r["allow_inplane"], target),
        ("Wall screw head bearing in the countersink", r["wall_head_bearing"],
         r["allow_inplane"], target),
        # Pessimistic cases, held to a lower bar.
        ("VESA hole bearing if only 2 screws carry (pessimistic)", r["vesa_bearing_2"],
         r["allow_inplane"], 3.0),
        ("Cleat root peak stress with Kt, vs short-term strength", r["root_peak"],
         cfg.PETG_YIELD_INTERLAYER, target),
    ]
    out = []
    for name, stress, allow, need in rows:
        factor = allow / stress
        out.append((f"{name}: safety factor >= {need:.0f}", factor >= need,
                    f"{stress:.2f} MPa vs {allow:.1f} MPa allowable, factor {factor:.1f}"))
    out.append(("Lock clip arm strain <= 2 percent", r["clip_strain"] <= 0.02,
                f"{r['clip_strain'] * 100:.2f} percent"))
    return out


def governing(r: dict = None) -> tuple[str, float]:
    """The lowest safety factor among the main (non-pessimistic) load paths."""
    r = r or calculate()
    paths = {
        "cleat slope bearing": r["allow_inplane"] / r["slope_bearing"],
        "cleat root": r["allow_interlayer"] / r["root_total"],
        "cleat root shear": 0.5 * r["allow_interlayer"] / r["root_shear"],
        "wall plate bending": r["allow_inplane"] / r["plate_bending"],
        "VESA hole bearing": r["allow_inplane"] / r["vesa_bearing_4"],
        "wall screw hole bearing": r["allow_inplane"] / r["wall_bearing"],
    }
    name = min(paths, key=paths.get)
    return name, paths[name]


def main() -> int:
    r = calculate()
    print(f"Strength hand calculation - {cfg.TV_MASS_MAX_KG:.0f} kg TV, {cfg.MATERIAL}")
    print("-" * 74)
    print(f"Weight W                          {r['W']:8.1f} N")
    print(f"Cleat: vertical V / horizontal H  {r['V']:8.1f} / {r['H']:.1f} N (frictionless wedge)")
    print(f"Cleat: normal force on slope      {r['N']:8.1f} N over {r['slope_area']:.0f} mm2")
    print(f"Lower rail push B = net wall pull {r['B']:8.1f} N")
    print(f"Cleat root moment                 {r['root_moment']:8.0f} N.mm "
          f"(arms {r['arm_v']:.1f} and {r['arm_h']:.1f} mm), Z = {r['root_modulus']:.0f} mm3")
    print(f"Wall plate moment at rail end     {r['plate_moment']:8.0f} N.mm, "
          f"Z = {r['plate_modulus']:.0f} mm3")
    print(f"VESA top screw tension            {r['vesa_tension']:8.1f} N each")
    print(f"Wall screw shear / pull-out       {r['wall_shear_each']:8.1f} / {r['wall_pullout']:.1f} N each (top pair)")
    print(f"Lock clip push-in / pull-out      {r['clip_push_in']:8.0f} / {r['clip_pull_out']:.0f} N (estimate)")
    print(f"Allowable long-term stress        {r['allow_inplane']:.1f} MPa along layers, "
          f"{r['allow_interlayer']:.1f} MPa between layers")
    print()
    failed = 0
    for text, ok, detail in checks(r):
        failed += not ok
        print(f"[{'PASS' if ok else 'FAIL'}] {text}  ({detail})")
    name, factor = governing(r)
    print("-" * 74)
    print(f"Governing load path: {name}, safety factor {factor:.1f} "
          f"(target {cfg.TARGET_SAFETY_FACTOR:.0f})")
    print("ALL PASS" if failed == 0 else f"{failed} FAILED")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
