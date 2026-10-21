---
name: screen-record
description: "Use Playwright to record interactions on a public web page (scrolling, hovering, clicking links, highlighting key points, chapter cards) and output a vertical 1080x1920 mp4 as tool / website walkthrough footage for a Reel. Triggers: 「錄一段網頁操作」 (record a web interaction), 「網站導覽素材」 (website walkthrough footage), 「螢幕錄影素材」 (screen recording footage), \"screen record\". Public pages only; never logs in or posts."
---

# screen-record: public web page interaction recording (Reel footage)

Josh approved installing this on 2026-10-11 for one purpose only: recording interactions on **public web pages** as footage for IG Reels.
The posting workflow is completely unchanged (IG / Threads still use the box browser method); this tool never touches posting.

## Hard rules (follow every time)

1. Always use a fresh, temporary, in-memory browser (`chromium.launch()` + `newContext()`, no userDataDir).
2. **Never** point at the box's logged-in browser profile; **never** use `--extension`, `attach`, or CDP / wsEndpoint to connect to the box browser; **never** load cookies or storageState; do not use `--persistent` / `--profile`.
3. Do not log in to any site, type text, submit forms, post, comment, or like.
4. Record public pages only (http/https; no localhost / internal network). IG, Threads, and FB may only be viewed as public pages while logged out; if you hit a login wall, switch sources and do not try to log in.
5. record.mjs has built-in guards: a spec containing fields such as storageState / cookies / userDataDir / profile / cdp / extension / login / password / fill / type is rejected outright; all POST / PUT / PATCH / DELETE requests are blocked (the log shows `blocked POST ...`, which is normal); clicking form submit buttons is refused; non-http(s) or internal URLs are refused.
6. Do not modify record.mjs to get around the guards. If you truly need logged-in screens, stop and ask Josh.

## Installed

- Playwright (Node library) 1.64.0: installed in this folder's `node_modules/` (Apache-2.0)
- Playwright CLI `@playwright/cli` 0.1.22: global command `playwright-cli` (~/.local/bin, Apache-2.0). The default session uses an in-memory profile, fine for ad-hoc manual viewing and screenshots; **do not** add `--persistent`, `--profile`, or `attach --extension`.
- Chromium: `npx playwright install chromium` (~/.cache/ms-playwright/chromium-1248, chromium_headless_shell-1248)
- @playwright/mcp is not installed (the CLI plus this script are enough, and Microsoft also recommends the CLI for agents).

## Usage

```bash
cd <SKILLS_DIR>/screen-record
node record.mjs spec.json                 # 輸出到 spec.out
node record.mjs spec.json --out /path/x.mp4
./contact_sheet.sh x.mp4 x_sheet.jpg 4 3  # 4x3 縮圖拼板，用 Read 看
```

Example: `examples/playwright-mcp.json` (test clip: <YOUR_WORKSPACE>/media-team/03-drafts/screen-record-test/test.mp4, 19.8 seconds, 4.1 MB).

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

- Locate elements in one of three ways: `selector` (CSS), `role` + `name` (most reliable), or `text` (optionally with `exact`).
- `scroll`: `by` in pixels, or `to` / `role` / `text` to scroll to an element (`offset` defaults to 25% from the top); `ms` is the scroll duration (ease in/out).
- `highlight`: yellow box plus an optional label, removed after `ms`.
- `chapter`: Playwright's native chapter card (blurred background + title).
- `click` and `hover` use Playwright's native showActions: animated cursor + target outline + action caption (turn off with `"showActions": false`).
- Other options: `fps` (default 30), `crf` (default 23), `mobile` (mobile emulation), `colorScheme`, `locale`, `tail`, `keepWebm`.

### Frame size

Playwright's screencast records in CSS pixels (deviceScaleFactor is not reflected in the video), so:
- By default, record at viewport 720x1280 and upscale to 1080x1920 with lanczos: the layout looks like a large phone with readable text; slightly soft, but good enough for Reels.
- For maximum sharpness: `"viewport": {"width":1080,"height":1920}` (desktop layout, smaller text).
- To record landscape and crop to vertical: `"viewport": {"width":1280,"height":720}, "cropTo916": true` (optionally `"cropX": 200` for the crop start). Output is still 1080x1920 but keeps only the middle strip; usually worse than a vertical viewport.

## Putting it into the final video

- **stock-footage-reel**: in shots.json, for that shot write
  `"pick": {"source":"file","path":"/abs/clip01.mp4","license":"Screen recording of <site>","author":"<site 擁有者>"}`
- **OpenMontage (via openmontage-house)**: add it to the asset list as a local clip, or use it as the real recording source for the screen-demo pipeline.
- House rules still apply: vertical 1080x1920, Sarah Explains voiceover, Traditional Chinese main subtitles + small English line, B clipping-style Vox cover, IG final under 45 MB.
- Add an entry to credits.json: `{"source":"screen-record","credit":"Screen recording of <site>","url":"<網址>","recorded":"YYYY-MM-DD"}`; the end credit reads "Screen recording of <site>".
- When recording someone else's site: use it only as introduction / commentary footage; do not record personal data, other people's private messages, or paywalled content.
