# kradinmodular: shared working notes for Claude and GPT/Codex

Owner: Dany-Ross (Neo-Akanism). Static site, no build step. Serve the folder (`python3 -m http.server`) and open `index.html`.
Both agents work from this repository. Keep edits small, commit with a clear message, never force-push.

## Pages
- `index.html` Type tester: Kɔradin, Adinkra alphabet, Latin; live fonts generated in the browser from stroke data (`kr.js` + opentype.js).
- `lab.html?s=<script>` Construction lab: edit strokes of any script (`kradin`, `adinkra`, `latin:franklin`, ...). Edits live in localStorage (`<prefix>edits`); "Download edits" exports them.
- `trace.html` Trace study (GPT's Radical Studio, ported): reads `trace/radicals.json`; the old `/api/*` routes are served by `trace/api-shim.js` from localStorage, same patch contract (expectedRevision, sourceHash, analysisVersion, rationale). In the console: `TraceStudio.getAnalysis()`, `TraceStudio.applyPatch({...})`, `TraceStudio.exportState()`. "Export state" / "Import state" move work between agents.
- `serif.html` style rules (contrast, ends, serifs). `calendar.html` Akan calendar. `radicals.html?s=<script>` overview.

## Data
- Stroke = `{x, y, h, segs:[{t:"L",len}|{t:"A",r,ang}|{t:"C",ang}], s, e, cap0, cap1}`; heading in degrees, 0 = right, 90 = up, arc `ang` + = anticlockwise.
- Kɔradin: `glyphs.json` (radicals + composites), body 0..700, axes 49/350/651, ends past 0/700 cut flat, strokes move inward with weight (K = (700-W)/602).
- Adinkra alphabet: `adinkra.json`, same body, 2:1.
- Latin: `latin/<id>.json` with `metrics {cap:700, x, asc, desc, W}`; baseline 0, cap height 700, plain ends, strokes fixed in place (KS.setBody({fixed:true})). Ghosts in `latin/<id>-ghost.json`.
- Register a script in `KR_SCRIPTS` at the end of `kr.js`.

## Rebuilding a font from a reference
`python3 src/autotrace.py REF.ttf latin/<id>.json --name "..." --ghost latin/<id>-ghost.json --version <id>-1`
(skeleton, good-continuation merge through junctions, line/arc fit). Output is a draft: check it in the lab over the orange ghost, fix junction overshoots and over-split curves, approve.
Pending references: Eckmannschrift, Auriol, Arnold Böcklin (need font files from the owner). Franklin is traced from Libre Franklin (OFL).

## Rules the owner has set (Kɔradin)
See `trace/CLAUDE.md`: Koradin.otf is the immutable reference; interpret strokes and reusable components, not every junction as a new shape; preserve vertical/horizontal supports; mirrored counterparts from one base; the owner validates, agents do the fitting.
