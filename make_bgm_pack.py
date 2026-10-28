"""
長時間 BGM・Sleep Piano の投稿パック (out/BGM_投稿パック_v2.md) を作る。

英語のタイトル・説明・タグは out/metadata/*.json から取り、
日本語・中国語・韓国語・スペイン語のタイトルと説明を「翻訳」用に添える (計 5 言語)。

    python3 make_bgm_pack.py
"""

from __future__ import annotations

import json
from pathlib import Path

OUT = Path(__file__).resolve().parent / "out"

# slug: (公開日時, 再生リスト, 種類, (日本語名, 中国語名, 韓国語名, スペイン語名))
PLAN = {
    "g01_gentle_piano_sleep": ("10月30日(金) 12:00", "Gentle Piano for Sleep", "sleep",
                               ("睡眠ピアノ", "睡眠钢琴", "수면 피아노", "Piano para dormir")),
    "07_fireplace_winter_jazz": ("11月1日(日) 12:00", "Cozy & Seasonal", "jazz",
                                 ("暖炉のジャズ", "壁炉爵士乐", "벽난로 재즈", "Jazz junto a la chimenea")),
    "05_bossa_nova_cafe": ("11月4日(水) 12:00", "Cozy Jazz & Café", "jazz",
                           ("ボサノヴァ・カフェ", "波萨诺瓦咖啡馆", "보사노바 카페", "Café bossa nova")),
    "g02_deep_sleep_piano": ("11月7日(土) 12:00", "Gentle Piano for Sleep", "sleep",
                             ("深い眠りのピアノ", "深度睡眠钢琴", "깊은 잠을 위한 피아노", "Piano para un sueño profundo")),
    "04_cozy_coffee_jazz": ("11月11日(水) 12:00", "Cozy Jazz & Café", "jazz",
                            ("コーヒーショップのジャズ", "咖啡馆爵士乐", "커피숍 재즈", "Jazz de cafetería")),
    "17_christmas_jazz": ("11月14日(土) 12:00", "Cozy & Seasonal", "jazz",
                          ("クリスマス・ジャズ", "圣诞爵士乐", "크리스마스 재즈", "Jazz navideño")),
    "g03_emotional_sleep_piano": ("11月19日(木) 12:00", "Gentle Piano for Sleep", "sleep",
                                  ("心に残る睡眠ピアノ", "唯美睡眠钢琴", "감성 수면 피아노", "Piano emotivo para dormir")),
}


def translations(kind: str, names: tuple[str, str, str, str], hours: int) -> list[tuple[str, str, str]]:
    ja, zh, ko, es = names
    if kind == "sleep":
        return [
            ("日本語", f"{ja} 🌙 {hours}時間｜雨音なし・雑音なしのやさしいピアノ",
             f"雨音も環境音も入れていない、やさしいピアノだけの睡眠用音楽です（{hours}時間）。\n"
             "ゆっくりした同じテンポのまま、急な変化はありません。寝る前やお休みのあいだにどうぞ。\n"
             "作曲・編曲・映像はこのチャンネルのオリジナルです。"),
            ("中国語（簡体字）", f"{zh} 🌙 {hours}小时｜无雨声、无杂音的柔和钢琴",
             f"没有雨声和环境音，只有柔和钢琴的睡眠音乐（{hours}小时）。\n"
             "节奏缓慢且始终如一，没有突然的变化。适合入睡前和整夜播放。\n"
             "作曲、编曲和画面均为本频道原创。"),
            ("韓国語", f"{ko} 🌙 {hours}시간｜빗소리·잡음 없는 부드러운 피아노",
             f"빗소리도 환경음도 없는, 부드러운 피아노만으로 만든 수면 음악입니다 ({hours}시간).\n"
             "느린 템포가 처음부터 끝까지 같으며 갑작스러운 변화가 없습니다.\n"
             "작곡·편곡·영상은 이 채널의 오리지널입니다."),
            ("スペイン語", f"{es} 🌙 {hours} horas | Sin lluvia, sin ruido, solo piano",
             f"{hours} horas de música para dormir, solo con un piano suave: sin lluvia y sin sonidos de fondo.\n"
             "El tempo es lento y constante, sin cambios repentinos.\n"
             "Composición, arreglo y animación originales de este canal."),
        ]
    return [
        ("日本語", f"{ja} ☕ {hours}時間｜作業・勉強・リラックス用BGM",
         f"{ja}の{hours}時間BGMです。作業や勉強、くつろぎの時間に流しっぱなしにできます。\n"
         "環境音は音楽の後ろにごく小さく入れているだけです。作曲・編曲・映像はこのチャンネルのオリジナルです。"),
        ("中国語（簡体字）", f"{zh} ☕ {hours}小时｜工作・学习・放松背景音乐",
         f"{zh}，{hours}小时背景音乐。适合工作、学习和放松时一直播放。\n"
         "环境音只在音乐后面轻轻铺垫。作曲、编曲和画面均为本频道原创。"),
        ("韓国語", f"{ko} ☕ {hours}시간｜작업·공부·휴식용 BGM",
         f"{ko} {hours}시간 BGM입니다. 작업, 공부, 휴식 시간에 틀어 두기 좋습니다.\n"
         "환경음은 음악 뒤에 아주 작게만 깔았습니다. 작곡·편곡·영상은 이 채널의 오리지널입니다."),
        ("スペイン語", f"{es} ☕ {hours} horas | Música para trabajar, estudiar y relajarse",
         f"{hours} horas de {es.lower()} para trabajar, estudiar o descansar.\n"
         "Los sonidos de ambiente quedan muy por detrás de la música. Composición, arreglo y animación originales."),
    ]


def main() -> int:
    L = [
        "# 長時間BGM・Sleep Piano 投稿パック v2（5言語）",
        "",
        "## 毎回の手順",
        "",
        "1. YouTube Studio 右上の［作成］→［動画をアップロード］で、zip の中の `.mp4` をドラッグする",
        "2. タイトル・説明・タグ：下の【英語】の欄を貼り付ける。サムネイル：同じ zip の `.png`",
        "3. 再生リスト：下に書いた名前のもの（無ければ［新しい再生リスト］で作る）",
        "4. 視聴者：**［いいえ、子ども向けではありません］**",
        "5. ［すべて表示］→ AI の使用：**はい**／動画の言語：英語／カテゴリ：音楽",
        "6. 動画の要素：［終了画面］→［追加］→「1本の動画、1つの登録要素」を選んで保存（2本目以降）",
        "7. 公開設定：［スケジュールを設定］→ 下の公開日時（または「非公開」で保存して試聴してから公開）",
        "8. **翻訳を追加する**：左メニュー［言語］→ その動画 →［言語を追加］で、日本語・中国語（簡体字）・",
        "   韓国語・スペイン語を順に追加し、下の各言語のタイトルと説明を貼る（英語と合わせて5言語）",
        "9. **動画どうしをつなぐ**：その再生リストの URL を、英語の説明の最後に `▶ More: （URL）` として足す",
        "",
        "> チャプターは付けません（つけっぱなしで聞く動画なので、区切りを見せない方が長く再生されます）。",
        "",
        "## 公開スケジュール", "", "| 公開日時 | 動画 | 再生リスト |", "|---|---|---|",
    ]
    metas = {}
    for slug, (when, pl, _k, _n) in PLAN.items():
        p = OUT / "metadata" / f"{slug}.json"
        if not p.exists():
            continue
        metas[slug] = json.loads(p.read_text(encoding="utf-8"))
        L.append(f"| {when} | {metas[slug]['title']} | {pl} |")
    L += ["", "---", ""]
    for slug, meta in metas.items():
        when, pl, kind, names = PLAN[slug]
        assert not meta["made_for_kids"], slug
        hours = int(meta["specs"]["total_seconds"] // 3600)
        L += [f"## {when} — {names[0]}", "",
              f"- zip：`{slug}.zip`", f"- 再生リスト：**{pl}**",
              f"- 長さ：{meta['specs']['total_hhmmss']}", "",
              "【英語タイトル】", "```", meta["title"], "```", "",
              "【英語の説明】", "```", meta["description"].rstrip(), "```", "",
              "【タグ】", "```", ", ".join(meta["tags"]), "```", ""]
        for lang, t, d in translations(kind, names, hours):
            assert len(t) <= 100, t
            L += [f"【{lang}タイトル】（翻訳用）", "```", t, "```", "",
                  f"【{lang}の説明】（翻訳用）", "```", d, "```", ""]
        L += ["---", ""]
    path = OUT / "BGM_投稿パック_v2.md"
    path.write_text("\n".join(L), encoding="utf-8")
    print(path, len(metas), "本")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
