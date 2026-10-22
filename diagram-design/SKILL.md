---
name: diagram-design
description: "House-rules adapter for making Josh's explainer diagrams with the third-party diagram-design skill (editorial HTML + SVG diagrams, 45 types, no shadows, no Mermaid default styling). Use when a video needs a drawn explanation rather than footage: how an AI agent works, a workflow, a system architecture, a process explainer. Covers the 9:16 plate geometry, how to render the HTML/SVG into 1080x1920 video frames, and how to hand the frames to stock-footage-reel or OpenMontage. Triggers: 「畫一張圖解」 (draw a diagram), 「架構圖」 (architecture diagram), 「流程圖」 (flowchart), 「agent 怎麼運作」 (how the agent works), \"diagram\", \"explainer diagram\"."
---

# diagram-design: editorial diagrams as 9:16 video frames

Upstream skill: **[cathrynlavery/diagram-design](https://github.com/cathrynlavery/diagram-design)** by Cathryn Lavery, MIT License, Copyright (c) 2025 Cathryn Lavery. Not this repo's work.

**Nothing from upstream is copied into this repo.** Its MIT license would permit copying with the notice kept, but this repo's convention is that third-party skills are linked, not vendored (see README, "Third-party skills"), so this folder is a house-rules adapter only: what the upstream skill is good for here, what to ask it for, and how to turn its output into video frames. The upstream repo is authoritative for the diagram rules themselves; a summary is in [references/upstream.md](references/upstream.md).

**Drafts only, never posts.** Posting is always handled by the main bot after Josh confirms.

## Step 1: Is a diagram the right answer?

| Topic | Diagram? | Type to ask for |
|---|---|---|
| How an AI agent works (loop, tools, memory, handoffs) | Yes, first choice | Loop/flywheel, sequence, or architecture |
| A workflow or an internal process (our own pipeline, a review flow) | Yes, first choice | Flowchart, swimlane, or user journey |
| System architecture of a product being discussed | Yes, first choice | Architecture, layer stack, data flow |
| Process explainer (how a regulation review runs, how a release ships) | Yes, first choice | Process, timeline, state machine |
| Price / benchmark / KPI numbers | No | huashu `templates/data_card_render.py` data card |
| News events, interview quotes, anything with real footage | No | stock-footage-reel / interview-reel |
| Decorative visuals, art styles, whole animated shorts | No | huashu-art-motion, lemo-opuscar |

A diagram is a **factual claim**, not decoration: every box and arrow has to be defensible from the sources in `facts.md`. If the structure of the thing is not actually known from the sources, do not draw it.

## Step 2: Check the upstream skill is installed (ask before installing)

The upstream skill is **also named `diagram-design`**, so it must not be installed on top of this folder. Keep it at its own path, referred to below as `<DIAGRAM_DESIGN_DIR>`; the recommended layout is `<SKILLS_DIR>/cathrynlavery-diagram-design/skills/diagram-design/`. When both are symlinked into one skills directory, expose this adapter as `diagram-design-house` so the two names and trigger words do not fight.

```bash
<SKILLS_DIR>/josh-video-router/scripts/check_skill.sh cathrynlavery-diagram-design skills/diagram-design/SKILL.md
```

If it is missing, **stop and ask Josh** before installing. Installing third-party skills on your own is a playbook "never" ([AGENT-PLAYBOOK.md](../AGENT-PLAYBOOK.md), §4). The documented install is `npx skills add cathrynlavery/diagram-design` (it also ships Claude Code / Codex / Cursor marketplace manifests); when installing it by hand, clone it to the path above. No API key, no paid service; export needs Playwright, which this repo already uses in `screen-record`.

Do not run the upstream "onboard diagram-design to <site>" brand-extraction flow against someone else's website to borrow their look. Set the house tokens by hand instead (Step 3).

## Step 3: What to ask the upstream skill for

Say the plate size, the type, and the house constraints in the request. The constraints that differ from upstream defaults:

1. **Plate size**: ask for a custom viewBox of **872 x 960** (not a size preset; the presets are landscape, square, or print). Geometry and why: [references/render-916.md](references/render-916.md).
2. **Complexity**: `simplified` detail level, and for 9:16 cap it tighter than upstream's budget: **max 5 nodes and 7 arrows per plate**. A bigger diagram becomes several plates revealed in sequence, never one crowded plate.
3. **Type sizes** (phone legibility; the frame's own English subtitle line is 34px): plate title ≥ 44px, node labels ≥ 28px, mono / technical labels ≥ 22px. Smaller type is unreadable on a phone and is the single most common reason a plate has to be redrawn.
4. **Fonts**: upstream defaults are Instrument Serif / Geist / Geist Mono, which have **no CJK glyphs**. For Traditional Chinese labels specify **Noto Sans TC** (and Noto Serif TC for titles), the same fonts as the covers and subtitles (`COVERS_DIR/fonts/`). Ask for system-font mode so the HTML makes no network request at render time.
5. **Icons**: upstream vendors devicon / simple-icons / logz icon sets, which are **brand logos**. House rule is no brand logos on screen, so use **tabler** (generic) icons only, or no icons.
6. Keep upstream's own non-negotiables as they are: no shadows, no generic Mermaid styling, orthogonal connectors, one accent color with at most 2 focal elements, 4px grid, accessible SVG.

Wording inside the plate follows the house rules: Taiwan Traditional Chinese, 「」 quotes, no em-dashes (—), no brand logos, no first-person opinion in news videos.

## Step 4: Render the HTML/SVG into 1080x1920 frames

Full recipe, safe zones, export and ffmpeg commands, step reveals, and the pitfalls: **[references/render-916.md](references/render-916.md)**.

Short version: export the HTML to PNG at 2x with the upstream export helper (or a Playwright screenshot), then composite the plate onto a 1080x1920 canvas at x=72, y=280 and hold it for the length of the line. Multi-step diagrams export one PNG per reveal step and cross-fade.

## Step 5: Put the frames into the video

- **stock-footage-reel**: in `shots.json`, for that shot write
  `"pick": {"source":"file","path":"/abs/diagram01.mp4","license":"Original diagram (diagram-design)","author":"Josh"}`
- **OpenMontage (via openmontage-house)**: add the mp4 (or the PNG) as a local asset.
- `credits.json` entry: `{"source":"diagram-design","credit":"Original diagram, rendered with diagram-design (MIT, Cathryn Lavery)","url":"https://github.com/cathrynlavery/diagram-design","made":"YYYY-MM-DD"}`. The diagram itself is original artwork, so there is no third-party asset license to clear; the **facts** in it still need sources in `facts.md`.
- No credit line is required in the post caption (MIT does not ask for it in the output), but keep the tool named in `credits.json` so Analytics can tag diagram videos.

## House rules (every video, from josh-video-router Step 2)

1. Vertical **1080x1920**, under 3 minutes; IG final under 45 MB (`video-pipeline/reel.sh ig`, confirm with `ffprobe`).
2. Voiceover: Chinese uses your own ElevenLabs voice `<YOUR_ELEVENLABS_VOICE_ID>`; English uses Josh's own voice **Josh - Calm, Warm Taiwanese narrator** (`ELEVENLABS_VOICE_ID_EN`, `xBHPgy3hJ2fclZQIoDnv`), model `eleven_multilingual_v2`, about 1,800 characters per video, `generations_count: 1`.
3. The voiceover reads the subtitles exactly; the final subtitle file is the single source. **The plate must not contradict the line it covers**, and a label the voiceover never says is usually a label to delete.
4. Subtitles: Traditional Chinese main lines + one smaller English line, bottom edge at **y=1490**. The plate stays clear of the subtitle block and of the IG interface (Step 4 geometry).
5. Cover by topic (`covers/render.py`); tool / explainer topics use template F light info card. A diagram plate is not a cover.
6. No brand logos on screen (this is why the devicon / simple-icons sets are out).
7. Taiwan Traditional Chinese, 「」 quotes, no em-dashes. News videos report only the news.
8. Do not turn on paid services or add API keys; do not use Chinese-mainland services. Upstream needs neither.
9. Output to `<YOUR_WORKSPACE>/media-team/03-drafts/<題目>/`, then hand off to 事實編輯 (Fact Editor).

## Best fit and agent usage

**Best fit:** explainer plates for how-it-works topics: AI agent mechanics, workflows, system architecture, process explainers. **Not for:** numbers and data cards (huashu), real-footage news, interview quotes, covers, or whole animated shorts.

- **內容製作 (Content Producer)**: the main user. Asks upstream for the plate with the Step 3 constraints, renders the frames per Step 4, wires them into stock-footage-reel or OpenMontage, and delivers to `03-drafts/`.
- **Grok Boss**: names "diagram-design plate" as the recommended visual style in a topic proposal when the topic is a how-it-works explanation rather than a news event, with the one-line reason required by the [recommended-style rule](../INDEX.md#topic-proposals-recommended-style-rule). Confirms the skill via the router before production.
- **事實編輯 (Fact Editor)**: treats every box, arrow, and label as a claim to check against `facts.md`; also checks no brand logos and no label the voiceover never says.
- **情報偵察員 (Scout)**: flags topics whose source explains a mechanism or architecture (those are the diagram candidates).
- **數據復盤師 (Analytics)**: tags these videos as the `diagram` style in `analytics/style_tags.csv` so diagram plates can be compared against footage edits.
- **Coding agent (Claude Code / Cursor)**: input: the upstream skill installed + the plate brief; output: `diagram01.png` (2x), `diagram01.mp4` (1080x1920), and a `pick` entry for `shots.json`. Never posts.

## License and attribution

The upstream diagram-design skill is **MIT**, Copyright (c) 2025 Cathryn Lavery (<https://github.com/cathrynlavery/diagram-design>). Its diagram rules, templates, and scripts belong to it and are not reproduced here. Files in this folder are this repo's own work under the repo's [MIT License](../LICENSE).

Agent workflow (preflight, human gates, costs, failures, done, handoff): see [AGENT-PLAYBOOK.md](../AGENT-PLAYBOOK.md).
