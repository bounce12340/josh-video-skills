# Agent playbook

How every agent on Josh's team runs the video skills in this repo: what to check first, when to stop and ask, what things cost, how to handle failures, and what "done" means. Skill-specific steps stay in each SKILL.md; the topic and style matrix is in [INDEX.md](INDEX.md#skill-matrix-topics-and-agents).

Team docs referenced here live outside this repo, in `<YOUR_WORKSPACE>/media-team/00-profile/` (`voice.md`, `voiceover-process.md`, `publish-queue.md`).

## 1. Preflight checklist

Stop before starting if any required item is missing, and report what is missing. Don't start and improvise.

| Skill | Required inputs | Check before running |
|---|---|---|
| josh-video-router | Topic, source URL(s), the target skill exists | `josh-video-router/scripts/check_skill.sh <skill> [path]` |
| interview-reel | Official public video URL + channel name, in/out times, spec.json | OpenMontage venv (`om-env.sh`), yt-dlp, ffmpeg, `ELEVENLABS_API_KEY`, `PEXELS_API_KEY`, `BRAND_NAME`/`BRAND_HANDLE`/`COVERS_DIR`/`SFR_USER_AGENT` (`build.py --check`) |
| stock-footage-reel | Source article/post URL, script.txt (approved), footage license per clip | `PEXELS_API_KEY`, `uv` + faster-whisper, ffmpeg, fonts in `COVERS_DIR`, `build.py --check` |
| screen-record | Public http(s) URL, spec.json | `node_modules/` installed (`npm install`), Chromium for Playwright |
| openmontage-house | Source media (and confirmed right to use it) or topic, house rules | `source OpenMontage/om-env.sh`, registry support envelope; no paid keys (none set) |
| x-scout | topics.json | `X_BEARER_TOKEN` env var (or `--input` file) |
| analytics/style_compare.py | X analytics CSV export, `analytics/style_tags.csv` rows | Column names (`--id-col`, `--metrics`) |

All skills: the source must be traceable (URL + author + date in facts.md / credits), and secrets come from environment variables only.

## 2. Human gates (stop and ask Josh)

- **Before recording the full voiceover**: Josh reviews the script (and storyboard) first. Recording 1 to 2 lines as a test is allowed.
- **Before spending credits** beyond what was approved (re-recording, extra generations, paid generation of any kind).
- **Before any post** on any platform. Agents only draft; Grok Boss posts after Josh approves.
- **When footage or voice licensing is unclear** (e.g. Mixkit Restricted, Archive.org items without a license, unofficial interview uploads).
- **When a style is new**: make a 10-second sample for Josh before full production.

Approval requests use three lines:

```
動作 (action): what you will do
對象 (target): which file / platform / account
理由 (reason): why, incl. source, cost, and risk
```

## 3. Cost awareness

Use only these documented figures. Anything else counts as **unknown**: say "cost unknown" and ask, and don't estimate.

| Item | Documented cost | Source |
|---|---|---|
| ElevenLabs English voiceover (Josh - Calm, Warm Taiwanese narrator, `xBHPgy3hJ2fclZQIoDnv`) | About 1,800 characters of credit per video, `generations_count: 1` (sun-reel English: 1,884 actual) | team `voice.md`, `voiceover-process.md` |
| ElevenLabs `creative_generate_speech` | Default `generations_count` is 4 = 4x credits; always set 1. Resending the same request charges again | stock-footage-reel SKILL.md |
| X post with an external link | $0.20 vs $0.015 without a link | X API Engineer (router Step 3) |
| Pexels, Wikimedia, Prelinger, Playwright, OpenMontage local tools | Free | licenses.md, SKILL.md files |
| Paid generation (Kling, Veo, Seedance, FLUX, Atlas Cloud…) | Unknown / no keys set; requires Josh | openmontage-house SKILL.md |

Check ElevenLabs credits with `estimate_only` (router) or `tts.py --dry-run` (interview-reel) before generating.

## 4. Failure handling

| Failure | Action | How |
|---|---|---|
| Download fails (yt-dlp, archive.org, NASA timeout) | Retry, then fall back | Retry a few times (fetch scripts retry 3x); NASA → another source; YouTube `--download-sections` 403 → whole-video download (already built in). Never add cookies or a login |
| Footage not found for a line | Fall back | Change to concrete keywords; `pick` a file / image / screen-record clip; `om_clips.py` sources; synth fallback last |
| Voiceover length doesn't match subtitles | Report or re-record (with approval) | Text sent to TTS must equal the subtitle file word for word; check with ASR (align.py / faster-whisper). Fix the text, never speed up the audio; a re-record needs Josh if it costs extra credits |
| File over 45 MB | Retry | build.py re-encodes at lower bitrate automatically; else `video-pipeline/reel.sh ig`; confirm with `ffprobe` |
| Missing skill or script | Fall back or report | `check_skill.sh` fails → stock-footage-reel if the topic fits; otherwise stop and ask the main bot. Don't install third-party skills on your own |
| Placeholder settings | Report | `build.py --check` error lists the env vars to set |

## 5. Definition of done (self-check before handoff)

- **Files** in `<YOUR_WORKSPACE>/media-team/03-drafts/<題目>/`: final mp4 (IG version ≤ 45 MB), script.txt, storyboard.md, facts.md, credits, ig_caption.txt, threads.txt, x_post.txt, x_longpost.md, covers, viral score, handoff note. English videos keep their copy in `en/`.
- **Voiceover matches subtitles word for word**: the final subtitle file is the single source.
- **No brand logos** on screen or cover.
- **Footage matches the line's real context** (no generic stock that contradicts the meaning).
- **BGM present**: credit it in the caption when needed. A missing music credit doesn't block the video.
- **AI-voiceover label on TikTok and YouTube only**, not on IG, Threads, X, or LinkedIn.
- **Viral score ≥ 10/14** (7 questions, 0 to 2 each).
- Then hand off to **事實編輯 (Fact Editor)**, who writes `04-review/<稿名>-review.md`. Only a pass makes the video publishable.

## 6. Handoff packet

Send these to 事實編輯 (Fact Editor) and then to Grok Boss:

1. Draft path (`03-drafts/<題目>/`) and final file name, duration, size.
2. Viral score (x/14), naming which of the 7 points it hits and which it misses (e.g. P1 takeaway, P2 real numbers, P6 search term, P8 different template).
3. Source list: URLs, authors, dates; footage and music licenses.
4. Recommended style plus a one-line reason (the [recommended-style rule](INDEX.md#topic-proposals-recommended-style-rule)).
5. Open questions: unverifiable facts, lines to audition, anything Josh must decide.

## 7. Never do

- Never use cookies or bypass a login with yt-dlp.
- Never clone a voice without the person's consent.
- Never upload Josh's voice to a new cloud service.
- Never use paid services without asking Josh.
- Never put a personal opinion in news videos.
- Never use the F1 / brakes analogy unless Josh asks.
- Never force an AI-governance framing onto a topic.
- Never fabricate numbers or quotes.
- Never send or reply to email or messages on Josh's behalf.
- Never print secrets (API keys, tokens).

## 8. Worked example: Dan Koe hand-drawn, English

Draft: `03-drafts/2026-10-21-dankoe-handdrawn/`. Each stage below uses only facts in that folder, its 04-review files, and publish-queue.md.

1. **Input**: Dan Koe's X Article "The influencer is dead. The Age of Experience is here." (2026-10-20 UTC), archived in `01-intel/`, and summarized in `summary.md`. It is a summary video with no opinion from Josh.
2. **Route and style**: hand-drawn whiteboard explainer, rendered with the huashu-art-motion `y3_whiteboard` grammar as 16 whiteboard segments with hard cuts (`handoff.md`).
3. **Script**: `script.txt` and `en/script.txt`. Josh's decisions: drop the line about the author's app, keep the shortened "ultimate moat" quote, keep the closing question.
4. **Voiceover**: Josh's English voice, eleven_multilingual_v2, speed 1.0. 19 lines were recorded once each (2,399 characters). Line 17 was re-recorded with approval (217), for 2,616 in total (`credits.txt`, `en/tts_log.json`).
5. **Music and mix**: an original synth score (`work/music.py`), 20 dB under the voice, mixed to -14.5 LUFS. The music check passed (`04-review/…-music.md`).
6. **Self-check**: ASR match 0.989, with lines 1 and 8 flagged for audition. `frames3s.jpg` contact sheet. No faces, logos, or third-party footage. 2:26.6, 8.7 MB.
7. **Viral score**: 11/14 self-scored (10/14 if Q6 is downgraded). It hits P1, P6, and P8 and misses P2 (no real numbers from Josh) (`en/viral_score.md`).
8. **Copy**: `en/ig_caption.txt`, `threads/1–4`, `x.txt`, `x_article.md`, `youtube_shorts.txt`, `tiktok.txt` plus the first comment, and `linkedin.txt`. The AI-voiceover label is only in TikTok and YouTube.
9. **Review**: 事實編輯 (Fact Editor) found it publishable on 10/21 09:03 (`04-review/2026-10-21-dankoe-handdrawn-review.md`). Josh knowingly accepted the risks on lines 1, 5, and 11. Josh auditioned lines 1 and 8 and approved them on 10/21 09:15.
10. **Cover**: `covers/cover_2_reel.jpg` / `cover_2_post.jpg`, 「Dan Koe：網紅時代過去了」, no EP number.
11. **Scheduled**: 2026-10-31 (Sat) 19:19 Taipei in `publish-queue.md`, with nothing pending from Josh.

## 9. Combining skills

| Topic | Chain | How |
|---|---|---|
| Interview + data (a founder quotes figures) | interview-reel + data card | Build the interview-reel spec. For the numbers, render a huashu `data_card_render.py` clip if `check_skill.sh` finds it, and add it as a line `"file"`. Otherwise use an explainer card with `cite` |
| News + tool demo | screen-record → stock-footage-reel | Record the public page with screen-record, then add it to shots.json via `pick: {"source":"file",...}`, and credit "Screen recording of <site>" |
| News + archival history | stock-footage-reel + om_clips.py | Fetch NASA / LOC / NARA / Archive.org footage with `om_clips.py`, then verify each license before using it with `pick` file |
| Long interview → several shorts with commentary | OpenMontage clip-factory → interview-reel | Use clip-factory to find segments, then build each short as an interview-reel spec (commentary required, original audio under 50%) |

Run the shared house rules and this playbook's gates once for the combined video, not separately per skill.
