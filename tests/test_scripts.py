"""Offline regression tests for the repo's stdlib-only scripts.

Run: python3 -m unittest discover -s tests -v
Every test uses the fictional fixtures under */examples/; nothing calls a network API and no token is needed.
"""
import csv, json, os, shutil, subprocess, sys, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable
CLEAN_ENV = {k: v for k, v in os.environ.items()
             if k not in ("X_BEARER_TOKEN", "THREADS_ACCESS_TOKEN", "IG_ACCESS_TOKEN", "IG_USER_ID", "SKILLS_DIR")}


def run(*args, ok=True):
    p = subprocess.run([PY, *map(str, args)], cwd=ROOT, env=CLEAN_ENV, capture_output=True, text=True, timeout=60)
    if ok and p.returncode != 0:
        raise AssertionError(f"{args} exited {p.returncode}\nstdout:\n{p.stdout}\nstderr:\n{p.stderr}")
    return p


def read_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def insights(self, platform):
        out = self.tmp / f"{platform}.csv"
        run("analytics/meta_insights.py", "--platform", platform, "--input",
            f"analytics/examples/{'ig' if platform == 'instagram' else 'threads'}_raw_sample.json",
            "--as-of", "2026-11-01T00:00:00Z", "--out", out)
        return out


class XScout(Base):
    def test_offline_classification(self):
        out = self.tmp / "hits.json"
        run("x-scout/scripts/x_scout.py", "--config", "x-scout/examples/topics.json",
            "--input", "x-scout/examples/sample_search.json", "--out", out)
        types = {h["id"]: h["topic_type"] for h in json.loads(out.read_text(encoding="utf-8"))}
        self.assertEqual(types, {"1": "interview", "2": "pharma_regulatory", "3": "tool_demo",
                                 "4": "numbers_news", "5": "one_person_company", "6": "ai_news"})

    def test_rejects_unsupported_operator(self):
        cfg = self.tmp / "bad.json"
        cfg.write_text(json.dumps({"queries": ["AI min_faves:100"]}))
        env = dict(CLEAN_ENV, X_BEARER_TOKEN="dummy")
        p = subprocess.run([PY, "x-scout/scripts/x_scout.py", "--config", str(cfg)], cwd=ROOT, env=env,
                           capture_output=True, text=True, timeout=60)
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("min_faves", p.stderr)


class ThreadsScout(Base):
    def test_offline_classification_drops_replies(self):
        out = self.tmp / "hits.json"
        run("threads-scout/scripts/threads_scout.py", "--config", "threads-scout/examples/topics.json",
            "--input", "threads-scout/examples/sample_search.json", "--out", out)
        types = {h["id"]: h["topic_type"] for h in json.loads(out.read_text(encoding="utf-8"))}
        self.assertEqual(types, {"t1": "interview", "t2": "pharma_regulatory", "t3": "tool_demo",
                                 "t4": "numbers_news", "t5": "one_person_company"})

    def test_rejects_x_operator_before_any_call(self):
        cfg = self.tmp / "bad.json"
        cfg.write_text(json.dumps({"queries": ["AI -is:retweet"]}))
        env = dict(CLEAN_ENV, THREADS_ACCESS_TOKEN="dummy")
        p = subprocess.run([PY, "threads-scout/scripts/threads_scout.py", "--config", str(cfg)], cwd=ROOT, env=env,
                           capture_output=True, text=True, timeout=60)
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("X-only search operator", p.stderr)

    def test_needs_token_without_input(self):
        p = run("threads-scout/scripts/threads_scout.py", "--config", "threads-scout/examples/topics.json", ok=False)
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("THREADS_ACCESS_TOKEN", p.stderr)


class MetaInsights(Base):
    def test_threads_rows_and_age(self):
        rows = {r["Post id"]: r for r in read_csv(self.insights("threads"))}
        self.assertEqual(set(rows), {"th1", "th2", "th3", "th4"})
        self.assertEqual(rows["th3"]["views"], "9100")
        self.assertEqual(rows["th4"]["age_hours"], "12.7")

    def test_instagram_values_and_total_value_shapes(self):
        rows = {r["Post id"]: r for r in read_csv(self.insights("instagram"))}
        self.assertEqual(rows["ig1"]["media_type"], "REELS")
        self.assertEqual(rows["ig1"]["shares"], "160")       # "values" shape
        self.assertEqual(rows["ig3"]["views"], "2500")       # "total_value" shape


class StyleCompare(Base):
    def test_x_regression(self):
        p = run("analytics/style_compare.py", "--csv", "analytics/examples/x_export_sample.csv",
                "--tags", "analytics/examples/style_tags_sample.csv", "--platform", "x",
                "--out", self.tmp / "o.csv")
        rows = {r["style"]: r for r in read_csv(self.tmp / "o.csv")}
        self.assertEqual(rows["Dark typography"]["posts"], "2")
        self.assertEqual(rows["Dark typography"]["median Impressions"], "1000.0")
        self.assertIn("999", p.stderr)  # tagged but missing from the export

    def test_threads_age_rate_outliers(self):
        p = run("analytics/style_compare.py", "--csv", self.insights("threads"),
                "--tags", "analytics/examples/style_tags_sample.csv", "--platform", "threads",
                "--min-age-hours", "72", "--rate", "share_rate=shares/views", "--outliers", "views")
        self.assertIn("1.75x", p.stdout)          # th3: 9100 / median 5200
        self.assertIn("th4", p.stderr)            # younger than 72 h, left out
        self.assertIn("median share_rate=shares/views", p.stdout)

    def test_mixed_platform_warning(self):
        p = run("analytics/style_compare.py", "--csv", "analytics/examples/x_export_sample.csv",
                "--tags", "analytics/examples/style_tags_sample.csv")
        self.assertIn("mixes platforms", p.stderr)


class QueueToTags(Base):
    def test_ready_pending_apply_and_idempotent(self):
        tags = self.tmp / "tags.csv"
        tags.write_text("post_id,platform,video,skill,style,posted_at,notes\n", encoding="utf-8")
        args = ["analytics/queue_to_tags.py", "--queue", "analytics/examples/publish_queue_sample.md",
                "--tags", tags, "--insights", self.insights("instagram"), "--insights", self.insights("threads"),
                "--drafts-dir", "analytics/examples/drafts_sample", "--pending-out", self.tmp / "pending.csv"]
        run(*args, "--apply")
        rows = {(r["platform"], r["post_id"]): r for r in read_csv(tags)}
        self.assertEqual(set(rows), {("instagram", "ig1"), ("threads", "th1"),
                                     ("x", "1850000000000000001"), ("instagram", "ig2")})
        self.assertEqual(rows[("instagram", "ig2")]["skill"], "interview-reel")   # from 技能： line
        self.assertEqual(rows[("x", "1850000000000000001")]["posted_at"], "2026-10-20")
        self.assertNotIn("igsh", rows[("instagram", "ig2")]["notes"])
        pending = read_csv(self.tmp / "pending.csv")
        self.assertEqual(len(pending), 2)
        self.assertTrue(any("no media id" in r["notes"] for r in pending))
        run(*args, "--apply")                                                     # second run adds nothing
        self.assertEqual(len(read_csv(tags)), 4)

    def test_existing_video_tag_is_reused(self):
        tags = self.tmp / "tags.csv"
        tags.write_text("post_id,platform,video,skill,style,posted_at,notes\n"
                        "999,x,2026-10-27-ep-h,diagram-design,Business motion explainer,2026-10-27,\n",
                        encoding="utf-8")
        run("analytics/queue_to_tags.py", "--queue", "analytics/examples/publish_queue_sample.md",
            "--tags", tags, "--insights", self.insights("threads"), "--apply")
        rows = {(r["platform"], r["post_id"]): r for r in read_csv(tags)}
        self.assertEqual(rows[("threads", "th3")]["style"], "Business motion explainer")


class CopyLint(Base):
    def draft(self):
        d = self.tmp / "draft"
        (d / "threads").mkdir(parents=True)
        (d / "en").mkdir()
        (d / "ig_caption.txt").write_text("黃仁勳專訪\n#a #b #c #d #e #f\n", encoding="utf-8")
        (d / "threads" / "1.txt").write_text("这是測試 — 好\n", encoding="utf-8")
        (d / "threads.txt").write_text("第一篇\n---\n第二篇​內容 #AI #NVIDIA\n", encoding="utf-8")
        (d / "x_post.txt").write_text("重點整理 https://example.com\n", encoding="utf-8")
        (d / "en" / "ig_caption.txt").write_text('He said "hi" \U0001F468‍\U0001F4BB\n', encoding="utf-8")
        return d

    def test_draft_folder(self):
        d = self.draft()
        p = run("josh-video-router/scripts/copy_lint.py", d, ok=False)
        self.assertEqual(p.returncode, 1)
        out = p.stdout
        self.assertIn("6 hashtags", out)
        self.assertIn("em-dash", out)
        self.assertIn("simplified character(s) 这", out)
        self.assertIn("invisible character", out)
        self.assertIn("post 2/2", out)
        self.assertIn("external link in the X post body", out)
        # find the en/ caption's section by its label, not its path: Windows prints en\ig_caption.txt
        en = next(s for s in out.split("== ") if "[instagram, en]" in s)
        self.assertNotIn("invisible", en)                     # ZWJ inside an emoji is legitimate
        self.assertNotIn("double quotes", en)                 # en/ skips Chinese-only checks

    def test_fix_invisible(self):
        d = self.draft()
        run("josh-video-router/scripts/copy_lint.py", "--fix-invisible", d / "threads.txt")
        self.assertNotIn("​", (d / "threads.txt").read_text(encoding="utf-8"))

    def test_quoted_title_exempt(self):
        f = self.tmp / "x_longpost.md"
        f.write_text("來源：〈Codex 爆款视频skill，10个装完百万播放〉\n", encoding="utf-8")
        run("josh-video-router/scripts/copy_lint.py", f)

    def test_threads_emoji_bytes_limit(self):
        f = self.tmp / "threads.txt"
        f.write_text("\U0001F600" * 130, encoding="utf-8")   # 130 characters but 520 UTF-8 bytes
        p = run("josh-video-router/scripts/copy_lint.py", f, ok=False)
        self.assertEqual(p.returncode, 1)
        self.assertIn("length 520 / 500", p.stdout)


if __name__ == "__main__":
    unittest.main()
