# -*- coding: utf-8 -*-
"""Subsets Noto Sans JP to the glyphs this manual uses and embeds them as base64
woff2, so the PDF and the web page render identically with no network access."""
import base64, io, os, re, sys
from fontTools import subset
from fontTools.ttLib import TTFont

SRC = "/tmp/claude-0/-home-user-Claude/6821d426-0d4e-5310-96ef-4b7a02294d6e/scratchpad"
WEIGHTS = [400, 500, 700, 900]


def used_chars(html_path):
    html = open(html_path, encoding="utf-8").read()
    html = re.sub(r"<style.*?</style>", " ", html, flags=re.S)
    html = re.sub(r"<script.*?</script>", " ", html, flags=re.S)
    # everything that survives - element text AND attribute text (the running
    # header and folio are delivered through data-* attributes)
    chars = set(html)
    # keep the full kana blocks + punctuation so small text edits never break
    for a, b in ((0x20, 0x7E), (0x3000, 0x303F), (0x3041, 0x309F), (0x30A0, 0x30FF),
                 (0xFF01, 0xFF60), (0xFFE0, 0xFFE6)):
        chars |= {chr(c) for c in range(a, b + 1)}
    chars |= set("\u00d7\u00f7\u00b1\u2192\u2190\u2191\u2193\u301c\u203b\u2103\u2026"
                 "\u2713\u2714\u25a0\u25a1\u25cf\u25cb\u25c6\u25c7"
                 "\u25b2\u25b3\u25bc\u25bd\u26a0\uff01\uff1f")
    return {c for c in chars if c not in "\n\r\t"}


def build(html_path, out_css):
    chars = used_chars(html_path)
    faces, total = [], 0
    for w in WEIGHTS:
        src = os.path.join(SRC, f"nsjp-{w}.ttf")
        opts = subset.Options()
        opts.flavor = "woff2"
        opts.desubroutinize = True
        opts.layout_features = ["kern", "palt", "liga", "vert", "vrt2", "ccmp", "locl"]
        opts.name_IDs = ["*"]
        opts.notdef_outline = True
        font = subset.load_font(src, opts)
        subsetter = subset.Subsetter(options=opts)
        subsetter.populate(text="".join(sorted(chars)))
        subsetter.subset(font)
        buf = io.BytesIO()
        subset.save_font(font, buf, opts)
        data = buf.getvalue()
        total += len(data)
        b64 = base64.b64encode(data).decode()
        faces.append("@font-face{font-family:'Noto Sans JP';font-style:normal;"
                     f"font-weight:{w};font-display:block;"
                     f"src:url(data:font/woff2;base64,{b64}) format('woff2');}}")
        print(f"  weight {w}: {len(data)//1024} KB")
    open(out_css, "w", encoding="utf-8").write("\n".join(faces))
    print(f"wrote {out_css} — {total//1024} KB of font data, {len(chars)} glyphs")


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else "bed-table-manual.html", "fonts.css")
