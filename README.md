# josh-video-skills

> **Language:** English (main) · [中文說明](#中文說明)

A set of agent skills (Claude Code style `SKILL.md` folders) built by the content team of Josh ([@bounce12340](https://www.threads.com/@bounce12340)) for producing vertical 1080x1920 short videos (IG Reels, YouTube Shorts, TikTok) in Traditional Chinese for a Taiwanese audience. Only the self-written skills are in this repo; third-party packs are linked below and keep their own licenses. Every skill produces drafts only and never posts automatically.

## Main entry point: josh-video-router

When asked to 「做一支影片／Reel」 (make a video / Reel), read `josh-video-router/SKILL.md` first. It will:

1. Decide the video type from a decision table (celebrity interview, voiceover + footage edit, narration-free montage, web interaction recording, etc.).
2. Hand off to the matching skill.
3. Apply the shared house rules (Taiwan Traditional Chinese, 「」 quotes, no em-dashes, voiceover reads the subtitles exactly, no brand logos, YouTube-sourced videos link the original).
4. Hand off to the fact editor (事實編輯) for review.

## Folder structure

```
josh-video-skills/
├── README.md
├── LICENSE                  # MIT, covers only files written for this repo
├── INDEX.md                 # Index and decision table of all video skills (including third-party)
├── AGENT-PLAYBOOK.md        # How agents run the skills: preflight, gates, costs, failures, done
├── ROUTER-PLAN.md           # Integration plan: inventory, keep / retire, rule conflicts
├── josh-video-router/       # Main entry point (router)
│   └── SKILL.md
├── interview-reel/          # Celebrity interview / talk clip Reels (commentary intercut with original audio)
│   ├── SKILL.md
│   ├── examples/
│   └── scripts/             # prep_clips → tts → fetch_broll → build (run.sh runs it all)
├── stock-footage-reel/      # Voiceover + real-footage Reels (Pexels, Prelinger archival films, etc.)
│   ├── SKILL.md
│   ├── examples/
│   ├── references/licenses.md
│   └── scripts/
├── screen-record/           # Playwright recording of public web pages as video footage
│   ├── SKILL.md
│   ├── record.mjs
│   └── examples/
├── diagram-design/          # House-rules adapter for diagram-design: editorial HTML + SVG diagrams as 9:16 frames
│   ├── SKILL.md
│   └── references/          # upstream.md (what the upstream skill does), render-916.md (HTML/SVG → 1080x1920)
├── lemo-opuscar-house/      # House rules for lemo-opuscar's Oct 2026 news / evidence styles and MY-STYLES
│   └── SKILL.md
├── openmontage-house/       # House-rules adapter layer for OpenMontage
│   ├── SKILL.md
│   └── scripts/om_clips.py
├── x-scout/                 # Read-only X topic watcher: classify hits, suggest skill + style
│   ├── SKILL.md
│   ├── scripts/x_scout.py
│   └── examples/
├── analytics/               # style_compare.py: median metrics per skill / style from X exports
│   ├── README.md
│   ├── style_compare.py
│   └── style_tags.csv
└── opus-5-5-prompts/        # Reference list of viral Opus 5.5 video prompts (links only, no prompt text)
    ├── README.md
    ├── catalog.md
    └── build_catalog.py
```

## Which skill for which topic

Agent workflow (preflight, human gates, costs, failures, done, handoff): see [AGENT-PLAYBOOK.md](AGENT-PLAYBOOK.md).

| Folder | What it produces | Reach for it when |
|---|---|---|
| josh-video-router | The choice of skill, plus the shared house rules | Any 「做一支影片／Reel」 request; always loaded first |
| interview-reel | Commentary Reels intercut with original interview audio | There is official public video of the person speaking |
| stock-footage-reel | Narrated Reels edited from real footage (the default) | AI news, essays, pharma regulatory news, narrated stories |
| screen-record | 1080x1920 recordings of public web pages, as footage | A tool or website has to be shown being used |
| diagram-design | Editorial HTML + SVG diagram plates rendered as 9:16 frames | The topic explains a mechanism: how an agent works, a workflow, an architecture, a process |
| lemo-opuscar-house | lemo-opuscar's Edit & Documentary and Evidence Films styles at 1080x1920 with ElevenLabs voices | Straight AI / startup news (Caption News), weekly roundups (Broadcast News Package), incident reconstructions (Visual Investigation) |
| openmontage-house | OpenMontage pipelines run under the house rules | Long-to-short, podcasts, dubbing, screen tutorials, narration-free montage, archival footage |
| x-scout | Topic proposals from recent X posts (read-only) | Looking for something to make |
| analytics | Median metrics per skill / style from X exports | Reviewing what worked after publishing |
| opus-5-5-prompts | A style reference list (links only) | Picking a visual style for a code-rendered video |

The skill × topics × agents matrix, the opus-5-5-prompts style picks, and the recommended-style rule for topic proposals live in [INDEX.md](INDEX.md#skill-matrix-topics-and-agents).

## Installation

1. Clone this repo.
2. Copy (or symlink) the skill folders you want into your skills directory, e.g. Claude Code's `~/.claude/skills/`:

   ```bash
   git clone https://github.com/bounce12340/josh-video-skills.git
   cd josh-video-skills
   for s in josh-video-router interview-reel stock-footage-reel screen-record diagram-design lemo-opuscar-house openmontage-house x-scout; do
     cp -r "$s" ~/.claude/skills/
   done
   ```

3. `<SKILLS_DIR>` in the docs means the single folder holding all skills (including third-party ones such as OpenMontage). Scripts look for `stock-footage-reel/` and `OpenMontage/` one level above the skill folder by default, so keeping them all at the same level is recommended.
4. screen-record needs its Node dependencies first: `cd screen-record && npm install`.
5. Install third-party skills as needed (see "Third-party skills" below); interview-reel and openmontage-house in particular use OpenMontage.

## Settings to fill in yourself

Placeholders in the docs:

| Placeholder | Replace with |
|---|---|
| `<YOUR_ELEVENLABS_VOICE_ID>` | Your own ElevenLabs Chinese voiceover voice_id |
| `<YOUR_VOICE_NAME>` | That voice's name in ElevenLabs |
| `<SKILLS_DIR>` | The folder holding all skills |
| `<YOUR_WORKSPACE>` | Your working folder (drafts, covers, voice file, etc.) |
| `<YOUR_CONTACT_URL>` | The contact URL left in the User-Agent when fetching footage |
| `<DIAGRAM_DESIGN_DIR>` | Where the third-party diagram-design skill is installed (default `<SKILLS_DIR>/cathrynlavery-diagram-design/skills/diagram-design`; it must not sit on top of this repo's `diagram-design/` adapter, which has the same name) |

Environment variables read by the scripts. `BRAND_NAME`, `BRAND_HANDLE`, `COVERS_DIR`, and `SFR_USER_AGENT` must be set before building: the build scripts (and `--check`) stop with a clear error if they still hold template placeholders.

| Environment variable | Purpose |
|---|---|
| `PEXELS_API_KEY`, `ELEVENLABS_API_KEY` | Keys for fetching footage and voiceover. Keep them in environment variables only; never write them to files or commit them |
| `SKILLS_DIR` | Skills root; defaults to one level above the script's skill |
| `OPENMONTAGE_DIR` | OpenMontage location; defaults to `<SKILLS_DIR>/OpenMontage` |
| `NODE_BIN_DIR` | Node bin folder, when you need a specific Node version |
| `COVERS_DIR` | Folder with the cover `render.py` and `fonts/` (Noto Sans TC / Noto Serif TC) |
| `BRAND_NAME`, `BRAND_HANDLE` | Brand mark text on the video and the end-card handle |
| `ELEVENLABS_VOICE_ID_EN` | English voiceover voice_id for interview-reel's tts.py (Josh: `xBHPgy3hJ2fclZQIoDnv`) |
| `SFR_USER_AGENT`, `SFR_CACHE` | stock-footage-reel's User-Agent and cache location |
| `X_BEARER_TOKEN` | Read-only X API token for x-scout and optional analytics pulls. Environment variable only; never commit it |

English voiceover (since 2026-10-20) uses Josh's own ElevenLabs voice "Josh - Calm, Warm Taiwanese narrator" (voice_id `xBHPgy3hJ2fclZQIoDnv`, model `eleven_multilingual_v2`; Josh confirmed it is his voice and approved its use). Scripts read it from the `ELEVENLABS_VOICE_ID_EN` environment variable (no voice_id is hard-coded); a spec's `voice_id` overrides it. Budget about 1,800 characters of credit per video and always use `generations_count: 1`. If you fork this repo, use your own voice.

A few files live in the author's own workspace and are **not included in this repo**; prepare your own or drop the related steps: the cover generator `covers/render.py` and fonts, the voice file `voice.md`, the motion rules `motion-contract.md`, and the wrap-up script `video-pipeline/reel.sh`.

## Third-party skills (not included; get them from the original repos)

`INDEX.md` and `ROUTER-PLAN.md` mention the skills below. None of them are this repo's work and none are copied in; each keeps its original license, so read the original LICENSE before use.

| Skill | Original repo | License (the original repo is authoritative) |
|---|---|---|
| OpenMontage | https://github.com/calesthio/OpenMontage | AGPL-3.0 |
| diagram-design (editorial HTML + SVG diagrams, 45 types; house adapter in `diagram-design/`) | https://github.com/cathrynlavery/diagram-design | MIT (Copyright (c) 2025 Cathryn Lavery; copying would be allowed with the notice kept, but nothing is copied here) |
| Punk-Skill | https://github.com/adrianpunk/Punk-Skill | MIT |
| book-sales-video | https://github.com/Kianzzz/book-sales-video | MIT |
| xilo-opus-video | https://github.com/Kianzzz/xilo-opus-video | MIT |
| creator-buddy | https://github.com/SpaceZephyr/creator-buddy | No license file included |
| dbskill | https://github.com/dontbesilent2025/dbskill(Taiwan Traditional Chinese fork: https://github.com/bounce12340/tw-dbskill) | CC BY-NC 4.0 |
| director | https://github.com/s1dashu/director | MIT |
| hand-drawn-video-prompts | https://github.com/kaomei/hand-drawn-video-prompts | MIT |
| kid-papercraft | https://github.com/kaomei/kid-papercraft | MIT |
| stickman-video-director | https://github.com/kaomei/stickman-video-director | MIT |
| hbg-classical-poem-silk-video | https://github.com/Mr-funny/hbg-classical-poem-silk-video | MIT |
| hbg-life-simulation | https://github.com/Mr-funny/hbg-life-simulation | MIT |
| huashu-art-motion | https://github.com/alchaincyf/huashu-art-motion | MIT |
| native-subtitle-quote-image | https://github.com/chengyi-ai/native-subtitle-quote-image | MIT |
| simon-skills | https://github.com/trustfuture/simon-skills | MIT |
| vox-director | https://github.com/Alisa0808/vox-director | MIT |
| lemo-opuscar (house notes for the Oct 2026 styles in `lemo-opuscar-house/`) | https://github.com/lemomo-ai/lemo-opuscar | Code MIT (Copyright (c) 2026 LemoLab); demo films and stills CC BY 4.0, credit LemoLab; three demo voice tracks are excluded and must not be reused |
| impeccable | https://github.com/pbakaus/impeccable | Apache-2.0 |
| video-shotcraft | https://github.com/Vincentwei1021/video-shotcraft | Apache-2.0 |
| video-talkcraft | https://github.com/Vincentwei1021/video-talkcraft | PolyForm Noncommercial |
| awesome-opus5-5-videos (prompt list, see opus-5-5-prompts/) | https://github.com/yihui-dev/awesome-opus5-5-videos | MIT (each prompt belongs to its author; this repo copies no prompt text) |
| anything2explainer | https://github.com/Vincentwei1021/anything2explainer | PolyForm Noncommercial |
| hyperframes (dependency) | https://github.com/heygen-com/hyperframes | Apache-2.0 |

`INDEX.md` was compiled from @xaiwind's post 〈Codex 爆款视频skill，10个装完百万播放〉.

## Usage notes

- Every skill produces drafts only; the account owner must confirm before posting.
- Confirm footage licenses item by item: stock-footage-reel's `references/licenses.md` summarizes each library's license terms. The interview footage used by interview-reel relies on fair use for "commentary and quotation", which is a gray area; SKILL.md explains it in detail.
- Do not upload voice files to other clouds; do not clone anyone's voice without their consent.

## License

Files written for this repo are released under the [MIT License](LICENSE), Copyright (c) 2026 Josh Tsai (bounce12340). Third-party skills are not in this repo and follow their original licenses.

---

## 中文說明

這是 Josh（[@bounce12340](https://www.threads.com/@bounce12340)）內容團隊自己寫的影片 skill 整合包，用來做直式短影音（IG Reel、YouTube Shorts、TikTok）。所有 skill 都只做草稿，不會自動發文。

- **總入口**：收到「做一支影片／Reel」時，先讀 `josh-video-router/SKILL.md`。它會依決策表判斷影片類型、轉給對應的 skill、套用共用的本家規則（台灣繁中、「」引號、不用破折號、配音照字幕念、不放品牌 logo、YouTube 來源要附原片連結），再交給事實編輯審稿。
- **安裝**：把要用的 skill 資料夾複製到你的 skills 目錄（例如 `~/.claude/skills/`），建議跟第三方 skill（例如 OpenMontage）放在同一層。screen-record 要先 `npm install`。
- **設定**：文件裡的 `<YOUR_ELEVENLABS_VOICE_ID>`、`<YOUR_VOICE_NAME>`、`<SKILLS_DIR>`、`<YOUR_WORKSPACE>`、`<YOUR_CONTACT_URL>` 要換成自己的值。金鑰只放環境變數，不要寫進檔案或 commit。
- **lemo-opuscar 新風格**：`lemo-opuscar-house/` 整理了 LemoLab 的 lemo-opuscar 在 2026 年 10 月新增的「剪輯與紀實」（2026-10-22，8 種）和「實證影像」（2026-10-16，8 種）風格，以及「做成自己的風格」（MY-STYLES.md）。適合 AI 新聞用 Caption News、每週整理用 Broadcast News Package、事件重建用 Visual Investigation。上游預設 1920×1080，一律加 `--size 1080x1920` 並重新排版；配音改用 Josh 的 ElevenLabs 聲音，不用 Kokoro。程式碼是 MIT、示範影片是 CC BY 4.0，要標註 LemoLab；有三段示範配音不在授權內，不准拿來用。本 repo 沒有複製上游檔案，只放連結和摘要。
- **圖解影片**：主題是在解釋一個機制（agent 怎麼運作、工作流程、系統架構、流程說明）時，用 `diagram-design/`。它是第三方 skill [cathrynlavery/diagram-design](https://github.com/cathrynlavery/diagram-design)（MIT，Copyright (c) 2025 Cathryn Lavery）的本家規則轉接層：本 repo 一個檔案都沒有複製過來，只寫「什麼題目適合畫圖、要跟它要什麼（繁中要指定 Noto Sans TC，上游字體沒有中文字）、怎麼把 HTML/SVG 輸出成 1080x1920 影片幀、字幕安全區在哪」。上游 skill 的名字也叫 diagram-design，裝的時候要分開放，不要蓋在本 repo 這個資料夾上。
- **第三方 skill**：都不在本 repo 內，各自保留原本的授權，清單見上方英文表格。
- **使用注意**：發文前要本人確認；素材授權逐支確認；不要把聲音檔上傳到別的雲端，沒有本人同意不要複製別人的聲音。
- **授權**：本 repo 自寫的檔案以 [MIT License](LICENSE) 釋出，Copyright (c) 2026 Josh Tsai（bounce12340）。
