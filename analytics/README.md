# analytics: compare performance by skill and style (X, Instagram, Threads)

Used by 數據復盤師 (Analytics).

- `style_compare.py` groups posts by the style (or skill) used to make them and prints the median of each metric.
- `meta_insights.py` pulls Josh's **own** Instagram and Threads post insights from the official Graph APIs into a CSV that `style_compare.py` reads. Read-only: GET calls only, own account only.

## Where the tags live
`analytics/style_tags.csv`, one row per published post **per platform** (the same video posted to IG, Threads, and X is three rows, because each platform gives it a different post id):

| Column | Meaning |
|---|---|
| `post_id` | Post id as it appears in the export / API (X post id, IG media id, Threads media id) |
| `platform` | `x`, `instagram`, or `threads` |
| `video` | Draft folder name in `03-drafts/` |
| `skill` | Skill used (e.g. `stock-footage-reel`) |
| `style` | Style used (e.g. `Dark typography`, matching the INDEX.md style picks) |
| `posted_at` | Date posted (Asia/Taipei) |
| `notes` | Free text |

Rows come from `publish-queue.md` with `queue_to_tags.py` (below); add a row by hand only for a post the queue doesn't list. x-scout / threads-scout's suggested style can be the starting value; correct it to what was actually used.

## Fill style_tags.csv from publish-queue.md
`queue_to_tags.py` reads `<YOUR_WORKSPACE>/media-team/00-profile/publish-queue.md` and writes one tag row per published post URL.

```bash
# 1. pull insights first: IG and Threads URLs don't contain the media id, the insights CSV maps them
python3 analytics/meta_insights.py --platform instagram --since 2026-10-01 --out ig.csv
python3 analytics/meta_insights.py --platform threads --since 2026-10-01 --out threads.csv
# 2. dry run: shows ready rows and pending rows with the reason
python3 analytics/queue_to_tags.py --queue <YOUR_WORKSPACE>/media-team/00-profile/publish-queue.md \
  --drafts-dir <YOUR_WORKSPACE>/media-team/03-drafts --insights ig.csv --insights threads.csv --pending-out pending.csv
# 3. append the ready rows (never edits or duplicates existing rows; safe to re-run every week)
python3 analytics/queue_to_tags.py ... --apply
```

What the queue needs (the parser is tolerant, but these three things must be there):
- **The draft folder** (`03-drafts/<題目>` or the `YYYY-MM-DD-slug` folder name), on the URL's line or on a heading above it.
- **The live post URL** for each platform once it is posted: `instagram.com/reel/...`, `threads.com/@.../post/...`, `x.com/.../status/...`.
- **The posting date** (`YYYY-MM-DD`) on the URL's line or the folder's line.

Skill and style come from an existing tag row for the same video, else from a `skill:` / `style:` (or `技能：` / `風格：`) line in that draft's `handoff.md`, `facts.md`, or `storyboard.md`. When neither has them the row stays in `pending.csv` for 數據復盤師 to fill; nothing is guessed. `examples/publish_queue_sample.md` shows both a heading-per-video layout and a table layout (fictional data).

## Pull Instagram and Threads insights
```bash
# Instagram (professional account): IG_ACCESS_TOKEN + IG_USER_ID as env vars
python3 analytics/meta_insights.py --platform instagram --since 2026-10-01 --product REELS --out ig.csv
# Threads: THREADS_ACCESS_TOKEN as env var
python3 analytics/meta_insights.py --platform threads --since 2026-10-01 --out threads.csv
# offline, from the fictional samples
python3 analytics/meta_insights.py --platform threads --input analytics/examples/threads_raw_sample.json \
  --as-of 2026-11-01T00:00:00Z --out threads.csv
```
- Permissions: Instagram needs `instagram_basic` + `instagram_manage_insights` (Facebook Login, host `graph.facebook.com`) or `instagram_business_basic` + `instagram_business_manage_insights` (Instagram Login, set `IG_GRAPH_BASE=https://graph.instagram.com/v26.0`). Threads needs `threads_basic` + `threads_manage_insights`.
- Default metrics (official names, checked 2026-11-01): IG Reels `views, reach, likes, comments, shares, saved, total_interactions, ig_reels_avg_watch_time` (milliseconds) `, ig_reels_video_view_total_time`; other IG media drop the two Reels-only metrics; Threads `views, likes, replies, reposts, quotes, shares` (Meta marks Threads `views` and `shares` as "in development"). Meta renames metrics; if one is rejected the script warns per post, so pass `--metrics` with the current names. Platform facts and sources: [references/meta-platforms.md](../references/meta-platforms.md).
- Each row also gets `posted_at`, `snapshot_at`, and `age_hours`. Insights keep growing after posting, so a 12-hour-old post and a 10-day-old post are not comparable.
- One insights request per post; keep `--limit` small and run it weekly rather than in a loop. Tokens are environment variables only, never in a file or printed.

## Inputs to style_compare.py
- `--csv`: metrics CSV (repeatable): an X analytics export or `meta_insights.py` output. `--id-col` (default `Post id`; also tries `Tweet id`, `id`, `post_id`) and `--metrics` (default: every numeric column, e.g. `Impressions`, `Likes`, `views`, `shares`). Column names vary by export; check the header and pass `--metrics` explicitly when needed.
- `--api` (optional): JSON of your own posts from the X API (`{"data": [...]}` with `public_metrics`). Its fields are added only where the CSV doesn't already have that column for the post. Needs `X_BEARER_TOKEN` (or user auth for non-public metrics) as an environment variable, never in a file.

## Comparing like with like
- `--platform x|instagram|threads`: keep only that platform's tags. Use it whenever the tag file mixes platforms (the script warns otherwise): `views` on Threads and `Impressions` on X are not the same thing.
- `--min-age-hours 72`: leave out posts younger than 72 hours (needs `age_hours`). The median post age per group is always shown when the column exists, so an "old vs new" difference is visible instead of hidden.
- Compare the same format: a Reel against Reels, a Threads video against Threads videos. Tag text-only Threads posts and carousels with their own style (e.g. `Text post`, `Carousel`) so they don't sit in a video style's median.
- Posting time is not a cause. Two posts at the same hour with different results say nothing about the hour.

## Opt-in derived numbers
Nothing is derived unless you ask, and derived columns are labeled with their formula:
- `--rate NAME=NUM/DEN` (repeatable): per-post ratio, then the median. Useful ones: `share_rate=shares/reach` (IG; sends per reach are a stronger signal than raw views), `save_rate=saved/reach` (IG), `share_rate=shares/views` (Threads).
- `--outliers METRIC`: every selected post's METRIC as a multiple of the median of all selected posts, highest first. "3.2x my own median" says more than a raw view count, because raw counts mostly track how old or how boosted a post is.

## Example
```bash
python3 analytics/style_compare.py --csv analytics/examples/x_export_sample.csv \
  --tags analytics/examples/style_tags_sample.csv --platform x
python3 analytics/style_compare.py --csv ig.csv --platform instagram --min-age-hours 72 \
  --metrics views,reach,shares,saved --rate share_rate=shares/reach --outliers views --out ig_style.csv
```
Medians from a few posts are noisy; treat groups with under 5 posts as anecdotes. The files in `examples/` are fictional test data.
