# -*- coding: utf-8 -*-
"""Transform-aware bounding box + <svg> wrapper for generated figures."""
import math
import re

TAG = re.compile(r'<(/?)([a-zA-Z]+)([^>]*?)(/?)>', re.S)
ATTR = re.compile(r'([a-zA-Z-]+)\s*=\s*"([^"]*)"')
NUM = re.compile(r'-?\d+\.?\d*(?:[eE][-+]?\d+)?')
XF = re.compile(r'(translate|rotate|scale|matrix)\s*\(([^)]*)\)')

I3 = (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)   # a b c d e f


def mul(m, n):
    a1, b1, c1, d1, e1, f1 = m
    a2, b2, c2, d2, e2, f2 = n
    return (a1 * a2 + c1 * b2, b1 * a2 + d1 * b2,
            a1 * c2 + c1 * d2, b1 * c2 + d1 * d2,
            a1 * e2 + c1 * f2 + e1, b1 * e2 + d1 * f2 + f1)


def apply(m, x, y):
    a, b, c, d, e, f = m
    return (a * x + c * y + e, b * x + d * y + f)


def parse_transform(s):
    m = I3
    for name, args in XF.findall(s or ""):
        v = [float(t) for t in NUM.findall(args)]
        if name == "translate":
            t = (1, 0, 0, 1, v[0], v[1] if len(v) > 1 else 0)
        elif name == "scale":
            sx = v[0]; sy = v[1] if len(v) > 1 else v[0]
            t = (sx, 0, 0, sy, 0, 0)
        elif name == "rotate":
            r = math.radians(v[0]); co, si = math.cos(r), math.sin(r)
            t = (co, si, -si, co, 0, 0)
            if len(v) >= 3:
                t = mul(mul((1, 0, 0, 1, v[1], v[2]), t), (1, 0, 0, 1, -v[1], -v[2]))
        elif name == "matrix":
            t = tuple(v[:6])
        else:
            continue
        m = mul(m, t)
    return m


def _leaf_points(tag, at):
    """Local-space extreme points of one element."""
    g = lambda k, d=0.0: float(at[k]) if k in at and NUM.fullmatch(at[k].strip() or "x") else d
    pts = []
    if tag == "polygon" or tag == "polyline":
        for p in at.get("points", "").split():
            if "," in p:
                a, b = p.split(",")[:2]
                pts.append((float(a), float(b)))
    elif tag == "line":
        pts += [(g("x1"), g("y1")), (g("x2"), g("y2"))]
    elif tag == "circle":
        cx, cy, r = g("cx"), g("cy"), g("r")
        pts += [(cx - r, cy - r), (cx + r, cy + r)]
    elif tag == "ellipse":
        cx, cy, rx, ry = g("cx"), g("cy"), g("rx"), g("ry")
        pts += [(cx - rx, cy - ry), (cx + rx, cy + ry)]
    elif tag == "rect":
        x, y, w, h = g("x"), g("y"), g("width"), g("height")
        pts += [(x, y), (x + w, y + h)]
    elif tag == "path":
        n = [float(t) for t in NUM.findall(at.get("d", ""))]
        pts += list(zip(n[0::2], n[1::2]))
    elif tag == "text":
        x, y = g("x"), g("y")
        fs = g("font-size", 16)
        body = at.get("_text", "")
        adv = sum(1.0 if ord(ch) > 0x2E7F else 0.55 for ch in body) or 1.0
        half = adv * fs / 2
        anc = at.get("text-anchor", "start")
        off = {"middle": -half, "end": -2 * half}.get(anc, 0.0)
        pts += [(x + off, y - fs), (x + off + 2 * half, y + fs * 0.4)]
    return pts


def bbox(svg_body):
    stack = [I3]
    xs, ys = [], []
    pos = 0
    for m in TAG.finditer(svg_body):
        close, tag, attrs, selfclose = m.group(1), m.group(2), m.group(3), m.group(4)
        at = {k: v for k, v in ATTR.findall(attrs)}
        if tag == "g" and not close:
            stack.append(mul(stack[-1], parse_transform(at.get("transform", ""))))
            continue
        if tag == "g" and close:
            if len(stack) > 1:
                stack.pop()
            continue
        if close:
            continue
        if tag == "text":
            end = svg_body.find("</text>", m.end())
            at["_text"] = svg_body[m.end():end] if end > 0 else ""
        cur = stack[-1]
        if at.get("transform"):
            cur = mul(cur, parse_transform(at["transform"]))
        for (x, y) in _leaf_points(tag, at):
            gx, gy = apply(cur, x, y)
            xs.append(gx); ys.append(gy)
    if not xs:
        return (0.0, 0.0, 100.0, 100.0)
    return min(xs), min(ys), max(xs), max(ys)


def svg(body, pad=26, cls="fig", extra="", vb=None, style=""):
    if vb is None:
        x0, y0, x1, y1 = bbox(body)
        vb = (x0 - pad, y0 - pad, (x1 - x0) + 2 * pad, (y1 - y0) + 2 * pad)
    return (f'<svg class="{cls}" viewBox="{vb[0]:.1f} {vb[1]:.1f} {vb[2]:.1f} {vb[3]:.1f}" '
            f'xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="xMidYMid meet" '
            f'style="{style}" {extra}>{body}</svg>')
