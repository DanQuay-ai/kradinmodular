# Kradin Radical Studio — shared working instructions

This is the actual working Site project, not a separate mock-up. The owner wants Claude and Codex to work from the same source, reference font, saved feedback and logs.

## Owner's constraints

- Scope: the 63 core signs (vowels, P, D, F, K, R, T, S, N × seven vowels). No variants or poster randomiser.
- The supplied `public/fonts/Koradin.otf` is the immutable reference. Its SHA-256 is `c7703eb117f670d0ca984bc9b2bbd80c260f29ef5815f8bcc26b6d3490360413`.
- Interpret strokes and reusable components. Do not treat every junction or short fit failure as a new shape or appendage.
- A removal must trigger re-fitting of its whole source path, adjacent primitives and connected junction paths. The owner often removed an “unassigned” part to point out over-segmentation, not to request a hole in the letter.
- Preserve vertical and horizontal supports. Correct free endpoints from actual OTF cap geometry; a closed loop has no free cap.
- `su` is Ɔ + O + C with a horizontal strike; the O shares its spines with the opposed outer forms. `tu` is opposed Ɔ/C forms with `=`. Intersections do not dictate writing order.
- Construct mirrored counterparts from one base when supported by the reference. Six R-family signs share an aligned lower U body. `ra` was excluded by the shape-consensus and ink checks; do not force it into that family.
- The owner validates and flags; do not require them to draw points or diagnose every bad path.

## Current analysis

`analysis/v1-radicals.json` is immutable review evidence. `public/radicals.json` is pass 2. Its IDs (`S2_*`, `P2_*`) deliberately do not reuse pass-1 IDs. `displayId` supplies short UI labels.

Pass 2 identifies OTF flat-cap midpoints, joins only clear tangent continuations, fits continuous curves across old gap fragments, uses explicit su/tu components and shared supports. It retains 122 fitted compound arcs; these are measured cubic chains, not certified circular-radius anatomy. Do not report zero “unresolved” labels as proof that every anatomical interpretation is solved.

The four-radius palette remains provisional. The OTF source and evidence are preserved beside each proposal. The original may have optical asymmetries; whole-glyph symmetry scores are evidence, not permission to mirror every shape blindly.

## Make live changes through the private MCP endpoint

Connect an MCP client using the private Site's authenticated MCP URL (obtain the canonical URL from Sites connection settings; the Site route is `/mcp`). No token is stored in this repository or source bundle. Claude must use the owner's own authenticated access. No Claude app configuration has been changed automatically.

Tools:
- `get_project_context`, `read_project_file`: rules, source inventory and logs.
- `get_trace_study`: get the latest `projectRevision`, `sourceHash`, analysis version and the selected glyph geometry.
- `get_component_library`: inspect a common base and all its instance transforms.
- `get_review_queue`, `get_revision_log`: user flags, historical snapshots and the append-only activity trail.
- `apply_component_patch`: change normalized base points once and propagate them to every registered instance, preserving cap anchors.
- `apply_stroke_patch`: change an unshared stroke. Shared supports must be edited through their base.
- `revert_trace_patch`: undo a patch while keeping the audit entry.

Every write requires the current revision, the reference hash, analysis version and a rationale. Re-read after a revision conflict. Patches affect the live trace study, not the original OTF. You can also return the same patch as a JSON file for the owner to import under Study & logs.

Example patch fields (use real current IDs and points):
`kind`, `glyph`, `strokeId`, `points`, `expectedRevision`, `sourceHash`, `analysisVersion`, `rationale`, `author`.
For a shared base use `kind: "component"`, `componentId` and normalized points instead of glyph/strokeId.

## Source code changes

Claude Code or another filesystem-enabled client can open this project folder directly. Edit `public/`, `lib/`, `app/` or the analysis code. Do not edit `dist/`, applied migrations or runtime credentials. Full application-code changes require a normal Sites build and publication; the MCP patch tools handle trace/component data changes immediately.

Before building: `node scripts/prepare-studio.mjs`, then the Sites `build-site.mjs` helper. Use `REVIEW_WORKFLOW.md` for private service access and the project ID. Keep the Site owner-private. Never bundle `.env*`, `.wrangler/`, `.sites-runtime/`, node_modules or credentials.

## Evidence and tests

- `collaboration/reviews/`: the saved user review snapshots available at the start of this pass.
- `collaboration/logs/`: retrace reports, endpoint changes, sampled OTF ink-fit measurements and execution logs.
- `analysis/figures/`: visual inspections.
- `public/retrace-report.json`: pass summary and limitations.
- `collaboration/project-history.md`: conversation decisions and earlier implementation mistakes.
- Git history and `collaboration/git-history.bundle` in the handoff archive preserve the available source history.
- The live D1 event log starts with the collaborative update. Earlier overwritten browser actions cannot be reconstructed; saved review snapshots and Git history are the historical evidence we have.

Run the construction, review sync, local API and retrace tests before publishing. Tests that mutate APIs must run against loopback, not production.
