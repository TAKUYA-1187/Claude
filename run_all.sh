#!/usr/bin/env bash
#
# 動画をぜんぶ作る。これ 1 本流せば終わり。
#
#   bash run_all.sh
#
# 途中で止まっても、もう一度同じコマンドを流せば続きから作り直せる
# (シードが固定されているので、何度実行しても同じものができる)。

set -u
cd "$(dirname "$0")"

PY=$(command -v python3 || command -v python)
if [ -z "$PY" ]; then
  echo "Python が見つかりません。https://www.python.org/downloads/ からインストールしてください。"
  exit 1
fi

echo "════════════════════════════════════════════"
echo " BGM Studio — 動画をまとめて生成します"
echo "════════════════════════════════════════════"
echo " 所要時間 : 2〜4 時間 (放置して構いません)"
echo " 必要な空き: 20GB 以上"
echo ""
df -h . | tail -1
echo ""

echo "▶ [1/4] 必要なライブラリを確認しています..."
"$PY" -m pip install --quiet --upgrade numpy pillow imageio-ffmpeg || {
  echo "ライブラリのインストールに失敗しました。"; exit 1; }
echo "   OK"
echo ""

echo "▶ [2/4] 2時間24分の動画を 10 本作ります (いちばん時間がかかります)"
"$PY" render_bgm.py --tracks \
  01_lofi_rainy_study 02_deep_sleep_ambient 03_piano_and_rain \
  04_cozy_coffee_jazz 05_bossa_nova_cafe 06_healing_meditation_432 \
  07_fireplace_winter_jazz 08_ocean_waves_ambient 09_fantasy_tavern \
  10_deep_focus_flow || { echo "エラーで止まりました。"; exit 1; }
echo ""

echo "▶ [3/4] 8時間版の睡眠BGMを 1 本作ります"
"$PY" render_bgm.py --tracks 11_sleep_city_8h --repeats 20 \
  || { echo "エラーで止まりました。"; exit 1; }
echo ""

echo "▶ [4/4] Shorts を作ります (登録者を集めるための縦動画)"
"$PY" make_shorts.py --per-track 2 || { echo "エラーで止まりました。"; exit 1; }
echo ""

echo "▶ 検証しています..."
"$PY" verify_output.py
echo ""

echo "════════════════════════════════════════════"
echo " 完成しました"
echo "════════════════════════════════════════════"
echo ""
echo " アップロードする動画 : $(pwd)/out/video/"
echo " Shorts               : $(pwd)/out/shorts/"
echo " サムネイル           : $(pwd)/out/thumbnail/"
echo " タイトル・説明文     : docs/06_channel_setup_pack.md"
echo ""
echo " Finder で開く:"
echo "   open out/video"
echo ""
