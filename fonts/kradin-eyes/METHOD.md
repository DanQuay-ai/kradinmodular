# Kɔradin Eyes: how it is made

Kɔradin Eyes is a two-master font (Thin W 40, Black W 140) built from strokes, with counters, eyes and apertures cut as shapes. This file records how it works and what the owner has taught it so far, so the same method carries on to the rest of the font, the serif styles and later projects.

## 1. Principles (set by the owner)

1. **One font, one direction.** Thin and Black are the same design. Topology, parts and junctions are read on Thin and then enforced on Black.
2. **Strokes that do not touch in Thin never touch in Black.** The exceptions are named per glyph (for example ku's rings, or hooks the owner asks to keep apart).
3. **Stay faithful to the akrokerri mod** (glyphs.json and its edits) for the skeleton. Use Koradin.otf as the guide for nasal marks, in the full-font pass.
4. **Negative space has a language:**
   - **Eye:** a closed small counter, drawn as a lens (two arcs meeting in sharp points), running point to point across the counter.
   - **Crossing:** a four-way crossing becomes a four-point star (e).
   - **Ink trap:** a dead-end slot between converging strokes becomes a leaf, pointed at both ends.
   - **Aperture:** a slit that opens to the outside becomes a blade, whose outer point runs out past the edge.
   - **Long slots** stay parallel.
   - **Sharp means sharp:** no rounding pass reaches the points.
5. **Corner rule.** An inside corner follows the outside one: concentric, at the gap (the ku hand drawing).
6. **Even weight.** No stroke gets thinner to make room. Make room by moving, shortening or reshaping strokes.
7. **Body lines.**
   - Ends that cross the baseline or the top line are cut flat on them.
   - Bars on the top axis reach the top line, and so must hooks (ne, nɛ).
   - Bowls that dip past a body line run flat along it.
8. **Symmetry.** Glyphs meant to be symmetric are made exactly symmetric (u on both axes, e by its mirror).
9. **Widths are harmonised.** Every Black glyph widens by at least the same factor, so the narrow ones stop looking pinched.

## 2. Pipeline (src/eyes2, run from site2)

1. `dump.js 40,140 rad.json override.json`: turtle strokes from the lab become centrelines and polygons per weight. `override.json` holds the skeleton edits.
2. `transform.py`: right-angle turns are squared, but only where the Thin contacts stay the same.
3. `stretch.py rad.json out.json 1.3`: body 700 → 910. The ops are read on Thin and applied to every weight:
   - **run:** a near-miss end runs on to the other stroke's centreline.
   - **trim:** an end that overshoots, past a crossing or past the end of an L-corner, is cut back.
   - **cap:** the ends of an L corner get square caps.
   - **cut / foot / pull:** owner ops. `cut` runs an end to the body line; `foot` makes an end overshoot the stroke it stops on; `pull` shortens an end, Black only.
   - Black uses an elliptical nib (contrast 0.82: horizontals lighter).
4. `engine.py` (`EYES_H=910 EYES_FLARE=1.15 EYES_GX_MIN=1.3 EYES_OWNER=owner.json`) builds both masters:
   - **separation:** Thin touch graph plus geodesic distance tell which samples are "far" (different parts).
   - **relax:** each stroke group moves and scales by least squares, while junctions and body lines hold. The glyph may widen (gx, at least 1.3, at most 1.45).
   - **cuts:** Voronoi ridges between far samples become gap bands.
     - `clean_cuts` drops bites, meaning cuts that change nothing topologically.
     - `bladeify` turns short kept gaps into blades.
   - **eyes:** small closed counters become lenses (`lens_eye`); large ones become rounded rectangles. Thin counters that close in Black get a minimum eye.
   - **spines:** they keep every stroke from being cut through.
   - **fills:** wedges, tapers and baseline notches.
   - **owner marks:** join, nogap, slit, crotch, smooth.
   - **sharp pass:** eyes and blades are re-cut at the end.
   - **finish:** body-line snap and symmetry.
5. `symm.py`: exact mirror symmetry for the symmetric list.
6. `post3.py`: the owner's drawn shapes:
   - e star
   - u symmetry on both axes
   - pe, du and no leaves
   - pɔ blade
   - fi column
   - ku rebuilt by rule
7. `verify.py` (topology: no merges or breaks, counters kept), `widths.py`, `overlay.py` (Thin compared with akrokerri), `otf.py`.

## 3. The feedback loop (privileged in every session)

The review board (a claude.ai artifact) stores everything in a database that Claude reads with the ArtifactData tool:
- **feedback:** remark marks, rules a glyph may break, notes, validation.
- **picks / picks14:** the A/B picks, with marks per variant.

1. **Read.** List the collections and render every glyph with its marks over the revision the owner saw (`marks.py`).
2. **Interpret before acting.** For each mark, say what it is pointing at in the geometry, and whether it calls for a skeleton change, a stroke-end op, an engine op or a drawn shape. Then confirm against the owner's own words:
   - "smoothing over" means smoothing, not joining
   - "ink trap too pronounced" means keep the aperture
   - "touch the topline" applies to the part that was named
3. **Change the strokes first.** Prefer the skeleton or stroke ops (override, stretch ops) to polygon hacks. Polygon patches (closings, hulls) are the last resort, limited to the mark and checked for topology. In r11 polygon patches added stray strokes and lines.
4. **Offer A/B when the reading is open.** Show both on the board and let the owner pick; use the pick and its notes as rules.
5. **Look before reporting.** Zoom on every changed glyph next to the previous revision, check topology on all 63, then republish the board with a new revision label.

## 4. Rules learned per glyph (r10 to r14)

- **Hooks against a stem (re, tɔ, no, nɔ):** keep the strokes apart.
  - A narrow straight slit cut from the hook only, so the stem edge stays straight.
  - Or the hook end shortened in Black (re).
  - Never joined.
- **Converging strokes (pe, pɔ, du, ti):** keep the aperture.
  - The tip becomes a leaf (pe, du, no) or a blade through the edge (pɔ).
  - Do not fill.
- **e:** the glyph overlaid with its vertical mirror, with a four-point star in the Black crossing.
- **u:** the two crossing strokes mirror each other (round curves), symmetric on both axes, vertical lens eye.
- **se, sɛ:** both hooks are one stroke, drawn twice at their own angles, 26° more vertical.
- **si:** a foot that runs a full stroke past the stem on the baseline.
- **sɔ:** arches 78 units shorter on each side.
- **ne, nɛ:** the hook's top run sits on the top axis. In nɛ, the bar and the bowl bottom share one line.
- **ku:**
  - Rings centred and separate.
  - The U runs concentric round the top ring at the gap; even weight.
  - Capsule or lens eyes.
- **fi:** one column. The lower part starts on the upper part's left edge, and the diagonal is steeper and stays inside the column.
- **fɔ:** bowl radius 145 and curl radius 80, so the weight stays even and clears the bottom.
- **pa:** right diagonal cut flat on the top line, asymmetric.

## 5. Roadmap (owner, 2026-10-29)

1. Validate the 63 radicals.
2. The rest of the font (composites and marks), with the nasal marks guided by Koradin.otf, not akrokerri.
3. Serifs, designed with the same feedback board.
4. A second serif style based on Agu Display.
