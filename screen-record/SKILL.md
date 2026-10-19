---
name: screen-record
description: "用 Playwright 錄「公開網頁」的操作畫面（捲動、滑過、點連結、高亮重點、章節卡），輸出 1080x1920 直式 mp4，當 Reel 的工具／網站導覽素材。觸發語：「錄一段網頁操作」「網站導覽素材」「螢幕錄影素材」「screen record」。只錄公開頁面，不登入、不發文。"
---

# screen-record：公開網頁操作錄影（Reel 素材）

Josh 2026-10-11 核准安裝，用途只有一個：錄**公開網頁**的操作畫面，當 IG Reel 的影片素材。
發文流程完全不變（IG／Threads 照舊用 box 瀏覽器那套方法），這個工具不碰發文。

## 硬規則（每次都要遵守）

1. 每次都用全新、暫存、只在記憶體裡的瀏覽器（`chromium.launch()` + `newContext()`，不給 userDataDir）。
2. **絕不**指向 box 已登入的瀏覽器設定檔；**絕不**用 `--extension`、`attach`、CDP／wsEndpoint 連到 box 瀏覽器；**絕不**載入 cookies 或 storageState；不用 `--persistent`／`--profile`。
3. 不登入任何網站、不輸入文字、不送出表單、不發文、不留言、不按讚。
4. 只錄公開頁面（http/https，不可 localhost／內網）。IG、Threads、FB 只能在「未登入」狀態看公開頁，遇到登入牆就換來源，不要嘗試登入。
5. record.mjs 內建防護：spec 出現 storageState／cookies／userDataDir／profile／cdp／extension／login／password／fill／type 等欄位直接拒絕；所有 POST／PUT／PATCH／DELETE 請求一律擋掉（log 會出現 `blocked POST ...`，正常）；拒絕點表單送出鈕；非 http(s) 或內網網址拒絕。
6. 不要為了繞過防護去改 record.mjs。真的需要登入後的畫面，停下來問 Josh。

## 已安裝

- Playwright（Node 函式庫）1.64.0：裝在本資料夾 `node_modules/`（Apache-2.0）
- Playwright CLI `@playwright/cli` 0.1.22：全域指令 `playwright-cli`（~/.local/bin，Apache-2.0）。預設 session 是記憶體設定檔，可以臨時手動看頁面、截圖；**不要**加 `--persistent`、`--profile`、`attach --extension`。
- Chromium：`npx playwright install chromium`（~/.cache/ms-playwright/chromium-1248、chromium_headless_shell-1248）
- 沒有裝 @playwright/mcp（CLI＋本腳本已足夠，Microsoft 也建議 agent 用 CLI）。

## 用法

```bash
cd <SKILLS_DIR>/screen-record
node record.mjs spec.json                 # 輸出到 spec.out
node record.mjs spec.json --out /path/x.mp4
./contact_sheet.sh x.mp4 x_sheet.jpg 4 3  # 4x3 縮圖拼板，用 Read 看
```

範例：`examples/playwright-mcp.json`（測試片：<YOUR_WORKSPACE>/media-team/03-drafts/screen-record-test/test.mp4，19.8 秒，4.1 MB）。

### spec.json

```json
{
  "url": "https://github.com/microsoft/playwright-mcp",
  "out": "<YOUR_WORKSPACE>/media-team/03-drafts/<題目>/work/screen/clip01.mp4",
  "viewport": {"width": 720, "height": 1280},
  "outSize": {"width": 1080, "height": 1920},
  "hide": [".cookie-banner"],
  "steps": [
    {"action": "chapter", "title": "Playwright MCP", "description": "github.com/microsoft/playwright-mcp", "ms": 2200},
    {"action": "scroll", "by": 500, "ms": 2000},
    {"action": "scroll", "role": "heading", "name": "Key Features", "ms": 2000},
    {"action": "highlight", "role": "heading", "name": "Key Features", "label": "Key Features", "ms": 2500},
    {"action": "hover", "text": "Getting started"},
    {"action": "click", "text": "Apache-2.0 license"},
    {"action": "goto", "url": "https://playwright.dev"},
    {"action": "wait", "ms": 1000}
  ]
}
```

- 找元素三選一：`selector`（CSS）、`role`＋`name`（最穩）、`text`（可加 `exact`）。
- `scroll`：`by` 像素，或用 `to`／`role`／`text` 捲到某元素（`offset` 預設離頂端 25%），`ms` 捲動時間（緩入緩出）。
- `highlight`：黃框＋可選標籤，`ms` 後移除。
- `chapter`：Playwright 原生章節卡（模糊背景＋標題）。
- `click`、`hover` 有 Playwright 原生 showActions：動畫游標＋目標外框＋動作說明（`"showActions": false` 可關）。
- 其他選項：`fps`（預設 30）、`crf`（預設 23）、`mobile`（手機模擬）、`colorScheme`、`locale`、`tail`、`keepWebm`。

### 畫面尺寸

Playwright 的 screencast 用 CSS 像素錄（deviceScaleFactor 不會反映到影片），所以：
- 預設 viewport 720x1280 錄，再用 lanczos 放大到 1080x1920：版面像大手機、字夠大，畫質略軟但 Reel 夠用。
- 要最銳利：`"viewport": {"width":1080,"height":1920}`（桌面版面、字比較小）。
- 要橫式錄再裁直式：`"viewport": {"width":1280,"height":720}, "cropTo916": true`（可加 `"cropX": 200` 指定裁切起點），輸出仍是 1080x1920，但只保留中間一條，通常不如直接用直式 viewport。

## 放進成片

- **stock-footage-reel**：在 shots.json 該鏡寫
  `"pick": {"source":"file","path":"/abs/clip01.mp4","license":"Screen recording of <site>","author":"<site 擁有者>"}`
- **OpenMontage（經 openmontage-house）**：當本機素材（local clip）丟進素材清單，或 screen-demo 流程的實錄來源。
- 本家規則照舊：直式 1080x1920、Sarah Explains 配音、繁中主字幕＋小字英文、B 剪報 Vox 封面、IG 成片 45 MB 以下。
- credits.json 加一筆：`{"source":"screen-record","credit":"Screen recording of <site>","url":"<網址>","recorded":"YYYY-MM-DD"}`；片尾出處寫「Screen recording of <site>」。
- 錄的是別人的網站：只當介紹／評論畫面使用，不要錄有個資、別人私訊或付費牆內容。
