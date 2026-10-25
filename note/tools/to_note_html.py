"""note 投稿用の原稿（Markdown）を、Google ドキュメントに取り込む HTML に変換する。

    python note/tools/to_note_html.py note/launch/02_free_kaitori_cash.md > out.html

- 「## 本文」より前（投稿設定など）は、オーナー向けのメモとして灰色の枠に入れる
- note のエディタには表がないので、本文の表は箇条書きに直す
- 見出し（##・###）は Google ドキュメントの見出しになり、note に貼ると大見出し・小見出しになる
外部ライブラリは使わない。
"""
import html
import re
import sys

INLINE_CODE = re.compile(r"`([^`]+)`")
BOLD = re.compile(r"\*\*(.+?)\*\*")
LINK = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")


def inline(text: str) -> str:
    out = html.escape(text, quote=False)
    out = BOLD.sub(r"<b>\1</b>", out)
    out = INLINE_CODE.sub(r"\1", out)
    out = LINK.sub(r'<a href="\2">\1</a>', out)
    return out


def cells(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def table_to_list(rows: list[list[str]]) -> str:
    """表を箇条書きにする。値が1列なら「A：B」、複数列なら「A：見出し2 B／見出し3 C」。
    1列目が番号（見出しが「#」）なら「1. 項目：…」にする。"""
    header, body = rows[0], rows[1:]
    items = []
    for r in body:
        if header[0] == "#" and len(r) > 2:
            key, pairs = f"{r[0]}. {r[1]}", list(zip(header[2:], r[2:]))
        else:
            key, pairs = r[0] or header[0], list(zip(header[1:], r[1:]))
        pairs = [(h, v) for h, v in pairs if v]
        if len(pairs) == 1:
            text = f"{key}：{pairs[0][1]}" if key else pairs[0][1]
        else:
            text = f"{key}：" + "／".join(f"{h} {v}" if h else v for h, v in pairs)
        items.append(f"<li>{inline(text)}</li>")
    return "<ul>" + "".join(items) + "</ul>"


def convert(md: str) -> str:
    lines = md.splitlines()
    out, para, i = [], [], 0

    def flush():
        if para:
            out.append("<p>" + "<br>".join(inline(p) for p in para) + "</p>")
            para.clear()

    while i < len(lines):
        line = lines[i]
        s = line.strip()
        if s.startswith("|") and i + 1 < len(lines) and re.match(r"^\|\s*:?-{3}", lines[i + 1].strip()):
            flush()
            rows = [cells(line)]
            i += 2
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append(cells(lines[i]))
                i += 1
            out.append(table_to_list(rows))
            continue
        if not s or s == "---":
            flush()
        elif s.startswith("```"):
            flush()
            i += 1
            block = []
            while i < len(lines) and not lines[i].strip().startswith("```"):
                block.append(html.escape(lines[i]))
                i += 1
            out.append("<p>" + "<br>".join(block) + "</p>")
        elif m := re.match(r"^(#{1,3}) (.*)", s):
            flush()
            level = len(m.group(1))
            out.append(f"<h{level}>{inline(m.group(2))}</h{level}>")
        elif re.match(r"^[-*] ", s):
            flush()
            items = []
            while i < len(lines) and re.match(r"^\s*[-*] ", lines[i]):
                items.append("<li>" + inline(re.sub(r"^\s*[-*] ", "", lines[i])) + "</li>")
                i += 1
            out.append("<ul>" + "".join(items) + "</ul>")
            continue
        elif re.match(r"^\d+\. ", s):
            flush()
            items = []
            while i < len(lines) and re.match(r"^\s*\d+\. ", lines[i]):
                items.append("<li>" + inline(re.sub(r"^\s*\d+\. ", "", lines[i])) + "</li>")
                i += 1
            out.append("<ol>" + "".join(items) + "</ol>")
            continue
        else:
            para.append(s)
        i += 1
    flush()
    return "\n".join(out)


def main(path: str) -> None:
    md = open(path, encoding="utf-8").read()
    head, sep, body = md.partition("\n## 本文\n")
    if not sep:
        head, body = "", md
    parts = ["<html><body>"]
    if head:
        parts.append('<p style="color:#5b636e">▼ オーナー向けメモ（note には貼らない）</p>')
        parts.append(convert(head))
        parts.append('<p style="color:#0f6b52"><b>▼ ここから下を note にコピーして貼る</b></p>')
    parts.append(convert(body))
    parts.append("</body></html>")
    sys.stdout.write("\n".join(parts))


if __name__ == "__main__":
    main(sys.argv[1])
