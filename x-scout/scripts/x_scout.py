#!/usr/bin/env python3
"""x-scout: read-only X topic watcher.

Searches recent posts for topic keywords (X API v2 GET /2/tweets/search/recent), classifies each hit into
the router's topic types, and suggests a skill plus style with a one-line reason. Read-only: it never posts,
likes, follows, or replies. The only network call is the search GET.

Usage:
  X_BEARER_TOKEN=... python3 x_scout.py --config ../examples/topics.json [--max 20] [--out hits.json]
  python3 x_scout.py --config ../examples/topics.json --input saved_search.json   # offline, no API call
"""
import argparse, json, os, re, sys, urllib.error, urllib.parse, urllib.request

API = "https://api.x.com/2/tweets/search/recent"

# Router topic types -> (skill, style, reason). Mirrors josh-video-router's decision table and INDEX.md style picks.
SUGGEST = {
    "interview": ("interview-reel", "Kinetic typography for quotes",
                  "A person speaking on record; commentary intercut with official original audio fits best."),
    "tool_demo": ("screen-record -> stock-footage-reel", "Claude Code / tool explainer",
                  "A tool on a public page can be shown with real screen footage."),
    "numbers_news": ("stock-footage-reel (+ data card if available)", "Data animation",
                     "The story is driven by figures; animate the key numbers."),
    "one_person_company": ("stock-footage-reel or huashu-art-motion", "Business motion explainer",
                           "An operations / workflow story reads best as a process explainer."),
    "pharma_regulatory": ("stock-footage-reel", "Dark typography",
                          "Serious regulatory news; a sober news style with sources on screen."),
    "ai_news": ("stock-footage-reel", "Dark typography",
                "Straight news; voiceover over real footage, no opinion."),
}
ORDER = ["interview", "tool_demo", "pharma_regulatory", "numbers_news", "one_person_company", "ai_news"]


def classify(text, rules):
    t = text.lower()
    for typ in ORDER:
        if any(k.lower() in t for k in rules.get(typ, [])):
            return typ
    return "ai_news"


# Operators from the old v1.1 / web search that X API v2 recent search rejects with HTTP 400.
UNSUPPORTED = ["min_faves", "min_retweets", "min_replies", "since", "until", "filter", "near", "within"]


def check_query(query):
    bad = [op for op in UNSUPPORTED if re.search(rf"(^|[\s(])-?{op}:", query)]
    if bad:
        sys.exit(f"Unsupported operator(s) {', '.join(o + ':' for o in bad)} in query: {query!r}\n"
                 "X API v2 recent search does not support these. Remove them; use --sort relevancy "
                 "and filter by metrics after the search instead.")


def search(query, max_results, token, sort="relevancy"):
    q = urllib.parse.urlencode({"query": query, "max_results": max(10, min(100, max_results)),
                                "sort_order": sort,
                                "tweet.fields": "created_at,public_metrics,author_id,lang",
                                "expansions": "author_id", "user.fields": "username"})
    req = urllib.request.Request(f"{API}?{q}", headers={"Authorization": f"Bearer {token}"}, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")[:1000]
        sys.exit(f"X API error HTTP {e.code} for query {query!r}:\n{body}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True, help="JSON with 'queries' and 'classify' keyword rules")
    ap.add_argument("--max", type=int, default=20)
    ap.add_argument("--input", help="offline: a saved search response JSON instead of calling the API")
    ap.add_argument("--sort", choices=["relevancy", "recency"], default="relevancy",
                    help="X sort_order (default relevancy = popular first; recency = newest first)")
    ap.add_argument("--out")
    a = ap.parse_args()
    cfg = json.load(open(a.config))
    rules = cfg.get("classify", {})
    if a.input:
        pages = [json.load(open(a.input))]
    else:
        token = os.environ.get("X_BEARER_TOKEN")
        if not token:
            sys.exit("X_BEARER_TOKEN is not set (environment variable only; never put it in a file).")
        for q in cfg["queries"]:
            check_query(q)
        pages = [search(q, a.max, token, a.sort) for q in cfg["queries"]]
    hits, seen = [], set()
    for page in pages:
        users = {u["id"]: u.get("username") for u in page.get("includes", {}).get("users", [])}
        for tw in page.get("data", []):
            if tw["id"] in seen:
                continue
            seen.add(tw["id"])
            typ = classify(tw.get("text", ""), rules)
            skill, style, reason = SUGGEST[typ]
            hits.append({"id": tw["id"], "author": users.get(tw.get("author_id")),
                         "url": (f"https://x.com/{users[tw.get('author_id')]}/status/{tw['id']}"
                                 if users.get(tw.get("author_id")) else f"https://x.com/i/web/status/{tw['id']}"),
                         "created_at": tw.get("created_at"), "metrics": tw.get("public_metrics", {}),
                         "text": tw.get("text", ""), "topic_type": typ,
                         "suggested_skill": skill, "suggested_style": style, "reason": reason})
    for h in hits:
        print(f"[{h['topic_type']}] {h['suggested_skill']} | {h['suggested_style']} | {h['reason']}\n    {h['url']}  {h['text'][:100]!r}")
    if a.out:
        json.dump(hits, open(a.out, "w"), ensure_ascii=False, indent=2)
    print(f"{len(hits)} hits", file=sys.stderr)


if __name__ == "__main__":
    main()
