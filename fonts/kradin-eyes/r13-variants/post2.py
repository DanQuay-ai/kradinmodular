"""variant post ops on finished glyphs (output coordinates), from the owner's review marks"""
import json, sys, glob, numpy as np
from shapely.geometry import Polygon, Point, box, LineString
from shapely.ops import unary_union
from shapely import affinity
R = json.load(open(sys.argv[1])); v = sys.argv[2]; BH = 910.0; GAP = 52 * 0.82
def geom(ps): return unary_union([Polygon(p[0], p[1:]).buffer(0) for p in ps])
def polys(g): return [] if g.is_empty else [p for p in (g.geoms if hasattr(g, "geoms") else [g]) if p.geom_type == "Polygon"]
def out(g): return [[np.round(np.array(p.exterior.coords), 1).tolist()] + [np.round(np.array(r.coords), 1).tolist() for r in p.interiors] for p in polys(g)]
def sig(g): P = [p for p in polys(g) if p.area > 50]; return (len(P), sum(1 for p in P for r in p.interiors if Polygon(r).area > 50))
FB = {}
for f in glob.glob('/tmp/claude-0/fbdata/feedback/*.json'):
    d = json.load(open(f)); d = d.get('data', d); FB[d['key']] = d
def marks(k, w): return [m for m in FB.get(k, {}).get('marks', []) if m['w'] == w]
def ell(m): return affinity.scale(Point(m['cx'], BH - m['cy']).buffer(1, quad_segs=32), m['rx'], m['ry'])
def close_in(g, r, Z): return g.union(g.buffer(r, quad_segs=16).buffer(-r, quad_segs=16).intersection(Z)).buffer(0)
def open_in(g, r, Z): return g.difference(Z).union(g.buffer(-r, quad_segs=16).buffer(r, quad_segs=16).intersection(Z)).buffer(0)
def taper(g, E, r):            # the pointed end of a slot is filled until the slot is 2r wide: a round, shallower end
    return close_in(g, r, E.buffer(r))
def slot(g, E, w):             # the slit becomes a clean straight slot of width w (flat hook end, straight stem edge)
    S = g.buffer(GAP, quad_segs=16).buffer(-GAP, quad_segs=16).difference(g).intersection(E.buffer(GAP))
    P = [p for p in polys(S) if p.area > 30]
    if not P: return g
    N = max(P, key=lambda p: p.area)
    xy = np.asarray(N.exterior.coords); c = np.asarray(N.centroid.coords[0]); ax = np.linalg.svd(xy - c, full_matrices=False)[2][0]
    t = (xy - c) @ ax; nrm = np.array([-ax[1], ax[0]]); off = (xy - c) @ nrm
    mid = c + nrm * (off.max() + off.min()) / 2                      # centre of the slit across its width
    band = LineString([mid + ax * (t.min() - w), mid + ax * (t.max() + w)]).buffer(w / 2, cap_style=2)
    filled = g.union(N.buffer(1))
    h = filled.difference(band.intersection(N.buffer(w).union(band.intersection(E.buffer(GAP)))))
    return h.buffer(-1.5).buffer(1.5)
def map_thin_to_black(m, k):   # a mark drawn on Thin, placed on Black by the two glyphs' boxes
    tb = geom(R['40'][k]).bounds; bb = geom(R['140'][k]).bounds
    sx = (bb[2] - bb[0]) / (tb[2] - tb[0])
    return dict(m, cx=bb[0] + (m['cx'] - tb[0]) * sx, rx=m['rx'] * sx * 1.6, ry=m['ry'] * 1.3)
SPEC = {
 'pe': ('taper', 0.25, 0.5), 'pɔ': ('taper', 0.25, 0.5), 'ti': ('taper', 0.25, 0.5),
 'tɔ': ('slot', 0.55, 1.0), 'no': ('slot', 0.55, 1.0), 'nɔ': ('slot', 0.55, 1.0), 're': ('slot', 0.55, 1.0),
}
for k, sp in SPEC.items():
    if k not in R['140']: continue
    g = geom(R['140'][k]); ref = sig(g)
    for m in marks(k, 'black'):
        E = ell(m)
        if sp[0] == 'taper':
            h = taper(g, E, (sp[1] if v == 'A' else sp[2]) * GAP * 2)
            if sig(h) != ref: h = slot(g, E, (0.55 if v == 'A' else 1.0) * GAP)      # a hairline: made a clean slot instead
        else: h = slot(g, E, (sp[1] if v == 'A' else sp[2]) * GAP)
        if sig(h) == ref: g = h
        else: print(k, v, 'op refused: it would change parts or counters')
    if k == 're':                                    # re is symmetric: the right hook gets the same treatment
        b = g.bounds; c = (b[0] + b[2]) / 2; half = g.intersection(box(b[0] - 9, b[1] - 9, c, b[3] + 9))
        g = unary_union([half, affinity.scale(half, -1, 1, origin=(c, 0))]).buffer(0.01).buffer(-0.01)
    R['140'][k] = out(g)
# du: the wedge where the slanted stroke meets the stem, smoothed in both masters (rounded crotch)
if 'du' in R['40']:
    for W in ('40', '140'):
        g = geom(R[W]['du']); ref = sig(g)
        for m in marks('du', 'thin'):
            E = ell(m if W == '40' else map_thin_to_black(m, 'du'))
            h = close_in(g, (0.6 if v == 'A' else 1.2) * float(W), E.buffer(150))
            if sig(h) == ref: g = h
        R[W]['du'] = out(g)
# ku (B): the joint of the ring and the U arm smoothed, then mirrored
if v == 'B' and 'ku' in R['140']:
    g = geom(R['140']['ku'])
    for m in marks('ku', 'black'): g = close_in(g, 0.3 * 140, ell(m).buffer(20))
    b = g.bounds; c = (b[0] + b[2]) / 2; half = g.intersection(box(b[0] - 9, b[1] - 9, c, b[3] + 9))
    R['140']['ku'] = out(unary_union([half, affinity.scale(half, -1, 1, origin=(c, 0))]).buffer(0.01).buffer(-0.01))
# e (A): the glyph and its vertical mirror, on itself
if v == 'A' and 'e' in R['40']:
    for W in ('40', '140'):
        g = geom(R[W]['e']); b = g.bounds; cy = (b[1] + b[3]) / 2
        R[W]['e'] = out(unary_union([g, affinity.scale(g, 1, -1, origin=(0, cy))]).buffer(0.01).buffer(-0.01))
# fi: the lower parts aligned on the upper part (A: left edges, B: centres)
if 'fi' in R['140']:
    for W in ('40', '140'):
        P = polys(geom(R[W]['fi'])); up = max(P, key=lambda p: p.centroid.y); lo = [p for p in P if p is not up]
        L = unary_union(lo); ub, lb = up.bounds, L.bounds
        dx = (ub[0] - lb[0]) if v == 'A' else ((ub[0] + ub[2]) / 2 - (lb[0] + lb[2]) / 2)
        if W == '40' and v == 'A': dx = 0                   # Thin is aligned already
        R[W]['fi'] = out(unary_union([up, affinity.translate(L, dx, 0)]))
json.dump(R, open(sys.argv[3], 'w'))
