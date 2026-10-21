# opus-5-5-prompts：Claude Opus 5.5 爆紅影片 prompt 參考清單

這不是新的 skill，而是一份參考清單，給 josh-video-router 和各影片 skill 找「程式渲染影片」靈感用。只做草稿，不發文。

## 來源與授權

- 來源：[yihui-dev/awesome-opus5-5-videos](https://github.com/yihui-dev/awesome-opus5-5-videos)（2026-10-21 抓取，703 筆 prompt）。
- 來源 repo 的 LICENSE 是 MIT（Copyright (c) 2026 yihui-dev），但它的 README〈Credits〉寫明「每支影片和 prompt 都屬於原作者」。MIT 只能確定涵蓋 repo 本身的整理，不一定涵蓋各作者寫的 prompt。
- 所以這裡**不複製任何 prompt 原文**，只放標題、分類、技術標籤、作者、原貼文連結和指向來源 repo 的 prompt 連結。要用某個 prompt，請到來源 repo 讀原文，並遵守原作者的意思。
- 來源 repo 也在幫 Skillry 網站導流（每筆都附 Skillry 重做版連結），本清單沒有收那些連結。

## 比對結果（自動初判）

`catalog.md` 把每筆 prompt 跟本 repo 和 INDEX.md 已收的 skill／風格比對，分三類：

| 結果 | 筆數 | 意思 |
|---|---|---|
| 新 | 204 | 本 repo 沒有對應：主要是 Three.js 3D 場景、shader、可互動小遊戲 |
| 部分重疊 | 375 | 同類流程已有 skill（lemo-opuscar、huashu-art-motion、xilo-opus-video、OpenMontage 圖表），但沒有同款風格 |
| 重複 | 124 | 跟現有風格相同或幾乎相同（例如 lemo dark-keynote 21 筆、pixel-rpg 13 筆、ascii-crt 10 筆），或來源 repo 內 prompt 重複（23 筆） |

比對是用關鍵字做的，會有誤判，用之前請人工確認。

## 怎麼用

1. 要做 3D 場景、shader 視覺或互動小遊戲錄影時，先看 `catalog.md` 的「新」區。
2. 點 prompt 連結讀原文，用自己的話改寫成這支影片的需求，套用本家規則（直式 1080x1920、台灣繁中、「」引號、不用破折號、配音照字幕念、不放品牌 logo）。
3. 要錄成影片：讓模型輸出單一 HTML 檔，用 screen-record 或 lemo-opuscar 的逐格渲染出片。
4. 片尾或說明欄標出靈感來源作者。

## 重新產生清單

```bash
git clone --depth 1 https://github.com/yihui-dev/awesome-opus5-5-videos
python3 opus-5-5-prompts/build_catalog.py awesome-opus5-5-videos
```
