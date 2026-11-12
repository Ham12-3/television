"""
render.py - PNG pictures drawn from the exported STL files.

    output/renders/tv_front.png        the set from the room
    output/renders/tv_back.png         from behind, wall mount fitted
    output/renders/tv_inside.png       rear cover and mount removed
    output/renders/tv_boards.png       circuit boards and cables only
    output/renders/tv_exploded.png     every layer pulled apart
    output/renders/remote.png          the remote control
    output/renders/mount_front.png     wall mount only: front, back, side,
    output/renders/mount_back.png      three-quarter and exploded
    output/renders/mount_side.png
    output/renders/mount_iso.png
    output/renders/mount_exploded.png

A small software renderer written with numpy (a z-buffer), so it needs no GPU
and opens no window. Flat shading, no perspective, no transparency: these are
plain documentation pictures. The web viewer is the better way to look round.

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

import config as cfg

ROOT = Path(__file__).parent
STL_DIR = ROOT / cfg.OUT_STL
OUT_DIR = ROOT / cfg.OUT_RENDERS
BACKGROUND_RGB = (0.957, 0.957, 0.949)
WIDTH, HEIGHT = 1300, 900     # final picture size in pixels
SUPERSAMPLE = 2               # drawn this many times larger, then shrunk

BOARD_GROUPS = {"Main board", "Power supply board", "T-con board", "LED driver board",
                "Wi-Fi / Bluetooth module", "IR / LED / key board"}
ACCESSORIES = {"Stand feet", "Remote control"}


def is_mount(e): return e["group"] == "Wall mount"
def is_tv(e): return e["group"] not in ACCESSORIES
def is_inside(e): return (e["group"] not in ACCESSORIES | {"Wall mount"}
                          and e["name"] not in ("rear_cover", "cover_screws"))
def is_boards(e): return e["group"] in BOARD_GROUPS | {"Cables"}
def is_remote(e): return e["group"] == "Remote control"


# file name: (which parts, elevation, azimuth, exploded?)
# Azimuth 90 puts the camera at +Y, in the room, looking at the screen.
VIEWS = {
    "tv_front": (is_tv, 0, 90, False),
    "tv_back": (is_tv, 12, -62, False),
    "tv_inside": (is_inside, 12, -62, False),
    "tv_boards": (is_boards, 0, -90, False),
    "tv_exploded": (is_tv, 16, 128, True),
    "remote": (is_remote, 35, 120, False),
    "mount_front": (is_mount, 0, 90, False),
    "mount_back": (is_mount, 0, -90, False),
    "mount_side": (is_mount, 0, 0, False),
    "mount_iso": (is_mount, 22, 58, False),
    "mount_exploded": (is_mount, 22, 58, True),
}


def load_parts() -> list[tuple[dict, trimesh.Trimesh]]:
    """Read the manifest and every STL it lists."""
    manifest = json.loads((STL_DIR / "manifest.json").read_text())
    return [(entry, trimesh.load_mesh(str(STL_DIR / entry["file"]))) for entry in manifest["parts"]]


def camera_direction(elev: float, azim: float) -> np.ndarray:
    """Unit vector pointing from the model towards the camera."""
    e, a = np.radians(elev), np.radians(azim)
    return np.array([np.cos(e) * np.cos(a), np.cos(e) * np.sin(a), np.sin(e)])


def draw(parts, wanted, elev: float, azim: float, exploded: bool, path: Path) -> int:
    """Render one picture with a z-buffer: every pixel shows its nearest surface.

    Orthographic (no perspective). Drawn at twice the final size and then
    halved, which smooths the edges.
    """
    to_camera = camera_direction(elev, azim)
    right = np.cross([0.0, 0.0, 1.0], to_camera)
    right /= np.linalg.norm(right)
    up = np.cross(to_camera, right)
    # Light from over the camera's shoulder, a little above and to one side.
    light = to_camera + 0.45 * right + 0.6 * up
    light /= np.linalg.norm(light)

    triangles, colours, owners = [], [], []
    for number, (entry, mesh) in enumerate(parts):
        if not wanted(entry):
            continue
        shift = np.array(entry.get("explode", (0, 0, 0)), dtype=float) if exploded else np.zeros(3)
        normals = mesh.face_normals
        facing = normals @ to_camera > 1e-6         # skip faces pointing away
        # Many parts are black; lift the colours so shapes stay readable.
        base = 0.20 + 0.80 * np.array(entry["colour"])
        shade = 0.40 + 0.60 * np.clip(normals[facing] @ light, 0, 1)
        triangles.append(mesh.triangles[facing] + shift)
        colours.append(np.clip(base[None, :] * shade[:, None], 0, 1))
        owners.append(np.full(int(facing.sum()), number))
    triangles = np.concatenate(triangles)
    colours = np.concatenate(colours)
    owners = np.concatenate(owners)

    # Project to the picture plane: sx to the right, sy up, depth towards the camera.
    sx, sy, depth = triangles @ right, triangles @ up, triangles @ to_camera
    span = max(np.ptp(sx), np.ptp(sy) * WIDTH / HEIGHT)
    scale = (WIDTH * SUPERSAMPLE) * 0.92 / span
    w, h = WIDTH * SUPERSAMPLE, HEIGHT * SUPERSAMPLE
    px = (sx - (sx.min() + sx.max()) / 2) * scale + w / 2
    py = h / 2 - (sy - (sy.min() + sy.max()) / 2) * scale

    image = np.empty((h, w, 3))
    image[:] = BACKGROUND_RGB
    zbuffer = np.full((h, w), -np.inf)
    owner = np.full((h, w), -1)

    for i in range(len(triangles)):
        x0, x1 = int(np.floor(px[i].min())), int(np.ceil(px[i].max()))
        y0, y1 = int(np.floor(py[i].min())), int(np.ceil(py[i].max()))
        x0, y0, x1, y1 = max(x0, 0), max(y0, 0), min(x1, w - 1), min(y1, h - 1)
        if x1 < x0 or y1 < y0:
            continue
        (ax, bx, cx), (ay, by, cy) = px[i], py[i]
        area = (bx - ax) * (cy - ay) - (cx - ax) * (by - ay)
        if abs(area) < 1e-9:
            continue
        # Barycentric coordinates of every pixel centre in the bounding box.
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        l0 = ((bx - gx) * (cy - gy) - (cx - gx) * (by - gy)) / area
        l1 = ((cx - gx) * (ay - gy) - (ax - gx) * (cy - gy)) / area
        l2 = 1 - l0 - l1
        z = l0 * depth[i, 0] + l1 * depth[i, 1] + l2 * depth[i, 2]
        window = (slice(y0, y1 + 1), slice(x0, x1 + 1))
        hit = (l0 >= 0) & (l1 >= 0) & (l2 >= 0) & (z > zbuffer[window])
        zbuffer[window][hit] = z[hit]
        image[window][hit] = colours[i]
        owner[window][hit] = owners[i]

    # Thin dark outline wherever two different parts (or part and background) meet.
    edge = np.zeros((h, w), dtype=bool)
    edge[:, 1:] |= owner[:, 1:] != owner[:, :-1]
    edge[1:, :] |= owner[1:, :] != owner[:-1, :]
    image[edge] *= 0.45

    small = image.reshape(HEIGHT, SUPERSAMPLE, WIDTH, SUPERSAMPLE, 3).mean(axis=(1, 3))
    plt.imsave(path, np.clip(small, 0, 1))
    return len(triangles)


def main() -> int:
    if not (STL_DIR / "manifest.json").exists():
        print("No STL files found. Run `python export.py` first.")
        return 1
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for old in ("front", "back", "side", "iso", "exploded"):     # names used before the TV existed
        (OUT_DIR / f"{old}.png").unlink(missing_ok=True)
    parts = load_parts()
    for name, (wanted, elev, azim, exploded) in VIEWS.items():
        path = OUT_DIR / f"{name}.png"
        count = draw(parts, wanted, elev, azim, exploded, path)
        print(f"wrote {path.relative_to(ROOT)} ({count} triangles, {path.stat().st_size / 1024:.0f} kB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
