# analytics: compare performance by skill and style

`style_compare.py` groups posts by the style (or skill) used to make them and prints the median of each metric. Used by 數據復盤師 (Analytics).

## Where the tags live
`analytics/style_tags.csv`, one row per published post:

| Column | Meaning |
|---|---|
| `post_id` | Post id as it appears in the X export (or API) |
| `platform` | e.g. `x` |
| `video` | Draft folder name in `03-drafts/` |
| `skill` | Skill used (e.g. `stock-footage-reel`) |
| `style` | Style used (e.g. `Dark typography`, matching the INDEX.md style picks) |
| `posted_at` | Date posted (Asia/Taipei) |
| `notes` | Free text |

Add the row when the post goes live. x-scout's suggested style can be the starting value; correct it to what was actually used.

## Inputs
- `--csv`: X analytics CSV export (repeatable). Expected columns are configurable: `--id-col` (default `Post id`; also tries `Tweet id`, `id`, `post_id`) and `--metrics` (default: every numeric column, e.g. `Impressions`, `Likes`, `Reposts`, `Replies`, `Bookmarks` if the export has them). Column names vary by export; check the header and pass `--metrics` explicitly when needed.
- `--api` (optional): JSON of your own posts from the X API (`{"data": [...]}` with `public_metrics`). Its fields (e.g. `like_count`) are added only where the CSV doesn't already have that column for the post. Pulling it needs `X_BEARER_TOKEN` (or user auth for non-public metrics) as an environment variable, never in a file.

## Output
A table with `posts` and `median <metric>` per group (`--by style|skill|skill_style`), plus `--out file.csv` if wanted. Only columns present in the inputs are summarized; no metrics are derived or invented. Tagged posts not found in the inputs are listed as a note.

## Example
```bash
python3 analytics/style_compare.py --csv analytics/examples/x_export_sample.csv \
  --tags analytics/examples/style_tags_sample.csv
python3 analytics/style_compare.py --csv export.csv --api own_posts.json --by skill_style \
  --metrics Impressions,Likes,Bookmarks --out style_medians.csv
```
Medians from a few posts are noisy; treat groups with under 5 posts as anecdotes.
