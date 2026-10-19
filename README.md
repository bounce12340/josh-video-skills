# josh-video-skills

**English:** A set of agent skills (Claude Code style `SKILL.md` folders) for producing vertical 1080x1920 short videos (IG Reels / Shorts / TikTok) in Traditional Chinese for a Taiwanese audience. `josh-video-router` is the entry point: it decides the video type and hands off to the matching skill. Only the self-written skills are in this repo; third-party packs are linked below and keep their own licenses. Every skill produces drafts only and never posts.

---

這是 Josh（[@bounce12340](https://www.threads.com/@bounce12340)）內容團隊自己寫的影片 skill 整合包，用來做直式短影音（IG Reel、YouTube Shorts、TikTok）。所有 skill 都只做草稿，不會自動發文。

## 總入口：josh-video-router

收到「做一支影片／Reel」時，先讀 `josh-video-router/SKILL.md`。它會：

1. 依決策表判斷影片類型（名人訪談、口播素材剪輯、無旁白蒙太奇、網頁操作錄影等）。
2. 轉給對應的 skill。
3. 套用共用的本家規則（台灣繁中、「」引號、不用破折號、配音照字幕念、不放品牌 logo、YouTube 來源要附原片連結）。
4. 交給事實編輯審稿。

## 資料夾結構

```
josh-video-skills/
├── README.md
├── LICENSE                  # MIT，只涵蓋本 repo 自寫的檔案
├── INDEX.md                 # 全部影片 skill 的索引與決策表（含第三方）
├── ROUTER-PLAN.md           # 整合計畫：盤點、保留／退役、規則衝突
├── josh-video-router/       # 總入口（路由）
│   └── SKILL.md
├── interview-reel/          # 名人訪談／演講片段 Reel（解說穿插原聲）
│   ├── SKILL.md
│   ├── examples/
│   └── scripts/             # prep_clips → tts → fetch_broll → build（run.sh 一鍵跑）
├── stock-footage-reel/      # 口播＋真實素材剪輯 Reel（Pexels、Prelinger 老片等）
│   ├── SKILL.md
│   ├── examples/
│   ├── references/licenses.md
│   └── scripts/
├── screen-record/           # Playwright 錄公開網頁操作，當影片素材
│   ├── SKILL.md
│   ├── record.mjs
│   └── examples/
└── openmontage-house/       # OpenMontage 的本家規則轉接層
    ├── SKILL.md
    └── scripts/om_clips.py
```

## 安裝

1. Clone 這個 repo。
2. 把要用的 skill 資料夾複製（或 symlink）到你的 skills 目錄，例如 Claude Code 的 `~/.claude/skills/`：

   ```bash
   git clone https://github.com/bounce12340/josh-video-skills.git
   cd josh-video-skills
   for s in josh-video-router interview-reel stock-footage-reel screen-record openmontage-house; do
     cp -r "$s" ~/.claude/skills/
   done
   ```

3. 文件裡的 `<SKILLS_DIR>` 指的是放所有 skill（含第三方 skill，例如 OpenMontage）的同一個資料夾。腳本預設會到 skill 資料夾的上一層找 `stock-footage-reel/`、`OpenMontage/`，所以建議全部放在同一層。
4. screen-record 要先裝 Node 依賴：`cd screen-record && npm install`。
5. 需要時再裝第三方 skill（見下方「第三方 skill」），尤其 interview-reel 和 openmontage-house 會用到 OpenMontage。

## 要自己填的設定

文件裡的佔位符：

| 佔位符 | 要換成 |
|---|---|
| `<YOUR_ELEVENLABS_VOICE_ID>` | 你自己的 ElevenLabs 中文配音 voice_id |
| `<YOUR_VOICE_NAME>` | 那個聲音在 ElevenLabs 裡的名稱 |
| `<SKILLS_DIR>` | 放所有 skill 的資料夾 |
| `<YOUR_WORKSPACE>` | 你的工作資料夾（放草稿、封面、語氣檔等） |
| `<YOUR_CONTACT_URL>` | 抓素材時 User-Agent 裡留的聯絡網址 |

腳本讀的環境變數（都可不設，有預設值）：

| 環境變數 | 用途 |
|---|---|
| `PEXELS_API_KEY`、`ELEVENLABS_API_KEY` | 抓素材、配音用的金鑰。只放在環境變數，不要寫進檔案或 commit |
| `SKILLS_DIR` | skill 根目錄，預設是腳本所在 skill 的上一層 |
| `OPENMONTAGE_DIR` | OpenMontage 位置，預設 `<SKILLS_DIR>/OpenMontage` |
| `NODE_BIN_DIR` | 要指定 Node 版本時，放 node 的 bin 資料夾 |
| `COVERS_DIR` | 封面 `render.py` 和 `fonts/`（Noto Sans TC／Noto Serif TC）的資料夾 |
| `BRAND_NAME`、`BRAND_HANDLE` | 影片上的品牌記號文字和片尾帳號 |
| `SFR_USER_AGENT`、`SFR_CACHE` | stock-footage-reel 的 User-Agent 和快取位置 |

英文配音預設用 ElevenLabs 公開聲音庫的 Sarah Explains（`Nhs7eitvQWFTQBsf0yiT`），可在 spec 的 `voice_id` 改掉。

另外有幾個檔案是作者自己工作區裡的，**沒有放進這個 repo**，要自己準備或拿掉相關步驟：封面產生器 `covers/render.py` 與字型、語氣檔 `voice.md`、動畫規則 `motion-contract.md`、收尾用的 `video-pipeline/reel.sh`。

## 第三方 skill（未包含，請到原作 repo 取得）

`INDEX.md` 和 `ROUTER-PLAN.md` 會提到下面這些 skill。它們都不是這個 repo 的作品，也沒有複製進來；各自保留原本的授權，使用前請讀原作的 LICENSE。

| Skill | 原作 repo | 授權（以原 repo 為準） |
|---|---|---|
| OpenMontage | https://github.com/calesthio/OpenMontage | AGPL-3.0 |
| Punk-Skill | https://github.com/adrianpunk/Punk-Skill | MIT |
| book-sales-video | https://github.com/Kianzzz/book-sales-video | MIT |
| xilo-opus-video | https://github.com/Kianzzz/xilo-opus-video | MIT |
| creator-buddy | https://github.com/SpaceZephyr/creator-buddy | 未附授權檔 |
| dbskill | https://github.com/dontbesilent2025/dbskill（台灣繁中 fork：https://github.com/bounce12340/tw-dbskill） | CC BY-NC 4.0 |
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
| lemo-opuscar | https://github.com/lemomo-ai/lemo-opuscar | MIT |
| impeccable | https://github.com/pbakaus/impeccable | Apache-2.0 |
| video-shotcraft | https://github.com/Vincentwei1021/video-shotcraft | Apache-2.0 |
| video-talkcraft | https://github.com/Vincentwei1021/video-talkcraft | PolyForm Noncommercial |
| anything2explainer | https://github.com/Vincentwei1021/anything2explainer | PolyForm Noncommercial |
| hyperframes（相依套件） | https://github.com/heygen-com/hyperframes | Apache-2.0 |

`INDEX.md` 的整理來源是 @xaiwind 的貼文〈Codex 爆款视频skill，10个装完百万播放〉。

## 使用注意

- 所有 skill 只做草稿，發文前要本人確認。
- 素材授權逐支確認：stock-footage-reel 的 `references/licenses.md` 整理了各素材庫的授權重點。interview-reel 用的訪談原片靠「評論、引用」的合理使用，屬於灰色地帶，SKILL.md 有詳細說明。
- 不要把聲音檔上傳到別的雲端；沒有本人同意，不要複製別人的聲音。

## 授權

本 repo 自寫的檔案以 [MIT License](LICENSE) 釋出，Copyright (c) 2026 Josh Tsai（bounce12340）。第三方 skill 不在本 repo 內，各自依原作授權。
