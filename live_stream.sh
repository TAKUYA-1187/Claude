#!/usr/bin/env bash
#
# 24時間ライブ配信
#
# 用意した動画をループしながら YouTube へ流し続けます。
# 「Soothing Relaxation」などが ライブ バッジを付けているのと同じ形式です。
#
#   bash live_stream.sh <ストリームキー> [動画ファイル]
#
# 例:
#   bash live_stream.sh abcd-1234-efgh-5678-ijkl
#   bash live_stream.sh abcd-1234-efgh-5678-ijkl out/video/02_deep_sleep_ambient.mp4
#
# ストリームキーの取得場所:
#   YouTube Studio → 右上［作成］→「ライブ配信を開始」
#   → 左メニュー「ストリーム」→「ストリームキー」の［コピー］
#
# ※ 初めてライブ配信する場合、有効化に 24 時間かかります。
#    先に「ライブ配信を開始」を一度押しておいてください。

set -u
cd "$(dirname "$0")"

KEY="${1:-}"
SRC="${2:-out/video/02_deep_sleep_ambient.mp4}"

if [ -z "$KEY" ]; then
  echo "使い方: bash live_stream.sh <ストリームキー> [動画ファイル]"
  echo ""
  echo "ストリームキーは YouTube Studio →［作成］→「ライブ配信を開始」"
  echo "→ 左メニュー「ストリーム」→「ストリームキー」からコピーできます。"
  exit 1
fi
if [ ! -f "$SRC" ]; then
  echo "動画が見つかりません: $SRC"
  echo "先に bash run_all.sh を実行してください。"
  exit 1
fi

FFMPEG=$(python3 -c "import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())" 2>/dev/null)
[ -z "$FFMPEG" ] && FFMPEG=$(command -v ffmpeg)
if [ -z "$FFMPEG" ]; then
  echo "ffmpeg が見つかりません。python3 -m pip install imageio-ffmpeg を実行してください。"
  exit 1
fi

URL="rtmp://a.rtmp.youtube.com/live2/${KEY}"

echo "════════════════════════════════════════════"
echo " 24時間ライブ配信を開始します"
echo "════════════════════════════════════════════"
echo " 配信する動画 : $SRC"
echo " 配信先       : rtmp://a.rtmp.youtube.com/live2/****"
echo ""
echo " 止めるとき   : Control + C"
echo " ※ Mac をスリープさせないでください"
echo "    (システム設定 → ロック画面 → 自動でスリープ → しない)"
echo ""

# 落ちても自動で入り直す。
# 一晩で切れて配信が終わっていた、という事故を避けるため。
ATTEMPT=0
while true; do
  ATTEMPT=$((ATTEMPT + 1))
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] 接続 #$ATTEMPT"

  # -re         : 実時間で読む (ライブ配信では必須)
  # -stream_loop: 動画を無限に繰り返す
  # -c copy     : 再エンコードしない。CPU をほぼ使わないので24時間回せる
  # -g          : YouTube 推奨のキーフレーム間隔に合わせる
  "$FFMPEG" -hide_banner -loglevel warning \
    -re -stream_loop -1 -i "$SRC" \
    -c:v copy -c:a aac -b:a 192k -ar 44100 \
    -f flv "$URL"

  echo "[$(date '+%Y-%m-%d %H:%M:%S')] 切断されました。10秒後に再接続します。"
  sleep 10
done
