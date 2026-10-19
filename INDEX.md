# 影片 Skill 索引（來源：@xaiwind〈Codex 爆款视频skill，10个装完百万播放〉，2026-10-10）

位置：每個 repo 都是 <SKILLS_DIR>/<repo>/ 底下的一般資料夾；Claude Code 從 ~/.claude/skills/<skill名> 的 symlink 讀取（共用這台機器的 bot 都能直接讀 SKILL.md）。
呼叫方式：在 Claude Code 裡講出觸發語，或輸入 /<skill名>；其他 bot 直接讀該路徑下的 SKILL.md 照流程做。
Node 22：放在 <YOUR_WORKSPACE>/tools/node22/bin（系統預設仍是 Node 20）。需要 Node 22 的工具先執行 `export PATH=<YOUR_WORKSPACE>/tools/node22/bin:$PATH`。hyperframes 已包成 wrapper，會自動使用 Node 22。
已裝好的共用相依套件：ffmpeg、uv、Playwright Chromium、Pillow、imageio-ffmpeg、requests、yt-dlp、edge-tts、HyperFrames CLI 0.8.145、Remotion（investigation 範本）。


## 先看這裡：哪種影片用哪個 skill（2026-10-11 合併 OpenMontage 後）

每種流程只有一個首選。本家規則（所有影片都要做到）：直式 1080x1920、配音依語言選聲（中文用你自己的 ElevenLabs 聲音「<YOUR_VOICE_NAME>」<YOUR_ELEVENLABS_VOICE_ID>；英文用 Sarah Explains Nhs7eitvQWFTQBsf0yiT；OpenMontage 用它的 elevenlabs_tts 直接產生，連接器當備案）、繁中主字幕＋小字英文、依題材挑封面（<YOUR_WORKSPACE>/media-team/00-profile/covers/render.py；新聞事件用模板 D 新聞海報、名人訪談用 E 人物大頭、工具教學用 F 亮底資訊卡，Josh 口中叫 C／D／E；B 剪報只在指定時用）、credits.json 授權紀錄、IG 成片 45 MB 以下、台灣用語。用 OpenMontage 時先讀 openmontage-house，它會把這些規則套上去。

| 要做的影片 | 首選 | 不要用（重複） | 備註 |
|---|---|---|---|
| 有口播的真實素材 Reel（AYi 紀錄片風） | stock-footage-reel | OpenMontage documentary-montage | 要 NASA／LOC／NARA／Archive.org 素材時，用 openmontage-house/scripts/om_clips.py 抓，再用 pick file 放進來 |
| 無旁白／少旁白的主題蒙太奇（Adam Curtis 風） | OpenMontage documentary-montage（經 openmontage-house） | 無 | CLIP 語意配對可用（CPU torch） |
| 資料卡（價格、成本、跑分對比）程式動畫 | huashu-art-motion templates/data_card_render.py | 靜態 PNG 字卡 | 2026-10-15 起照 00-profile/motion-contract.md；只用在資料卡 |
| Vox／知識解說動畫、藝術畫風短片 | huashu-art-motion | OpenMontage animated-explainer、vox-director | animated-explainer 的好畫面要付費生圖；vox-director 要付費 ATLASCLOUD key |
| 程式渲染的特殊風格短片（浮世繪、像素、藍圖等 39 種） | lemo-opuscar | OpenMontage animation | 要 huashu 沒有的風格才用 |
| 資料圖表、KPI 卡片類動畫 | OpenMontage（Remotion 元件，免 key，已實測出片） | 無 | lemo 的 dataviz 風格也可以，二選一看畫面 |
| 長影片切成多支短片 | OpenMontage clip-factory | 無 | 新能力 |
| 名人訪談／演講片段（Fox Hsiao 式：解說穿插 15 到 30 秒原聲、標出處） | interview-reel | OpenMontage clip-factory（那是長片切短片，沒有解說）、AI郵報式整段原聲搬運 | Josh 2026-10-12 核准；只用官方頻道公開影片（yt-dlp，不登入），原聲每段 30 秒內、合計低於一半；credits.json 記來源網址、頻道、起訖時間；合理使用屬灰色地帶，見 SKILL.md |
| 工具／網站導覽素材（錄公開網頁的捲動、點擊、高亮畫面） | screen-record | lemo living-screencast（那是模擬畫面） | 只錄公開頁、暫存瀏覽器、不登入；輸出 1080x1920 mp4，用 pick file 放進 stock-footage-reel 或當 OpenMontage 本機素材；credit「Screen recording of <site>」 |
| 真實螢幕錄製教學 | OpenMontage screen-demo（網頁畫面用 screen-record 錄） | 無 | lemo 的 living-screencast 是「模擬」螢幕，不是實錄 |
| 翻譯配音（影片換語言） | OpenMontage localization-dub | 無 | 配音用它的 elevenlabs_tts（中文用 <YOUR_ELEVENLABS_VOICE_ID>，英文用 Sarah Explains），連接器備案 |
| Podcast 轉影片 | OpenMontage podcast-repurpose | 無 | 新能力 |
| 「照這支參考 Reel 做」：分析節奏結構、出 2 到 3 個原創版本 | OpenMontage 參考影片分析 | dbskill dbs-deconstruct／dbs-benchmark（只做文字，且限非商用） | 只學結構，不抄畫面和文案 |
| 出片前的分鏡確認 | 各 skill 自己的關卡（stock-footage-reel 的 --plan＋contact_sheet；OpenMontage 的 Backlot 看板） | 無 | Josh 的確認一律回到聊天裡 |
| 封面 | 依題材：新聞 D／名人 E／教學 F（covers/render.py，見 covers/README.md 2026-10-12 規則） | Punk-Skill（只在要別種封面時用）、OpenMontage 縮圖 | |
| 不露臉長篇調查片（10 分鐘以上） | simon-skills investigation-video | 無 | 要火山 TTS key，目前不能出片 |

已標為不建議使用（資料夾保留，不會壞）：無。這次比對下來，我們現有的 skill 沒有一個被 OpenMontage 完全取代；重複的部分都是「OpenMontage 那一條不用」，所以是在上表標「不要用」。


- huashu-art-motion｜35 種藝術畫風卡＋9 種解說影片語法，用 HTML 動畫加 TTS 做知識影片｜<YOUR_WORKSPACE>/tools/huashu-art-motion（skills/ 底下有 symlink）｜/huashu-art-motion｜之前就裝好了，這次沒有重裝
- vox-director｜Vox 剪報拼貼風解說／廣告片：一個主題一路做到腳本、拼貼關鍵影格、動態、配音、配樂、字幕｜vox-director/｜/vox-director、「做一支 vox 風影片」｜需要 ATLASCLOUD_API_KEY（Atlas Cloud，付費）
- hand-drawn-video-prompts｜把中文口播稿拆成 9:16 手繪蠟筆風 B-roll 分鏡和 Nano Banana／Flow 提示詞，也可以接著做成完整影片｜hand-drawn-video-prompts/hand-drawn-video-prompts/｜/hand-drawn-video-prompts｜提示詞模式不需要 key；成片要自己準備生圖、生影片工具（Google Flow 等）
- directing-stickman-videos（stickman-video-director）｜火柴人極簡英文影片導演，產出 Gemini Omni Flash／Google Flow 用的分鏡提示詞包｜stickman-video-director/skills/directing-stickman-videos/｜/directing-stickman-videos｜不需要 API key；出片會消耗 Google Flow 點數（Google AI Pro）。SKILL.md 的 YAML 已在本機修正（description 加上引號）
- kid-papercraft｜問 5 個問題，產出 3 段 10 秒兒童摺紙風生日祝福短片提示詞｜kid-papercraft/skills/kid-papercraft/｜/kid-papercraft｜不需要 key；使用卡通 IP，README 有非商用免責聲明
- classical-poem-silk-video（hbg-classical-poem-silk-video）｜把古詩詞做成絲綢質感的直式國畫影片，搭配書法逐字字幕｜hbg-classical-poem-silk-video/skill/classical-poem-silk-video/｜/classical-poem-silk-video｜還不能出片：需要 Docker 加上 gemini-flow-suite 容器（要匯入 Google 帳號 Cookie，這次刻意跳過），生圖則需要 GPT ImageGen
- hbg-life-simulation｜把長文案做成固定漫畫主角的「人生副本」旁白影片，用 Edge TTS、HyperFrames 推拉運鏡，最後跑 MP4 品質檢查｜hbg-life-simulation/｜/hbg-life-simulation｜需要生圖能力（Codex ImageGen 或其他）；CLIProxyAPI OAuth 代理沒有裝。預設輸出 1920×1080 橫式，做直式短影音要記得改。相依的 hyperframes、hyperframes-cli、hyperframes-core、media-use 這幾個 skill 已連結
- investigation-video（simon-skills）｜不露臉的商業／消費調查長片：選題、事實查核、10 分鐘以上的敘事、配音字幕、封面和各平台文案｜simon-skills/skills/investigation-video/｜/investigation-video｜需要 VOLC_TTS_APP_ID、VOLC_TTS_ACCESS_TOKEN（或 VOLC_TTS_API_KEY），也就是火山引擎 TTS；Remotion 範本已 npm install，渲染測試通過
- whiteboard-video（simon-skills）｜Excalidraw 白板「邊畫邊講」影片，用 wb CLI 一條龍產出｜simon-skills/skills/whiteboard-video/（bin/wb）｜/whiteboard-video 或 `bin/wb --help`｜需要火山 TTS 的 key（同上）；`wb image` 需要 codex CLI（沒裝）
- video-common（simon-skills）｜上面兩個共用的事實查核、封面驗收、文案、成片驗收工序｜simon-skills/skills/video-common/｜不會直接觸發，由上面兩個 skill 引用｜不需要 key
- director｜科普影片導演，有動畫解說、故事動畫、劇情影像三種模式，從劇本做到分鏡和生成提示詞｜director/｜/director｜要出畫面得裝好並登入 LibTV CLI 或即夢 dreamina CLI（都要登入帳號、會扣點數，這次沒裝）
- book-sales-video｜輸入書名，自動做出圖書帶貨／書評短影片｜book-sales-video/｜/book-sales-video｜需要 DOUBAO_API_KEY（還要 resource ID 和 speaker）、PEXELS_API_KEY、WEREAD_API_KEY，以及 OpenChatCut 桌面版（macOS）和飛書 lark-cli（要互動設定）；weread-skills 已連結
- native-subtitle-quote-image｜從影片精準擷取畫面，拼成帶字幕的長圖或金句圖（3:4）｜native-subtitle-quote-image/skills/native-subtitle-quote-image/｜/native-subtitle-quote-image｜不需要 key，環境檢查已通過（本機影片、YouTube URL 模式都能用）
- creator-buddy（33 個 skill）｜公眾號、小紅書、影片創作全流程：熱點、爆款分析、標題、長短文、封面、排版、腳本、剪輯、字幕｜creator-buddy/（gzh-Skills、xhs-Skills、video-Skills）｜/creator-buddy、/space-xhs-buddy、/space-video 等｜搜尋類要 GUAIKEI_API_TOKEN、REDFOX_API_KEY、SOCIALDATAX_API_KEY；space-video-transcript 要 GROQ_API_KEY；space-video-broll-sketch 要 ARK_API_KEY 和 LIBTV_ACCESS_KEY；space-chart-image 要 LABNANA_API_KEY。repo 沒有 LICENSE 檔
- dbskill（37 個 skill）｜dontbesilent 商業與內容工具箱：選題、鉤子、標題封面、AI 味檢查、對標、診斷等文案上游工具｜dbskill/skills/｜/dbs（總入口）｜一般寫作不需要 key；dbs-video-extract 要 TIKHUB_API_KEY 或 QINGDOU_API_KEY。授權是 CC BY-NC 4.0，限非商用
- impeccable｜網頁／介面設計品味與排版檢查，24 個指令、59 條免金鑰檢查規則｜impeccable/｜/impeccable｜不需要 API key；launcher 首次執行會從官方 GitHub releases 下載 engine
- lemo-opuscar｜純程式渲染的風格短片導演（Canvas／WebGL 逐格渲染，配 TTS、程式配樂、混音），原本 43 種風格，跟 huashu 重複的水墨、白板、皮影戲、橡皮管卡通 4 種已略過，留 39 種｜lemo-opuscar/（~/lemo-opuscar 和 ~/.claude/skills/lemo-opuscar 都是 symlink，不會重新下載）｜/lemo-opuscar 或「用 ○○ 風格做一支短片」｜核心不需要 key；預設 1920×1080，做直式 Reel 加 `--size 1080x1920`（已實測可行，但各風格的範例是照橫式設計，構圖要重排）。中文配音可用 core/tts/tts_zh.py（edge-tts）或 ElevenLabs；`deps voice`（Kokoro 英文模型約 350 MB）和 `deps music`、樂器取樣庫（tools/fetch.sh，來源是 GitHub Releases）都還沒裝。略過清單見 lemo-opuscar/skipped_styles.md
  - 新增風格（39）：蠟筆兒童繪本 crayon-book｜水彩筆刷 watercolor｜油畫厚塗 impasto｜一筆畫 one-line｜鋼筆淡彩 urban-sketch｜浮世繪 ukiyoe｜紅色窗花剪紙 papercut-red｜紙雕燈影 paper-lantern｜Risograph 孔版印刷 risograph｜復古半調案卷 halftone-dossier｜木刻版畫 woodcut｜銅版畫 engraving｜絲印旅行海報 silkscreen-poster｜瑞士動態排版 swiss-motion｜60 年代間諜片頭 spy-titles｜裝飾藝術 art-deco｜藍圖工程製圖 blueprint｜彩色玻璃窗 stained-glass｜象形運動圖形 pictogram-motion｜ASCII／CRT 終端機 ascii-crt｜數據敘事 dataviz｜等距資訊圖 iso-infographic｜暗色科技發表 dark-keynote｜活體實機錄屏 living-screencast｜科幻全像介面 hologram-hud｜80 年代賽璐珞動畫 cel-anime-80s｜科幻情境喜劇卡通 scifi-toon｜50 年代扁平卡通 midcentury-toon｜16-bit 像素 RPG pixel-rpg｜HD-2D hd-2d｜微遊戲快閃 microgame｜綜藝節奏扁平 game-show｜1920 年代默片 silent-film｜後室／新怪談偽紀錄片 backrooms｜積木玩具 brick-toy｜紙片立體書 paper-popup｜移軸微縮 tilt-shift｜低多邊形等距島嶼 lowpoly-island｜玻璃質感產品 glass-product
- Punk-Skill（punk-cover、punk-avatar）｜Adrian Punk 的封面／頭像提示詞系統，已固定在 MIT 授權版 v1.0.0-mit（2026/9/7，38 種風格），依平台比例組出生圖提示詞｜Punk-Skill/（git checkout v1.0.0-mit，請勿 git pull 到 v2；~/.claude/skills/punk-* 是 symlink）｜/punk-cover、/punk-avatar｜MIT 授權可商用、可修改，需保留版權聲明；不需要 API key，出圖要另接生圖工具（會花點數）。v2 才有的小紅書人物 IP 影片封面 punk-ip-video-cover 已移除。Josh 的封面依題材挑選（見 <YOUR_WORKSPACE>/media-team/00-profile/covers/README.md），B 剪報只在指定時用
- stock-footage-reel（首選：有口播的真實素材 Reel）｜真實素材剪輯 Reel（AYi 紀錄片風）：照口播稿每句自動抓 Pexels 現代素材和 Prelinger 公有領域老片，硬切、洋紅／青藍調色、雙語字幕（重點字金色）、ElevenLabs 配音（中文用「<YOUR_VOICE_NAME>」<YOUR_ELEVENLABS_VOICE_ID>；英文用 Sarah Explains Nhs7eitvQWFTQBsf0yiT）、合成配樂、片尾金句卡和出處，封面依題材挑（covers/README.md）｜stock-footage-reel/｜/stock-footage-reel、「做一支真實素材剪輯」｜Pexels 用 PEXELS_API_KEY（已設）；Mixkit 只收 Free License，免費 720p 多為 Restricted（個人非商用）會自動跳過；Josh 自己做的 skill，可商用
- OpenMontage｜開源 AI 影片製作流水線（給 Claude Code 用）：12 條流程（documentary-montage、animated-explainer、animation、clip-factory、screen-demo、localization-dub、podcast-repurpose、talking-head、avatar-spokesperson、cinematic、character-animation、hybrid）、參考影片分析、Backlot 分鏡看板、16 個素材來源轉接（Pexels、Archive.org、NASA、NARA、LOC、Wikimedia…）｜OpenMontage/（git commit 9327439，2026-10-03，請勿任意 git pull）；本家規則轉接層 openmontage-house/（~/.claude/skills/openmontage-house 是 symlink）｜/openmontage-house、「用 OpenMontage」、「長片切短片」、「照這支 Reel 做」、「翻譯配音」｜先 `source OpenMontage/om-env.sh`（venv＋Node 22）。已裝 requirements、Remotion（npm）、piper-tts、faster-whisper、yt-dlp、youtube-transcript-api、opencv-headless、HyperFrames；另裝 CPU 版 torch＋transformers（沒有 GPU 套件），CLIP 語意配對（corpus_builder＋clip_search rank_for_slot）和 video_understand 可用，已實測排序正確。金鑰：PEXELS_API_KEY、ELEVENLABS_API_KEY 都沿用機器環境變數（.env 不寫）。配音可以直接用 OpenMontage 的 elevenlabs_tts（中文指定 <YOUR_ELEVENLABS_VOICE_ID>，英文指定 Sarah Explains Nhs7eitvQWFTQBsf0yiT）產生，已實測；ElevenLabs 連接器保留當備案。付費生成（Kling、Veo、FLUX 等）沒有 key。免 key 示範片已實測出片（projects/demos/renders/code-to-screen.mp4，1920x1080、25 秒）。授權 AGPLv3：當工具用、做商用影片都可以，影片不受限；只有修改程式碼並架成網路服務給別人用才要公開原始碼
  - 新增風格（2）：clean-professional（企業／SaaS 解說，白底藍色）｜flat-motion-graphics（社群用扁平動態圖形，深底紫粉）。略過重複的 3 種：anime-ghibli（＝huashu 25_ghibli）、minimalist-diagram（≈huashu 3b1b／whiteboard 語法）、premium-minimalist（≈huashu keynote_ui、lemo dark-keynote）
- openmontage-house｜OpenMontage 的本家規則轉接層：什麼時候用 OpenMontage、怎麼套 9:16／配音依語言選聲（中文 <YOUR_VOICE_NAME>、英文 Sarah Explains）／雙語字幕／依題材挑封面／credits／45 MB，以及 om_clips.py（幫 stock-footage-reel 從 OpenMontage 素材來源抓片並輸出 pick）｜openmontage-house/｜/openmontage-house｜不需要新 key
- screen-record｜用 Playwright 錄公開網頁操作（捲動、滑過、點連結、高亮、章節卡、動畫游標），JSON spec 一鍵出 1080x1920 mp4＋縮圖拼板，當工具／網站導覽素材｜screen-record/（record.mjs、contact_sheet.sh、examples/）｜/screen-record、「錄一段網頁操作」「網站導覽素材」｜Josh 2026-10-11 核准，只錄公開頁：暫存記憶體瀏覽器，絕不接 box 已登入的瀏覽器、不載 cookies、不登入、不送表單（腳本會擋 POST）。Playwright 1.64.0（本資料夾 node_modules）、Playwright CLI 0.1.22（playwright-cli）、Chromium 1248，皆 Apache-2.0；不需要 key。發文流程不變
- interview-reel（首選：名人訪談／演講片段）｜Fox Hsiao 式訪談 Reel：配音依語言選聲（中文用 <YOUR_ELEVENLABS_VOICE_ID>，英文用 Sarah Explains）＋繁中字幕的解說段落，穿插 15 到 30 秒官方原聲（16:9 置中、模糊底、「原聲 姓名｜場合｜日期」、「影片／原頻道」），結尾問觀眾；JSON spec → prep_clips.py（yt-dlp＋faster-whisper medium 轉錄）→ tts.py（OpenMontage elevenlabs_tts，逐句快取不重複扣點）→ fetch_broll.py（Pexels）→ build.py（規則檢查、成片、720p 預覽、聯絡表、credits.json、covers/render.py 封面，預設 E 人物大頭）｜interview-reel/（SKILL.md、scripts/、examples/mcp_test.spec.json）｜/interview-reel、「名人訪談」「演講片段」「Fox 式」｜不需要新 key（沿用 ELEVENLABS_API_KEY、PEXELS_API_KEY）。範例 spec 用的是 Anthropic 官方 MCP 訪談（測試片已依 Josh 要求刪除）。訪談畫面未取得授權，靠評論引用的合理使用，屬灰色地帶
