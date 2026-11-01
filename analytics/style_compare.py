#!/usr/bin/env python3
"""Compare post performance by skill and style (X, Instagram, Threads).

Inputs
  --csv     metrics CSV, one row per post (X analytics export, or meta_insights.py output). Repeatable.
  --api     optional JSON of own posts from the X API (list of tweets, or {"data": [...]}) with public_metrics.
  --tags    tag file mapping post -> platform/skill/style (default: analytics/style_tags.csv).
Output
  Per-style (or per-skill) count and median of each metric column, printed as a table; optional --out CSV.

Column names differ between exports, so they are configurable:
  --id-col     post id column in the CSV (default "Post id"; also tries "Tweet id", "id")
  --metrics    comma-separated metric columns to summarize (default: every numeric column except bookkeeping ones)

Comparability (posts are only comparable on the same platform and at a similar age):
  --platform        keep only tags with this platform (x, instagram, threads). Strongly recommended when the
                    tag file mixes platforms, because metric names mean different things per platform.
  --min-age-hours   drop posts younger than N hours (needs an age_hours column, as meta_insights.py writes).
                    The median post age per group is always shown when age_hours exists.

Derived numbers are opt-in and labeled; nothing is derived unless asked for:
  --rate NAME=NUM/DEN   per-post ratio of two existing columns, then its median (e.g. share_rate=shares/reach).
  --outliers METRIC     list each post's METRIC as a multiple of the median of all selected posts
                        ("how far did this beat my own typical post"), highest first.
"""
import argparse, csv, json, statistics, sys
from collections import defaultdict
from pathlib import Path

ID_FALLBACKS = ["Post id", "Tweet id", "id", "post_id"]
NOT_METRICS = {"age_hours"}  # numeric bookkeeping columns from meta_insights.py; shown separately


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


def parse_rate(spec):
    try:
        name, expr = spec.split("=", 1)
        n, d = expr.split("/", 1)
        return name.strip(), n.strip(), d.strip()
    except ValueError:
        sys.exit(f"--rate {spec!r}: expected NAME=NUMERATOR/DENOMINATOR, e.g. share_rate=shares/reach")


def median_of(rows, key):
    vals = [x for x in (num(r.get(key)) for r in rows) if x is not None]
    return round(statistics.median(vals), 4 if key.startswith("rate:") else 2) if vals else ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", action="append", default=[])
    ap.add_argument("--api")
    ap.add_argument("--tags", default=str(Path(__file__).parent / "style_tags.csv"))
    ap.add_argument("--id-col", default="Post id")
    ap.add_argument("--metrics", help="comma-separated metric columns (default: all numeric)")
    ap.add_argument("--by", choices=["style", "skill", "skill_style"], default="style")
    ap.add_argument("--platform", help="only tags with this platform value (x, instagram, threads)")
    ap.add_argument("--min-age-hours", type=float, help="drop posts younger than this (needs age_hours)")
    ap.add_argument("--rate", action="append", default=[], help="NAME=NUM/DEN, repeatable")
    ap.add_argument("--outliers", metavar="METRIC", help="list posts by multiple of the overall median of METRIC")
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
        [c for c in cols if c not in NOT_METRICS and any(num(r.get(c)) is not None for r in posts.values())]
    rates = [parse_rate(s) for s in a.rate]
    for _, n, d in rates:
        for c in (n, d):
            if c not in cols:
                sys.exit(f"--rate column {c!r} is not in the inputs; columns are {cols}")
    if not metrics and not rates:
        sys.exit("no numeric metric columns found")
    has_age = "age_hours" in cols
    if a.min_age_hours is not None and not has_age:
        sys.exit("--min-age-hours needs an age_hours column (meta_insights.py writes one)")

    with open(a.tags, newline="", encoding="utf-8-sig") as f:
        tags = list(csv.DictReader(f))
    if a.platform:
        tags = [t for t in tags if t.get("platform", "").strip().lower() == a.platform.lower()]
    elif len({t.get("platform", "").strip().lower() for t in tags}) > 1:
        print("note: the tag file mixes platforms; pass --platform so metrics are compared like for like",
              file=sys.stderr)

    groups, selected, missing, young = defaultdict(list), [], [], []
    for t in tags:
        pid = str(t["post_id"]).strip()
        if pid not in posts:
            missing.append(pid); continue
        row = dict(posts[pid])
        if a.min_age_hours is not None and (num(row.get("age_hours")) or 0) < a.min_age_hours:
            young.append(pid); continue
        for name, n, d in rates:
            nv, dv = num(row.get(n)), num(row.get(d))
            row[f"rate:{name}"] = nv / dv if nv is not None and dv else None
        key = {"style": t["style"], "skill": t["skill"], "skill_style": f"{t['skill']} / {t['style']}"}[a.by]
        groups[key].append(row)
        selected.append((pid, key, row))

    extra = (["median age_hours"] if has_age else []) + [f"median {n}={x}/{y}" for n, x, y in rates]
    header = [a.by, "posts"] + extra + [f"median {m}" for m in metrics]
    table = []
    for k, rows in sorted(groups.items()):
        line = [k, len(rows)]
        if has_age:
            line.append(median_of(rows, "age_hours"))
        line += [median_of(rows, f"rate:{n}") for n, _, _ in rates]
        line += [median_of(rows, m) for m in metrics]
        table.append(line)
    w = [max(len(str(x)) for x in col) for col in zip(header, *table)]
    for r in [header] + table:
        print("  ".join(str(x).ljust(n) for x, n in zip(r, w)))

    if a.outliers:
        vals = [(pid, key, num(row.get(a.outliers))) for pid, key, row in selected]
        vals = [v for v in vals if v[2] is not None]
        base = statistics.median([v for _, _, v in vals]) if vals else 0
        print(f"\noutliers: {a.outliers} as a multiple of the median of {len(vals)} selected posts ({base:g})")
        for pid, key, v in sorted(vals, key=lambda x: -x[2]):
            print(f"  {v / base if base else 0:6.2f}x  {pid:<14} {key:<30} {v:g}")

    if missing:
        print(f"note: {len(missing)} tagged post(s) not found in the inputs: {', '.join(missing[:10])}", file=sys.stderr)
    if young:
        print(f"note: {len(young)} post(s) younger than {a.min_age_hours:g} h left out: {', '.join(young[:10])}",
              file=sys.stderr)
    if a.out:
        with open(a.out, "w", newline="") as f:
            csv.writer(f).writerows([header] + table)


if __name__ == "__main__":
    main()
