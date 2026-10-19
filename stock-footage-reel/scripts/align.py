#!/usr/bin/env python3
"""把整段配音對到 script.txt 的每一行（每一鏡），輸出 timing.json：每行的起訖秒數＋每個字的時間。

用法（建議，自動帶 faster-whisper）：
  uv run -q --with faster-whisper --with numpy python align.py --audio vo.mp3 --script script.txt --out timing.json
沒有 uv 或 whisper 失敗時，會退回「靜音偵測＋字數比例」估計（--no-asr 可強制）。

做法沿用 ai-company-reel/work/align.py：whisper 逐字時間 → 和稿子做 difflib 字元對齊 → 對不到的字用前後內插。
"""
import argparse, difflib, json, re, subprocess, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from common import read_script, probe_duration, save_json  # noqa

SKIP = set(" \n，。、：；「」『』？！,.?!:;\"'（）()…—-")


def asr_words(audio):
    import numpy as np
    from faster_whisper import WhisperModel
    pcm = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", audio, "-ac", "1", "-ar", "16000", "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    a = np.frombuffer(pcm, np.float32)
    m = WhisperModel("small", device="cpu", compute_type="int8")
    segs, _ = m.transcribe(a, language="zh", word_timestamps=True, initial_prompt="以下是繁體中文的句子。")
    return [[w.start, w.end, w.word] for s in segs for w in s.words]


def char_times(script_text, words):
    wc = []
    for s, e, w in words:
        cs = [c for c in w.lower() if c not in SKIP]
        for i, c in enumerate(cs):
            wc.append((c, s + (e - s) * i / max(1, len(cs)), s + (e - s) * (i + 1) / max(1, len(cs))))
    sc = [(i, c.lower()) for i, c in enumerate(script_text) if c not in SKIP]
    A = "".join(c for _, c in sc); B = "".join(c for c, _, _ in wc)
    sm = difflib.SequenceMatcher(None, A, B, autojunk=False)
    t0 = [None] * len(sc); t1 = [None] * len(sc)
    for a, b, n in sm.get_matching_blocks():
        for k in range(n):
            t0[a + k] = wc[b + k][1]; t1[a + k] = wc[b + k][2]
    known = [k for k in range(len(sc)) if t0[k] is not None]
    for k in range(len(sc)):
        if t0[k] is None:
            prev = max([j for j in known if j < k], default=None)
            nxt = min([j for j in known if j > k], default=None)
            if prev is None:
                t0[k] = t1[k] = (wc[0][1] if wc else 0) * k / max(1, nxt or 1)
            elif nxt is None:
                t0[k] = t1[k] = t1[prev]
            else:
                f = (k - prev) / (nxt - prev); t0[k] = t1[prev] + (t0[nxt] - t1[prev]) * f; t1[k] = t0[k]
    matched = sum(n for *_, n in sm.get_matching_blocks())
    return {i: (t0[k], t1[k]) for k, (i, _) in enumerate(sc)}, matched / max(1, len(A))


def proportional(lines, audio):
    """備案：用靜音偵測找行界，找不到就照字數比例。"""
    dur = probe_duration(audio)
    out = subprocess.run(["ffmpeg", "-i", audio, "-af", "silencedetect=noise=-35dB:d=0.25", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    sil = [(float(a), float(b)) for a, b in zip(re.findall(r"silence_start: ([\d.]+)", out), re.findall(r"silence_end: ([\d.]+)", out))]
    w = [len([c for c in l if c not in SKIP]) for l in lines]
    tot = sum(w); acc = 0; bounds = [0.0]
    for x in w[:-1]:
        acc += x; guess = dur * acc / tot
        near = min(sil, key=lambda s: abs((s[0] + s[1]) / 2 - guess), default=None)
        bounds.append((near[0] + near[1]) / 2 if near and abs((near[0] + near[1]) / 2 - guess) < 1.5 else guess)
    bounds.append(dur)
    return bounds


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--audio", required=True)
    ap.add_argument("--script", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--no-asr", action="store_true")
    a = ap.parse_args()
    lines = read_script(a.script)
    text = "\n".join(lines)
    dur = probe_duration(a.audio)
    res = {"audio": str(Path(a.audio).resolve()), "audio_dur": round(dur, 3), "lines": []}
    ct = None
    if not a.no_asr:
        try:
            words = asr_words(a.audio)
            ct, rate = char_times(text, words)
            res["method"] = f"faster-whisper small + difflib (matched {rate:.0%})"
            res["words"] = words
        except Exception as e:  # noqa
            print("ASR failed, fallback:", e)
    if ct is None:
        b = proportional(lines, a.audio)
        res["method"] = "silence/proportional fallback"
        pos = 0
        for i, l in enumerate(lines):
            st, en = b[i], b[i + 1]
            idx = [j for j in range(len(l)) if l[j] not in SKIP]
            chars = {str(pos + j): (st + (en - st) * k / len(idx), st + (en - st) * (k + 1) / len(idx)) for k, j in enumerate(idx)}
            res["lines"].append({"i": i + 1, "text": l, "offset": pos, "speech_start": st, "speech_end": en, "chars": chars})
            pos += len(l) + 1
    else:
        pos = 0
        for i, l in enumerate(lines):
            idx = [pos + j for j in range(len(l)) if l[j] not in SKIP]
            chars = {str(j): ct[j] for j in idx if j in ct}
            st = min(v[0] for v in chars.values()); en = max(v[1] for v in chars.values())
            res["lines"].append({"i": i + 1, "text": l, "offset": pos, "speech_start": st, "speech_end": en, "chars": chars})
            pos += len(l) + 1
    # 鏡頭切點：放在兩句之間的停頓中間；第一鏡從 0 開始，最後一鏡到音檔結束
    L = res["lines"]
    for i, ln in enumerate(L):
        ln["start"] = 0.0 if i == 0 else round((L[i - 1]["speech_end"] + ln["speech_start"]) / 2, 3)
    for i, ln in enumerate(L):
        ln["end"] = round(L[i + 1]["start"], 3) if i + 1 < len(L) else round(dur, 3)
        ln["dur"] = round(ln["end"] - ln["start"], 3)
    save_json(a.out, res)
    print(res["method"])
    for ln in L:
        print(f"[{ln['i']}] {ln['start']:6.2f}-{ln['end']:6.2f} ({ln['dur']:.2f}s) {ln['text'][:30]}")


if __name__ == "__main__":
    main()
