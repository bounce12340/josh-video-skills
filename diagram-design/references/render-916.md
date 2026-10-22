# HTML + SVG diagram → 1080x1920 video frames

How a diagram-design plate becomes footage for a vertical Reel. The commands below are the house recipe; always confirm the result with a contact sheet and `ffprobe` before using it in a video (step 5).

## 1. Safe zones of a 1080x1920 Reel

From `stock-footage-reel/scripts/common.py` (`LAYOUTS["1080x1920"]`) and the IG interface measurements in the same file:

| Band | y range | What is there |
|---|---|---|
| IG top interface | 0 – 220 | Account name, mute button |
| Fixed house title bar | around 232 | Brand mark + source title, drawn by `build.py` |
| **Diagram plate** | **280 – 1240** | The area this page is about |
| Subtitle block | about 1275 – 1490 | Up to 2 Traditional Chinese lines (64px) + 1 English line (34px), bottom edge y=1490 |
| IG bottom interface | 1540 – 1920 | Caption text, audio row |
| IG right-side buttons | x > 950 | Like / comment / share / share sheet |

**Plate geometry: x = 72 … 944 (width 872), y = 280 … 1240 (height 960).** 872 and 960 are both divisible by 4, so the plate keeps upstream's 4px grid intact. Left-aligned at x=72 matches the subtitles and the title bar, and keeps everything clear of the right-side buttons.

- No title bar in this shot (a plain diagram shot, or an OpenMontage edit): the plate may grow to y = 240 … 1240 (height 1000).
- A legend strip adds about 60px of viewBox height upstream, so ask for **872 x 900** when the diagram needs a legend.
- Minimum type sizes for a phone: plate title ≥ 44px, node labels ≥ 28px, mono / technical ≥ 22px. At 872px wide that is about **5 nodes maximum**; anything bigger becomes several plates (section 4).

## 2. Export the plate to PNG

Ask the upstream skill for a viewBox of 872 x 960, then export at 2x (so 1744 x 1920) and let ffmpeg do the single downscale.

**Path A (preferred): the upstream export helper.** It rasterizes with Playwright at 2x by default:

```bash
python3 <DIAGRAM_DESIGN_DIR>/scripts/export_png.py diagram01.html -o diagram01.png
# 或 /diagram-design:export-diagram，格式選 PNG
```

`<DIAGRAM_DESIGN_DIR>` is the upstream skill folder, by default `<SKILLS_DIR>/cathrynlavery-diagram-design/skills/diagram-design` (kept apart from this adapter folder, which has the same name; see SKILL.md Step 2).

**Path B (fallback): a Playwright screenshot.** Reuses `screen-record`'s Playwright 1.64.0 (`cd <SKILLS_DIR>/screen-record && npm install` first, or set `NODE_PATH=<SKILLS_DIR>/screen-record/node_modules`):

```js
// work/diagram_shot.mjs — node diagram_shot.mjs /abs/diagram01.html /abs/diagram01.png
import { chromium } from 'playwright';
const [html, out] = process.argv.slice(2);
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 872, height: 960 }, deviceScaleFactor: 2 });
await page.goto('file://' + html);
await page.waitForTimeout(500);                      // 等字體載入
await page.locator('svg').first().screenshot({ path: out });
await browser.close();
```

`screen-record/record.mjs` **cannot** be used for this: its guards refuse `file://` and local addresses by design, and modifying the guards is forbidden (`screen-record/SKILL.md`, hard rule 6). Use the snippet above instead.

Ask for system-font mode in the HTML so the export makes no network request; otherwise the first screenshot can land before the webfonts arrive and the text reflows.

## 3. Composite the plate onto a 1080x1920 clip

Static hold, the default. `0xF6F3EE` is the house paper color (`WHITE` in `common.py`); use the diagram's own `paper` token if it differs, so the plate edge is invisible.

```bash
ffmpeg -loglevel error -y \
  -f lavfi -t 6 -i "color=c=0xF6F3EE:s=1080x1920:r=30" \
  -loop 1 -t 6 -i diagram01.png \
  -filter_complex "[1:v]scale=872:960:force_original_aspect_ratio=decrease:flags=lanczos,setsar=1[plate];\
                   [0:v][plate]overlay=72:280+(960-h)/2:format=auto,format=yuv420p[v]" \
  -map "[v]" -c:v libx264 -crf 18 -r 30 -pix_fmt yuv420p diagram01.mp4
```

Hold at least 3 seconds, and long enough for the line that covers it. Set `-t` on both inputs to the same value.

**Optional 2x pipeline** (sharpest hairlines, one resample): build the whole frame at 2160x3840 with the 2x PNG placed at x=144, y=560, then finish with `scale=1080:1920:flags=lanczos`.

## 4. Several plates: step reveals

Upstream's animation layer has a `step` mode. Rather than screen-recording the animation, export **one PNG per step** and cross-fade them. Pass 1 builds the plate sequence:

```bash
ffmpeg -loglevel error -y \
  -loop 1 -t 3.0 -i step1.png -loop 1 -t 3.0 -i step2.png -loop 1 -t 3.4 -i step3.png \
  -filter_complex "\
    [0:v]fps=30,scale=872:960:force_original_aspect_ratio=decrease:flags=lanczos,setsar=1[a];\
    [1:v]fps=30,scale=872:960:force_original_aspect_ratio=decrease:flags=lanczos,setsar=1[b];\
    [2:v]fps=30,scale=872:960:force_original_aspect_ratio=decrease:flags=lanczos,setsar=1[c];\
    [a][b]xfade=transition=fade:duration=0.35:offset=2.65[ab];\
    [ab][c]xfade=transition=fade:duration=0.35:offset=5.30[v]" \
  -map "[v]" -c:v libx264 -crf 18 -r 30 -pix_fmt yuv420p plate_seq.mp4   # 8.70 秒
```

Each `xfade` offset is "previous length minus the fade duration", and each fade shortens the total by its own duration (3.0 + 3.0 − 0.35 = 5.65, then 5.65 + 3.4 − 0.35 = 8.70). All inputs must share the same size and fps, which is what the per-input `fps` + `scale` chains are for. Pass 2 composites `plate_seq.mp4` exactly like section 3, replacing the `-loop 1 -i diagram01.png` input and matching `-t` to 8.70.

2.5 to 3.5 seconds per step, 0.3 to 0.4 second fades. Steps are cuts in meaning, so they should line up with subtitle lines, not with the music.

## 5. Check before using it

1. Contact sheet: `<SKILLS_DIR>/screen-record/contact_sheet.sh diagram01.mp4 diagram01_sheet.jpg 4 3`, then look at it with Read.
2. `ffprobe` the size, duration, and fps (1080x1920, 30fps).
3. Read the plate at 1:1 and ask: is every label legible, is anything inside x > 950 or y > 1240, does the plate contradict the line it covers, is there a label the voiceover never says?
4. No brand logos (so no devicon / simple-icons glyphs), no shadows, one accent color.
5. Every box and arrow traces to a source in `facts.md`; the Fact Editor checks this as a claim, not as artwork.

## Pitfalls

- **Hairline shimmer.** Upstream draws 1px hairlines. Non-integer scaling, `zoompan` pushes, and slow pans make them crawl. Prefer a static hold with step reveals. If a push is unavoidable, do it on the 2x image with integer pixel steps and check the result on a phone.
- **A diagram too wide for 872px.** Split it into plates (first choice), or render full-bleed at 1080 wide while keeping all focal content left of x=950. A horizontal pan across a wide diagram is the last resort, for the shimmer reason above.
- **CJK fonts.** Geist and Instrument Serif have no Chinese glyphs; without Noto Sans TC / Noto Serif TC specified, Chinese labels fall back to whatever the renderer has and the 4px grid alignment drifts.
- **Export before fonts load.** Wait for the fonts (or use system-font mode), or the PNG catches a reflowed layout.
- **Double resampling.** Exporting at 2x, downscaling to 1x, then letting `reel.sh ig` re-encode softens thin strokes. Keep the plate at its native plate size through the edit and compress only once at the end.
