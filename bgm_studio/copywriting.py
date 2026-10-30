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

DESCRIPTIONS["18_starship_sleep"] = """\
{duration} inside the sleeping quarters of a starship.

The engine is somewhere below deck — a deep, steady hum you feel more
than hear. Air moves through the vents. Nothing beeps. Nothing changes.
That's the entire point: the most reliable sleep sounds are the ones a
building (or a ship) makes on its own.

Under the hull noise there are two very low drones, slightly detuned so
they beat against each other about once every few seconds, like the
engines are breathing. Everything above 6.5 kHz is removed.

For sleeping, night shifts, long-haul flights, and imagining you are
somewhere between two stars.

— The engine, the air and the hum are all synthesised for this video.
"""

DESCRIPTIONS["19_528hz_love_frequency"] = """\
{duration} tuned so that C is exactly 528.0 Hz.

A note on honesty, because this genre has a problem with it: many
"528Hz" videos are ordinary music with a label on it. This one is
actually tuned — the whole piece is played at A = 444 Hz, which places
C5 at precisely 528.0 Hz, and a soft drone holds that C through the
entire runtime. If you check it with a spectrum analyser, you will find
the peak where the title says it is.

What you'll hear: slow golden pads, singing bowls a few minutes apart,
and that steady 528 Hz centre. No melody, no percussion.

We make no medical claims about tuning frequencies. Some people find
this pitch particularly warm to rest inside — that's all, and it's enough.

For meditation, massage, reading, and falling asleep.

— Composed and synthesised for this channel, at pitch.
"""

DESCRIPTIONS["20_focus_40hz"] = """\
{duration} of ambient with a 40 Hz pulse folded into it.

Gamma-band stimulation is an area of active research, and this video
makes no health claims. What it offers is simpler: a very steady,
featureless soundscape whose loudness ripples 40 times per second —
deep enough to be present, shallow enough that most people stop
noticing it within a minute. Unlike binaural beats, an amplitude pulse
survives speakers, mono phones, and cheap earbuds.

Underneath: slow dorian pads, a drone, a marimba note here and there,
and a brown-noise floor. No melody to follow, nothing to wait for.

60 BPM · A dorian · pads, drone, marimba, brown noise, 40 Hz pulse.

For deep work, long reading, and code that refuses to compile.

— Original composition, synthesised for this channel.
"""

DESCRIPTIONS["21_halloween_night"] = """\
🎃 HALLOWEEN NIGHT AMBIENCE — {duration}

An October night on a hill: wind in the dead leaves, crickets that
haven't noticed the cold yet, a far-off roll of thunder once or twice,
and a music box playing something in a minor key that never quite
resolves.

This is spooky, not scary — made to sit under a Halloween party, a
carving session, or an evening of horror reading without ever jump-scaring
anyone. The dissonances are gentle and the wind does most of the work.

66 BPM · A harmonic minor · music-box celesta, low pads, distant bell,
wind, night insects, far thunder.

Runs {duration} and loops seamlessly — set it playing at dusk and forget it.

— All sounds synthesised for this video. No sound-effect libraries.
"""

DESCRIPTIONS["22_snowstorm_fireplace"] = """\
Outside: a blizzard. Inside: a fire. {duration} of both.

The pleasure of a snowstorm video is the contrast — the louder the wind
howls, the warmer the room feels. So the wind here is layered twice
(a far roar and a near gust against the window) and the fireplace sits
just underneath it, popping now and then to remind you it's still lit.
A quiet chord drifts below everything, more felt than heard.

Everything above 8.5 kHz is rolled off, so the storm never hisses.

For sleeping through winter nights, reading under a blanket, and
being smug about not being outside.

— Wind, fire and music all synthesised for this channel.
"""

DESCRIPTIONS["23_forest_night_camp"] = """\
A campfire in a dark forest, {duration} long.

Crickets on all sides, wood crackling at your feet, wind high in the
trees, and — every few minutes — a few notes from a harp, as if someone
across the fire is half-playing, half-dozing. That's the whole scene.

Built to serve two audiences at once: tabletop parties who need a
wilderness camp that runs all session, and people who simply fall
asleep faster outdoors than indoors.

50 BPM · D dorian · harp, soft pads, campfire, crickets, wind.

For D&D rests, reading fantasy, and sleeping under imaginary stars.

— Every sound synthesised from scratch. No field recordings.
"""

DESCRIPTIONS["24_deep_space_drone"] = """\
{duration} of dark ambient for the middle of nowhere.

Vast, slow, and mostly empty. A drone at the bottom of the range, pads
that take ten seconds to arrive and twelve to leave, a bowl struck
somewhere far away every minute or so, and a shimmer of high harmonics
so the darkness never turns to mud. The reverb is tuned to be
implausibly large — about ten seconds of tail — because the size of the
space is the instrument here.

Nothing threatening happens. Dark ambient for sleeping, not for horror.

40 BPM · E minor · drones, pads, bowls, celesta, deep-space reverb.

For sleep, night trains, long flights, and staring out of windows.

— Composed and synthesised for this channel.
"""

DESCRIPTIONS["25_cyberpunk_rain"] = """\
Rain on neon, {duration}.

A synth arpeggio that never hurries, two chords that never resolve, a
sub-bass pulse, and rain that isn't sad — just weather in a city that
stopped sleeping years ago. There's tape wobble on everything, because
the future imagined in 1982 sounds better than the real one.

86 BPM · A minor · analog-style synths, sub bass, rain, distant thunder.

For coding, night shifts, driving after midnight, and open-world games
with the game music turned off.

— All synths programmed and rendered for this video.
"""

DESCRIPTIONS["26_dark_academia_library"] = """\
🕯️ DARK ACADEMIA LIBRARY — {duration}

An old reading room after hours. A grandfather clock ticks once per
second — exactly; the piece is written at 60 BPM so the clock and the
music share a pulse. A melancholy piano works through minor-key
changes, rain streaks the tall windows, and a fire settles in the
grate. Every hour or so you may notice the clock's tick land a little
heavier; that's the only event in the entire video.

60 BPM · A minor · piano, upright bass, string pad, clock, rain, fire.

For essays, thesis chapters, translation, and reading dead languages
by candlelight.

— Original music, synthesised and mixed for this channel.
"""

DESCRIPTIONS["27_rain_black_screen"] = """\
{duration} of gentle night rain. The screen stays black.

No visuals, no logo, no brightness in a dark bedroom — the video is a
black frame from the first second to the last, which is the point.
Phone face-down not required.

The rain itself is soft: window-filtered, no thunder, with the barest
low chord underneath so the room never feels empty. Mastered quietly
and evenly, with everything above 8 kHz rolled away.

Put it on, screen off or on — the room stays dark either way.

For sleep. That's it. Good night.

— The rain is synthesised, original, and loops without a seam.
"""

SHORT_HOOKS["18_starship_sleep"] = [
    "sleep like you're\nbetween two stars",
    "the engine hum\nis the lullaby",
    "night shift?\nthis is your bunk.",
]
SHORT_HOOKS["19_528hz_love_frequency"] = [
    "check it with a\nspectrum app. it's real.",
    "C = exactly 528.0 Hz\nnot just the title",
    "tuned to A = 444,\nso C lands on 528",
]
SHORT_HOOKS["20_focus_40hz"] = [
    "40 pulses per second.\nyou'll stop hearing them.",
    "works on speakers,\nunlike binaural beats",
    "nothing to follow.\nthat's the feature.",
]
SHORT_HOOKS["21_halloween_night"] = [
    "spooky,\nnot scary",
    "a music box\nthat never resolves",
    "october,\nbottled",
]
SHORT_HOOKS["22_snowstorm_fireplace"] = [
    "the louder the wind,\nthe warmer the room",
    "blizzard outside.\nyou're not in it.",
    "winter, from\nthe right side of glass",
]
SHORT_HOOKS["23_forest_night_camp"] = [
    "your party rests\nhere tonight",
    "crickets, fire,\nand a lazy harp",
    "fall asleep\noutdoors, indoors",
]
SHORT_HOOKS["24_deep_space_drone"] = [
    "dark ambient,\nnot horror",
    "a reverb the size\nof a nebula",
    "for the middle\nof nowhere",
]
SHORT_HOOKS["25_cyberpunk_rain"] = [
    "rain on neon,\ntwo chords, no hurry",
    "the future from 1982\nsounds better",
    "for coding\nafter midnight",
]
SHORT_HOOKS["26_dark_academia_library"] = [
    "the clock ticks\nexactly on the beat",
    "60 BPM. one tick\nper second. on purpose.",
    "essays due?\nlight the candle.",
]
SHORT_HOOKS["27_rain_black_screen"] = [
    "black screen.\nrain. that's it.",
    "your room\nstays dark",
    "no logo, no light,\njust rain",
]


# ──────────────────────────────────────────────────────────────
# 童謡・子守唄シリーズ (n01-n10)
# 旋律は全てパブリックドメインの伝承曲/古典。他人の録音・編曲は使っていない。
# 音は合成。効能は謳わない (調律は「やわらかく聞こえる選択」とだけ書く)。
# ──────────────────────────────────────────────────────────────

DESCRIPTIONS["g01_gentle_piano_sleep"] = """\
🌙 SLEEP PIANO — {duration} of gentle piano, with no rain and no noise

Most sleep music comes with rain, wind or white noise underneath. This one
doesn't. It's only a soft, felt-like piano, a quiet pad, and once in a while a
single music-box note — nothing else, from the first second to the last.

The melody is slow and comes back the way a song does, so your ear always knows
where it is and has nothing to follow or wait for. The tempo is a resting 58
beats a minute, the dynamics stay low, and there are no sudden changes.

▸ No rain, no ambience, no hiss — only the instruments and their reverb
▸ Same calm pace for the whole {duration}
▸ Loops seamlessly, so you can let it play through the night

For falling asleep, staying asleep, reading in bed, or a quiet room.

— Composed, arranged and animated for this channel.
"""

# 童謡は 2026-10-26 に作り直した (無音・転調・硬い音を解消し、1 時間・新映像に)。
# 説明文は実際の内容と食い違わないことを最優先に書き直した:
#   楽器はやわらかいピアノとオルゴールだけ / 調とテンポは最後まで同じ /
#   やさしい 4 つの弾き方を 2 コーラスずつ回す / 映像はオリジナルキャラ Luna。

DESCRIPTIONS["g02_deep_sleep_piano"] = """\
🌙 DEEP SLEEP PIANO — {duration} of calm piano, with no rain and no noise

The second in our Sleep Piano series, slower than the first: 54 beats a minute,
long chords that change only every few bars, and a melody that returns like a
song you already know. A soft piano and a quiet pad, with an occasional
music-box note — and nothing else. No rain, no wind, no white noise.

▸ No ambience layer of any kind — only instruments and their reverb
▸ Same low, even dynamics for the whole {duration}
▸ Loops seamlessly through the night

For falling asleep, staying asleep, and quiet late nights.

— Composed, arranged and animated for this channel.
"""

DESCRIPTIONS["g03_emotional_sleep_piano"] = """\
🌙 BEAUTIFUL SLEEP PIANO — {duration} of gentle, emotional piano

The third in our Sleep Piano series. This one uses the warm, slightly
bittersweet chord changes you hear in Japanese film and anime soundtracks,
slowed right down for sleep. The melody is soft and comes back again and again,
so there is always something familiar to hold on to and nothing to wait for.

▸ Soft piano and a quiet pad — no rain, no ambience, no hiss
▸ A steady, resting 60 beats a minute
▸ Loops seamlessly for the whole {duration}

For bedtime, reading in bed, or a calm evening.

— Composed, arranged and animated for this channel.
"""

DESCRIPTIONS["n11_lullaby_medley"] = """\
🌙 10 LULLABIES FOR BABIES — {duration}, one song after another

Ten of the best-known lullabies and nursery songs, each played for about twelve
minutes on a soft piano and a music box, while Luna, our sleepy little moon,
rocks gently among the stars.

00:00 Twinkle, Twinkle, Little Star
12:00 Mary Had a Little Lamb
24:00 Row, Row, Row Your Boat
36:00 Frère Jacques
48:00 London Bridge
1:00:00 Old MacDonald Had a Farm
1:12:00 Au Clair de la Lune
1:24:00 Ode to Joy
1:36:00 Silent Night
1:48:00 Jingle Bells

Every song stays in one key and one calm tempo, and moves gently into the next.
There is no background noise anywhere — no rain, no hiss, no room tone.
Tuned to A = 432 Hz, a slightly lower reference pitch (a tuning choice, not a
treatment; no health claims are made).

All melodies are traditional or in the public domain. Arrangement, sound and
animation are made for this channel.
"""

DESCRIPTIONS["n01_twinkle_lullaby_musicbox"] = """\
🎵 TWINKLE, TWINKLE, LITTLE STAR — {duration} of music box lullaby

The same gentle lullaby as our piano version, played this time on a music box,
high and soft like the little tune inside a toy, with a quiet piano underneath.
It stays in one key and one calm tempo the whole way through, with nothing
sudden and no background noise of any kind — a kitten asleep by a moonlit window sets the mood.

▸ Music box melody with a soft piano — no rain, no hiss
▸ Tuned to A = 432 Hz (a softer reference pitch; no health claims)
▸ Traditional melody; arrangement and sound made for this channel

For bedtime, naptime, and quiet evenings.
"""

DESCRIPTIONS["n02_mary_lamb_lullaby_musicbox"] = """\
🎵 MARY HAD A LITTLE LAMB — {duration} of music box lullaby

The same gentle lullaby as our piano version, played this time on a music box,
high and soft like the little tune inside a toy, with a quiet piano underneath.
It stays in one key and one calm tempo the whole way through, with nothing
sudden and no background noise of any kind — a lamb asleep under a big tree sets the mood.

▸ Music box melody with a soft piano — no rain, no hiss
▸ Tuned to A = 432 Hz (a softer reference pitch; no health claims)
▸ Traditional melody; arrangement and sound made for this channel

For bedtime, naptime, and quiet evenings.
"""

DESCRIPTIONS["n03_row_your_boat_lullaby_musicbox"] = """\
🎵 ROW, ROW, ROW YOUR BOAT — {duration} of music box lullaby

The same gentle lullaby as our piano version, played this time on a music box,
high and soft like the little tune inside a toy, with a quiet piano underneath.
It stays in one key and one calm tempo the whole way through, with nothing
sudden and no background noise of any kind — a duckling asleep in a little boat sets the mood.

▸ Music box melody with a soft piano — no rain, no hiss
▸ Tuned to A = 432 Hz (a softer reference pitch; no health claims)
▸ Traditional melody; arrangement and sound made for this channel

For bedtime, naptime, and quiet evenings.
"""

DESCRIPTIONS["n04_frere_jacques_lullaby_musicbox"] = """\
🎵 FRÈRE JACQUES — {duration} of music box lullaby

The same gentle lullaby as our piano version, played this time on a music box,
high and soft like the little tune inside a toy, with a quiet piano underneath.
It stays in one key and one calm tempo the whole way through, with nothing
sudden and no background noise of any kind — a bunny asleep by a village window sets the mood.

▸ Music box melody with a soft piano — no rain, no hiss
▸ Tuned to A = 432 Hz (a softer reference pitch; no health claims)
▸ Traditional melody; arrangement and sound made for this channel

For bedtime, naptime, and quiet evenings.
"""


# 2026-10-30 クリスマス曲のまとめ版
DESCRIPTIONS["x01_christmas_piano"] = """\
🎄 CHRISTMAS PIANO — {duration} of soft Christmas carols

Ten of the best-loved Christmas carols, played slowly and gently on a real piano,
about twelve minutes each, while snow drifts past a warm, glowing window.

00:00 We Wish You a Merry Christmas
12:00 Silent Night
24:00 Jingle Bells
36:00 O Christmas Tree
48:00 Deck the Halls
1:00:00 Away in a Manger
1:12:00 Joy to the World
1:24:00 The First Noel
1:36:00 Hark! The Herald Angels Sing
1:48:00 O Come, All Ye Faithful

▸ Soft piano only — no rain, no crackle, no background noise
▸ Every carol stays in one calm tempo, then moves gently into the next
▸ Tuned to A = 432 Hz, a slightly lower, warmer reference pitch (a tuning choice;
  no health claims are made)
▸ All melodies are traditional or in the public domain. Arrangement and sound
  made for this channel.

For Christmas dinner, wrapping presents, reading by the tree, or a quiet winter evening.
"""

DESCRIPTIONS["x02_christmas_musicbox"] = """\
🎁 CHRISTMAS MUSIC BOX — {duration} of Christmas carols

Ten of the best-loved Christmas carols, played on a music box, high and soft like
the little tune inside a snow globe, with a quiet piano underneath. About twelve
minutes each.

00:00 We Wish You a Merry Christmas
12:00 Silent Night
24:00 Jingle Bells
36:00 O Christmas Tree
48:00 Deck the Halls
1:00:00 Away in a Manger
1:12:00 Joy to the World
1:24:00 The First Noel
1:36:00 Hark! The Herald Angels Sing
1:48:00 O Come, All Ye Faithful

▸ Music box with a soft piano — no rain, no crackle, no background noise
▸ Every carol stays in one calm tempo, then moves gently into the next
▸ Tuned to A = 432 Hz, a slightly lower, warmer reference pitch (a tuning choice;
  no health claims are made)
▸ All melodies are traditional or in the public domain. Arrangement and sound
  made for this channel.

For Christmas Eve, decorating the tree, bedtime in December, or a cozy winter night.
"""

# 2026-10-29 海外でよく知られた子守唄 (ピアノ版とオルゴール版)
DESCRIPTIONS["n12_brahms_lullaby"] = """\
🌙 BRAHMS' LULLABY — {duration} of soft piano lullaby

Brahms' Lullaby ("Lullaby and Goodnight"), played slowly on a real, gently-played piano.
Johannes Brahms wrote this cradle song in 1868, and it is still the tune most
parents around the world hum at bedtime.

Luna, our sleepy little moon, rocks softly among the stars. The tune stays in one
key and one calm tempo the whole way through, with nothing sudden and no
background noise of any kind.

▸ Soft piano only — no rain, no hiss, no room tone
▸ Loops seamlessly for the whole {duration}
▸ Tuned to A = 432 Hz (a softer reference pitch; no health claims)
▸ Music by Johannes Brahms (1868), in the public domain. Arrangement and sound made for this channel.

For bedtime, naptime, and quiet evenings.
"""

DESCRIPTIONS["n12_brahms_lullaby_musicbox"] = """\
🎵 BRAHMS' LULLABY — {duration} of music box lullaby

Brahms' Lullaby ("Lullaby and Goodnight"), played on a music box, high and soft like the little tune inside a toy,
with a quiet piano underneath.
Johannes Brahms wrote this cradle song in 1868, and it is still the tune most
parents around the world hum at bedtime.

It stays in one key and one calm tempo the whole way through, with nothing
sudden and no background noise of any kind.

▸ Music box melody with a soft piano — no rain, no hiss
▸ Loops seamlessly for the whole {duration}
▸ Tuned to A = 432 Hz (a softer reference pitch; no health claims)
▸ Music by Johannes Brahms (1868), in the public domain. Arrangement and sound made for this channel.

For bedtime, naptime, and quiet evenings.
"""

DESCRIPTIONS["n13_rockabye_baby"] = """\
🌙 ROCK-A-BYE BABY — {duration} of soft piano lullaby

"Rock-a-bye Baby", played slowly on a real, gently-played piano.
A gentle rocking lullaby in a slow, swaying rhythm, sung to babies in English
for well over a century.

Luna, our sleepy little moon, rocks softly among the stars. The tune stays in one
key and one calm tempo the whole way through, with nothing sudden and no
background noise of any kind.

▸ Soft piano only — no rain, no hiss, no room tone
▸ Loops seamlessly for the whole {duration}
▸ Tuned to A = 432 Hz (a softer reference pitch; no health claims)
▸ Traditional melody, in the public domain. Arrangement and sound made for this channel.

For bedtime, naptime, and quiet evenings.
"""

DESCRIPTIONS["n13_rockabye_baby_musicbox"] = """\
🎵 ROCK-A-BYE BABY — {duration} of music box lullaby

"Rock-a-bye Baby", played on a music box, high and soft like the little tune inside a toy,
with a quiet piano underneath.
A gentle rocking lullaby in a slow, swaying rhythm, sung to babies in English
for well over a century.

It stays in one key and one calm tempo the whole way through, with nothing
sudden and no background noise of any kind.

▸ Music box melody with a soft piano — no rain, no hiss
▸ Loops seamlessly for the whole {duration}
▸ Tuned to A = 432 Hz (a softer reference pitch; no health claims)
▸ Traditional melody, in the public domain. Arrangement and sound made for this channel.

For bedtime, naptime, and quiet evenings.
"""

DESCRIPTIONS["n14_amazing_grace_lullaby"] = """\
🌙 AMAZING GRACE — {duration} of soft piano lullaby

"Amazing Grace", played slowly on a real, gently-played piano.
One of the best-loved melodies in the English-speaking world, slowed down
into a quiet lullaby.

Luna, our sleepy little moon, rocks softly among the stars. The tune stays in one
key and one calm tempo the whole way through, with nothing sudden and no
background noise of any kind.

▸ Soft piano only — no rain, no hiss, no room tone
▸ Loops seamlessly for the whole {duration}
▸ Tuned to A = 432 Hz (a softer reference pitch; no health claims)
▸ Traditional melody ("New Britain", 1829), in the public domain. Arrangement and sound made for this channel.

For bedtime, naptime, and quiet evenings.
"""

DESCRIPTIONS["n14_amazing_grace_lullaby_musicbox"] = """\
🎵 AMAZING GRACE — {duration} of music box lullaby

"Amazing Grace", played on a music box, high and soft like the little tune inside a toy,
with a quiet piano underneath.
One of the best-loved melodies in the English-speaking world, slowed down
into a quiet lullaby.

It stays in one key and one calm tempo the whole way through, with nothing
sudden and no background noise of any kind.

▸ Music box melody with a soft piano — no rain, no hiss
▸ Loops seamlessly for the whole {duration}
▸ Tuned to A = 432 Hz (a softer reference pitch; no health claims)
▸ Traditional melody ("New Britain", 1829), in the public domain. Arrangement and sound made for this channel.

For bedtime, naptime, and quiet evenings.
"""

DESCRIPTIONS["n15_all_through_the_night"] = """\
🌙 ALL THROUGH THE NIGHT — {duration} of soft piano lullaby

"All Through the Night" ("Ar Hyd y Nos"), played slowly on a real, gently-played piano.
A tender old Welsh lullaby, sung around the world in English as
"All Through the Night".

Luna, our sleepy little moon, rocks softly among the stars. The tune stays in one
key and one calm tempo the whole way through, with nothing sudden and no
background noise of any kind.

▸ Soft piano only — no rain, no hiss, no room tone
▸ Loops seamlessly for the whole {duration}
▸ Tuned to A = 432 Hz (a softer reference pitch; no health claims)
▸ Traditional Welsh melody (first printed 1784), in the public domain. Arrangement and sound made for this channel.

For bedtime, naptime, and quiet evenings.
"""

DESCRIPTIONS["n15_all_through_the_night_musicbox"] = """\
🎵 ALL THROUGH THE NIGHT — {duration} of music box lullaby

"All Through the Night" ("Ar Hyd y Nos"), played on a music box, high and soft like the little tune inside a toy,
with a quiet piano underneath.
A tender old Welsh lullaby, sung around the world in English as
"All Through the Night".

It stays in one key and one calm tempo the whole way through, with nothing
sudden and no background noise of any kind.

▸ Music box melody with a soft piano — no rain, no hiss
▸ Loops seamlessly for the whole {duration}
▸ Tuned to A = 432 Hz (a softer reference pitch; no health claims)
▸ Traditional Welsh melody (first printed 1784), in the public domain. Arrangement and sound made for this channel.

For bedtime, naptime, and quiet evenings.
"""

DESCRIPTIONS["n01_twinkle_lullaby"] = """\
{duration} of "Twinkle, Twinkle, Little Star", played softly on piano and music box.

Luna, our sleepy little moon, rocks gently in her nightcap while the stars
twinkle around her. The tune is played slowly and stays in the same key and
the same calm tempo from start to finish, so nothing changes suddenly and
nothing wakes anyone up. Every couple of verses the sound shifts a little —
piano, then music box, then piano with slow broken chords — and that's all.

There is no background noise in this recording: no hiss, no rain, no room
tone. Just the two instruments and a little reverb. Tuned to A = 432 Hz, a
slightly lower reference pitch than the usual 440 Hz — a tuning choice, not a
treatment, and no health claims are made.

For bedtime, naptime, and quiet afternoons.

— Traditional melody. Arrangement, sound and animation made for this channel.
"""

DESCRIPTIONS["n02_mary_lamb_lullaby"] = """\
Mary had a little lamb, and for {duration} she has a very quiet piano with her.

A short, friendly tune that is easy to follow and easy to fall asleep to,
played slowly on a soft piano and a music box under a sleepy moon. The key and
the tempo never change, and the accompaniment is either a quiet pad or a few
slow notes per bar. Nothing sudden, nothing loud, and no background noise of
any kind.

A = 432 Hz tuning (a softer reference pitch — a tuning choice, not a treatment).
The song is traditional; the performance and animation are made for this channel.

Good for naptime, a calm play corner, and the last ten minutes before lights-out.
"""

DESCRIPTIONS["n03_row_your_boat_lullaby"] = """\
🚣 ROW, ROW, ROW YOUR BOAT — {duration} (calm piano version)

The nursery rhyme slowed right down, with the little rocking feel of its 6/8
rhythm kept intact. A soft piano carries the tune and a music box takes over
now and then, always in the same key and at the same gentle pace.

▸ Clean sound: no hiss, no ambience layer, no noise floor — only instruments.
▸ Tuning: A = 432 Hz (a softer reference pitch, no health claims).
▸ Tune: traditional. Sound, arrangement and animation: made for this channel.

For rocking to sleep, quiet bath-time, and car rides.
"""

DESCRIPTIONS["n04_frere_jacques_lullaby"] = """\
Frère Jacques, sung by no one: {duration} of it, on soft piano and music box.

The round is one of the oldest tunes anyone still hums, which is why it works
without lyrics — every parent already knows the words. Here it goes slowly,
with quiet chords underneath, and with nothing in the background but the
instruments themselves. The key and tempo stay the same the whole way through.

Tuned to A = 432 Hz. Traditional melody; arrangement, sound and animation
original to this channel.

Use it for settling down, reading time, or calm background at home.
"""

DESCRIPTIONS["n05_london_bridge_lullaby"] = """\
🌉 LONDON BRIDGE IS FALLING DOWN — {duration} of music-box and piano lullaby

The old game-song, with the game taken out. Eight bars, played slowly and
evenly on a music box and a soft piano, with chords chosen to follow the tune
and land on a quiet C at the end of every phrase. Same key, same tempo, no
surprises.

▸ No background noise at all
▸ A = 432 Hz, a softer-sounding reference pitch
▸ Traditional melody, original sound and animation

For naps, calm-down corners, and quiet rooms.
"""

DESCRIPTIONS["n06_old_macdonald_lullaby"] = """\
Old MacDonald, with the animals asleep. {duration}.

The famous farm song is much calmer than it sounds when sung loudly. Played
slowly on a soft piano and a music box, it works as an easy, familiar
background for winding down — the E-I-E-I-O turn is a natural place to breathe.

No noise layer, no effects, nothing sudden. A = 432 Hz.
Traditional song; sound, arrangement and animation made for this channel.
"""

DESCRIPTIONS["n07_au_clair_lullaby"] = """\
"Au clair de la lune" — {duration} by moonlight.

A French lullaby from the eighteenth century, simple enough to be played with
one finger and gentle enough to play for an hour. Here it moves between a music
box and a soft piano, with a short breath between verses so the room has time
to settle. There is no hiss and no background sound; the only thing you'll hear
is the instruments and their reverb.

Tuned to A = 432 Hz. Traditional melody; sound, arrangement and animation
original to this channel.

For late evenings, early mornings, and candle-light.
"""

DESCRIPTIONS["n08_silent_night_lullaby"] = """\
🎄 SILENT NIGHT — {duration} of soft piano for a peaceful Christmas night

The carol at its slowest, in a calm 3-beat sway, played on a soft piano and a
music box. It's quiet enough for a nursery and plain enough for a living room,
and there is no background noise, just the instruments.

Traditional melody (public domain). All sound, arrangement and animation are
original to this channel. Tuned to A = 432 Hz, a softer-sounding reference
pitch — a tuning choice, nothing more.

For putting children to bed on Christmas Eve, wrapping presents, and the quiet
part of the evening.
"""

DESCRIPTIONS["n09_ode_to_joy_lullaby"] = """\
Beethoven's "Ode to Joy" as a music box lullaby. {duration}.

Normally a tune of triumph, it turns out to be very gentle when you slow it
down and play it on a music box and a soft piano: the melody barely moves, and
the sound stays warm. Same key and tempo from start to finish.

No hiss, no ambience, no added noise. A = 432 Hz, a softer reference pitch.
Beethoven's melody is in the public domain; this performance and animation are
made for this channel.
"""

DESCRIPTIONS["n10_jingle_bells_lullaby"] = """\
❄️ JINGLE BELLS, SLOWED DOWN — {duration} of piano for a cozy winter evening

The bells and the sleigh are gone; what's left is the melody, played gently on
a soft piano and a music box. It's the version for after the presents are
opened and everyone's a bit tired.

▸ Traditional tune (public domain), original arrangement, sound and animation
▸ No background noise of any kind
▸ A = 432 Hz tuning (softer reference pitch, no health claims)

For wintry evenings and gentle bedtimes.
"""

SHORT_HOOKS["n01_twinkle_lullaby"] = ["twinkle twinkle,\\nvery quietly", "a music box\\nand a piano", "no noise.\\njust the notes"]
SHORT_HOOKS["n02_mary_lamb_lullaby"] = ["mary's lamb,\\nsoftly", "a tune that\\nfalls asleep itself", "no hiss.\\nno noise."]
SHORT_HOOKS["n03_row_your_boat_lullaby"] = ["row row row,\\nvery slowly", "gently down\\nthe stream", "6/8 rocking\\nfor sleepy heads"]
SHORT_HOOKS["n04_frere_jacques_lullaby"] = ["frère jacques,\\nno words needed", "one of the oldest\\ntunes we still hum", "dormez-vous?\\nalmost."]
SHORT_HOOKS["n05_london_bridge_lullaby"] = ["london bridge,\\nwithout the game", "a music box,\\nvery slowly", "falling down,\\ngently"]
SHORT_HOOKS["n06_old_macdonald_lullaby"] = ["old macdonald,\\nanimals asleep", "e-i-e-i-o,\\nwhispered", "the farm song,\\nturned down"]
SHORT_HOOKS["n07_au_clair_lullaby"] = ["by the light\\nof the moon", "a french lullaby,\\ntwo hundred years old", "play it\\nby candle-light"]
SHORT_HOOKS["n08_silent_night_lullaby"] = ["silent night,\\nslowest version", "christmas eve,\\nbedtime", "no noise.\\njust a music box"]
SHORT_HOOKS["n09_ode_to_joy_lullaby"] = ["beethoven,\\nbut sleepy", "ode to joy\\nas a music box", "the triumphant tune,\\nturned gentle"]
SHORT_HOOKS["n10_jingle_bells_lullaby"] = ["jingle bells,\\nslowed way down", "after the presents,\\nbefore sleep", "winter, in\\ntwo hands"]
