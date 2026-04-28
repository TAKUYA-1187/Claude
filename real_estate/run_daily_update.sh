#!/bin/bash
# 毎日11時に実行する不動産投資物件リサーチ更新スクリプト
# 設定方法: crontab -e で以下を追加
# 0 11 * * * /home/user/Claude/real_estate/run_daily_update.sh

cd /home/user/Claude/real_estate
DATE=$(date +%Y%m%d)
LOG_FILE="daily_log_${DATE}.txt"

echo "=== 物件リサーチ更新開始: $(date) ===" >> "$LOG_FILE"
python3 property_search.py >> "$LOG_FILE" 2>&1
echo "=== 更新完了: $(date) ===" >> "$LOG_FILE"

echo "レポートを生成しました: report_${DATE}.md"
