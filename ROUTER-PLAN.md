# Video skill integration plan: josh-video-router (draft, 2026-10-19)

Status: **draft, not installed**. This document only plans; no code was deleted, moved, or merged, and nothing was git pushed.
Approach: do not merge code; add a single "router skill" that points to the preferred skill for each video type and applies the house rules uniformly.

## 1. Inventory (30 folders)

`<SKILLS_DIR>/` has 22 folders (21 skills plus `_deps`), and `<YOUR_WORKSPACE>/tools/` has 8 more. huashu-art-motion is a symlink in skills/, and lemo-opuscar exists in two places (the tools/ copy has .git, the skills/ copy does not, and some files differ). Counting each once, there are about 27.

| Skill | What it does | Input → output | Dependencies | License | Fit |
|---|---|---|---|---|---|
| interview-reel | Fox-style celebrity interview: commentary intercut with 15 to 30 seconds of original audio | spec.json + official video → 1080x1920 mp4 | yt-dlp, ElevenLabs, ffmpeg | Self-written | ✅ Preferred |
| stock-footage-reel | Voiceover + real footage, documentary style | Voiceover script → mp4 | Pexels (free key), Mixkit, Wikimedia, ElevenLabs / edge-tts | Self-written | ✅ Preferred |
| openmontage-house | OpenMontage house-rules adapter + om_clips.py | Depends on pipeline | OpenMontage | Self-written | ✅ |
| screen-record | Playwright recording of public web pages | JSON spec → 1080x1920 mp4 | Playwright | Self-written | ✅ |
| OpenMontage | 12 pipelines (montage, clipping, screen tutorials, translated dubbing, podcast, etc.) | Depends on pipeline | Python, Remotion, some paid image generation | AGPLv3 | ✅ (local use only, not offered as a service) |
| huashu-art-motion | 35 art styles + 9 explainer grammars | Shot list + voiceover → mp4 | Can take an existing recording | MIT | ✅ Preferred (explainer / art) |
| xilo-opus-video | Three-option preview → frame-by-frame web capture | brief + voice.wav → mp4 | Local Chrome, no cloud TTS | MIT | ✅ |
| lemo-opuscar | 39 special code-rendered styles | Story → mp4 | TTS, code-generated music | MIT | ✅ (styles huashu lacks) |
| video-shotcraft | Product promo videos, 124 shot cards | URL / screenshots → mp4 | Remotion 4.0.484 | Apache-2.0 | ⚠️ Landscape by default; needs re-layout |
| video-talkcraft | Voiceover-driven explainers with word-level timestamps | Script + voiceover → mp4 | Remotion, sherpa-onnx ASR; Fish Audio option not used | PolyForm Noncommercial | ⚠️ Commercial use restricted; reference only |
| anything2explainer | Black-background motion-graphics explainers | Topic → mp4 | Remotion, edge-tts | PolyForm Noncommercial | ⚠️ Hard-coded 1280x720, commercial use restricted |
| vox-director | Vox collage-style explainers / ads | Topic → mp4 | Atlas Cloud API (paid) | MIT | ❌ Paid key |
| hand-drawn-video-prompts | Chinese voiceover script → hand-drawn crayon-style B-roll prompts | Script → prompts (final video needs image generation) | Image generation service | MIT | ⚠️ Prompt mode only |
| stickman-video-director | Stickman English video prompt pack | Copy → Gemini Omni / Flow prompts | Google Flow credits | MIT | ⚠️ Prompts only |
| kid-papercraft | Children's papercraft birthday video prompts | 5 questions → prompts | Cartoon IP | MIT (README has a non-commercial disclaimer) | ❌ Unrelated to the account, IP risk |
| hbg-life-simulation | "Life dungeon" (人生副本) comic narrative videos | Long copy → mp4 | Image generation, Edge TTS, HyperFrames | MIT | ⚠️ Needs image generation |
| hbg-classical-poem-silk-video | Classical poetry silk-painting videos | Poem → mp4 | Docker + gemini-flow-suite | MIT | ❌ Environment not ready, topic mismatch |
| simon-skills | Long investigative videos, whiteboard videos | Topic → 10+ minute video | Volcano Engine TTS (Chinese-mainland service) | MIT | ❌ Volcano TTS; whiteboard also needs codex CLI |
| director | Science-explainer director, three modes | Idea → storyboard / prompts | LibTV, Jimeng dreamina, Seedance (Chinese-mainland services, consume credits) | MIT | ⚠️ Usable only up to storyboard |
| book-sales-video | Book-selling short videos | Book title → edit draft | Doubao TTS, WeChat Reading, Feishu, OpenChatCut (macOS) | MIT | ❌ Chinese-mainland services |
| creator-buddy | 33 skills for WeChat Official Accounts / Xiaohongshu / video | Platform + keyword → analysis | Mostly Chinese-mainland platforms | MIT | ⚠️ A few video sub-skills are useful as reference |
| dbskill / tw-dbskill | Copywriting tools: topics, hooks, AI-tone checks, etc. | Text → text | dbs-video-extract needs a TikHub / Qingdou key | CC BY-NC 4.0 | ⚠️ Non-commercial; thinking reference only |
| native-subtitle-quote-image | Stitch subtitle screenshots into long images / 3:4 quote images | Video → image | No key | MIT | ✅ (auxiliary, not video) |
| Punk-Skill | Cover / avatar prompts | Article → prompts | Image generation | MIT (pinned v1.0.0-mit) | ✅ Backup covers |
| impeccable | Web UI design checks | Front end → suggestions | Downloads engine on first run | Apache 2.0 | — Not a video skill |
| video-pipeline | reel.sh: mixing, IG compression, QA | mp4 → IG version | ffmpeg | Self-written | ✅ Wrap-up for every video |
| _deps | WeChatReading, hyperframes dependencies | — | — | — | Not a skill |

## 2. Type → skill

| Type | Preferred | Fallback | Do not use |
|---|---|---|---|
| Celebrity interview / talk Reel | interview-reel | ffmpeg edit + xilo overlay | OpenMontage clip-factory (no commentary) |
| News explainer (voiceover + real footage) | stock-footage-reel | OpenMontage documentary-montage (when little narration) + om_clips.py for footage | anything2explainer |
| Vox / knowledge explainer animation | huashu-art-motion | xilo-opus-video | vox-director (paid), anything2explainer, talkcraft (license) |
| Footage documentary / montage | stock-footage-reel (with narration), OpenMontage documentary-montage (no narration) | Each is the other's fallback | — |
| Screen recording / tool walkthrough | screen-record (real web recording) | OpenMontage screen-demo | lemo living-screencast (simulated screens) |
| Art-style animation | huashu-art-motion | lemo-opuscar (special styles) | OpenMontage animation |
| Stickman / hand-drawn | huashu-art-motion whiteboard / hand-drawn grammar (renders video directly) | stickman-video-director, hand-drawn-video-prompts (prompts only; ask Josh separately about image generation) | — |
| Data cards / KPIs | huashu data_card_render.py | OpenMontage Remotion components | Static PNG |
| Product promo | video-shotcraft (re-laid out vertical) | xilo-opus-video | — |
| Long video into shorts, translated dubbing, podcast | OpenMontage (via openmontage-house) | — | — |
| Covers | covers/render.py | Punk-Skill | OpenMontage thumbnails |
| Wrap-up (mixing, compression, QA) | video-pipeline/reel.sh | — | — |

## 3. Duplicates: keep / retire

- **Two copies of lemo-opuscar**: recommend keeping `<YOUR_WORKSPACE>/tools/lemo-opuscar` (has .git, can be updated) and later turning the skills/ copy into a symlink. Needs Josh's approval before touching.
- **huashu-art-motion**: already a symlink in skills/; nothing to do.
- **dbskill and tw-dbskill** (plus josh-dbskill, dbskill-upstream): all CC BY-NC; recommend keeping only tw-dbskill as a reference and marking the others as not used.
- **anything2explainer, video-talkcraft**: covered by huashu / xilo, plus non-commercial licenses; recommend marking "reference only, no final videos".
- **vox-director**: replaced by huashu; mark "not used".
- Retiring only means marking it in the routing table; folders are not deleted.

## 4. Skills that cannot be used here

| Skill | Reason |
|---|---|
| book-sales-video | Doubao TTS, WeChat Reading, Feishu lark-cli, OpenChatCut (macOS): all Chinese-mainland services or environments we don't have |
| simon-skills (investigative, whiteboard) | Volcano Engine TTS key; whiteboard videos also need codex CLI |
| vox-director | Atlas Cloud paid API |
| director (video output part) | LibTV, Jimeng dreamina, and Seedance require login and consume credits, and are Chinese-mainland services; the storyboard part can be used as reference |
| hbg-classical-poem-silk-video | Needs Docker + gemini-flow-suite, and the topic doesn't fit |
| kid-papercraft | Children's birthday videos using cartoon IP, unrelated to the account |
| Most of creator-buddy | WeChat Official Account and Xiaohongshu search |
| dbskill dbs-video-extract | TikHub / Qingdou paid key |
| anything2explainer, video-talkcraft (final videos) | PolyForm Noncommercial, and the account earns revenue |

## 5. Rule conflicts (Josh to decide)

1. **Voiceover voice**: INDEX.md, stock-footage-reel, and interview-reel specify the English female voice Sarah Explains (Nhs7eitvQWFTQBsf0yiT) + Traditional Chinese subtitles; VIDEO-SKILLS.md and video-pipeline specify your own voice <YOUR_ELEVENLABS_VOICE_ID> for Chinese. Router draft for now: Chinese voiceover uses <YOUR_ELEVENLABS_VOICE_ID>, English voiceover uses Sarah Explains. **Resolved 2026-10-20:** English voiceover uses Josh's own voice Josh - Calm, Warm Taiwanese narrator (`xBHPgy3hJ2fclZQIoDnv`), eleven_multilingual_v2.
2. **BGM**: VIDEO-SKILLS.md still says "every video must have BGM and a music credit", which conflicts with the 10/19 new rule (credit music when used; not a hard requirement); needs updating.
3. **OpenMontage is AGPLv3**: making videos locally is fine; revisit if it ever becomes a public-facing service.

---

## 6. josh-video-router SKILL.md draft

```markdown
---
name: josh-video-router
description: Main entry point for Josh's (@bounce12340) videos. When asked to 「做一支影片／Reel」 (make a video / Reel), use this skill first to decide the type, hand off to the matching video skill, and apply the shared house rules and review handoff. Drafts only, never posts.
---

# josh-video-router: Josh's video router

**Drafts only, never posts.** Posting is always handled by the main bot after Josh confirms.

## Step 0: Read the house rules first
- Voice and wording: `<YOUR_WORKSPACE>/media-team/00-profile/voice.md`
- Motion rules: `<YOUR_WORKSPACE>/media-team/00-profile/motion-contract.md`
- Covers: `<YOUR_WORKSPACE>/media-team/covers/README.md`

## Step 1: Decide the type (decision table)

| Question | Yes → use |
|---|---|
| Is there original footage of a famous person's interview or talk? | interview-reel |
| Voiceover + real news / stock footage? | stock-footage-reel |
| Themed montage with no narration? | OpenMontage documentary-montage (read openmontage-house) |
| Need to record a web page or tool being used? | screen-record (footage) → then stock-footage-reel or OpenMontage screen-demo |
| Knowledge explainer, Vox style, art style, whiteboard, hand-drawn? | huashu-art-motion; use lemo-opuscar only for styles huashu lacks; use xilo-opus-video for a three-option preview |
| Price, benchmark, or KPI comparison? | huashu templates/data_card_render.py |
| Product promo? | video-shotcraft (must be re-laid out as vertical) |
| Long video into shorts, translated dubbing, podcast? | OpenMontage (read openmontage-house) |
| None of the above? | Stop and ask the main bot; do not pick a skill yourself |

Do not use: vox-director, book-sales-video, simon-skills, director for final output, hbg-classical-poem, kid-papercraft, or anything2explainer and video-talkcraft for final videos (reasons in ROUTER-PLAN.md).

## Step 2: Shared house rules (every video must meet them)
- Traditional Chinese with Taiwan wording; use 「」 quotes; no em-dashes (—).
- Voiceover: Chinese uses your own ElevenLabs voice `<YOUR_ELEVENLABS_VOICE_ID>`; English uses Josh's own English voice **Josh - Calm, Warm Taiwanese narrator** (voice_id `xBHPgy3hJ2fclZQIoDnv`, set as `ELEVENLABS_VOICE_ID_EN`), model eleven_multilingual_v2, about 1,800 characters of credit per video, `generations_count: 1`. Natural pace, no speed-up. Check credits with estimate_only first.
- The voiceover reads the subtitles exactly: the final subtitle file is the single source, and on-screen subtitles are chunked from that same file.
- BGM: include it whenever possible; if used, note the track name, source, and license in facts.md; lacking it does not block the video.
- No brand logos on screen.
- Vertical 1080x1920, under 3 minutes; compress the IG version under 45 MB with `video-pipeline/reel.sh ig`.
- Do not turn on paid services or add new API keys; stop and ask Josh when needed.
- VoiceStudio rules: do not upload the user's recordings; do not clone a voice without the person's consent.
- Do not use Chinese-mainland services (Doubao 豆包, Volcano Engine 火山, Feishu 飛書, WeChat Reading 微信讀書, Jimeng 即夢, LibTV).

## Step 3: Wrap-up
1. `reel.sh mix` (when there is BGM) → `reel.sh qa` → `reel.sh ig`
2. Deliver script.txt, storyboard.md, ig_caption.txt, threads.txt, facts.md, x_post.txt, x_longpost.md to `<YOUR_WORKSPACE>/media-team/03-drafts/<題目>/`
3. X drafts: `x_post.txt` (single post) and `x_longpost.md` (long post) go to X Launch Traction; Josh approves; then Grok Boss posts. Keep external links out of the post body and put them in a reply instead (per X API Engineer, a post with a link costs $0.20 vs $0.015 without). On X, the original-video link and credit required in Step 2 go in that reply.

## Step 4: Hand off to the fact editor
- Notify the fact editor (事實編輯) to review `03-drafts/<題目>/`; the report goes in `04-review/<稿名>-review.md`.
- Once it passes, report to the main bot: file path, duration, file size, the full script, and any facts that could not be verified.
```
