# -*- coding: utf-8 -*-
"""v5 content (2026-10-27 data): finalists with links, verified rejections, type verdicts,
summary texts. Re-uses the v4 texts where the product and the evidence did not change."""
import data_v4 as V4

AL = "https://www.alibaba.com/trade/search?SearchText="

SUMMARY_SUB = ("2026-10-27 取得：Amazon.co.jp 352キーワード（v4の231語＋新規121語）、¥1万以上・月50個以上の1,249商品／"
               "1688 市場ページ 352語＋60タイプ＋最終候補の仕様別検索＋2026新款62語（各出品の商品ページURL付き）／"
               "米国Amazon New Releases 401カテゴリ（$70以上 約2,500品）。料金は天瞳 送料・保管料一覧表（2024.1.6版）。")

SUMMARY = [
    "1. 調査範囲を広げました：Amazon.co.jpは352キーワード（屋外・ガーデン、ホームジム、キッズ、ペット、DIY・車、業務用、趣味、介護を追加）で、"
    "¥1万以上・月50個以上の1,249商品（うち月100個以上600商品）を02シートに全件掲載。各行にAmazon商品ページ・1688参考出品・Alibaba検索のリンクがあります。",
    "2. 1688の仕様一致品で原価を確かめると、売れている大型品の多くは価格差2〜2.5倍しかなく、天瞳の国内送料と海上運賃で利益が消えます"
    "（テントサウナ、ファイヤーピットテーブル、ピザ窯、コールドプランジ、電動乗馬マシン、コレクションケース、ガーデンブランコ、ガレージテント、ジャッキ、ダンベル、マットレス）。",
    "3. 採用9品：HERO＝オフィスチェア、主力＝折りたたみベビーベッド・スピンバイク・ドレッサー（160サイズ設計）・ペットカート（新規）、"
    "新商品＝ピラティスリフォーマー（米国発・日本は¥10万の1品のみ）、条件付き＝食器棚（3個口）・懸垂マシン・大型ゴルフネット（市場の裏付けが薄い）。"
    "各R0xシートと『10_利益商品リンク集』にAmazon・1688・Alibabaのリンクを記載しました。",
    "4. 『需要はあるがAmazonの価格が高くて売れていない市場』（07シート）：乗馬マシン（中央値¥118,800・月販ほぼ0）、ピザ窯（¥42,000）、ルーフテント（¥150,000）、"
    "卓球台、ビリヤード台、ガゼボ、オーニング等を検証。1688の同等品も高く（電動乗馬は1,450元、ルーフテントは3,500元前後）、安くしても天瞳料金で利益が残るものは見つかりませんでした。"
    "価格を下げて市場を開ける余地があるのは大型ゴルフネット（¥29,800で天瞳表38%）のみです。",
    "5. 米国Amazonの2026年新着（08シート）：Boneless/Cloud型モジュールソファ、木製ピラティスリフォーマー、TCGカード用の大型施錠ディスプレイケース、木製ベビーサークル等は"
    "日本のAmazonに翻訳ページはあるが『在庫切れ・再入荷予定なし』で実質未発売。最有力はピラティスリフォーマー：日本は¥100,680の1品（月販バッジ無し）しかなく、"
    "1688の折りたたみ品700元から¥49,800で出せば天瞳表32%・実質26%（R09）。次点はTCG用の大型施錠ディスプレイケース（トレカ人気・利益は薄め）。",
    "6. 中国Amazon（amazon.cn）は2024年1月27日でPCの販売を終了しアプリの海外購入のみのため、中国の新商品は1688の『2026新款』で代替しました（09シート）。"
    "渓流水槽（侧滤溪流缸）、ドレッサー＋ナイトテーブル一体型、スチール引き戸ワードローブ、雲形ソファベッドが中国で月20〜350件売れています。",
    "7. 9品を各市場の1位ライン近く（チェア月500個、その他月100〜250個）まで育て、楽天・Yahoo!を加えると3年目に総年商約7.5億円・営業利益（固定費前）約1.5億円の計画（06シート）。"
    "全品が計画通りに伸びる前提のため、1年目はチェア・ペットカート・ドレッサーに集中し、Keepaで月販を確認しながら残りを投入します。",
    "8. 未確定：1688は少量の掲載価格（50個以上で1〜2割下がる余地）。梱包は推定（青字）。日本のAmazonは今回アクセス制限が厳しく、商品ページは最終候補のライバルのみ取得しました。",
]

TODO = [
    "① HERO（チェア）・ペットカート・ドレッサーの1688見積（各3社）とサンプル。梱包を実測し01シートの黄色セルを差し替え",
    "② 米国新商品のピラティスリフォーマーとTCGディスプレイケースは、1688で同等品のサンプルを取り、日本での検索需要（Googleキーワードプランナー等）を確認",
    "③ ベビーベッドはPSC（登録検査機関）の試験を依頼",
    "④ Keepaで上位品の30/60/90日ランキングを確認（ゴルフネットは月500個のバッジが本当か要確認）",
    "⑤ 商標出願・JAN・PL保険。初回は2〜20m³（17,325円/m³）、2年目から20m³以上（13,125円/m³）",
]

ROADMAP_NOTES = [
    "・年商5億円は1商品では届かない。HEROのチェアを月500個、ベビーベッド・ドレッサー・懸垂マシン・ペットカート・ピラティスリフォーマーを月150〜250個、"
    "スピンバイク・食器棚・ゴルフネットを月100〜150個まで育て、楽天・Yahoo!（Amazonの25%）を加えて3年目に到達させる計画。",
    "・月販目標は各市場の1位の購入バッジ（下限値）以下。ベビーベッドのカトージは今回バッジが消えており（在庫切れの可能性）、アップリカの月200個を上限にしています。",
    "・年収5,000万円（役員報酬）の原資は総年利から固定費・法人税等を引いた残り。総年利1億円前後が必要。",
    "・1年目は広告10%・導入価格期間があるため利益が薄い（1個利益（広告10%）で試算）。",
]

_by = {f["id"]: f for f in V4.FINALISTS}


def _upd(fid, **kw):
    f = dict(_by[fid])
    f.update(kw)
    return f


FINALISTS = [
    _upd("F01", y=(150, 350, 500), top_units=800, en="ergonomic office chair headrest 4D armrest",
         rivals=["B0DQY63XXP", "B0GSQW89GZ"], rival_cny=[400, 300]),
    _upd("F02", y=(60, 120, 180), top_units=200, en="foldable baby crib playard",
         rivals=["B0GVQQFB1Q", "B0CKBF6PYH"], rival_cny=[420, 340],
         memo="アップリカ ココネル（¥36,667・月200個）が上位。カトージ（前回月700個）は今回バッジ無し（在庫切れの可能性）。PSC検査費は別途固定費。原価は1688の折りたたみ婴儿床 360元。"),
    _upd("F03", y=(50, 80, 100), top_units=100, en="magnetic spin bike FTMS"),
    _upd("F04", y=(100, 180, 250), top_units=200, en="vanity dresser with LED mirror",
         rivals=["B0CRRB9DY4", "B0D25T97DS"], rival_cny=[200, 230]),
    _upd("F05", y=(40, 80, 100), top_units=100, en="kitchen pantry cabinet sliding shelf",
         rivals=["B0F1T4QMVT", "B0F7XMW9ZF"], rival_cny=[330, 280]),
    _upd("F06", y=(80, 150, 200), top_units=300, en="power tower pull up station foldable",
         rivals=["B09K3QQBKH", "B0FT7RDYXL"], rival_cny=[220, 180], price=18980,
         memo="STEADY（¥18,990・月300個）・BARWING（¥12,800・月200個）。ONETWOFITは¥12,600まで値下げしており価格競争が強い。原価は1688の折りたたみ単杠260元。"),
    dict(id="F07", sheet="R07_ゴルフネット", code="R07", type="golfnet", type_jp="ゴルフ練習ネット（大型）", role="条件付き（市場要確認）",
         fin_key="golfnet", en="golf practice net cage 10x10",
         title="ゴルフ練習ネット 大型 3m×3m（据え置き鉄管フレーム・ターゲット・マット付き）",
         name="ゴルフ練習ネット 3m×3m（鉄管フレーム・二重ネット・ターゲット布・ショットマット付き・屋内外）",
         price=29800, launch=26800, cny=280, va=500, pkg=(150, 30, 25, 25), parcels=1, fee="B", y=(30, 60, 100), order=50,
         top_units=500, rivals=["B0BVM96YM5", "B09P14XTCQ"], rival_cny=[300, 280], reg="",
         kw_jp="ゴルフ練習ネット 大型", kw_cn="高尔夫练习网 大型 打击网",
         merits="・ドライバーまで打てる、3m×3mは広くのびのび練習できる、枠があるので大振りにならない。衝撃吸収ネット付きで貫通を気にせず打てる。",
         demerits="【A】取扱説明書が紙1枚でネットの張り方が分からない（『ネットは内側から付けると後で知った』）／【A】支柱とベースの穴が合わない・部品欠品\n"
                  "【B】ネットに穴が空いていた・ターゲットマットが弱い／【C】3mは庭や軒先に入らなかった",
         ours="・ネットの張り方まで写真付きの日本語説明書＋動画、支柱は色分け・向き表示で穴ずれを防止、出荷前の部品数検品\n"
              "・ターゲットは厚手の二重布、2.5m／3m の2サイズ展開（設置寸法を画像で明示）",
         latent="『庭に入るサイズが欲しい』『野球・ティーバッティングにも使いたい』→ 2.5m版と多球技対応を訴求",
         memo="B0BVM96YM5（¥33,580・月500個のバッジ、評価14件）とFkstyle 3m（¥27,980・月50個）。月500個はバリエーション合算の可能性があり要確認。原価は1688の高尔夫打击笼 250〜280元。",
         strategy=dict(kw="ゴルフ練習ネット 大型／ゴルフネット 3m／ゴルフ ケージ",
                       leader="ゴルフネット 大型 シミュレーター ¥33,580（月500個・評価14件）／Fkstyle 3m×3m ¥27,980（月50個）",
                       why="上位の評価数が少なく、¥3万前後の大型ネットは出品が少ない。二重ネット・耐候性で差別化できる。",
                       spec="二重ネット／粉体塗装フレーム／ターゲット布・ショットマット付き／色分けジョイント",
                       price="導入¥26,800 → 定常¥29,800",
                       launch="ゴルフ練習・自宅練習キーワード広告、組立動画、庭での使用写真",
                       risk="市場が小さい可能性（月500個は要検証）：初回50個で反応を見る")),
    dict(id="F08", sheet="R08_ペットカート", code="R08", type="petcart", type_jp="ペットカート", role="主力（新規）",
         fin_key="petcart", en="pet stroller detachable carrier large dog",
         title="ペットカート 分離型（キャリー分離・自立折りたたみ・中大型犬対応）",
         name="ペットカート 分離型（キャリー取外し・自立折りたたみ・耐荷重30kg・前輪360°・後輪ブレーキ）",
         price=19800, launch=17800, cny=210, va=400, pkg=(90, 55, 25, 12), parcels=1, fee="A", y=(80, 150, 200), order=100,
         top_units=200, rivals=["B0DPKLVZQY", "B0D9K3YKZT"], rival_cny=[220, 230], reg="",
         kw_jp="ペットカート 分離型", kw_cn="宠物推车 大型犬 分离",
         merits="・折りたたみ・展開が簡単（カチッと音がする）、畳んで自立する、小回りが利く、サスペンションで段差も楽、中型犬2匹・大型犬30kgでも乗れる。",
         demerits="【A】異音（ガタガタ音）で夜に使えない・不良品対応に手間（Totoro ball★1）／【A】コット脱着のファスナーが面倒・折りたたみ時にコットに一手間（PETTENA）\n"
                  "【B】横幅が大きい／【C】手押し部分に荷物フックが欲しい",
         ours="・車輪とフレームの接合部に樹脂ブッシュ＋出荷前の走行検査で異音を防止、交換部品の国内在庫\n"
              "・コットはワンタッチバックルで着脱、コットを付けたまま折りたたみ、幅は改札・エレベーターを通れる寸法に\n・ハンドルに荷物フックとドリンクホルダー",
         latent="『大型犬でも階段で持ち上げられる軽さ』『通院・旅行で車に積みやすい』→ 重量と折りたたみ寸法を比較表で訴求",
         memo="Totoro ball（¥19,999・月200個）・PETTENA（¥22,999・月100個）。1688の分离式宠物推车 140〜220元。170サイズ送料¥2,000。",
         strategy=dict(kw="ペットカート／ペットカート 分離型／犬 カート 大型",
                       leader="Totoro ball 大型犬カート ¥19,999（月200個・★4.3）／PETTENA 分離型 ¥22,999（月100個・★4.5）",
                       why="¥2万前後で月100〜200個の出品が複数あり市場が分散。足回りの耐久性と折りたたみで差別化。",
                       spec="ゴムタイヤ・ダブルブレーキ／自立折りたたみ／二重メッシュ／低床",
                       price="導入¥17,800 → 定常¥19,800",
                       launch="シニア犬・多頭飼いの訴求、折りたたみ動画、ペット用品の比較表",
                       risk="低価格品（¥1.2万前後）との競争：耐荷重と足回りを数値で比較")),
]

REJECTED = V4.REJECTED + [
    dict(id="X08", name="ファイヤーピットテーブル 大型 蓋付き（¥21,980・月1,000個）", type_jp="ファイヤーピット", fee="B", price=21980, cny=369, va=500,
         pkg=(85, 85, 25, 25), parcels=1, top_units=1000, reg="見送り：1688の薪用火盆桌 蓋付きが369元で価格差2.5倍、200サイズ送料¥3,200"),
    dict(id="X09", name="ピザ窯 ポータブル（ガス／ペレット・回転式）（Amazon中央値¥42,000）", type_jp="ピザ窯", fee="B", price=29800, cny=700, va=500,
         pkg=(70, 55, 45, 25), parcels=1, top_units=100, reg="見送り：1688の便携披萨炉が685〜770元で価格差1.8倍"),
    dict(id="X10", name="コールドプランジ（折りたたみ冰浴桶）（¥8,000〜14,000・月900個）", type_jp="水風呂", fee="A", price=12800, cny=210, va=300,
         pkg=(70, 50, 25, 12), parcels=1, top_units=300, reg="見送り：小型で単価が低く、価格差2.6倍"),
    dict(id="X11", name="電動乗馬マシン（Amazon中央値¥118,800・月販ほぼ0）", type_jp="乗馬マシン", fee="B", price=49800, cny=1450, va=500,
         pkg=(80, 60, 60, 40), parcels=1, top_units=0, reg="見送り：1688の電動骑马机1,450元（195元の品は手動の腹筋器）。PSE必要"),
    dict(id="X12", name="テントサウナ＋薪ストーブ（Justart型・¥65,039・月600個）", type_jp="テントサウナ", fee="B", price=64800, cny=1100, va=500,
         pkg=(130, 45, 45, 43), parcels=2, top_units=600, reg="見送り（あと一歩）：¥64,800で天瞳表24%・実質19%。テント645元＋炉435元"),
    dict(id="X13", name="アウトドア薪ストーブ（ガラス窓・煙突付き）（Mt.SUMI型）", type_jp="薪ストーブ", fee="B", price=29800, cny=480, va=500,
         pkg=(70, 45, 45, 25), parcels=1, top_units=100, reg="条件付き水準（天瞳表25%・実質19%）だが上位はブランド（Mt.SUMI）"),
]

DRESSER = V4.DRESSER

TYPES = V4.TYPES + [
    dict(id="petcart", jp="ペットカート", verdict="採用", why="分離型で1688 210元・170サイズ。¥19,800で天瞳表33%・実質19%。"),
    dict(id="golfnet", jp="ゴルフ練習ネット", verdict="条件付き", why="大型3m×3mは1688 280元。¥29,800で天瞳表38%だが市場の裏付けが薄い。"),
]
TYPES = [t for t in TYPES if not (t["id"] in ("petcart", "golfnet") and t["verdict"] == "見送り")]

SOURCES = V4.SOURCES + [
    ("米国Amazon", "Amazon.com New Releases（401カテゴリ・各2ページ）と商品ページ141件。2026-10-27取得。ASINがB0G/B0Hの系列＝2025年末〜2026年の新規出品。",
     "https://www.amazon.com/gp/new-releases"),
    ("中国Amazon", "amazon.cnは2024年1月27日でPCでの購入を終了（アプリの海外購入のみ）。中国の新商品は1688の『2026新款』出品で代替。",
     "https://www.amazon.cn/"),
    ("Alibaba", "Alibaba.com（英語の卸サイト）：各最終候補・各商品タイプの検索リンクを記載。", "https://www.alibaba.com/"),
    ("抖音", "抖音电商《2026轻户外生活消费趋势报告》（2026年7月23日）：速開ビーチテント+359%、充気ベッド+57%、野外コンロ+195%。",
     "https://news.mydrivers.com/1/987/987871.htm"),
]

SCREEN_MIN_UNITS = 50

# English search words for Alibaba.com per product type
TYPE_EN = {
    "chair": "ergonomic mesh office chair", "gamingchair": "gaming chair footrest", "dresser": "vanity dresser LED mirror",
    "babycrib": "foldable baby crib", "babypen": "baby playpen", "spinbike": "spin bike magnetic", "fitbike": "exercise bike",
    "cupboard": "kitchen pantry cabinet", "pullup": "power tower pull up", "golfnet": "golf practice net", "petcart": "pet stroller",
    "mattress": "pocket spring mattress roll pack", "bed": "metal bed frame", "sofa": "sofa bed", "sofa3": "sectional sofa",
    "recliner": "recliner chair", "desk": "computer desk", "elecdesk": "electric standing desk", "tvstand": "tv stand",
    "bookshelf": "bookshelf", "catTower": "cat tree large", "steelrack": "steel shelving rack", "rack": "heavy duty storage rack",
    "trampoline": "trampoline with net", "benchpress": "adjustable weight bench", "rowing": "rowing machine", "kotatsu": "kotatsu table",
    "dogcage": "dog crate large", "storageshed": "outdoor storage shed", "tent": "camping tent large", "ladder": "telescopic ladder",
    "massage": "massage chair", "wagon": "folding wagon cart", "dumbbell": "adjustable dumbbell", "stocker": "outdoor garbage storage",
    "outdoorbox": "outdoor storage box", "dartboard": "electronic dartboard", "bbq": "charcoal grill", "catcage": "cat cage large",
    "sideboard": "sideboard cabinet", "whiteboard": "mobile whiteboard", "powerrack": "power rack", "smith": "smith machine",
    "massagebed": "folding massage table", "babyhighchair": "baby high chair", "fireplace": "fire pit", "treadmill": "walking pad treadmill",
    "stepper": "stepper", "dryrack": "clothes drying rack", "entrance": "storage bench", "shoebox": "shoe cabinet", "chest": "chest of drawers",
    "wardrobe": "wardrobe closet", "showcase": "glass display cabinet LED", "sauna": "sauna tent stove", "swing": "patio swing canopy",
    "garage": "carport tent", "jack": "floor jack 3 ton", "sup": "inflatable paddle board", "cycleport": "bike storage shed",
    "parcelbox": "parcel delivery box",
}


# --- R09: US new release with a gap in Japan --------------------------------------------
FINALISTS.append(dict(
    id="F09", sheet="R09_ピラティスリフォーマー", code="R09", type="reformer", type_jp="ピラティスリフォーマー", role="新商品（米国発・日本未発売）",
    fin_key="us_reformer", en="foldable pilates reformer home",
    title="ピラティスリフォーマー 家庭用（折りたたみ・キャスター・スプリング5本）",
    name="ピラティスリフォーマー 家庭用（折りたたみ収納・キャスター移動・スプリング5本・ジャンプボード付き）",
    price=49800, launch=44800, cny=700, va=800, pkg=(125, 45, 25, 35), parcels=1, fee="B", y=(30, 80, 120), order=50,
    top_units=0, rivals=["B0FX9PQK6X", "B0FY2F85WW"], rival_cny=[1000, 60], reg="",
    kw_jp="ピラティス リフォーマー 家庭用", kw_cn="普拉提核心床 折叠 家用",
    merits="・（日本の競合 ¥100,680）『おうちピラティス大満足』『ジムに行けない日も使える』『折りたたみでコンパクト』『組立は簡単』。\n"
           "・（米国）木製ピラティスリフォーマー（$159.99）が2026年の新着で月200個以上。",
    demerits="【A】重くて女性1人では2階に上げられない／【A】身長165cm位までしか使えない（レール長）\n"
             "【B】スプリングが4本で負荷の幅が狭い・折りたたみ時の安定性／【C】部品欠品時の対応への不満、セールでの値下がり",
    ours="・レールを延長して身長180cmまで対応、スプリング5本（色分け）で負荷を細かく調整、日本語の動画プログラム（QRコード）\n"
         "・本体は2分割梱包も選べる設計にして運搬を楽に、折りたたみ時のロック機構、キャスター移動\n"
         "・¥49,800（日本の既存品の半額）で『自宅ピラティス』の新しい市場を作る",
    latent="『スタジオに通う時間がない』『マンションでも静か』『狭い部屋で収納したい』→ 静音・折りたたみ・縦置き収納を訴求",
    memo="米国の2026年新着（木製リフォーマー $159.99・月200個以上）。日本は¥100,680の1品のみで月販バッジ無し＝価格が高くて市場が開いていない。1688の折叠普拉提核心床 644〜1,050元。",
    strategy=dict(kw="ピラティス リフォーマー／ピラティスマシン 家庭用／ピラティス 器具",
                  leader="（日本）折り畳み式ピラティスリフォーマー ¥100,680（月販バッジ無し）／（米国）Wooden Pilates Reformer $159.99（月200個以上）",
                  why="日本に手頃な家庭用リフォーマーが無い。¥49,800なら天瞳表32%・実質26%を確保しつつ既存品の半額で出せる。",
                  spec="日本語動画プログラム／色分けスプリング／静音キャリッジ／折りたたみ＋キャスター",
                  price="導入¥44,800 → 定常¥49,800",
                  launch="Instagram・YouTubeのピラティス講師とのタイアップ、スポンサー広告（ピラティス 器具）、動画",
                  risk="需要が未知数：初回50台で反応を確認。重量35kgで200サイズ送料¥3,200を織込み済み")))

US_VERDICT = {
    "reformer": ("◎ 最有力", "日本のAmazonは家庭用リフォーマーが¥100,680の1品のみ（月販バッジ無し）。ピラティス人気と合い、¥49,800なら天瞳表32%・実質26%（R09シート）。"),
    "cardcase": ("○ 有望（小型）", "トレカ人気で日本の需要は大きいが、大型施錠ディスプレイは日本で販売無し（翻訳ページは在庫切れ）。1688は148〜395元。¥19,800で天瞳表25%と薄め・160サイズ未満。"),
    "cloudsofa": ("△", "日本にも圧縮モジュールソファ（HOMFINE ¥27,531・月50個）が既にあり新規性は低い。1688は490〜960元で価格差2倍台。"),
    "woodpen": ("△", "日本はメッシュ・樹脂製（GU MODE等）が中心で木製は少ない。1688は160〜290元だが200サイズ送料で¥19,800でも天瞳表22%。"),
    "bedrail": ("×", "日本はベッドガードが¥2,000〜の低価格帯で月500個以上。3面キングサイズは日本の寝具サイズと合わない。"),
    "romanchair": ("×", "日本はGOGOJUMP等のトレーニングベンチが¥6,000前後で月1,000個。新規性・単価ともに不足。"),
    "bedsidecrib": ("×", "日本は添い寝ベビーベッドが¥11,800で月600個。既に競合が多い。"),
    "pantrysteel": ("△", "日本はスチール書庫が中心でキッチン用の高い収納庫は少ないが、1688同等品が3,000元前後と高い。"),
    "changingdresser": ("△", "日本はおむつ交換台（¥9,552・月1,000個）が売れているが、チェスト一体型は少ない。単価・梱包のバランス要検証。"),
    "swivelrocker": ("×", "日本ではゲーミングチェア等が検索上位で、回転ロッキングリクライナーの需要は小さい。"),
    "glider": ("×", "日本の授乳グライダーは¥21,850で月100個。1688は540元前後・大型で天瞳料金では赤字。"),
    "toyorganizer": ("×", "日本はおもちゃ収納が¥2,680〜で月300個。単価不足。"),
    "hitchcargo": ("×", "日本はヒッチメンバー装着車が少なく月販バッジ無し。"),
    "outdoorhoriz": ("×", "日本はAlebert等の樹脂製屋外収納が¥12,880で月1,000個。既存品が強い。"),
    "picnic8ft": ("×", "日本は折りたたみテーブルが低価格帯中心。8フィートの大型は需要が小さい。"),
    "partytent": ("×", "日本は3m×3mのワンタッチタープが中心（¥12,980）。3m×9mは業務用で需要が小さい。"),
    "bigtallchair": ("×", "日本はゲーミングチェアが¥13,778で月500個。大柄向けはニッチ。"),
    "basketport": ("×", "日本でも同じ商品が販売中（Yohood ¥14,600・月100個）。"),
}
US_EN = {"reformer": "foldable pilates reformer", "cardcase": "card display case aluminum lock", "cloudsofa": "modular cloud sofa compressed",
         "woodpen": "wooden baby playpen foldable", "bedrail": "toddler bed rail 3 sides", "romanchair": "roman chair back extension",
         "bedsidecrib": "bedside crib pack and play", "pantrysteel": "metal pantry cabinet", "changingdresser": "changing table dresser",
         "swivelrocker": "swivel rocker recliner", "glider": "glider rocker ottoman", "toyorganizer": "toy storage organizer bookshelf",
         "hitchcargo": "hitch cargo carrier folding", "outdoorhoriz": "outdoor horizontal storage shed", "picnic8ft": "8ft folding picnic table",
         "partytent": "10x30 party tent", "bigtallchair": "big and tall gaming chair", "basketport": "portable basketball hoop"}
CN_VERDICT = {
    "dressernight": ("○ 有望", "ドレッサー＋ナイトテーブル一体型は日本のAmazonで見当たらず、中国で月351件。一人暮らし向けにR04ドレッサーのバリエーションとして投入。"),
    "steelwardrobe": ("△", "日本はメタルラック型ワードローブ（¥7,227・月500個）が中心。引き戸付きスチール製は1688で850〜1,370元と高く、利益が残りにくい。"),
    "streamtank": ("△（小型）", "渓流水槽は日本のAmazonで見当たらない新ジャンル。1688は120〜180元と安いが小型（160サイズ未満）。"),
    "floatbed": ("△", "日本はフレームの見えない『フローティングベッド』の手頃な品が少ないが、1688は1,400元前後と高い。"),
    "cloudsofabed": ("△", "日本は折りたたみソファベッド・座椅子が¥7,000前後で多数。新規性が弱い。"),
    "deskbike": ("○", "日本は『立ち・座り2wayバイク』（¥18,900・月200個）がある。デスク一体型は少なく、在宅ワーク向けに差別化余地。"),
}
CN_EN = {"dressernight": "vanity dresser with nightstand", "steelwardrobe": "steel wardrobe sliding door", "streamtank": "stream aquarium side filter",
         "floatbed": "floating bed frame", "cloudsofabed": "folding sofa bed", "deskbike": "exercise bike with desk"}
LATENT_VERDICT = {
    "soundproof": ("× 見送り", "1688の組立式防音ブースも1.2万〜1.5万元と高く、安くできない。"),
    "sauna": ("× 見送り", "1688で同等の木製サウナが見つからない（遠赤外線はPSE）。"),
    "plunge": ("× 見送り", "日本では¥8,000〜14,000で既に売れており、価格差2.6倍・小型で利益不足。"),
    "oxygen": ("× 見送り", "1688も4万〜14万元。薬機法の表示規制。"),
    "pizza": ("× 見送り", "1688の便携披萨炉が685〜770元で価格差1.8倍。"),
    "rooftent": ("× 見送り", "1688も3,500元前後で価格差1.6倍・大型。"),
    "mahjong": ("△", "日本で月1,000個売れている（高くても売れている市場）。1688は1,540〜1,760元・90kgで価格差2倍、PSE必要。"),
    "horse": ("× 見送り", "日本の乗馬マシン（中央値¥118,800）は電動。1688の電動骑马机は1,450元、195元の品は手動の腹筋器で別物。"),
    "crosstrainer": ("× 見送り", "1688の椭圆机が1,300〜1,700元で価格差不足。"),
    "gazebo": ("× 見送り", "1688のアルミ屋根ガゼボは4,800元以上。"),
    "pingpong": ("× 見送り", "1688の卓球台720〜900元・70kgで送料・運賃が重い。"),
    "billiard": ("× 見送り", "100kg超・チャーター便。"),
    "carbed": ("△", "日本の車中泊ベッドキットは車種別の専用品（ハイエース等）で1688の汎用品と別物。車種別に作れば余地あり。"),
    "carebed": ("× 見送り", "1688で同等品が見つからない・PSE・介護用は別基準。"),
    "golfsim": ("○", "大型ゴルフネットは1688 250〜280元で¥29,800なら天瞳表38%（R07シート）。センサー付きは技適が必要。"),
    "deck": ("× 見送り", "人工木デッキは重量物で国内送料が重く、1688の同等品が少ない。"),
    "awning": ("× 見送り", "長さ3m超の長尺物で送料が高い。1688の伸縮遮阳棚は540元前後で価格差1.9倍。"),
}
LATENT_EN = {"soundproof": "soundproof booth", "sauna": "infrared sauna wooden", "plunge": "cold plunge tub", "oxygen": "hyperbaric chamber soft",
             "pizza": "outdoor pizza oven", "rooftent": "roof top tent", "mahjong": "automatic mahjong table", "horse": "horse riding machine",
             "crosstrainer": "elliptical machine", "gazebo": "hardtop gazebo", "pingpong": "table tennis table", "billiard": "billiard table",
             "carbed": "car bed platform", "carebed": "electric nursing bed", "golfsim": "golf practice net", "deck": "wpc decking", "awning": "retractable awning"}


# screen rows whose product type was verified with spec-matched 1688 prices and rejected (01 sheet X rows)
VERIFIED_NO = {"sauna": "X01/X12", "showcase": "X02", "swing": "X03", "garage": "X04", "jack": "X05", "dumbbell": "X06",
               "mattress": "X07", "ファイヤーピット": "X08", "ピザ窯": "X09", "水風呂 家庭用": "X10", "コールドプランジ": "X10",
               "乗馬マシン": "X11", "薪ストーブ": "X13"}
