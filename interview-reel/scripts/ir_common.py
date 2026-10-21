"""interview-reel 共用：路徑、字型、版面、JSON、ffmpeg helpers。沿用 stock-footage-reel/scripts/common.py。"""
import hashlib, json, os, subprocess, sys
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
SKILLS_DIR = Path(os.environ.get("SKILLS_DIR", Path(__file__).resolve().parents[2]))  # 放所有 skill 的資料夾
SFR = SKILLS_DIR / "stock-footage-reel" / "scripts"
sys.path.insert(0, str(SFR))
from common import (font, FONT_SANS, FONT_SERIF, COVERS, load_json, save_json, probe_duration, download,  # noqa
                    http_get, WHITE, BRAND_RED, check_config)

CACHE = SKILL / "cache"
FONT_EN = "/usr/share/fonts/truetype/sand-box/google/Noto Sans/NotoSans-VariableFont_wdth,wght.ttf"
FPS = 30
W, H = 1080, 1920
YELLOW = (255, 214, 10)      # 字幕重點字（D／E 新聞風同一個黃 #FFD60A）
ORANGE = (255, 122, 48)      # 字卡重點字、標題重點字
TAG_RED = (232, 58, 48)      # 字卡上方小分類標籤
GREY = (214, 210, 202)

# 版面（1080x1920，IG 上方約 220px、下方約 380px、右側約 130px 會被介面蓋住）
L = dict(brand_y=214, title_y=252, title_size=44,
         card_tag_y=470, card_size=78, hook_card_size=96,
         clip_label_y=424, clip_y=468, src_tag_y=1098,
         sub_bottom=1490, zh_size=60, en_size=32, text_w=900, margin=72,
         outro_top=600, credit_y=1508)

VOICE_ID = "Nhs7eitvQWFTQBsf0yiT"   # Sarah Explains
VOICE_MODEL = "eleven_multilingual_v2"


def run(cmd, quiet=True):
    r = subprocess.run([str(c) for c in cmd], capture_output=True, text=True)
    if r.returncode:
        print(" ".join(map(str, cmd))[:1500]); print(r.stderr[-3000:])
        raise SystemExit("command failed")
    return r


def sha(s):
    return hashlib.sha1(s.encode("utf-8")).hexdigest()[:16]


def yt_id(url):
    import re
    m = re.search(r"(?:v=|youtu\.be/|shorts/|live/)([\w-]{11})", url)
    return m.group(1) if m else sha(url)


def narr_lines(seg):
    """narration 類段落的每一行：回傳 [(en_tts_text, [(zh, en_chunk), ...], line_dict)]"""
    out = []
    for ln in seg.get("lines", []):
        en, zh = ln["en"], ln["zh"]
        ens = en if isinstance(en, list) else [en]
        zhs = zh if isinstance(zh, list) else [zh]
        if len(ens) != len(zhs):
            raise SystemExit(f"line en/zh chunk count mismatch: {en!r} / {zh!r}")
        out.append((" ".join(ens), list(zip(zhs, ens)), ln))
    return out
