#!/usr/bin/env python3
"""下載封面和字幕用的字型到 covers/fonts/（Google Fonts 官方 repo，SIL OFL 授權）。

用法：python fetch_fonts.py
字型檔很大（約 30 MB），所以不放進 git。
"""
import urllib.request
from pathlib import Path

BASE = "https://github.com/google/fonts/raw/main/ofl/"
FONTS = {
    "NotoSansTC[wght].ttf": "notosanstc/NotoSansTC%5Bwght%5D.ttf",
    "NotoSerifTC[wght].ttf": "notoseriftc/NotoSerifTC%5Bwght%5D.ttf",
    "NotoSans[wdth,wght].ttf": "notosans/NotoSans%5Bwdth,wght%5D.ttf",
}

out = Path(__file__).resolve().parent / "fonts"
out.mkdir(exist_ok=True)
for name, src in FONTS.items():
    dst = out / name
    if dst.exists():
        print(f"已有 {name}")
        continue
    urllib.request.urlretrieve(BASE + src, dst)
    print(f"下載 {name}（{dst.stat().st_size / 1e6:.1f} MB）")
