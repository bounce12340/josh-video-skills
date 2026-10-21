---
name: x-scout
description: "Read-only X topic watcher for 情報偵察員 (Scout): search recent X posts for topic keywords, classify each hit into the router's topic types (AI news, interview, one-person company, tool demo, numbers-heavy news, pharma regulatory), and suggest a skill plus style with a one-line reason. Never posts, likes, follows, or replies."
---

# x-scout: read-only X topic watcher

**Read-only.** It never posts, likes, follows, replies, or sends DMs. Its only network call is a GET to X API v2 recent search. Topic proposals go to Grok Boss; the router decides the final skill.

## Credentials
- `X_BEARER_TOKEN` as an environment variable only (app-only bearer token, read access). Never write it to a file, commit it, or print it.
- Without the token, use `--input` with a saved search response to work offline.

## Usage
```bash
cd <SKILLS_DIR>/x-scout
X_BEARER_TOKEN=... python3 scripts/x_scout.py --config examples/topics.json --max 20 --out hits.json
python3 scripts/x_scout.py --config examples/topics.json --input examples/sample_search.json   # offline test
```
- `examples/topics.json`: `queries` (X search query syntax) and `classify` (keyword lists per topic type). Edit both to match the current watch list.
- Output per hit: post URL, time, public metrics, text, `topic_type`, `suggested_skill`, `suggested_style`, `reason`.
- Each query costs read quota on X API; keep `--max` small and run on a schedule rather than in a loop.
- Filtered stream rules (`/2/tweets/search/stream/rules`) are an alternative for continuous watching; this script uses recent search because it needs no long-running connection. Changing stream rules is a write to X app config, so ask Josh before adding them.

## Topic type → suggestion
| Topic type | Skill | Style (from INDEX.md style picks) |
|---|---|---|
| interview | interview-reel (only if an official public video exists; otherwise stock-footage-reel) | Kinetic typography for quotes |
| tool_demo | screen-record → stock-footage-reel | Tool explainer |
| pharma_regulatory | stock-footage-reel | Dark typography |
| numbers_news | stock-footage-reel (+ huashu data card if installed; check with the router's check_skill.sh) | Data animation |
| one_person_company | stock-footage-reel or huashu-art-motion | Business motion explainer |
| ai_news (default) | stock-footage-reel | Dark typography |

Classification is keyword-based and will misfire; the Scout reviews each hit before proposing it. Every proposal follows the [recommended-style rule](../INDEX.md#topic-proposals-recommended-style-rule).

## Best fit and agent usage

**Best fit:** finding fresh topics on X for every topic type Josh covers. **Not for:** engagement of any kind (posting, liking, following, replying), or verifying facts (that is the Fact Editor's job).

- **情報偵察員 (Scout)**: runs it on the watch list, reviews hits, and proposes topics with skill, style, and reason.
- **Grok Boss**: receives proposals and confirms the skill via the router.
- **數據復盤師 (Analytics)**: can reuse the suggested style as the initial tag in `analytics/style_tags.csv`.
- **Coding agent (Claude Code / Cursor)**: input: topics.json + `X_BEARER_TOKEN` env var (or `--input` file); output: printed suggestions and an optional hits.json.

Agent workflow (preflight, human gates, costs, failures, done, handoff): see [AGENT-PLAYBOOK.md](../AGENT-PLAYBOOK.md).
