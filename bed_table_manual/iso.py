# -*- coding: utf-8 -*-
"""Isometric line-art primitives for the bed-table manual illustrations.

Coordinate system (model space, millimetre-ish):
    +X : along the base spine, to the screen right-and-down
    +Y : up
    +Z : across the base feet, to the screen left-and-down
Visible faces of any axis-aligned box are always max-X, max-Y, max-Z.
"""
import math

COS30 = math.cos(math.radians(30))
SIN30 = 0.5

# ---------------------------------------------------------------- palettes
class Mat:
    def __init__(self, top, right, left, stroke="#1F2A37"):
        self.top, self.right, self.left, self.stroke = top, right, left, stroke

METAL = Mat("#FFFFFF", "#E9EDF1", "#D3DAE2")
METAL_D = Mat("#F2F4F7", "#DEE4EA", "#C6CFD9")
BLACK = Mat("#4A5058", "#33383F", "#23272C", "#14171A")
WOOD = Mat("#EFE1C8", "#DFCBA8", "#C9B189", "#8A6E48")
GHOST = Mat("none", "none", "none", "#B6BFC9")


def proj(p):
    x, y, z = p
    return (COS30 * (x - z), SIN30 * (x + z) - y)


def _poly(pts, fill, stroke, sw, dash=None, opacity=None):
    d = " ".join(f"{x:.2f},{y:.2f}" for x, y in pts)
    a = f'<polygon points="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" stroke-linejoin="round"'
    if dash:
        a += f' stroke-dasharray="{dash}"'
    if opacity is not None:
        a += f' opacity="{opacity}"'
    return a + "/>"


def box(x0, y0, z0, dx, dy, dz, mat=METAL, sw=1.5, opacity=None, dash=None):
    """Three visible faces of an axis-aligned box."""
    x1, y1, z1 = x0 + dx, y0 + dy, z0 + dz
    P = lambda x, y, z: proj((x, y, z))
    top = [P(x0, y1, z0), P(x1, y1, z0), P(x1, y1, z1), P(x0, y1, z1)]
    right = [P(x1, y1, z0), P(x1, y0, z0), P(x1, y0, z1), P(x1, y1, z1)]
    left = [P(x0, y1, z1), P(x1, y1, z1), P(x1, y0, z1), P(x0, y0, z1)]
    return "".join([
        _poly(left, mat.left, mat.stroke, sw, dash, opacity),
        _poly(right, mat.right, mat.stroke, sw, dash, opacity),
        _poly(top, mat.top, mat.stroke, sw, dash, opacity),
    ])


def plate(x0, y0, z0, dx, dy, dz, mat=METAL, sw=1.3):
    return box(x0, y0, z0, dx, dy, dz, mat, sw)


def line3(p0, p1, stroke="#1F2A37", sw=1.3, dash=None, opacity=None):
    a, b = proj(p0), proj(p1)
    s = f'<line x1="{a[0]:.2f}" y1="{a[1]:.2f}" x2="{b[0]:.2f}" y2="{b[1]:.2f}" stroke="{stroke}" stroke-width="{sw}" stroke-linecap="round"'
    if dash:
        s += f' stroke-dasharray="{dash}"'
    if opacity is not None:
        s += f' opacity="{opacity}"'
    return s + "/>"


def hole(x, y, z, r=7, stroke="#1F2A37", sw=1.2, fill="#FFFFFF"):
    """A bolt hole drawn on a horizontal (+Y facing) surface."""
    cx, cy = proj((x, y, z))
    return (f'<ellipse cx="{cx:.2f}" cy="{cy:.2f}" rx="{r*COS30:.2f}" ry="{r*SIN30:.2f}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')


def dot3(x, y, z, r=3, fill="#1F2A37"):
    cx, cy = proj((x, y, z))
    return f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{r}" fill="{fill}"/>'


def pt(x, y, z):
    return proj((x, y, z))
