# ChatGPT 画像生成プロンプト集 ─ ドレッサー 幅80cm

---

## 最初に：最高品質を出すための3つの鉄則

### 鉄則1　日本語テキストは絶対に生成させない

画像生成AIは日本語の描画が苦手で、必ず崩れます。「LEDライト」が「LEDフイト」になる、
文字が溶ける、といった失敗が起きます。**プロンプトには必ず
`no text, no letters, no logos, no watermarks` を入れてください。**

テキストと図解は、このリポジトリのパイプラインで合成します。

```
AIに作らせるもの  →  商品の「写真」だけ
パイプラインが乗せるもの  →  日本語コピー・数値・寸法線・仕様表
```

この分担が、最高品質を得る唯一の方法です。

### 鉄則2　1枚目を「基準画像」として作り込み、残りは参照画像から派生させる

テキストだけで生成すると、**毎回ちがう商品が出てきます。**
引き出しの数が変わる、取っ手の色が変わる、鏡の形が変わる。
とくに 03（LED3色）と 04（2WAY）は「同じ商品の同じ画角」であることが命なので、
テキストだけで作ると成立しません。

**正しい手順:**

```
1. § A の基準画像を1枚だけ生成し、納得いくまで作り込む
2. その画像を ChatGPT にアップロードする
3. 「この画像と同じ商品で、○○の状態を」と指示して残りを生成
```

参照画像を渡しても完全一致はしません。比較カットは特に慎重に見てください。

### 鉄則3　商品ページのメイン画像には使わない

AI生成画像は実物と一致しないため、Amazonのメイン画像には使用できません。
出品停止やアカウント健全性の問題につながります。

**この生成画像が有効な用途:**

| 用途 | 有効性 |
|---|---|
| 仕入先・工場への仕様イメージ伝達 | ◎ 「こういう商品が欲しい」が一発で伝わります |
| 撮影時の構図リファレンス（カメラマンに見せる） | ◎ 撮影指示書と併せて渡すと精度が上がります |
| 社内の企画検討・モック | ◎ |
| SNS広告のイメージカット（商品が主役でないもの） | ○ |
| **Amazon商品ページのメイン画像** | **✗ 使用不可** |
| **Amazon商品ページのサブ画像** | **✗ 実物と相違するため不可** |

---

## 共通設定

- ChatGPTで**画像生成を有効**にし、**参照画像をアップロードできる状態**で使ってください
- 出力は**正方形 1:1**（Amazon用）または**縦長 4:5**（ヒーロー用）を指定
- 生成後、`photos/` に置いて `node build.js` → `node check.js`
- **プロンプトは英語のまま使ってください。** 画像生成モデルは英語のほうが精度が高く、
  日本語で指示すると細部が落ちます

---

## § A　基準画像（最初にこれを作り込む）

まずこの1枚を、満足いくまで再生成してください。ここで妥協すると全部に響きます。

```
Professional commercial e-commerce product photograph of a modern compact vanity
dressing table, shot for a Japanese furniture catalogue.

PRODUCT — describe exactly:
A white vanity dresser, 80cm wide, 35cm deep, 130cm tall.
Matte white MDF body with a smooth, clean finish.
UPPER SECTION: an open shelving unit divided into three horizontal tiers, and a
rectangular LED-backlit mirror about 38cm wide and 50cm tall, mounted on a slim
horizontal rail so it can slide sideways across the front of the shelves. The mirror
sits on the right half, covering the right shelves; the left shelves are visible and
hold a few skincare bottles and a small perfume bottle.
LOWER SECTION: a chest of three drawers on the left with slim horizontal oak wooden
bar handles; on the right, one wide shallow drawer beneath the desktop with a small
round keyhole; open knee space below it.
A matching white stool with a pale blush-pink upholstered seat cushion is tucked
into the knee space.

CAMERA: straight-on frontal view, camera at the product's mid-height (about 65cm
from the floor). 85mm lens equivalent. No wide-angle distortion, no keystoning,
perfectly vertical lines. Sharp focus from front to back.

LIGHTING: two large softboxes at 45 degrees left and right, plus soft overhead fill.
Even and shadowless. Neutral white balance so the white furniture reads as clean
bright white, never grey, cream or yellow. The LED mirror is softly lit with a warm
white glow around its inner frame.

BACKGROUND: seamless pure white studio background, no horizon line, no cast shadow
on the floor, no wall.

CONSTRAINTS: no text, no letters, no numbers, no logos, no watermarks, no brand
names, no people, no hands, no plants, no rugs, no decorative props beyond the few
cosmetic bottles on the shelves.

STYLE: photorealistic, ultra sharp, high resolution, clean commercial catalogue
quality, minimal Japanese interior aesthetic.

Square 1:1 composition, product fills about 85% of the frame height, centred.
```

**日本語での要点:** 幅80×奥行35×高さ130cmの白いドレッサー。上段は3段のオープンラックと
横スライドするLEDミラー（右半分を覆う）。下段は左に3杯の引き出し（オークのバー取っ手）、
右に鍵付きのワイド引き出しとニースペース。淡いピンクの座面のスツールが足元に。
正面・85mm相当・影なし・純白背景・テキストなし。

---

## § B　派生カット（基準画像をアップロードしてから指示）

以下はすべて**基準画像を添付した状態**で送ってください。
冒頭の `Using the attached image as the exact reference product` が要です。

### B-1　`main` — メイン画像用（白背景・切り抜き）

```
Using the attached image as the exact reference product, keep the product design,
proportions, colours and every detail identical.

Re-render it as a pure white background cut-out product shot:
seamless #FFFFFF background, absolutely no cast shadow, no floor line, no gradient.
Straight-on frontal view. The product plus the stool fills 88% of the frame height,
perfectly centred, generous even margins.
Turn the mirror LED off or very dim so the white body colour reads accurately.

No text, no logos, no watermarks, no props, no people.
Square 1:1, ultra high resolution, photorealistic commercial product photography.
```

### B-2　`hero` — 斜め45度の全体カット

```
Using the attached image as the exact reference product, keep the design identical.

Re-render from a three-quarter angle: the camera rotated 45 degrees to the left of
the product, at the product's mid-height, 85mm lens equivalent, showing both the
front face and the left side panel so the depth is visible.
The LED mirror is switched on with a warm 3000K glow.
Soft studio lighting, seamless very light warm-grey background with a gentle
gradient, subtle soft contact shadow under the product only.

No text, no logos, no watermarks, no people.
Vertical 4:5 composition, photorealistic, ultra sharp, commercial catalogue quality.
```

### B-3〜B-5　`led_warm` / `led_neutral` / `led_cool` — LED 3色比較

3枚は**同じ画角・同じ露出**であることが命です。1枚ずつ、同じ参照画像から作ってください。

```
【共通の骨格 — 色の部分だけ差し替える】

Using the attached image as the exact reference product, keep the design identical.

Close-up crop of the LED mirror section only, filling the frame.
Camera straight-on, level with the centre of the mirror, 85mm lens equivalent.
The room is dark so the LED is the dominant light source.
The LED strip around the inner frame of the mirror is glowing [★COLOUR★].
The glow spills softly onto the white body around the mirror.
Identical framing, identical exposure, identical camera position.

No text, no logos, no watermarks, no people, no reflection of a person in the mirror.
Horizontal 4:3 composition, photorealistic, ultra sharp.
```

`★COLOUR★` を差し替えます。

| ファイル | 差し替える文言 |
|---|---|
| `led_warm` | `a warm amber 3000K warm-white, cosy and soft` |
| `led_neutral` | `a natural 4500K neutral white, clean and balanced` |
| `led_cool` | `a crisp 6000K cool daylight white, slightly blue-tinted` |

### B-6　`mirror_closed` — ミラー中央（ドレッサーとして）

```
Using the attached image as the exact reference product, keep the design identical.

Straight-on frontal view, full product, camera at mid-height, 85mm lens equivalent.
The sliding mirror is positioned in the centre-right of the upper unit — the normal
dressing-table position. The LED is on with a warm glow.
Seamless very light warm-grey background, soft contact shadow only.

No text, no logos, no watermarks, no people.
Vertical 3:4, photorealistic, ultra sharp, commercial product photography.
```

### B-7　`mirror_open` — ミラーを左へスライド（デスクとして）

```
Using the attached image as the exact reference product, keep the design, the camera
position, the framing and the lighting EXACTLY the same as the previous image.

The only change: the sliding mirror has been moved along its rail to the far LEFT
of the upper unit. The right-hand shelves are now fully exposed and visible, holding
skincare bottles and small cosmetic items on all three tiers.
The LED is switched off.

Identical camera angle, identical distance, identical lighting, identical background.
No text, no logos, no watermarks, no people.
Vertical 3:4, photorealistic, ultra sharp.
```

### B-8〜B-11　`storage_1`〜`storage_4` — 収納ディテール

```
【storage_1 — オープンラック】
Using the attached image as the exact reference product, keep the design identical.
Close-up of the three-tier open shelving unit, filling the frame.
Each tier holds skincare bottles, a tall perfume bottle, and small jars, arranged
neatly with room to spare. Slight three-quarter angle to show depth.
Soft even studio lighting, warm and clean.
No text, no logos, no watermarks, no people. Horizontal 4:3, photorealistic.
```

```
【storage_2 — 鍵付き引き出し】
Using the attached image as the exact reference product, keep the design identical.
Close-up of the wide drawer beneath the desktop, pulled open about 20cm, seen from a
slightly elevated three-quarter angle so the inside is visible.
A small round keyhole and a slim metal key are clearly visible on the drawer front.
Inside: neatly arranged makeup palettes and small boxes.
Soft even studio lighting. No text, no logos, no watermarks, no people.
Horizontal 4:3, photorealistic, ultra sharp.
```

```
【storage_3 — 引き出し3杯】
Using the attached image as the exact reference product, keep the design identical.
The three left-hand drawers pulled open in a staggered cascade, seen from a slightly
elevated three-quarter angle so the contents of all three are visible.
Top drawer: lipsticks and compacts. Middle: makeup brushes and palettes.
Bottom: a hair dryer and larger bottles.
Soft even studio lighting. No text, no logos, no watermarks, no people.
Horizontal 4:3, photorealistic, ultra sharp.
```

```
【storage_4 — スツール収納】
Using the attached image as the exact reference product, keep the design identical.
Wider frontal shot showing the stool fully tucked into the knee space beneath the
desktop, so the product's footprint looks compact and the floor is clear.
The full width of the product is in frame.
Soft even studio lighting, seamless light warm-grey background.
No text, no logos, no watermarks, no people. Horizontal 4:3, photorealistic.
```

---

## § C　仕入先に見せる仕様イメージ用（この用途が今いちばん実用的）

現物がない段階では、これが最も価値を生みます。工場に「こういう商品が欲しい」と
見せるための、構造がわかる図です。

```
A clean technical product visualisation of a white vanity dressing table for a
furniture manufacturing brief.

Show the same product from three angles arranged side by side on a plain light grey
background: front elevation, side elevation, and a three-quarter view.
The product: 80cm wide, 35cm deep, 130cm tall, matte white body, oak wooden bar
handles, three-tier open shelving on top with a sliding LED mirror on a rail,
three drawers on the lower left, one wide lockable drawer on the lower right,
open knee space, matching stool with a pale pink cushion.

Clean, evenly lit, no shadows, no background clutter.
No text, no numbers, no dimension lines, no logos, no watermarks.
Horizontal 16:9, sharp, clear, technical illustration style with realistic materials.
```

**使い方:** この画像を 1688 / Alibaba のサプライヤーに送り、
「这样的产品，你们能做吗？」（こういう商品は作れますか）と聞きます。
言葉で説明するより圧倒的に速く伝わります。

---

## § D　思ったとおりに出ないときの修正指示

生成し直すのではなく、**出てきた画像に対して追加指示**を出すほうが早く収束します。

| 症状 | 送る修正指示 |
|---|---|
| 白がグレー・クリーム色に見える | `The furniture must be pure clean white, not grey or cream. Brighten the whites and set a neutral white balance.` |
| 家具が歪む・広がって見える | `Use an 85mm lens perspective. Remove all wide-angle distortion. All vertical edges must be perfectly vertical and parallel.` |
| 勝手に文字やロゴが入る | `Remove all text, letters, numbers, logos and watermarks from the image completely.` |
| 床に影が落ちる（メイン画像用） | `Remove the cast shadow entirely. Pure seamless white background with no floor line and no gradient.` |
| 引き出しの数が変わってしまう | `There must be exactly three drawers on the lower left and exactly one wide drawer on the lower right. Do not change the number of drawers.` |
| 鏡が棚を覆っていない | `The mirror must overlap and cover the right half of the shelving unit, mounted in front of it on a horizontal rail — not beside it.` |
| 人物や手が写り込む | `Remove all people, hands and body parts from the image.` |
| 生活感が出すぎる | `Remove the rug, plants and decorative props. Keep only the product and the stool.` |
| 解像度が足りない | `Regenerate at the highest available resolution, ultra sharp, fine detail.` |

---

## § E　生成後の手順

```bash
# 1. 生成画像を photos/ に、決められた名前で保存
#    main.png / hero.png / led_warm.png / ... （photos/README.md 参照）

# 2. 合成
node build.js

# 3. 検証（解像度・背景の白色純度・商品の占有率）
node check.js
```

生成画像は長辺が2000px未満のことが多いため、`check.js` が警告を出す可能性があります。
その場合は生成時に最大解像度を指定し直すか、アップスケールしてください。

**繰り返しになりますが、この画像を商品ページに入稿しないでください。**
実物の撮影ができるまでの「つなぎ」と「仕入先への伝達手段」として使ってください。
