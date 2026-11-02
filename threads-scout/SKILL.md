---
name: threads-scout
description: "Read-only Threads topic watcher for 情報偵察員 (Scout): search public Threads posts with the official Threads API keyword search, classify each hit with the same topic types as x-scout (AI news, interview, one-person company, tool demo, numbers-heavy news, pharma regulatory), and suggest a skill plus style with a one-line reason. Never posts, replies, likes, reposts, or follows."
---

# threads-scout: read-only Threads topic watcher

**Read-only.** Its only network calls are GETs to the official Threads API (`/me` once, then `/keyword_search` per query). It never posts, replies, likes, reposts, or follows, and never uses a logged-in browser session or an unofficial / reverse-engineered client. Topic proposals go to Grok Boss; the router decides the final skill.

Taiwan's Chinese-language AI and pharma conversation is often on Threads before X, which is why this sits next to x-scout. Both share one topic table: `scripts/threads_scout.py` imports `classify()` and `SUGGEST` from `../x-scout/scripts/x_scout.py`, so keep the two folders at the same level (or set `SKILLS_DIR`).

## Credentials and permissions
- `THREADS_ACCESS_TOKEN` as an environment variable only. Never write it to a file, commit it, or print it. Long-lived Threads tokens last 60 days; refreshing one is Josh's call.
- The Meta app needs `threads_basic` and `threads_keyword_search`. **Without an approved `threads_keyword_search`, Meta does not return an error: it searches only the token owner's own posts.** The script warns when every hit is Josh's own. Requesting that permission (App Review) is a human gate: ask Josh. **Status (2026-11-01): Josh decided not to request it for now.** Until he does, x-scout is the Scout's live source; threads-scout runs offline (`--input`) or on Josh's own posts only, so don't run it on a schedule.
- Without a token, use `--input` with a saved response to work offline.

## Usage
```bash
cd <SKILLS_DIR>/threads-scout
THREADS_ACCESS_TOKEN=... python3 scripts/threads_scout.py --config examples/topics.json --limit 25 --out hits.json
THREADS_ACCESS_TOKEN=... python3 scripts/threads_scout.py --config examples/topics.json --search-type RECENT --since-hours 24
python3 scripts/threads_scout.py --config examples/topics.json --input examples/sample_search.json   # offline test
```
- `examples/topics.json`: `queries` are plain keywords (Chinese works), or objects `{"q": ..., "search_mode": "TAG", "media_type": "TEXT|IMAGE|VIDEO"}`. X operators such as `-is:retweet` or `lang:` are rejected before any call. `classify` adds Chinese keywords per topic type; edit both for the current watch list.
- `--search-type TOP` (default, popular first) or `RECENT`. Replies are dropped unless `--include-replies`.
- Output per hit: permalink, author, time, media type, text, `topic_type`, `suggested_skill`, `suggested_style`, `reason`. Keyword search returns **no engagement numbers** for other people's posts, so the Scout judges traction by reading the post, not from metrics.
- `examples/sample_search.json` is fictional test data, not real posts.

## Cost and limits (official docs, checked 2026-11-01)
- 2,200 keyword_search queries per user per rolling 24 hours, **shared across every app** the account uses. Repeats of the same keyword count again; queries with no results do not count. Run on a schedule, not in a loop.
- Keywords Meta treats as sensitive return an empty list, not an error.
- Sources and the other platform facts the team relies on: [references/meta-platforms.md](../references/meta-platforms.md).

## Topic type → suggestion
Same table as [x-scout](../x-scout/SKILL.md#topic-type--suggestion). Classification is keyword-based and will misfire; the Scout reviews each hit before proposing it, and every proposal follows the [recommended-style rule](../INDEX.md#topic-proposals-recommended-style-rule). A Threads post is a lead, not a source: facts.md cites the original article, video, or filing the post points to.

## Best fit and agent usage

**Best fit:** spotting Traditional Chinese topics (Taiwan AI, TFDA, solo-business) that surface on Threads before X. **Not for:** posting or any engagement, reading private data, or verifying facts (Fact Editor).

- **情報偵察員 (Scout)**: runs it with x-scout on the same schedule, merges both hit lists, and proposes topics with skill, style, and reason.
- **Grok Boss**: receives proposals and confirms the skill via the router.
- **Coding agent (Claude Code / Cursor)**: input: topics.json + `THREADS_ACCESS_TOKEN` env var (or `--input` file); output: printed suggestions and an optional hits.json.

Agent workflow (preflight, human gates, costs, failures, done, handoff): see [AGENT-PLAYBOOK.md](../AGENT-PLAYBOOK.md).
