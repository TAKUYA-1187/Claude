"""
クラシックの名曲を、楽譜データ (MIDI) どおりに、録音したピアノ・チェロ・ヴァイオリンで演奏する。

なぜ (2026-11-01): 最近 6 か月に再生数の多かったメロディ動画を調べると、上位 30 本のうち
5 本が「クラシックのアダージョ (チェロ・ヴァイオリン・ピアノ)」、ほかにも「録音の楽器らしい
音色」が売りの動画が並んでいた (out/YouTube_人気メロディ動画_上位30.md)。
作曲者が書いたとおりの和声と伴奏を、そのまま録音の楽器で鳴らすのがいちばん質が高い。

楽譜データは data/classical/ (出どころとライセンスは SOURCES.md)。
ShareAlike のライセンスの楽譜は、この音源まで同じライセンスになってしまうので使わない。
"""

from __future__ import annotations

from fractions import Fraction
from pathlib import Path

import numpy as np

from . import dsp
from . import instruments as I
from . import arrange as A
from .arrange import Clock

DATA = Path(__file__).resolve().parent.parent / "data" / "classical"
SAMPLES = Path(__file__).resolve().parent.parent / "samples"

# 曲: ファイル, 題名, トラック番号 → 楽器, 速さの倍率, 旋律のトラック
# (ジムノペディは楽譜データの速さだと 2.4 分と速いので 0.75 倍。ゆったりした演奏の 3 分強に)
PIECES = {
    "gymnopedie_1": dict(file="gymnopedie_1.mid", title="Satie – Gymnopédie No. 1",
                         tracks={1: "piano", 2: "piano"}, tempo=0.75, lead=1),
    "gymnopedie_2": dict(file="gymnopedie_2.mid", title="Satie – Gymnopédie No. 2",
                         tracks={1: "piano", 2: "piano"}, tempo=0.75, lead=1),
    "gymnopedie_3": dict(file="gymnopedie_3.mid", title="Satie – Gymnopédie No. 3",
                         tracks={1: "piano", 2: "piano"}, tempo=0.75, lead=1),
    "clair_de_lune": dict(file="debussy_Ste_Bergamesq_Clair.mid", title="Debussy – Clair de Lune",
                          tracks={1: "piano", 2: "piano"}, tempo=1.0, lead=1),
    "arabesque_1": dict(file="debussy_Arabesque_1.mid", title="Debussy – Arabesque No. 1",
                        tracks={1: "piano", 2: "piano"}, tempo=0.95, lead=1),
    # 歌の旋律 (track 1) をチェロで
    "ave_maria_schubert": dict(file="SchubertF-D839_AveMaria.mid", title="Schubert – Ave Maria",
                               tracks={1: "cello", 2: "piano", 3: "piano"}, tempo=1.0, lead=1),
    # 原曲はヴァイオリン。録音のヴァイオリンは高い音域で 2〜4kHz が耳に刺さったので、
    # 1 オクターブ下のチェロで (チェロ版もよく演奏される)
    "ave_maria_gounod": dict(file="AveMaria-PianoViolin.mid", title="Bach / Gounod – Ave Maria",
                             tracks={1: ("cello", -12), 2: "piano", 3: "piano"}, tempo=1.0, lead=1),
    # 原曲はチェンバロ協奏曲の緩徐楽章。旋律 (track 1) をチェロ、伴奏 2 声をピアノで
    "arioso_bach": dict(file="arioso.mid", title="Bach – Arioso (BWV 1056)",
                        tracks={1: "cello", 2: "piano", 3: "piano"}, tempo=1.0, lead=1),
}
# 曲と曲のあいだ。曲の後ろの静かな部分は render_piece で切ってあり、そこから先は残響が 2〜3 秒
# 鳴るので、間はほとんど足さない (1.5 秒では、弱く終わるジムノペディの後が 4 秒の無音になった)
GAP_S = 0.3
# ジムノペディ第 1 番は低い音域だけで書かれていて、単曲版では 4kHz が検査の下限を 2dB 下回った
EXTRA_SHELF = {"k02_gymnopedie_1": 2.5}


def midi_notes(path: Path, tempo_scale: float = 1.0) -> list[tuple[int, float, float, int, int]]:
    """MIDI → [(トラック, 開始秒, 終了秒, 音高, 強さ)]。テンポの変化とペダル (CC64) を反映する"""
    import mido
    m = mido.MidiFile(str(path))
    tpb = m.ticks_per_beat
    tempos = {0: 500000}
    for t in m.tracks:
        tick = 0
        for x in t:
            tick += x.time
            if x.type == "set_tempo":
                tempos[tick] = x.tempo
    marks = sorted(tempos.items())
    # 区切りごとの開始秒を前計算
    starts, sec = [], 0.0
    for i, (tk, tp) in enumerate(marks):
        if i:
            ptk, ptp = marks[i - 1]
            sec += (tk - ptk) * ptp / 1e6 / tpb
        starts.append((tk, tp, sec))

    def t2s(tick: int) -> float:
        tk, tp, s0 = starts[0]
        for item in starts:
            if item[0] <= tick:
                tk, tp, s0 = item
            else:
                break
        return (s0 + (tick - tk) * tp / 1e6 / tpb) / tempo_scale

    out = []
    for ti, t in enumerate(m.tracks):
        tick, on, ped, held = 0, {}, False, []
        for x in t:
            tick += x.time
            if x.type == "note_on" and x.velocity > 0:
                on.setdefault(x.note, []).append((tick, x.velocity))
            elif x.type in ("note_off", "note_on") and on.get(x.note):
                st, v = on[x.note].pop(0)
                if ped:
                    held.append((st, x.note, v))
                else:
                    out.append((ti, t2s(st), t2s(tick), x.note, v))
            elif x.type == "control_change" and x.control == 64:
                down = x.value >= 64
                if ped and not down:
                    for st, n, v in held:
                        out.append((ti, t2s(st), t2s(tick), n, v))
                    held = []
                ped = down
    return sorted(out, key=lambda r: r[1])


# ── 弓で弾く弦 (チェロ・ヴァイオリン) ─────────────────────────────
_BOWED: dict[str, dict[int, np.ndarray]] = {}
# 高域を丸める基準の周波数 (強く鳴らすほど上げる)。管楽器 (flute.py / jazz.py) もこの関数で鳴らす
SUSTAIN_CUT = {"cello": 1700.0, "violin": 2000.0, "altoflute": 2600.0, "altosax": 2000.0}


def _bowed_bank(inst: str) -> dict[int, np.ndarray]:
    if inst not in _BOWED:
        d = SAMPLES / f"{inst}_clean"
        _BOWED[inst] = {int(p.stem[1:]): np.load(p).astype(np.float32) for p in d.glob("m*.npy")}
    return _BOWED[inst]


def bowed_note(inst: str, midi: int, dur: float, vel: float, sr: int = dsp.SR) -> np.ndarray:
    """
    弓で弾く 1 音。録音は ff (強く弾いた音) しかないので、
    ・立ち上がりを 80ms かけて柔らかくする (弓をそっと置く)
    ・高域を丸める (強く弾いた弦のザラつきを抑える)
    ・録音より長い音は、まん中の部分をクロスフェードでつないでのばす
    """
    from scipy import signal as sg
    bank = _bowed_bank(inst)
    keys = np.array(sorted(bank))
    base = int(keys[np.argmin(np.abs(keys - midi))])
    x = bank[base]
    r = float(dsp.midi2hz(midi)) / (440.0 * 2.0 ** ((base - 69) / 12.0))
    if abs(r - 1.0) > 1e-4:
        fr = Fraction(1.0 / r).limit_denominator(2000)
        x = sg.resample_poly(x, fr.numerator, fr.denominator).astype(np.float32)
    rel = 0.35
    need = int((dur + rel) * sr)
    if len(x) < need:
        a, b = int(len(x) * 0.30), int(len(x) * 0.80)
        seg = x[a:b]
        xf = min(int(0.12 * sr), len(seg) // 3)
        out = x[:b].copy()
        while len(out) < need:
            fade = np.linspace(0, 1, xf, dtype=np.float32)
            out[-xf:] = out[-xf:] * (1 - fade) + seg[:xf] * fade
            out = np.concatenate([out, seg[xf:]])
        x = out
    x = x[:need].copy()
    na = min(int(0.08 * sr), len(x) // 3)
    x[:na] *= np.linspace(0, 1, na, dtype=np.float32) ** 1.5
    nr = int(rel * sr)
    x[-nr:] *= np.linspace(1, 0, nr, dtype=np.float32) ** 2
    # 試聴で 2〜4kHz が強すぎた (ヴァイオリンで 2kHz が基準帯の -1.5dB) ので、しっかり丸める
    cut = SUSTAIN_CUT[inst] + 1800.0 * vel ** 2
    sos = sg.butter(2, cut, "lowpass", fs=sr, output="sos")
    return (sg.sosfilt(sos, x) * vel).astype(np.float32)


def render_piece(key: str, seed: int = 0) -> np.ndarray:
    """1 曲をステレオで。旋律の弦は、伴奏のピアノとの音量比を曲ごとに測って合わせる"""
    p = PIECES[key]
    sr = dsp.SR
    notes = midi_notes(DATA / p["file"], p["tempo"])
    # 楽譜の頭の休み (シューベルトのアヴェ・マリアは 2.5 秒) を詰める。曲間の無音になるため
    lead_in = min(st for _, st, _, _, _ in notes)
    notes = [(t, st - lead_in, e - lead_in, m, v) for t, st, e, m, v in notes]
    end = max(e for _, _, e, _, _ in notes) + 4.0
    n = int(end * sr)
    rng = np.random.default_rng(seed)
    bank = I.SampleBank(seed=seed, n_variants=3)
    piano = np.zeros((n, 2), dtype=np.float32)
    lead = np.zeros((n, 2), dtype=np.float32)
    for ti, s, e, m, v in notes:
        inst = p["tracks"].get(ti)
        if inst is None:
            continue
        shift = 0
        if isinstance(inst, tuple):
            inst, shift = inst
        m = m + shift
        vel = float(np.clip(0.30 + 0.34 * (v / 127.0) + rng.normal(0, 0.02), 0.25, 0.68))
        pos = int(round((s + rng.normal(0, 0.004)) * sr))
        if inst == "piano":
            x = bank.note("soft_piano", int(m), vel)
            # 鍵盤を離した後も少し響かせる (ペダルの代わり)。そこから 0.5 秒で消す
            hold = int((e - s + 0.35) * sr)
            if hold < len(x):
                nr = min(int(0.5 * sr), len(x) - hold)
                x = x[:hold + nr].copy()
                x[hold:] *= np.linspace(1, 0, nr, dtype=np.float32) ** 2
            pan = -0.12 if m < 60 else 0.08
            A.add_panned(piano, x, pos, 0.36 if ti == p["lead"] else 0.30, pan)
        else:
            x = bowed_note(inst, int(m), e - s, vel, sr)
            A.add_panned(lead, x, pos, 1.0, 0.10)
            lead_inst = inst
    if np.abs(lead).max() > 0:
        rp = float(np.sqrt(np.mean(piano.astype(np.float64) ** 2))) + 1e-9
        rl = float(np.sqrt(np.mean(lead.astype(np.float64) ** 2))) + 1e-9
        # チェロは伴奏より 1.5dB 上、高いヴァイオリンは同じ大きさ (それ以上だと耳に刺さった)
        piano += lead * np.float32(rp / rl * 10 ** ({"cello": 1.5, "violin": 0.0}[lead_inst] / 20))
    # 最後の音が消えた後の静かな部分を切る。1 本目では曲の後ろに -50dB 以下が 5〜8 秒続き、
    # 検査で「無音」になった。最後の音が -32dB (最大値比) まで下がった 0.8 秒後で切る
    # (-45dB で切ると、弱く終わるジムノペディでは切る位置がもう -50dBFS を下回っていて、
    # 曲間が 4.5 秒あいた)。切った後の響きは残響が自然につなぐ
    env = np.abs(piano).max(axis=1)
    loud = np.nonzero(env > env.max() * 10 ** (-32 / 20))[0]
    end = min(len(piano), int(loud[-1]) + int(0.8 * sr))
    piano = piano[:end].copy()
    nf = min(int(0.5 * sr), end // 4)
    piano[-nf:] *= np.linspace(1, 0, nf, dtype=np.float32)[:, None]
    return piano


def build_classical(spec, seconds: float):
    """曲の並び (SETS) を順に演奏し、ループ長 `seconds` にぴったり収める (曲間の間で調整)"""
    from . import tracks as TR
    order = SETS[spec.slug]
    parts = [render_piece(k, seed=spec.seed + i) for i, k in enumerate(order)]
    sr = dsp.SR
    content = sum(len(x) for x in parts)
    n = int(round(seconds * sr))
    gap = (n - content) // len(parts)
    if gap < int(0.2 * sr):
        raise ValueError(f"{spec.slug}: ループ長 {seconds}s が短すぎます (曲だけで {content / sr:.0f}s)")
    buf = np.zeros((n + int(8 * sr), 2), dtype=np.float32)
    pos = 0
    starts = []
    for x in parts:
        starts.append(pos / sr)
        buf[pos:pos + len(x)] += x
        pos += len(x) + gap
    clock = Clock(total_seconds=seconds, bars=max(int(seconds / 4), 4), beats_per_bar=4)
    ir = dsp.make_reverb_ir(3.0, rt60=2.6, damp=0.5, predelay=0.025, width=0.6, seed=spec.seed)

    shelf_db = 2.5 + EXTRA_SHELF.get(spec.slug, 0.0)

    def master(x):
        x = dsp.shelf(x, 3000.0, shelf_db, kind="high")
        x = dsp.lowpass(x, 12000.0, order=2)
        return dsp.highpass(x, 40.0, order=2)

    out, info = TR._finish(buf, clock, spec, ir, 0.32, [], master)
    info["piece_starts"] = [round(s, 1) for s in starts]
    return out, info


def set_seconds(slug: str, seed: int, gap: float = GAP_S) -> float:
    """その動画の曲の並びを、曲間 `gap` 秒で演奏するのに必要なループ長 (整数秒に切り上げ)。
    曲の長さは後ろの静かな部分を切った後で決まるので、実際に演奏して測る"""
    total = sum(len(render_piece(k, seed=seed + i)) / dsp.SR + gap for i, k in enumerate(SETS[slug]))
    return float(int(np.ceil(total)))


# 動画ごとの曲の並び (動画の記号 → 曲)。静かな曲と弦の曲を交互に
SETS = {
    "k01_classical_piano_cello": ["gymnopedie_1", "ave_maria_schubert", "clair_de_lune", "arioso_bach",
                                  "gymnopedie_2", "ave_maria_gounod", "arabesque_1", "gymnopedie_3"],
    "k02_gymnopedie_1": ["gymnopedie_1"],
    "k03_clair_de_lune": ["clair_de_lune"],
}
