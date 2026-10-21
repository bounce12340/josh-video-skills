---
name: interview-reel
description: "Vertical Reel of 「名人訪談／演講片段」 (celebrity interview / talk clips), Fox Hsiao style \"commentary intercut with original audio\": commentary segments with voiceover chosen by language (Chinese uses 「<YOUR_VOICE_NAME>」 <YOUR_ELEVENLABS_VOICE_ID>; English uses Sarah Explains) + Traditional Chinese main subtitles, intercut with 15 to 30 second clips of the celebrity's original audio (16:9 centered, blurred fill above and below, a 「原聲 姓名｜場合｜日期」 source label, 「影片／原頻道」 at top left), ending with a question to the audience. One JSON spec goes all the way to the final video, a 720p preview, a contact sheet, credits.json, and covers. Triggers: 「名人訪談」, 「演講片段」, 「訪談 Reel」, 「Fox 式」, 「解說加原聲」, \"interview reel\"."
---

# interview-reel: celebrity interview / talk clip Reels (Fox Hsiao style)

Josh approved on 2026-10-12: celebrity interviews use the Fox style, with commentary intercut with 15 to 30 second original-audio clips and sources labeled, made into a fixed skill.
**This skill produces drafts only, never posts.** Posting is always handled by the main bot after Josh confirms.

- Scripts: `<SKILLS_DIR>/interview-reel/scripts/` (called `$S` below)
- Example spec: `examples/mcp_test.spec.json` (Anthropic's official MCP interview, test clip)
- Reference output: `<YOUR_WORKSPACE>/media-team/03-drafts/interview-reel-test/test.mp4`
- Reference videos: `<YOUR_WORKSPACE>/refs/ig-DeWJjxJyoEb/` (Fox Hsiao, Musk Terafab, the format to learn), `<YOUR_WORKSPACE>/refs/ig-DWVQfDmE41Z/` (AI郵報, Jensen Huang, original audio only, the simplest; don't copy its lack of source labels)
- Reused: stock-footage-reel's common.py (fonts, downloads), synth_music.py (original music), Pexels cache; OpenMontage's venv (faster-whisper, yt-dlp) and `elevenlabs_tts`; covers via `<YOUR_WORKSPACE>/media-team/00-profile/covers/render.py`.

## Format (broken down from the Fox Hsiao video)
| Segment | Visuals | Audio |
|---|---|---|
| hook (0 to about 11 seconds) | Full-frame 9:16 B-roll (darkened, slow push-in), cutting every 1 to 2.5 seconds; large title card at top left (small red category tag + two lines of bold text, key words orange) | Narration (Chinese <YOUR_VOICE_NAME> / English Sarah Explains) + music |
| clip (original audio, 15 to 30 seconds each, 3 to 4 clips) | 16:9 source centered (y=468), filled above and below with the same frame blurred and darkened; small 「影片／原頻道」 (video / original channel) at the source's top left; below the source a red 「原聲」 (original audio) tag + 「英文名　中文名或身分」 (English name, Chinese name or role) + 「場合｜YYYY.MM.DD」 (occasion, date) | **Original audio only**, no narration on top; music ducked lower (clip_music_db) plus sidechain ducking |
| explainer (commentary, between clips) | Same as hook, with a fact card instead and small 「來源：誰｜日期」 (source: who, date) below; cuts every 2 to 3.2 seconds | Narration (Chinese <YOUR_VOICE_NAME> / English Sarah Explains) + music |
| outro | Large centered question (key words yellow) + brand mark + @bounce12340 + one line of small source text at the bottom | Narration asks the audience (Chinese <YOUR_VOICE_NAME> / English Sarah Explains) |

Shared across the video: a fixed title bar at the top (brand mark + one-line title, key words orange); centered subtitles, large Traditional Chinese text (white, bold, soft shadow, key words yellow) + one small English line below. In commentary segments the English is the narration text; in clip segments the English is a transcript of the speaker's words and the Chinese is our translation.

## House rules (must follow)
- 1080x1920, under 3 minutes, IG final under 45 MB (re-encoded at a lower bitrate automatically if over), H.264 / AAC.
- Narration: pick the ElevenLabs voice by language. Chinese uses **「<YOUR_VOICE_NAME>」** (`<YOUR_ELEVENLABS_VOICE_ID>`); English uses **Sarah Explains** (`Nhs7eitvQWFTQBsf0yiT`). Model `eleven_multilingual_v2`, via OpenMontage's `elevenlabs_tts`. The key is the machine environment variable `ELEVENLABS_API_KEY` (only carried over with `bash -lc`); **do not print it or write it to files**.
- Subtitles: Traditional Chinese main subtitles + small English line. Taiwan wording (軟體、資料、影片、網路、運算資源…), 「」 quotes, **no em-dashes** (build.py blocks them).
- **Commentary must be the majority**: total original audio is recommended at 40% or less; over 50% is blocked by build.py. Each clip is at most 30 seconds (prep_clips.py blocks longer), recommended 15 to 30 seconds.
- No narration over clips and no altering the speaker's words; the Chinese translation must be faithful and must not add conclusions for the speaker.
- Faithful to the source: numbers and dates in the commentary must trace back to primary sources; cards mark 「來源：誰｜日期」 with `cite`, and these go into facts.md.
- Always end with a question to the audience (outro.question must contain 「？」).
- Covers use covers/render.py, with `cover.template` defaulting to `"E"` (large portrait; Josh calls it 「D 人物大頭」). Josh decided before 2026-10-12: celebrity interviews always use this layout.

## Footage sources and licensing (recorded in every video's credits.json)
1. **Prefer official sources**: official company channels (Anthropic, OpenAI, NVIDIA, Microsoft…), event organizers (GTC, Build, TED…), a podcast's own channel. The spec's `channel` must be the original channel name; prep_clips.py compares it with YouTube's channel field and warns on mismatch.
2. **Never use reposts or versions with someone else's watermark** (e.g. fan page re-uploads, clips cut by other accounts, versions with someone else's logo). If no official version exists, skip that segment.
3. **Always label the source on screen**: 「原聲 姓名｜場合｜日期」 below the clip + 「影片／原頻道」 at top left, repeated in small text at the end, and paste `credits.json`'s `caption_credits` into the post caption.
4. credits.json automatically records: source URL, channel, channel URL, video title, upload date, the cut in/out times (source_in / source_out), position in the final video, each B-roll's URL and author, voiceover, and music.
5. **License note**: copyright in these interview visuals belongs to the original channels; we have no license and rely on fair use for "commentary and quotation" (Taiwan Copyright Act Articles 52 and 65), **which is a gray area**. So: keep each clip short, make the whole video mainly Josh's commentary and synthesis (transformative), use original audio only as supporting evidence; do not lift whole segments or cut it into something the speaker never meant.
6. **Do not imply endorsement**: never write things like "recommended by X" or "official partnership"; covers and titles must not suggest the speaker supports Josh or his products.
7. Downloads: use yt-dlp only for **public** videos; no login, no cookies, no bypassing paywalls or region locks. On this machine YouTube's `--download-sections` returns 403, so prep_clips.py downloads the whole video (up to 1080p), caches it in `cache/sources/`, then cuts with ffmpeg.
8. If the original channel requests removal or Josh is uneasy, switch to text quotes only, without visuals.

## Workflow
```
D=<YOUR_WORKSPACE>/media-team/03-drafts/<題目>-interview ; mkdir -p $D/work
cp $S/../examples/mcp_test.spec.json $D/spec.json      # 改成這次的內容
bash -lc "source <SKILLS_DIR>/OpenMontage/om-env.sh >/dev/null; cd $S; python prep_clips.py --spec $D/spec.json --work $D/work"
```
1. **Pick clips**: first read the source's chapters (yt-dlp `--print description`), and in the official video pick a 15 to 30 second stretch where the speaker states the point completely. Transcribe with `prep_clips.py`; to just audition first, download the whole video and cut a short piece with ffmpeg to listen.
2. **prep_clips.py**: download, cut, transcribe (faster-whisper `medium`; a 20-second clip takes about 10 seconds on CPU). It prints a `"subs"` template: paste it back into that clip, translate `zh` into Taiwan Traditional Chinese, and merge or split lines as needed (`t` is seconds relative to the clip start). English follows the speaker's exact words; re-listen to any doubtful words, or cross-check with another model (`--retranscribe --model small`).
3. **tts.py**: one audio file per line; identical text is sent only once (cached by text hash in `cache/tts/`). Run `--dry-run` first to see how many characters will be sent. Fallback on failure: the user-Elevenlabs connector `creative_generate_speech` (`generations_count: 1`), saved to the cache path it prints.
4. **fetch_broll.py**: fetches 3 clips per keyword from Pexels (landscape preferred; keywords are more accurate). Write concrete visuals ("server rack lights", "programmer coding"), not abstract words. A line can also take `"image"` (a still, slowly pushed in) or `"file"` (e.g. a web page recorded with screen-record).
5. **build.py --check**: prints duration, original-audio share, each subtitle's timing, and rule warnings.
6. **build.py**: renders the video. Or run everything at once: `bash $S/run.sh $D/spec.json $D <name>` (translate the subs first).

## spec fields
```json
{
  "title": "上方固定標題，[[重點]] 變橘色",
  "voice": {"voice_id": "Nhs7eitvQWFTQBsf0yiT", "model": "eleven_multilingual_v2"},  // 英文 Sarah Explains；中文片改 <YOUR_ELEVENLABS_VOICE_ID>（你的中文聲音）
  "music": "synth",            // 原創合成配樂；或音檔路徑（要附 music_license）；或 "none"
  "music_db": -19,             // 配樂基準音量
  "clip_music_db": -8,         // 原聲段配樂再壓低幾 dB
  "gap": 0.28,                 // 每句旁白後的停頓（秒），單句可用 line.pause 覆寫
  "max_cut": 3.2,              // 解說段每幾秒換一次畫面（hook 預設 2.4，段落可用 seg.max_cut 覆寫）
  "segments": [
    {"type": "hook", "broll": ["關鍵字"], "lines": [
      {"en": "旁白英文", "zh": "字幕中文", "card": {"tag": "紅色小標", "text": "第一行\n第二行[[重點]]", "cite": "來源：…｜YYYY.MM.DD"}}
    ]},
    {"type": "clip", "url": "https://www.youtube.com/watch?v=…", "channel": "原頻道", "official": true,
     "in": 147.1, "out": 166.75, "speaker_en": "David Soria Parra", "speaker_zh": "MCP 共同創造者",
     "event": "Anthropic 官方訪談", "date": "2025.12.11", "highlight": ["要變黃的中文詞"],
     "subs": [{"t": [0.0, 3.56], "en": "講者原話", "zh": "台灣繁中翻譯"}]},
    {"type": "explainer", "broll": ["…"], "lines": [
      {"en": ["分段一,", "分段二。"], "zh": ["字幕一", "字幕二"], "broll": ["這句專用的關鍵字"], "card": {…}}
    ]},
    {"type": "outro", "tag": "留言聊聊", "question": "大問題第一行\n第二行[[重點]]？", "broll": ["…"], "lines": [{"en": "…", "zh": "…"}]}
  ],
  "cover": {"template": "E", "ep": "EP.13", "kicker": "…", "title": "…\n[[…]]", "subtitle": "…", "frame": {"clip": 1, "t": 4.0}}
}
```
- `en` / `zh` can be a string or lists of equal length (a list = one narration line split into several subtitles, timed in proportion to English word count).
- `card` carries over to the next line within the same segment until a new card appears; `"card": false` clears it.
- A `zh` that is too long breaks automatically into two lines at 「，」; use `\n` to break it yourself. Mark key words with `[[ ]]` or an `hl` list.
- `cover.frame`: which second of which clip (original 16:9 frame) to use for the cover. Other E-template fields (`photo_side`, `visual_pos`, `brightness`, `tag`) follow covers/README.md.
- Chinese names: use the speaker's common Chinese name if there is one (e.g. 黃仁勳, 馬斯克); otherwise write their role (e.g. 「MCP 共同創造者」); do not transliterate on your own.

## Output (OUT)
`<name>.mp4`, `preview_720p.mp4` (for Josh to watch in chat), `contact_sheet.jpg` (one middle frame per shot), `credits.json`, `timeline.json`, `cover_reel.png` / `cover_post.png`, `cover_spec.json`.

## Self-check before delivery
1. View contact_sheet.jpg with Read: are cards, subtitles, and clip labels overlapping or covered by the IG interface (top 220px, bottom 380px, right 130px)?
2. Clip subtitles: the English matches the speaker's words, and the Chinese doesn't distort the meaning; flag uncertain transcriptions for Josh to listen to.
3. Check duration and size with `ffprobe`; the original-audio share is on build.py's last line.
4. Every entry in credits.json's interview_clips has a URL, channel, and in/out times; confirm it is an official channel.
5. Report to the main bot: file path, duration, size, clip sources and license note, and anything Josh needs to decide. Do not post.

## Known limitations
- faster-whisper on this machine: `*.en` models (small.en, etc.) output garbage, so use multilingual `medium` / `small`; the PyAV version is incompatible, so audio must be fed via numpy (the script handles this). Different models occasionally drop words in the same passage, so cross-check key lines.
- YouTube `--download-sections` returns 403, so only whole-video downloads work (a long 1080p interview may be hundreds of MB, cached in cache/sources/; delete after use).
- No GPU: a 1-minute video takes about 2 minutes to render; a 3-minute video about 6 to 8 minutes.
- Pexels keyword results are sometimes off; check the contact sheet, then change keywords or use `image` / `file`.

## Best fit and agent usage

**Best fit:** celebrity / founder interview highlights and talks with an official public video; speaker-on-record AI news. **Not for:** no official video, reposts, tool demos, or mostly-original-audio cuts (over 50% is blocked).

- **Grok Boss**: routes here only when official interview footage exists.
- **內容製作 (Content Producer)**: writes the spec, translates the clip subs, runs prep_clips → tts → fetch_broll → build.
- **事實編輯 (Fact Editor)**: checks official channel, translation faithfulness, `cite` sources, and no implied endorsement.
- **情報偵察員 (Scout)**: names the official source video and channel when proposing the topic.
- **數據復盤師 (Analytics)**: records the original-audio share and clip count from build.py next to the results.
- **Coding agent (Claude Code / Cursor)**: input: spec.json (see examples/); output: mp4, 720p preview, contact sheet, credits.json, covers. Run `build.py --check` first.
