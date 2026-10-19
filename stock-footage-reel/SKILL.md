---
name: stock-footage-reel
description: 「真實素材剪輯」直式短影音（AYi @ayi_ainotes 那種紀錄片風）：照口播稿每一句，自動搜尋並下載免費可商用素材（Pexels、Mixkit Free、Wikimedia Commons），加上洋紅調的 1950 到 70 年代 Prelinger 公有領域老片，硬切剪輯，燒上雙語字幕（繁中＋英文，重點字金色），左上固定標題，ElevenLabs 配音，暗色合成器配樂，片尾金句卡加出處小字，再用 B 剪報 Vox 樣板出封面。觸發語：「做一支真實素材剪輯」、「stock footage reel」、「AYi 風格」、「素材庫剪輯」。
---

# stock-footage-reel：真實素材剪輯 Reel

> **2026-10-11 合併說明：** 有口播的真實素材 Reel，這個 skill 仍是首選（canonical）。OpenMontage 的 documentary-montage 只用在無旁白／少旁白的蒙太奇；兩者的分工見 `<SKILLS_DIR>/INDEX.md` 決策表。
> - 要更多素材來源（NASA、國會圖書館 LOC、NARA、Archive.org、Wikimedia）：用 `python3 <SKILLS_DIR>/openmontage-house/scripts/om_clips.py --query "..." --out $D/work/om_clips`，它會印出可以直接貼進 shots.json 的 `pick: {"source":"file",...}`。授權要逐支確認後才放進 credits.json。
> - 配音現行設定：中文用你自己的 ElevenLabs 聲音 **「<YOUR_VOICE_NAME>」**（`<YOUR_ELEVENLABS_VOICE_ID>`）；英文用 **Sarah Explains**（`Nhs7eitvQWFTQBsf0yiT`）。繁中主字幕＋小字英文。英文配音的做法看 EP.07：`<YOUR_WORKSPACE>/media-team/03-drafts/grokbot-team-reel/`（script_en.txt、work/shots.json 用 `subs_zh`＋`en`，對時和剪片用 work/ 裡的 mktiming.py、build_custom.py）。下面第 2 步依語言選聲。

給 Josh（IG／Threads @bounce12340，AI 創業、AI Agent、一人公司，台灣）的內容團隊用。照這份流程做，Claude Code 和內容製作 bot 都能直接出片。**這個 skill 只做草稿，不發文。** 發文一律交給主 bot，Josh 確認後才發。

腳本在 `<SKILLS_DIR>/stock-footage-reel/scripts/`（下面簡稱 `$S`）。範例在 `examples/`，授權查證在 `references/licenses.md`。
參考成品：`<YOUR_WORKSPACE>/media-team/03-drafts/stock-footage-test/test.mp4`。

## 內容守則（一定要遵守）
- 忠於原文：每一句都要對得回原始來源。不可以編數字、編引文；原文沒說的不要寫成原文說的。轉述就寫「整理自」。
- 標出原作者：左上標題寫來源作者和原文標題；片尾和貼文說明都要標。
- 完整重於精簡：重點講完整，不要為了短而砍掉關鍵論點。但全片要在 3 分鐘內。
- 配音語速自然，不要加速硬塞。字太多就拆成兩支或刪次要句。
- 繁體中文、台灣用語（軟體、資料、影片、網路、品質…），引號用「」，不用破折號（——），用逗號或句號。
- 英文字幕是我們的翻譯，不是原文引言；除非原文就是英文且逐字相同，否則不要加引號。
- 素材只用授權清楚、可商用的；看 `references/licenses.md`。不登入任何網站、不用付費來源、不繞過網站限制。

## 環境
- Pexels：`PEXELS_API_KEY` 已設在環境變數（**不要印出來**）。Pixabay 要 `PIXABAY_API_KEY`（目前沒有）。
- ASR 對時：`uv run --with faster-whisper`（第一次會下載套件，之後有快取）。
- 字型：`<YOUR_WORKSPACE>/media-team/00-profile/covers/fonts/` 的 Noto Sans TC／Noto Serif TC。英文 Noto Sans。
- 素材快取：`$S/../stock-footage-reel/cache/`（同一支素材不會重抓）。

## 流程

### 0. 開工作資料夾
```
D=<YOUR_WORKSPACE>/media-team/03-drafts/<題目>-reel ; mkdir -p $D/work ; cd $D/work
```

### 1. 寫 script.txt（一行＝一鏡）
每行一句口播，可以用 `[1] 文字` 格式。每行 1 到 3 個子句、大約 5 到 9 秒最好。

### 2. 配音（ElevenLabs，透過 MCP；腳本不能直接呼叫 MCP）
1. 依語言選聲：中文用 **「<YOUR_VOICE_NAME>」**，voice_id `<YOUR_ELEVENLABS_VOICE_ID>`；英文用 **Sarah Explains**，voice_id `Nhs7eitvQWFTQBsf0yiT`。用 `user-Elevenlabs` 的 `creative_list_voices` 對一下名字後再送，不要憑記憶亂換 id。
2. `creative_generate_speech`：`voice_id`、`model_id: "eleven_multilingual_v2"`、`generations_count: 1`（預設是 4，會花 4 倍點數）、`prompt` 放整份稿子（行與行之間空一行，讓自然停頓；不要放 `[1]` 編號）。不要重送同一個請求，會重複扣點。
3. 用 `creative_get_flow_run_status`（flow_id、session_ids）輪詢到 `all_completed`，拿 `media[0].url`，`curl -o vo.mp3 '<url>'`（網址 2 小時內有效）。
4. 送出的文字要和 script.txt 一字不差（對時靠這個）。
備案：ElevenLabs 不能用時 `bash $S/scripts/tts_edge.sh script.txt vo.mp3`（edge-tts zh-TW-HsiaoChenNeural），shots.json 的 `voice.provider` 改成 `"Edge TTS (zh-TW-HsiaoChenNeural)"`，片尾就會正確標示。

### 3. 對時
```
uv run -q --with faster-whisper --with numpy python $S/scripts/align.py --audio vo.mp3 --script script.txt --out timing.json
```
會印出每鏡起訖和對齊率（八成以上就正常）。鏡頭切點自動放在句間停頓中間。

### 4. 寫 shots.json（範例：`examples/satya_test.shots.json`；下面的 `//` 註解只是說明，實際檔案不能有）
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
欄位重點：
- `keywords`：英文搜尋詞，依序嘗試。寫具體畫面（"security camera", "typing keyboard close up", "server rack lights"），不要寫抽象概念。
- `archival: true`：這鏡用 Prelinger 老片，自動上洋紅調和顆粒。AYi 的做法是講「歷史、以前、傳統、1970 年代」或比喻「控管、權限、監控」時用老片，其他用現代素材。一支片至少放一兩鏡老片，風格才會出來。
- `highlight`：這鏡要變金色的詞（要和字幕裡的字完全一樣）。也可以在 `end_card.zh` 用 `[[ ]]` 標金色。
- `en`：英文字幕清單，數量要等於這鏡的字幕段數。先跑 `build.py --plan` 看自動切好的段落，再照段落寫英文。數量不對時會整句英文顯示在每段。
- `pick`：手動指定素材。`{"source":"archive","id":"<identifier>","starts":[秒,...]}`、`{"source":"mixkit","id":"23215"}`、`{"source":"commons","title":"File:xxx.webm","start":12}`、`{"source":"file","path":"/abs.mp4","license":"...","author":"..."}`、`{"source":"synth","kind":"code|terminal|grid"}`。
- 其他：`grade`（"archival"／"modern"／"none"）、`focus_x`（0 到 1，直式裁切的水平中心）、`cuts`（這鏡固定切幾段）。
- `cover.frame_shot`：封面剪報用哪一鏡的素材（取原始橫式畫面），預設第一個老片鏡頭。`ep` 照 Josh 的集數接下去。

### 5. 抓素材
```
python3 $S/scripts/fetch_footage.py --shots shots.json --work . --timing timing.json
```
- 一般鏡頭順序：Pexels（有 key）→ Pixabay（有 key）→ Mixkit（只收 Free License）→ Wikimedia Commons（PD／CC0／CC BY）→ 本機 synth 保底。
- archival 鏡頭：Internet Archive Prelinger（只收 metadata 標公有領域的）→ Commons。
- 結果寫進 `footage.json` 和 `credits.json`（每支素材的網址、作者、授權）。`note:` 開頭的行是被跳過的素材和原因。
- 挑老片段落：自動挑會避開片頭字卡和重複段落，但最好自己看一次：
  `python3 $S/scripts/fetch_footage.py --sheet archive:OnGuard1956 --work .` → 產生 `sheet_*.jpg`（每 15 秒一格，左上是秒數），用 Read 看圖挑秒數，寫進 `pick.starts`，再用 `--only <鏡號> --refresh` 重抓那一鏡。
- 好用的 Prelinger 電腦題材：`OnGuard1956`（IBM SAGE 防空電腦，1956：控制台 120s、操作員 240s/300s、開關 330s/600s、「RESTRICTED AREA」門 630s、控制室 660s）。其他可搜 `computer`、`automation`、`electronic`。
- 換素材：改 shots.json 後 `--only N --refresh`。

### 6. 剪片
```
python3 $S/scripts/build.py --shots shots.json --work . --out .. --name reel --plan   # 先看字幕段落
python3 $S/scripts/build.py --shots shots.json --work . --out .. --name reel
```
產出（在 `--out`）：`reel.mp4`（H.264／AAC，30fps，超過 45 MB 會自動降碼率重壓）、`contact_sheet.jpg`（每段中間一格＋片尾卡）、`credits.json`（含 `credit_line` 和貼文用的 `caption_credits`）、`cover_reel.png`、`cover_post.png`（B 剪報 Vox 樣板，透過 `<YOUR_WORKSPACE>/media-team/00-profile/covers/render.py`）。

畫面規格（對照 AYi 原片做的）：
- 硬切，每段 2 到 4.5 秒，畫面緩慢左右平移。老片：洋紅偏色、柔焦、顆粒、暗角。現代：壓暗、偏青藍、降飽和、暗角。
- 左上固定標題：品牌記號「●○○○ Josh｜AI 一人公司」＋來源中文標題＋英文原標題。
- 字幕：左對齊、最多兩行中文（Noto Sans TC Bold），下面一行較小的英文；重點詞金色 #E9A44A。直式版字幕底邊在 y=1490，避開 IG 下方說明文字和右側按鈕。
- 片尾卡：素材壓暗模糊，襯線大字金句（第二行金色）、英文、「── 整理自 …」、品牌記號、@bounce12340，最下方一行出處小字（例如「Archival: Prelinger Archives (Public Domain) • Footage: Pexels • Voice: ElevenLabs」）。
- 聲音：配音＋配樂側鏈壓縮（講話時音樂自動讓開），結尾 2.5 秒淡出，整體響度約 -14 到 -16 LUFS。

### 7. 交件前自己檢查
1. 用 Read 看 `contact_sheet.jpg`：每格的畫面和那句話搭不搭、字幕有沒有斷在怪地方（例如人名中間）、有沒有被 IG 介面蓋到的風險。
2. 素材裡不能有：別人的商標特寫、可辨識的人臉被放在負面語境、和文意相反的畫面、浮水印。
3. `credits.json` 每支素材都有網址和授權；有 CC BY 的，貼文說明一定要貼 `caption_credits` 那幾行。
4. 片長、檔案大小（`ffprobe`）。
5. 成品放在 `<YOUR_WORKSPACE>/media-team/03-drafts/<題目>-reel/`，回報給主 bot：片長、大小、素材來源、還要 Josh 決定的事。不發文。

## 已知限制
- Mixkit 現在免費下載的影片多數是 Restricted（只限個人非商業），腳本會自動跳過；要用要 Josh 同意。
- archive.org 偶爾很慢或回空白，腳本會重試三次；失敗時那一鏡會退回 synth，看 `note:` 訊息再補抓。
- Prelinger 老片多半是 4:3、480p，裁成直式會放大很多，靠柔焦和顆粒蓋過去；寧可挑構圖簡單、主體在中間的段落。
- 這台機器沒有 GPU，30 秒的片大約 1 分鐘出片，3 分鐘的片大約 5 到 8 分鐘。
