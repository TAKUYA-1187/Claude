"""
bgm_studio — YouTube 向け BGM 動画の自動生成スタジオ。

外部の音源素材・映像素材を一切使わず、numpy だけで
音楽・環境音・映像をすべて手続き的に合成する。

    dsp          … 信号処理プリミティブ (フィルタ / リバーブ / ラウドネス)
    theory       … スケール・コード・進行・構成
    instruments  … 手続き生成のサンプルバンク
    nature       … 雨・焚き火・波・カフェなどの環境音
    arrange      … シーケンサ (どの楽器がいつ何を弾くか)
    tracks       … 10 本のトラック定義
    visuals      … ループ映像のシーン生成
    video        … WAV / MP4 書き出しと ffmpeg 合成
"""

__all__ = ["dsp", "theory", "instruments", "nature",
           "arrange", "tracks", "visuals", "video"]

__version__ = "1.0.0"
