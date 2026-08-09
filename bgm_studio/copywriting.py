"""
動画ごとの説明文。

これを別ファイルに切り出している理由:

10本すべてを同じテンプレートに流し込むと、見出しも語順も全部同じになり、
外形が「テンプレート量産」そのものになる。YouTube の Inauthentic content
ポリシーで真っ先に引っかかるのがこの形なので、
**1本ずつ違う文章を人の手で書く**。

各説明文で守っていること:
  - 書き出しの型を全部変える（説明から入る / 情景から入る / 制作の話から入る）
  - 見出しの有無・数・文言をバラす
  - その曲固有の事実（楽器編成・BPM・キー・環境音）を必ず具体的に書く
  - 効能を断定しない（「不眠症が治る」等はポリシー違反かつ広告単価を下げる）
  - 末尾に「この動画のために制作した」という事実を書く（人の付加価値の明示）
"""

from __future__ import annotations

# {duration} は "2:24:00" に置換される
DESCRIPTIONS: dict[str, str] = {

    # ──────────────────────────────────────────────────────────
    "01_lofi_rainy_study": """\
Rain against the window, a Rhodes piano, and a drum kit that never quite
sits on the beat. {duration} of it.

I wrote this one for the hours where you have to keep going but don't
want to be pushed. The drums drag a little behind the click on purpose —
that lazy, slightly-late feel is most of what makes lo-fi sound like
lo-fi. Everything is run through tape saturation and a touch of wow and
flutter, so the pitch drifts by a fraction of a percent the way an old
cassette does.

78 BPM. A minor. Rhodes, sub bass, brushed drums, vinyl crackle,
and rain recorded low so it sits under the music instead of over it.

No sudden changes, no drops, nothing that will pull your eyes off the page.

Works well for: essays, revision, coding, long email afternoons.

— Every note and every frame in this video was made from scratch for this
channel. No sample packs, no stock footage.
""",

    # ──────────────────────────────────────────────────────────
    "02_deep_sleep_ambient": """\
{duration} of very slow, very quiet music for falling asleep to.

There is no melody here, and that is deliberate. A tune gives your brain
something to follow, and following is the opposite of what you want at
1am. Instead there are wide pads that take six seconds to fade in, a low
drone underneath them, and a singing bowl every few minutes — far enough
apart that you stop expecting the next one.

Almost everything above 7 kHz has been rolled off. Bright treble is what
keeps you awake; take it away and the same music feels like a warm room.

52 BPM · A minor · pads, drone, singing bowls, and light rain.

Mastered quietly and evenly, so nothing jumps out while you're drifting
off. Leave it running — it loops seamlessly and won't wake you at the join.

Not a medical treatment. Just music made to be easy to sleep through.

— Composed, mixed and mastered for this video.
""",

    # ──────────────────────────────────────────────────────────
    "03_piano_and_rain": """\
Piano and heavy rain, {duration}.

Recorded to feel like sitting near a window during a long evening
downpour. The rain is the loudest thing in the mix for a reason — the
piano wanders in and out of it rather than sitting on top. There is
distant thunder a few times an hour, low enough that you'll feel it more
than hear it.

The playing is deliberately unhurried: lots of rests, chords rolled
rather than struck together, nothing rushed toward a resolution.

62 BPM · key of C · piano, soft pad, rain, distant thunder.

Good for reading, writing, winding down, or sleeping through.

Two and a half hours, one continuous take, no gaps.

— All music and visuals in this video were created for this channel.
""",

    # ──────────────────────────────────────────────────────────
    "04_cozy_coffee_shop_jazz": """\
☕ COZY COFFEE SHOP JAZZ — {duration}

Warm jazz piano, upright bass, and brushed drums, with the murmur of a
café underneath.

▸ THE MIX
Piano plays rootless voicings — thirds and sevenths in the right hand,
the bass covering the root — which is most of why café jazz sounds the
way it does. The bass walks. The drums are brushes rather than sticks, so
there's no attack to distract you. Room noise, cups, and indistinct
conversation sit well below the music: enough to fill the silence,
never enough to make out words.

▸ SPECS
96 BPM · key of C · swing feel · piano, upright bass, brushes, café ambience

▸ USE IT FOR
Working, writing, studying, or as background in a shop or small café.

Runs {duration} and loops without a seam, so you can leave it going all day.

— Original composition. Nothing here is sampled or licensed from elsewhere.
""",

    # ──────────────────────────────────────────────────────────
    "05_bossa_nova_cafe": """\
Nylon-string guitar, upright bass and a shaker. {duration} of it.

Bossa nova is a strange thing to work to — it's cheerful without being
loud, and it moves without ever getting urgent. That's why it's been
playing in cafés for sixty years.

The guitar comps on the off-beats against a clave pattern; the bass
alternates root and fifth in that steady two-feel; a shaker keeps
everything moving. A Rhodes takes the melody now and then, softly.

124 BPM · key of G · nylon guitar, upright bass, shaker, Rhodes,
and a quiet café behind it all.

Best in the morning, or any time the room feels too silent.

— Written, played back and mastered from scratch for this channel.
""",

    # ──────────────────────────────────────────────────────────
    "06_healing_meditation_432": """\
{duration} of singing bowls and slow pads, tuned to A = 432 Hz.

A note on the tuning: 432 Hz is simply a slightly lower reference pitch
than the modern standard of 440 Hz — about a third of a semitone flat.
Some people prefer how it sits. It is a tuning choice, not a treatment,
and this video makes no health claims.

What's actually here: singing bowls whose overtones are deliberately
detuned against each other, so they beat slowly against one another —
that shimmer is the sound people describe as "healing". Underneath, a
drone and wide sus chords that avoid thirds entirely, which is what
keeps it floating instead of resolving. A harp adds a note every few bars.

48 BPM · D dorian · A = 432 Hz · bowls, drone, pads, harp.

For meditation, yoga, breathwork, or lying down in a dark room.

— Every sound in this video was synthesised for it. Nothing sampled.
""",

    # ──────────────────────────────────────────────────────────
    "07_fireplace_winter_jazz": """\
A fire, and a jazz trio playing quietly across the room. {duration}.

The fire is doing half the work here — a low burn with the occasional
crack and pop, mixed loud enough to be company. The music stays out of
its way: piano in the middle of the keyboard, walking bass, brushes,
and a celesta that comes in overhead now and then like something small
and bright catching the light.

88 BPM · key of F · piano, upright bass, brushes, celesta, crackling fire.

Warmer and slower than the café mixes on this channel. Made for December
evenings, long dinners, and the hour before bed.

Loops cleanly for {duration} — put it on and forget about it.

— Composed and mixed for this video. The fire is synthesised too.
""",

    # ──────────────────────────────────────────────────────────
    "08_ocean_waves_ambient": """\
Waves and a slow chord that takes half a minute to change. {duration}.

The sea here breaks about every eight and a half seconds. That interval
matters more than it sounds like it should — much faster and it becomes
restless, much slower and you start waiting for it. Low frequencies swell
with each set; the higher spray only appears at the moment a wave breaks.

Over the top: wide pads sitting low in the mix, and a celesta that
appears maybe twice a minute. Wind, faintly.

50 BPM · key of G · pads, celesta, ocean, wind.

Rolled off above 10 kHz so it stays soft at low volume — meant to be
played quietly, overnight, on a small speaker.

— All audio and visuals made from scratch for this channel.
""",

    # ──────────────────────────────────────────────────────────
    "09_fantasy_tavern": """\
🍺 MEDIEVAL TAVERN AMBIENCE — {duration}

A hearth, a low murmur of voices, and a harp somewhere in the corner.

This one is written in D dorian and deliberately avoids stacking thirds —
open fifths and fourths instead. That's the interval world of medieval
music, and it's why the same notes that would sound like pop in one
voicing sound like a tavern in another.

Instruments: harp arpeggios, nylon-string lute, upright bass, and a
fireplace. The crowd noise is formant-shaped rather than recorded speech,
so you can hear that people are there without ever making out a word —
which is exactly what you want when you're trying to concentrate.

84 BPM · D dorian · {duration} · seamless loop.

Made for: tabletop sessions, reading, writing, world-building,
long RPG evenings.

— Everything you hear was synthesised for this video. No sound libraries.
""",

    # ──────────────────────────────────────────────────────────
    "10_deep_focus_flow": """\
{duration} of ambient music with no melody in it at all.

That's the whole design. A tune, however quiet, gives you something to
track, and tracking it costs you exactly the attention you were trying to
protect. So there isn't one. What's here instead is a sustained chord
that changes every eight bars, a drone locked to the root, a marimba
pulse marking time, and a bed of brown noise underneath to cover the
sounds of wherever you happen to be.

Nothing arrives. Nothing resolves. It just keeps going.

60 BPM · A dorian · pads, drone, marimba, brown noise.
Rolled off above 11 kHz so it disappears into the background.

For deep work, exam revision, and long sessions where you need to not
notice the time passing.

— Written and produced from scratch for this channel.
""",
    "12_anime_piano_emotional": """\
{duration} of piano written the way anime themes are written.

The feeling in those songs isn't an accident of production — it comes
from the chord movement. Two progressions do most of the work here. The
first is the one Japanese songwriters call the ōdō, the "royal road":
IV–V–iii–vi. The move from the third chord to the fourth is where the
ache lives. The second is the Canon progression, where the bass walks
down step by step and the melody is free to drift over the top of it.

So this is built on those, in C major, and then left mostly alone. Piano
carries the melody, a soft string pad sits underneath, celesta adds a
little light in the high register, and nothing else gets in the way.
There are no drums and no rain — atmosphere would only blunt it.

76 BPM · C major · piano, strings, celesta, sub bass.

For studying, drawing, writing, long train rides, and the particular kind
of evening where you want to feel something quietly.

— Written and produced from scratch for this channel.
""",
    "13_fresh_morning_acoustic": """\
{duration} of acoustic music for the first part of the day.

Bright music goes wrong in a predictable way: it gets heavy. Pile on low
end and busy parts and "cheerful" turns into tiring by the second hour.
So the arrangement here stays deliberately thin. Nylon-string guitar
holds the chords, a marimba takes the melody, and there's a shaker
keeping a walking pace underneath. Everything below 55 Hz is cut, and the
mix is tilted slightly toward the top end to keep air in it.

The chords are built on add9 and maj9 shapes rather than plain triads —
open-sounding, unresolved, easy to leave running. The key is D major.

104 BPM · D major · nylon guitar, marimba, upright bass, shaker.

For mornings, commutes, cleaning the flat, opening a café, and work that
you'd rather not feel serious about.

— Written and produced from scratch for this channel.
""",
}


def get(slug: str, duration: str) -> str | None:
    """スラッグに対応する説明文を返す。無ければ None"""
    # ファイル名とキーの表記ゆれを吸収する
    key = slug if slug in DESCRIPTIONS else {
        "04_cozy_coffee_jazz": "04_cozy_coffee_shop_jazz",
    }.get(slug)
    if key is None:
        return None
    return DESCRIPTIONS[key].format(duration=duration)


# ──────────────────────────────────────────────────────────────
# Shorts 用のフック文言
#
# BGMチャンネル最大のボトルネックは登録者1,000人であり、
# それを突破する現実的な手段は Shorts しかない。
# Shorts は最初の2秒で「何の音か」が分からないと即スワイプされるので、
# 画面に出す文字は短く、用途を名詞で言い切る。
# ──────────────────────────────────────────────────────────────

SHORT_HOOKS: dict[str, list[str]] = {
    "01_lofi_rainy_study": [
        "rain on the window\nand a rhodes piano",
        "lo-fi for the\nlast hour of studying",
        "the drums are late\non purpose",
    ],
    "02_deep_sleep_ambient": [
        "no melody.\nnothing to follow.",
        "everything above 7kHz\nis gone. that's the trick.",
        "for the nights\nyou can't switch off",
    ],
    "03_piano_and_rain": [
        "piano, and rain\nlouder than the piano",
        "for reading\non a wet evening",
        "there's thunder\nif you wait for it",
    ],
    "04_cozy_coffee_jazz": [
        "a café that never\ncloses",
        "piano, upright bass,\nbrushes. that's all.",
        "you can hear people.\nyou can't hear words.",
    ],
    "05_bossa_nova_cafe": [
        "bossa nova for\nslow mornings",
        "nylon guitar\nand a shaker",
        "cheerful without\nbeing loud",
    ],
    "06_healing_meditation_432": [
        "singing bowls,\ntuned to 432 Hz",
        "that shimmer is two\nnotes beating together",
        "for lying down\nin a dark room",
    ],
    "07_fireplace_winter_jazz": [
        "a fire, and a jazz trio\nacross the room",
        "december evenings",
        "the fire is doing\nhalf the work",
    ],
    "08_ocean_waves_ambient": [
        "waves every\n8.5 seconds",
        "play it quietly,\novernight",
        "one chord.\nhalf a minute to change.",
    ],
    "09_fantasy_tavern": [
        "a hearth, and a harp\nin the corner",
        "for tabletop nights",
        "open fifths.\nno thirds. medieval.",
    ],
    "10_deep_focus_flow": [
        "no melody, on purpose",
        "nothing arrives.\nnothing resolves.",
        "for the long\nrevision sessions",
    ],
}

# Shorts の説明文。長尺へ誘導するのが唯一の目的なので短くする。
SHORT_DESCRIPTION = """\
{hook}

Full {duration} version on the channel — no ads mid-track, seamless loop.

#{tag1} #{tag2} #shorts
"""


DESCRIPTIONS["11_sleep_city_8h"] = """\
Eight hours. Enough for a whole night.

This is the long one. Most sleep mixes stop after two or three hours and
leave you in silence at 4am — this doesn't. Put it on when you get into
bed and it will still be going when your alarm does.

It's built the same way as the shorter sleep mix on this channel, but
slower and in a different key: 46 BPM, D minor, and the chords hold for
four bars at a time before they move. Wide pads, a drone underneath, and
a singing bowl every few minutes. Nothing above 7 kHz, so there's no
treble to keep you alert.

The picture is a city at night from across the water, because that is
what most of us actually fall asleep near.

46 BPM · D minor · {duration} · seamless loop, no gaps.

Not a medical treatment — just music designed to be easy to sleep through.

— A different composition from the two-hour sleep mix on this channel.
  Written and produced from scratch, like everything else here.
"""

SHORT_HOOKS["11_sleep_city_8h"] = [
    "eight hours.\nenough for a whole night.",
    "most sleep mixes leave you\nin silence at 4am",
    "46 BPM. nothing\nabove 7 kilohertz.",
]

SHORT_HOOKS["12_anime_piano_emotional"] = [
    "the chord that makes\nanime openings hurt",
    "IV–V–iii–vi.\nthat's the whole feeling.",
    "piano, strings,\nand nothing else",
]

SHORT_HOOKS["13_fresh_morning_acoustic"] = [
    "music for the first\nhour of the day",
    "nylon guitar\nand a marimba",
    "bright without\ngetting heavy",
]

DESCRIPTIONS["14_japanese_lofi_koto"] = """\
{duration} of lo-fi built around a koto.

The koto is tuned to hirajōshi, the five-note scale that makes Japanese
music sound Japanese — leave that scale and you just have lo-fi with an
unusual guitar. Under it: a slow boom-bap beat with the drums dragged
behind the click, sub bass, tape flutter, vinyl crackle, and rain against
a window somewhere behind everything.

The pitch of the koto bends slightly upward at each pluck and settles,
the way a real string does under a plectrum. That detail is most of the
instrument's character, so it's synthesised rather than faked with a
sample.

72 BPM · A hirajōshi · koto, sub bass, lo-fi kit, rain, vinyl.

For studying, late trains, rainy evenings, and long focused work.

— Composed and produced from scratch for this channel.
"""

DESCRIPTIONS["15_rain_thunder_night"] = """\
{duration} of heavy rain on a window, with thunder far away.

There is almost no music in this one, on purpose. A low chord drifts
underneath — quiet enough that you will probably never notice it, present
enough that the room never feels empty. Everything above 8 kHz is rolled
off, because bright rain is what keeps light sleepers awake.

The thunder never cracks. It stays distant, a few times an hour, more
felt than heard.

Rain, distant thunder, wind, and one very quiet chord.
Mastered softly and evenly for overnight playback — it loops without a
seam, so the storm never ends until you stop it.

For sleeping, and for pretending you don't have to go outside.

— The rain, thunder and wind are all synthesised for this video.
"""

DESCRIPTIONS["16_autumn_cafe_jazz"] = """\
🍂 AUTUMN CAFÉ JAZZ — {duration}

Slow jazz for the months when it gets dark early.

▸ WHAT'S PLAYING
Piano comping rootless voicings, a Rhodes taking the tunes, an upright
bass walking underneath, and brushes keeping everything at a murmur.
It swings, but at 80 BPM nothing is in a hurry. Wind moves outside;
a café murmurs quietly behind the band.

▸ SPECS
80 BPM · B♭ major · piano, Rhodes, upright bass, brushes, wind, café room

▸ GOOD FOR
October afternoons, rainy commutes, essays, bookshops, and the first
cold week where the coat comes out.

Plays for {duration} and loops cleanly.

— Original music, written and mixed for this channel.
"""

DESCRIPTIONS["17_christmas_jazz"] = """\
🎄 CHRISTMAS JAZZ — {duration}

Cozy holiday jazz by a synthesised fireplace.

A note on what this is: there are no carols here. Every tune is original.
What makes it sound like Christmas is the harmony — the maj6 chords and
that one sweet dominant-with-a-flat-nine that every December record from
the 1950s leans on — plus sleigh bells shaken softly on the off-beats and
a celesta glittering over the top like tinsel.

Piano, upright bass and brushes do the rest, the same warm trio sound as
the café mixes on this channel, just pointed at the holidays.

92 BPM · C major · piano, celesta, upright bass, brushes, sleigh bells,
and a fire crackling in the corner.

For wrapping presents, cooking too much food, reading by the tree, and
keeping the house warm through December.

— All original compositions. No licensed or traditional melodies.
"""

SHORT_HOOKS["14_japanese_lofi_koto"] = [
    "a koto,\nand a beat that drags",
    "five notes.\nthat's all japan needs.",
    "lofi, but the strings\nare four centuries old",
]

SHORT_HOOKS["15_rain_thunder_night"] = [
    "rain on the window.\nthunder far away.",
    "the storm never ends\nuntil you stop it",
    "no melody.\njust weather.",
]

SHORT_HOOKS["16_autumn_cafe_jazz"] = [
    "jazz for the months\nthat get dark early",
    "80 BPM.\nnothing is in a hurry.",
    "the coat-weather\nplaylist",
]

SHORT_HOOKS["17_christmas_jazz"] = [
    "christmas jazz,\nno carols needed",
    "sleigh bells on\nthe off-beats",
    "december, by\nthe fireplace",
]
