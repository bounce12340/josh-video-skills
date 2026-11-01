#!/usr/bin/env python3
"""Turn publish-queue.md into style_tags.csv rows, so tagging published posts is not a manual chore.

publish-queue.md (in <YOUR_WORKSPACE>/media-team/00-profile/) is free-form Markdown, so the parser is tolerant:
  - A line that names a draft (`03-drafts/<slug>` or a `YYYY-MM-DD-some-slug` token) sets the current video;
    lines after it inherit that video until another one is named (so a heading per video works, and so does a table row).
  - Every Instagram, Threads, or X post URL on a line becomes one row for the current video.
  - The first YYYY-MM-DD on the URL's line (else on the video's line) is posted_at.

Post ids:
  - X: the status id in the URL.
  - Instagram / Threads: the media id is not in the URL, so it is looked up by shortcode in meta_insights.py CSVs
    (--insights, repeatable). Without a match the row stays pending with the reason.
Skill and style, first hit wins:
  1. an existing style_tags.csv row for the same video (e.g. already tagged on another platform);
  2. a `skill:` / `style:` (or 技能／風格) line in 03-drafts/<slug>/handoff.md, facts.md, or storyboard.md (--drafts-dir).
Anything still missing stays pending. Nothing is guessed.

Usage:
  python3 queue_to_tags.py --queue <YOUR_WORKSPACE>/media-team/00-profile/publish-queue.md \
      --drafts-dir <YOUR_WORKSPACE>/media-team/03-drafts --insights ig.csv --insights threads.csv
  ... --apply      # append the complete rows to style_tags.csv (never edits or duplicates existing rows)
Pending rows (missing id, skill, or style) are printed and, with --pending-out, written to a CSV for a human to fill.
"""
import argparse, csv, re, sys
from pathlib import Path
from urllib.parse import urlparse

FIELDS = ["post_id", "platform", "video", "skill", "style", "posted_at", "notes"]
POST_URL = re.compile(r"https?://(?:www\.)?(?:instagram\.com/(?:[\w.]+/)?(?:p|reels?|tv)/[\w-]+|"
                      r"threads\.(?:com|net)/@[\w.]+/post/[\w-]+|(?:x|twitter)\.com/[\w]+/status/\d+)[^\s)|>\]]*", re.I)
DRAFT = re.compile(r"03-drafts/([^\s/|)`'\"]+)|\b(\d{4}-\d{2}-\d{2}-[a-z0-9][\w-]*)", re.I)
DATE = re.compile(r"\b(\d{4}-\d{2}-\d{2})\b")
META = re.compile(r"(?im)^[\s>*#|-]*(skill|style|技能|風格)\s*[:：]\s*(.+?)\s*\|?\s*$")
KEYS = {"skill": "skill", "技能": "skill", "style": "style", "風格": "style"}


def platform_and_key(url):
    """(platform, key): key is the X status id, or the IG / Threads shortcode."""
    u = urlparse(url)
    host, parts = u.netloc.lower(), [p for p in u.path.split("/") if p]
    if "instagram.com" in host:
        i = next(i for i, p in enumerate(parts) if p in ("p", "reel", "reels", "tv"))
        return "instagram", parts[i + 1]
    if "threads." in host:
        return "threads", parts[parts.index("post") + 1]
    return "x", parts[parts.index("status") + 1]


def parse_queue(text):
    out, video, video_date = [], None, None
    for line in text.splitlines():
        m = DRAFT.search(line)
        if m:
            video = (m.group(1) or m.group(2)).rstrip(".,;:")
            d = DATE.search(line)
            video_date = d.group(1) if d else None
        for url in POST_URL.findall(line):
            d = DATE.search(DRAFT.sub("", line))  # a date inside the slug is not the posting date
            out.append({"url": url.split("?")[0].rstrip(".,;:"),  # drop share-tracking params such as ?igsh=
"video": video, "posted_at": d.group(1) if d else video_date})
    return out


def load_insights(paths):
    """shortcode -> (platform, media id) from meta_insights.py CSVs."""
    idx = {}
    for p in paths:
        with open(p, newline="", encoding="utf-8-sig") as f:
            for r in csv.DictReader(f):
                if r.get("permalink"):
                    try:
                        plat, key = platform_and_key(r["permalink"])
                    except (StopIteration, ValueError, IndexError):
                        continue
                    idx[key] = (plat, r["Post id"])
    return idx


def draft_meta(drafts_dir, video):
    found = {}
    if not drafts_dir or not video:
        return found
    for name in ("handoff.md", "facts.md", "storyboard.md"):
        p = Path(drafts_dir) / video / name
        if p.is_file():
            for k, v in META.findall(p.read_text(encoding="utf-8")):
                found.setdefault(KEYS[k.lower()], v.strip().strip("`*"))
    return found


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--queue", required=True)
    ap.add_argument("--tags", default=str(Path(__file__).parent / "style_tags.csv"))
    ap.add_argument("--insights", action="append", default=[], help="meta_insights.py CSV (repeatable)")
    ap.add_argument("--drafts-dir", help="03-drafts folder, for skill/style lines in handoff.md etc.")
    ap.add_argument("--apply", action="store_true", help="append complete rows to --tags")
    ap.add_argument("--pending-out", help="write incomplete rows here for a human to fill")
    a = ap.parse_args()

    with open(a.tags, newline="", encoding="utf-8-sig") as f:
        existing = list(csv.DictReader(f))
    have_ids = {(r["platform"], r["post_id"]) for r in existing}
    by_video = {}
    for r in existing:
        if r.get("skill") and r.get("style"):
            by_video.setdefault(r["video"], (r["skill"], r["style"]))
    idx = load_insights(a.insights)

    ready, pending, seen = [], [], set()
    for item in parse_queue(Path(a.queue).read_text(encoding="utf-8")):
        plat, key = platform_and_key(item["url"])
        pid, why = (key, []) if plat == "x" else (idx.get(key, (None, None))[1], [])
        if not pid:
            why.append("no media id: run meta_insights.py and pass its CSV with --insights")
        if (plat, pid) in have_ids or (plat, pid or item["url"]) in seen:
            continue
        seen.add((plat, pid or item["url"]))
        skill, style = by_video.get(item["video"], (None, None))
        if not (skill and style):
            m = draft_meta(a.drafts_dir, item["video"])
            skill, style = skill or m.get("skill"), style or m.get("style")
        if not item["video"]:
            why.append("no draft folder named before this URL")
        if not skill:
            why.append("skill unknown")
        if not style:
            why.append("style unknown")
        row = {"post_id": pid or "", "platform": plat, "video": item["video"] or "", "skill": skill or "",
               "style": style or "", "posted_at": item["posted_at"] or "",
               "notes": "; ".join(why) if why else f"from publish-queue.md {item['url']}"}
        (pending if why else ready).append(row)

    for label, rows in (("ready", ready), ("pending", pending)):
        print(f"{label}: {len(rows)}")
        for r in rows:
            print(f"  {r['platform']:<9} {r['post_id'] or '?':<22} {r['video'] or '?':<34} "
                  f"{r['skill'] or '?'} / {r['style'] or '?'}" + (f"   <- {r['notes']}" if label == "pending" else ""))
    if a.pending_out:
        with open(a.pending_out, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=FIELDS); w.writeheader(); w.writerows(pending)
    if a.apply and ready:
        with open(a.tags, encoding="utf-8") as f:
            needs_nl = (f.read()[-1:] or "\n") != "\n"
        with open(a.tags, "a", newline="", encoding="utf-8") as f:
            if needs_nl:
                f.write("\n")
            csv.DictWriter(f, fieldnames=FIELDS).writerows(ready)
        print(f"appended {len(ready)} row(s) to {a.tags}", file=sys.stderr)
    elif ready:
        print("dry run: add --apply to append the ready rows", file=sys.stderr)


if __name__ == "__main__":
    main()
