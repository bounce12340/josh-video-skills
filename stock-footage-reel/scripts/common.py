"""Shared helpers for stock-footage-reel: paths, fonts, layout, HTTP, script parsing."""
import json, os, re, subprocess, time, urllib.request, urllib.parse
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
CACHE = Path(os.environ.get("SFR_CACHE", SKILL / "cache"))
COVERS = Path(os.environ.get("COVERS_DIR", SKILL.parent / "covers"))  # 放封面 render.py 和 fonts/ 的資料夾，預設用 repo 裡的 covers/
FONT_SANS = str(COVERS / "fonts" / "NotoSansTC[wght].ttf")
FONT_SERIF = str(COVERS / "fonts" / "NotoSerifTC[wght].ttf")
# 英文字型：沙盒有系統 Noto Sans 就用，否則用 covers/fonts/（covers/fetch_fonts.py 下載）
_FONT_EN_SYS = "/usr/share/fonts/truetype/sand-box/google/Noto Sans/NotoSans-VariableFont_wdth,wght.ttf"
FONT_EN = _FONT_EN_SYS if os.path.exists(_FONT_EN_SYS) else str(COVERS / "fonts" / "NotoSans[wdth,wght].ttf")
UA = os.environ.get("SFR_USER_AGENT", "stock-footage-reel/1.0 (+<YOUR_CONTACT_URL>; low-volume, cached)")
BROWSER_UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36"

GOLD = (233, 164, 74)        # 重點字顏色（對齊 AYi 的金橘色）
BRAND_RED = (210, 35, 28)    # B 剪報 Vox 封面系統的紅色 #D2231C
WHITE = (246, 243, 238)

# 版面：所有座標都依格式換算。IG Reel 1080x1920：上方約 220px、下方約 380px、右側約 130px 會被 IG 介面蓋住。
LAYOUTS = {
    "1080x1920": dict(W=1080, H=1920, header_y=232, sub_bottom=1490, margin=72, text_w=880,
                      zh_size=64, en_size=34, end_top=640, credit_y=1500),
    "1080x1350": dict(W=1080, H=1350, header_y=58, sub_bottom=1150, margin=64, text_w=900,
                      zh_size=58, en_size=31, end_top=420, credit_y=1260),
}


PLACEHOLDER_MARKERS = ("<YOUR_", "@your_handle", "你的名字", "你的品牌")


def check_config(**values):
    """Stop with a clear message if any setting still holds a template placeholder.

    Always checks COVERS_DIR and SFR_USER_AGENT; callers pass extra name=value pairs (e.g. BRAND_NAME)."""
    values = {"COVERS_DIR": str(COVERS), "SFR_USER_AGENT": UA, **values}
    bad = [f"  {k} = {v!r}" for k, v in values.items() if any(m in str(v) for m in PLACEHOLDER_MARKERS)]
    if bad:
        raise SystemExit("config error: these settings still use template placeholders:\n" + "\n".join(bad) +
                         "\nSet them as environment variables (see README.md, 'Settings to fill in yourself'), e.g.\n"
                         "  export BRAND_NAME='Josh｜AI 一人公司' BRAND_HANDLE='@bounce12340' COVERS_DIR=/path/to/covers \\\n"
                         "         SFR_USER_AGENT='stock-footage-reel/1.0 (+https://your.site; low-volume, cached)'")


def layout(fmt):
    if fmt not in LAYOUTS:
        raise SystemExit(f"format must be one of {list(LAYOUTS)}")
    return LAYOUTS[fmt]


def font(path, size, weight="Bold"):
    from PIL import ImageFont
    f = ImageFont.truetype(path, size)
    try:
        f.set_variation_by_name(weight)
    except Exception:
        pass
    return f


def http_get(url, headers=None, timeout=60, retries=3, delay=1.0, binary=False, browser=False):
    h = {"User-Agent": BROWSER_UA if browser else UA}
    h.update(headers or {})
    last = None
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers=h)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                data = r.read()
            time.sleep(delay)  # 禮貌間隔
            return data if binary else data.decode("utf-8", "replace")
        except Exception as e:  # noqa
            last = e
            time.sleep(2 * (i + 1))
    raise RuntimeError(f"GET failed {url}: {last}")


def download(url, dest, headers=None, browser=False):
    dest = Path(dest)
    if dest.exists() and dest.stat().st_size > 10000:
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    cmd = ["curl", "-sSL", "--fail", "-m", "900", "--retry", "3", "-A", BROWSER_UA if browser else UA, "-o", str(tmp), url]
    for k, v in (headers or {}).items():
        cmd[1:1] = ["-H", f"{k}: {v}"]
    subprocess.run(cmd, check=True)
    tmp.rename(dest)
    return dest


def read_script(path):
    """script.txt：一行一鏡。接受「[1] 文字」或純文字行，空行略過。"""
    lines = []
    for raw in Path(path).read_text(encoding="utf-8").splitlines():
        s = raw.strip()
        if not s:
            continue
        s = re.sub(r"^\[\d+\]\s*", "", s)
        lines.append(s)
    return lines


def probe_duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                         capture_output=True, text=True).stdout.strip()
    return float(out or 0)


def load_json(p, default=None):
    p = Path(p)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else default


def save_json(p, obj):
    Path(p).write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
