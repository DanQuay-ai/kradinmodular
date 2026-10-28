# Project history and decisions

## Original request
The owner created Kradin and wanted automated type design and Swiss-inspired posters. The poster randomiser was subsequently excluded: this project focuses exclusively on font construction.

## Sources located
Koradin.otf, the modular website and variable fonts, the modular stroke-source archive, the Kradin chart and orthography documents were available on the owner's laptop. The OTF in the modular archive matches the supplied OTF byte-for-byte. The OTF has 259 glyphs and 208 ligature substitutions.

## Earlier implementation errors
The first studio changed arbitrary traced polylines, lacked a real GPT backend and did not generate installable fonts. The owner rejected this as structurally meaningless. A later inventory showed all ligatures but still did not contain actual proposals. These limits were acknowledged.

The owner clarified the scope as the 63 signs in the nine core rows, not all 208 ligatures. The studio then added original OTF references, candidate stroke/part markers and four draft directions. Its first fitter over-segmented smooth regions and treated trace caps and branch noise as anatomical parts.

## Review workflow
The owner requested faster navigation, pinned glyphs, linked hover highlighting, direct path selection and one-click flags. The studio gained letter/row buttons, a 63-sign map, keyboard navigation, pinned comparison, reversible exclusions and a private D1 queue. Flags preserve source geometry and requested actions; the owner is not expected to diagnose each problem.

## Pass 2 request — 2026-10-28
The owner pointed out patterns such as vertical–unassigned–arc and arc–arc–arc–unassigned–arc. Removed regions may indicate a bad fragment assignment rather than an unwanted appendage. Every removal must cause the surrounding geometry to be reconsidered.

The owner supplied component interpretations: su = Ɔ/O/C plus a strike; tu = opposed Ɔ/C plus equals bars. Many glyphs have symmetry or mostly shared structure. Components must be reused rather than redrawn independently.

The owner also asked that Claude have access to the working site, source and logs. The collaboration interface therefore exposes authenticated, versioned live trace/component edits plus complete available source and audit exports. It does not share publishing tokens or automatically configure a third-party app.

## Evidence boundaries
The saved pass-1 review snapshot, its original geometry, pass-2 reports, visual checks and Git history are preserved. An append-only event log records subsequent flag and patch operations. There is no claim to recover browser actions that were overwritten before logging existed, nor any claim to expose private model reasoning or hidden system data.
