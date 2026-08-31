# -*- coding: utf-8 -*-
"""All illustrations for the manual."""
import parts as P
from iso import box, hole, proj, METAL, METAL_D, BLACK, WOOD, Mat
from canvas import svg
import glyph as G

UNDER = Mat("#E7E3DC", "#D8D3C9", "#C3BDB1", "#8A8377")   # laminate underside
GHOSTM = Mat("none", "none", "none", "#AEB7C2")
RED, BLUE, INK = G.RED, G.BLUE, G.INK


def shadow(cx, cy, rx, ry=None, op=0.13):
    ry = ry or rx * 0.30
    return (f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{rx:.1f}" ry="{ry:.1f}" '
            f'fill="#1F2A37" opacity="{op}"/>')


def face_z(x0, x1, y0, y1, z, fill="#2B3038", stroke="#14171A", sw=2):
    pts = [proj((x0, y0, z)), proj((x1, y0, z)), proj((x1, y1, z)), proj((x0, y1, z))]
    d = " ".join(f"{a:.1f},{b:.1f}" for a, b in pts)
    return f'<polygon points="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'


def ghost_box(x0, y0, z0, dx, dy, dz, sw=2.8):
    return box(x0, y0, z0, dx, dy, dz, GHOSTM, sw, dash="11 8")


# ============================================================ hero / product
def hero(lift=110, w=None):
    body, top_y = P.table(lift)
    body += P.lever(P.pole_top(lift) + P.BRK_H + P.FRM_T * 0.5)
    sh = shadow(*proj((260, 0, 0)), 330, 96)
    return svg(sh + body, pad=30)


def hero_folded(lift=110):
    body = P.table_folded(lift)
    sh = shadow(*proj((260, 0, 0)), 300, 88)
    return svg(sh + body, pad=30)


# ================================================================ part icons
def _wrap(body, pad=16):
    return svg(body, pad=pad, cls="pfig")


def part_A():
    return _wrap(P.tabletop(0, WOOD, 2.0))


def part_B():
    return _wrap(P.base(sw=2.0))


def part_C():
    """Pole lying down, thin end to the left."""
    o = []
    o.append(box(0, 0, -P.IN_HW, 150, 2 * P.IN_HW, 2 * P.IN_HW, METAL, 2.0))
    o.append(box(150, -6, -P.COLLAR_HW, 22, 2 * P.COLLAR_HW, 2 * P.COLLAR_HW, BLACK, 2.0))
    o.append(box(172, -6, -P.OUT_HW, 300, 2 * P.OUT_HW, 2 * P.OUT_HW, METAL, 2.0))
    return _wrap("".join(o))


def part_D():
    o = [box(-40, 0, -95, 340, 9, 190, METAL, 1.8)]
    o += [hole(hx, 9, hz, 8) for hx in P.HOLES_X for hz in P.HOLES_Z]
    o.append(box(P.POLE_CX - 38, 9, -38, 76, 34, 76, BLACK, 1.8))
    o.append(P.pull_pin(P.POLE_CX, 26, 38))
    b = "".join(o)
    b += G.bolt(-150, -95, 26, 1.05) + G.bolt(-104, -95, 26, 1.05)
    b += G.bolt(-150, -20, 26, 1.05) + G.bolt(-104, -20, 26, 1.05)
    return _wrap(b)


def part_E():
    return _wrap(G.lever_icon(0, 0, 1.0))


# All three bolt cells share one viewBox so the lengths stay honestly comparable.
BOLT_VB = (-30, -20, 244, 178)


def part_bolt(length, n, cols=None):
    cols = cols or min(n, 4)
    o = []
    for i in range(n):
        r, c = divmod(i, cols)
        o.append(G.bolt(c * 46, r * 88, length, 1.0))
    return svg("".join(o), cls="pfig", vb=BOLT_VB)


def bolt_compare():
    """F / G / H side by side at true relative length."""
    o = []
    for i, (ltr, mm, ln) in enumerate((("F", "M8×50", 64), ("G", "M8×40", 48), ("H", "M8×12", 16))):
        x = i * 78
        o.append(G.bolt(x, 0, ln, 1.0))
        o.append(f'<text x="{x}" y="112" font-size="26" font-weight="900" fill="#1F2A37" '
                 f'text-anchor="middle" font-family="Noto Sans JP, sans-serif">{ltr}</text>')
        o.append(f'<text x="{x}" y="138" font-size="19" font-weight="500" fill="#4B535D" '
                 f'text-anchor="middle" font-family="Noto Sans JP, sans-serif">{mm}</text>')
        o.append(f'<line x1="{x+22}" y1="7" x2="{x+22}" y2="{7+ln+6}" stroke="#B6BFC9" '
                 f'stroke-width="1.4" stroke-dasharray="3 3"/>')
    return svg("".join(o), pad=14, cls="cmpfig")


def part_I(n=4):
    return _wrap("".join(G.washer(i * 46, 0, 1.0) for i in range(n)))


def part_J():
    return _wrap(G.hexkey(0, 0, 1.0))


# ============================================================ assembly steps
SHORT_OUT, SHORT_IN = 150.0, 62.0          # stubby pole for the close-in steps


def _short_top():
    return SHORT_IN + P.COLLAR_H + SHORT_OUT


def step1():
    """Insert the height-adjust lever into the pole slot."""
    o = [shadow(*proj((P.POLE_CX, 0, 0)), 120, 34)]
    o.append(P.pole(0, y0=0, sw=1.9, out_h=SHORT_OUT, in_h0=SHORT_IN))
    top = _short_top()
    sy0, sy1 = top - 66, top - 40
    o.append(face_z(P.POLE_CX - 20, P.POLE_CX + 20, sy0, sy1, P.OUT_HW, "#2B3038"))
    tipx, tipy = proj((P.POLE_CX, (sy0 + sy1) / 2, P.OUT_HW))
    o.append(G.lever_icon(tipx - 300, tipy - 130, 1.25, rot=18))
    o.append(G.arrow((tipx - 176, tipy - 22), (tipx - 26, tipy - 2), RED, 12, 28))
    o.append(G.label((tipx - 268, tipy - 168), "E", 46))
    o.append(G.leader((tipx - 250, tipy - 150), (tipx - 232, tipy - 108), INK))
    o.append(G.tag((tipx + 150, tipy - 78), "スロット", 34, "#1F2A37"))
    o.append(G.leader((tipx + 74, tipy - 64), (tipx + 8, tipy - 12), INK))
    return svg("".join(o), pad=34)


def step2():
    """Bolt the top unit (D) onto the pole head with 4 x G."""
    o = [shadow(*proj((P.POLE_CX, 0, 0)), 120, 34)]
    o.append(P.pole(0, y0=0, sw=1.9, out_h=SHORT_OUT, in_h0=SHORT_IN))
    ptop = _short_top()
    o += [hole(P.POLE_CX + dx, ptop, dz, 7) for dx in (-17, 17) for dz in (-17, 17)]
    by = ptop + 126
    hx = P.POLE_CX + P.BRK_HW
    o.append(box(hx, by, -P.FRM_Z, P.FRM_T, 175, 2 * P.FRM_Z, METAL, 1.7))
    o.append(box(P.POLE_CX - P.BRK_HW, by, -P.BRK_HW, 2 * P.BRK_HW, P.BRK_H,
                 2 * P.BRK_HW, BLACK, 1.9))
    o.append(P.pull_pin(P.POLE_CX, by + 17, P.BRK_HW))
    for dx in (-17, 17):
        for dz in (-17, 17):
            a = proj((P.POLE_CX + dx, by, dz))
            b = proj((P.POLE_CX + dx, ptop + 4, dz))
            o.append(G.leader(a, b, INK, 1.7, "6 6", dot=False))
    for dx in (-17, 17):
        for dz in (-17, 17):
            a = proj((P.POLE_CX + dx, by, dz))
            o.append(G.bolt(a[0], a[1] - 126, 46, 0.95))
    o.append(G.label(proj((hx + 26, by + 212, 60)), "D", 48))
    o.append(G.leader(proj((hx + 20, by + 200, 58)), proj((hx + 8, by + 146, 40))))
    gx, gy = proj((P.POLE_CX - 17, by, 17))
    o.append(G.label((gx - 78, gy - 176), "G", 48))
    o.append(G.leader((gx - 62, gy - 172), (gx - 14, gy - 140)))
    return svg("".join(o), pad=36)


def step3():
    """Table top face down; bolt the frame to it with 6 x H."""
    o = []
    o.append(shadow(*proj((290, 0, 0)), 400, 108))
    o.append(P.tabletop(0, UNDER, 1.8))
    ty = P.TOP_T
    o += [hole(hx, ty, hz, 9) for hx in P.HOLES_X for hz in P.HOLES_Z]
    fy = ty + 48
    o.append(box(P.FRM_X0, fy, -P.FRM_Z, P.FRM_X1 - P.FRM_X0, P.FRM_T, 2 * P.FRM_Z, METAL, 1.7))
    o.append(box(P.POLE_CX - P.BRK_HW, fy + P.FRM_T, -P.BRK_HW, 2 * P.BRK_HW,
                 P.BRK_H, 2 * P.BRK_HW, BLACK, 1.8))
    o.append(P.pull_pin(P.POLE_CX, fy + P.FRM_T + 17, P.BRK_HW))
    pb, ptp = P.pole_inverted(fy + P.FRM_T + P.BRK_H, 1.8)
    o.append(pb)
    for hx in P.HOLES_X:
        for hz in P.HOLES_Z:
            a = proj((hx, fy + P.FRM_T, hz))
            b = proj((hx, ty + 4, hz))
            o.append(G.leader(a, b, INK, 1.7, "6 6", dot=False))
            o.append(G.bolt(a[0], a[1] - 86, 26, 0.95))
    lx, ly = proj((P.HOLES_X[2], fy, P.HOLES_Z[0]))
    o.append(G.label((lx + 110, ly - 132), "H", 46))
    o.append(G.leader((lx + 92, ly - 132), (lx + 30, ly - 104)))
    o.append(G.label(proj((520, ty + 14, 120)), "A", 46))
    o.append(G.leader(proj((510, ty + 10, 120)), proj((440, ty + 2, 60))))
    o.append(G.tag(proj((300, ty + 10, 400)), "天板は裏返して床に置く", 34, "#1C6FA8"))
    return svg("".join(o), pad=38)


def step4():
    """Drop the H base onto the upward-facing pole end; 4 x F + 4 x I."""
    o = []
    o.append(shadow(*proj((290, 0, 0)), 400, 108))
    o.append(P.tabletop(0, UNDER, 1.6))
    ty = P.TOP_T
    o.append(box(P.FRM_X0, ty, -P.FRM_Z, P.FRM_X1 - P.FRM_X0, P.FRM_T, 2 * P.FRM_Z, METAL, 1.6))
    o.append(box(P.POLE_CX - P.BRK_HW, ty + P.FRM_T, -P.BRK_HW, 2 * P.BRK_HW,
                 P.BRK_H, 2 * P.BRK_HW, BLACK, 1.7))
    pb, ptp = P.pole_inverted(ty + P.FRM_T + P.BRK_H, 1.7)
    o.append(pb)
    by = ptp + 132
    o.append(P.base(sw=1.8).replace('id=', 'id='))
    # base sits high: rebuild it at height `by`
    o = o[:-1]
    o.append(_base_at(by, 1.8))
    o += [hole(P.POLE_CX + dx, by + P.SPINE_H, dz, 7) for dx in (-16, 16) for dz in (-16, 16)]
    for dx in (-16, 16):
        for dz in (-16, 16):
            a = proj((P.POLE_CX + dx, by + P.SPINE_H, dz))
            b = proj((P.POLE_CX + dx, ptp + 4, dz))
            o.append(G.leader(a, b, INK, 1.7, "6 6", dot=False))
            o.append(G.washer(a[0], a[1] - 54, 0.85))
            o.append(G.bolt(a[0], a[1] - 150, 62, 0.92))
    ax, ay = proj((P.POLE_CX + 16, by + P.SPINE_H, 16))
    o.append(G.label((ax + 116, ay - 210), "F", 46))
    o.append(G.leader((ax + 98, ay - 208), (ax + 24, ay - 176)))
    o.append(G.label((ax + 150, ay - 40), "I", 46))
    o.append(G.leader((ax + 132, ay - 46), (ax + 34, ay - 52)))
    o.append(G.label(proj((470, by + 40, 190)), "B", 46))
    o.append(G.leader(proj((462, by + 34, 186)), proj((420, by + 22, 150))))
    return svg("".join(o), pad=40)


def _base_at(y, sw=1.6):
    out = [box(P.SPINE_X0, y, -P.SPINE_Z, P.SPINE_X1 - P.SPINE_X0, P.SPINE_H,
               2 * P.SPINE_Z, METAL, sw)]
    for fx in (P.SPINE_X0, P.SPINE_X1 - P.FOOT_W):
        out.append(box(fx, y, -P.FOOT_Z, P.FOOT_W, P.SPINE_H, 2 * P.FOOT_Z, METAL, sw))
        for cz in (-P.FOOT_Z, P.FOOT_Z - 20):
            out.append(box(fx + 3, y + 1, cz, P.FOOT_W - 6, P.SPINE_H - 2, 20, BLACK, sw))
    return "".join(out)


def step5():
    """Turn the table the right way up."""
    body, top_y = P.table(0)
    body += P.lever(P.pole_top(0) + P.BRK_H + P.FRM_T * 0.5)
    o = [shadow(*proj((260, 0, 0)), 330, 96), body]
    a = proj((-140, 120, 240))
    b = proj((-150, 470, 240))
    o.append(G.arrow_curve((a[0] - 40, a[1]), (b[0] - 36, b[1]), 0.55, BLUE, 14, 34))
    o.append(G.tag(((a[0] + b[0]) / 2 - 214, (a[1] + b[1]) / 2), "静かに起こす", 36, "#1C6FA8"))
    return svg("".join(o), pad=36)


# ============================================================== how to use
def _hands_and_table(lift, ghost_lift, arrow_dir):
    body, top_y = P.table(lift)
    lev_y = P.pole_top(lift) + P.BRK_H + P.FRM_T * 0.5
    o = [shadow(*proj((260, 0, 0)), 330, 96)]
    gy = P.pole_top(ghost_lift) + P.BRK_H + P.FRM_T
    o.append(ghost_box(P.TOP_X0, gy, -P.TOP_Z, P.TOP_X1 - P.TOP_X0, P.TOP_T, 2 * P.TOP_Z))
    o.append(body)
    o.append(P.lever(lev_y))
    tip = P.lever_tip(lev_y)
    o.append(G.hand(tip[0] + 8, tip[1] + 78, 1.45, rot=-58, curl=0.9))
    px, py = proj((215, top_y + P.TOP_T, -70))
    o.append(G.hand(px + 226, py - 40, 1.5, rot=178, mirror=True, curl=0.22))
    ax, ay = proj((215, top_y + P.TOP_T, 30))
    if arrow_dir < 0:
        o.append(G.arrow((ax - 20, ay - 292), (ax - 20, ay - 76), RED, 18, 42))
    else:
        o.append(G.arrow((ax - 20, ay - 76), (ax - 20, ay - 292), RED, 18, 42))
    return o, tip


def op_down():
    o, tip = _hands_and_table(190, 0, -1)
    o.append(G.tag((tip[0] - 10, tip[1] + 226), "レバーを握る", 36, RED))
    return svg("".join(o), pad=40)


def op_up():
    o, tip = _hands_and_table(0, 190, +1)
    o.append(G.tag((tip[0] - 10, tip[1] + 226), "レバーを握る", 36, RED))
    return svg("".join(o), pad=40)


# ============================================================== folding
def fold_pin():
    """Close-up: pull the one-touch pin to release the hinge."""
    o = [box(P.POLE_CX - P.OUT_HW, -180, -P.OUT_HW, 2 * P.OUT_HW, 180,
             2 * P.OUT_HW, METAL, 2.0)]
    o.append(box(P.POLE_CX - P.BRK_HW, 0, -P.BRK_HW, 2 * P.BRK_HW, P.BRK_H,
                 2 * P.BRK_HW, BLACK, 2.0))
    o.append(box(P.POLE_CX - 34, P.BRK_H + 4, -42, 190, P.FRM_T, 84, METAL, 1.9))
    o.append(P.pull_pin(P.POLE_CX, 16, P.BRK_HW, 46))
    px, py = proj((P.POLE_CX, 16, P.BRK_HW + 46))
    o.append(G.arrow((px + 6, py - 4), (px - 112, py + 66), RED, 13, 30))
    o.append(G.hand(px - 178, py + 106, 1.15, rot=-30, curl=0.78))
    o.append(G.tag((px + 196, py - 112), "ワンタッチピン", 34, RED))
    o.append(G.leader((px + 86, py - 100), (px + 6, py - 8), RED))
    return svg("".join(o), pad=32)


def fold_lift(lift=110):
    body, top_y = P.table(lift)
    body += P.lever(P.pole_top(lift) + P.BRK_H + P.FRM_T * 0.5)
    o = [shadow(*proj((260, 0, 0)), 330, 96), body]
    hx = P.POLE_CX + P.BRK_HW
    o.append(ghost_box(hx + P.FRM_T, P.pole_top(lift) - 40, -P.TOP_Z, P.TOP_T,
                       P.TOP_X1 - P.TOP_X0, 2 * P.TOP_Z, 3.4))
    a = proj((600, top_y + P.TOP_T + 30, 0))
    b = proj((150, P.pole_top(lift) + 480, 0))
    o.append(G.arrow_curve(a, b, 0.30, BLUE, 15, 36))
    return svg("".join(o), pad=40)


def fold_done(lift=110):
    o = [shadow(*proj((260, 0, 0)), 300, 88), P.table_folded(lift)]
    return svg("".join(o), pad=34)


# ============================================================== small marks
def flow_icon(kind):
    if kind == "lever":
        return svg(G.lever_icon(0, 0, 0.7), pad=12, cls="ficon")
    if kind == "unit":
        b = box(-38, 0, -38, 76, 30, 76, BLACK, 2.2) + box(38, 0, -70, 8, 170, 140, METAL, 2.0)
        return svg(b, pad=12, cls="ficon")
    if kind == "top":
        return svg(P.tabletop(0, WOOD, 2.4, x0=0, x1=430), pad=12, cls="ficon")
    if kind == "base":
        return svg(P.base(sw=2.4, caps=False), pad=12, cls="ficon")
    if kind == "done":
        b, _ = P.table(60, sw=2.2)
        return svg(b, pad=12, cls="ficon")
    return ""
