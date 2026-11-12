"""
common.py - small geometry helpers shared by all parts.

Every part is modelled directly in assembly coordinates (see config.py for the
axes), so no part needs to be moved when the assembly is put together.

The helpers hide build123d's plane conventions so the part files read as plain
"draw this outline, extrude it between these two coordinates".
"""

from build123d import (
    Axis, Box, Circle, Cylinder, Part, Plane, Polygon, Pos, Rot,
    extrude, fillet,
)


def box(x0, x1, y0, y1, z0, z1) -> Part:
    """Axis-aligned box given by its min / max corner coordinates."""
    return Pos((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2) * Box(x1 - x0, y1 - y0, z1 - z0)


def xz_plane(y: float) -> Plane:
    """Sketch plane parallel to the wall at distance y. Local axes are (X, Z)."""
    # Plane.XZ's normal points to -Y, so a negative offset moves it to +Y.
    return Plane.XZ.offset(-y)


def extrude_xz(sketch_2d, y0: float, y1: float) -> Part:
    """Extrude a 2D shape drawn in (X, Z) from y0 out to y1 (y1 > y0)."""
    # An explicit direction is used (here and below) because the default
    # direction flips when an outline is drawn clockwise.
    return extrude(xz_plane(y0) * sketch_2d, amount=y1 - y0, dir=(0, 1, 0))


def extrude_yz(points, x0: float, x1: float) -> Part:
    """Extrude a polygon given as (Y, Z) points along X from x0 to x1."""
    # Plane.YZ has local axes (Y, Z) and its normal points to +X.
    profile = Plane.YZ.offset(x0) * Polygon(*points, align=None)
    return extrude(profile, amount=x1 - x0, dir=(1, 0, 0))


def extrude_xy(sketch_2d, z0: float, z1: float) -> Part:
    """Extrude a 2D shape drawn in (X, Y) from z0 up to z1."""
    return extrude(Plane.XY.offset(z0) * sketch_2d, amount=z1 - z0, dir=(0, 0, 1))


def hole_along_y(x: float, z: float, dia: float, y0: float, y1: float) -> Part:
    """Cylinder with its axis along Y, used as a cutting tool for through holes."""
    length = y1 - y0
    return Pos(x, (y0 + y1) / 2, z) * Rot(X=90) * Cylinder(dia / 2, length)


def round_y_edges(part: Part, radius: float) -> Part:
    """Fillet every edge that runs parallel to Y (the print-up direction)."""
    return fillet(part.edges().filter_by(Axis.Y), radius)


def edges_along_x_at(part: Part, y: float, z: float, tol: float = 0.05):
    """Edges parallel to X whose midpoint is at the given (y, z). For root fillets."""
    found = []
    for edge in part.edges().filter_by(Axis.X):
        c = edge.center()
        if abs(c.Y - y) < tol and abs(c.Z - z) < tol:
            found.append(edge)
    return found


def try_fillet(part: Part, edges, radius: float, what: str) -> Part:
    """Fillet if possible; otherwise keep the part and say so (never fail silently)."""
    if not edges:
        print(f"  note: no edge found for {what}; fillet skipped")
        return part
    try:
        return fillet(edges, radius)
    except Exception as err:  # OpenCascade raises several error types here
        print(f"  note: fillet for {what} failed ({type(err).__name__}); left sharp")
        return part
