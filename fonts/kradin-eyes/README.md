# Kɔradin Eyes (63 radicals, Thin + Black)

Pipeline (src/eyes2), run in this order:
1. `dump.js 40,140 rad.json skeleton-override.json` (stroke data from the lab, with the skeleton pass applied)
2. `transform.py` skeleton pass: spirals re-spaced and drawn arc-line-arc-line, right-angle turns squared, hairpins opened when Thin topology allows
3. `stretch.py rad.json rad4.json 1.25` body 700 -> 875 (taller x-height: room for stacked parts), bowls that dip past a body line run flat on it
4. `EYES_H=875 engine.py` Thin and Black: topology read on Thin, enforced on Black (relax, cuts, eyes, spines, body lines)
5. `symm.py` exact mirror symmetry for the glyphs meant to be symmetric
6. `verify.py` (parts never merge or break, counters kept), `widths.py` (stroke width consistency), `otf.py`
`anatomy.py` writes anatomy.json / anatomy.png (parts, terminals, junctions, counters read on Thin).
