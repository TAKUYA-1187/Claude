#!/bin/bash
# Amazon購入者メッセージ自動送信 - cronジョブセットアップ
# 毎日 15:00 JST (= 06:00 UTC) に実行

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="${PYTHON_BIN:-$(which python3)}"
LOG_FILE="$SCRIPT_DIR/cron.log"

if [[ ! -f "$PYTHON_BIN" ]]; then
    echo "Error: python3 が見つかりません。PYTHON_BIN=/path/to/python3 を指定してください。"
    exit 1
fi

# 依存ライブラリのインストール
echo "依存ライブラリをインストール中..."
"$PYTHON_BIN" -m pip install -r "$SCRIPT_DIR/requirements.txt" --quiet

# 設定ファイルの確認
if [[ ! -f "$SCRIPT_DIR/config.json" ]]; then
    echo ""
    echo "警告: config.json が見つかりません。"
    echo "  cp $SCRIPT_DIR/config.json.template $SCRIPT_DIR/config.json"
    echo "  上記コマンドで作成し、認証情報を入力してください。"
    echo ""
fi

# JST判定 (UTC+9の場合は06:00 UTC、JSTの場合は15:00)
TZ_OFFSET=$(date +%z)
if [[ "$TZ_OFFSET" == "+0900" ]]; then
    CRON_TIME="0 15 * * *"
    TZ_NOTE="JST (日本時間) 15:00"
else
    CRON_TIME="0 6 * * *"
    TZ_NOTE="UTC 06:00 (= JST 15:00)"
fi

CRON_CMD="$CRON_TIME $PYTHON_BIN $SCRIPT_DIR/amazon_buyer_message.py >> $LOG_FILE 2>&1"

# 既存エントリを削除して追加
(crontab -l 2>/dev/null | grep -v "amazon_buyer_message.py" || true; echo "$CRON_CMD") | crontab -

echo "=============================="
echo "cronジョブ登録完了"
echo "  実行時刻: 毎日 $TZ_NOTE"
echo "  スクリプト: $SCRIPT_DIR/amazon_buyer_message.py"
echo "  ログ: $LOG_FILE"
echo ""
echo "現在のcrontab:"
crontab -l
echo "=============================="
echo ""
echo "動作確認 (手動実行):"
echo "  $PYTHON_BIN $SCRIPT_DIR/amazon_buyer_message.py"
