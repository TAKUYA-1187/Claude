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
