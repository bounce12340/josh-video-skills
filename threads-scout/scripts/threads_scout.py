#!/usr/bin/env python3
"""threads-scout: read-only Threads topic watcher.

Searches public Threads posts with the official Threads API keyword search
(GET https://graph.threads.com/v1.0/keyword_search), classifies each hit with the
same rules as x-scout, and suggests a skill plus style with a one-line reason.
Read-only: it never posts, replies, likes, reposts, or follows. The only network
calls are GETs to /keyword_search and one GET to /me (to detect the
"own posts only" fallback described below).

Usage:
  THREADS_ACCESS_TOKEN=... python3 threads_scout.py --config ../examples/topics.json [--limit 25] [--out hits.json]
  python3 threads_scout.py --config ../examples/topics.json --input ../examples/sample_search.json   # offline

Notes from the official docs (checked 2026-11-01, see references/meta-platforms.md):
  - Needs threads_basic + threads_keyword_search. Without an approved
    threads_keyword_search permission, Meta does not refuse the call: it only
    searches the token owner's own posts. This script warns when every hit is yours.
  - 2,200 queries per user per rolling 24 h, shared across all apps; repeated
    queries count again; queries with no results do not count.
  - Keyword search returns no engagement metrics for other people's posts.
"""
import argparse, importlib.util, json, os, re, sys, time, urllib.error, urllib.parse, urllib.request
from pathlib import Path

BASE = os.environ.get("THREADS_GRAPH_BASE", "https://graph.threads.com/v1.0").rstrip("/")
FIELDS = "id,text,media_type,permalink,timestamp,username,has_replies,is_quote_post,is_reply"
# X search operators that mean nothing to Threads keyword search; a query carrying them was copied from x-scout.
X_ONLY = re.compile(r"(^|[\s(])-?(is|lang|from|to|has|url|conversation_id|min_faves|min_retweets|since|until):")


def load_classifier():
    """Reuse x-scout's classify() and SUGGEST table so both scouts map topics the same way."""
    here = Path(__file__).resolve()
    candidates = [Path(os.environ["SKILLS_DIR"]) / "x-scout/scripts/x_scout.py"] if os.environ.get("SKILLS_DIR") else []
    candidates.append(here.parents[2] / "x-scout/scripts/x_scout.py")
    for p in candidates:
        if p.is_file():
            spec = importlib.util.spec_from_file_location("x_scout", p)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            return mod.classify, mod.SUGGEST
    sys.exit("x-scout not found next to threads-scout (needed for the shared topic table). "
             "Install both folders at the same level, or set SKILLS_DIR.")


def norm_query(q):
    q = {"q": q} if isinstance(q, str) else dict(q)
    if not q.get("q"):
        sys.exit(f"query without 'q': {q!r}")
    if X_ONLY.search(q["q"]):
        sys.exit(f"X-only search operator in Threads query {q['q']!r}. Threads keyword search takes plain "
                 "keywords (or a topic tag with search_mode TAG); remove operators like -is:retweet or lang:.")
    return q


def get(path, params, token):
    url = f"{BASE}/{path}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"}, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")[:1000]
        sys.exit(f"Threads API error HTTP {e.code} on /{path}:\n{body}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True, help="JSON with 'queries' (strings or {q, search_mode, media_type}) and 'classify'")
    ap.add_argument("--limit", type=int, default=25, help="results per query (1-100, default 25)")
    ap.add_argument("--search-type", choices=["TOP", "RECENT"], default="TOP", help="TOP = popular first (default)")
    ap.add_argument("--since-hours", type=float, help="only posts from the last N hours")
    ap.add_argument("--include-replies", action="store_true", help="keep replies (dropped by default)")
    ap.add_argument("--input", help="offline: a saved keyword_search response (or a list of them) instead of the API")
    ap.add_argument("--out")
    a = ap.parse_args()

    classify, suggest = load_classifier()
    cfg = json.load(open(a.config, encoding="utf-8"))
    rules = cfg.get("classify", {})
    me = None
    if a.input:
        raw = json.load(open(a.input, encoding="utf-8"))
        pages = raw if isinstance(raw, list) else [raw]
    else:
        token = os.environ.get("THREADS_ACCESS_TOKEN")
        if not token:
            sys.exit("THREADS_ACCESS_TOKEN is not set (environment variable only; never put it in a file).")
        queries = [norm_query(q) for q in cfg["queries"]]
        me = get("me", {"fields": "username"}, token).get("username")
        pages = []
        for q in queries:
            params = {"q": q["q"], "search_type": a.search_type, "fields": FIELDS,
                      "limit": max(1, min(100, a.limit))}
            for k in ("search_mode", "media_type"):
                if q.get(k):
                    params[k] = q[k]
            if a.since_hours:
                params["since"] = int(time.time() - a.since_hours * 3600)
            pages.append(get("keyword_search", params, token))
        print(f"{len(queries)} keyword_search queries used (quota: 2,200 per rolling 24 h, shared across apps)",
              file=sys.stderr)

    hits, seen = [], set()
    for page in pages:
        for p in page.get("data", []):
            if p["id"] in seen or (p.get("is_reply") and not a.include_replies):
                continue
            seen.add(p["id"])
            typ = classify(p.get("text", ""), rules)
            skill, style, reason = suggest[typ]
            hits.append({"id": p["id"], "author": p.get("username"), "url": p.get("permalink"),
                         "created_at": p.get("timestamp"), "media_type": p.get("media_type"),
                         "text": p.get("text", ""), "topic_type": typ, "suggested_skill": skill,
                         "suggested_style": style, "reason": reason})
    for h in hits:
        print(f"[{h['topic_type']}] {h['suggested_skill']} | {h['suggested_style']} | {h['reason']}\n"
              f"    {h['url']}  @{h['author']}  {h['text'][:100]!r}")
    if me and hits and all(h["author"] == me for h in hits):
        print(f"warning: every hit is by @{me}. threads_keyword_search is probably not approved for this app, "
              "so Meta searched only your own posts.", file=sys.stderr)
    if a.out:
        json.dump(hits, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"{len(hits)} hits", file=sys.stderr)


if __name__ == "__main__":
    main()
