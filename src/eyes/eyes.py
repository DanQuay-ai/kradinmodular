"""Kɔradin Eyes: strokes -> ink; every counter ("eye") is filled solid, then a designed negative is fitted in it.
Negative = a squircle (superellipse) in the counter's own orientation, kept a wall away from the strokes;
when the counter is too tight, a minimum eye (a capsule slot) sits on its pole of inaccessibility."""
import json, math, sys, numpy as np
from shapely.geometry import Polygon, MultiPolygon, Point, LineString
from shapely.ops import unary_union
from shapely import affinity
from shapely.algorithms.polylabel import polylabel

def geoms(g): return [] if g.is_empty else list(g.geoms) if hasattr(g, "geoms") else [g]
def squircle(cx, cy, a, b, ang, n=3.2, k=64):
    t = np.linspace(0, 2 * math.pi, k, endpoint=False); c, s = np.cos(t), np.sin(t)
    x = a * np.sign(c) * np.abs(c) ** (2 / n); y = b * np.sign(s) * np.abs(s) ** (2 / n)
    return affinity.translate(affinity.rotate(Polygon(np.c_[x, y]), ang, origin=(0, 0)), cx, cy)
def capsule(cx, cy, L, w, ang): return affinity.rotate(LineString([(cx - L / 2, cy), (cx + L / 2, cy)]).buffer(w / 2, quad_segs=12), ang, origin=(cx, cy))

def counters(ink, W, close):
    """closed holes + 'eyes' that are almost closed (gap under `close`)"""
    out = []
    for p in geoms(ink):
        out += [Polygon(r) for r in p.interiors]
    shut = ink.buffer(close, quad_segs=8).buffer(-close, quad_segs=8)
    for p in geoms(shut):
        for r in p.interiors:
            h = Polygon(r).difference(ink)
            for q in geoms(h):
                if q.area > 0.15 * W * W and not any(q.intersects(o) and q.intersection(o).area > 0.5 * q.area for o in out): out.append(q)
    return [c for c in out if c.area > 4]

def fit_eye(C, W, wall, minw):
    inner = C.buffer(-wall, quad_segs=8)
    mrr = (inner if not inner.is_empty and inner.area > minw * minw else C).minimum_rotated_rectangle
    xy = np.array(mrr.exterior.coords)[:4]; e1, e2 = xy[1] - xy[0], xy[2] - xy[1]
    L1, L2 = np.hypot(*e1), np.hypot(*e2); ang = math.degrees(math.atan2(*(e1 if L1 >= L2 else e2)[::-1]))
    cx, cy = mrr.centroid.x, mrr.centroid.y; A, B = max(L1, L2) / 2, min(L1, L2) / 2
    if not inner.is_empty and inner.area > minw * minw:
        for s in np.linspace(1.0, 0.45, 12):              # biggest squircle that fits the inner counter
            sq = squircle(cx, cy, A * s, B * s, ang)
            if inner.buffer(1).contains(sq): return sq
        sq = squircle(cx, cy, A, B, ang).intersection(inner)
        if sq.area > minw * minw * .6: return sq.buffer(-minw * .2).buffer(minw * .2)
    # minimum eye: a slot on the pole of inaccessibility, along the counter
    pl = polylabel(max(geoms(C), key=lambda g: g.area), 1.0)
    room = C.exterior.distance(pl) if hasattr(C, "exterior") else 0
    w = max(minw * .8, min(minw, 2 * room * .8)); Lc = max(w, 2 * A * .75)
    eye = capsule(pl.x, pl.y, Lc, w, ang)
    return eye if C.buffer(-0.5).contains(eye) or eye.difference(C).area < 0.25 * eye.area else eye.intersection(C.buffer(-1))

def glyph(polys, W, skel):
    """polys: the strokes at weight W. skel: the same strokes, same positions, drawn hairline (22 units):
    the counters are read on the skeleton, so they exist even where the heavy strokes swallow them."""
    ink = unary_union([Polygon(p).buffer(0) for p in polys if len(p) >= 3])
    sk = unary_union([Polygon(p).buffer(0) for p in skel if len(p) >= 3])
    t = (W - 40) / 75
    close = 11 + W * (0.45 + 0.2 * t)               # skeleton gap under which an open counter counts as an eye
    wall = W * (0.30 + 0.12 * t)                    # from the skeleton line to the negative: the stroke that stays
    minw = max(22, W * (0.22 + 0.06 * t))           # the smallest eye
    Cs = [c for c in counters(sk, W, close) if c.area > (W * 0.6) ** 2]
    solid = unary_union([ink] + [c.buffer(0.5) for c in Cs])
    neg = [fit_eye(c, W, wall - 11, minw) for c in Cs]
    # open counters / apertures that the heavy strokes swallowed: the white of the skeleton (inside its hull)
    # stays white wherever it is more than `wall` from the skeleton line, rounded; tiny bits are dropped
    hull = sk.convex_hull; ap = []
    for comp in geoms(hull.difference(sk.buffer(0.5))):
        if any(comp.intersection(c).area > 0.5 * comp.area for c in Cs): continue
        a = comp.buffer(-(wall - 11), quad_segs=8)
        if a.is_empty: continue
        a = a.buffer(-minw * .35, quad_segs=8).buffer(minw * .35, quad_segs=8)
        if not a.is_empty and a.intersection(ink).area > 0.2 * minw * minw: ap.append(a)
    out = solid.difference(unary_union(neg + ap)) if neg or ap else solid
    return out.buffer(0), Cs, neg

if __name__ == "__main__":
    D = json.load(open(sys.argv[1])); res = {}
    for W in D["W"]:
        res[W] = {}
        for k in D["keys"]:
            g, Cs, neg = glyph(D["W"][W][k], float(W), D["S"][W][k])
            res[W][k] = [[list(map(list, np.round(np.array(p.exterior.coords), 1)))] + [list(map(list, np.round(np.array(r.coords), 1))) for r in p.interiors] for p in geoms(g) if p.geom_type == "Polygon"]
    json.dump(res, open(sys.argv[2], "w"))
