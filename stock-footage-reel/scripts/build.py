#!/usr/bin/env python3
"""把配音＋素材＋字幕＋配樂剪成成片，並輸出聯絡表、credits、封面。

用法：
  python3 build.py --shots shots.json --work WORK --out OUT_DIR [--name reel] [--plan] [--check]
需要先跑：align.py（timing.json）→ fetch_footage.py（footage.json、credits.json）。
--check 只檢查設定（品牌、帳號、COVERS_DIR、User-Agent 不能還是範本佔位符），沒過就停下來。
--plan 只印出每鏡自動切好的字幕段落，方便在 shots.json 寫對應的英文 "en" 清單。
"""
import argparse, json, math, os, re, subprocess, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from common import (check_config, layout, font, FONT_SANS, FONT_SERIF, GOLD, BRAND_RED, WHITE, COVERS, load_json, save_json,
                    probe_duration)  # noqa
from PIL import Image, ImageDraw, ImageFilter

FONT_EN = "/usr/share/fonts/truetype/sand-box/google/Noto Sans/NotoSans-VariableFont_wdth,wght.ttf"
FPS = 30
BRAND_NAME = os.environ.get("BRAND_NAME", "你的名字｜你的品牌")   # 品牌記號文字
BRAND_HANDLE = os.environ.get("BRAND_HANDLE", "@your_handle")      # 片尾帳號
PUNCT_END = "，。：；、"


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        print(" ".join(map(str, cmd))[:2000]); print(r.stderr[-3000:]); raise SystemExit("ffmpeg failed")
    return r

# ---------------------------------------------------------------- 字幕切段
def wlen(s):
    return sum(0.55 if ord(c) < 128 else 1 for c in re.sub(r"\s", "", s))


def chunk_line(text, maxw=14.0, max_lines=2):
    """先切成子句，再把子句組成「最多兩行、每行 maxw 字寬」的字幕段。回傳 [(start_idx, end_idx, [line1, line2])]。"""
    parts = [(m.start(), m.end(), m.group()) for m in re.finditer(r"[^，。：；？！]+[，。：；？！」]*", text)]
    # 太長的子句再從中間的空白或「的」後面切
    fixed = []
    for a, b, p in parts:
        while wlen(p) > maxw:
            cut = int(len(p) / 2)
            sp = [m.end() for m in re.finditer(r"[ 、]|的|和|把|讓|要", p) if 3 < m.end() < len(p) - 3
                  and not (p[m.start() - 1:m.start()].isascii() and p[m.start() - 1:m.start()].isalpha()
                           and p[m.end():m.end() + 1].isascii() and p[m.end():m.end() + 1].isalpha())]
            if sp:
                cut = min(sp, key=lambda x: abs(x - len(p) / 2))
            fixed.append((a, a + cut, p[:cut])); a, p = a + cut, p[cut:]
        fixed.append((a, b, p))
    chunks, cur = [], []
    for a, b, p in fixed:
        if cur and (len(cur) >= max_lines or re.search(r"[。？！]」?$", cur[-1][2].strip())):
            chunks.append(cur); cur = []
        cur.append((a, b, p))
    if cur:
        chunks.append(cur)
    out = []
    for c in chunks:
        lines = [clean(p) for _, _, p in c]
        out.append((c[0][0], c[-1][1], lines))
    return out


def clean(s):
    s = s.strip()
    s = re.sub(r"[，。：；、]+$", "", s)
    s = re.sub(r"[，。：；、](」)$", r"\1", s)
    return s.replace("—", "，")


def plan_subs(spec, timing):
    subs = []
    for i, ln in enumerate(timing["lines"]):
        shot = spec["shots"][i]
        chars = {int(k): v for k, v in ln["chars"].items()}
        text = ln["text"]
        chunks = shot.get("subs_zh") and [(None, None, s.split("\n")) for s in shot["subs_zh"]] or chunk_line(text)
        en = shot.get("en", "")
        ens = en if isinstance(en, list) else [en] * len(chunks)
        if len(ens) != len(chunks):
            print(f"warn shot {i+1}: en has {len(ens)} items but {len(chunks)} chunks; using joined English for all")
            ens = [" ".join(ens)] * len(chunks)
        pos = 0
        for k, (a, b, lines) in enumerate(chunks):
            if a is None:  # 手動指定的字幕段：在原句中找位置
                flat = "".join(lines); a = text.find(flat[:2], pos); a = max(a, pos); b = a + len(flat)
            pos = b
            idx = [ln["offset"] + j for j in range(a, b) if (ln["offset"] + j) in chars]
            st = chars[idx[0]][0] if idx else ln["speech_start"]
            subs.append(dict(shot=i + 1, k=k, lines=lines, en=ens[k], st=st,
                             hl=shot.get("highlight") or []))
    # 每段顯示到下一段開始（同一鏡內）或該鏡結束
    for j, s in enumerate(subs):
        ln = timing["lines"][s["shot"] - 1]
        nxt = subs[j + 1] if j + 1 < len(subs) else None
        s["st"] = max(ln["start"], s["st"] - 0.08)
        s["en_t"] = nxt["st"] - 0.08 if nxt and nxt["shot"] == s["shot"] else ln["end"]
        if j == 0:
            s["st"] = 0.0
    return subs

# ---------------------------------------------------------------- 畫字
def rich_runs(line, highlights):
    """[[字]] 或 shot.highlight 清單裡的詞 → 金色。回傳 [(text, is_gold)]"""
    hl = [h for h in (highlights if isinstance(highlights, list) else [highlights]) if h]
    marks = [False] * len(line)
    plain = line
    for m in re.finditer(r"\[\[(.+?)\]\]", line):
        pass
    if "[[" in line:
        out, gold = [], False
        for tok in re.split(r"(\[\[|\]\])", line):
            if tok == "[[": gold = True
            elif tok == "]]": gold = False
            elif tok: out.append((tok, gold))
        return out
    for h in hl:
        for m in re.finditer(re.escape(h), plain):
            for x in range(m.start(), m.end()):
                marks[x] = True
    out = []
    for ch, g in zip(plain, marks):
        if out and out[-1][1] == g:
            out[-1] = (out[-1][0] + ch, g)
        else:
            out.append((ch, g))
    return out


def draw_shadowed(img, draw_fn, blur=6, alpha=170):
    shadow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw_fn(ImageDraw.Draw(shadow), (0, 0, 0, alpha), True)
    shadow = shadow.filter(ImageFilter.GaussianBlur(blur))
    img.alpha_composite(shadow)
    draw_fn(ImageDraw.Draw(img), None, False)


def wrap_en(text, f, maxw, d):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if d.textlength(t, font=f) > maxw and cur:
            lines.append(cur); cur = w
        else:
            cur = t
    if cur:
        lines.append(cur)
    return lines


def brand_mark(d, x, y, size, color=WHITE, f=None):
    r = size / 2
    d.ellipse([x, y, x + size, y + size], fill=BRAND_RED)
    for k in range(3):
        cx = x + size * 1.55 + k * size * 0.62
        rr = size * 0.21
        d.ellipse([cx - rr, y + r - rr, cx + rr, y + r + rr], outline=color, width=max(2, int(size * 0.11)))
    tx = x + size * 1.55 + 2 * size * 0.62 + size * 0.55
    d.text((tx, y + r), BRAND_NAME, font=f, fill=color, anchor="lm")


def gradient_layer(L):
    W, H = L["W"], L["H"]
    g = Image.new("L", (1, H))
    for y in range(H):
        top = max(0, 1 - y / (H * 0.2)) * 120
        bot = max(0, (y - H * 0.45) / (H * 0.55)) ** 1.3 * 200
        g.putpixel((0, y), int(min(230, top + bot)))
    a = g.resize((W, H))
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0)); layer.putalpha(a)
    return layer


def header_layer(L, spec):
    W, H = L["W"], L["H"]
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    m, y = L["margin"], L["header_y"]
    fb = font(FONT_SANS, 26, "Medium")
    fz = font(FONT_SANS, 34, "Bold")
    fe = font(FONT_EN, 22, "Medium")
    def fn(d, col, sh):
        brand_mark(d, m, y, 26, col or WHITE, fb)
        d.text((m, y + 48), spec.get("title_zh", ""), font=fz, fill=col or WHITE)
        d.text((m, y + 98), spec.get("title_en", ""), font=fe, fill=col or (235, 232, 226, 200))
    draw_shadowed(img, fn, blur=4, alpha=150)
    return img


def sub_layer(L, s):
    W, H = L["W"], L["H"]
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    fz = font(FONT_SANS, L["zh_size"], "Bold")
    fe = font(FONT_EN, L["en_size"], "Medium")
    d0 = ImageDraw.Draw(img)
    m = L["margin"]
    en_lines = wrap_en(s["en"], fe, L["text_w"], d0) if s["en"] else []
    lh_z = int(L["zh_size"] * 1.32); lh_e = int(L["en_size"] * 1.35)
    total = lh_z * len(s["lines"]) + (18 + lh_e * len(en_lines) if en_lines else 0)
    y0 = L["sub_bottom"] - total
    # 中文太寬就縮字
    zs = L["zh_size"]
    while zs > 40 and max(d0.textlength(re.sub(r"\[\[|\]\]", "", l), font=fz) for l in s["lines"]) > L["text_w"]:
        zs -= 2; fz = font(FONT_SANS, zs, "Bold")
    def fn(d, col, sh):
        y = y0
        for line in s["lines"]:
            x = m
            for t, g in rich_runs(line, s["hl"]):
                d.text((x, y), t, font=fz, fill=col or (GOLD if g else WHITE))
                x += d.textlength(t, font=fz)
            y += lh_z
        y += 18
        for e in en_lines:
            d.text((m, y), e, font=fe, fill=col or (240, 238, 232, 225))
            y += lh_e
    draw_shadowed(img, fn, blur=7, alpha=190)
    return img


def credit_line(credits):
    arch, foot = [], []
    for c in credits.get("clips", []):
        src = c["source"]
        if src.startswith("Generated"):
            continue
        if src.startswith("Prelinger"):
            lab = "Prelinger Archives (Public Domain)"
            if lab not in arch: arch.append(lab)
        else:
            short = {"Wikimedia Commons": "Wikimedia Commons"}.get(src, src)
            lic = c.get("license", "")
            lab = short if src in ("Mixkit", "Pexels", "Pixabay") else f"{short} ({lic.split('(')[0].strip()})"
            if lab not in foot: foot.append(lab)
    parts = []
    if arch: parts.append("Archival: " + ", ".join(arch))
    if foot: parts.append("Footage: " + ", ".join(foot))
    v = credits.get("voice", {})
    if v.get("provider"): parts.append("Voice: " + v["provider"])
    return "  •  ".join(parts)


def endcard_layer(L, ec, credits_text):
    W, H = L["W"], L["H"]
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    m = L["margin"]
    big = 96 if H > 1500 else 84
    fz = font(FONT_SERIF, big, "Bold")
    fe = font(FONT_EN, 44 if H > 1500 else 40, "SemiBold")
    fb = font(FONT_SANS, 32, "Regular")
    fc = font(FONT_EN, 22, "Regular")
    fbm = font(FONT_SANS, 28, "Medium")
    d0 = ImageDraw.Draw(img)
    zl = ec.get("zh", [])
    while big > 56 and max(d0.textlength(re.sub(r"\[\[|\]\]", "", l), font=fz) for l in zl) > W - 2 * m:
        big -= 4; fz = font(FONT_SERIF, big, "Bold")
    en_lines = []
    for e in (ec.get("en") if isinstance(ec.get("en"), list) else [ec.get("en", "")]):
        en_lines += wrap_en(e, fe, W - 2 * m, d0) if e else []
    def fn(d, col, sh):
        y = L["end_top"]
        for line in zl:
            x = m
            for t, g in rich_runs(line, []):
                d.text((x, y), t, font=fz, fill=col or (GOLD if g else WHITE)); x += d.textlength(t, font=fz)
            y += int(big * 1.3)
        y += 30
        for e in en_lines:
            d.text((m, y), e, font=fe, fill=col or WHITE); y += int(fe.size * 1.3)
        y += 40
        if ec.get("by"):
            d.text((m, y), ec["by"], font=fb, fill=col or (230, 228, 222, 210)); y += 70
        brand_mark(d, m, y, 28, col or WHITE, fbm)
        d.text((m, y + 50), BRAND_HANDLE, font=fbm, fill=col or (230, 228, 222, 220))
        if credits_text:
            d.text((m, L["credit_y"]), credits_text, font=fc, fill=col or (225, 222, 215, 170))
    draw_shadowed(img, fn, blur=6, alpha=170)
    return img

# ---------------------------------------------------------------- 影像
GRADES = {
    "archival": "eq=contrast=1.12:brightness=-0.02:saturation=0.95,colorbalance=rs=0.14:gs=-0.07:bs=0.11:rm=0.10:gm=-0.07:bm=0.07:rh=0.05:bh=0.04,gblur=sigma=0.7,noise=alls=12:allf=t+u,vignette=PI/4",
    "modern": "eq=contrast=1.06:brightness=-0.06:saturation=0.75,colorbalance=rs=-0.07:bs=0.08:rm=-0.05:gm=0.01:bm=0.06,vignette=PI/4.5",
    "none": "null",
}


def render_cut(src, start, dur, out, L, grade, drift, focus=0.5, endcard=False):
    W, H = L["W"], L["H"]
    W2, H2 = int(W * 1.08) // 2 * 2, int(H * 1.08) // 2 * 2
    clip_len = probe_duration(src)
    loop = clip_len < start + dur + 0.1
    if loop and clip_len < dur + 0.1:
        start = 0
    elif loop:
        start = max(0, clip_len - dur - 0.1)
    fx = f"(iw-{W})*({focus}+{0.3 * drift}*(t/{dur:.3f}-0.5))"
    vf = (f"scale='if(gt(a,{W}/{H}),-2,{W2})':'if(gt(a,{W}/{H}),{H2},-2)',"
          f"crop={W}:{H}:'max(0,min(iw-{W},{fx}))':'(ih-{H})/2',fps={FPS},{GRADES[grade]}")
    if endcard:
        vf += ",eq=brightness=-0.20:saturation=0.6:contrast=0.95,gblur=sigma=5"
    vf += ",setsar=1,format=yuv420p"
    cmd = ["ffmpeg", "-loglevel", "error", "-y"]
    if clip_len < dur + 0.1:
        cmd += ["-stream_loop", "-1"]
    cmd += ["-ss", f"{start:.3f}", "-i", src, "-t", f"{dur:.3f}", "-an", "-vf", vf,
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-r", str(FPS), "-video_track_timescale", "15360", out]
    run(cmd)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--shots", required=True)
    ap.add_argument("--work", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--name", default="reel")
    ap.add_argument("--plan", action="store_true")
    ap.add_argument("--no-cover", action="store_true")
    ap.add_argument("--check", action="store_true", help="only validate settings (placeholders) and exit")
    a = ap.parse_args()
    check_config(BRAND_NAME=BRAND_NAME, BRAND_HANDLE=BRAND_HANDLE)
    if a.check:
        print("config OK"); return
    spec = load_json(a.shots); work = Path(a.work).resolve(); out = Path(a.out).resolve(); out.mkdir(parents=True, exist_ok=True)
    timing = load_json(work / "timing.json")
    if len(timing["lines"]) != len(spec["shots"]):
        raise SystemExit(f"script has {len(timing['lines'])} lines but shots.json has {len(spec['shots'])} shots")
    subs = plan_subs(spec, timing)
    if a.plan:
        for s in subs:
            print(f"shot {s['shot']}.{s['k']}  {s['st']:.2f}-{s['en_t']:.2f}  {' / '.join(s['lines'])}  || {s['en'][:60]}")
        return
    L = layout(spec.get("format", "1080x1920")); W, H = L["W"], L["H"]
    footage = load_json(work / "footage.json")
    credits = load_json(work / "credits.json", {"clips": []})
    credits["voice"] = spec.get("voice", credits.get("voice", {}))
    tmp = work / "build"; tmp.mkdir(exist_ok=True)
    vo_dur = timing["audio_dur"]
    ec = spec.get("end_card")
    ec_dur = float(ec.get("dur", 4.0)) if ec else 0
    total = vo_dur + float(spec.get("tail", 0.4)) + ec_dur

    # 1) 逐鏡剪素材（同一鏡多段時在字幕段落交界切）
    cuts, drift = [], 1
    for i, ln in enumerate(timing["lines"]):
        f = footage[str(i + 1)]
        shot = spec["shots"][i]
        st, en = ln["start"], ln["end"]
        if i == len(timing["lines"]) - 1:
            en = vo_dur + float(spec.get("tail", 0.4))
        starts = f.get("starts") or [f.get("start", 0)]
        n = len(starts)
        bounds = [st]
        sb = [s["st"] for s in subs if s["shot"] == i + 1 and s["st"] > st + 1.2 and s["st"] < en - 1.2]
        for k in range(1, n):
            ideal = st + (en - st) * k / n
            b = min(sb, key=lambda x: abs(x - ideal)) if sb and min(abs(x - ideal) for x in sb) < 1.2 else ideal
            bounds.append(b)
        bounds.append(en)
        grade = shot.get("grade") or ("archival" if f.get("archival") else "modern")
        for k in range(n):
            d = bounds[k + 1] - bounds[k]
            p = tmp / f"cut_{i+1:02d}_{k}.mp4"
            render_cut(f["path"], float(starts[k]), d, str(p), L, grade, drift, shot.get("focus_x", 0.5))
            drift = -drift
            cuts.append((p, d, i + 1))
    if ec:
        bg = ec.get("bg_shot", len(spec["shots"]))
        f = footage[str(bg)]
        p = tmp / "cut_end.mp4"
        st0 = float((f.get("starts") or [0])[-1]) + 2.0
        render_cut(f["path"], st0, ec_dur, str(p), L, ec.get("grade") or ("archival" if f.get("archival") else "modern"),
                   drift, endcard=True)
        cuts.append((p, ec_dur, "end"))
    lst = tmp / "cuts.txt"
    lst.write_text("".join(f"file '{p}'\n" for p, _, _ in cuts))
    bgv = tmp / "bg.mp4"
    cc = ["ffmpeg", "-loglevel", "error", "-y"]
    for p, _, _ in cuts:
        cc += ["-i", str(p)]
    fc = "".join(f"[{k}:v]setpts=PTS-STARTPTS,setsar=1[c{k}];" for k in range(len(cuts)))
    fc += "".join(f"[c{k}]" for k in range(len(cuts))) + f"concat=n={len(cuts)}:v=1:a=0,fps={FPS}[v]"
    run(cc + ["-filter_complex", fc, "-map", "[v]", "-c:v", "libx264", "-preset", "veryfast", "-crf", "16",
              "-pix_fmt", "yuv420p", str(bgv)])

    # 2) 疊字層：每個時間區間一張全幅 PNG，用 concat 串成一條透明軌
    grad = gradient_layer(L); head = header_layer(L, spec)
    base = Image.new("RGBA", (W, H), (0, 0, 0, 0)); base.alpha_composite(grad); base.alpha_composite(head)
    events = []
    t = 0.0
    for j, s in enumerate(subs):
        if s["st"] > t + 0.01:
            events.append((base, s["st"] - t)); t = s["st"]
        im = base.copy(); im.alpha_composite(sub_layer(L, s))
        events.append((im, s["en_t"] - t)); t = s["en_t"]
    vo_end = total - ec_dur
    if vo_end > t:
        events.append((base, vo_end - t)); t = vo_end
    ctext = credit_line(credits)
    if ec:
        eim = Image.new("RGBA", (W, H), (0, 0, 0, 0)); eim.alpha_composite(grad)
        eim.alpha_composite(endcard_layer(L, ec, ctext))
        events.append((eim, ec_dur))
    ol = tmp / "overlay.txt"; lines = ["ffconcat version 1.0"]
    for k, (im, d) in enumerate(events):
        pth = tmp / f"ov_{k:03d}.png"; im.save(pth)
        lines += [f"file '{pth}'", f"duration {max(0.04, d):.3f}"]
    lines.append(f"file '{pth}'")
    ol.write_text("\n".join(lines) + "\n")
    ovm = tmp / "overlay.mov"   # 先轉成一條固定 30fps 的透明影片，直接拿 PNG concat 疊會在中途掉字
    run(["ffmpeg", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(ol), "-vf", f"fps={FPS},format=rgba",
         "-t", f"{total:.3f}", "-c:v", "qtrle", str(ovm)])

    # 3) 聲音：配音＋配樂（側鏈壓縮讓音樂在講話時讓開）
    music = spec.get("music", "synth")
    mus = None
    if music == "synth":
        import synth_music
        mus = str(tmp / "music.wav"); synth_music.make(total + 0.5, mus, bpm=spec.get("bpm", 84))
        credits["music"] = {"source": "Original code-synth track (synth_music.py)", "license": "Own work"}
    elif music and music != "none":
        mus = music
        credits.setdefault("music", {"source": music, "license": spec.get("music_license", "CHECK")})
    vol = spec.get("music_db", -17)
    afil = (f"[1:a]aresample=48000,apad,atrim=0:{total:.3f},asplit=2[vo][sc];")
    if mus:
        afil += (f"[2:a]aresample=48000,aloop=loop=-1:size=2e9,atrim=0:{total:.3f},volume={vol}dB,"
                 f"afade=t=out:st={total-2.5:.3f}:d=2.5[mu];"
                 f"[mu][sc]sidechaincompress=threshold=0.02:ratio=8:attack=30:release=500[duck];"
                 f"[vo][duck]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11[aout]")
    else:
        afil += "[vo]loudnorm=I=-14:TP=-1.5:LRA=11[aout];[sc]anullsink"
    final = out / f"{a.name}.mp4"
    cmd = ["ffmpeg", "-loglevel", "error", "-y", "-i", str(bgv), "-i", timing["audio"]]
    if mus:
        cmd += ["-i", mus]
    cmd += ["-i", str(ovm),
            "-filter_complex", afil + f";[0:v]setpts=PTS-STARTPTS[bgv];[{3 if mus else 2}:v]setpts=PTS-STARTPTS[ovl];[bgv][ovl]overlay=0:0:eof_action=repeat:format=auto,format=yuv420p[vout]",
            "-map", "[vout]", "-map", "[aout]", "-t", f"{total:.3f}", "-r", str(FPS),
            "-c:v", "libx264", "-preset", "medium", "-crf", str(spec.get("crf", 21)), "-profile:v", "high", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-movflags", "+faststart", str(final)]
    run(cmd)
    size = final.stat().st_size / 1e6
    if size > 45:
        br = int(44 * 8e6 / total) - 170_000
        c2 = list(cmd); j = c2.index("-crf")
        c2[j:j + 2] = ["-b:v", str(br), "-maxrate", str(br), "-bufsize", str(2 * br)]
        run(c2)
        size = final.stat().st_size / 1e6

    # 4) 聯絡表
    sheet_imgs = []
    tt = 0
    for p, d, lab in cuts:
        mid = tt + d / 2; tt += d
        r = subprocess.run(["ffmpeg", "-loglevel", "error", "-ss", f"{mid:.2f}", "-i", str(final), "-frames:v", "1",
                            "-vf", "scale=270:-2", "-f", "image2pipe", "-vcodec", "png", "-"], capture_output=True).stdout
        import io
        im = Image.open(io.BytesIO(r)).convert("RGB")
        ImageDraw.Draw(im).text((6, 4), f"{lab} @{mid:.1f}s", fill=(255, 230, 0), font=font(FONT_SANS, 18, "Bold"))
        sheet_imgs.append(im)
    cols = min(6, len(sheet_imgs)); rows = math.ceil(len(sheet_imgs) / cols)
    tw, th = sheet_imgs[0].size
    S = Image.new("RGB", (cols * tw, rows * th), (0, 0, 0))
    for k, im in enumerate(sheet_imgs):
        S.paste(im, ((k % cols) * tw, (k // cols) * th))
    S.save(out / "contact_sheet.jpg", quality=88)  # 每個 cut 中間一格＋片尾卡

    # 5) credits（影片下方小字＋貼文說明用的完整出處）
    credits["credit_line"] = ctext
    full = []
    for c in credits["clips"]:
        if c["source"].startswith("Generated"):
            continue
        full.append(f"・{c['title']} — {c.get('author') or c['source']}｜{c['source']}｜{c['license']}｜{c['page']}")
    credits["caption_credits"] = full
    save_json(out / "credits.json", credits)
    save_json(work / "credits.json", credits)

    # 6) 封面：B 剪報 Vox 樣板，剪報用影片裡的一格
    if not a.no_cover and spec.get("cover"):
        cv = dict(spec["cover"])
        # 剪報用素材原始比例的一格（不是直式裁切後的畫面），套同一套調色
        fs = int(cv.pop("frame_shot", 0) or next((int(k) for k in sorted(footage, key=int) if footage[k].get("archival")), 1))
        fk = int(cv.pop("frame_cut", 0)); off = float(cv.pop("frame_offset", 1.0)); cv.pop("frame_t", None)
        ff = footage[str(fs)]
        fst = float((ff.get("starts") or [ff.get("start", 0)])[min(fk, len(ff.get("starts") or [0]) - 1)]) + off
        grade = spec["shots"][fs - 1].get("grade") or ("archival" if ff.get("archival") else "modern")
        frame = out / "cover_frame.jpg"
        run(["ffmpeg", "-loglevel", "error", "-y", "-ss", f"{fst:.2f}", "-i", ff["path"], "-frames:v", "1",
             "-vf", f"scale=1280:-2,{GRADES[grade].replace('noise=alls=12:allf=t+u,', 'noise=alls=8:allf=u,')}", "-q:v", "2", str(frame)])
        cv.update({"template": "B", "visual": str(frame), "out": str(out / "cover")})
        sp = out / "cover_spec.json"; save_json(sp, cv)
        r = subprocess.run(["python3", str(COVERS / "render.py"), str(sp)], capture_output=True, text=True, cwd=str(COVERS))
        print(r.stdout.strip() or r.stderr[-800:])
    print(f"{final}  {probe_duration(final):.2f}s  {size:.1f} MB")


if __name__ == "__main__":
    main()
