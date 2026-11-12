"""
tv/common.py - helpers shared by all television modules.

Inside the TV, depth is measured as w: millimetres forward from the TV's back
surface (see config.py). These helpers take w and convert to global Y, so the
part files can be written in the same terms as the stack-up in config.py.
"""

from dataclasses import dataclass, field

from build123d import Compound, Cone, Cylinder, Pos, Rot

import config as cfg
from parts.common import box


def gy(w: float) -> float:
    """Global Y for a depth w inside the TV."""
    return cfg.STACK_DEPTH + w


def tbox(x0, x1, z0, z1, w0, w1):
    """Axis-aligned box from X, Z and w limits (any order)."""
    x0, x1 = sorted((x0, x1))
    z0, z1 = sorted((z0, z1))
    w0, w1 = sorted((w0, w1))
    return box(x0, x1, gy(w0), gy(w1), z0, z1)


def centred(half_x, half_z, w0, w1, z_centre=0.0):
    """Box centred on X = 0 and Z = z_centre, given half sizes."""
    return tbox(-half_x, half_x, z_centre - half_z, z_centre + half_z, w0, w1)


def cyl_w(x, z, dia, w0, w1):
    """Cylinder with its axis along the depth direction."""
    w0, w1 = sorted((w0, w1))
    return Pos(x, gy((w0 + w1) / 2), z) * Rot(X=90) * Cylinder(dia / 2, w1 - w0)


def cyl_x(x0, x1, z, w, dia):
    """Cylinder with its axis along X."""
    x0, x1 = sorted((x0, x1))
    return Pos((x0 + x1) / 2, gy(w), z) * Rot(Y=90) * Cylinder(dia / 2, x1 - x0)


def cyl_z(x, z0, z1, w, dia):
    """Cylinder with its axis along Z (vertical)."""
    z0, z1 = sorted((z0, z1))
    return Pos(x, gy(w), (z0 + z1) / 2) * Cylinder(dia / 2, z1 - z0)


def cone_w(x, z, dia_back, dia_front, w0, w1):
    """Cone along the depth direction: dia_back at w0, dia_front at w1."""
    # Rot(X=90) puts the Cone's "bottom" at the +Y (front) end.
    return (Pos(x, gy((w0 + w1) / 2), z) * Rot(X=90)
            * Cone(dia_front / 2, dia_back / 2, w1 - w0))


def group(solids):
    """Bundle separate solids into one shape without fusing them (fast)."""
    return Compound(list(solids))


def fuse(solids):
    """Fuse solids into one body."""
    result = None
    for s in solids:
        result = s if result is None else result + s
    return result


def cut_all(part, tools):
    """Subtract many tools from a part."""
    tools = list(tools)
    if not tools:
        return part
    try:
        return part - group(tools)        # one boolean operation, much faster
    except Exception:
        for tool in tools:                # slow but dependable fallback
            part = part - tool
        return part


def wire(points, size=(2.5, 2.5)):
    """A cable drawn as straight box segments between (X, Z, w) points.

    Each segment must run along one axis. size = (width, thickness): the cable
    is `thickness` deep in w and `width` across. Real cables curve; these are
    simple stand-ins that show the routing.
    """
    width, thick = size
    segments = []
    for (xa, za, wa), (xb, zb, wb) in zip(points, points[1:]):
        hx = hz = width / 2
        hw = thick / 2
        segments.append(tbox(min(xa, xb) - hx, max(xa, xb) + hx,
                             min(za, zb) - hz, max(za, zb) + hz,
                             min(wa, wb) - hw, max(wa, wb) + hw))
    return fuse(segments)


def ribbon(points, width, thick=0.3):
    """A flat flexible cable (FFC) drawn as thin box segments.

    Runs along Z or along w keep their width across X; runs along X have their
    width across Z. Real FFCs fold at 45 degrees to turn a corner; here the
    corner is simply two overlapping straight pieces.
    """
    segments = []
    for (xa, za, wa), (xb, zb, wb) in zip(points, points[1:]):
        if xa != xb:                               # along X: width across Z
            segments.append(tbox(min(xa, xb) - width / 2, max(xa, xb) + width / 2,
                                 za - width / 2, za + width / 2, wa - thick / 2, wa + thick / 2))
        elif za != zb:                             # along Z: width across X
            segments.append(tbox(xa - width / 2, xa + width / 2, za, zb,
                                 wa - thick / 2, wa + thick / 2))
        else:                                      # along w (a riser): thin in Z
            segments.append(tbox(xa - width / 2, xa + width / 2, za - thick / 2, za + thick / 2,
                                 min(wa, wb) - thick / 2, max(wa, wb) + thick / 2))
    return fuse(segments)


@dataclass
class Item:
    """One thing in the TV assembly: a part, or a set of like parts."""
    name: str
    group: str                       # heading it appears under in the viewer
    shape: object                    # a build123d Part or Compound
    colour: tuple                    # display colour (r, g, b), 0..1
    material: str                    # key into cfg.DENSITY
    explode: tuple = (0.0, 0.0, 0.0) # movement at full "explode", mm
    fitted: bool = True              # False = accessory not installed on the wall
    opacity: float = 1.0
    note: str = ""
    extra: dict = field(default_factory=dict)

    def solids(self):
        return list(self.shape.solids())

    def volume(self) -> float:
        return sum(s.volume for s in self.solids())

    def mass_g(self) -> float:
        return self.volume() / 1000.0 * cfg.DENSITY[self.material]
