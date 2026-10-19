# 影片 Skill 整合計畫：josh-video-router（草稿，2026-10-19）

狀態：**草稿，尚未安裝**。這份只規劃，沒有刪除、搬移、合併任何程式碼，也沒有 git push。
做法：不合併程式碼，只加一個「路由 skill」，依影片類型指到首選 skill，並統一套用本家規則。

## 一、盤點（30 個資料夾）

`<SKILLS_DIR>/` 共 22 個資料夾（21 個 skill 加 `_deps`），`<YOUR_WORKSPACE>/tools/` 另有 8 套。其中 huashu-art-motion 在 skills/ 是 symlink，lemo-opuscar 兩處各有一份（tools/ 那份有 .git，skills/ 那份沒有，部分檔案不同）。不重複計算約 27 套。

| Skill | 做什麼 | 輸入 → 輸出 | 相依 | 授權 | 適用度 |
|---|---|---|---|---|---|
| interview-reel | 名人訪談 Fox 式：解說穿插 15 到 30 秒原聲 | spec.json＋官方影片 → 1080x1920 mp4 | yt-dlp、ElevenLabs、ffmpeg | 自寫 | ✅ 首選 |
| stock-footage-reel | 口播＋真實素材紀錄片風 | 口播稿 → mp4 | Pexels（免費 key）、Mixkit、Wikimedia、ElevenLabs／edge-tts | 自寫 | ✅ 首選 |
| openmontage-house | OpenMontage 本家規則轉接層＋om_clips.py | 依流程 | OpenMontage | 自寫 | ✅ |
| screen-record | Playwright 錄公開網頁 | JSON spec → 1080x1920 mp4 | Playwright | 自寫 | ✅ |
| OpenMontage | 12 條流程（蒙太奇、切片、螢幕教學、翻譯配音、podcast 等） | 依流程 | Python、Remotion、部分付費生圖 | AGPLv3 | ✅（只在本機用，不對外提供服務） |
| huashu-art-motion | 35 種畫風＋9 種解說語法 | 鏡頭表＋配音 → mp4 | 可吃現成錄音 | MIT | ✅ 首選（解說／藝術） |
| xilo-opus-video | 三方案預覽 → 網頁逐格截圖 | brief＋voice.wav → mp4 | 本機 Chrome，無雲端 TTS | MIT | ✅ |
| lemo-opuscar | 程式渲染 39 種特殊風格 | 故事 → mp4 | TTS、程式配樂 | MIT | ✅（huashu 沒有的風格） |
| video-shotcraft | 產品宣傳片，124 張鏡頭卡 | 網址／截圖 → mp4 | Remotion 4.0.484 | Apache-2.0 | ⚠️ 預設橫式，要重排版 |
| video-talkcraft | 口播驅動解說，字級時間戳 | 腳本＋配音 → mp4 | Remotion、sherpa-onnx ASR；Fish Audio 選項不用 | PolyForm Noncommercial | ⚠️ 商用受限，只當參考 |
| anything2explainer | 黑底 MG 解說 | 主題 → mp4 | Remotion、edge-tts | PolyForm Noncommercial | ⚠️ 寫死 1280x720、商用受限 |
| vox-director | Vox 拼貼風解說／廣告 | 主題 → mp4 | Atlas Cloud API（付費） | MIT | ❌ 付費 key |
| hand-drawn-video-prompts | 中文口播稿 → 手繪蠟筆風 B-roll 提示詞 | 稿 → 提示詞（成片要生圖） | 生圖服務 | MIT | ⚠️ 只用提示詞模式 |
| stickman-video-director | 火柴人英文影片提示詞包 | 文案 → Gemini Omni／Flow 提示詞 | Google Flow 點數 | MIT | ⚠️ 只出提示詞 |
| kid-papercraft | 兒童摺紙生日片提示詞 | 5 問 → 提示詞 | 卡通 IP | MIT（README 非商用免責） | ❌ 跟帳號無關、IP 風險 |
| hbg-life-simulation | 「人生副本」漫畫敘事片 | 長文案 → mp4 | 生圖、Edge TTS、HyperFrames | MIT | ⚠️ 要生圖能力 |
| hbg-classical-poem-silk-video | 古詩詞絲綢國畫片 | 詩 → mp4 | Docker＋gemini-flow-suite | MIT | ❌ 環境未備、題材不符 |
| simon-skills | 調查長片、白板片 | 選題 → 10 分鐘以上成片 | 火山引擎 TTS（中國服務） | MIT | ❌ 火山 TTS；白板也要 codex CLI |
| director | 科普導演，三種模式 | 創意 → 分鏡／提示詞 | LibTV、即夢 dreamina、Seedance（中國服務、扣點） | MIT | ⚠️ 只能用到分鏡 |
| book-sales-video | 圖書帶貨短片 | 書名 → 剪輯稿 | 豆包 TTS、微信讀書、飛書、OpenChatCut（macOS） | MIT | ❌ 中國服務 |
| creator-buddy | 公眾號／小紅書／影片 33 個 skill | 平台＋關鍵字 → 分析 | 多為中國平台 | MIT | ⚠️ 少數影片子 skill 可參考 |
| dbskill／tw-dbskill | 選題、鉤子、AI 味檢查等文案工具 | 文字 → 文字 | dbs-video-extract 要 TikHub／青豆 key | CC BY-NC 4.0 | ⚠️ 非商用，只當思考參考 |
| native-subtitle-quote-image | 影片截字幕拼長圖／金句圖 3:4 | 影片 → 圖 | 無 key | MIT | ✅（輔助，非影片） |
| Punk-Skill | 封面／頭像提示詞 | 文章 → 提示詞 | 生圖 | MIT（固定 v1.0.0-mit） | ✅ 備用封面 |
| impeccable | 網頁 UI 設計檢查 | 前端 → 建議 | 首次下載 engine | Apache 2.0 | — 不是影片 skill |
| video-pipeline | reel.sh：混音、IG 壓縮、QA | mp4 → IG 版 | ffmpeg | 自寫 | ✅ 所有片的收尾 |
| _deps | WeChatReading、hyperframes 相依 | — | — | — | 不是 skill |

## 二、類型 → skill

| 類型 | 首選 | 備案 | 不要用 |
|---|---|---|---|
| 名人訪談／演講 Reel | interview-reel | ffmpeg 剪輯＋xilo 疊層 | OpenMontage clip-factory（沒有解說） |
| 新聞解說（口播＋真實素材） | stock-footage-reel | OpenMontage documentary-montage（少旁白時）＋om_clips.py 找素材 | anything2explainer |
| Vox／知識解說動畫 | huashu-art-motion | xilo-opus-video | vox-director（付費）、anything2explainer、talkcraft（授權） |
| 素材紀錄片／蒙太奇 | stock-footage-reel（有旁白）、OpenMontage documentary-montage（無旁白） | 互為備案 | — |
| 螢幕錄影／工具導覽 | screen-record（網頁實錄） | OpenMontage screen-demo | lemo living-screencast（模擬畫面） |
| 藝術畫風動畫 | huashu-art-motion | lemo-opuscar（特殊風格） | OpenMontage animation |
| 火柴人／手繪 | huashu-art-motion 白板／手繪語法（能直接出片） | stickman-video-director、hand-drawn-video-prompts（只出提示詞，生圖另外問 Josh） | — |
| 資料卡／KPI | huashu data_card_render.py | OpenMontage Remotion 元件 | 靜態 PNG |
| 產品宣傳 | video-shotcraft（重排直式） | xilo-opus-video | — |
| 長片切短片、翻譯配音、podcast | OpenMontage（經 openmontage-house） | — | — |
| 封面 | covers/render.py | Punk-Skill | OpenMontage 縮圖 |
| 收尾（混音、壓縮、QA） | video-pipeline/reel.sh | — | — |

## 三、重複：保留／退役

- **lemo-opuscar 兩份**：建議保留 `<YOUR_WORKSPACE>/tools/lemo-opuscar`（有 .git 可更新），skills/ 那份將來改成 symlink。要 Josh 同意才動。
- **huashu-art-motion**：skills/ 已是 symlink，不用處理。
- **dbskill 與 tw-dbskill**（加 josh-dbskill、dbskill-upstream）：都是 CC BY-NC，建議只留 tw-dbskill 當參考，其他標為不使用。
- **anything2explainer、video-talkcraft**：功能被 huashu／xilo 涵蓋，加上非商用授權，建議標「只做參考，不出正式片」。
- **vox-director**：被 huashu 取代，標「不使用」。
- 退役只是在路由表標記，資料夾不刪。

## 四、在這裡不能用的 skill

| Skill | 原因 |
|---|---|
| book-sales-video | 豆包 TTS、微信讀書、飛書 lark-cli、OpenChatCut（macOS），都是中國服務或我們沒有的環境 |
| simon-skills（調查片、白板片） | 火山引擎 TTS key；白板片還要 codex CLI |
| vox-director | Atlas Cloud 付費 API |
| director（出片部分） | LibTV、即夢 dreamina、Seedance 要登入、扣點，屬中國服務；分鏡部分可參考 |
| hbg-classical-poem-silk-video | 要 Docker＋gemini-flow-suite，題材也不符 |
| kid-papercraft | 兒童生日片，使用卡通 IP，跟帳號無關 |
| creator-buddy 大部分 | 公眾號、小紅書搜尋 |
| dbskill dbs-video-extract | TikHub／青豆付費 key |
| anything2explainer、video-talkcraft（正式片） | PolyForm Noncommercial，帳號有營收 |

## 五、規則衝突（要 Josh 決定）

1. **配音聲音**：INDEX.md、stock-footage-reel、interview-reel 寫的是英文女聲 Sarah Explains（Nhs7eitvQWFTQBsf0yiT）＋繁中字幕；VIDEO-SKILLS.md 和 video-pipeline 寫中文用自己的聲音 <YOUR_ELEVENLABS_VOICE_ID>。路由草稿暫定：中文配音用 <YOUR_ELEVENLABS_VOICE_ID>，英文配音用 Sarah Explains。
2. **BGM**：VIDEO-SKILLS.md 還寫「每支影片都要有 BGM 和音樂署名」，跟 10/19 新規則（配樂署名有就標，不是硬性條件）不一致，要更新。
3. **OpenMontage 是 AGPLv3**：只在本機做片沒問題；如果將來改成對外服務要再看。

---

## 六、josh-video-router SKILL.md 草稿

```markdown
---
name: josh-video-router
description: Josh（@bounce12340）影片的總入口。收到「做一支影片／Reel」時先用這個 skill 判斷類型，再轉給對應的影片 skill，並套用共用的本家規則與審稿交接。只做草稿，不發文。
---

# josh-video-router：Josh 影片路由

**只做草稿，不發文。** 發文一律由主 bot 在 Josh 確認後處理。

## 第 0 步：先讀本家規則
- 語氣與用字：`<YOUR_WORKSPACE>/media-team/00-profile/voice.md`
- 動畫規則：`<YOUR_WORKSPACE>/media-team/00-profile/motion-contract.md`
- 封面：`<YOUR_WORKSPACE>/media-team/covers/README.md`

## 第 1 步：判斷類型（決策表）

| 問題 | 是 → 用 |
|---|---|
| 有名人訪談或演講原片？ | interview-reel |
| 口播＋真實新聞／素材畫面？ | stock-footage-reel |
| 無旁白的主題蒙太奇？ | OpenMontage documentary-montage（讀 openmontage-house） |
| 要錄網頁或工具操作？ | screen-record（素材）→ 接 stock-footage-reel 或 OpenMontage screen-demo |
| 知識解說、Vox 風、藝術畫風、白板、手繪？ | huashu-art-motion；要它沒有的風格才用 lemo-opuscar；要三方案預覽用 xilo-opus-video |
| 價格、跑分、KPI 對比？ | huashu templates/data_card_render.py |
| 產品宣傳？ | video-shotcraft（必須重排成直式） |
| 長片切短片、翻譯配音、podcast？ | OpenMontage（讀 openmontage-house） |
| 都不是？ | 停下來問主 bot，不要自己挑 skill |

不要用：vox-director、book-sales-video、simon-skills、director 出片、hbg-classical-poem、kid-papercraft、anything2explainer 與 video-talkcraft 的正式片（原因見 ROUTER-PLAN.md）。

## 第 2 步：共用本家規則（每支都要做到）
- 台灣繁體中文、台灣用語，用「」，不用破折號（—）。
- 配音：中文用你自己的 ElevenLabs 聲音 `<YOUR_ELEVENLABS_VOICE_ID>`；英文用 Sarah Explains。自然語速，不加速。先用 estimate_only 看點數。
- 配音照字幕念：定稿字幕檔是唯一來源，畫面字幕照同一份切塊。
- BGM：盡量放，有就在 facts.md 標曲名、來源、授權；沒有不擋出片。
- 畫面不放品牌 logo。
- 直式 1080x1920，3 分鐘內；IG 版用 `video-pipeline/reel.sh ig` 壓到 45 MB 以下。
- 不開付費服務、不加新 API key，需要時停下來問 Josh。
- VoiceStudio 規則：不上傳使用者錄音，沒有本人同意不複製聲音。
- 不用中國服務（豆包、火山、飛書、微信讀書、即夢、LibTV）。

## 第 3 步：收尾
1. `reel.sh mix`（有 BGM 時）→ `reel.sh qa` → `reel.sh ig`
2. 交付 script.txt、storyboard.md、ig_caption.txt、threads.txt、facts.md 到 `<YOUR_WORKSPACE>/media-team/03-drafts/<題目>/`

## 第 4 步：交給事實編輯
- 通知事實編輯審 `03-drafts/<題目>/`，報告寫在 `04-review/<稿名>-review.md`。
- 通過後回報主 bot：檔案路徑、片長、檔案大小、全文腳本、無法查證的事實。
```
