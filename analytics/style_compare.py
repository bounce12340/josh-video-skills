#!/usr/bin/env python3
"""Compare post performance by skill and style.

Inputs
  --csv     X analytics CSV export (one row per post). Repeatable.
  --api     optional JSON of own posts from the X API (list of tweets, or {"data": [...]}) with public_metrics.
  --tags    tag file mapping post -> skill/style (default: analytics/style_tags.csv).
Output
  Per-style (or per-skill) count and median of each metric column, printed as a table; optional --out CSV.

Column names differ between exports, so they are configurable:
  --id-col     post id column in the CSV (default "Post id"; also tries "Tweet id", "id")
  --metrics    comma-separated metric columns to summarize (default: every numeric column except the id)
Nothing is computed that is not in the input: no derived or invented metrics.
"""
import argparse, csv, json, statistics, sys
from collections import defaultdict
from pathlib import Path

ID_FALLBACKS = ["Post id", "Tweet id", "id", "post_id"]


def num(v):
    try:
        return float(str(v).replace(",", "").strip())
    except (ValueError, TypeError):
        return None


def load_csv(path, id_col):
    with open(path, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        return {}, []
    cols = list(rows[0].keys())
    idc = id_col if id_col in cols else next((c for c in ID_FALLBACKS if c in cols), None)
    if not idc:
        sys.exit(f"{path}: no id column found; columns are {cols}. Pass --id-col.")
    return {str(r[idc]).strip(): r for r in rows}, [c for c in cols if c != idc]


def load_api(path):
    d = json.load(open(path))
    out = {}
    for tw in (d.get("data", []) if isinstance(d, dict) else d):
        out[str(tw["id"])] = {k: v for k, v in tw.get("public_metrics", {}).items()}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", action="append", default=[])
    ap.add_argument("--api")
    ap.add_argument("--tags", default=str(Path(__file__).parent / "style_tags.csv"))
    ap.add_argument("--id-col", default="Post id")
    ap.add_argument("--metrics", help="comma-separated metric columns (default: all numeric)")
    ap.add_argument("--by", choices=["style", "skill", "skill_style"], default="style")
    ap.add_argument("--out")
    a = ap.parse_args()
    if not a.csv and not a.api:
        sys.exit("give at least one --csv or --api")

    posts, cols = {}, []
    for p in a.csv:
        rows, c = load_csv(p, a.id_col)
        posts.update(rows); cols += [x for x in c if x not in cols]
    if a.api:
        for pid, m in load_api(a.api).items():
            posts.setdefault(pid, {}).update({k: v for k, v in m.items() if k not in posts.get(pid, {})})
            cols += [k for k in m if k not in cols]

    metrics = [m.strip() for m in a.metrics.split(",")] if a.metrics else \
        [c for c in cols if any(num(r.get(c)) is not None for r in posts.values())]
    if not metrics:
        sys.exit("no numeric metric columns found")

    with open(a.tags, newline="", encoding="utf-8-sig") as f:
        tags = list(csv.DictReader(f))
    groups, missing = defaultdict(list), []
    for t in tags:
        pid = str(t["post_id"]).strip()
        if pid not in posts:
            missing.append(pid); continue
        key = {"style": t["style"], "skill": t["skill"], "skill_style": f"{t['skill']} / {t['style']}"}[a.by]
        groups[key].append(posts[pid])

    header = [a.by, "posts"] + [f"median {m}" for m in metrics]
    table = []
    for k, rows in sorted(groups.items()):
        line = [k, len(rows)]
        for m in metrics:
            vals = [x for x in (num(r.get(m)) for r in rows) if x is not None]
            line.append(round(statistics.median(vals), 2) if vals else "")
        table.append(line)
    w = [max(len(str(x)) for x in col) for col in zip(header, *table)]
    for r in [header] + table:
        print("  ".join(str(x).ljust(n) for x, n in zip(r, w)))
    if missing:
        print(f"note: {len(missing)} tagged post(s) not found in the inputs: {', '.join(missing[:10])}", file=sys.stderr)
    if a.out:
        with open(a.out, "w", newline="") as f:
            csv.writer(f).writerows([header] + table)


if __name__ == "__main__":
    main()
