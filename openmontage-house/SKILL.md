---
name: openmontage-house
description: 用 OpenMontage（開源 AI 影片製作流水線，<SKILLS_DIR>/OpenMontage）做 Josh 的影片時的「本家規則」轉接層。適用：長片剪成多支短片（clip-factory）、真實螢幕錄製教學（screen-demo）、翻譯配音（localization-dub）、Podcast 轉影片（podcast-repurpose）、「照這支參考影片做」（reference video 分析）、無旁白紀錄片蒙太奇（documentary-montage），以及幫 stock-footage-reel 加抓 NASA／國會圖書館／NARA／Archive.org 老片。觸發語：「用 OpenMontage」、「長片切短片」、「照這支 Reel 做」、「翻譯配音」、「螢幕教學影片」。
---

# openmontage-house：OpenMontage ＋ Josh 本家規則

OpenMontage 本體：`<SKILLS_DIR>/OpenMontage`（commit 9327439，2026-10-03，AGPLv3）。
本體的完整說明：`AGENT_GUIDE.md`、`CLAUDE.md`、`skills/INDEX.md`、`pipeline_defs/*.yaml`。
**這個 skill 只做草稿，不發文。** 發文一律由主 bot 在 Josh 確認後處理。

## 先決定要不要用 OpenMontage（看 <SKILLS_DIR>/INDEX.md 的決策表）
- 有口播的雙語 Reel、真實素材剪輯 → 用 **stock-footage-reel**（本家格式），不要用 OpenMontage 的 documentary-montage。需要更多老片／公有領域素材時，用下面的 `om_clips.py` 抓，再用 `pick: {"source":"file", ...}` 放進 shots.json。
- Vox／知識解說動畫 → 用 **huashu-art-motion**，不要用 OpenMontage 的 animated-explainer。
- 其他（切片、螢幕錄製、翻譯配音、Podcast、參考影片分析、無旁白蒙太奇）→ 用 OpenMontage，照下面的本家規則覆寫它的預設。

## 環境
```
source <SKILLS_DIR>/OpenMontage/om-env.sh   # 啟用 .venv 和 Node 22，並 cd 進 OpenMontage
python -c "from tools.tool_registry import registry; import json; registry.discover(); print(json.dumps(registry.support_envelope(), indent=2))"   # 看哪些工具可用
```
- 已裝：requirements.txt、Remotion composer（npm）、piper-tts、faster-whisper、yt-dlp、youtube-transcript-api、opencv-headless、HyperFrames（npx 快取 0.8.147），以及 CPU 版 torch 2.14.1＋transformers 5.19（沒有 GPU 套件）。**CLIP 語意配對可用**：corpus_builder 建素材庫後，clip_search 的 `rank_for_slot` 用文字描述排序素材（分數 0.25 以上算可用）；video_understand（CLIP 模式）也可用。第一次會從 Hugging Face 下載 CLIP 模型（openai/clip-vit-base-patch32），CPU 上一次建 5 支素材的小庫約 1 分鐘。corpus_builder 顯示 degraded 只是因為一半的素材來源沒有 key，不影響使用。
- 金鑰：`PEXELS_API_KEY`、`ELEVENLABS_API_KEY` 都是機器環境變數（新開的 shell 才會有，必要時用 `bash -lc`），om-env.sh 會沿用，.env 裡刻意不寫，**不要印出來或寫進檔案**。其他 key 全空。**不要為了 OpenMontage 去申請新帳號或付費金鑰**，要加之前先問 Josh。
- 付費生成（Kling、Veo、Seedance、FLUX 等）目前沒有 key，selector 會自動略過。OpenMontage 在花錢前會先報價，要 Josh 同意。

## 本家規則（覆寫 OpenMontage 預設，每支片都要做到）
1. 畫面：直式 1080x1920（OpenMontage 多數預設是 16:9，開工時就要指定 9:16）。3 分鐘內，完整重於精簡。
2. 配音：ElevenLabs 英文女聲 **Sarah Explains**（voice_id `Nhs7eitvQWFTQBsf0yiT`），model `eleven_multilingual_v2`。
   - 首選：OpenMontage 自己的 `elevenlabs_tts` 工具直接產生（已實測可用）。指定 `voice_id`，不要讓 tts_selector 自動挑聲音或退到 piper。範例：`ElevenLabsTTS().execute({"text":..., "voice_id":"Nhs7eitvQWFTQBsf0yiT", "model_id":"eleven_multilingual_v2", "output_path":".../vo.mp3"})`。一份稿子送一次，不要重送（會重複扣點）。
   - 備案：直接 API 失敗時，改用 user-Elevenlabs 連接器（`creative_generate_speech`，`generations_count: 1`）產生 vo.mp3，再當成現成旁白交給 OpenMontage。不要用 piper 當正式配音。
3. 字幕：繁體中文主字幕＋下方一行較小的英文（英文對應配音）。台灣用語，「」引號，不用破折號。字幕底邊不低於 y=1490，避開 IG 介面。
4. 封面：B 剪報 Vox 版型，`<YOUR_WORKSPACE>/media-team/00-profile/covers/render.py`（不要用 OpenMontage 自己的封面／縮圖）。
5. 授權：每支素材都記進 `credits.json`（網址、作者、授權）。Archive.org 的授權是「verify per item」，一定要逐支打開頁面確認是公有領域或 CC0／CC BY；BBC、電視台、電影公司的片不要用。CC BY 要在貼文說明標註。
6. 檔案：IG 成片 H.264／AAC，壓到 45 MB 以下（`ffprobe` 確認大小和片長）。
7. 內容：忠於原文，不捏造數字與引文，標註原作者。
8. 輸出：成品放 `<YOUR_WORKSPACE>/media-team/03-drafts/<題目>/`；OpenMontage 的 `projects/` 只當工作區。

## 各流程怎麼開
在 OpenMontage 資料夾開 Claude Code（它會讀 CLAUDE.md），或其他 bot 直接讀 `skills/pipelines/<流程>/executive-producer.md` 照階段做。開工第一句就把上面的本家規則貼給它。
- clip-factory：長影片（YouTube、直播、Podcast 錄影）切成多支直式短片。影片用 yt-dlp 抓前先確認 Josh 有權使用。
- screen-demo：真實螢幕錄製教學（screen_recorder／cap_recorder 可用）。
- localization-dub：把影片翻成別的語言配音。配音一樣先用 ElevenLabs 連接器產生，再交給它對時、混音。
- podcast-repurpose：Podcast 音檔轉成重點短片。
- 參考影片分析：貼一支 Reel／Short，讓它分析節奏、開場、結構，提出 2 到 3 個原創版本並估成本（animated-explainer、animation、cinematic、character-animation 有 reference_input）。只學結構，不抄畫面和文案。
- documentary-montage：無旁白或少旁白的主題蒙太奇（Adam Curtis 風），用 CLIP 語意配對自動幫每個段落挑素材。有口播的 Reel 還是用 stock-footage-reel。
- Backlot 分鏡看板：`python -m backlot open <project-id>`（本機看板，只是觀察用，失敗也不影響製作）。只是看進度和確認關卡，Josh 確認還是要回到聊天裡。

## 幫 stock-footage-reel 加抓素材
```
python3 <SKILLS_DIR>/openmontage-house/scripts/om_clips.py \
  --query "1960s computer room" --query "mission control" \
  --sources archive_org,nasa,loc,nara,wikimedia --n 3 --out $D/work/om_clips
```
印出每支的縮圖路徑和可以直接貼進 shots.json 的 `pick`（`{"source":"file",...}`），授權紀錄寫在 `om_clips/om_credits.json`。用 Read 看縮圖挑，逐支確認授權後才放進片子。
可用來源：pexels（有 key）、archive_org、wikimedia、nasa、nara、loc、coverr、pond5_pd。NASA 下載有時連線逾時（images-assets.nasa.gov），失敗會印 `note:`，換來源即可。

## 授權（AGPLv3）
拿 OpenMontage 當工具做影片、做商用貼文都可以，產出的影片不受 AGPL 限制。只有「修改它的程式碼並架成網路服務給別人用」才要公開原始碼。所以不要把改過的 OpenMontage 架成對外服務。
