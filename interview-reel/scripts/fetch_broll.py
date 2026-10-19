#!/usr/bin/env python3
"""第 3 步：解說段落的 B-roll。每個關鍵字從 Pexels 抓幾支（可商用、免標註，仍記進 credits），快取在 stock-footage-reel 的 cache/pexels。
也可以在 line 裡直接指定 "image"（靜態圖，會做緩慢推近）或 "file"（本機影片，例如 screen-record 錄好的網頁）。

用法：python fetch_broll.py --spec spec.json --work WORK [--per 3]
輸出 WORK/broll.json：{keyword: [ {path, page, author, license, ...}, ... ]}
"""
import argparse, json, os, sys, urllib.parse
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from ir_common import load_json, save_json, http_get, download  # noqa
from common import CACHE as SFR_CACHE  # stock-footage-reel 的素材快取，同一支不重抓  # noqa


def pexels_many(q, n, min_dur=4.0):
    key = os.environ.get("PEXELS_API_KEY")
    if not key:
        raise SystemExit("PEXELS_API_KEY not set（新開 bash -lc 或 source om-env.sh）")
    out = []
    for orient in ("landscape", "portrait"):   # 橫式素材多、關鍵字比較準，裁成直式即可
        url = "https://api.pexels.com/videos/search?" + urllib.parse.urlencode(
            {"query": q, "per_page": 15, "orientation": orient, "size": "medium"})
        d = json.loads(http_get(url, headers={"Authorization": key}))
        for v in d.get("videos", []):
            if len(out) >= n:
                break
            if v.get("duration", 0) < min_dur or any(o["id"] == str(v["id"]) for o in out):
                continue
            files = [f for f in v["video_files"] if f.get("file_type") == "video/mp4" and (f.get("height") or 0) >= 720]
            if not files:
                continue
            f = sorted(files, key=lambda f: abs((f.get("height") or 0) - 1920))[0]
            dest = SFR_CACHE / "pexels" / f"{v['id']}_{f['height']}.mp4"
            download(f["link"], dest)
            out.append(dict(path=str(dest), source="Pexels", id=str(v["id"]), title=v["url"].rstrip("/").split("/")[-1],
                            page=v["url"], author=v.get("user", {}).get("name", ""), duration=v.get("duration"),
                            license="Pexels License (free for commercial use; attribution not required)",
                            license_url="https://www.pexels.com/license/"))
        if len(out) >= n:
            break
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", required=True); ap.add_argument("--work", required=True)
    ap.add_argument("--per", type=int, default=3); ap.add_argument("--refresh", action="store_true")
    a = ap.parse_args()
    spec = load_json(a.spec); work = Path(a.work); work.mkdir(parents=True, exist_ok=True)
    bj = work / "broll.json"; pool = {} if a.refresh else (load_json(bj, {}) or {})
    kws = []
    for seg in spec["segments"]:
        for k in seg.get("broll", []):
            kws.append(k)
        for ln in seg.get("lines", []):
            for k in ln.get("broll", []):
                kws.append(k)
    for k in dict.fromkeys(kws):
        if k in pool and pool[k]:
            continue
        pool[k] = pexels_many(k, a.per)
        print(f"{k!r}: {len(pool[k])} clips  " + ", ".join(c['page'] for c in pool[k]))
        if not pool[k]:
            print(f"note: no Pexels result for {k!r}; 換更具體的畫面關鍵字")
    save_json(bj, pool)


if __name__ == "__main__":
    main()
