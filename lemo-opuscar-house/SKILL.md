---
name: lemo-opuscar-house
description: "House-rules adapter for the October 2026 additions to the third-party lemo-opuscar style library (LemoLab): the Edit & Documentary styles (2026-10-22), the Evidence Films styles (2026-10-16) and Make a style your own (MY-STYLES.md). Use when a 9:16 Reel about AI startups, AI agents, one-person companies or straight news should be built from real footage, documents or data in one of these looks. Triggers: 「用 lemo 的新聞風格」, 「Caption News」, 「Broadcast News Package」, 「視覺調查」, 「做成我自己的風格」."
---

# lemo-opuscar-house: new lemo-opuscar styles under the house rules

Upstream: https://github.com/lemomo-ai/lemo-opuscar (checked 2026-10-22, commit on main of that date). Style list: [`styles/README.md`](https://github.com/lemomo-ai/lemo-opuscar/blob/main/styles/README.md). Nothing from upstream is copied into this repo; this page links and summarizes.

**Credit: LemoLab.** Code is MIT (Copyright (c) 2026 LemoLab). Demo films and stills are CC BY 4.0: if a demo still or clip is ever shown, credit "LemoLab, lemo-opuscar" with a link and say if it was changed. Third-party assets inside demos keep their own licences (each demo's `CREDITS`).

**Excluded voice tracks.** Three upstream voice tracks are not covered by CC BY 4.0 and must never be reused: the shouts in Game Show Flat (macOS `say`), the narration in Paper-cut Lightbox (Microsoft Edge TTS), and the narration in Broadcast News Package (Doubao TTS, Volcengine terms).

**This skill produces drafts only and never posts.**

## House overrides (apply to every style below)

- **Size**: upstream renders 1920×1080 by default. Always pass `--size 1080x1920` to the render tools, and re-lay out the frame; never crop a landscape render. Keep the bottom subtitle block above y=1490 and focal content left of x=950 (IG buttons), same zones as `stock-footage-reel`.
- **Voice**: use Josh's ElevenLabs voices instead of upstream's default Kokoro: Chinese 「<YOUR_VOICE_NAME>」 `<YOUR_ELEVENLABS_VOICE_ID>`, English "Josh - Calm, Warm Taiwanese narrator" (`xBHPgy3hJ2fclZQIoDnv`), via OpenMontage `elevenlabs_tts` with per-line caching. Voiceover reads the subtitles exactly.
- **Copy**: Taiwan Traditional Chinese, 「」 quotes, no em-dashes, no brand logos, no first-person opinion in news videos. Every number and date goes in `facts.md` for 事實編輯.
- **Real material only**: these styles are built from real footage, documents and data. Use licence-clean sources (Pexels, Prelinger, NASA, LOC, Wikimedia via `openmontage-house/scripts/om_clips.py`) or the company's own public material, and credit them. Never pass a generated image off as evidence.
- Don't edit upstream `core/` or `styles/` for a film (upstream rule too).

## Styles worth using for Josh's topics

| Style (folder) | Added | Fits | 9:16 notes |
|---|---|---|---|
| Caption News (`caption-news`) | 2026-10-22 | Daily AI / startup news, sound-off first; the default pick among the new styles | Upstream documents vertical: caption under a 1080×1560 footage band, caption chunks stacked on two lines. One Chinese keyword in the yellow block |
| Broadcast News Package (`news-package`) | 2026-10-22 | Weekly roundups (「本週 AI 新聞」), funding / launch rundowns | Rebuild the strap and rundown for a 1080-wide frame; replace the demo's voice (excluded Doubao track) with ElevenLabs. No real network branding |
| Visual Investigation (`visual-investigation`) | 2026-10-22 | Reconstructing an incident: an AI agent security breach, an outage, a timeline of a company collapse | Landscape layout is content y 60–900; for 9:16 stack sources vertically and move the clock readout above the subtitle block. 30 fps |
| Live Countdown Split-screen (`countdown`) | 2026-10-22 | Launch events, livestream moments that ran in real time | Split screen becomes top / bottom halves; the clock sits between them. Never speed up or reorder the footage |
| Constructivist Montage (`kino-montage`) | 2026-10-22 | Argument-style pieces on big shifts (e.g. one-person company vs. old org charts) built from archive | Two-tone print with red as the only colour; enlarge type for phones |
| 1920s Newsreel (`newsreel`) | 2026-10-22 | Occasional history hook ("100 年前也有人怕自動化") | 1.37:1 gate does not fit 9:16; put the gate in the upper band, captions below. Archive ≤ 2.5× upscale |
| Engineering Briefing Board (`briefing-board`) | 2026-10-16 | How an AI hardware product or system decides, explained on a "board" | Board crop to a tall panel; real cut-out photos only |
| Data Physicalization (`data-physical`) | 2026-10-16 | Funding totals, compute, model sizes ("1 塊 = 10 億美元") | Stacks read well vertically; state the unit rule on screen once |
| Exploded Teardown (`teardown`) | 2026-10-16 | AI device / chip hardware explainers when layout files are public | Needs real board layout data; otherwise skip |
| Archive Light Table (`archive-lighttable`) | 2026-10-16 | Documents and filings as evidence (court papers, S-1, patent drawings) | Licensed or public-domain scans only |

Skipped for Josh's channel (link only): Time-lapse Symphony (`city-symphony`, a film about a place, score-led), Sports Telestrator (`telestrator`, sports footage), Satellite Briefing, LiDAR Survey, Projection on White Model, Microscope Story (need georeferenced imagery, point clouds, building data or micrographs that AI-business topics rarely have). Use them only if a topic truly calls for that data.

## Make a style your own (MY-STYLES.md, 2026-10-19 / 2026-10-22)

Upstream now lets a user change a library style or start from a blank page, prove it with a style frame and a 15–30 s test film, and keep it in `~/lemo-my-styles/<slug>/` (outside the library, so updates never touch it). See [`MY-STYLES.md`](https://github.com/lemomo-ai/lemo-opuscar/blob/main/MY-STYLES.md).

For Josh: a confirmed house variant (for example Caption News with the house palette, Noto Sans TC, 1080×1920 and the ElevenLabs voices) should set `"size": "1080x1920"` in its `style.json`, so the vertical size is the default. Making one needs Josh's approval of the style frame and test film; nothing is posted.

## Who uses it

- **內容製作**: picks the style, gathers real material, renders at 1080×1920, voices with ElevenLabs, hands off to 事實編輯.
- **Grok Boss**: names one of these styles as the recommended visual style in topic proposals (news → Caption News; weekly roundup → Broadcast News Package; incident reconstruction → Visual Investigation).
- **事實編輯**: checks every caption, number, date and source credit.
