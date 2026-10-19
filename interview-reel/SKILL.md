---
name: interview-reel
description: 「名人訪談／演講片段」直式 Reel（Fox Hsiao 式「解說穿插原聲」）：配音依語言選聲（中文用「<YOUR_VOICE_NAME>」<YOUR_ELEVENLABS_VOICE_ID>；英文用 Sarah Explains）＋繁中主字幕的解說段落，中間穿插 15 到 30 秒的名人原聲片段（16:9 置中、上下模糊底、「原聲 姓名｜場合｜日期」出處標籤、左上「影片／原頻道」），結尾拋問題給觀眾。一份 JSON spec 一路做到成片、720p 預覽、聯絡表、credits.json、封面。觸發語：「名人訪談」、「演講片段」、「訪談 Reel」、「Fox 式」、「解說加原聲」、「interview reel」。
---

# interview-reel：名人訪談／演講片段 Reel（Fox Hsiao 式）

Josh 2026-10-12 核准：名人訪談用 Fox 式，解說穿插 15 到 30 秒原聲片段、標出處，做成固定 skill。
**這個 skill 只做草稿，不發文。** 發文一律由主 bot 在 Josh 確認後處理。

- 腳本：`<SKILLS_DIR>/interview-reel/scripts/`（下面簡稱 `$S`）
- 範例 spec：`examples/mcp_test.spec.json`（Anthropic 官方 MCP 訪談，測試片）
- 參考成品：`<YOUR_WORKSPACE>/media-team/03-drafts/interview-reel-test/test.mp4`
- 參考影片：`<YOUR_WORKSPACE>/refs/ig-DeWJjxJyoEb/`（Fox Hsiao，馬斯克 Terafab，要學的格式）、`<YOUR_WORKSPACE>/refs/ig-DWVQfDmE41Z/`（AI郵報，黃仁勳，只放原聲，最簡單，不學它不標出處）
- 沿用：stock-footage-reel 的 common.py（字型、下載）、synth_music.py（原創配樂）、Pexels 快取；OpenMontage 的 venv（faster-whisper、yt-dlp）和 `elevenlabs_tts`；封面 `<YOUR_WORKSPACE>/media-team/00-profile/covers/render.py`。

## 格式（照 Fox Hsiao 那支拆出來的）
| 段落 | 畫面 | 聲音 |
|---|---|---|
| hook（0 到約 11 秒） | 滿版 9:16 B-roll（壓暗、慢慢推近），每 1 到 2.5 秒換一次；左上大字卡（紅色小分類標籤＋兩行粗體大字，重點字橘色） | 旁白（中文 <YOUR_VOICE_NAME>／英文 Sarah Explains）＋配樂 |
| clip（原聲，每段 15 到 30 秒，3 到 4 段） | 16:9 原片置中（y=468），上下用同一畫面模糊壓暗補滿；原片左上小字「影片／原頻道」；原片下方紅色「原聲」標籤＋「英文名　中文名或身分」＋「場合｜YYYY.MM.DD」 | **只放原音**，旁白不疊；配樂壓得更低（clip_music_db）再加側鏈閃避 |
| explainer（解說，穿插在原聲之間） | 同 hook，字卡換成事實卡，下方小字標「來源：誰｜日期」；每 2 到 3.2 秒換畫面 | 旁白（中文 <YOUR_VOICE_NAME>／英文 Sarah Explains）＋配樂 |
| outro | 置中大問題（重點字黃色）＋品牌記號＋@bounce12340＋最下方一行出處小字 | 旁白問觀眾（中文 <YOUR_VOICE_NAME>／英文 Sarah Explains） |

全片共用：上方固定標題列（品牌記號＋一句標題，重點字橘色）；字幕置中，繁中大字（白、粗、淡陰影，重點字黃色）＋下面一行小字英文。解說段的英文就是旁白原文；原聲段的英文是講者原話的轉錄，中文是我們的翻譯。

## 本家規則（一定要遵守）
- 1080x1920、3 分鐘內、IG 成片 45 MB 以下（超過會自動降碼率重壓）、H.264／AAC。
- 旁白：依語言選 ElevenLabs 聲音。中文用 **「<YOUR_VOICE_NAME>」**（`<YOUR_ELEVENLABS_VOICE_ID>`）；英文用 **Sarah Explains**（`Nhs7eitvQWFTQBsf0yiT`）。模型 `eleven_multilingual_v2`，用 OpenMontage 的 `elevenlabs_tts`。金鑰是機器環境變數 `ELEVENLABS_API_KEY`（用 `bash -lc` 才會帶到），**不要印出來或寫進檔案**。
- 字幕：繁體中文主字幕＋小字英文。台灣用語（軟體、資料、影片、網路、運算資源…），引號用「」，**不用破折號**（build.py 會擋）。
- **解說要占多數**：原聲合計建議 40% 以下，超過 50% build.py 直接擋下。每段原聲最多 30 秒（prep_clips.py 會擋），建議 15 到 30 秒。
- 原聲段不疊旁白、不改講者原話；中文翻譯要忠於原意，不要替講者加結論。
- 忠於原文：解說裡的數字、日期都要回到一手出處，字卡用 `cite` 標「來源：誰｜日期」，並寫進 facts.md。
- 結尾一定要拋一個問題給觀眾（outro.question 要有「？」）。
- 封面用 covers/render.py，`cover.template` 預設 `"E"`（人物大頭，Josh 稱「D 人物大頭」）。Josh 2026-10-12 前已定：名人訪談一律用此版型。

## 素材來源與授權（寫進每支片的 credits.json）
1. **優先官方來源**：公司官方頻道（Anthropic、OpenAI、NVIDIA、Microsoft…）、活動主辦方（GTC、Build、TED…）、Podcast 自己的頻道。spec 的 `channel` 要寫原頻道名，prep_clips.py 會和 YouTube 的 channel 欄位比對，不一致會警告。
2. **絕不使用轉貼／有別人浮水印的版本**（例如粉專重新上傳、別的帳號剪好的片段、加了別人 logo 的版本）。找不到官方版就不要做這一段。
3. **一定要畫面標出處**：原聲下方「原聲 姓名｜場合｜日期」＋左上「影片／原頻道」，片尾小字再標一次，貼文說明貼 `credits.json` 的 `caption_credits`。
4. credits.json 會自動記：來源網址、頻道、頻道網址、影片標題、上傳日期、剪用的起訖時間（source_in／source_out）、在成片的位置、B-roll 每支的網址與作者、配音、配樂。
5. **授權說明**：這些訪談畫面的著作權屬原頻道，我們沒有取得授權，靠的是「評論、引用」的合理使用（台灣著作權法第 52、65 條），**屬於灰色地帶**。所以：每段剪短、整支以 Josh 的評論和整理為主（轉化性）、原聲只當佐證；不要整段搬運、不要剪成講者沒講過的意思。
6. **不可暗示背書**：不寫「某某推薦」「官方合作」這類字；封面、標題不要讓人以為講者支持 Josh 或他的產品。
7. 下載：只用 yt-dlp 抓**公開**影片，不登入、不帶 cookies、不繞過付費牆或地區限制。這台機器上 YouTube 的 `--download-sections` 會 403，所以 prep_clips.py 會抓整支（1080p 以下）快取在 `cache/sources/`，再用 ffmpeg 切。
8. 原頻道要求下架或 Josh 不放心時，就換成只用文字引述，不放畫面。

## 流程
```
D=<YOUR_WORKSPACE>/media-team/03-drafts/<題目>-interview ; mkdir -p $D/work
cp $S/../examples/mcp_test.spec.json $D/spec.json      # 改成這次的內容
bash -lc "source <SKILLS_DIR>/OpenMontage/om-env.sh >/dev/null; cd $S; python prep_clips.py --spec $D/spec.json --work $D/work"
```
1. **選片段**：先讀原片的章節（yt-dlp `--print description`），在官方影片裡挑 15 到 30 秒、講者自己把重點講完整的一段。轉錄用 `prep_clips.py`；只想先試聽可以先抓整支再用 ffmpeg 切一小段聽。
2. **prep_clips.py**：下載、切片、轉錄（faster-whisper `medium`，CPU 20 秒片段約 10 秒）。會印出 `"subs"` 樣板：把它貼回這段 clip，`zh` 翻成台灣繁中，可以合併或拆段（`t` 是相對片段起點的秒數）。英文照講者原話，轉錄有疑問的字要再聽一次或換模型交叉比對（`--retranscribe --model small`）。
3. **tts.py**：每行一個音檔，同一句文字只送一次（以文字雜湊快取在 `cache/tts/`）。先 `--dry-run` 看要送幾個字元。失敗時的備案：user-Elevenlabs 連接器 `creative_generate_speech`（`generations_count: 1`），存到它印出的快取路徑。
4. **fetch_broll.py**：每個關鍵字從 Pexels 抓 3 支（橫式優先，關鍵字比較準）。寫具體畫面（"server rack lights"、"programmer coding"），不要寫抽象詞。也可以在 line 裡給 `"image"`（靜態圖，會慢慢推近）或 `"file"`（例如 screen-record 錄的網頁）。
5. **build.py --check**：印出片長、原聲占比、每段字幕時間，以及規則警告。
6. **build.py**：出片。或整套一次跑：`bash $S/run.sh $D/spec.json $D <name>`（要先把 subs 翻好）。

## spec 欄位
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
- `en`／`zh` 可以是字串或等長清單（清單＝同一句旁白分幾段字幕，時間照英文字數比例分）。
- `card` 在同一段落裡會沿用到下一句，直到換新卡；`"card": false` 清掉。
- `zh` 太長會自動在「，」斷成兩行；要自己斷就用 `\n`。重點字用 `[[ ]]` 或 `hl` 清單。
- `cover.frame`：封面用第幾段原聲的第幾秒（原始 16:9 畫面）。E 樣板的其他欄位（`photo_side`、`visual_pos`、`brightness`、`tag`）照 covers/README.md。
- 中文名：講者有通用中文譯名就寫（例：黃仁勳、馬斯克），沒有就寫身分（例：「MCP 共同創造者」），不要自己音譯。

## 產出（OUT）
`<name>.mp4`、`preview_720p.mp4`（給 Josh 在聊天裡看）、`contact_sheet.jpg`（每個鏡頭中間一格）、`credits.json`、`timeline.json`、`cover_reel.png`／`cover_post.png`、`cover_spec.json`。

## 交件前自己檢查
1. 用 Read 看 contact_sheet.jpg：字卡、字幕、原聲標籤有沒有重疊、被 IG 介面蓋到（上 220px、下 380px、右 130px）。
2. 原聲字幕：英文對得上講者原話、中文沒有扭曲意思；有轉錄不確定的字要標給 Josh 聽。
3. `ffprobe` 看片長、大小；原聲占比看 build.py 最後一行。
4. credits.json 的 interview_clips 每段都有網址、頻道、起訖時間；確認是官方頻道。
5. 回報主 bot：檔案路徑、片長、大小、原聲來源與授權說明、要 Josh 決定的事。不發文。

## 已知限制
- 這台機器的 faster-whisper：`*.en` 模型（small.en 等）轉出來是亂碼，用多語 `medium`／`small`；PyAV 版本不相容，音訊要用 numpy 餵（腳本已處理）。同一段話不同模型偶爾會漏字，關鍵句要交叉比對。
- YouTube `--download-sections` 會 403，只能整支下載（長訪談 1080p 可能幾百 MB，快取在 cache/sources/，用完可以刪）。
- 沒有 GPU：1 分鐘的片約 2 分鐘出片，3 分鐘的片約 6 到 8 分鐘。
- Pexels 關鍵字結果有時不準，看聯絡表再換關鍵字或用 `image`／`file`。
