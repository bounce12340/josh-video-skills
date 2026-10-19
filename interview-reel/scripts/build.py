#!/usr/bin/env python3
"""第 4 步：照 spec 剪出名人訪談 Reel（Fox Hsiao 式：解說穿插原聲）。

用法（先 source OpenMontage/om-env.sh）：
  python build.py --spec spec.json --work WORK --out OUT [--name reel] [--check]
需要先跑：prep_clips.py（原聲片段＋轉錄）、tts.py（旁白）、fetch_broll.py（B-roll）。
--check 只做規則檢查和時間軸計算（片長、原聲占比、字幕），不出片。
產出（OUT）：<name>.mp4、preview_720p.mp4、contact_sheet.jpg、credits.json、timeline.json、cover_reel.png／cover_post.png
"""
import argparse, io, math, os, re, subprocess, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from ir_common import (L, W, H, FPS, YELLOW, ORANGE, TAG_RED, GREY, WHITE, BRAND_RED, FONT_SANS, FONT_EN, COVERS,
                       font, load_json, save_json, probe_duration, run, narr_lines)  # noqa
from PIL import Image, ImageDraw, ImageFilter

GRADE = "eq=contrast=1.05:brightness=-0.15:saturation=0.78,vignette=PI/4.2"
BRAND_NAME = os.environ.get("BRAND_NAME", "你的名字｜你的品牌")   # 品牌記號文字
BRAND_HANDLE = os.environ.get("BRAND_HANDLE", "@your_handle")      # 片尾帳號
ZH_BAD = ["—", "――", "--"]


# ------------------------------------------------------------------ 文字工具
def runs(text, hl=(), color=YELLOW, base=WHITE):
    """[[字]] 或 hl 清單 → 強調色。回傳 [(str, color)]"""
    if "[[" in text:
        out, on = [], False
        for tok in re.split(r"(\[\[|\]\])", text):
            if tok == "[[": on = True
            elif tok == "]]": on = False
            elif tok: out.append((tok, color if on else base))
        return out
    marks = [False] * len(text)
    for h in hl or []:
        for m in re.finditer(re.escape(h), text):
            for x in range(m.start(), m.end()): marks[x] = True
    out = []
    for ch, g in zip(text, marks):
        c = color if g else base
        if out and out[-1][1] == c: out[-1] = (out[-1][0] + ch, c)
        else: out.append((ch, c))
    return out


def plain(s):
    return re.sub(r"\[\[|\]\]", "", s)


def clean_zh(s):
    s = s.strip()
    s = re.sub(r"[，。、；：]+$", "", s)
    return s


def split_zh(s, f, maxw, d):
    """太寬就在中間附近的「，」或空白斷成兩行。"""
    s = clean_zh(s)
    if "\n" in s:
        return [clean_zh(x) for x in s.split("\n")]
    if d.textlength(plain(s), font=f) <= maxw:
        return [s]
    cands = [m.end() for m in re.finditer(r"[，、；：]", s) if 2 < m.end() < len(s) - 2]
    if not cands:  # 沒有標點才在空白斷，而且不切開英文詞組（例如 AI agent）
        cands = [m.end() for m in re.finditer(r" ", s) if 2 < m.end() < len(s) - 2
                 and not (s[m.start() - 1].isascii() and s[m.end()].isascii())]
    cut = min(cands, key=lambda x: abs(x - len(s) / 2)) if cands else len(s) // 2
    # 不要把 [[ ]] 切開
    while s[:cut].count("[[") != s[:cut].count("]]") and cut < len(s): cut += 1
    return [clean_zh(s[:cut]), clean_zh(s[cut:])]


def wrap_en(text, f, maxw, d):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if d.textlength(t, font=f) > maxw and cur: lines.append(cur); cur = w
        else: cur = t
    if cur: lines.append(cur)
    return lines


def shadowed(img, fn, blur=6, alpha=180):
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
    fn(ImageDraw.Draw(sh), (0, 0, 0, alpha))
    img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(blur)))
    fn(ImageDraw.Draw(img), None)


def draw_runs(d, x, y, rs, f, col, anchor="la"):
    for t, c in rs:
        d.text((x, y), t, font=f, fill=col or c, anchor=anchor); x += d.textlength(t, font=f)


def brand(d, x, y, size, col, f):
    d.ellipse([x, y, x + size, y + size], fill=col or BRAND_RED)
    r = size / 2
    for k in range(3):
        cx = x + size * 1.55 + k * size * 0.62; rr = size * 0.21
        d.ellipse([cx - rr, y + r - rr, cx + rr, y + r + rr], outline=col or WHITE, width=max(2, int(size * 0.11)))
    d.text((x + size * 1.55 + 2 * size * 0.62 + size * 0.55, y + r), BRAND_NAME, font=f, fill=col or WHITE, anchor="lm")


# ------------------------------------------------------------------ 圖層
def gradient():
    g = Image.new("L", (1, H))
    for y in range(H):
        top = max(0, 1 - y / (H * 0.22)) * 150
        bot = max(0, (y - H * 0.55) / (H * 0.45)) ** 1.4 * 190
        g.putpixel((0, y), int(min(220, top + bot)))
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); lay.putalpha(g.resize((W, H)))
    return lay


def header(spec):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    fb = font(FONT_SANS, 22, "Medium"); ft = font(FONT_SANS, L["title_size"], "Black")
    title = spec.get("title", "")
    d0 = ImageDraw.Draw(img)
    while d0.textlength(plain(title), font=ft) > W - 2 * L["margin"] and ft.size > 30:
        ft = font(FONT_SANS, ft.size - 2, "Black")
    rs = runs(title, color=ORANGE)
    tw = d0.textlength(plain(title), font=ft)
    bw = 22 * 1.55 + 2 * 22 * 0.62 + 22 * 0.55 + d0.textlength(BRAND_NAME, font=fb)
    def fn(d, col):
        brand(d, (W - bw) / 2, L["brand_y"], 22, col, fb)
        draw_runs(d, (W - tw) / 2, L["title_y"], rs, ft, col)
    shadowed(img, fn, 5, 170)
    return img


def card_layer(card, big=False):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if not card:
        return img
    m = L["margin"]; size = L["hook_card_size"] if big else L["card_size"]
    ftag = font(FONT_SANS, 30, "Black"); fc = font(FONT_SANS, 28, "Medium")
    lines = card.get("text", "").split("\n")
    d0 = ImageDraw.Draw(img)
    fm = font(FONT_SANS, size, "Black")
    while max(d0.textlength(plain(l), font=fm) for l in lines) > W - 2 * m - 40 and fm.size > 44:
        fm = font(FONT_SANS, fm.size - 2, "Black")
    lh = int(fm.size * 1.22)
    # 字卡後面加一層左側暗色漸層，亮的 B-roll 上也讀得到
    top = L["card_tag_y"] - 50; bot = L["card_tag_y"] + (58 if card.get("tag") else 0) + lh * len(lines) + (70 if card.get("cite") else 0) + 50
    g = Image.new("L", (W, 1))
    for x in range(W): g.putpixel((x, 0), int(150 * max(0.0, 1 - x / (W * 0.95)) ** 0.8))
    band = Image.new("RGBA", (W, bot - top), (0, 0, 0, 0)); band.putalpha(g.resize((W, bot - top)).filter(ImageFilter.GaussianBlur(4)))
    fade = Image.new("L", (1, bot - top))
    for y in range(bot - top): fade.putpixel((0, y), int(255 * min(1, y / 40, (bot - top - y) / 40)))
    band.putalpha(Image.fromarray(__import__("numpy").minimum(__import__("numpy").array(band.getchannel("A")),
                                   __import__("numpy").array(fade.resize((W, bot - top))))))
    img.alpha_composite(band, (0, top))
    def fn(d, col):
        y = L["card_tag_y"]
        if card.get("tag"):
            d.rectangle([m, y + 6, m + 8, y + 36], fill=col or TAG_RED)
            d.text((m + 22, y), card["tag"], font=ftag, fill=col or TAG_RED); y += 58
        for l in lines:
            draw_runs(d, m, y, runs(l, card.get("hl"), color=ORANGE), fm, col); y += lh
        if card.get("cite"):
            d.text((m, y + 16), card["cite"], font=fc, fill=col or GREY)
    shadowed(img, fn, 7, 200)
    return img


def sub_layer(zh, en, hl=()):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if not zh and not en:
        return img
    d0 = ImageDraw.Draw(img)
    fz = font(FONT_SANS, L["zh_size"], "Bold"); fe = font(FONT_EN, L["en_size"], "Medium")
    zl = split_zh(zh, fz, L["text_w"], d0) if zh else []
    while zl and max(d0.textlength(plain(x), font=fz) for x in zl) > L["text_w"] and fz.size > 40:
        fz = font(FONT_SANS, fz.size - 2, "Bold")
    el = wrap_en(en, fe, L["text_w"], d0) if en else []
    lz, le = int(fz.size * 1.3), int(fe.size * 1.32)
    y0 = L["sub_bottom"] - (lz * len(zl) + (14 + le * len(el) if el else 0))
    def fn(d, col):
        y = y0
        for x in zl:
            w = d.textlength(plain(x), font=fz)
            draw_runs(d, (W - w) / 2, y, runs(x, hl, color=YELLOW), fz, col); y += lz
        y += 14
        for e in el:
            w = d.textlength(e, font=fe); d.text(((W - w) / 2, y), e, font=fe, fill=col or (240, 238, 232, 235)); y += le
    shadowed(img, fn, 5, 210)
    return img


def clip_layer(seg, fg_h):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    m = L["margin"]
    fl = font(FONT_SANS, 24, "Medium"); fp = font(FONT_SANS, 24, "Black")
    fn_ = font(FONT_SANS, 38, "Black"); fe = font(FONT_SANS, 27, "Medium")
    ty = L["clip_y"] + fg_h + 26
    name = f"{seg['speaker_en']}　{seg['speaker_zh']}"
    def fn(d, col):
        d.text((m - 30, L["clip_label_y"]), f"影片／{seg['channel']}", font=fl, fill=col or GREY)
        # 「原聲」紅色標籤
        tw = d.textlength("原聲", font=fp)
        d.rounded_rectangle([m - 30, ty, m - 30 + tw + 28, ty + 40], 8, fill=col or TAG_RED)
        d.text((m - 16, ty + 20), "原聲", font=fp, fill=col or WHITE, anchor="lm")
        d.text((m - 30, ty + 56), name, font=fn_, fill=col or WHITE)
        d.text((m - 30, ty + 108), f"{seg['event']}｜{seg['date']}", font=fe, fill=col or GREY)
    shadowed(img, fn, 5, 190)
    return img


def outro_layer(seg, credit_text):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    q = seg.get("question", "")
    lines = q.split("\n")
    d0 = ImageDraw.Draw(img)
    fq = font(FONT_SANS, 90, "Black")
    while max(d0.textlength(plain(l), font=fq) for l in lines) > W - 2 * L["margin"] and fq.size > 50:
        fq = font(FONT_SANS, fq.size - 2, "Black")
    fb = font(FONT_SANS, 28, "Medium"); fc = font(FONT_EN, 20, "Regular"); fh = font(FONT_SANS, 28, "Medium")
    def fn(d, col):
        y = L["outro_top"]
        if seg.get("tag"):
            tw = d.textlength(seg["tag"], font=fb)
            d.text(((W - tw) / 2, y - 64), seg["tag"], font=fb, fill=col or YELLOW)
        for l in lines:
            w = d.textlength(plain(l), font=fq)
            draw_runs(d, (W - w) / 2, y, runs(l, color=YELLOW), fq, col); y += int(fq.size * 1.25)
        y += 40
        bw = 28 * 1.55 + 2 * 28 * 0.62 + 28 * 0.55 + d.textlength(BRAND_NAME, font=fb)
        brand(d, (W - bw) / 2, y, 28, col, fb)
        hw = d.textlength(BRAND_HANDLE, font=fh); d.text(((W - hw) / 2, y + 48), BRAND_HANDLE, font=fh, fill=col or GREY)
        for k, cl in enumerate(credit_text.split("\n")):
            cw = d.textlength(cl, font=fc); d.text(((W - cw) / 2, L["credit_y"] + k * 26), cl, font=fc, fill=col or (225, 222, 215, 190))
    shadowed(img, fn, 7, 200)
    return img


# ------------------------------------------------------------------ 影像
def push_vf(d, z, focus=0.5):
    return (f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}:'(iw-{W})*{focus}':'(ih-{H})/2',fps={FPS},"
            f"scale=w='2*trunc({W}*(1+{z}*t/{d:.3f})/2)':h=-2:eval=frame:flags=bicubic,crop={W}:{H},{GRADE},setsar=1,format=yuv420p")


def render_broll(src, start, d, out, still=False, z=0.06, focus=0.5):
    cmd = ["ffmpeg", "-loglevel", "error", "-y"]
    if still:
        cmd += ["-loop", "1", "-framerate", str(FPS), "-t", f"{d:.3f}", "-i", src]
    else:
        ln = probe_duration(src)
        if ln < d + 0.2:
            cmd += ["-stream_loop", "-1"]; start = 0
        else:
            start = min(start, ln - d - 0.2)
        cmd += ["-ss", f"{start:.3f}", "-i", src]
    cmd += ["-t", f"{d:.3f}", "-an", "-vf", push_vf(d, z, focus), "-c:v", "libx264", "-preset", "veryfast", "-crf", "17",
            "-r", str(FPS), "-video_track_timescale", "15360", out]
    run(cmd)


def render_clip(src, d, out):
    fc = (f"[0:v]fps={FPS},split[a][b];[a]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
          f"boxblur=28:2,eq=brightness=-0.24:saturation=0.75[bg];[b]scale={W}:-2[fg];"
          f"[bg][fg]overlay=0:{L['clip_y']},setsar=1,format=yuv420p[v]")
    run(["ffmpeg", "-loglevel", "error", "-y", "-i", src, "-t", f"{d:.3f}", "-filter_complex", fc, "-map", "[v]", "-an",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "17", "-r", str(FPS), "-video_track_timescale", "15360", out])


def fg_height(src):
    o = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "csv=p=0", src],
                       capture_output=True, text=True).stdout.strip().split(",")
    w, h = int(o[0]), int(o[1])
    return int(round(W * h / w / 2) * 2)


# ------------------------------------------------------------------ 時間軸
def timeline(spec, work):
    man = load_json(work / "tts" / "manifest.json")
    if not man:
        raise SystemExit("先跑 tts.py")
    durs = {(m["seg"], m["line"]): m for m in man["lines"]}
    gap = float(spec.get("gap", 0.28))
    t, items, subs, problems, ncl = 0.0, [], [], [], 0
    for si, seg in enumerate(spec["segments"]):
        typ = seg["type"]
        if typ == "clip":
            ncl += 1
            d = float(seg["out"]) - float(seg["in"])
            src = str(work / "clips" / f"clip_{ncl}.mp4")
            items.append(dict(kind="clip", seg=si, n=ncl, start=t, dur=d, src=src, wav=str(work / "clips" / f"clip_{ncl}.wav")))
            ss = seg.get("subs")
            if not ss:
                tr = load_json(work / "clips" / f"clip_{ncl}.transcript.json", [])
                problems.append(f"clip {ncl}: 沒有 subs（中文翻譯），暫時只顯示英文轉錄")
                ss = [{"t": c["t"], "en": c["en"], "zh": ""} for c in tr]
            for k, s in enumerate(ss):
                a, b = float(s["t"][0]), float(s["t"][1])
                nxt = float(ss[k + 1]["t"][0]) if k + 1 < len(ss) else d
                subs.append(dict(st=t + max(0, a - 0.05), en_t=t + min(d, max(b, min(nxt - 0.08, b + 0.6))), zh=s.get("zh", ""),
                                 en=s.get("en", ""), hl=seg.get("highlight", []), seg=si, kind="clip"))
            t += d
            continue
        card = None
        for li, (text, chunks, ln) in enumerate(narr_lines(seg)):
            m = durs[(si, li)]; d = m["dur"]
            slot = d + float(ln.get("pause", gap))
            if "card" in ln:
                card = ln["card"] or None
            items.append(dict(kind="narr", seg=si, line=li, start=t, dur=slot, speech=d, audio=m["path"], card=card,
                              typ=typ, ln=ln))
            wts = [max(1, len(c[1].split())) for c in chunks]; acc = 0
            for (zh, en), wt in zip(chunks, wts):
                a = t + d * acc / sum(wts); acc += wt; b = t + d * acc / sum(wts)
                subs.append(dict(st=a, en_t=b if acc < sum(wts) else t + slot, zh=zh, en=en, hl=ln.get("hl", seg.get("highlight", [])),
                                 seg=si, kind=typ))
            t += slot
    total = t + float(spec.get("tail", 0.6))
    return items, subs, total, problems, man


def check(spec, items, total, problems):
    clip_t = sum(i["dur"] for i in items if i["kind"] == "clip")
    share = clip_t / total
    errs, warns = [], list(problems)
    if total > 180: errs.append(f"片長 {total:.1f}s 超過 3 分鐘")
    if share > 0.5: errs.append(f"原聲占 {share:.0%}，超過一半；解說要占多數")
    elif share > 0.4: warns.append(f"原聲占 {share:.0%}，建議 40% 以下")
    for i in items:
        if i["kind"] == "clip" and i["dur"] > 30: errs.append(f"clip {i['n']} {i['dur']:.1f}s > 30s")
    segs = spec["segments"]
    if segs[0]["type"] != "hook": warns.append("第一段不是 hook")
    else:
        hook_t = sum(i["dur"] for i in items if i["seg"] == 0)
        if hook_t > 12: warns.append(f"hook {hook_t:.1f}s，Fox 的開場約 11 秒內")
    if segs[-1]["type"] != "outro": warns.append("最後一段不是 outro（要拋問題給觀眾）")
    elif "？" not in segs[-1].get("question", ""): warns.append("outro.question 沒有問號")
    blob = str(spec)
    for b in ZH_BAD:
        if b in blob: errs.append(f"文字裡有破折號 {b!r}")
    if re.search(r'"[^"]*[\u4e00-\u9fff][^"]*"', "".join(s.get("zh", "") if isinstance(s.get("zh"), str) else "" for sg in segs for s in sg.get("lines", []))):
        warns.append("中文用了直引號，請改「」")
    return share, errs, warns


# ------------------------------------------------------------------ 主流程
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", required=True); ap.add_argument("--work", required=True); ap.add_argument("--out", required=True)
    ap.add_argument("--name", default="reel"); ap.add_argument("--check", action="store_true"); ap.add_argument("--no-cover", action="store_true")
    a = ap.parse_args()
    spec = load_json(a.spec); work = Path(a.work).resolve(); out = Path(a.out).resolve(); out.mkdir(parents=True, exist_ok=True)
    items, subs, total, problems, man = timeline(spec, work)
    share, errs, warns = check(spec, items, total, problems)
    print(f"total {total:.1f}s | clips {sum(i['dur'] for i in items if i['kind']=='clip'):.1f}s ({share:.0%}) | {len(items)} items, {len(subs)} subs")
    for w in warns: print("warn:", w)
    for e in errs: print("ERROR:", e)
    if a.check:
        for s in subs: print(f"  {s['st']:6.2f}-{s['en_t']:6.2f} [{s['kind']}] {s['zh']} || {s['en'][:70]}")
        return
    if errs: raise SystemExit("規則檢查沒過")
    tmp = work / "build"; tmp.mkdir(exist_ok=True)
    pool = load_json(work / "broll.json", {}) or {}
    use = {}

    # 1) 畫面
    cuts = []  # (path, dur, label, start)
    for it in items:
        seg = spec["segments"][it["seg"]]
        if it["kind"] == "clip":
            p = tmp / f"clip_{it['n']}.mp4"; render_clip(it["src"], it["dur"], str(p))
            it["fg_h"] = fg_height(it["src"]); cuts.append((p, it["dur"], f"clip{it['n']}", it["start"])); continue
        ln = it["ln"]
        mc = float(seg.get("max_cut", spec.get("max_cut", 2.4 if it["typ"] == "hook" else 3.2)))
        n = max(1, math.ceil(it["dur"] / mc - 0.15))
        srcs = []
        if ln.get("image"): srcs = [("still", x) for x in (ln["image"] if isinstance(ln["image"], list) else [ln["image"]])]
        elif ln.get("file"): srcs = [("file", x) for x in (ln["file"] if isinstance(ln["file"], list) else [ln["file"]])]
        else:
            kws = ln.get("broll") or seg.get("broll") or []
            for k in kws:
                srcs += [("pool", c) for c in pool.get(k, [])]
            if not srcs: raise SystemExit(f"segment {it['seg']} line {it['line']}: no b-roll（先跑 fetch_broll.py 或給 image/file）")
        for k in range(n):
            d = it["dur"] / n
            rk = f"rot{it['seg']}"; rot = use.setdefault(rk, 0); use[rk] += 1   # 同一段落輪流用不同素材
            kind, s = srcs[rot % len(srcs)]
            path = s["path"] if kind == "pool" else s
            cnt = use.setdefault(path, 0); use[path] += 1
            p = tmp / f"cut_{it['seg']:02d}_{it['line']:02d}_{k}.mp4"
            render_broll(path, 1.0 + cnt * 3.3, d, str(p), still=(kind == "still"), z=0.08 if kind == "still" else 0.06,
                         focus=float(ln.get("focus_x", 0.5)))
            if kind == "pool": s.setdefault("_used", True)
            cuts.append((p, d, f"s{it['seg']}l{it['line']}", it["start"] + k * d))
    tail = total - sum(c[1] for c in cuts)
    if tail > 0.02:  # 片尾多留的秒數：延長最後一格
        p0 = cuts[-1][0]; p = tmp / "cut_tail.mp4"
        run(["ffmpeg", "-loglevel", "error", "-y", "-sseof", "-0.05", "-i", p0, "-frames:v", "1", tmp / "last.png"])
        run(["ffmpeg", "-loglevel", "error", "-y", "-loop", "1", "-framerate", str(FPS), "-t", f"{tail:.3f}", "-i", tmp / "last.png",
             "-c:v", "libx264", "-preset", "veryfast", "-crf", "17", "-pix_fmt", "yuv420p", "-r", str(FPS), "-video_track_timescale", "15360", p])
        cuts.append((p, tail, "tail", total - tail))
    bgv = tmp / "bg.mp4"
    cc = ["ffmpeg", "-loglevel", "error", "-y"]
    for p, *_ in cuts: cc += ["-i", p]
    fc = "".join(f"[{k}:v]setpts=PTS-STARTPTS,setsar=1[c{k}];" for k in range(len(cuts)))
    fc += "".join(f"[c{k}]" for k in range(len(cuts))) + f"concat=n={len(cuts)}:v=1:a=0,fps={FPS}[v]"
    run(cc + ["-filter_complex", fc, "-map", "[v]", "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-pix_fmt", "yuv420p", bgv])

    # 2) 字層
    grad = gradient(); head = header(spec)
    base = Image.new("RGBA", (W, H), (0, 0, 0, 0)); base.alpha_composite(grad); base.alpha_composite(head)
    clips_meta = [load_json(work / "clips" / f"clip_{i['n']}.meta.json", {}) for i in items if i["kind"] == "clip"]
    credit_text = spec.get("credit_line") or credit_line(spec, clips_meta, man, pool)
    # 每個 item 的固定層（字卡／原聲標籤／片尾問題）
    fixed = {}
    for it in items:
        seg = spec["segments"][it["seg"]]
        key = (it["seg"], it.get("line", 0))
        im = base.copy()
        if it["kind"] == "clip": im.alpha_composite(clip_layer(seg, it["fg_h"]))
        elif it["typ"] == "outro": im.alpha_composite(outro_layer(seg, credit_text))
        else: im.alpha_composite(card_layer(it["card"], big=(it["typ"] == "hook")))
        fixed[key] = im
        it["key"] = key
    # 事件：每個 item 內，依字幕切
    events = []
    for it in items:
        st, en = it["start"], it["start"] + it["dur"]
        if it is items[-1]: en = total
        ss = [s for s in subs if s["seg"] == it["seg"] and s["st"] < en - 0.01 and s["en_t"] > st + 0.01]
        cur = st
        for s in ss:
            a_, b_ = max(st, s["st"]), min(en, s["en_t"])
            if a_ > cur + 0.01: events.append((fixed[it["key"]], a_ - cur)); cur = a_
            if b_ <= cur: continue
            im = fixed[it["key"]].copy(); im.alpha_composite(sub_layer(s["zh"], s["en"], s["hl"]))
            events.append((im, b_ - cur)); cur = b_
        if en > cur + 0.01: events.append((fixed[it["key"]], en - cur))
    ol = tmp / "overlay.txt"; lines = ["ffconcat version 1.0"]
    for k, (im, d) in enumerate(events):
        pth = tmp / f"ov_{k:03d}.png"; im.save(pth); lines += [f"file '{pth}'", f"duration {max(0.034, d):.3f}"]
    lines.append(f"file '{pth}'"); ol.write_text("\n".join(lines) + "\n")
    ovm = tmp / "overlay.mov"
    run(["ffmpeg", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", ol, "-vf", f"fps={FPS},format=rgba",
         "-t", f"{total:.3f}", "-c:v", "qtrle", ovm])

    # 3) 聲音：旁白＋原聲放在各自時間點，配樂在原聲段額外再壓低
    ins, fl = [], []
    for it in items:
        if it["kind"] == "clip":
            ins.append(it["wav"]); ms = int(it["start"] * 1000)
            fl.append(f"[{len(ins)-1}:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-16:TP=-2:LRA=11,aresample=48000,"
                      f"afade=t=in:d=0.06,afade=t=out:st={it['dur']-0.08:.3f}:d=0.08,adelay={ms}|{ms}[a{len(ins)-1}]")
        else:
            ins.append(it["audio"]); ms = int(it["start"] * 1000)
            fl.append(f"[{len(ins)-1}:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-16:TP=-2:LRA=11,aresample=48000,"
                      f"adelay={ms}|{ms}[a{len(ins)-1}]")
    nv = len(ins)
    fl.append("".join(f"[a{k}]" for k in range(nv)) + f"amix=inputs={nv}:normalize=0:duration=longest,apad,atrim=0:{total:.3f},asplit=2[vo][sc]")
    music = spec.get("music", "synth"); credits_music = None; mus = None
    if music == "synth":
        sys.path.insert(0, str(Path(os.environ.get("SKILLS_DIR", Path(__file__).resolve().parents[2])) / "stock-footage-reel" / "scripts")); import synth_music
        mus = str(tmp / "music.wav"); synth_music.make(total + 0.5, mus, bpm=spec.get("bpm", 80))
        credits_music = {"source": "Original code-synth track (stock-footage-reel/scripts/synth_music.py)", "license": "Own work"}
    elif music and music != "none":
        mus = music; credits_music = {"source": music, "license": spec.get("music_license", "CHECK")}
    if mus:
        ins.append(mus)
        clip_ranges = "+".join(f"between(t,{i['start']:.2f},{i['start']+i['dur']:.2f})" for i in items if i["kind"] == "clip") or "0"
        cdb = float(spec.get("clip_music_db", -8))
        fl.append(f"[{nv}:a]aresample=48000,aformat=channel_layouts=stereo,aloop=loop=-1:size=2e9,atrim=0:{total:.3f},"
                  f"volume={spec.get('music_db', -19)}dB,volume='if({clip_ranges},{10**(cdb/20):.3f},1)':eval=frame,"
                  f"afade=t=in:d=0.8,afade=t=out:st={total-2.2:.3f}:d=2.2[mu]")
        fl.append("[mu][sc]sidechaincompress=threshold=0.02:ratio=6:attack=25:release=450[duck]")
        fl.append("[vo][duck]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[aout]")
    else:
        fl.append("[sc]anullsink"); fl.append("[vo]loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[aout]")
    aud = tmp / "mix.wav"
    cmd = ["ffmpeg", "-loglevel", "error", "-y"]
    for p in ins: cmd += ["-i", p]
    run(cmd + ["-filter_complex", ";".join(fl), "-map", "[aout]", "-t", f"{total:.3f}", aud])

    final = out / f"{a.name}.mp4"
    cmd = ["ffmpeg", "-loglevel", "error", "-y", "-i", bgv, "-i", ovm, "-i", aud, "-filter_complex",
           "[0:v]setpts=PTS-STARTPTS[b];[1:v]setpts=PTS-STARTPTS[o];[b][o]overlay=0:0:eof_action=repeat:format=auto,format=yuv420p[v]",
           "-map", "[v]", "-map", "2:a", "-t", f"{total:.3f}", "-r", str(FPS), "-c:v", "libx264", "-preset", "medium",
           "-crf", str(spec.get("crf", 21)), "-profile:v", "high", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k",
           "-ar", "48000", "-movflags", "+faststart", final]
    run(cmd)
    size = final.stat().st_size / 1e6
    if size > 45:
        br = int(44 * 8e6 / total) - 170_000; c2 = list(cmd); j = c2.index("-crf")
        c2[j:j + 2] = ["-b:v", str(br), "-maxrate", str(br), "-bufsize", str(2 * br)]; run(c2); size = final.stat().st_size / 1e6
    prev = out / "preview_720p.mp4"
    run(["ffmpeg", "-loglevel", "error", "-y", "-i", final, "-vf", "scale=720:1280", "-c:v", "libx264", "-preset", "medium", "-crf", "27",
         "-c:a", "aac", "-b:a", "96k", "-movflags", "+faststart", prev])

    # 4) 聯絡表
    ims = []
    for p, d, lab, st in cuts:
        mid = st + d / 2
        r = subprocess.run(["ffmpeg", "-loglevel", "error", "-ss", f"{mid:.2f}", "-i", str(final), "-frames:v", "1", "-vf", "scale=270:-2",
                            "-f", "image2pipe", "-vcodec", "png", "-"], capture_output=True).stdout
        im = Image.open(io.BytesIO(r)).convert("RGB")
        ImageDraw.Draw(im).text((6, 4), f"{lab} @{mid:.1f}s", fill=(255, 230, 0), font=font(FONT_SANS, 18, "Bold")); ims.append(im)
    cols = min(6, len(ims)); rows = math.ceil(len(ims) / cols); tw, th = ims[0].size
    S = Image.new("RGB", (cols * tw, rows * th)); [S.paste(im, ((k % cols) * tw, (k // cols) * th)) for k, im in enumerate(ims)]
    S.save(out / "contact_sheet.jpg", quality=88)

    # 5) credits
    cl = []
    ncl = 0
    for it in items:
        if it["kind"] != "clip": continue
        seg = spec["segments"][it["seg"]]; meta = clips_meta[ncl]; ncl += 1
        fmt = lambda x: f"{int(x//3600):02d}:{int(x%3600//60):02d}:{x%60:05.2f}"
        cl.append(dict(speaker=f"{seg['speaker_en']}（{seg['speaker_zh']}）", channel=seg["channel"], youtube_channel=meta.get("channel"),
                       channel_url=meta.get("channel_url"), video_title=meta.get("title"), url=seg["url"], upload_date=meta.get("upload_date"),
                       event=seg["event"], date_on_screen=seg["date"], source_in=fmt(float(seg["in"])), source_out=fmt(float(seg["out"])),
                       clip_seconds=round(it["dur"], 2), placed_at=f"{it['start']:.2f}-{it['start']+it['dur']:.2f}s",
                       on_screen_credit=f"原聲 {seg['speaker_en']} {seg['speaker_zh']}｜{seg['event']}｜{seg['date']}；影片／{seg['channel']}",
                       license=seg.get("license", "YouTube 標準授權，著作權屬原頻道；未取得授權，以評論、引用方式短片段使用（著作權法第 52、65 條合理使用，屬灰色地帶）"),
                       official_source=seg.get("official", True)))
    used = []
    for k, lst in pool.items():
        for c in lst:
            if c.pop("_used", False) and not any(u["page"] == c["page"] for u in used): used.append(dict(c, keyword=k))
    credits = dict(interview_clips=cl, clips=used, voice=man["voice"], music=credits_music, credit_line=credit_text,
                   footage_share=round(share, 3), total_seconds=round(total, 2),
                   caption_credits=[f"・原聲：{c['speaker']}，{c['channel']}〈{(c['video_title'] or '').replace('—', ' - ')}〉{c['url']}（{c['source_in']} 到 {c['source_out']}）" for c in cl]
                   + ([f"・B-roll：Pexels（" + "、".join(sorted({u['author'] for u in used if u.get('author')})) + "）"] if used else []))
    save_json(out / "credits.json", credits)
    save_json(out / "timeline.json", dict(total=total, items=[{k: v for k, v in i.items() if k not in ("ln",)} for i in items], subs=subs))

    # 6) 封面（covers/render.py，樣板可選；預設 B，訪談建議 E＝對話裡說的「D 人物大頭」）
    if not a.no_cover and spec.get("cover"):
        cv = dict(spec["cover"]); fr = cv.pop("frame", {"clip": 1, "t": 3.0})
        src = work / "clips" / f"clip_{fr.get('clip', 1)}.mp4"; frame = out / "cover_frame.jpg"
        run(["ffmpeg", "-loglevel", "error", "-y", "-ss", f"{float(fr.get('t', 3.0)):.2f}", "-i", src, "-frames:v", "1", "-q:v", "2", frame])
        cv.setdefault("template", "E"); cv["visual"] = str(frame); cv["out"] = str(out / "cover")
        ch = spec["segments"][[s["type"] for s in spec["segments"]].index("clip")]["channel"]
        if cv["template"].upper() == "B": cv.setdefault("clip_credit", f"畫面：{ch} 官方影片")
        else: cv.setdefault("credit", f"畫面：{ch} 官方影片")
        sp = out / "cover_spec.json"; save_json(sp, cv)
        r = subprocess.run(["python3", str(COVERS / "render.py"), str(sp)], capture_output=True, text=True, cwd=str(COVERS))
        print(r.stdout.strip() or r.stderr[-800:])
    print(f"{final}  {probe_duration(final):.2f}s  {size:.1f} MB  | preview {prev.stat().st_size/1e6:.1f} MB | 原聲占 {share:.0%}")


def credit_line(spec, metas, man, pool):
    chans = []
    for s in spec["segments"]:
        if s["type"] == "clip" and s["channel"] not in chans: chans.append(s["channel"])
    parts = ["Interview clips: " + ", ".join(f"{c} (YouTube)" for c in chans)]
    if pool: parts.append("B-roll: Pexels")
    parts.append("Voice: ElevenLabs")
    return "  •  ".join(parts)


if __name__ == "__main__":
    main()
