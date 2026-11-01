# GitHub survey: Instagram and Threads repos (2026-11-01)

Searched GitHub for Instagram / Threads skills, MCP servers, and API tools, then read the READMEs of the most relevant ones. Nothing was copied from any of them: this repo only adopts ideas, rewritten under the house rules. Star counts and dates are as of the search; README content is the authors' own claims and was not independently tested.

## What was reviewed and what was adopted

| Repo | Stars / last push / license | What it is | Adopted here |
|---|---|---|---|
| [Jakeschincariol/instagram-agent-skill](https://github.com/Jakeschincariol/instagram-agent-skill) | 4,262 / 2026-09 / MIT | 13 Instagram skills: hooks, captions, humanizer, swipe file; drafts only, never posts | Ranking by **multiple over the account's own median** (→ `style_compare.py --outliers`); **sends per reach** over raw views (→ `--rate share_rate=shares/reach`); caption feed-window preview and the 5-hashtag cap (→ `copy_lint.py`); stripping invisible characters (→ `copy_lint.py --fix-invisible`). Its stance that browser automation of IG breaks the Terms matches ours |
| [sergebulaev/instagram-skills](https://github.com/sergebulaev/instagram-skills) | 693 / 2026-10 / MIT | 9 IG marketing skills; optional publishing through a paid third-party API | Confirms the 125-character fold and 3 to 5 sized hashtags. Not adopted: third-party publishing services (paid, and posting stays manual) |
| [Hao0321/claude-skill-social-post](https://github.com/Hao0321/claude-skill-social-post) | 748 / 2026-10 / MIT | Traditional Chinese FB / IG / Threads posting and outcome logging | **Only compare like with like**: same platform, same content type, similar post age; posting time is a candidate variable, never a cause (→ `--platform`, `--min-age-hours`, `age_hours`, analytics README). Not adopted: its logged-in Chrome comment actuation |
| [thenavidm/threads-mcp-cli](https://github.com/thenavidm/threads-mcp-cli) | 2 / 2026-10 / MIT | Threads MCP + CLI on the official API | Pointed to the silent own-posts-only fallback of keyword search and the emoji byte counting; both confirmed in Meta's docs, then built into `threads-scout` and `copy_lint.py` |
| [mikusnuz/meta-mcp](https://github.com/mikusnuz/meta-mcp), [exileum/meta-mcp](https://github.com/exileum/meta-mcp), [oliverames/meta-mcp-server](https://github.com/oliverames/meta-mcp-server) | 31 / 13 / 66, MIT | MCP servers for the IG Graph API and Threads API (publish, comments, insights) | Not installed. They include write tools; if the team ever wants one, run it read-only and ask Josh first (new token, new service) |
| [ScrapeCreators/social-media-research-skills](https://github.com/ScrapeCreators/social-media-research-skills) | 5,218 / 2026-08 / MIT | Research skills (outlier posts, comment mining) on a paid scraping API | Outlier idea already covered; not adopted (paid third-party scraping) |
| [social-media-skills/skills](https://github.com/social-media-skills/skills) | 227 / 2026-10 / MIT | 106 general social media skills | Nothing specific beyond the above |
| [itchernetski/threads-carousel-claude-skill](https://github.com/itchernetski/threads-carousel-claude-skill) | 119 / 2026-04 / MIT | Text post → carousel images | Not adopted; covers/render.py already makes the team's stills |
| [junhoyeo/threads-api](https://github.com/junhoyeo/threads-api) | 1,619 / 2023-09 / MIT | Unofficial, reverse-engineered Threads client | **Do not use**: unofficial client, unmaintained since 2023, and the official API now covers search and insights |

## Rules that came out of this

- Use only the official APIs, read-only, with tokens in environment variables. No logged-in browser sessions, cookie exports, or reverse-engineered clients for IG or Threads (AGENT-PLAYBOOK §7).
- Engagement numbers are compared against Josh's own median on the same platform and format, never as raw counts across platforms.
- Platform limits live in one place, [meta-platforms.md](meta-platforms.md), each with its source and a label for how sure it is.
