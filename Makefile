.PHONY: setup run run-test clean

# 仮想環境のセットアップとパッケージインストール
setup:
	python -m venv .venv
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install -r requirements.txt -r price_comparison/requirements.txt

# 価格比較ツールを全件実行
run:
	cd price_comparison && python -m src.main

# 価格比較ツールをテスト実行（20件のみ）
run-test:
	cd price_comparison && python -m src.main --limit 20

# 価格比較ツールをローカルCSVのみで実行（OneDriveスキップ）
run-local:
	cd price_comparison && python -m src.main --skip-fetch

# 生成ファイルを削除
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	rm -f price_comparison/data/output/profitable_2*.csv
	rm -f price_comparison/data/output/profitable_2*.json
