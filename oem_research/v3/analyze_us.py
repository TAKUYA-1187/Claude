# -*- coding: utf-8 -*-
"""US new releases -> candidates for Japan: launched recently (ASIN series B0G*/B0H*),
priced >= $70, selling (past-month purchase badge), large or heavy, and whether the same
ASIN or the concept already exists on Amazon.co.jp."""
import re

ELECTRIC = re.compile(r"\b(electric|battery|rechargeable|cordless|motor|heater|\d+W\b|volt|USB|smart|app|wifi|wi-fi|"
                      r"bluetooth|led|charger|freezer|refrigerator|ice maker|dryer|vacuum|camera|robot|purifier)\b", re.I)


def bought_n(s):
    m = re.match(r"([\d.,]+)(K)?\+?", s or "")
    if not m:
        return 0
    return int(float(m.group(1).replace(",", "")) * (1000 if m.group(2) else 1))


def pounds(w):
    m = re.search(r"([\d.]+)\s*(pounds|lbs?|kilograms|kg|ounces)", w or "", re.I)
    if not m:
        return None
    v = float(m.group(1))
    u = m.group(2).lower()
    return v * 2.2046 if u.startswith("k") else (v / 16 if u.startswith("o") else v)


def dims_in(d):
    m = re.findall(r"([\d.]+)\s*\"?\s*[DWHL]?", d or "")
    v = [float(x) for x in m[:3] if x.replace(".", "").isdigit()]
    return v if len(v) == 3 else None


def candidates(det):
    out = []
    for a, x in det.items():
        if not x.get("ok") or not re.match(r"B0[GH]", a):
            continue
        n = bought_n(x.get("bought"))
        lb = pounds(x.get("weight"))
        dm = dims_in(x.get("dims"))
        s3_cm = sum(dm) * 2.54 if dm else None
        big = (lb or 0) >= 30 or (s3_cm or 0) >= 140
        out.append(dict(x, units=n, lb=lb, s3_cm=s3_cm, big=big, electric=bool(ELECTRIC.search(x.get("title") or "")),
                        yen=round((x["usd"] or 0) * 150, -2)))
    return out
