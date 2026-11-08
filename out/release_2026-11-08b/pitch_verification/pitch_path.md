# 音の高さが決まる場所（verify_pitch.py が実行時に検索して作った一覧）

## 1. 基準ピッチ（A=440 / A=432）：1 か所だけ
- `bgm_studio/dsp.py:39` `_TUNING_A4 = 440.0`
- `bgm_studio/dsp.py:42` `def set_tuning(a4: float) -> None:`
- `bgm_studio/dsp.py:54` `_TUNING_A4 = float(a4)`
- `bgm_studio/dsp.py:57` `def midi2hz(m: float | np.ndarray, a4: float | None = None) -> float | np.ndarray:`
- `bgm_studio/dsp.py:61` `return a4 * 2.0 ** ((np.asarray(m, dtype=np.float64) - 69.0) / 12.0)`

`set_tuning(a4)` で決めた A を、`midi2hz(m)` が MIDI 番号から周波数にするときに 1 回だけ使う。

## 2. 録音サンプルの保存レート：1 か所だけ
- `prepare_piano_samples.py:42` `from bgm_studio.dsp import SR  # noqa: E402`
- `prepare_piano_samples.py:66` `"-f", "f32le", "-ac", "2", "-ar", str(SR), "-"],`

元の録音（44.1kHz）を、エンジンと同じ 44.1kHz で保存する。修正前はここが 48000 で、44.1k→48k に変換していた。

## 3. 演奏時に音の高さを合わせる再サンプリング：楽器ごとに 1 回
- `bgm_studio/instruments.py:368` `r = float(midi2hz(m)) / (440.0 * 2.0 ** ((base - 69) / 12.0))`
- `bgm_studio/instruments.py:371` `x = _sig.resample_poly(x, fr.numerator, fr.denominator).astype(np.float32)`
- `bgm_studio/instruments.py:405` `r = float(midi2hz(m)) / (440.0 * 2.0 ** ((base - 69) / 12.0))`
- `bgm_studio/instruments.py:408` `x = _sig.resample_poly(x, fr.numerator, fr.denominator).astype(np.float32)`
- `bgm_studio/instruments.py:454` `r = float(midi2hz(m)) / (440.0 * 2.0 ** ((base - 69) / 12.0))`
- `bgm_studio/instruments.py:457` `x = _sig.resample_poly(x, fr.numerator, fr.denominator).astype(np.float32)`
- `bgm_studio/instruments.py:483` `x = _sig.resample_poly(src[start:start + m], 3, 2)[:n].astype(np.float32)`
- `bgm_studio/classical.py:137` `r = float(dsp.midi2hz(midi)) / (440.0 * 2.0 ** ((base - 69) / 12.0))`
- `bgm_studio/classical.py:140` `x = sg.resample_poly(x, fr.numerator, fr.denominator).astype(np.float32)`
- `bgm_studio/handpan.py:53` `r = float(dsp.midi2hz(midi)) / (440.0 * 2.0 ** ((base - 69) / 12.0))`
- `bgm_studio/handpan.py:56` `x = sg.resample_poly(x, fr.numerator, fr.denominator).astype(np.float32)`
- `bgm_studio/jazz.py:371` `r = 2.0 ** ((midi - base) / 12.0)`
- `bgm_studio/jazz.py:374` `x = sg.resample_poly(x, fr.numerator, fr.denominator).astype(np.float32)`

比は「目標周波数 midi2hz(m) ÷ 録音の音の周波数（A=440 の平均律と仮定）」。サンプルレートの補正はどこにも入っていない（入れる必要がない）。
例外：`jazz._bass_note` は `2 ** ((midi - base) / 12)` で、A の設定を使わない（ジャズは A=440 だけで使う）。

## 4. 移調（曲の調を変える）：楽譜データの MIDI 番号に足すだけ
- `bgm_studio/nursery.py:98` `mb_trans=-5, mb_lg=0.75,`
- `bgm_studio/nursery.py:140` `mb_trans=-5,`
- `bgm_studio/nursery.py:173` `# 伴奏より前に出すぎた (2 分の試作で 500Hz が基準超え)。オルゴール版は mb_trans で`
- `bgm_studio/nursery.py:178` `mb_trans=-7,`
- `bgm_studio/nursery.py:190` `trans=5, mb_trans=-5,`
- `bgm_studio/nursery.py:199` `trans=7, mb_trans=-5,`
- `bgm_studio/nursery.py:210` `trans=2, mb_trans=-2,`
- `bgm_studio/nursery.py:219` `trans=2, mb_trans=-2,`
- `bgm_studio/nursery.py:232` `trans=-5, mb_trans=-2, mb_lg=0.8,`
- `bgm_studio/nursery.py:242` `trans=-5, mb_trans=-2,`
- `bgm_studio/nursery.py:253` `mb_trans=-7,`
- `bgm_studio/nursery.py:267` `# mb_trans はオルゴール版の旋律を C5〜D6 あたりに収めるための移調`
- `bgm_studio/nursery.py:271` `trans=-6, mb_trans=-3,`
- `bgm_studio/nursery.py:283` `trans=-2, mb_trans=-5,`
- `bgm_studio/nursery.py:298` `six8=True, trans=-4, mb_trans=-3,`
- `bgm_studio/nursery.py:306` `trans=-2, mb_trans=-5,`
- `bgm_studio/nursery.py:315` `trans=-4, mb_trans=-5,`
- `bgm_studio/nursery.py:327` `trans=-4, mb_trans=-5,`
- `bgm_studio/nursery.py:336` `six8=True, trans=3, mb_trans=-7,`
- `bgm_studio/nursery.py:351` `trans=-4, mb_trans=-5,`
- `bgm_studio/nursery.py:362` `trans=-6, mb_trans=-3,`
- `bgm_studio/nursery.py:372` `trans=-1, mb_trans=-6,`
- `bgm_studio/nursery.py:384` `trans=-6, mb_trans=-3,`
- `bgm_studio/nursery.py:393` `trans=-2, mb_trans=-7,`
- `bgm_studio/nursery.py:403` `trans=-4, mb_trans=-3,`
- `bgm_studio/nursery.py:419` `tail_s=1.5, trans=-4, mb_trans=-5,`
- `bgm_studio/nursery.py:440` `trans=5, mb_trans=-5, mb_lg=0.85,  # オルゴール版は旋律が少し前に出すぎた (500Hz +14.3)`
- `bgm_studio/nursery.py:451` `trans=5, mb_trans=-2, mb_lg=0.8,  # オルゴール版は旋律が前に出すぎた (500Hz +15.3)`
- `bgm_studio/nursery.py:462` `trans=-4, mb_trans=-5,`
- `bgm_studio/nursery.py:472` `trans=-1, mb_trans=-3, mb_lg=1.3,  # オルゴール版は旋律の音域が狭く (E5〜C6) こもって聞こえた (2kHz -29)`
- `bgm_studio/nursery.py:483` `trans=1, mb_trans=-5,`
- `bgm_studio/nursery.py:492` `trans=-3, mb_trans=-4,`
- `bgm_studio/nursery.py:751` `# 移調して音域を下げる (mb_trans)。旋律と伴奏の音量も曲ごとに変えられる (mb_lg, mb_ag)`
- `bgm_studio/nursery.py:753` `mb_trans = int(song.get("trans", 0)) + (int(song.get("mb_trans", 0)) if is_mb else 0)`
- `bgm_studio/nursery.py:792` `lm = midi + arr.get("octave", 0) + mb_trans`
- `bgm_studio/nursery.py:830` `bass, mids = _chord_notes(cname, mb_trans % 12)`

移調は MIDI 番号を整数で足すだけで、周波数やサンプルレートには触れない。

## 5. サンプルレートを参照する所
- `bgm_studio/dsp.py:20` `SR = 44100  # サンプリングレート (YouTube 推奨は 48k だが 44.1k で作って最後に 48k へ変換)`
- `bgm_studio/video.py:79` `sample_rate: int = 48000) -> Path:`

`video.py` の 48000 は、完成した音声を AAC にするときの出力レート（最後に 1 回）。音の高さは変わらない。

## 結論
音の高さに関わる処理は「基準ピッチ 1 回」と「楽器ごとの再サンプリング 1 回」だけ。
修正は 2. の保存レートだけで、補正の処理を足していないので、二重補正にはならない。
