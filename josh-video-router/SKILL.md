---
name: josh-video-router
description: "Use first when asked to 「做一支影片／Reel」 (make a video / Reel): decide the video type, hand off to the matching video skill, apply the shared house rules, and pass to the fact editor (事實編輯). Drafts only, never posts."
---
# josh-video-router: Josh's video router

**Drafts only, never posts.** Posting is always handled by the main bot after Josh confirms. For the full inventory and reasoning, see `<SKILLS_DIR>/ROUTER-PLAN.md`.

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
- Voiceover: Chinese uses your own ElevenLabs voice `<YOUR_ELEVENLABS_VOICE_ID>`; English uses Sarah Explains. Natural pace, no speed-up. Check credits with estimate_only first.
- The voiceover reads the subtitles exactly: the final subtitle file is the single source, and on-screen subtitles are chunked from that same file.
- News videos report only the news, with no first-person opinion from Josh unless he asks for it.
- BGM: include it whenever possible; if used, note the track name, source, and license in facts.md; lacking it does not block the video.
- No brand logos on screen; footage must match the real context of the line it covers.
- Vertical 1080x1920, under 3 minutes; compress the IG version under 45 MB with `video-pipeline/reel.sh ig`.
- For videos based on a YouTube video, every post links the original video and credits the original creator.
- Do not turn on paid services or add new API keys; stop and ask Josh when needed.
- VoiceStudio rules: do not upload the user's recordings; do not clone a voice without the person's consent.
- Do not use Chinese-mainland services (Doubao 豆包, Volcano Engine 火山, Feishu 飛書, WeChat Reading 微信讀書, Jimeng 即夢, LibTV).

## Step 3: Wrap-up
1. `reel.sh mix` (when there is BGM) → `reel.sh qa` → `reel.sh ig`
2. Deliver script.txt, storyboard.md, ig_caption.txt, threads.txt, facts.md to `<YOUR_WORKSPACE>/media-team/03-drafts/<題目>/`

## Step 4: Hand off to the fact editor
- Notify the fact editor (事實編輯) to review `03-drafts/<題目>/`; the report goes in `04-review/<稿名>-review.md`.
- Once it passes, report to the main bot: file path, duration, file size, the full script, and any facts that could not be verified.
