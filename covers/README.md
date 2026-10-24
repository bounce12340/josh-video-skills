# covers: cover generator

`render.py` draws the video covers for stock-footage-reel and interview-reel. Each run writes the main cover plus **3 to 6 cover options** and a comparison sheet, so Josh can pick one before posting.

## Setup

```bash
python covers/fetch_fonts.py   # downloads Noto Sans TC / Noto Serif TC / Noto Sans (SIL OFL) into covers/fonts/
```

The fonts are about 30 MB, so they are not committed. The build scripts read `COVERS_DIR`; it defaults to this folder.

## Templates

Pick the main cover by topic (Josh's rule from 2026-10-12): news events use **D**, celebrity interviews use **E**, tool tutorials use **F**; use **B** only when asked. Josh calls D / E / F 「C / D / E」 in conversation. G and H are extra options for the comparison sheet.

| Code | Name | Notes |
|---|---|---|
| B | 剪報 Vox (clipping) | Paper background, tilted clipping with tape, yellow marker highlight. Only when asked |
| D | 新聞海報 (news poster) | Yellow background, inverted highlight box, black-and-white photo. News events |
| E | 人物大頭 (big portrait) | Full-bleed photo, dark bottom gradient, yellow highlight. Celebrity interviews (interview-reel default) |
| F | 淺色資訊卡 (light info card) | White background, circular photo, centered serif title with underline. Tool tutorials |
| G | 黑底雜誌 (black magazine) | Black background, large serif title, duotone photo strip. Extra option |
| H | 上圖下字 (photo over text) | Photo on top, navy text panel, kicker on the seam. Extra option |

## Usage

```bash
python render.py cover_spec.json            # main cover + options + comparison sheets
python render.py cover_spec.json --pick D   # after Josh picks: make D the main cover
```

Spec fields: `template` (main cover, default B), `variants` (3 to 6, or a list such as `["B","E","F"]`; falls back to `COVER_VARIANTS`, default 6), `ep`, `kicker`, `title` (`\n` breaks lines, `[[word]]` highlights), `subtitle`, `clip_credit` / `credit`, `visual` (background image), `out` (output prefix). Brand text comes from `BRAND_NAME` and `BRAND_HANDLE`.

With `"out": "OUT/cover"` it writes:

- `OUT/cover_reel.png` (1080x1920) and `OUT/cover_post.png` (1080x1350): the main cover
- `OUT/cover_options/<code>_reel.png`, `<code>_post.png`: every option
- `OUT/cover_options/compare_reel.png`, `compare_post.png`: comparison sheets to show Josh

## 中文說明

每次出片都會產生主封面，加上 3 到 6 款封面選項和比較圖，交稿時把 `cover_options/compare_reel.png` 給 Josh 挑，挑好後用 `--pick <版型>` 換主封面。字型用 `fetch_fonts.py` 下載，不放進 git。
