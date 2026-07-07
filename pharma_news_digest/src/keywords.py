"""検索キーワード定義。

担当領域（ノバルティス 腎臓領域：ファビハルタ／IgA腎症）に合わせて、
各セクションごとの Google ニュース検索クエリと論文検索クエリをまとめる。
"""

# --- 自社製品・注目領域 -------------------------------------------------
FABHALTA_TERMS = [
    "ファビハルタ",
    "Fabhalta",
    "iptacopan",
    "イプタコパン",
    "LNP023",
]

IGAN_TERMS = [
    "IgA腎症",
    "IgA nephropathy",
    "IgAN",
]

# --- 競合・腎臓パイプライン ---------------------------------------------
# IgA 腎症を中心とした腎領域の主な競合・関連品目
COMPETITOR_TERMS = [
    "フィルスパリ",      # sparsentan
    "sparsentan",
    "ネフェコン",        # budesonide (Nefecon / Tarpeyo)
    "Nefecon",
    "sibeprenlimab",     # シベプレンリマブ
    "atacicept",
    "アタシセプト",
    "ravulissran",
    "cemdisiran",
    "felzartamab",
    "C3腎症",
    "C3 glomerulopathy",
]

# --- 会社・業界一般 -----------------------------------------------------
COMPANY_TERMS = [
    "ノバルティス",
    "Novartis",
]

INDUSTRY_JP_TERMS = [
    "薬価",
    "中医協",
    "PMDA 承認",
    "厚生労働省 医薬品",
    "製薬 業界",
]

# 情報誌（RISFAX / じほう 等）の公開見出しを拾うためのクエリ
TRADE_PRESS_TERMS = [
    "RISFAX",
    "じほう 医薬",
    "ミクスOnline",
    "ミクス 製薬",
]

# --- 世界のアップデート（グローバル） -----------------------------------
GLOBAL_TERMS = [
    "iptacopan",
    "Fabhalta",
    "IgA nephropathy",
    "complement inhibitor kidney",
    "FDA nephrology approval",
    "EMA nephrology",
]

# --- 論文検索（PubMed / Europe PMC） ------------------------------------
# 各要素が 1 本のクエリになる。過去 N 日の新着のみ抽出する。
LITERATURE_QUERIES = [
    "iptacopan",
    "IgA nephropathy",
    "C3 glomerulopathy",
    "complement factor B inhibitor",
    "paroxysmal nocturnal hemoglobinuria iptacopan",
]
