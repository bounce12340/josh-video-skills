#!/usr/bin/env python3
"""封面產生器（josh-video-skills 用）。

用法：
  python render.py cover_spec.json            產生主封面 + 3–6 款封面選項和比較圖
  python render.py cover_spec.json --pick D   把主封面換成 D 款（挑完選項後用）

spec 欄位：
  template     主封面版型（預設 B）：
               B 剪報 Vox｜D 新聞海報｜E 人物大頭｜F 淺色資訊卡｜G 黑底雜誌｜H 上圖下字
               依題材選主封面：新聞 D、名人訪談 E、工具教學 F；B 只在指定時用
  variants     選項數量 3–6，或指定版型清單如 ["B","E","F"]；
               沒寫就讀環境變數 COVER_VARIANTS，預設 6
  ep           集數小標，例如 "試片"、"EP.12"
  kicker       標題上方的引言標籤
  title        主標，\n 換行，[[字]] 是重點字
  subtitle     副標（自動換行）
  clip_credit / credit   畫面來源小字
  visual       底圖路徑（沒有就用漸層代替）
  out          輸出前綴 <out>，產出：
                 <out>_reel.png（1080x1920）、<out>_post.png（1080x1350）  主封面
                 <out>_options/<版型>_reel.png、<版型>_post.png         各款選項
                 <out>_options/compare_reel.png、compare_post.png       比較圖
品牌字樣讀環境變數 BRAND_NAME、BRAND_HANDLE。
"""
import json
import math
import os
import re
import shutil
import sys
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

HERE = Path(__file__).resolve().parent
SANS = HERE / "fonts" / "NotoSansTC[wght].ttf"
SERIF = HERE / "fonts" / "NotoSerifTC[wght].ttf"
BRAND_NAME = os.environ.get("BRAND_NAME", "")
BRAND_HANDLE = os.environ.get("BRAND_HANDLE", "")
SIZES = {"reel": (1080, 1920), "post": (1080, 1350)}
NO_LINE_START = "，。、！？：；」』）》,.!?:;)"


@lru_cache(maxsize=None)
def font(path, size, weight):
    f = ImageFont.truetype(str(path), int(size))
    try:
        f.set_variation_by_axes([weight])
    except Exception:
        pass  # 非可變字型就用預設字重
    return f


def parse(line):
    """'把 AI 當成[[內部風險]]' -> [('把 AI 當成', False), ('內部風險', True)]"""
    parts = re.split(r"(\[\[.*?\]\])", line)
    return [(p[2:-2], True) if p.startswith("[[") else (p, False) for p in parts if p]


def fit_title(title, path, weight, max_w, max_size, min_size=56):
    lines = [parse(l) for l in title.split("\n")]
    size = max_size
    while size > min_size:
        f = font(path, size, weight)
        if max(sum(f.getlength(t) for t, _ in segs) for segs in lines) <= max_w:
            break
        size -= 4
    return lines, font(path, size, weight), size


def title_height(lines, size, lh):
    return int(size * lh * (len(lines) - 1) + size * 1.4)


def draw_title(d, lines, f, size, x, y, color, hl, mode, lh, center_w=None, hl_text=None):
    """重點字 mode：marker 螢光筆底線｜color 換色｜box 反白方塊（hl_text 是方塊裡的字色）｜underline 粗底線"""
    for segs in lines:
        lw = sum(f.getlength(t) for t, _ in segs)
        cx = x if center_w is None else (center_w - lw) / 2
        for t, is_hl in segs:
            w = f.getlength(t)
            fill = color
            if is_hl:
                l, tp, r, b = d.textbbox((cx, y), t, font=f)
                if mode == "marker":
                    d.rectangle([l - 10, tp + (b - tp) * 0.52, r + 10, b + 8], fill=hl)
                elif mode == "box":
                    d.rectangle([l - 12, tp - 10, r + 12, b + 14], fill=hl)
                    fill = hl_text or color
                elif mode == "underline":
                    d.rectangle([l, b + 10, r, b + 10 + max(6, size // 14)], fill=hl)
                else:
                    fill = hl
            d.text((cx, y), t, font=f, fill=fill)
            cx += w
        y += size * lh


def wrap(text, f, max_w):
    lines, cur = [], ""
    for ch in text:
        if ch == "\n":
            lines.append(cur)
            cur = ""
        elif cur and f.getlength(cur + ch) > max_w and ch not in NO_LINE_START:
            lines.append(cur)
            cur = ch
        else:
            cur += ch
    if cur:
        lines.append(cur)
    return lines


def text_block(d, spec, key, f, max_w, fill, lh, x, center_w=None):
    """副標區塊：回傳 (高度, 畫法)。沒有內容回傳 None。"""
    if not spec.get(key):
        return None
    sl = wrap(spec[key], f, max_w)

    def draw(y):
        for i, s in enumerate(sl):
            tx = x if center_w is None else (center_w - f.getlength(s)) / 2
            d.text((tx, y + i * f.size * lh), s, font=f, fill=fill)
    return int(len(sl) * f.size * lh), draw


def load_visual(path, w, h, centering=(0.5, 0.5)):
    if path and Path(path).exists():
        return ImageOps.fit(Image.open(path).convert("RGB"), (int(w), int(h)), Image.LANCZOS, centering=centering)
    g = Image.linear_gradient("L").resize((int(w), int(h)))
    return ImageOps.colorize(g, "#2b2b2b", "#8a8a8a")


def masked(im, shape, r=0):
    m = Image.new("L", im.size, 0)
    md = ImageDraw.Draw(m)
    box = [0, 0, im.width - 1, im.height - 1]
    md.ellipse(box, fill=255) if shape == "circle" else md.rounded_rectangle(box, radius=r, fill=255)
    out = im.convert("RGBA")
    out.putalpha(m)
    return out


def brand(d, x, y, size, color, accent, center_w=None, handle_color=None):
    """品牌記號：一顆圓點 + BRAND_NAME，下面一行 BRAND_HANDLE。"""
    if not BRAND_NAME:
        return
    f = font(SANS, size, 700)
    r = size * 0.32
    gap = size * 0.45
    total = 2 * r + gap + f.getlength(BRAND_NAME)
    if center_w is not None:
        x = (center_w - total) / 2
    d.ellipse([x, y - r, x + 2 * r, y + r], fill=accent)
    d.text((x + 2 * r + gap, y), BRAND_NAME, font=f, fill=color, anchor="lm")
    if BRAND_HANDLE:
        fh = font(SANS, size * 0.72, 500)
        hx = x + 2 * r + gap if center_w is None else (center_w - fh.getlength(BRAND_HANDLE)) / 2
        d.text((hx, y + size * 0.95), BRAND_HANDLE, font=fh, fill=handle_color or color)


def stack(blocks, top, bottom):
    """把 (高度, 畫法) 區塊垂直置中排在 top..bottom 之間。"""
    blocks = [b for b in blocks if b]
    total = sum(h for h, _ in blocks)
    y = top + max(0, (bottom - top - total) / 2)
    for h, fn in blocks:
        fn(y)
        y += h


def credit_of(spec):
    return spec.get("clip_credit") or spec.get("credit") or ""


# ---------- B：剪報 Vox ----------
def tmpl_b(spec, W, H):
    INK, PAPER, RED, MARK = (20, 20, 20), (239, 233, 221), (222, 56, 43), (255, 210, 63)
    noise = Image.effect_noise((W, H), 22).convert("RGB")
    img = Image.blend(Image.new("RGB", (W, H), PAPER), noise, 0.05)
    d = ImageDraw.Draw(img)
    M = 76
    reel = H > 1500
    blocks = []

    fk = font(SANS, 40 if reel else 34, 800)
    fe = font(SANS, 30 if reel else 26, 600)
    kh = int(fk.size * 1.7)

    def kicker(y):
        if spec.get("kicker"):
            tw = fk.getlength(spec["kicker"])
            d.rectangle([M, y, M + tw + 44, y + kh], fill=RED)
            d.text((M + 22, y + kh / 2), spec["kicker"], font=fk, fill="white", anchor="lm")
        if spec.get("ep"):
            d.text((W - M, y + kh / 2), f"EP. {spec['ep']}", font=fe, fill=(90, 90, 90), anchor="rm")
    blocks.append((kh + (48 if reel else 34), kicker))

    # 剪報：截圖貼在紙上，略為傾斜、白邊、陰影、膠帶
    cw = W - 2 * M - 20
    ch = int(H * (0.29 if reel else 0.27))
    clip = ImageOps.expand(load_visual(spec.get("visual"), cw, ch), border=14, fill="white").convert("RGBA")
    rot = clip.rotate(-2.2, resample=Image.BICUBIC, expand=True)
    tape = Image.new("RGBA", (200, 54), (245, 226, 160, 190)).rotate(5, resample=Image.BICUBIC, expand=True)
    credit = credit_of(spec)
    fc = font(SANS, 24 if reel else 22, 500)

    def clipping(y):
        sh = Image.new("RGBA", rot.size, (0, 0, 0, 0))
        sh.putalpha(rot.getchannel("A").point(lambda a: int(a * 0.42)))
        sh = sh.filter(ImageFilter.GaussianBlur(16))
        x = (W - rot.width) // 2
        img.paste(sh, (x + 10, int(y) + 18), sh)
        img.paste(rot, (x, int(y)), rot)
        img.paste(tape, ((W - tape.width) // 2, int(y) - 22), tape)
        if credit:
            d.text((W - M, y + rot.height + 14), credit, font=fc, fill=(110, 110, 110), anchor="ra")
    blocks.append((rot.height + (70 if reel else 54), clipping))

    lines, ft, size = fit_title(spec.get("title", ""), SANS, 900, W - 2 * M, 150 if reel else 116)
    blocks.append((title_height(lines, size, 1.2) + (30 if reel else 20),
                   lambda y: draw_title(d, lines, ft, size, M, y, INK, MARK, "marker", 1.2)))
    blocks.append(text_block(d, spec, "subtitle", font(SERIF, 46 if reel else 38, 600), W - 2 * M, (60, 60, 60), 1.45, M))

    bottom = H - (230 if reel else 170)
    stack(blocks, 90 if reel else 60, bottom)
    d.line([M, bottom + 30, W - M, bottom + 30], fill=INK, width=3)
    brand(d, M, bottom + 90, 40 if reel else 34, INK, RED, handle_color=(90, 90, 90))
    return img


# ---------- E：人物大頭 ----------
def tmpl_e(spec, W, H):
    YEL = (255, 210, 63)
    reel = H > 1500
    img = load_visual(spec.get("visual"), W, H, centering=(0.5, 0.3))
    # 底部漸層壓暗，讓字讀得清楚
    grad = Image.linear_gradient("L").resize((W, H)).point(lambda v: 0 if v < 105 else min(240, int((v - 105) * 2.1)))
    img.paste(Image.new("RGB", (W, H), (8, 8, 8)), (0, 0), grad)
    top = Image.linear_gradient("L").rotate(180).resize((W, 260)).point(lambda v: int(v * 0.55))
    img.paste(Image.new("RGB", (W, 260), (0, 0, 0)), (0, 0), top)
    d = ImageDraw.Draw(img)
    M = 72

    fsm = font(SANS, 26 if reel else 23, 500)
    if credit_of(spec):
        d.text((M, 70 if reel else 54), credit_of(spec), font=fsm, fill=(230, 230, 230))
    if spec.get("ep"):
        d.text((W - M, 70 if reel else 54), f"EP. {spec['ep']}", font=fsm, fill=(230, 230, 230), anchor="ra")

    blocks = []
    fk = font(SANS, 38 if reel else 32, 800)
    kh = int(fk.size * 1.7)
    if spec.get("kicker"):
        def kicker(y):
            tw = fk.getlength(spec["kicker"])
            d.rounded_rectangle([M, y, M + tw + 48, y + kh], radius=kh // 2, fill=YEL)
            d.text((M + 24, y + kh / 2), spec["kicker"], font=fk, fill=(15, 15, 15), anchor="lm")
        blocks.append((kh + 30, kicker))

    lines, ft, size = fit_title(spec.get("title", ""), SANS, 900, W - 2 * M, 160 if reel else 124)
    blocks.append((title_height(lines, size, 1.16) + 24,
                   lambda y: draw_title(d, lines, ft, size, M, y, "white", YEL, "color", 1.16)))
    blocks.append(text_block(d, spec, "subtitle", font(SANS, 44 if reel else 36, 500), W - 2 * M, (225, 225, 225), 1.45, M))

    # 字塊貼底排（reel 停在 IG 4:5 裁切線上方）
    bottom = H - (330 if reel else 190)
    total = sum(b[0] for b in blocks if b)
    stack(blocks, bottom - total, bottom)
    brand(d, 0, H - (230 if reel else 100), 34 if reel else 28, "white", YEL, center_w=W, handle_color=(200, 200, 200))
    return img


# ---------- G：黑底雜誌 ----------
def tmpl_g(spec, W, H):
    BG, ACC, FG = (14, 14, 14), (255, 90, 54), (242, 236, 226)
    reel = H > 1500
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    M = 80
    blocks = []

    fk = font(SANS, 34 if reel else 30, 700)

    def head(y):
        if spec.get("ep"):
            d.text((M, y), f"EP. {spec['ep']}", font=fk, fill=ACC)
        if spec.get("kicker"):
            d.text((W - M, y), spec["kicker"], font=fk, fill=(170, 170, 170), anchor="ra")
        d.line([M, y + fk.size * 1.6, W - M, y + fk.size * 1.6], fill=(80, 80, 80), width=2)
    blocks.append((int(fk.size * 1.6) + (56 if reel else 40), head))

    lines, ft, size = fit_title(spec.get("title", ""), SERIF, 900, W - 2 * M, 158 if reel else 120)
    blocks.append((title_height(lines, size, 1.22) + (30 if reel else 20),
                   lambda y: draw_title(d, lines, ft, size, M, y, FG, ACC, "color", 1.22)))
    sub = text_block(d, spec, "subtitle", font(SANS, 42 if reel else 34, 400), W - 2 * M, (185, 185, 185), 1.5, M)
    if sub:
        blocks.append((sub[0] + (60 if reel else 36), sub[1]))

    # 雙色調畫面條
    vh = int(H * (0.27 if reel else 0.24))
    g = ImageOps.grayscale(load_visual(spec.get("visual"), W - 2 * M, vh))
    strip = ImageOps.colorize(ImageOps.autocontrast(g, cutoff=1), black=BG, mid=(120, 44, 30), white=FG)
    fc = font(SANS, 24 if reel else 21, 400)

    def visual(y):
        img.paste(strip, (M, int(y)))
        if credit_of(spec):
            d.text((M, y + vh + 14), credit_of(spec), font=fc, fill=(120, 120, 120))
    blocks.append((vh + 60, visual))

    bottom = H - (220 if reel else 150)
    stack(blocks, 100 if reel else 64, bottom)
    brand(d, M, bottom + 80, 36 if reel else 30, FG, ACC, handle_color=(140, 140, 140))
    return img


# ---------- D：新聞海報（黃底大字報） ----------
def tmpl_d(spec, W, H):
    YEL, INK, RED = (255, 210, 63), (17, 17, 17), (222, 56, 43)
    reel = H > 1500
    img = Image.new("RGB", (W, H), YEL)
    d = ImageDraw.Draw(img)
    M = 76
    blocks = []

    fk = font(SANS, 36 if reel else 30, 800)

    def head(y):
        if spec.get("kicker"):
            d.text((M, y), spec["kicker"], font=fk, fill=INK)
        if spec.get("ep"):
            d.text((W - M, y), f"EP. {spec['ep']}", font=fk, fill=INK, anchor="ra")
        ly = y + fk.size * 1.6
        d.rectangle([M, ly, W - M, ly + 7], fill=INK)
    blocks.append((int(fk.size * 1.6) + (64 if reel else 44), head))

    lines, ft, size = fit_title(spec.get("title", ""), SANS, 900, W - 2 * M - 24, 172 if reel else 128)
    blocks.append((title_height(lines, size, 1.22) + (26 if reel else 18),
                   lambda y: draw_title(d, lines, ft, size, M + 12, y, INK, INK, "box", 1.22, hl_text=YEL)))
    sub = text_block(d, spec, "subtitle", font(SANS, 44 if reel else 36, 600), W - 2 * M, INK, 1.45, M)
    if sub:
        blocks.append((sub[0] + (56 if reel else 34), sub[1]))

    # 黑白照片，圓角
    vh = int(H * (0.24 if reel else 0.2))
    photo = ImageOps.autocontrast(ImageOps.grayscale(load_visual(spec.get("visual"), W - 2 * M, vh, centering=(0.5, 0.35))), cutoff=1)
    photo = masked(photo.convert("RGB"), "round", 28)
    fc = font(SANS, 23 if reel else 20, 500)

    def visual(y):
        img.paste(photo, (M, int(y)), photo)
        if credit_of(spec):
            d.text((W - M, y + vh + 12), credit_of(spec), font=fc, fill=(70, 60, 20), anchor="ra")
    blocks.append((vh + 50, visual))

    bottom = H - (220 if reel else 150)
    stack(blocks, 100 if reel else 64, bottom)
    brand(d, M, bottom + 80, 38 if reel else 32, INK, RED, handle_color=(70, 60, 20))
    return img


# ---------- H：上圖下字 ----------
def tmpl_h(spec, W, H):
    NAVY, ACC, FG = (19, 35, 58), (255, 122, 89), (255, 255, 255)
    reel = H > 1500
    ph = int(H * (0.5 if reel else 0.46))
    img = Image.new("RGB", (W, H), NAVY)
    img.paste(load_visual(spec.get("visual"), W, ph, centering=(0.5, 0.35)), (0, 0))
    d = ImageDraw.Draw(img)
    M = 72

    fsm = font(SANS, 25 if reel else 22, 500)
    if spec.get("ep"):
        d.text((M, 64 if reel else 48), f"EP. {spec['ep']}", font=fsm, fill="white", stroke_width=2, stroke_fill=(0, 0, 0))
    if credit_of(spec):
        d.text((W - M, ph - 70), credit_of(spec), font=fsm, fill="white", anchor="ra", stroke_width=2, stroke_fill=(0, 0, 0))

    # 引言標籤壓在圖文交界
    fk = font(SANS, 38 if reel else 32, 800)
    kh = int(fk.size * 1.7)
    if spec.get("kicker"):
        tw = fk.getlength(spec["kicker"])
        d.rectangle([M, ph - kh // 2, M + tw + 48, ph + kh // 2], fill=ACC)
        d.text((M + 24, ph), spec["kicker"], font=fk, fill=NAVY, anchor="lm")

    blocks = []
    lines, ft, size = fit_title(spec.get("title", ""), SANS, 900, W - 2 * M, 146 if reel else 104)
    blocks.append((title_height(lines, size, 1.18) + (26 if reel else 16),
                   lambda y: draw_title(d, lines, ft, size, M, y, FG, ACC, "color", 1.18)))
    blocks.append(text_block(d, spec, "subtitle", font(SANS, 42 if reel else 32, 500), W - 2 * M, (190, 202, 220), 1.45, M))

    bottom = H - (230 if reel else 140)
    stack(blocks, ph + kh // 2 + 30, bottom)
    brand(d, M, bottom + 70, 36 if reel else 28, FG, ACC, handle_color=(150, 165, 190))
    return img


# ---------- F：淺色資訊卡（白底極簡） ----------
def tmpl_f(spec, W, H):
    BG, INK, ACC = (250, 249, 246), (20, 20, 20), (37, 99, 235)
    reel = H > 1500
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    M = 90
    blocks = []

    dia = 480 if reel else 300
    photo = masked(load_visual(spec.get("visual"), dia, dia, centering=(0.5, 0.3)), "circle")
    fc = font(SANS, 23 if reel else 20, 400)

    def visual(y):
        x = (W - dia) // 2
        d.ellipse([x - 12, y - 12, x + dia + 12, y + dia + 12], outline=ACC, width=4)
        img.paste(photo, (x, int(y)), photo)
        if credit_of(spec):
            d.text((W / 2, y + dia + 30), credit_of(spec), font=fc, fill=(140, 140, 140), anchor="ma")
    blocks.append((dia + (110 if reel else 74), visual))

    fk = font(SANS, 32 if reel else 28, 600)
    head = "　｜　".join(s for s in [spec.get("kicker", ""), f"EP. {spec['ep']}" if spec.get("ep") else ""] if s)
    if head:
        blocks.append((int(fk.size * 1.4) + (34 if reel else 22), lambda y: d.text((W / 2, y), head, font=fk, fill=(120, 120, 120), anchor="ma")))

    lines, ft, size = fit_title(spec.get("title", ""), SERIF, 900, W - 2 * M, 140 if reel else 104)
    blocks.append((title_height(lines, size, 1.3) + (36 if reel else 24),
                   lambda y: draw_title(d, lines, ft, size, 0, y, INK, ACC, "underline", 1.3, center_w=W)))
    blocks.append(text_block(d, spec, "subtitle", font(SANS, 40 if reel else 32, 400), W - 2 * M, (90, 90, 90), 1.5, 0, center_w=W))

    bottom = H - (220 if reel else 150)
    stack(blocks, 100 if reel else 60, bottom)
    brand(d, 0, bottom + 80, 34 if reel else 28, INK, ACC, center_w=W, handle_color=(130, 130, 130))
    return img


TEMPLATES = {"B": tmpl_b, "D": tmpl_d, "E": tmpl_e, "F": tmpl_f, "G": tmpl_g, "H": tmpl_h}
NAMES = {"B": "剪報 Vox", "D": "新聞海報", "E": "人物大頭", "F": "淺色資訊卡", "G": "黑底雜誌", "H": "上圖下字"}


def pick_variants(spec, main):
    v = spec.get("variants", os.environ.get("COVER_VARIANTS", len(TEMPLATES)))
    if isinstance(v, list):
        order = [str(t).upper() for t in v]
        n = max(1, len(order))
    else:
        order = list(TEMPLATES)
        n = max(3, min(len(TEMPLATES), int(v)))
    return list(dict.fromkeys([main] + [t for t in order if t in TEMPLATES]))[:n]


def contact_sheet(opt_dir, ts, kind, main):
    """把各款選項排成一張比較圖，主封面標「目前」。"""
    w, h = (360, 640) if kind == "reel" else (360, 450)
    cols = min(3, len(ts))
    rows = math.ceil(len(ts) / cols)
    G, L = 24, 52
    sheet = Image.new("RGB", (cols * w + (cols + 1) * G, rows * (h + L + G) + G), (245, 245, 245))
    d = ImageDraw.Draw(sheet)
    f = font(SANS, 26, 700)
    for i, t in enumerate(ts):
        x, y = G + (i % cols) * (w + G), G + (i // cols) * (h + L + G)
        d.text((x, y + 8), f"{t}  {NAMES[t]}" + ("（目前）" if t == main else ""), font=f, fill=(20, 20, 20))
        sheet.paste(Image.open(opt_dir / f"{t}_{kind}.png").resize((w, h), Image.LANCZOS), (x, y + L))
    p = opt_dir / f"compare_{kind}.png"
    sheet.save(p)
    return p


def main():
    sys.stdout.reconfigure(encoding="utf-8")  # Windows 主控台預設 cp950，中文會變亂碼
    args = sys.argv[1:]
    pick = None
    if "--pick" in args:
        i = args.index("--pick")
        pick = args[i + 1].upper() if i + 1 < len(args) else ""
        del args[i:i + 2]
    if len(args) != 1:
        sys.exit("用法：python render.py cover_spec.json [--pick 版型]")
    spec = json.loads(Path(args[0]).read_text(encoding="utf-8"))
    main_t = pick or str(spec.get("template", "B")).upper()
    if main_t not in TEMPLATES:
        sys.exit(f"不認得的版型：{main_t}（可用：{'、'.join(f'{k} {v}' for k, v in NAMES.items())}）")

    out = Path(spec.get("out", "cover"))
    out.parent.mkdir(parents=True, exist_ok=True)
    opt_dir = out.parent / f"{out.name}_options"

    if pick:  # 只換主封面：有現成選項就直接複製，沒有就重畫
        for kind, (W, H) in SIZES.items():
            dst = out.parent / f"{out.name}_{kind}.png"
            src = opt_dir / f"{pick}_{kind}.png"
            shutil.copyfile(src, dst) if src.exists() else TEMPLATES[pick](spec, W, H).save(dst)
            print(dst)
        print(f"主封面已換成 {pick} {NAMES[pick]}")
        return

    opt_dir.mkdir(exist_ok=True)
    ts = pick_variants(spec, main_t)
    for t in ts:
        for kind, (W, H) in SIZES.items():
            TEMPLATES[t](spec, W, H).save(opt_dir / f"{t}_{kind}.png")
    for kind in SIZES:
        dst = out.parent / f"{out.name}_{kind}.png"
        shutil.copyfile(opt_dir / f"{main_t}_{kind}.png", dst)
        print(dst)
        contact_sheet(opt_dir, ts, kind, main_t)
    print(f"封面選項 {len(ts)} 款（{'、'.join(f'{t} {NAMES[t]}' for t in ts)}）：{opt_dir}")
    print(f"比較圖：{opt_dir / 'compare_reel.png'}、{opt_dir / 'compare_post.png'}；挑好後用 --pick <版型> 換主封面")


if __name__ == "__main__":
    main()
