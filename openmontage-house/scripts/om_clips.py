#!/usr/bin/env python3
"""用 OpenMontage 的素材來源（Pexels、Archive.org、NASA、NARA、LOC、Wikimedia…）抓素材，
輸出可以直接貼進 stock-footage-reel shots.json 的 pick 區塊，並寫一份 credits 紀錄。

用法（不用先 source，腳本會自己切到 OpenMontage 的 venv）：
  python3 om_clips.py --query "1960s computer room" --out ./om_clips \
      [--sources nasa,archive_org,loc] [--n 3] [--max-dur 60] [--orientation portrait]
"""
import argparse, json, os, subprocess, sys
OM = os.environ.get("OPENMONTAGE_DIR", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "OpenMontage"))
PY = f"{OM}/.venv/bin/python"
DEFAULT_SOURCES = "pexels,archive_org,wikimedia,nasa,nara,loc"

if os.path.realpath(sys.executable) != os.path.realpath(PY) and os.environ.get("_OM_REEXEC") != "1":
    env = dict(os.environ, _OM_REEXEC="1", PATH=f"{OM}/.venv/bin:" + (os.environ.get("NODE_BIN_DIR", "") + ":" if os.environ.get("NODE_BIN_DIR") else "") + os.environ.get("PATH", ""))
    sys.exit(subprocess.call([PY, os.path.abspath(__file__), *sys.argv[1:]], env=env, cwd=OM))

ap = argparse.ArgumentParser()
ap.add_argument("--query", required=True, action="append", help="可重複多次")
ap.add_argument("--out", required=True)
ap.add_argument("--sources", default=DEFAULT_SOURCES)
ap.add_argument("--n", type=int, default=3)
ap.add_argument("--max-dur", type=float, default=90)
ap.add_argument("--orientation", choices=["landscape", "portrait", "square"])
a = ap.parse_args()
sys.path.insert(0, OM)
from tools.video.direct_clip_search import DirectClipSearch  # noqa: E402

filters = {"max_duration": a.max_dur}
if a.orientation:
    filters["orientation"] = a.orientation
out = os.path.abspath(a.out)
r = DirectClipSearch().execute({
    "output_dir": out,
    "queries": [{"query": q, "slot_id": f"q{i+1}"} for i, q in enumerate(a.query)],
    "sources": [s.strip() for s in a.sources.split(",") if s.strip()],
    "clips_per_query": a.n, "filters": filters,
})
if not r.success:
    print("失敗：", r.error); sys.exit(1)
clips = (r.data or {}).get("clips", [])
log = []
for c in clips:
    pick = {"source": "file", "path": c["path"], "license": c.get("license", ""),
            "author": c.get("creator") or "", "page": c.get("source_url", ""),
            "credit_source": f'OpenMontage/{c.get("source")}', "title": c.get("source_tags") or c.get("source_id", "")}
    log.append({**pick, "query": c.get("query"), "duration": c.get("duration"),
                "size": f'{c.get("width")}x{c.get("height")}', "thumbnail": c.get("thumbnail"), "provider": c.get("source")})
    print(f'[{c.get("source")}] {c.get("duration")}s {c.get("width")}x{c.get("height")}  {c.get("source_url")}')
    print("   縮圖：", c.get("thumbnail"))
    print('   pick：', json.dumps(pick, ensure_ascii=False))
json.dump(log, open(os.path.join(out, "om_credits.json"), "w"), ensure_ascii=False, indent=1)
for e in (r.data or {}).get("errors", []):
    print("note:", e)
print(f"共 {len(clips)} 支，授權紀錄：{out}/om_credits.json（每支都要再確認授權可商用，才放進 credits.json）")
