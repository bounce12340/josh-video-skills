---
name: josh-video-router
description: 收到「做一支影片／Reel」時先用：判斷影片類型、轉給對應的影片 skill，套用共用本家規則並交給事實編輯。只做草稿，不發文。
---
# josh-video-router：Josh 影片路由

**只做草稿，不發文。** 發文一律由主 bot 在 Josh 確認後處理。完整盤點與原因見 `<SKILLS_DIR>/ROUTER-PLAN.md`。

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
- 新聞片只報新聞，不加 Josh 的第一人稱觀點，除非他要求。
- BGM：盡量放，有就在 facts.md 標曲名、來源、授權；沒有不擋出片。
- 畫面不放品牌 logo，素材要對上那句話真正的情境。
- 直式 1080x1920，3 分鐘內；IG 版用 `video-pipeline/reel.sh ig` 壓到 45 MB 以下。
- 根據 YouTube 影片做的，所有貼文附原片連結並標註原作者。
- 不開付費服務、不加新 API key，需要時停下來問 Josh。
- VoiceStudio 規則：不上傳使用者錄音，沒有本人同意不複製聲音。
- 不用中國服務（豆包、火山、飛書、微信讀書、即夢、LibTV）。

## 第 3 步：收尾
1. `reel.sh mix`（有 BGM 時）→ `reel.sh qa` → `reel.sh ig`
2. 交付 script.txt、storyboard.md、ig_caption.txt、threads.txt、facts.md 到 `<YOUR_WORKSPACE>/media-team/03-drafts/<題目>/`

## 第 4 步：交給事實編輯
- 通知事實編輯審 `03-drafts/<題目>/`，報告寫在 `04-review/<稿名>-review.md`。
- 通過後回報主 bot：檔案路徑、片長、檔案大小、全文腳本、無法查證的事實。
