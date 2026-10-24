---
name: openmontage-house
description: "House-rules adapter layer for making Josh's videos with OpenMontage (an open-source AI video production pipeline, <SKILLS_DIR>/OpenMontage). Use for: cutting long videos into multiple shorts (clip-factory), real screen-recording tutorials (screen-demo), translated dubbing (localization-dub), podcast to video (podcast-repurpose), \"make it like this reference video\" (reference video analysis), narration-free documentary montage (documentary-montage), and fetching extra archival footage from NASA / Library of Congress / NARA / Archive.org for stock-footage-reel. Triggers: 「用 OpenMontage」 (use OpenMontage), 「長片切短片」 (cut long video into shorts), 「照這支 Reel 做」 (make it like this Reel), 「翻譯配音」 (translated dubbing), 「螢幕教學影片」 (screen tutorial video)."
---

# openmontage-house: OpenMontage + Josh's house rules

OpenMontage itself: `<SKILLS_DIR>/OpenMontage` (commit 9327439, 2026-10-03, AGPLv3).
Its full documentation: `AGENT_GUIDE.md`, `CLAUDE.md`, `skills/INDEX.md`, `pipeline_defs/*.yaml`.
**This skill produces drafts only, never posts.** Posting is always handled by the main bot after Josh confirms.

## First decide whether to use OpenMontage (see the decision table in <SKILLS_DIR>/INDEX.md)
- Bilingual Reels with voiceover, real-footage edits → use **stock-footage-reel** (the house format), not OpenMontage's documentary-montage. When you need more archival / public-domain footage, fetch it with `om_clips.py` below, then put it in shots.json with `pick: {"source":"file", ...}`.
- Vox / knowledge explainer animation → use **huashu-art-motion**, not OpenMontage's animated-explainer.
- Everything else (clipping, screen recording, translated dubbing, podcasts, reference video analysis, narration-free montage) → use OpenMontage, overriding its defaults with the house rules below.

## Environment
```
source <SKILLS_DIR>/OpenMontage/om-env.sh   # 啟用 .venv 和 Node 22，並 cd 進 OpenMontage
python -c "from tools.tool_registry import registry; import json; registry.discover(); print(json.dumps(registry.support_envelope(), indent=2))"   # 看哪些工具可用
```
- Installed: requirements.txt, Remotion composer (npm), piper-tts, faster-whisper, yt-dlp, youtube-transcript-api, opencv-headless, HyperFrames (npx cache 0.8.147), plus CPU torch 2.14.1 + transformers 5.19 (no GPU packages). **CLIP semantic matching works**: after corpus_builder builds an asset library, clip_search's `rank_for_slot` ranks assets by text description (a score of 0.25 or above counts as usable); video_understand (CLIP mode) also works. The first run downloads the CLIP model (openai/clip-vit-base-patch32) from Hugging Face; on CPU, building a small 5-clip library takes about 1 minute. corpus_builder showing degraded only means half the asset sources lack keys; it does not affect use.
- Keys: `PEXELS_API_KEY` and `ELEVENLABS_API_KEY` are machine environment variables (only present in new shells; use `bash -lc` if needed), and om-env.sh inherits them. They are deliberately left out of .env. **Do not print them or write them to files.** All other keys are empty. **Do not sign up for new accounts or paid keys for OpenMontage**; ask Josh before adding any.
- Paid generation (Kling, Veo, Seedance, FLUX, etc.) currently has no keys, and the selector skips it automatically. OpenMontage quotes a price before spending money and needs Josh's approval.

## House rules (override OpenMontage defaults; every video must meet them)
1. Frame: vertical 1080x1920 (most OpenMontage defaults are 16:9, so specify 9:16 at the start). Under 3 minutes; completeness over brevity.
2. Voiceover: Josh's own English voice **Josh - Calm, Warm Taiwanese narrator** (voice_id `xBHPgy3hJ2fclZQIoDnv`, set as `ELEVENLABS_VOICE_ID_EN`), model `eleven_multilingual_v2`, about 1,800 characters of credit per video.
   - First choice: generate directly with OpenMontage's own `elevenlabs_tts` tool (tested and working). Specify `voice_id`; do not let tts_selector pick a voice automatically or fall back to piper. Example: `ElevenLabsTTS().execute({"text":..., "voice_id":"xBHPgy3hJ2fclZQIoDnv", "model_id":"eleven_multilingual_v2", "output_path":".../vo.mp3"})`. Send each script once; do not resend (it charges credits again).
   - Fallback: if the direct API fails, generate vo.mp3 with the user-Elevenlabs connector (`creative_generate_speech`, `generations_count: 1`), then hand it to OpenMontage as ready-made narration. Do not use piper for final voiceover.
3. Subtitles: Traditional Chinese main subtitles + one smaller English line below (the English matches the voiceover). Taiwan wording, 「」 quotes, no em-dashes. The subtitle bottom edge stays no lower than y=1490 to avoid the IG interface.
4. Cover: B clipping-style Vox layout, `covers/render.py` (`COVERS_DIR`; 3 to 6 options, see covers/README.md) (do not use OpenMontage's own covers / thumbnails).
5. Licensing: record every asset in `credits.json` (URL, author, license). Archive.org licensing is "verify per item": always open each item's page to confirm it is public domain or CC0 / CC BY; do not use footage from the BBC, TV stations, or film studios. CC BY requires credit in the post caption.
6. Files: IG final H.264 / AAC, compressed under 45 MB (confirm size and duration with `ffprobe`).
7. Content: faithful to the source, no fabricated numbers or quotes, credit the original creator.
8. Output: finished files go in `<YOUR_WORKSPACE>/media-team/03-drafts/<題目>/`; OpenMontage's `projects/` is only a workspace.

## How to start each pipeline
Open Claude Code in the OpenMontage folder (it reads CLAUDE.md), or have other bots read `skills/pipelines/<流程>/executive-producer.md` directly and follow its stages. Paste the house rules above as the very first message.
- clip-factory: cut long videos (YouTube, livestreams, podcast recordings) into multiple vertical shorts. Before downloading with yt-dlp, confirm Josh has the right to use the video.
- screen-demo: real screen-recording tutorials (screen_recorder / cap_recorder available).
- localization-dub: dub a video into another language. Generate the voiceover with the ElevenLabs connector first, then hand it over for timing and mixing.
- podcast-repurpose: turn podcast audio into highlight shorts.
- Reference video analysis: paste a Reel / Short and let it analyze pacing, opening, and structure, then propose 2 to 3 original versions with cost estimates (animated-explainer, animation, cinematic, and character-animation have reference_input). Learn the structure only; do not copy visuals or copy.
- documentary-montage: themed montage with no or little narration (Adam Curtis style), using CLIP semantic matching to pick footage for each segment automatically. Reels with voiceover still use stock-footage-reel.
- Backlot storyboard board: `python -m backlot open <project-id>` (a local board for observation only; failure does not affect production). It is only for checking progress and gates; Josh's confirmation still happens back in chat.

## Fetching extra footage for stock-footage-reel
```
python3 <SKILLS_DIR>/openmontage-house/scripts/om_clips.py \
  --query "1960s computer room" --query "mission control" \
  --sources archive_org,nasa,loc,nara,wikimedia --n 3 --out $D/work/om_clips
```
It prints each clip's thumbnail path and a `pick` (`{"source":"file",...}`) you can paste straight into shots.json; license records are written to `om_clips/om_credits.json`. Look at the thumbnails with Read to choose, and confirm each license before putting a clip in the video.
Available sources: pexels (has key), archive_org, wikimedia, nasa, nara, loc, coverr, pond5_pd. NASA downloads sometimes time out (images-assets.nasa.gov); failures print `note:`, so just switch sources.

## License (AGPLv3)
Using OpenMontage as a tool to make videos, including for commercial posts, is fine, and the output videos are not bound by the AGPL. Only "modifying its code and running it as a network service for others" requires releasing source code. So do not run a modified OpenMontage as a public-facing service.

## Best fit and agent usage

**Best fit:** long video or podcast into shorts, translated dubbing, screen tutorials, reference-Reel analysis, narration-free montage, extra archival footage. **Not for:** narrated real-footage Reels, explainer animation, interview commentary, or paid generation.

- **Grok Boss**: routes long-to-short, dubbing, podcast, and montage requests here.
- **內容製作 (Content Producer)**: starts the pipeline with the house rules pasted first and delivers to 03-drafts.
- **事實編輯 (Fact Editor)**: verifies each Archive.org item's license and the rights to downloaded videos.
- **情報偵察員 (Scout)**: proposes it when a topic starts from a long video, podcast, or reference Reel.
- **數據復盤師 (Analytics)**: tags which OpenMontage pipeline was used.
- **Coding agent (Claude Code / Cursor)**: `source OpenMontage/om-env.sh`; input: source media + house rules; output: 9:16 mp4 under 45 MB; `om_clips.py` prints `pick` entries.

Agent workflow (preflight, human gates, costs, failures, done, handoff): see [AGENT-PLAYBOOK.md](../AGENT-PLAYBOOK.md).
