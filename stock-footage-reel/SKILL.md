---
name: stock-footage-reel
description: "Vertical 「真實素材剪輯」 (real-footage edit) short video in the documentary style of AYi @ayi_ainotes: for each line of the voiceover script, automatically search and download free, commercially usable footage (Pexels, Mixkit Free, Wikimedia Commons), plus magenta-tinted 1950s to 70s Prelinger public-domain archival film; hard-cut editing, burned-in bilingual subtitles (Traditional Chinese + English, key words gold), a fixed title at top left, ElevenLabs voiceover, dark synth music, an end quote card with small source text, then a cover from the B clipping-style Vox template. Triggers: 「做一支真實素材剪輯」, \"stock footage reel\", 「AYi 風格」, 「素材庫剪輯」."
---

# stock-footage-reel: real-footage edit Reels

> **2026-10-11 merge note:** for real-footage Reels with voiceover, this skill is still the first choice (canonical). OpenMontage's documentary-montage is only for montages with no or little narration; see the decision table in `<SKILLS_DIR>/INDEX.md` for the split.
> - For more footage sources (NASA, Library of Congress LOC, NARA, Archive.org, Wikimedia): use `python3 <SKILLS_DIR>/openmontage-house/scripts/om_clips.py --query "..." --out $D/work/om_clips`; it prints a `pick: {"source":"file",...}` you can paste straight into shots.json. Confirm each license before adding it to credits.json.
> - Current voiceover settings: Chinese uses your own ElevenLabs voice **「<YOUR_VOICE_NAME>」** (`<YOUR_ELEVENLABS_VOICE_ID>`); English uses **Sarah Explains** (`Nhs7eitvQWFTQBsf0yiT`). Traditional Chinese main subtitles + small English line. For how English voiceover is done, see EP.07: `<YOUR_WORKSPACE>/media-team/03-drafts/grokbot-team-reel/` (script_en.txt; work/shots.json uses `subs_zh` + `en`; timing and editing use mktiming.py and build_custom.py in work/). Step 2 below picks the voice by language.

For the content team of Josh (IG / Threads @bounce12340; AI startups, AI agents, one-person companies; Taiwan). Following this workflow, both Claude Code and the content-production bot can produce videos directly. **This skill produces drafts only, never posts.** Posting always goes to the main bot and happens only after Josh confirms.

Scripts are in `<SKILLS_DIR>/stock-footage-reel/scripts/` (called `$S` below). Examples are in `examples/`; license research is in `references/licenses.md`.
Reference output: `<YOUR_WORKSPACE>/media-team/03-drafts/stock-footage-test/test.mp4`.

## Content rules (must follow)
- Faithful to the source: every line must trace back to the original source. Never invent numbers or quotes; do not present what the source didn't say as if it did. When paraphrasing, write 「整理自」 (compiled from).
- Credit the original author: the top-left title names the source author and original title; credit them in the end card and the post caption too.
- Completeness over brevity: cover the key points fully; don't cut key arguments just to be short. But the whole video must be under 3 minutes.
- Natural voiceover pace; don't speed up to cram. If there is too much text, split into two videos or drop minor lines.
- Traditional Chinese, Taiwan wording (軟體、資料、影片、網路、品質…), 「」 quotes, no em-dashes (——); use commas or periods.
- English subtitles are our translation, not quotes from the source; don't put them in quotation marks unless the source is in English and identical word for word.
- Use only footage with a clear, commercially usable license; see `references/licenses.md`. Don't log in to any site, use paid sources, or bypass site restrictions.

## Environment
- Pexels: `PEXELS_API_KEY` is set as an environment variable (**do not print it**). Pixabay needs `PIXABAY_API_KEY` (not available yet).
- ASR timing: `uv run --with faster-whisper` (downloads packages on first run, cached afterward).
- Fonts: Noto Sans TC / Noto Serif TC in `<YOUR_WORKSPACE>/media-team/00-profile/covers/fonts/`. English uses Noto Sans.
- Footage cache: `$S/../stock-footage-reel/cache/` (the same clip is never re-downloaded).

## Workflow

### 0. Create a working folder
```
D=<YOUR_WORKSPACE>/media-team/03-drafts/<題目>-reel ; mkdir -p $D/work ; cd $D/work
```

### 1. Write script.txt (one line = one shot)
One voiceover sentence per line; the `[1] 文字` format is allowed. Each line works best with 1 to 3 clauses, about 5 to 9 seconds.

### 2. Voiceover (ElevenLabs via MCP; scripts cannot call MCP directly)
1. Pick the voice by language: Chinese uses **「<YOUR_VOICE_NAME>」**, voice_id `<YOUR_ELEVENLABS_VOICE_ID>`; English uses **Sarah Explains**, voice_id `Nhs7eitvQWFTQBsf0yiT`. Check the name with `user-Elevenlabs`'s `creative_list_voices` before sending; don't swap ids from memory.
2. `creative_generate_speech`: `voice_id`, `model_id: "eleven_multilingual_v2"`, `generations_count: 1` (the default is 4, which costs 4x credits), `prompt` holds the whole script (a blank line between lines for natural pauses; no `[1]` numbers). Don't resend the same request; it charges credits again.
3. Poll `creative_get_flow_run_status` (flow_id, session_ids) until `all_completed`, take `media[0].url`, then `curl -o vo.mp3 '<url>'` (the URL is valid for 2 hours).
4. The text sent must match script.txt exactly (timing depends on it).
Fallback: when ElevenLabs is unavailable, `bash $S/scripts/tts_edge.sh script.txt vo.mp3` (edge-tts zh-TW-HsiaoChenNeural), and change shots.json's `voice.provider` to `"Edge TTS (zh-TW-HsiaoChenNeural)"` so the end credit is labeled correctly.

### 3. Timing
```
uv run -q --with faster-whisper --with numpy python $S/scripts/align.py --audio vo.mp3 --script script.txt --out timing.json
```
It prints each shot's start/end and the alignment rate (80% or higher is normal). Shot cuts are placed automatically in the middle of pauses between sentences.

### 4. Write shots.json (example: `examples/satya_test.shots.json`; the `//` comments below are explanations only and must not appear in the real file)
```json
{
  "format": "1080x1920",                      // 或 "1080x1350"
  "title_zh": "微軟執行長 Satya Nadella 長文",   // 左上固定標題（來源）
  "title_en": "Satya Nadella · \"Models as Insider Risks in the Super Intelligence Era\"",
  "max_cut": 4.5,                              // 一鏡超過幾秒就在同一支素材裡多切一段
  "voice": {"provider": "ElevenLabs", "voice": "<YOUR_VOICE_NAME> (<YOUR_ELEVENLABS_VOICE_ID>)", "model": "eleven_multilingual_v2"},  // 中文；英文片改 Sarah Explains (Nhs7eitvQWFTQBsf0yiT)
  "music": "synth",                            // "synth"＝自己合成的暗色配樂；或音檔路徑；或 "none"
  "music_db": -17,
  "shots": [
    {"keywords": ["server room", "data center"], "highlight": ["內部風險"],
     "en": ["Microsoft CEO Satya Nadella, in a new long essay,", "argues AI models should be managed as an internal risk."]},
    {"keywords": ["computer operators"], "archival": true, "highlight": ["控制權分開"], "en": ["..."],
     "pick": {"source": "archive", "id": "OnGuard1956", "starts": [630, 300]}}
  ],
  "end_card": {"zh": ["最值得信任的系統，", "[[是最不需要信任模型的那一個。]]"], "en": "...", "by": "── 整理自 Satya Nadella〈...〉", "dur": 4.0, "bg_shot": 2},
  "cover": {"ep": "EP.05", "kicker": "Satya Nadella 長文", "title": "把 AI 當成\n[[內部風險]]來管", "subtitle": "...", "clip_credit": "畫面：...", "frame_shot": 3}
}
```
Key fields:
- `keywords`: English search terms, tried in order. Write concrete visuals ("security camera", "typing keyboard close up", "server rack lights"), not abstract concepts.
- `archival: true`: this shot uses Prelinger archival film, with magenta tint and grain applied automatically. AYi's approach is to use archival film when talking about "history, the past, tradition, the 1970s" or metaphors like "control, permissions, surveillance", and modern footage otherwise. Put at least one or two archival shots in each video for the style to come through.
- `highlight`: words in this shot to turn gold (must match the subtitle text exactly). You can also mark gold with `[[ ]]` in `end_card.zh`.
- `en`: list of English subtitles; the count must equal this shot's number of subtitle chunks. Run `build.py --plan` first to see the automatic chunks, then write English to match. If the count is wrong, the whole English sentence shows on every chunk.
- `pick`: specify footage manually. `{"source":"archive","id":"<identifier>","starts":[秒,...]}`, `{"source":"mixkit","id":"23215"}`, `{"source":"commons","title":"File:xxx.webm","start":12}`, `{"source":"file","path":"/abs.mp4","license":"...","author":"..."}`, `{"source":"synth","kind":"code|terminal|grid"}`.
- Others: `grade` ("archival" / "modern" / "none"), `focus_x` (0 to 1, horizontal center of the vertical crop), `cuts` (fixed number of cuts for this shot).
- `cover.frame_shot`: which shot's footage the cover clipping uses (original landscape frame), defaulting to the first archival shot. `ep` continues Josh's episode numbering.

### 5. Fetch footage
```
python3 $S/scripts/fetch_footage.py --shots shots.json --work . --timing timing.json
```
- Regular shot order: Pexels (with key) → Pixabay (with key) → Mixkit (Free License only) → Wikimedia Commons (PD / CC0 / CC BY) → local synth fallback.
- Archival shots: Internet Archive Prelinger (only items tagged public domain in metadata) → Commons.
- Results go into `footage.json` and `credits.json` (each clip's URL, author, license). Lines starting with `note:` are skipped clips and why.
- Picking archival segments: auto-picking avoids title cards and repeated segments, but it's best to look yourself:
  `python3 $S/scripts/fetch_footage.py --sheet archive:OnGuard1956 --work .` → produces `sheet_*.jpg` (one frame every 15 seconds, seconds at top left); view it with Read, pick the seconds, write them into `pick.starts`, then re-fetch that shot with `--only <鏡號> --refresh`.
- Useful Prelinger computer footage: `OnGuard1956` (IBM SAGE air-defense computer, 1956: console 120s, operators 240s/300s, switches 330s/600s, "RESTRICTED AREA" door 630s, control room 660s). Other searches: `computer`, `automation`, `electronic`.
- Swapping footage: edit shots.json, then `--only N --refresh`.

### 6. Edit
```
python3 $S/scripts/build.py --shots shots.json --work . --out .. --name reel --plan   # 先看字幕段落
python3 $S/scripts/build.py --shots shots.json --work . --out .. --name reel
```
Output (in `--out`): `reel.mp4` (H.264 / AAC, 30fps, automatically re-encoded at a lower bitrate if over 45 MB), `contact_sheet.jpg` (one middle frame per chunk + end card), `credits.json` (with `credit_line` and `caption_credits` for the post), `cover_reel.png`, `cover_post.png` (B clipping-style Vox template, via `<YOUR_WORKSPACE>/media-team/00-profile/covers/render.py`).

Visual spec (matched to AYi's original videos):
- Hard cuts, 2 to 4.5 seconds each, slow horizontal pan. Archival: magenta cast, soft focus, grain, vignette. Modern: darkened, teal-blue cast, desaturated, vignette.
- Fixed top-left title: brand mark 「●○○○ Josh｜AI 一人公司」 + the source's Chinese title + the original English title.
- Subtitles: left-aligned, up to two lines of Chinese (Noto Sans TC Bold), one smaller English line below; key words gold #E9A44A. In the vertical version the subtitle bottom edge is at y=1490, avoiding IG's caption text at the bottom and buttons on the right.
- End card: darkened, blurred footage; large serif quote (second line gold), English, 「── 整理自 …」, brand mark, @bounce12340, and one line of small source text at the bottom (e.g. "Archival: Prelinger Archives (Public Domain) • Footage: Pexels • Voice: ElevenLabs").
- Audio: voiceover + music with sidechain compression (music ducks automatically under speech), 2.5-second fade-out at the end, overall loudness about -14 to -16 LUFS.

### 7. Self-check before delivery
1. View `contact_sheet.jpg` with Read: does each frame fit its line, are subtitles broken in odd places (e.g. in the middle of a name), and is anything at risk of being covered by the IG interface?
2. Footage must not contain: close-ups of others' trademarks, identifiable faces in a negative context, visuals contradicting the meaning, or watermarks.
3. Every clip in `credits.json` has a URL and license; if there is any CC BY, the post caption must include the `caption_credits` lines.
4. Duration and file size (`ffprobe`).
5. Put the final in `<YOUR_WORKSPACE>/media-team/03-drafts/<題目>-reel/` and report to the main bot: duration, size, footage sources, and anything Josh still needs to decide. Do not post.

## Known limitations
- Most of Mixkit's free downloads are now Restricted (personal, non-commercial only); the script skips them automatically; using them requires Josh's approval.
- archive.org is occasionally very slow or returns empty; the script retries three times; on failure that shot falls back to synth; check the `note:` messages and re-fetch.
- Prelinger films are mostly 4:3, 480p, so cropping to vertical enlarges them a lot, masked with soft focus and grain; prefer segments with simple composition and the subject centered.
- This machine has no GPU: a 30-second video takes about 1 minute to render; a 3-minute video about 5 to 8 minutes.

## Best fit and agent usage

**Best fit:** narrated AI news and essay summaries; pharma regulatory news; narrated one-person-company stories. **Not for:** interview highlights, explainer animation, or numbers-heavy data cards.

- **Grok Boss**: routes narrated news with real footage here (the default fallback).
- **內容製作 (Content Producer)**: writes script.txt and shots.json, generates the voiceover, fetches footage, builds.
- **事實編輯 (Fact Editor)**: checks every line against the source and every clip's license in credits.json.
- **情報偵察員 (Scout)**: flags whether archival film suits the angle.
- **數據復盤師 (Analytics)**: compares archival-heavy vs modern-footage videos.
- **Coding agent (Claude Code / Cursor)**: input: script.txt, vo.mp3, shots.json; output: reel.mp4, contact sheet, credits.json, covers.

Agent workflow (preflight, human gates, costs, failures, done, handoff): see [AGENT-PLAYBOOK.md](../AGENT-PLAYBOOK.md).
