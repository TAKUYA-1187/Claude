#!/usr/bin/env python3
"""毎日15:00 JSTの自動実行をMac launchdに登録する。"""

import os
import subprocess
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
PYTHON_BIN = subprocess.check_output(["which", "python3"]).decode().strip()
PLIST_PATH = Path.home() / "Library/LaunchAgents/com.amazon.buyer.message.plist"

plist = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
    "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.amazon.buyer.message</string>
    <key>ProgramArguments</key>
    <array>
        <string>{PYTHON_BIN}</string>
        <string>{SCRIPT_DIR}/amazon_buyer_message_browser.py</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>15</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>{SCRIPT_DIR}/amazon_message.log</string>
    <key>StandardErrorPath</key>
    <string>{SCRIPT_DIR}/amazon_message.log</string>
</dict>
</plist>"""

# 既存ジョブを解除してから再登録
subprocess.run(["launchctl", "unload", str(PLIST_PATH)], capture_output=True)
PLIST_PATH.write_text(plist)
subprocess.run(["launchctl", "load", str(PLIST_PATH)], check=True)

print("=== launchd 登録完了 ===")
print(f"Python  : {PYTHON_BIN}")
print(f"スクリプト: {SCRIPT_DIR}/amazon_buyer_message_browser.py")
print(f"実行時刻: 毎日 15:00")
print(f"ログ    : {SCRIPT_DIR}/amazon_message.log")
print("")
result = subprocess.run(["launchctl", "list", "com.amazon.buyer.message"],
                        capture_output=True, text=True)
print("登録状態:", result.stdout.strip() or "登録済み（次回15:00に実行）")
