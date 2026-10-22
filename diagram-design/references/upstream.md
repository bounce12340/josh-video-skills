# What the upstream diagram-design skill is

Summary only, for routing decisions. **No upstream file is copied into this repo**; the upstream repo is authoritative and may have changed since this page was written.

- Repo: <https://github.com/cathrynlavery/diagram-design>
- Author: Cathryn Lavery
- License: **MIT**, Copyright (c) 2025 Cathryn Lavery (permits copying and commercial use with the copyright and permission notice kept; this repo links instead, per its own convention)
- Skill folder inside that repo: `skills/diagram-design/` (`SKILL.md` version 2.6 at the time of writing)
- Checked: 2026-10-22

## What it does

Takes a diagram described in plain language, picks a type, states its plan, and writes **one self-contained HTML file with inline SVG**: no build step, no JavaScript runtime, no external images. Optional PNG and SVG export. Install: `npx skills add cathrynlavery/diagram-design`, or via the Claude Code / Codex / Cursor / Cline / Copilot marketplace manifests it ships.

## The 45 diagram types

Architecture · IT current-state · Flowchart · Sequence · State machine · ER / data model · Timeline · Swimlane · Quadrant · Radar / spider · Loop / flywheel · Nested · Tree · Org chart · Layer stack · Venn · Pyramid / funnel · Bar chart · Treemap · Line chart (slopegraph, streamgraph variants) · Gantt · Scatter plot (bubble, beeswarm variants) · High-Level · Process · Medallion · Data flow · DP integration · DP security matrix · Sankey · Fishbone · Wardley map · Kanban · User journey · Deployment · Dependency graph · UML class · Story map · Database schema · Polar chart · Waterfall · Architecture delta · Exploded axonometric · Axonometric plan · Heatmap · Service blueprint.

The ones that fit Josh's topics: **loop/flywheel, sequence, architecture, layer stack, data flow, flowchart, swimlane, process, state machine, timeline, user journey**. Chart types (bar, line, treemap, waterfall, heatmap…) overlap with huashu's data cards, which stay the first choice for numbers.

## Design rules it enforces

What makes its output look editorial rather than generic:

- **No shadows.** No generic Mermaid styling.
- **One accent color**, at most 2 focal elements per diagram; everything else uses the `ink` / `muted` / `soft` roles.
- **Orthogonal connectors only**: rounded right-angle elbows, no diagonals; no overlapping strokes (parallel routes offset, bridge/hop at crossings); distinct fan-out attach points; arrow labels sit in a small opaque mask gap, max ~14 characters, never rotated vertically.
- **4px grid**: every coordinate, width, and gap divisible by 4. Border radius ≤ 10px, 1px hairlines.
- **Complexity budget**: about 9 nodes, 12 arrows, 2 callouts, 2 accent elements per diagram, with per-type limits; a "remove test" asks whether each node, arrow, and label could be deleted without losing meaning.
- **Typography by role**: Instrument Serif titles, Geist sans node names, Geist Mono for technical content only (ports, URLs, commands), never mono as a blanket font. **None of these cover CJK**, which is why the house plate specifies Noto Sans TC / Noto Serif TC.
- **Accessible SVG**: `role="img"`, `aria-labelledby`, prefixed title/desc ids; WCAG AA text contrast.

## Size presets

`doc-inline` (~720 wide) · `doc-wide` (~1080) · `slide-16x9` (1920x1080) · `slide-4x3` · `social-og` (1200x630) · `social-square` (1080x1080) · `print-a4/a3/letter-landscape` · `fit` (auto-size to content). A preset sets both the viewBox and the type ramp. Detail levels: `simplified` (≤7 nodes), `balanced` (≤12), `faithful` (≤24).

**There is no 9:16 preset.** For video we ask for a custom viewBox instead; see [render-916.md](render-916.md).

## Other capabilities (mostly unused here)

- **Import and redraw** from draw.io, Mermaid, and Excalidraw (`/diagram-design:import-drawio`, `:import-mermaid`, `:import-excalidraw`), with detail level, audience (engineer / mixed / executive), and output size dials, plus a fidelity ledger of what was merged, collapsed, or dropped. Useful when a source article ships a Mermaid or draw.io diagram: redraw it rather than screenshotting theirs.
- **Export** (`/diagram-design:export-diagram`, `scripts/export_svg.py`, `scripts/export_png.py`): SVG with embedded fonts, PNG rasterized via Playwright at 2x by default. This is the path the house render uses.
- **Validation scripts**: `verify-geometry.py` (connector rules), `self_check.py` (accessible SVG and content), `verify-motion.py` (animation contract).
- **Animation layer** (`references/animation.md`): reveal / step / loop modes. We use **step** and screenshot each step, because the house pipeline composites stills (see render-916.md).
- **Brand onboarding and profiles**: extracts a palette and font stack from a website and maps them to the `paper` / `ink` / `muted` / `accent` / `link` roles, saved per named profile. Do not point it at someone else's site to copy their look; set the house tokens by hand.
