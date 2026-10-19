#!/usr/bin/env python3
"""第 1 步：下載訪談來源（yt-dlp，公開影片、不登入、不帶 cookies）、切出每段原聲、轉錄英文字幕。

用法（先 source OpenMontage/om-env.sh）：
  python prep_clips.py --spec spec.json --work WORK
輸出：
  WORK/clips/clip_<n>.mp4（原聲片段，含 0.0 秒對齊的音軌）、clip_<n>.wav
  WORK/clips/clip_<n>.transcript.json：[{"t":[起,訖], "en":"..."}]（相對片段起點）
  並印出可以直接貼回 spec 的 "subs" 樣板（zh 留空，由寫稿的人／bot 翻成台灣繁中）。
規則檢查：每段 15 到 30 秒（超過 30 秒直接擋下）、來源要寫 channel／date／url。
"""
import argparse, json, re, subprocess, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from ir_common import CACHE, load_json, save_json, run, yt_id, probe_duration  # noqa

MAX_CLIP = 30.0


def fetch_source(url, max_h=1080):
    """整支下載後快取（YouTube 的 --download-sections 在這台機器會 403，所以抓整支再切）。"""
    vid = yt_id(url)
    d = CACHE / "sources"; d.mkdir(parents=True, exist_ok=True)
    mp4 = d / f"{vid}.mp4"
    if not mp4.exists():
        cmd = ["yt-dlp", "--no-playlist", "--no-cookies-from-browser", "-f",
               f"bv*[height<={max_h}][ext=mp4]+ba[ext=m4a]/b[height<={max_h}][ext=mp4]/b",
               "--merge-output-format", "mp4", "--write-info-json", "-o", str(d / f"{vid}.%(ext)s"), url]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode or not mp4.exists():
            print(r.stderr[-2000:]); raise SystemExit(f"yt-dlp failed for {url}")
    info = load_json(d / f"{vid}.info.json", {}) or {}
    meta = {k: info.get(k) for k in ("id", "title", "channel", "channel_url", "uploader", "upload_date", "webpage_url",
                                    "license", "duration")}
    return mp4, meta


def transcribe(wav, model="medium", lang="en"):
    """faster-whisper（CPU int8）。注意：本機的 *.en 模型快取（small.en 等）轉出來是亂碼，一律用多語 small／medium。
    預設 medium（20 秒片段 CPU 約 10 秒，small 會聽錯關鍵句）。音訊用 numpy 餵進去（本機 PyAV 版本和 faster-whisper 的 decode_audio 不相容）。"""
    import numpy as np
    from faster_whisper import WhisperModel
    pcm = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", str(wav), "-ac", "1", "-ar", "16000", "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    a = np.frombuffer(pcm, np.float32)
    m = WhisperModel(model, device="cpu", compute_type="int8")
    segs, _ = m.transcribe(a, language=lang, word_timestamps=True, vad_filter=False)
    words = [(w.start, w.end, w.word) for s in segs for w in (s.words or [])]
    # 重新分段：每段最多約 9 個字或 3.6 秒，優先在標點斷
    chunks, cur = [], []
    for w in words:
        cur.append(w)
        txt = w[2].strip()
        dur = cur[-1][1] - cur[0][0]
        if re.search(r"[.?!,;]$", txt) and (len(cur) >= 4 or re.search(r"[.?!]$", txt)) or len(cur) >= 9 or dur > 3.6:
            chunks.append(cur); cur = []
    if cur:
        chunks.append(cur)
    merged = []   # 太短的尾巴（2 個字以內）併回前一段
    for c in chunks:
        if merged and len(c) <= 2 and c[-1][1] - merged[-1][0][0] < 4.8:
            merged[-1] = merged[-1] + c
        else:
            merged.append(c)
    chunks = merged
    out = []
    for c in chunks:
        out.append({"t": [round(float(c[0][0]), 2), round(float(c[-1][1]), 2)], "en": "".join(x[2] for x in c).strip()})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", required=True); ap.add_argument("--work", required=True)
    ap.add_argument("--model", default="medium"); ap.add_argument("--retranscribe", action="store_true")
    a = ap.parse_args()
    spec = load_json(a.spec); work = Path(a.work); (work / "clips").mkdir(parents=True, exist_ok=True)
    n = 0
    for seg in spec["segments"]:
        if seg["type"] != "clip":
            continue
        n += 1
        for k in ("url", "in", "out", "speaker_en", "speaker_zh", "event", "date", "channel"):
            if not seg.get(k) and seg.get(k) != 0:
                raise SystemExit(f"clip {n}: missing '{k}'")
        dur = float(seg["out"]) - float(seg["in"])
        if dur > MAX_CLIP:
            raise SystemExit(f"clip {n}: {dur:.1f}s > {MAX_CLIP}s。原聲每段最多 30 秒（建議 15 到 30 秒，測試片 20 秒內）")
        if dur < 5:
            print(f"warn clip {n}: only {dur:.1f}s")
        src, meta = fetch_source(seg["url"])
        save_json(work / "clips" / f"clip_{n}.meta.json", meta)
        mp4 = work / "clips" / f"clip_{n}.mp4"; wav = work / "clips" / f"clip_{n}.wav"
        run(["ffmpeg", "-loglevel", "error", "-y", "-ss", f"{float(seg['in']):.3f}", "-i", src, "-t", f"{dur:.3f}",
             "-c:v", "libx264", "-preset", "veryfast", "-crf", "15", "-c:a", "aac", "-b:a", "192k", mp4])
        run(["ffmpeg", "-loglevel", "error", "-y", "-i", mp4, "-vn", "-ac", "2", "-ar", "48000", wav])
        tj = work / "clips" / f"clip_{n}.transcript.json"
        if a.retranscribe or not tj.exists():
            save_json(tj, transcribe(wav, a.model))
        tr = load_json(tj)
        print(f"\n== clip {n}: {meta.get('channel')} | {meta.get('title')} | upload {meta.get('upload_date')} | {dur:.1f}s")
        if meta.get("channel") and seg.get("channel") and meta["channel"].lower() not in seg["channel"].lower() \
                and seg["channel"].lower() not in meta["channel"].lower():
            print(f"warn: spec channel '{seg['channel']}' != YouTube channel '{meta['channel']}'。確認這是官方頻道，不是轉貼。")
        print('"subs": [\n' + ",\n".join("  " + json.dumps({"t": c["t"], "en": c["en"], "zh": ""}, ensure_ascii=False) for c in tr) + "\n]")
        if not seg.get("subs"):
            print("→ 把上面的 subs 貼進這段 clip，zh 翻成台灣繁中（可以合併／拆段，t 是相對片段起點的秒數）。")


if __name__ == "__main__":
    main()
