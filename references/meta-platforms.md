# Instagram, Threads, and X: platform facts the scripts rely on

Checked on **2026-11-01**. Platforms change these without notice: if a script and the platform disagree, the platform is right; update this file and the script together. Every figure here is used by `threads-scout`, `analytics/meta_insights.py`, or `josh-video-router/scripts/copy_lint.py`.

Labels: **official** = Meta's or X's developer docs. **reported** = trade press quoting the company, not in official docs; scripts only WARN on these. **unverified** = widely cited, no primary source found in this check.

## Threads

| Fact | Value | Label | Source |
|---|---|---|---|
| API base | `https://graph.threads.com/v1.0` (older code uses `graph.threads.net`) | official | [Threads insights](https://developers.facebook.com/docs/threads/insights) |
| Post text limit | 500 characters; emoji count by UTF-8 byte length | official | [Threads posts](https://developers.facebook.com/docs/threads/posts) |
| Links per post | at most 5 unique links (text + link attachment); more fails with `THREADS_API__LINK_LIMIT_EXCEEDED` since 2025-12-22 | official | same |
| Topic tags | one per post; 1 to 50 characters, no `.` or `&`; with several in-text tags only the first valid one is used | official | same |
| Video | up to 300 s, up to 1 GB, MOV/MP4, 23 to 60 fps, max width 1920 px | official | same |
| Carousel | 2 to 20 items, counts as one post | official | same |
| Publishing cap | 250 posts per profile per 24 h | official | same |
| Keyword search | `GET /keyword_search`, `q`, `search_type` TOP/RECENT, `search_mode` KEYWORD/TAG, `media_type`, `since`, `until`, `limit` ≤ 100, `author_username` | official | [Keyword search](https://developers.facebook.com/docs/threads/keyword-search) |
| Keyword search permission | `threads_basic` + `threads_keyword_search`; **without approval it silently searches only the token owner's own posts** | official | same |
| Keyword search quota | 2,200 queries per user per rolling 24 h, shared across all apps; repeats count; empty results don't | official | same |
| Sensitive keywords | return an empty list, not an error | official | same |
| Post insights | `views` (in development), `likes`, `replies`, `reposts`, `quotes`, `shares` (in development) | official | [Threads insights](https://developers.facebook.com/docs/threads/insights) |
| Account insights | `views`, `likes`, `replies`, `reposts`, `quotes`, `clicks`, `followers_count`, `follower_demographics`; `since`/`until` not before 2024-04-13; not guaranteed before 2024-06-01 | official | same |
| Insights permission | `threads_basic` + `threads_manage_insights` | official | same |

## Instagram

| Fact | Value | Label | Source |
|---|---|---|---|
| Graph API version | v26.0; host `graph.facebook.com` (Facebook Login) or `graph.instagram.com` (Instagram Login) | official | [Media insights](https://developers.facebook.com/docs/instagram-platform/reference/instagram-media/insights) |
| Reels insights | `views`, `reach`, `likes`, `comments`, `shares`, `saved`, `total_interactions`, `ig_reels_avg_watch_time`, `ig_reels_video_view_total_time`, `reels_skip_rate`, `reposts`, `crossposted_views`, `facebook_views`, and others | official | same |
| `impressions` | deprecated for media created after 2024-07-02 | official | same |
| Insights permissions | `instagram_basic` + `instagram_manage_insights` (Facebook Login; may also need `pages_read_engagement`), or `instagram_business_basic` + `instagram_business_manage_insights` (Instagram Login) | official | same |
| API publishing cap | the page states both 100 and 50 posts per 24 h; check `GET /<IG_ID>/content_publishing_limit` | official, inconsistent | [Content publishing](https://developers.facebook.com/docs/instagram-platform/content-publishing) |
| Hashtags per caption | 5, "gradually" rolling out from 2025-12-18 (older Help Center pages still say 30) | reported | [Social Media Today, 2025-12-18](https://www.socialmediatoday.com/news/instagram-implements-new-limits-on-hashtag-use/808309/) |
| Caption length | 2,200 characters | unverified | not stated on the content publishing page |
| Feed preview | about 125 characters before "more" (Latin text; CJK shows fewer) | unverified | community figure, used only as an approximate preview |

## X

| Fact | Value | Label | Source |
|---|---|---|---|
| Weighted length | 280; Latin and common punctuation 1, CJK and emoji 2, any URL 23; NFC-normalized | official | [Counting characters](https://docs.x.com/fundamentals/counting-characters) |
| Link cost | post with an external link $0.20 vs $0.015 without | team (X API Engineer) | router Step 3 |

## What this means for the team

- Threads search is a lead source, not evidence: it returns no engagement numbers for other people's posts, and the post itself is not a citation. facts.md cites the original.
- Compare insights only within one platform and one format, at a similar post age (`age_hours`). See [analytics/README.md](../analytics/README.md).
- Posting stays manual (Grok Boss after Josh approves). Nothing here uses a publishing permission, a logged-in browser, or an unofficial client. See [github-ig-threads-survey.md](github-ig-threads-survey.md) for why.
