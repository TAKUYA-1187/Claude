#!/bin/bash
# ローカルPC用セットアップ（Mac / Linux）
# Amazon購入者メッセージ自動送信 毎日15:00 JST実行

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="${PYTHON_BIN:-$(which python3)}"

echo "=============================="
echo "依存ライブラリをインストール中..."
"$PYTHON_BIN" -m pip install playwright --quiet
"$PYTHON_BIN" -m playwright install chromium
echo "インストール完了"
echo ""

# Macの場合: launchd (推奨)
if [[ "$(uname)" == "Darwin" ]]; then
    PLIST_PATH="$HOME/Library/LaunchAgents/com.amazon.buyer.message.plist"
    cat > "$PLIST_PATH" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
    "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.amazon.buyer.message</string>
    <key>ProgramArguments</key>
    <array>
        <string>$PYTHON_BIN</string>
        <string>$SCRIPT_DIR/amazon_buyer_message_browser.py</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>15</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>$SCRIPT_DIR/cron.log</string>
    <key>StandardErrorPath</key>
    <string>$SCRIPT_DIR/cron.log</string>
    <key>RunAtLoad</key>
    <false/>
</dict>
</plist>
EOF
    launchctl load "$PLIST_PATH"
    echo "Mac launchd ジョブ登録完了: 毎日15:00に自動実行"
    echo "確認: launchctl list | grep amazon"
    echo "停止: launchctl unload $PLIST_PATH"

else
    # Linux: cron
    # JST環境なら "0 15 * * *", UTC環境なら "0 6 * * *"
    TZ_OFFSET=$(date +%z)
    if [[ "$TZ_OFFSET" == "+0900" ]]; then
        CRON_TIME="0 15 * * *"
    else
        CRON_TIME="0 6 * * *"
    fi
    CRON_CMD="$CRON_TIME $PYTHON_BIN $SCRIPT_DIR/amazon_buyer_message_browser.py >> $SCRIPT_DIR/cron.log 2>&1"
    (crontab -l 2>/dev/null | grep -v "amazon_buyer_message" || true; echo "$CRON_CMD") | crontab -
    echo "cronジョブ登録完了: 毎日15:00 JST に自動実行"
fi

echo ""
echo "手動テスト実行:"
echo "  $PYTHON_BIN $SCRIPT_DIR/amazon_buyer_message_browser.py"
echo "=============================="
