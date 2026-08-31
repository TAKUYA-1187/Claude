# -*- coding: utf-8 -*-
"""Model of the lift/fold bed table, drawn from iso primitives."""
from iso import (box, line3, hole, proj, pt, METAL, METAL_D, BLACK, WOOD, GHOST, Mat)

# ------------------------------------------------------------------ geometry
SPINE_X0, SPINE_X1 = 0.0, 520.0
SPINE_H, SPINE_Z = 28.0, 22.0          # spine height, half depth
FOOT_W, FOOT_Z = 46.0, 190.0           # foot bar width (X), half depth (Z)
POLE_CX = 57.0
IN_HW, OUT_HW = 22.0, 28.0             # inner / outer tube half width
COLLAR_HW = 30.0
POLE_BASE = SPINE_H                    # pole starts on top of the spine
IN_TOP0, COLLAR_H, OUT_H = 100.0, 14.0, 300.0
BRK_HW, BRK_H = 38.0, 34.0             # folding bracket
FRM_X0, FRM_X1, FRM_Z, FRM_T = -40.0, 300.0, 95.0, 9.0
TOP_X0, TOP_X1, TOP_Z, TOP_T = -60.0, 640.0, 180.0, 18.0
HOLES_X = (-10.0, 130.0, 270.0)
HOLES_Z = (-65.0, 65.0)


def pole_top(lift=0.0):
    return POLE_BASE + IN_TOP0 + COLLAR_H + OUT_H + lift


# ------------------------------------------------------------------- pieces
def base(mat=METAL, sw=1.6, caps=True, flip=False):
    """H base: spine + two foot bars. flip=True draws it upside down."""
    s = -1 if flip else 1
    o = SPINE_H if flip else 0.0          # keep the top face on y=0 when flipped

    def B(x0, y0, z0, dx, dy, dz, m=mat):
        return box(x0, s * (y0 + dy) + o if flip else y0, z0, dx, dy, dz, m, sw)

    out = []
    out.append(B(SPINE_X0, 0, -SPINE_Z, SPINE_X1 - SPINE_X0, SPINE_H, 2 * SPINE_Z))
    for fx in (SPINE_X0, SPINE_X1 - FOOT_W):
        out.append(B(fx, 0, -FOOT_Z, FOOT_W, SPINE_H, 2 * FOOT_Z))
        if caps:
            for cz in (-FOOT_Z, FOOT_Z - 20):
                out.append(B(fx + 3, 1, cz, FOOT_W - 6, SPINE_H - 2, 20, BLACK))
    return "".join(out)


def base_holes(y=SPINE_H, r=6):
    """The four pole-mounting holes on the spine."""
    return "".join(hole(POLE_CX + dx, y, dz, r)
                   for dx in (-16, 16) for dz in (-16, 16))


def pole(lift=0.0, y0=POLE_BASE, mat=METAL, sw=1.6, flip=False, out_h=None, in_h0=None):
    """Two-stage gas column. Thin inner tube at the bottom, thick outer above."""
    s = -1 if flip else 1
    out_h = OUT_H if out_h is None else out_h
    in_h = (IN_TOP0 if in_h0 is None else in_h0) + lift
    parts = [
        (y0, in_h, IN_HW, mat),                              # inner tube
        (y0 + in_h, COLLAR_H, COLLAR_HW, BLACK),             # black resin collar
        (y0 + in_h + COLLAR_H, out_h, OUT_HW, mat),          # outer tube
    ]
    out = []
    for (yy, hh, hw, m) in parts:
        yy2 = -(yy + hh) if flip else yy
        out.append(box(POLE_CX - hw, yy2, -hw, 2 * hw, hh, 2 * hw, m, sw))
    return "".join(out)


def bracket(y, sw=1.5, pin=True, flip=False):
    """Black spring folding bracket that sits on the pole top."""
    y0 = -(y + BRK_H) if flip else y
    out = [box(POLE_CX - BRK_HW, y0, -BRK_HW, 2 * BRK_HW, BRK_H, 2 * BRK_HW, BLACK, sw)]
    if pin:
        out.append(pull_pin(POLE_CX, y0 + BRK_H * 0.5, BRK_HW))
    return "".join(out)


def pull_pin(x, y, z, length=34):
    """One-touch spring pin sticking out of the bracket toward the viewer."""
    a, b = proj((x, y, z)), proj((x, y, z + length))
    return (f'<line x1="{a[0]:.2f}" y1="{a[1]:.2f}" x2="{b[0]:.2f}" y2="{b[1]:.2f}" '
            f'stroke="#14171A" stroke-width="5.5" stroke-linecap="round"/>'
            f'<circle cx="{b[0]:.2f}" cy="{b[1]:.2f}" r="7" fill="#F2F4F7" '
            f'stroke="#14171A" stroke-width="1.8"/>')


def frame(y, sw=1.4, holes=True, mat=METAL):
    """Table-top connecting frame plate."""
    out = [box(FRM_X0, y, -FRM_Z, FRM_X1 - FRM_X0, FRM_T, 2 * FRM_Z, mat, sw)]
    if holes:
        out += [hole(hx, y + FRM_T, hz, 7) for hx in HOLES_X for hz in HOLES_Z]
    return "".join(out)


def tabletop(y, mat=WOOD, sw=1.5, x0=TOP_X0, x1=TOP_X1, flip=False):
    y0 = -(y + TOP_T) if flip else y
    return box(x0, y0, -TOP_Z, x1 - x0, TOP_T, 2 * TOP_Z, mat, sw)


def lever(y, sw=1.5, ghost=False, reach=1.0):
    """Height-adjust lever: rod + black paddle grip, poking out front-left."""
    m = "#8A939E" if ghost else "#14171A"
    a = proj((POLE_CX - BRK_HW, y, 12))
    b = proj((POLE_CX - BRK_HW - 60 * reach, y, 90 * reach + 12))
    c = proj((POLE_CX - BRK_HW - 118 * reach, y, 176 * reach + 12))
    return (f'<path d="M{a[0]:.1f},{a[1]:.1f} L{b[0]:.1f},{b[1]:.1f}" stroke="{m}" '
            f'stroke-width="7" stroke-linecap="round" fill="none"/>'
            f'<path d="M{b[0]:.1f},{b[1]:.1f} L{c[0]:.1f},{c[1]:.1f}" stroke="{m}" '
            f'stroke-width="17" stroke-linecap="round" fill="none"/>')


def lever_tip(y, reach=1.0):
    """Screen position of the lever grip - anchor for hands and callouts."""
    return proj((POLE_CX - BRK_HW - 100 * reach, y, 150 * reach + 12))


def pole_inverted(y0, sw=1.6, lift=0.0):
    """Pole drawn upside down: thick outer tube at the bottom, thin end on top."""
    seq = [(OUT_H, OUT_HW, METAL), (COLLAR_H, COLLAR_HW, BLACK),
           (IN_TOP0 + lift, IN_HW, METAL)]
    out, y = [], y0
    for hh, hw, m in seq:
        out.append(box(POLE_CX - hw, y, -hw, 2 * hw, hh, 2 * hw, m, sw))
        y += hh
    return "".join(out), y


# --------------------------------------------------------- composite scenes
def table(lift=0.0, wood=True, sw=1.6, with_lever=True, top=True):
    """A fully assembled, upright table."""
    pt_ = pole_top(lift)
    brk_y = pt_
    frm_y = brk_y + BRK_H
    top_y = frm_y + FRM_T
    out = [base(sw=sw), pole(lift, sw=sw), bracket(brk_y, sw)]
    out.append(frame(frm_y, sw, holes=False))
    if with_lever:
        out.append(lever(frm_y + FRM_T * 0.5))
    if top:
        out.append(tabletop(top_y, WOOD if wood else METAL, sw))
    return "".join(out), top_y


def table_folded(lift=0.0, sw=1.6):
    """Top folded 90 deg up: rotated about the Z axis at the hinge."""
    pt_ = pole_top(lift)
    brk_y, hinge_x = pt_, POLE_CX + BRK_HW
    out = [base(sw=sw), pole(lift, sw=sw), bracket(brk_y, sw)]
    out.append(box(hinge_x, brk_y, -FRM_Z, FRM_T, FRM_X1 - FRM_X0, 2 * FRM_Z, METAL, sw))
    out.append(box(hinge_x + FRM_T, brk_y - 40, -TOP_Z, TOP_T,
                   TOP_X1 - TOP_X0, 2 * TOP_Z, WOOD, sw))
    out.append(lever(brk_y + 16))
    return "".join(out)
