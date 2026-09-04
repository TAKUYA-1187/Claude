#!/usr/bin/env bash
# スキル本体を .skill（zip）に固める。チャット側や他の環境へインストールするとき用。
#
#   bash smart_tax_return/tools/build_skill.sh
#
# .claude/skills/smart-tax-return/ を編集したら、これを実行して dist/ を更新すること。
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SRC="$ROOT/.claude/skills/smart-tax-return"
OUT="$ROOT/smart_tax_return/dist/smart-tax-return.skill"

[ -f "$SRC/SKILL.md" ] || { echo "スキル本体が見つからない: $SRC" >&2; exit 1; }

mkdir -p "$(dirname "$OUT")"
rm -f "$OUT"
cd "$(dirname "$SRC")"
zip -r -q -X "$OUT" "$(basename "$SRC")" -x '*.DS_Store' '*__pycache__*'

echo "built: ${OUT#"$ROOT"/}"
unzip -l "$OUT" | tail -n 1
