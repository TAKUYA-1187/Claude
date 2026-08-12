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
echo " 所要時間 : 3〜5 時間 (放置して構いません)"
echo " 必要な空き: 25GB 以上"
echo ""
df -h . | tail -1
echo ""

echo "▶ [1/5] 必要なライブラリを確認しています..."
"$PY" -m pip install --quiet --upgrade numpy pillow imageio-ffmpeg || {
  echo "ライブラリのインストールに失敗しました。"; exit 1; }
echo "   OK"
echo ""

echo "▶ [2/5] 2時間24分の動画を 25 本作ります (いちばん時間がかかります)"
"$PY" render_bgm.py --tracks \
  01_lofi_rainy_study 02_deep_sleep_ambient 03_piano_and_rain \
  04_cozy_coffee_jazz 05_bossa_nova_cafe 06_healing_meditation_432 \
  07_fireplace_winter_jazz 08_ocean_waves_ambient 09_fantasy_tavern \
  10_deep_focus_flow 12_anime_piano_emotional 13_fresh_morning_acoustic \
  14_japanese_lofi_koto 15_rain_thunder_night 16_autumn_cafe_jazz \
  17_christmas_jazz 18_starship_sleep 19_528hz_love_frequency \
  20_focus_40hz 21_halloween_night 22_snowstorm_fireplace \
  23_forest_night_camp 24_deep_space_drone 25_cyberpunk_rain \
  26_dark_academia_library \
  || { echo "エラーで止まりました。"; exit 1; }
echo ""

echo "▶ [3/5] 長時間版を 2 本作ります (8時間の睡眠BGMと10時間の黒画面雨)"
"$PY" render_bgm.py --tracks 11_sleep_city_8h --repeats 20 \
  || { echo "エラーで止まりました。"; exit 1; }
"$PY" render_bgm.py --tracks 27_rain_black_screen --repeats 25 \
  || { echo "エラーで止まりました。"; exit 1; }
echo ""

echo "▶ [4/5] Shorts を作ります (登録者を集めるための縦動画)"
"$PY" make_shorts.py --per-track 2 || { echo "エラーで止まりました。"; exit 1; }
echo ""

echo "▶ [5/5] 品質検査をしています (ノイズ・音量・ループ・映像を全数チェック)..."
"$PY" qa_check.py || {
  echo ""
  echo "⚠ 品質検査で指摘が出ました。この状態ではアップロードしないでください。"
  echo "  out/qa.json に詳細があります。"
  exit 1
}
echo ""
"$PY" verify_output.py
echo ""

echo "════════════════════════════════════════════"
echo " 完成しました (全数検査に合格しています)"
echo "════════════════════════════════════════════"
echo ""
echo " アップロードする動画 : $(pwd)/out/video/"
echo " Shorts               : $(pwd)/out/shorts/"
echo " サムネイル           : $(pwd)/out/thumbnail/"
echo " タイトル・説明文     : out/metadata/ (動画ごとの .json)"
echo ""
echo " Finder で開く:"
echo "   open out/video"
echo ""
