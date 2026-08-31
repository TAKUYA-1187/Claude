# ChatGPT 画像生成プロンプト集 ─ 実物写真を「参照画像」として使う方式

添付いただいた商品写真をもとに、実測仕様を反映して全面改訂しました。

---

## § 0　実際の進め方（まずここ）

長いプロンプトを毎回貼る必要はありません。**最初の1通で前提を伝え、
2通目以降は一行の指示**で回すのが、いちばん速く、いちばん精度が出ます。

### 1通目（これだけ長い / 商品写真を添付して送る）

```
これから、添付した化粧台（ドレッサー）の写真をもとに、EC用の商品写真を何枚か
作ってもらいます。以下を必ず守ってください。

【絶対条件】
1. 添付写真の商品は一切変更しない。形・比率・白いマット塗装・木目の取っ手・
   引き出しの数・鏡の形と位置、すべてそのまま維持すること。
   変えてよいのは、背景・床・光・周囲に置く小物だけ。
2. 画像に文字・数字・ロゴ・透かしを入れない。
3. CG・3Dレンダリング風にしない。カメラで撮った実写に見えるように、
   自然な粒状感、わずかに不均一な光、リアルな素材の質感で。
   HDR風の過度な鮮やかさ、グロー、不自然なシャープネスは不可。
4. これから複数枚を作ります。商品の見た目が毎回変わらないよう、
   常に添付写真を基準にしてください。

【商品仕様】（描写の参考に）
外寸 幅80 × 奥行35 × 高さ130cm、天板高70cm。
左：3段チェスト（幅30cm）の上にオープン棚（幅24cm・4段）。
右：デスク（天板幅50cm・高さ70cm）と鍵付き引き出し（42×23×8cm）。
デスクの上に45×60cmのLEDミラーがレールで横にスライドし、
その裏に40×8.5×60cmの収納が隠れている。
スツール（32×21.5×36cm）付属。LEDは電球色・昼白色・昼光色の3色。

では1枚目です。商品はそのままに、背景だけ以下に変えてください。

Bright, lived-in Japanese bedroom. Warm white painted wall, light oak flooring,
soft natural daylight from a window on the left. The dresser stands against the
wall with correct perspective and a realistic soft contact shadow on the floor.
Match the lighting on the product to the room so it does not look pasted in.
Photorealistic interior photography, 35mm lens, natural depth of field.
No text, no logos, no watermarks, no people.
```

### 2通目以降（一行でよい）

前提は1通目で伝わっているので、変えたい点だけを短く指示します。

```
同じ商品のまま、背景を夜の間接照明の寝室に変えて。ミラーのLEDを暖色で点灯させて。
```
```
同じ商品・同じ画角のまま、鏡をレールで右にスライドさせて、裏の収納が見えた状態に。LEDは消灯。
```
```
もっと生活感を出して。天板にスキンケアボトルとメイクブラシ、床にラグ、左端にベッドの端。商品自体は変えないで。
```
```
引き出しを3つとも階段状に開けて、中にコスメが入っている状態に。斜め上から。
```
```
ミラー部分だけのアップに。部屋を暗くして、LEDを昼光色で点灯。
```

### 添付する写真の使い分け

| 作りたいもの | 添付する写真 |
|---|---|
| 背景差し替え・生活シーン | 白背景の商品単体カット |
| ミラーのスライド2状態 | 白背景の商品単体カット |
| LED 3色 | ミラーのアップが写っているカット |
| 収納ディテール | 引き出しを開けているカット |

### うまくいかないときの順番

1. **まず追加指示で直す**（§7の修正文）。作り直すより速く収束します
2. 3回直しても直らなければ、チャットを新しく開いて1通目からやり直す
3. 商品が別物になったら、必ず `添付写真と同じ商品に戻して。背景だけ変えて。` と伝える

---

## 最重要：ゼロから生成せず、実物写真を「編集」させる

「AI作成だとわかる画像」になる最大の原因は、**テキストだけで商品を作らせること**です。
存在しない商品を想像で描くため、細部が破綻します。

正解は、**実物写真をアップロードして背景や状況だけを変えさせる**ことです。
商品そのものは実写のまま残るので、AIっぽさが出ません。

```
✗ 「白いドレッサーの写真を作って」          → 想像で描く → AIだとバレる
◎ 「この写真の商品はそのまま、背景だけ変えて」 → 商品は実写のまま → バレない
```

**すべてのプロンプトで、必ず商品写真を添付してください。**

### 生成物の使いどころ

| 用途 | 可否 |
|---|---|
| 仕入先・工場への仕様イメージ伝達 | ◎ |
| 撮影時の構図リファレンス | ◎ |
| 社内の企画検討 | ◎ |
| Amazon商品ページへの入稿 | ✗ 実物との相違・権利の問題があるため不可 |

添付の写真は他社の商品ページの画像です。これを加工したものも含め、
自社の商品ページには使用できません。**自社で撮影した写真に対して
同じプロンプトを使えば、そのまま入稿できる画像になります。**

---

## 実測仕様（添付の製品仕様図より）

プロンプト内の数値はすべてこの実測値に統一してあります。

| 項目 | 実測値 |
|---|---|
| 外寸 | 幅80 × 奥行35 × 高さ130cm |
| 天板高 | 70cm |
| ミラー | 45 × 60cm（横スライド式） |
| 鏡裏収納 | 40 × 8.5 × 60cm |
| オープン棚（左タワー） | 24 × 13 × 60cm |
| デスク引き出し | 42 × 23 × 8cm（鍵付き） |
| 3段チェスト引き出し | 24 × 23 × 8cm × 3杯 |
| 3段チェスト本体 | 幅30 × 奥行35 × 高さ50cm |
| スツール | 32 × 21.5 × 36cm |
| LED | 電球色・昼白色・昼光色（タップ切替）／長押しで0〜100%調光 |

---

## § 1　背景差し替え（いちばん使う）

商品写真（白背景のもの）を添付して送ります。

```
Keep the product in the attached photo EXACTLY as it is — do not redraw, redesign or
alter the furniture in any way. Preserve every detail: the proportions, the white
matte finish, the light oak bar handles, the three-tier chest, the sliding LED mirror,
the open shelf tower, the keyhole, and the white upholstered stool.

Change ONLY the background and the floor.

New setting: a bright, lived-in Japanese bedroom. Warm white painted wall, light oak
flooring, soft natural daylight coming from a window on the left. Place the dresser
against the wall so it sits naturally in the room, with correct perspective and a
realistic soft contact shadow where it meets the floor.

The lighting on the product must match the new room lighting — soft, warm, directional
from the left — so the product does not look pasted in.

Photorealistic interior photography, 35mm lens, natural depth of field, no HDR look,
no over-saturation, no glow, no artificial sharpening.
No text, no letters, no logos, no watermarks, no people.
```

### 背景のバリエーション

上の `New setting:` の段落だけ差し替えます。

```
【朝の窓辺】
A sunlit bedroom corner in the morning. Off-white wall, pale oak floor, sheer white
curtains diffusing bright daylight from the right. A few soft shadows on the wall.
```

```
【夜・間接照明】
A calm bedroom at night. Warm dim ambient light, a soft glow from a bedside lamp out
of frame. The mirror's LED is switched on with a warm 3000K glow, and it is the
brightest light in the scene, casting a gentle warm light onto the wall.
```

```
【ワンルーム・狭さが伝わる】
A compact Japanese one-room apartment. The dresser sits against a white wall between
a bed on the left and a window on the right, showing how little floor space it needs.
Light wood flooring, minimal styling, daylight.
```

```
【北欧ナチュラル】
A Scandinavian-style bedroom. White wall, pale birch flooring, a small woven rug, a
green plant in a terracotta pot at the edge of the frame. Bright, airy, soft daylight.
```

---

## § 2　「使っている感」を出す

生活感は**商品の周りの状況**で作ります。商品自体には手を入れさせないのが鉄則です。

```
Keep the product in the attached photo EXACTLY as it is — same design, same
proportions, same finish, same angle. Do not redraw the furniture.

Place it in a real, lived-in Japanese bedroom and add natural signs of daily use
AROUND it, not on it:
a few skincare bottles and a makeup brush holder on the desktop, a hair tie and a
small tray, a soft cotton rug partly visible on the floor, a bed edge with rumpled
linen entering the frame on the left, and daylight from a window on the right.

Everything should look casually arranged, not styled for a catalogue — slightly
imperfect placement, natural clutter, real textures.

Photorealistic interior photography, 35mm lens, natural window light, gentle shadows,
no HDR, no glow, no over-saturation.
No text, no letters, no logos, no watermarks, no people.
```

### 人物を入れる場合

```
Keep the product in the attached photo EXACTLY as it is.

Add a Japanese woman in her late twenties sitting on the stool, seen from behind and
slightly to the side, so her face is only partly visible in the mirror. She is
applying makeup with a brush, wearing a simple cream knit top, hair loosely tied.
Natural, relaxed posture — a real moment, not a pose.

The room: warm white wall, light oak floor, soft morning daylight from the left.
The mirror's LED is on with a warm glow lighting her face.

Photorealistic candid interior photography, 50mm lens, shallow depth of field with the
product in focus, natural skin texture, no beauty filter, no over-smoothing.
No text, no letters, no logos, no watermarks.
```

**人物を入れると一気にAIっぽくなります。** 手の指、髪の生え際、鏡像の整合性が
崩れやすいためです。生成したら必ず**手・指の本数・鏡に映る像**を確認してください。

---

## § 3　ミラーのスライド 2状態

比較として並べるので、**1枚目を作ってから2枚目**を続けて指示します。

```
【1枚目：鏡を閉じた状態】
Keep the product in the attached photo EXACTLY as it is.
Show the sliding mirror in its CLOSED position — centred over the storage unit,
completely hiding the shelves behind it. The LED is on with a warm glow.
Straight-on frontal view. Warm white wall, light oak floor, soft daylight.
Photorealistic, 35mm lens, natural shadows.
No text, no letters, no logos, no watermarks, no people.
```

```
【2枚目：鏡を右へスライド】
Keep the product, the camera position, the framing, the background and the lighting
EXACTLY the same as the previous image.

The ONLY change: the mirror has slid along its rail to the RIGHT, overhanging past the
right edge of the desk, so the hidden storage behind it is now fully exposed — three
tiers holding skincare bottles, lipsticks and small cosmetic jars. The black metal
slide rails above and below the storage are visible. The LED is switched off.

Identical camera angle, identical distance, identical lighting, identical background.
No text, no letters, no logos, no watermarks, no people.
```

---

## § 4　LED 3色

ミラー部分のクローズアップ写真を添付し、**色の語句だけ差し替えて3回**送ります。

```
Keep the product in the attached photo EXACTLY as it is.

Close-up of the LED mirror, filling the frame. The room is dim so the LED is the
dominant light source. The LED strip inside the mirror frame is glowing ★COLOUR★.
The glow spills softly onto the white body and the shelves beside it.
Identical framing, identical exposure, identical camera position across all versions.

Photorealistic, sharp, natural. No blown-out highlights, no bloom, no lens flare.
No text, no letters, no logos, no watermarks, no people.
```

| ファイル名 | `★COLOUR★` |
|---|---|
| `led_warm` | `a warm amber 3000K warm-white, cosy and soft` |
| `led_neutral` | `a natural 4500K neutral white, clean and balanced` |
| `led_cool` | `a crisp 6000K cool daylight white, slightly blue-tinted` |

---

## § 5　収納ディテール 4枚

```
【storage_1 オープン棚】
Keep the product in the attached photo EXACTLY as it is.
Close-up of the narrow open shelf tower on the left side (24cm wide, four tiers),
filling the frame at a slight three-quarter angle. Each tier holds skincare bottles,
a tall perfume bottle and small jars, casually arranged with room to spare.
Soft natural daylight. Photorealistic, sharp, no HDR.
No text, no letters, no logos, no watermarks, no people.
```

```
【storage_2 鏡裏収納】
Keep the product in the attached photo EXACTLY as it is.
The mirror slid fully to the right, revealing the three-tier hidden storage behind it.
Close-up filling the frame, slight three-quarter angle. The shelves hold lipsticks,
skincare bottles and small cosmetic boxes. The black metal slide rails are visible
above and below. Soft natural daylight. Photorealistic, sharp.
No text, no letters, no logos, no watermarks, no people.
```

```
【storage_3 鍵付きデスク引き出し】
Keep the product in the attached photo EXACTLY as it is.
The wide desk drawer pulled open about 20cm, seen from slightly above at a three-quarter
angle so the inside is visible. The keyhole and a small silver key hanging from it are
clearly in frame. Inside: makeup palettes, brushes and small boxes, casually arranged.
Soft natural daylight. Photorealistic, sharp.
No text, no letters, no logos, no watermarks, no people.
```

```
【storage_4 3段チェスト】
Keep the product in the attached photo EXACTLY as it is.
The three chest drawers pulled open in a staggered cascade, seen from slightly above at
a three-quarter angle so the contents of all three are visible. Top: lipsticks and
compacts. Middle: brushes and palettes. Bottom: larger bottles and a hair dryer.
The light oak bar handles are clearly visible. Soft natural daylight. Photorealistic.
No text, no letters, no logos, no watermarks, no people.
```

---

## § 6　仕入先に見せる仕様イメージ

現物がない段階では、これがいちばん実用的です。商品写真を添付して送ります。

```
Keep the product in the attached photo exactly as it is.
Re-render it as a clean manufacturing reference sheet: the same product shown from
three angles side by side on a plain light grey background — front elevation, side
elevation, and a three-quarter view.
Even lighting, no shadows, no background clutter, no styling props.
No text, no numbers, no dimension lines, no logos, no watermarks.
Horizontal 16:9, sharp and clear.
```

生成した画像を 1688 / Alibaba のサプライヤーに送り、こう聞きます。

```
这样的产品，你们能做吗？
外径 80×35×130cm，台面高 70cm，镜子 45×60cm 可横向滑动，镜后收纳 40×8.5×60cm，
开放格 24×13×60cm，带锁抽屉 42×23×8cm，三层抽屉柜 24×23×8cm×3，凳子 32×21.5×36cm。
LED 三色（暖光/自然光/冷光），触摸切换，长按无级调光。
请报价，并告知起订量、交货期，以及产品图片能否授权我们用于亚马逊商品页面。
```

---

## § 7　AIっぽさを消す修正指示

生成し直すより、**出てきた画像に追加で指示**するほうが早く収束します。

| 症状 | そのまま送る修正文 |
|---|---|
| CG・レンダリングっぽい | `This looks like a 3D render. Make it look like a real photograph taken with a camera: natural film grain, slightly imperfect lighting, realistic material texture, no perfect symmetry.` |
| 全体がツヤツヤ・過剰に鮮やか | `Reduce the saturation and contrast. Remove the HDR look, the glow and the artificial sharpening. Make it look like a natural, unedited photo.` |
| 商品が別物になった | `You changed the furniture. Restore the product to be IDENTICAL to the attached reference photo — same proportions, same handles, same drawer count, same mirror. Change only the background.` |
| 合成に見える（浮いている） | `The product looks pasted in. Match the lighting direction and colour temperature of the product to the room, and add a realistic soft contact shadow where it meets the floor.` |
| 影が不自然 | `Fix the shadows. There is a single soft light source from the left, so all shadows must fall to the right with consistent softness.` |
| 木目・質感がのっぺり | `Add realistic material texture: fine wood grain on the oak handles, a subtle matte texture on the white painted surfaces, visible fabric weave on the stool cushion.` |
| 引き出しの数が変わる | `There must be exactly three drawers in the left chest and exactly one wide drawer under the desktop. Do not change the number of drawers.` |
| 鏡の映り込みがおかしい | `The mirror must reflect the room in front of it with correct perspective and geometry. Remove any impossible or duplicated reflection.` |
| 人物の手や指が破綻 | `The hands are malformed. Redraw with anatomically correct hands, five fingers, natural proportions.` |
| 文字やロゴが入る | `Remove all text, letters, numbers, logos and watermarks from the image completely.` |

---

## § 8　生成後の手順

```bash
# 1. photos/ に決められた名前で保存（photos/README.md 参照）
# 2. 日本語コピー・寸法線・仕様表を合成
node build.js
# 3. 解像度・背景の白色純度・商品占有率を検証
node check.js
```

**日本語テキストは絶対にAIに描かせないでください。** 必ず崩れます。
文字はすべて `build.js` が乗せます。AIには写真だけを作らせてください。
