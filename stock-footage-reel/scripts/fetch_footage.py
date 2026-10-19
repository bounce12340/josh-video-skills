#!/usr/bin/env python3
"""Search + download one footage clip per shot, with license checks. Writes <work>/footage.json and <work>/credits.json.

用法：
  python3 fetch_footage.py --shots shots.json --work WORK_DIR [--only 3] [--refresh] [--allow-mixkit-restricted]
  python3 fetch_footage.py --sheet archive:OnGuard1956 --work WORK_DIR      # 產生 Prelinger 影片每 15 秒一格的挑選圖
  python3 fetch_footage.py --sheet path/to/clip.mp4 --work WORK_DIR

來源順序（shot.source = "auto" 時）：
  一般鏡頭：pexels（有 PEXELS_API_KEY 才用）→ pixabay（有 PIXABAY_API_KEY 才用）→ mixkit（只收 Free License）→ commons（PD/CC0/CC BY）→ synth（本機產生）
  archival 鏡頭：archive（Internet Archive Prelinger，公有領域）→ commons
每個 shot 可用 "pick" 指定：{"source":"archive","id":"OnGuard1956","start":630} 或 {"source":"mixkit","id":"23215"}
或 {"source":"commons","title":"File:xxx.webm","start":12} 或 {"source":"file","path":"/abs/clip.mp4","license":"...","credit":"..."}
或 {"source":"synth","kind":"code"}。
"""
import argparse, json, os, re, subprocess, sys, html, urllib.parse
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from common import CACHE, http_get, download, probe_duration, load_json, save_json  # noqa

MIN_DUR = 3.0

# ---------------------------------------------------------------- Pexels
def pexels(q, need, portrait):
    key = os.environ.get("PEXELS_API_KEY")
    if not key:
        return None
    url = "https://api.pexels.com/videos/search?" + urllib.parse.urlencode(
        {"query": q, "per_page": 15, "orientation": "portrait" if portrait else "landscape", "size": "medium"})
    d = json.loads(http_get(url, headers={"Authorization": key}))
    for v in d.get("videos", []):
        if v.get("duration", 0) < max(MIN_DUR, need * 0.6):
            continue
        files = [f for f in v["video_files"] if f.get("file_type") == "video/mp4" and (f.get("height") or 0) >= 720]
        if not files:
            continue
        f = sorted(files, key=lambda f: abs((f.get("height") or 0) - 1920))[0]
        dest = CACHE / "pexels" / f"{v['id']}_{f['height']}.mp4"
        download(f["link"], dest)
        return dict(path=str(dest), source="Pexels", id=str(v["id"]), title=v["url"].rstrip("/").split("/")[-1], page=v["url"], author_url=v.get("user", {}).get("url", ""),
                    author=v.get("user", {}).get("name", ""), license="Pexels License (free for commercial use; attribution not required but appreciated)",
                    license_url="https://www.pexels.com/license/", start=0.0)
    return None

# ---------------------------------------------------------------- Pixabay
def pixabay(q, need, portrait):
    key = os.environ.get("PIXABAY_API_KEY")
    if not key:
        return None
    url = "https://pixabay.com/api/videos/?" + urllib.parse.urlencode({"key": key, "q": q, "per_page": 20, "safesearch": "true"})
    d = json.loads(http_get(url))
    for v in d.get("hits", []):
        if v.get("duration", 0) < max(MIN_DUR, need * 0.6):
            continue
        vs = v.get("videos", {})
        f = vs.get("large") if vs.get("large", {}).get("url") else vs.get("medium")
        if not f or not f.get("url"):
            continue
        dest = CACHE / "pixabay" / f"{v['id']}.mp4"
        download(f["url"], dest)
        return dict(path=str(dest), source="Pixabay", id=str(v["id"]), title=v.get("tags", ""), page=v.get("pageURL", ""),
                    author=v.get("user", ""), license="Pixabay Content License (free commercial use, no attribution required)",
                    license_url="https://pixabay.com/service/license-summary/", start=0.0)
    return None

# ---------------------------------------------------------------- Mixkit
def mixkit_item(item_id_or_slug, allow_restricted):
    """回傳 dict 或 None。逐片檢查下載區塊寫的授權：Free License 才收；Restricted（只限個人用途）預設跳過。"""
    slug = item_id_or_slug
    if re.fullmatch(r"\d+", slug):
        # 只有 id：從快取的搜尋結果找 slug
        idx = load_json(CACHE / "mixkit" / "index.json", {})
        slug = idx.get(slug, {}).get("slug") or slug
    page_url = f"https://mixkit.co/free-stock-video/{slug}/" if not slug.startswith("http") else slug
    h = http_get(page_url, browser=True, delay=2.0)
    m = re.search(r"-(\d+)/?$", page_url.rstrip("/"))
    vid = m.group(1) if m else slug
    i = h.find("download-video-options")
    block = h[i:i + 4000] if i >= 0 else h
    restricted = 'data-license="videoRestricted"' in block
    free = 'data-license="videoFree"' in block
    title = html.unescape(re.search(r"<title>(.*?)</title>", h, re.S).group(1)).split("|")[0].strip() if "<title>" in h else vid
    author = (re.search(r'created by ([^"]+?) that you can use', h) or [None, ""])[1]
    if restricted and not free and not allow_restricted:
        return {"skip": "Mixkit Restricted License（只限個人非商業用途）", "page": page_url}
    lic = ("Mixkit Stock Video Free License (commercial OK, no attribution required)" if free else
           "Mixkit Stock Video Restricted License (PERSONAL, NON-COMMERCIAL USE ONLY)")
    dest = CACHE / "mixkit" / f"{vid}-720.mp4"
    download(f"https://assets.mixkit.co/videos/{vid}/{vid}-720.mp4", dest, browser=True)
    return dict(path=str(dest), source="Mixkit", id=vid, title=title, page=page_url, author=author, license=lic,
                license_url="https://mixkit.co/license/#" + ("videoFree" if free else "videoRestricted"), start=0.0)


def mixkit(q, need, portrait, allow_restricted, log):
    term = urllib.parse.quote(q.strip().lower().replace(" ", "-"))
    h = http_get(f"https://mixkit.co/free-stock-video/discover/{term}/", browser=True, delay=2.0)
    items = re.findall(r'href="/free-stock-video/([a-z0-9-]+-(\d+))/" class="item-grid-video-player__overlay-link"', h)
    idx = load_json(CACHE / "mixkit" / "index.json", {})
    for slug, vid in items:
        idx[vid] = {"slug": slug}
    (CACHE / "mixkit").mkdir(parents=True, exist_ok=True)
    save_json(CACHE / "mixkit" / "index.json", idx)
    for slug, vid in items[:4]:   # 最多看 4 個項目頁，避免頻繁請求
        r = mixkit_item(slug, allow_restricted)
        if r and "skip" in r:
            log.append(f"mixkit {vid}: skipped, {r['skip']}")
            continue
        if r and probe_duration(r["path"]) >= max(MIN_DUR, need * 0.6):
            return r
    return None

# ---------------------------------------------------------------- Wikimedia Commons
COMMONS_OK = re.compile(r"^(public domain|pd|cc0|cc by(?!-sa)[ -]?\d|cc-by-\d|cc by \d)", re.I)

def commons_info(title):
    url = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode({
        "action": "query", "titles": title, "prop": "videoinfo", "viprop": "url|size|derivatives|extmetadata", "format": "json"})
    d = json.loads(http_get(url))
    p = next(iter(d["query"]["pages"].values()))
    return p["videoinfo"][0] if "videoinfo" in p else None


def commons_pick(title, vi, start=None):
    em = vi.get("extmetadata", {})
    lic = em.get("LicenseShortName", {}).get("value", "")
    if not COMMONS_OK.search(lic.strip()):
        return {"skip": f"license {lic} not in whitelist (PD / CC0 / CC BY)"}
    ders = [x for x in vi.get("derivatives", []) if x.get("height", 0) <= 1080]
    ders = sorted(ders, key=lambda x: (abs(x.get("height", 0) - 1080), "mp4" not in x["type"]))
    src = ders[0]["src"] if ders else vi["url"]
    ext = ".webm" if "webm" in (ders[0]["type"] if ders else vi["url"]) else ".mov"
    safe = re.sub(r"[^A-Za-z0-9._-]+", "_", title.replace("File:", ""))[:80]
    dest = CACHE / "commons" / (safe + ext)
    download(src, dest)
    artist = re.sub(r"<[^>]+>", "", em.get("Artist", {}).get("value", "")).strip()
    return dict(path=str(dest), source="Wikimedia Commons", id=title, title=title.replace("File:", ""),
                page="https://commons.wikimedia.org/wiki/" + urllib.parse.quote(title.replace(" ", "_")),
                author=artist, license=lic, license_url=em.get("LicenseUrl", {}).get("value", ""),
                attribution_required=em.get("AttributionRequired", {}).get("value", "") == "true",
                start=float(start) if start is not None else None)


def commons(q, need, portrait, log):
    url = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode({
        "action": "query", "generator": "search", "gsrsearch": f"{q} filetype:video", "gsrnamespace": 6, "gsrlimit": 20,
        "prop": "videoinfo", "viprop": "size|extmetadata", "format": "json"})
    d = json.loads(http_get(url))
    pages = sorted(d.get("query", {}).get("pages", {}).values(), key=lambda p: p.get("index", 99))
    for p in pages:
        vi = (p.get("videoinfo") or [{}])[0]
        dur = vi.get("duration") or 0
        if dur < max(MIN_DUR, need * 0.6) or dur > 900:
            continue
        lic = vi.get("extmetadata", {}).get("LicenseShortName", {}).get("value", "")
        if not COMMONS_OK.search(lic.strip()):
            log.append(f"commons {p['title']}: skipped, license {lic}")
            continue
        r = commons_pick(p["title"], commons_info(p["title"]))
        if r and "skip" not in r:
            return r
    return None

# ---------------------------------------------------------------- Internet Archive (Prelinger)
def ia_pd(meta):
    lic = (meta.get("licenseurl") or "").lower()
    rights = str(meta.get("rights") or "").lower()
    return ("publicdomain" in lic or "/zero/" in lic or "public domain" in rights), (meta.get("licenseurl") or meta.get("rights") or "")


def ia_item(ident, start=None, allow_unverified=False):
    md = json.loads(http_get(f"https://archive.org/metadata/{ident}", timeout=60))
    meta = md.get("metadata", {})
    ok, lic = ia_pd(meta)
    if not ok and not allow_unverified:
        return {"skip": f"no public-domain license field on {ident}"}
    files = [f for f in md.get("files", []) if f["name"].lower().endswith(".mp4") and int(f.get("size") or 0) < 450_000_000]
    if not files:
        return {"skip": "no mp4"}
    def rank(f):
        h = int(f.get("height") or 0)
        return (0 if h >= 400 else 1, -h if h <= 720 else h, int(f.get("size") or 0))
    f = sorted(files, key=rank)[0]
    dest = CACHE / "archive" / f"{ident}__{f['name']}".replace("/", "_")
    if not dest.exists() and (CACHE / "archive" / f["name"]).exists():
        dest = CACHE / "archive" / f["name"]
    download(f"https://archive.org/download/{ident}/{urllib.parse.quote(f['name'])}", dest)
    return dict(path=str(dest), source="Prelinger Archives (Internet Archive)", id=ident,
                title=f"{meta.get('title', ident)} ({meta.get('year') or meta.get('date', '')})".strip(),
                page=f"https://archive.org/details/{ident}", author=str(meta.get("creator") or meta.get("sponsor") or ""),
                license="Public Domain" if ok else f"UNVERIFIED: {lic}", license_url=lic or "https://archive.org/details/prelinger",
                start=float(start) if start is not None else None, archival=True)


def archive(q, need, used_ids, log):
    words = [w for w in re.split(r"[ ,]+", q) if w]
    kq = " OR ".join(words)
    query = f"collection:prelinger AND mediatype:movies AND (title:({kq}) OR subject:({kq}) OR description:({kq}))"
    url = "https://archive.org/advancedsearch.php?" + urllib.parse.urlencode(
        [("q", query), ("fl[]", "identifier"), ("fl[]", "licenseurl"), ("rows", 25), ("sort[]", "downloads desc"), ("output", "json")])
    docs = json.loads(http_get(url, timeout=60))["response"]["docs"]
    # 先試有公有領域標記的
    docs = sorted(docs, key=lambda d: 0 if "publicdomain" in (d.get("licenseurl") or "") else 1)
    for d in docs[:6]:
        r = ia_item(d["identifier"])
        if r and "skip" in r:
            log.append(f"archive {d['identifier']}: skipped, {r['skip']}")
            continue
        return r
    return None

# ---------------------------------------------------------------- 自動挑段落
def frame_scores(path, step=3.0, w=160):
    """每 step 秒取一張小圖，回傳 [(t, score)]。score 偏好有細節、不太暗不太亮、不是字卡的畫面。"""
    import numpy as np
    dur = probe_duration(path)
    h = int(w * 0.75)
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", path, "-vf", f"fps=1/{step},scale={w}:{h},format=gray",
                          "-f", "rawvideo", "-"], capture_output=True).stdout
    n = len(raw) // (w * h)
    a = np.frombuffer(raw[: n * w * h], np.uint8).reshape(n, h, w).astype(float)
    out = []
    for i in range(n):
        f = a[i]
        mean, std = f.mean(), f.std()
        edges = np.abs(np.diff(f, axis=1)).mean()
        bimodal = ((f < 40).mean() + (f > 215).mean())   # 黑底白字的字卡
        motion = np.abs(a[i] - a[i - 1]).mean() if i else 0
        s = edges * (1 if 45 < mean < 200 else 0.3) * (0.4 if bimodal > 0.8 else 1) + std * 0.05 + min(motion, 25) * 0.1
        out.append((i * step, s))
    return out, dur


def auto_start(path, need, used, archival):
    scores, dur = frame_scores(path)
    lo = min(45.0, dur * 0.1) if archival else 0.0     # 老片開頭多半是片頭字卡
    hi = max(lo, dur - need - (20.0 if archival else 0.2))
    best, bt = -1, lo
    for t, s in scores:
        if t < lo or t > hi:
            continue
        if any(abs(t - u) < max(need, 8) for u in used):
            continue
        # 用 need 長度內的平均分，避免剛好切到換場
        win = [x for tt, x in scores if t <= tt <= t + need]
        sc = sum(win) / max(1, len(win))
        if sc > best:
            best, bt = sc, t
    return round(bt, 2)

# ---------------------------------------------------------------- synth（本機產生的抽象 B-roll，零授權風險）
def synth(kind, need, idx):
    import synth_broll
    dest = CACHE / "synth" / f"{kind}_{idx}_{int(need * 10)}.mp4"
    if not dest.exists():
        dest.parent.mkdir(parents=True, exist_ok=True)
        synth_broll.make(kind, need + 1.0, str(dest), seed=idx)
    return dict(path=str(dest), source="Generated locally (synth_broll.py)", id=f"{kind}-{idx}", title=f"synth {kind}",
                page="", author="Josh media team", license="Own work", license_url="", start=0.0)

# ---------------------------------------------------------------- 挑選圖
def sheet(target, work, step=15):
    from PIL import Image, ImageDraw
    if target.startswith("archive:"):
        r = ia_item(target.split(":", 1)[1], allow_unverified=True)
        path = r["path"]
    else:
        path = target
    dur = probe_duration(path)
    ts = [t for t in range(0, int(dur), step)]
    tiles = []
    for t in ts:
        p = subprocess.run(["ffmpeg", "-loglevel", "error", "-ss", str(t), "-i", path, "-frames:v", "1", "-vf", "scale=240:180",
                            "-f", "image2pipe", "-vcodec", "png", "-"], capture_output=True).stdout
        if p:
            import io
            im = Image.open(io.BytesIO(p)).convert("RGB")
            ImageDraw.Draw(im).text((5, 3), f"{t}s", fill=(255, 230, 0))
            tiles.append(im)
    cols = 8
    rows = (len(tiles) + cols - 1) // cols
    S = Image.new("RGB", (cols * 240, rows * 180))
    for i, im in enumerate(tiles):
        S.paste(im, ((i % cols) * 240, (i // cols) * 180))
    out = Path(work) / f"sheet_{Path(path).stem}.jpg"
    S.save(out, quality=85)
    print(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--shots")
    ap.add_argument("--work", required=True)
    ap.add_argument("--timing", help="timing.json from align.py（有的話用實際每鏡長度）")
    ap.add_argument("--only", type=int, action="append")
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--allow-mixkit-restricted", action="store_true",
                    help="收 Mixkit Restricted License（只限個人非商業）。要 Josh 同意才可用")
    ap.add_argument("--sheet")
    a = ap.parse_args()
    work = Path(a.work).resolve(); work.mkdir(parents=True, exist_ok=True)
    if a.sheet:
        return sheet(a.sheet, work)
    spec = load_json(a.shots)
    fmt = spec.get("format", "1080x1920")
    portrait = fmt == "1080x1920"
    timing = load_json(a.timing) if a.timing else None
    fj = work / "footage.json"
    footage = {} if a.refresh else load_json(fj, {})
    log = []
    used = {}
    for k, v in footage.items():
        used.setdefault(v["path"], []).append(v.get("start") or 0)
    for i, shot in enumerate(spec["shots"], 1):
        key = str(i)
        if a.only and i not in a.only:
            continue
        if key in footage and not a.refresh:
            continue
        need = (timing["lines"][i - 1]["dur"] if timing else shot.get("est_dur", 5.0)) + 0.3
        pick = shot.get("pick") or {}
        src = pick.get("source") or shot.get("source", "auto")
        archival = bool(shot.get("archival"))
        kws = shot.get("keywords") or []
        r = None
        try:
            if src == "archive" and pick.get("id"):
                r = ia_item(pick["id"], pick.get("start"))
            elif src == "mixkit" and pick.get("id"):
                r = mixkit_item(pick["id"], a.allow_mixkit_restricted)
            elif src == "commons" and pick.get("title"):
                r = commons_pick(pick["title"], commons_info(pick["title"]), pick.get("start"))
            elif src == "file":
                r = dict(path=pick["path"], source=pick.get("credit_source", "Local file"), id=Path(pick["path"]).name,
                         title=pick.get("title", ""), page=pick.get("page", ""), author=pick.get("author", ""),
                         license=pick.get("license", "UNKNOWN"), license_url=pick.get("license_url", ""), start=pick.get("start"))
            elif src == "synth":
                r = synth(pick.get("kind", shot.get("synth", "code")), need, i)
            else:
                order = ({"auto": ["archive", "commons"] if archival else ["pexels", "pixabay", "mixkit", "commons", "synth"]}
                         .get(src) or [src])
                for s in order:
                    for q in (kws or ["technology"]):
                        if s == "pexels": r = pexels(q, need, portrait)
                        elif s == "pixabay": r = pixabay(q, need, portrait)
                        elif s == "mixkit": r = mixkit(q, need, portrait, a.allow_mixkit_restricted, log)
                        elif s == "commons": r = commons(q, need, portrait, log)
                        elif s == "archive": r = archive(q, need, used, log)
                        elif s == "synth": r = synth(shot.get("synth", "code"), need, i)
                        if r and "skip" not in r:
                            break
                        r = None
                    if r:
                        break
        except Exception as e:  # noqa
            log.append(f"shot {i}: error {e}")
            r = None
        if not r or "skip" in r:
            log.append(f"shot {i}: no footage found ({r.get('skip') if r else 'no result'}); falling back to synth")
            r = synth(shot.get("synth", "code"), need, i)
        if r.get("start") is None:
            r["start"] = auto_start(r["path"], need, used.get(r["path"], []), archival or r.get("archival", False))
        r["archival"] = archival or r.get("archival", False)
        r["need"] = round(need, 2)
        used.setdefault(r["path"], []).append(r["start"])
        # 一鏡太長就在同一支素材裡多挑幾段，維持 AYi 那種 2 到 4 秒一切的節奏
        import math
        n = int(shot.get("cuts") or max(1, math.ceil(need / float(spec.get("max_cut", 4.5)))))
        starts = list(pick.get("starts") or [])
        if not starts:
            starts = [r["start"]]
            clip_len = probe_duration(r["path"])
            for _ in range(n - 1):
                if clip_len < need / n * 2 + 2 or r["source"].startswith("Generated"):
                    break   # 素材太短：build 時同一段放慢或循環
                st = auto_start(r["path"], need / n, used.get(r["path"], []), r["archival"])
                starts.append(st); used.setdefault(r["path"], []).append(st)
        r["starts"] = starts
        footage[key] = r
        print(f"shot {i}: {r['source']} {r['id']} @ {r['start']}s  [{r['license']}]")
        save_json(fj, footage)
    save_json(fj, footage)
    # credits.json：每片來源、網址、授權
    credits = {"clips": [], "log": log}
    for k in sorted(footage, key=int):
        v = footage[k]
        credits["clips"].append({"shot": int(k), **{x: v.get(x) for x in
                                 ["source", "id", "title", "page", "author", "author_url", "license", "license_url", "starts", "need"]}})
    old = load_json(work / "credits.json", {})
    for extra in ("voice", "music"):
        if extra in old:
            credits[extra] = old[extra]
    save_json(work / "credits.json", credits)
    for l in log:
        print("note:", l)


if __name__ == "__main__":
    main()
