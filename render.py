"""
render.py - PNG pictures of the assembly, drawn from the exported STL files.

    output/renders/front.png      seen from the room (the TV plate side)
    output/renders/back.png       seen from the wall side
    output/renders/side.png       seen from the right
    output/renders/iso.png        three-quarter view
    output/renders/exploded.png   three-quarter view, parts pulled apart

Uses matplotlib only, so it needs no GPU and opens no window. These are
simple shaded pictures for documentation, not photo-real renders.

Run:  python export.py   (first, to create the STL files)
      python render.py
"""

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # draw straight to files, never open a window
import matplotlib.pyplot as plt
import numpy as np
import trimesh
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

import config as cfg

ROOT = Path(__file__).parent
STL_DIR = ROOT / cfg.OUT_STL
OUT_DIR = ROOT / cfg.OUT_RENDERS

# name: (elevation, azimuth, exploded?)  Azimuth 90 puts the camera at +Y,
# which is where the TV would be, looking back at the wall.
VIEWS = {
    "front": (0, 90, False),
    "back": (0, -90, False),
    "side": (0, 0, False),
    "iso": (22, 58, False),
    "exploded": (22, 58, True),
}

# How far each part moves in the exploded view (x, y, z) in mm.
EXPLODE = {
    "wall_plate": (0, 0, 0),
    "tv_plate": (0, 55, 0),
    "lock_clip": (0, 20, -35),
    "cable_clip": (0, 20, -35),
}

BACKGROUND = "#f4f4f2"


def load_parts() -> list[tuple[str, trimesh.Trimesh, np.ndarray]]:
    """Read the manifest and every STL it lists."""
    manifest = json.loads((STL_DIR / "manifest.json").read_text())
    loaded = []
    for entry in manifest["parts"]:
        mesh = trimesh.load_mesh(str(STL_DIR / entry["file"]))
        loaded.append((entry["name"], mesh, np.array(entry["colour"])))
    return loaded


def camera_direction(elev: float, azim: float) -> np.ndarray:
    """Unit vector pointing from the model towards the camera."""
    e, a = np.radians(elev), np.radians(azim)
    return np.array([np.cos(e) * np.cos(a), np.cos(e) * np.sin(a), np.sin(e)])


def draw(parts, elev: float, azim: float, exploded: bool, path: Path) -> None:
    to_camera = camera_direction(elev, azim)
    # Light from over the camera's shoulder, a little above and to one side.
    side = np.cross(to_camera, [0, 0, 1])
    light = to_camera + 0.5 * side + np.array([0, 0, 0.6])
    light /= np.linalg.norm(light)

    triangles, colours = [], []
    for name, mesh, colour in parts:
        shift = np.array(EXPLODE[name.rstrip("_0123456789")]) if exploded else np.zeros(3)
        normals = mesh.face_normals
        facing = normals @ to_camera > 0            # skip faces pointing away
        # The real parts are black; lift the colours so shapes stay readable.
        base = 0.25 + 0.75 * colour
        shade = 0.35 + 0.65 * np.clip(normals[facing] @ light, 0, 1)
        triangles.append(mesh.triangles[facing] + shift)
        colours.append(np.clip(base[None, :] * shade[:, None], 0, 1))
    triangles = np.concatenate(triangles)
    colours = np.concatenate(colours)

    fig = plt.figure(figsize=(8, 8), facecolor=BACKGROUND)
    ax = fig.add_subplot(projection="3d", proj_type="ortho", facecolor=BACKGROUND)
    # One collection for everything, so matplotlib depth-sorts across parts.
    ax.add_collection3d(Poly3DCollection(triangles, facecolors=colours,
                                         edgecolors=colours, linewidths=0.2))

    low, high = triangles.reshape(-1, 3).min(axis=0), triangles.reshape(-1, 3).max(axis=0)
    centre, half = (low + high) / 2, (high - low).max() / 2 * 1.05
    ax.set_xlim(centre[0] - half, centre[0] + half)
    ax.set_ylim(centre[1] - half, centre[1] + half)
    ax.set_zlim(centre[2] - half, centre[2] + half)
    ax.set_box_aspect((1, 1, 1), zoom=1.25)
    ax.view_init(elev=elev, azim=azim)
    ax.set_axis_off()
    fig.subplots_adjust(0, 0, 1, 1)
    fig.savefig(path, dpi=150, facecolor=BACKGROUND)
    plt.close(fig)


def main() -> int:
    if not (STL_DIR / "manifest.json").exists():
        print("No STL files found. Run `python export.py` first.")
        return 1
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    parts = load_parts()
    for name, (elev, azim, exploded) in VIEWS.items():
        path = OUT_DIR / f"{name}.png"
        draw(parts, elev, azim, exploded, path)
        print(f"wrote {path.relative_to(ROOT)} ({path.stat().st_size / 1024:.0f} kB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
