# opus-5-5-prompts: reference list of viral Claude Opus 5.5 video prompts

This is not a new skill but a reference list that josh-video-router and the video skills use for "code-rendered video" inspiration. Drafts only, never posts.

## Source and license

- Source: [yihui-dev/awesome-opus5-5-videos](https://github.com/yihui-dev/awesome-opus5-5-videos) (fetched 2026-10-21, 703 prompts).
- The source repo's LICENSE is MIT (Copyright (c) 2026 yihui-dev), but its README "Credits" section states that "every video and prompt belongs to its original author". MIT can only be confirmed to cover the repo's own curation, not necessarily the prompts written by each author.
- So **no prompt text is copied here**; only titles, categories, tech tags, authors, original post links, and prompt links pointing to the source repo. To use a prompt, read the original in the source repo and respect the original author's intent.
- The source repo also drives traffic to the Skillry site (every entry links a Skillry remake); this list does not include those links.

## Comparison results (automatic first pass)

`catalog.md` compares every prompt against the skills / styles already in this repo and INDEX.md, in three groups:

| Result | Count | Meaning |
|---|---|---|
| New | 204 | No counterpart in this repo: mainly Three.js 3D scenes, shaders, interactive mini-games |
| Partial overlap | 375 | A skill exists for the same kind of workflow (lemo-opuscar, huashu-art-motion, xilo-opus-video, OpenMontage charts), but not the same style |
| Duplicate | 124 | Same or nearly the same as an existing style (e.g. lemo dark-keynote 21, pixel-rpg 13, ascii-crt 10), or a duplicate prompt within the source repo (23) |

The comparison uses keywords and will have false matches; check manually before use.

## How to use

1. When making 3D scenes, shader visuals, or interactive mini-game recordings, start with the "新" (New) section of `catalog.md`.
2. Click the prompt link to read the original, rewrite it in your own words for this video's needs, and apply the house rules (vertical 1080x1920, Taiwan Traditional Chinese, 「」 quotes, no em-dashes, voiceover reads the subtitles, no brand logos).
3. To render a video: have the model output a single HTML file, then record it with screen-record or lemo-opuscar's frame-by-frame rendering.
4. Credit the inspiring author in the end card or caption.

## Regenerating the list

```bash
git clone --depth 1 https://github.com/yihui-dev/awesome-opus5-5-videos
python3 opus-5-5-prompts/build_catalog.py awesome-opus5-5-videos
```
