# 素材來源與授權（2026-10-11 實際查證）

| 來源 | 怎麼抓 | 授權（查到的原文重點） | 能不能用在 @bounce12340 |
|---|---|---|---|
| Pexels | 官方 API `api.pexels.com/videos/search`，要 `PEXELS_API_KEY`（免費） | Pexels License：免費、可商用、可修改，不需標註但歡迎標註；不能把素材原樣轉賣、不能暗示被拍攝者代言 | 可以，主力來源。credits.json 記攝影師與網址 |
| Pixabay | 官方 API，要 `PIXABAY_API_KEY`（目前沒有） | Pixabay Content License：免費可商用、不需標註 | 可以（有 key 才會啟用） |
| Mixkit | 搜尋頁 `mixkit.co/free-stock-video/discover/<詞>/` 加項目頁；robots.txt 全站 Allow（只擋 CCBot）；每次請求間隔 2 秒，最多看 4 個項目頁 | 有兩種影片授權。**Free License**：可商用、社群貼文、廣告。**Restricted License**：只限個人、非商業；明文不可用在「公司社群貼文」或「替你賺錢的生意做行銷」。2026-10-11 抽查 12 支影片（server、hacker 兩個分類），免費下載的 720p 全部標成 Restricted，商用要付費走 Envato | 腳本預設只收 Free License，Restricted 會自動跳過。要用 Restricted 需加 `--allow-mixkit-restricted`，**這要 Josh 決定** |
| Mixkit 音樂 | 同上 | Stock Music Free License：可用在社群影片、廣告、YouTube；不可用在 CD/DVD、電視廣播、遊戲；不可單獨 remix 成音樂 | 可以（目前預設改用自己合成的配樂） |
| Internet Archive／Prelinger | `archive.org/advancedsearch.php`＋`archive.org/metadata/<id>`，下載一次就快取 | Prelinger 收藏多數標 `creativecommons.org/licenses/publicdomain/`（公有領域）。**有些項目 metadata 沒寫授權**，腳本只收有標公有領域的 | 可以；片尾標「Archival: Prelinger Archives (Public Domain)」 |
| Wikimedia Commons | MediaWiki API，`filetype:video` 搜尋 | 只收 Public domain／CC0／CC BY（CC BY 一定要標作者、授權、網址；CC BY-SA 預設排除） | 可以，但現代 B-roll 很少，當備案 |
| synth_broll.py | 本機產生程式碼捲動、終端機、格線 | 自己做的 | 都找不到時的保底 |
