#!/usr/bin/env python3
"""純程式合成的暗色合成器配樂（原創，無授權問題）。只用 numpy。
用法：python3 synth_music.py --dur 35 --out music.wav [--bpm 84] [--seed 1]
和弦 Am – F – Dm – E（每小節一個），鋸齒波 pad 加低通、次低音、輕微 hi-hat，給口播墊底用。
"""
import argparse, wave
import numpy as np

SR = 44100


def lowpass_fft(x, cutoff):
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    X *= 1 / np.sqrt(1 + (f / cutoff) ** 4)
    return np.fft.irfft(X, len(x))


def saw(freq, t):
    return 2 * ((t * freq) % 1.0) - 1


def make(dur, out, bpm=84, seed=1):
    rng = np.random.default_rng(seed)
    n = int(dur * SR); t = np.arange(n) / SR
    bar = 4 * 60 / bpm
    chords = [[57, 60, 64], [53, 57, 60], [50, 53, 57], [52, 56, 59]]   # Am F Dm E
    bass = [45, 41, 38, 40]
    hz = lambda m: 440 * 2 ** ((m - 69) / 12)
    pad = np.zeros(n); sub = np.zeros(n); hat = np.zeros(n)
    nb = int(np.ceil(dur / bar)) + 1
    for b in range(nb):
        s0 = int(b * bar * SR); s1 = min(n, int((b + 1) * bar * SR) + int(0.4 * SR))
        if s0 >= n:
            break
        tt = t[s0:s1] - t[s0]
        env = np.minimum(1, tt / 0.8) * np.exp(-np.maximum(0, tt - bar) / 0.3)
        c = chords[b % 4]
        sig = sum(saw(hz(m) * d, tt) for m in c for d in (0.997, 1.003)) / 6
        pad[s0:s1] += sig * env
        for q in range(4):  # 每拍一個次低音
            q0 = s0 + int(q * bar / 4 * SR)
            if q0 >= n:
                break
            qt = np.arange(min(int(0.5 * SR), n - q0)) / SR
            sub[q0:q0 + len(qt)] += np.sin(2 * np.pi * hz(bass[b % 4]) * qt) * np.exp(-qt / 0.25)
        for e in range(8):
            h0 = s0 + int(e * bar / 8 * SR)
            if h0 >= n:
                break
            ln = min(int(0.04 * SR), n - h0)
            hat[h0:h0 + ln] += rng.normal(0, 1, ln) * np.exp(-np.arange(ln) / (0.008 * SR)) * (0.6 if e % 2 else 0.3)
    lfo = 900 + 500 * np.sin(2 * np.pi * t / (bar * 2))
    pad = lowpass_fft(pad, 1100) * (0.8 + 0.2 * np.sin(2 * np.pi * t / bar))
    hat = hat - lowpass_fft(hat, 6000)
    mix = 0.55 * pad + 0.6 * sub + 0.08 * hat
    fade = np.minimum(1, t / 1.5) * np.minimum(1, (dur - t) / 2.0)
    mix *= fade
    mix /= np.max(np.abs(mix)) + 1e-9
    mix *= 0.7
    st = np.stack([mix, np.roll(mix, int(0.012 * SR))], 1)
    with wave.open(out, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((st * 32767).astype("<i2").tobytes())
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dur", type=float, required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--bpm", type=float, default=84)
    ap.add_argument("--seed", type=int, default=1)
    a = ap.parse_args()
    make(a.dur, a.out, a.bpm, a.seed)
    print(a.out)
