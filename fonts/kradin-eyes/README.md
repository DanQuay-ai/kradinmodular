# Kɔradin Eyes (63 radicals, Thin + Black)

Pipeline (src/eyes2), run in this order:
1. `dump.js 40,140 rad.json skeleton-override.json` (stroke data from the lab, with the skeleton pass applied)
2. `transform.py` skeleton pass: right-angle turns squared when Thin keeps every contact
3. `stretch.py rad.json rad5.json 1.3` body 700 -> 910 (stacked parts get room for two heavy strokes + the gap). Ends read on Thin:
   near misses run on to the other stroke, short overshoots stop on it, L corners get square caps. Black is drawn with an
   elliptical nib (contrast 0.82: horizontals a little lighter than verticals; Thin stays monoline)
4. `EYES_H=910 EYES_FLARE=1.15 engine.py` Thin and Black: topology read on Thin, enforced on Black (relax, cuts, eyes, spines,
   body lines). Cuts that only bite into ink joined anyway (ink traps) are dropped, kept gaps are drawn straight, acute wedges
   and baseline notches are filled, free ends may shorten up to 2 W to clear a part, free terminals flare where there is room
5. `symm.py` exact mirror symmetry for the glyphs meant to be symmetric
6. `verify.py` (parts never merge or break, counters kept), `widths.py` (stroke width), `overlay.py` (Thin vs akrokerri mod), `otf.py`
`anatomy.py` writes anatomy.json / anatomy.png (parts, terminals, junctions, counters read on Thin).
