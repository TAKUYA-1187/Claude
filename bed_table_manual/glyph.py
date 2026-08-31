# -*- coding: utf-8 -*-
"""2D glyphs: arrows, hands, fasteners, callouts. All in screen space."""
import math

RED = "#D62828"
BLUE = "#1C6FA8"
INK = "#1F2A37"
GREEN = "#2E7D5B"


def text_w(text, size):
    """Advance width estimate: CJK/full-width ~1.0em, ASCII ~0.55em."""
    w = 0.0
    for ch in text:
        w += 1.0 if ord(ch) > 0x2E7F else 0.55
    return w * size


def _u(p0, p1):
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    n = math.hypot(dx, dy) or 1
    return dx / n, dy / n, n


def arrow(p0, p1, color=RED, w=13, head=30, hw=None, opacity=1.0):
    """Solid straight arrow from p0 to p1."""
    ux, uy, n = _u(p0, p1)
    px, py = -uy, ux
    hw = hw or w * 1.85
    tipx, tipy = p1
    bx, by = p1[0] - ux * head, p1[1] - uy * head
    pts = [
        (p0[0] + px * w / 2, p0[1] + py * w / 2),
        (bx + px * w / 2, by + py * w / 2),
        (bx + px * hw, by + py * hw),
        (tipx, tipy),
        (bx - px * hw, by - py * hw),
        (bx - px * w / 2, by - py * w / 2),
        (p0[0] - px * w / 2, p0[1] - py * w / 2),
    ]
    d = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    return (f'<polygon points="{d}" fill="{color}" opacity="{opacity}" '
            f'stroke="#FFFFFF" stroke-width="1.6" stroke-linejoin="round"/>')


def arrow_curve(p0, p1, bulge=0.45, color=BLUE, w=13, head=30):
    """Curved arrow; bulge is perpendicular offset as a fraction of length."""
    ux, uy, n = _u(p0, p1)
    px, py = -uy, ux
    mx, my = (p0[0] + p1[0]) / 2 + px * n * bulge, (p0[1] + p1[1]) / 2 + py * n * bulge
    # shorten the end so the head sits at p1
    ex, ey = p1[0] - (p1[0] - mx) / max(n, 1) * head * 0.9, p1[1] - (p1[1] - my) / max(n, 1) * head * 0.9
    tux, tuy, _ = _u((mx, my), p1)
    bx, by = p1[0] - tux * head, p1[1] - tuy * head
    tpx, tpy = -tuy, tux
    d = f'M{p0[0]:.1f},{p0[1]:.1f} Q{mx:.1f},{my:.1f} {bx:.1f},{by:.1f}'
    headpts = f'{p1[0]:.1f},{p1[1]:.1f} {bx+tpx*w*1.7:.1f},{by+tpy*w*1.7:.1f} {bx-tpx*w*1.7:.1f},{by-tpy*w*1.7:.1f}'
    return (f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{w}" stroke-linecap="butt"/>'
            f'<polygon points="{headpts}" fill="{color}"/>')


def leader(p0, p1, color=INK, w=1.6, dash="5 5", dot=True):
    s = (f'<path d="M{p0[0]:.1f},{p0[1]:.1f} L{p1[0]:.1f},{p1[1]:.1f}" fill="none" '
         f'stroke="{color}" stroke-width="{w}" stroke-dasharray="{dash}"/>')
    if dot:
        s += f'<circle cx="{p1[0]:.1f}" cy="{p1[1]:.1f}" r="3.4" fill="{color}"/>'
    return s


def label(p, text, size=34, color=INK, weight=700, anchor="middle", dy=0):
    return (f'<text x="{p[0]:.1f}" y="{p[1]+dy:.1f}" font-size="{size}" fill="{color}" '
            f'font-weight="{weight}" text-anchor="{anchor}" '
            f'font-family="Noto Sans JP, sans-serif" paint-order="stroke" '
            f'stroke="#FFFFFF" stroke-width="5" stroke-linejoin="round">{text}</text>')


def tag(p, text, size=30, fill="#1F2A37", tc="#FFFFFF", pad=11, r=8):
    """Small filled pill label."""
    w = text_w(text, size) + pad * 2
    h = size * 1.5
    return (f'<g><rect x="{p[0]-w/2:.1f}" y="{p[1]-h/2:.1f}" width="{w:.1f}" height="{h:.1f}" '
            f'rx="{r}" fill="{fill}"/>'
            f'<text x="{p[0]:.1f}" y="{p[1]+size*0.36:.1f}" font-size="{size}" fill="{tc}" '
            f'font-weight="700" text-anchor="middle" font-family="Noto Sans JP, sans-serif">{text}</text></g>')


def circle_num(p, n, r=27, fill="#1F2A37", tc="#FFFFFF", size=32):
    return (f'<circle cx="{p[0]:.1f}" cy="{p[1]:.1f}" r="{r}" fill="{fill}"/>'
            f'<text x="{p[0]:.1f}" y="{p[1]+size*0.36:.1f}" font-size="{size}" fill="{tc}" '
            f'font-weight="700" text-anchor="middle" font-family="Noto Sans JP, sans-serif">{n}</text>')


# ------------------------------------------------------------------- hands
def hand(x, y, s=1.0, rot=0.0, mirror=False, curl=0.0):
    """Simple, readable hand glyph. Points +x (fingers to the right) at rot=0.
    curl 0 = flat/open, 1 = fingers curled down (gripping)."""
    sx = -1 if mirror else 1
    f = []
    f.append('<rect x="-64" y="-17" width="52" height="34" rx="17" '
             'fill="#FFFFFF" stroke="#1F2A37" stroke-width="4"/>')          # forearm
    f.append('<rect x="-24" y="-25" width="54" height="50" rx="16" '
             'fill="#FFFFFF" stroke="#1F2A37" stroke-width="4"/>')          # palm
    f.append(f'<g transform="rotate(38 4 20)"><rect x="-6" y="8" width="46" height="21" rx="10.5" '
             f'fill="#FFFFFF" stroke="#1F2A37" stroke-width="4"/></g>')      # thumb
    for i, cy in enumerate((-16.5, -5.5, 5.5, 16.5)):
        ln = 44 - abs(i - 1.4) * 3.5
        rr = 15 + curl * (28 - i * 3)
        f.append(f'<g transform="rotate({rr:.1f} 26 {cy})">'
                 f'<rect x="18" y="{cy-5.6:.1f}" width="{ln:.1f}" height="11.2" rx="5.6" '
                 f'fill="#FFFFFF" stroke="#1F2A37" stroke-width="4"/></g>')
    body = "".join(f)
    return (f'<g transform="translate({x:.1f},{y:.1f}) rotate({rot:.1f}) '
            f'scale({s*sx:.3f},{s:.3f})">{body}</g>')


# --------------------------------------------------------------- fasteners
def bolt(x, y, length=52, s=1.0, label_txt=None, rot=0.0, color="#EDF1F5"):
    """Socket-head cap screw, head up, shank pointing down."""
    b = []
    b.append(f'<rect x="-13" y="-11" width="26" height="13" rx="3.5" fill="{color}" '
             f'stroke="#1F2A37" stroke-width="2.6"/>')
    b.append('<circle cx="0" cy="-4.5" r="4.6" fill="#C9D2DB" stroke="#1F2A37" stroke-width="2"/>')
    b.append(f'<rect x="-11" y="2" width="22" height="5" rx="2" fill="#D9E0E7" '
             f'stroke="#1F2A37" stroke-width="2.2"/>')
    b.append(f'<rect x="-6.5" y="7" width="13" height="{length}" fill="#F3F6F8" '
             f'stroke="#1F2A37" stroke-width="2.4"/>')
    n = int(length // 7)
    for i in range(n):
        yy = 12 + i * 7
        if yy < length + 4:
            b.append(f'<line x1="-6.5" y1="{yy}" x2="6.5" y2="{yy-3.4}" stroke="#1F2A37" '
                     f'stroke-width="1.5" opacity="0.65"/>')
    b.append(f'<path d="M-6.5,{7+length} L0,{13+length} L6.5,{7+length}" fill="#F3F6F8" '
             f'stroke="#1F2A37" stroke-width="2.4" stroke-linejoin="round"/>')
    body = "".join(b)
    return f'<g transform="translate({x:.1f},{y:.1f}) rotate({rot}) scale({s:.3f})">{body}</g>'


def washer(x, y, s=1.0):
    body = ('<ellipse cx="0" cy="0" rx="17" ry="6.4" fill="#EDF1F5" stroke="#1F2A37" stroke-width="2.6"/>'
            '<ellipse cx="0" cy="0" rx="6.6" ry="2.5" fill="#FFFFFF" stroke="#1F2A37" stroke-width="2.2"/>')
    return f'<g transform="translate({x:.1f},{y:.1f}) scale({s:.3f})">{body}</g>'


def hexkey(x, y, s=1.0, rot=0.0):
    d = "M0,0 L0,84 L52,84"
    body = (f'<path d="{d}" fill="none" stroke="#1F2A37" stroke-width="14" '
            'stroke-linecap="round" stroke-linejoin="round"/>'
            f'<path d="{d}" fill="none" stroke="#DCE3EA" stroke-width="10" '
            'stroke-linecap="round" stroke-linejoin="round"/>'
            f'<path d="M-2.4,5 L-2.4,77" fill="none" stroke="#FFFFFF" stroke-width="2.4" '
            'stroke-linecap="round" opacity="0.9"/>')
    return f'<g transform="translate({x:.1f},{y:.1f}) rotate({rot}) scale({s:.3f})">{body}</g>'


def lever_icon(x, y, s=1.0, rot=0.0):
    body = ('<path d="M0,0 L64,64" stroke="#C6CFD9" stroke-width="11" stroke-linecap="round"/>'
            '<path d="M0,0 L64,64" stroke="#1F2A37" stroke-width="2.4" stroke-linecap="round" fill="none"/>'
            '<path d="M-16,16 L16,-16" stroke="#1F2A37" stroke-width="7" stroke-linecap="round"/>'
            '<path d="M58,58 C86,74 100,96 88,110 C76,124 52,112 40,86 Z" fill="#23272C" '
            'stroke="#14171A" stroke-width="2.4" stroke-linejoin="round"/>')
    return f'<g transform="translate({x:.1f},{y:.1f}) rotate({rot}) scale({s:.3f})">{body}</g>'


def check(x, y, s=1.0, color=GREEN):
    body = (f'<circle cx="0" cy="0" r="19" fill="{color}"/>'
            f'<path d="M-9,0 L-3,7 L10,-8" fill="none" stroke="#FFFFFF" stroke-width="5" '
            f'stroke-linecap="round" stroke-linejoin="round"/>')
    return f'<g transform="translate({x:.1f},{y:.1f}) scale({s:.3f})">{body}</g>'


def ban(x, y, s=1.0):
    body = ('<circle cx="0" cy="0" r="20" fill="none" stroke="#D62828" stroke-width="6"/>'
            '<line x1="-13" y1="13" x2="13" y2="-13" stroke="#D62828" stroke-width="6" stroke-linecap="round"/>')
    return f'<g transform="translate({x:.1f},{y:.1f}) scale({s:.3f})">{body}</g>'
