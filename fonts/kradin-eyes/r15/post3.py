"""r14 post: the owner's negative-space language (lens eyes are in the engine) applied where he drew it
- e: the glyph and its vertical mirror; Black's centre counter a four-point star inscribed in the crossing
- u: exact symmetry on both axes
- ink traps (pe, du, no): the slot becomes a leaf, pointed at both ends, convex sides
- aperture (pɔ): a blade, the leaf's outer point carried out through the edge
- fi: the lower part centred (by its bar) under the upper part
- ku: rebuilt from the hand drawing: consistent weight, the U's inside runs concentric round the ring at the gap"""
import json, sys, glob, math, numpy as np
sys.path.insert(0, '/home/claude/work/eyes2')
from shapely.geometry import Polygon, Point, box, LineString
from shapely.ops import unary_union
from shapely import affinity
import engine
R = json.load(open(sys.argv[1])); KUEYE = sys.argv[3] if len(sys.argv) > 3 else 'capsule'; BH = 910.0; C = 0.82
def geom(ps): return unary_union([Polygon(p[0], p[1:]).buffer(0) for p in ps])
def polys(g): return [] if g.is_empty else [p for p in (g.geoms if hasattr(g, "geoms") else [g]) if p.geom_type == "Polygon"]
def out(g): return [[np.round(np.array(p.exterior.coords), 1).tolist()] + [np.round(np.array(r.coords), 1).tolist() for r in p.interiors] for p in polys(g)]
def sig(g): P = [p for p in polys(g) if p.area > 50]; return (len(P), sum(1 for p in P for r in p.interiors if Polygon(r).area > 50))
def ell(cx, cy, rx, ry): return affinity.scale(Point(cx, BH - cy).buffer(1, quad_segs=32), rx, ry)
FB = {}
for f in glob.glob('/tmp/claude-0/fbdata/feedback/*.json') + glob.glob('/tmp/claude-0/picks/picks/*.json'):
    d = json.load(open(f)); d = d.get('data', d); FB.setdefault(d['key'], []).extend(d.get('marks', []))
def nib(g, d):            # offset with the elliptical nib (horizontals lighter): d > 0 grows, d < 0 shrinks
    s = affinity.scale(g, 1, 1 / C, origin=(0, 0)); s = s.buffer(d, quad_segs=16, join_style=1)
    return affinity.scale(s, 1, C, origin=(0, 0))
def rrect(x0, y0, x1, y1, r):
    r = min(r, (x1 - x0) / 2 - 0.5, (y1 - y0) / 2 - 0.5); return box(x0 + r, y0 + r, x1 - r, y1 - r).buffer(r, quad_segs=16)
def leaf(g, E, W, blade=False):
    r = 0.5 * W; S = g.buffer(r, quad_segs=16).buffer(-r, quad_segs=16).difference(g)
    comps = [p for p in polys(S) if p.intersects(E) and p.area > 20]
    if not comps: return g, 'no slot found'
    N = max(comps, key=lambda p: p.intersection(E).area)
    xy = np.asarray(N.exterior.coords); c = np.asarray(N.centroid.coords[0]); ax = np.linalg.svd(xy - c, full_matrices=False)[2][0]
    t = (xy - c) @ ax; p0, p1 = xy[t.argmin()], xy[t.argmax()]; L = np.hypot(*(p1 - p0))
    b_ = g.bounds; outside = box(b_[0] - 500, b_[1] - 500, b_[2] + 500, b_[3] + 500).difference(g.union(S).buffer(0.5))
    if Point(p0).distance(outside) < Point(p1).distance(outside): mouth, tip = p0, p1
    else: mouth, tip = p1, p0
    if blade: mouth = mouth + (mouth - tip) / L * 0.35 * L
    cen = (mouth + tip) / 2; a = np.hypot(*(mouth - tip)) / 2; ang = math.degrees(math.atan2(*(mouth - tip)[::-1]))
    meanw = N.area / max(L, 1); bb = min(max(0.62 * meanw, 0.1 * a), 0.3 * a)
    lf = engine.lens(cen[0], cen[1], a, bb, ang)
    return g.union(N.buffer(0.3)).difference(lf).buffer(0), 'ok'
def try_op(k, W, fn, *args):
    g = geom(R[W][k]); ref = sig(g); h, msg = fn(g, *args)
    if sig(h) != ref: print(k, W, fn.__name__, 'refused (parts or counters would change)'); return
    print(k, W, fn.__name__, msg); R[W][k] = out(h)

# e: vertical mirror on itself; Black: a four-point star in the crossing
def e_op(g, W):
    b = g.bounds; cy = (b[1] + b[3]) / 2; g = unary_union([g, affinity.scale(g, 1, -1, origin=(0, cy))]).buffer(0.01).buffer(-0.01)
    if W == '140':
        xs = LineString([(b[0] - 9, BH - 60), (b[2] + 9, BH - 60)]).intersection(g).bounds
        ys = LineString([(b[0] + 40, -9), (b[0] + 40, BH + 9)]).intersection(g).bounds
        x0, x1, y0, y1 = xs[0], xs[2], ys[1], ys[3]; cx, cy2 = (x0 + x1) / 2, (y0 + y1) / 2
        hx, hy = (x1 - x0) / 2 * 0.96, (y1 - y0) / 2 * 0.96; n = 0.62
        th = np.linspace(0, 2 * math.pi, 240)
        star = Polygon(np.c_[cx + hx * np.sign(np.cos(th)) * np.abs(np.cos(th)) ** (2 / n), cy2 + hy * np.sign(np.sin(th)) * np.abs(np.sin(th)) ** (2 / n)])
        g = g.union(box(x0, y0, x1, y1)).difference(star)
    return g, 'ok'
for W in ('40', '140'):
    g = geom(R[W]['e']); h, _ = e_op(g, W); R[W]['e'] = out(h)
# u: symmetric on both axes
for W in ('40', '140'):
    g = geom(R[W]['u']); b = g.bounds; cx, cy = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
    q = g.intersection(box(b[0] - 9, cy, cx, b[3] + 9))
    h = unary_union([q, affinity.scale(q, -1, 1, origin=(cx, 0)), affinity.scale(q, 1, -1, origin=(0, cy)), affinity.scale(q, -1, -1, origin=(cx, cy))]).buffer(0.01).buffer(-0.01)
    if sig(h) == sig(g): R[W]['u'] = out(h)
    else: print('u', W, 'symmetry refused')
# leaves and the blade, where the owner marked the ink traps
def marks(k, w, v=None): return [m for m in FB.get(k, []) if m['w'] == w and (v is None or m.get('v') in (None, v))]
for m in marks('pe', 'black'): try_op('pe', '140', leaf, ell(m['cx'], m['cy'], m['rx'], m['ry']), 140.)
for m in marks('pɔ', 'black'): try_op('pɔ', '140', leaf, ell(m['cx'], m['cy'], m['rx'], m['ry']), 140., True)
for m in marks('no', 'black', 'A'): try_op('no', '140', leaf, ell(m['cx'], m['cy'], m['rx'] * 1.3, m['ry'] * 1.3), 140.)
for m in marks('du', 'thin'):
    try_op('du', '40', leaf, ell(m['cx'], m['cy'], m['rx'], m['ry']), 40.)
    tb = geom(R['40']['du']).bounds; bb = geom(R['140']['du']).bounds; sx = (bb[2] - bb[0]) / (tb[2] - tb[0])
    try_op('du', '140', leaf, ell(bb[0] + (m['cx'] - tb[0]) * sx, m['cy'], m['rx'] * sx * 1.6, m['ry'] * 1.3), 140.)
# fi: one column. The lower part starts on the upper part's left edge, and nothing passes its right edge
for W in ('40', '140'):
    P = polys(geom(R[W]['fi'])); up = max(P, key=lambda p: p.centroid.y); lo = [p for p in P if p is not up]
    ub = up.bounds; L = unary_union(lo); dx = ub[0] - L.bounds[0]
    lo = [affinity.translate(p, dx, 0) for p in lo]
    over = max(p.bounds[2] for p in lo) - ub[2]
    if over > 0:                                    # the diagonal: drawn back inside the column
        dg = max(lo, key=lambda p: p.bounds[2]); rest = [p for p in lo if p is not dg]
        moved = affinity.translate(dg, -over, 0)
        if all(moved.distance(q) > 20 for q in rest + [up]): lo = rest + [moved]
    R[W]['fi'] = out(unary_union([up] + lo))
    print('fi', W, 'lower part moved', round(dx), 'overhang', round(over))
# ku Black, rebuilt: rings with an even weight, the U's inside concentric round the top ring at the gap
G = 52.0; Wv = 140.0
r1 = rrect(125, 620, 461, 910, 95); r2 = rrect(128, 0, 459, 250, 90); utop = 805
def ring(o):
    inner = nib(o, -Wv / 2 * 1.0)
    bx = inner.bounds; w_, h_ = bx[2] - bx[0], bx[3] - bx[1]; cx_, cy_ = (bx[0] + bx[2]) / 2, (bx[1] + bx[3]) / 2
    if KUEYE == 'capsule':
        ew = min(w_, 0.6 * h_); eye = rrect(cx_ - ew / 2, bx[1], cx_ + ew / 2, bx[3], ew / 2)
    else: eye = engine.lens(cx_, cy_, w_ / 2, min(h_ * 0.32, w_ * 0.3), 0)
    return o.difference(eye)
inside = nib(r1, G).union(box(r1.bounds[0] - G, (r1.bounds[1] + r1.bounds[3]) / 2, r1.bounds[2] + G, BH + 50))
U = nib(inside, Wv).difference(inside).intersection(box(-3000, -3000, 4000, utop))
U = U.buffer(-19, quad_segs=8).buffer(19, quad_segs=8)
bar = rrect(-27, 297, 613, 412, 19)
ku = unary_union([U, bar, ring(r1), ring(r2)])
print('ku black parts', sig(ku), 'U bottom', round(U.bounds[1]), 'bar', bar.bounds[1], bar.bounds[3])
R['140']['ku'] = out(ku)
json.dump(R, open(sys.argv[2], 'w'))
