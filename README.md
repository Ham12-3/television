# 3D-printed TV wall mount (32", VESA 100x100)

A code-driven (parametric) CAD model of a French-cleat TV wall mount, printed in
PETG. See [DESIGN.md](DESIGN.md) for the design brief, assumptions and limits.

**Status:** all 8 steps done. The parts are modelled, exported, viewable in
the browser and pass all 91 validation checks, including a strength hand
calculation (lowest safety factor 6.2 for an 8 kg TV).

**Nothing has been printed or load-tested.** Read the limits and the proof-load
procedure in DESIGN.md section 8 before hanging a TV on this.

## Regenerate everything

After changing `config.py`, run these in order:

```powershell
.\.venv\Scripts\python.exe config.py      # are the numbers consistent?
.\.venv\Scripts\python.exe assembly.py    # do the parts build without clashing?
.\.venv\Scripts\python.exe printing.py    # can each part print without supports?
.\.venv\Scripts\python.exe strength.py    # is every load path above the safety factor?
.\.venv\Scripts\python.exe export.py      # write STEP and STL files
.\.venv\Scripts\python.exe render.py      # write PNG pictures
.\.venv\Scripts\python.exe validate.py    # full pass / fail report
```

`validate.py` is the one to trust: it repeats the config, printability and
strength checks and adds mesh, wall-thickness, screw-hole, TV-fit and assembly
checks.
It also fails if the STL files on disk no longer match `config.py`.

Each script prints PASS / FAIL and exits with a non-zero code on failure.

## Web viewer

Rotate, zoom, explode and toggle each part in the browser:

```powershell
.\.venv\Scripts\python.exe -m http.server 5173 --bind 127.0.0.1
```

Then open <http://localhost:5173/>. Press Ctrl+C in the terminal to stop it.

- It must be served like this; opening `index.html` by double-click will not
  work, because browsers block pages on disk from loading other files.
- It reads `output/stl/manifest.json`, so run `export.py` first, and refresh
  the page after each re-export.
- three.js (version 0.160.0) loads from the jsDelivr CDN, so the page needs
  internet access the first time.
- Any free port works. Port 8000 is blocked on some Windows machines.

## Outputs

| Folder | Contents |
|--------|----------|
| `output/step/` | One STEP per part, plus `tv_wall_mount.step` (assembly with dummy screws) |
| `output/stl/` | STLs in assembly position, plus `manifest.json` for the viewer |
| `output/stl_print/` | STLs laid flat on the bed. **Load these in your slicer.** Print `cable_clip.stl` twice |
| `output/renders/` | `front`, `back`, `side`, `iso` and `exploded` PNGs |

## Setup (once)

Windows PowerShell, from this folder:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

macOS / Linux:

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

## Commands

Run these with the virtual environment's Python (`.\.venv\Scripts\python.exe` on
Windows, `.venv/bin/python` elsewhere).

| Command | What it does |
|---------|--------------|
| `python config.py` | Prints every parameter and checks they are consistent |
| `python smoke_test.py` | Builds a test plate and checks STEP / STL export works |
| `python assembly.py` | Builds all parts, prints size and mass, checks no parts overlap |
| `python printing.py` | Checks overhangs, bridges and bed fit in print orientation |
| `python strength.py` | Hand calculation: stress and safety factor for each load path |
| `python export.py` | Writes all STEP and STL files |
| `python render.py` | Draws the PNG views from the STL files (run `export.py` first) |
| `python validate.py` | Full validation report (run `export.py` first) |

## Changing a dimension

Every dimension lives in [config.py](config.py). Edit a number there, then run
`python config.py` to check nothing clashes. No other file holds dimensions.

## Files

| File | Purpose |
|------|---------|
| `DESIGN.md` | Design brief, assumptions, load case, limits |
| `config.py` | All named parameters, plus quick consistency checks |
| `smoke_test.py` | Confirms the CAD toolchain works on this machine |
| `parts/wall_plate.py` | Wall plate: cleat rail, lower rail, wall-screw holes |
| `parts/tv_plate.py` | TV plate: cleat hook, lock tab, VESA holes |
| `parts/lock_clip.py` | Snap-in clip that stops the TV lifting off |
| `parts/cable_clip.py` | Snap-in cable holder |
| `parts/common.py` | Small geometry helpers shared by the parts |
| `assembly.py` | Collects the parts, adds dummy screws, checks for clashes |
| `printing.py` | Print orientation of each part, plus the overhang and bridge check |
| `export.py` | STEP and STL export |
| `render.py` | PNG renders (matplotlib, no GPU needed) |
| `strength.py` | Strength hand calculation (mirrors DESIGN.md section 8) |
| `validate.py` | Pass / fail validation report |
| `index.html` | three.js web viewer |
| `requirements.txt` | Pinned Python dependencies |
