#!/usr/bin/env python3
"""Pull Josh's own Instagram and Threads post insights into a CSV for style_compare.py.

Read-only: only GET calls to the official Graph APIs for the token owner's own posts.
It never posts, comments, or reads anyone else's account.

  Instagram  GET {IG_GRAPH_BASE}/{IG_USER_ID}/media, then GET /{media-id}/insights
             env: IG_ACCESS_TOKEN, IG_USER_ID, optional IG_GRAPH_BASE
             (default https://graph.facebook.com/v26.0; Instagram-Login tokens use https://graph.instagram.com/v26.0)
             scopes: instagram_basic + instagram_manage_insights (Facebook Login) or
                     instagram_business_basic + instagram_business_manage_insights (Instagram Login)
  Threads    GET {THREADS_GRAPH_BASE}/me/threads, then GET /{media-id}/insights
             env: THREADS_ACCESS_TOKEN, optional THREADS_GRAPH_BASE (default https://graph.threads.com/v1.0)
             scopes: threads_basic + threads_manage_insights

One insights request per post, so keep --limit small. Output columns:
  Post id, platform, permalink, posted_at, media_type, snapshot_at, age_hours, <metric columns as Meta names them>
Metrics are copied as returned; nothing is derived. Metric names checked against the official docs on 2026-11-01
(see references/meta-platforms.md); Meta renames metrics, so pass --metrics when the API rejects one.

Usage:
  python3 meta_insights.py --platform instagram --since 2026-10-01 --out ig.csv
  python3 meta_insights.py --platform threads --limit 30 --out threads.csv
  python3 meta_insights.py --platform threads --input examples/threads_raw_sample.json --as-of 2026-11-01T00:00:00Z --out t.csv
  python3 style_compare.py --csv ig.csv --platform instagram --by style
"""
import argparse, csv, json, os, sys, urllib.error, urllib.parse, urllib.request
from datetime import datetime, timezone

IG_REELS = "views,reach,likes,comments,shares,saved,total_interactions,ig_reels_avg_watch_time,ig_reels_video_view_total_time"
IG_FEED = "views,reach,likes,comments,shares,saved,total_interactions"
THREADS = "views,likes,replies,reposts,quotes,shares"
AUTH_CODES = {190, 102, 10, 200}  # token expired / invalid / permission missing: stop instead of looping


def env(name):
    v = os.environ.get(name)
    if not v:
        sys.exit(f"{name} is not set (environment variable only; never put tokens in a file).")
    return v


def get(url, params, token):
    req = urllib.request.Request(f"{url}?{urllib.parse.urlencode(params)}" if params else url,
                                 headers={"Authorization": f"Bearer {token}"}, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r), None
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")[:800]
        try:
            code = json.loads(body).get("error", {}).get("code")
        except ValueError:
            code = None
        if e.code != 400 or code in AUTH_CODES:
            sys.exit(f"API error HTTP {e.code} (code {code}):\n{body}")
        return None, body


def ts(s):
    """Meta timestamps look like 2026-10-30T01:00:00+0000."""
    return datetime.strptime(s.replace("Z", "+0000"), "%Y-%m-%dT%H:%M:%S%z")


def parse_insights(resp):
    out = {}
    for m in (resp or {}).get("data", []):
        if m.get("values"):
            out[m["name"]] = m["values"][0].get("value")
        elif isinstance(m.get("total_value"), dict):
            out[m["name"]] = m["total_value"].get("value")
    return out


def list_media(first_url, params, token, since, limit):
    url, items = first_url, []
    while url and len(items) < limit:
        page, err = get(url, params, token)
        if err:
            sys.exit(f"could not list posts:\n{err}")
        for it in page.get("data", []):
            if since and ts(it["timestamp"]) < since:
                return items
            items.append(it)
            if len(items) >= limit:
                break
        url, params = page.get("paging", {}).get("next"), None  # next already carries the query string
    return items


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--platform", choices=["instagram", "threads"], required=True)
    ap.add_argument("--since", help="only posts on/after this date (YYYY-MM-DD, UTC)")
    ap.add_argument("--limit", type=int, default=50, help="max posts (one insights request each)")
    ap.add_argument("--product", help="Instagram only: keep one media_product_type, e.g. REELS")
    ap.add_argument("--metrics", help="override the metric list (comma-separated, Meta's names)")
    ap.add_argument("--input", help="offline: JSON {'media': [...], 'insights': {id: <insights response>}}")
    ap.add_argument("--as-of", help="snapshot time for age_hours (ISO, default now); useful with --input")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    now = datetime.fromisoformat(a.as_of.replace("Z", "+00:00")) if a.as_of else datetime.now(timezone.utc)
    since = datetime.fromisoformat(a.since).replace(tzinfo=timezone.utc) if a.since else None
    ig = a.platform == "instagram"

    if a.input:
        raw = json.load(open(a.input, encoding="utf-8"))
        media = [m for m in raw["media"] if not since or ts(m["timestamp"]) >= since][:a.limit]
        fetch = lambda mid, metrics: (raw.get("insights", {}).get(mid), None)
    elif ig:
        token, uid = env("IG_ACCESS_TOKEN"), env("IG_USER_ID")
        base = os.environ.get("IG_GRAPH_BASE", "https://graph.facebook.com/v26.0").rstrip("/")
        media = list_media(f"{base}/{uid}/media", {"fields": "id,caption,media_type,media_product_type,permalink,timestamp",
                                                     "limit": 50}, token, since, a.limit)
        fetch = lambda mid, metrics: get(f"{base}/{mid}/insights", {"metric": metrics}, token)
    else:
        token = env("THREADS_ACCESS_TOKEN")
        base = os.environ.get("THREADS_GRAPH_BASE", "https://graph.threads.com/v1.0").rstrip("/")
        params = {"fields": "id,media_type,permalink,timestamp,text,is_quote_post", "limit": 50}
        if since:
            params["since"] = int(since.timestamp())
        media = list_media(f"{base}/me/threads", params, token, since, a.limit)
        fetch = lambda mid, metrics: get(f"{base}/{mid}/insights", {"metric": metrics}, token)

    if ig and a.product:
        media = [m for m in media if m.get("media_product_type") == a.product]
    rows, cols, failed = [], [], []
    for m in media:
        if a.metrics:
            metrics = a.metrics
        elif ig:
            metrics = IG_REELS if m.get("media_product_type") == "REELS" else IG_FEED
        else:
            metrics = THREADS
        resp, err = fetch(m["id"], metrics)
        if err:
            failed.append((m["id"], err.replace("\n", " ")[:160]))
        vals = parse_insights(resp)
        cols += [k for k in vals if k not in cols]
        posted = ts(m["timestamp"])
        rows.append({"Post id": m["id"], "platform": a.platform, "permalink": m.get("permalink", ""),
                     "posted_at": posted.strftime("%Y-%m-%dT%H:%M:%SZ"),
                     "media_type": m.get("media_product_type") or m.get("media_type", ""),
                     "snapshot_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
                     "age_hours": round((now - posted).total_seconds() / 3600, 1), **vals})

    header = ["Post id", "platform", "permalink", "posted_at", "media_type", "snapshot_at", "age_hours"] + cols
    with open(a.out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=header)
        w.writeheader()
        w.writerows(rows)
    print(f"{len(rows)} posts -> {a.out} (metrics: {', '.join(cols) or 'none'})", file=sys.stderr)
    for mid, err in failed:
        print(f"warning: insights failed for {mid}: {err}. Check the metric names with --metrics.", file=sys.stderr)


if __name__ == "__main__":
    main()
