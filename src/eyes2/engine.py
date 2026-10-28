"""Kɔradin Eyes, engine 2: topology is read on the Thin master and enforced on every weight.

Rule: two parts of a glyph that do not touch in Thin never touch in any weight.
 1. Every stroke centreline is sampled (same arc fractions at every weight).
 2. Thin touch graph: consecutive samples + any two samples whose Thin inks overlap. Geodesic distance
    in that graph = how far apart two points are *through the ink* in Thin.
 3. Two samples are separate parts when that geodesic is much longer than the straight distance
    (ratio > LAMBDA): the Thin glyph has white between them (counter, aperture, spiral turn, gap).
 4. Voronoi of the samples at the target weight: every ridge between two separate parts is a cut line.
    Where the heavy ink covers a cut line, a white band of width GAP is cut along it. So heavy strokes give
    up width to each other instead of merging, and every white shape of Thin survives, never narrower
    than GAP.
 5. Closed counters ("eyes") are filled and a squircle is fitted in them as the designed negative.
 6. Soft corners: inner radius (closing, before the cuts), outer radius (opening, after: can only remove ink).
"""
import json, math, sys
import numpy as np
from scipy.spatial import Voronoi, cKDTree
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import dijkstra
from shapely.geometry import Polygon, LineString, MultiLineString, Point, box
from shapely.ops import unary_union
from shapely import affinity

LAMBDA = 1.5      # geodesic / straight ratio above which two points belong to separate parts
STEP = 5.0        # sample spacing along the centrelines (Thin units)

def geoms(g):
    if g is None or g.is_empty: return []
    return list(g.geoms) if hasattr(g, "geoms") else [g]

def polys(g): return [p for p in geoms(g) if p.geom_type == "Polygon"]

def resample(P, fr):
    P = np.asarray(P, float); L = np.r_[0, np.cumsum(np.hypot(*np.diff(P, axis=0).T))]
    if L[-1] <= 0: return np.repeat(P[:1], len(fr), axis=0)
    t = fr * L[-1]
    return np.c_[np.interp(t, L, P[:, 0]), np.interp(t, L, P[:, 1])]

def samples(thin_strokes, other_strokes):
    """sample fractions from the Thin centreline; the same fractions on the other weight"""
    S0, S1, sid = [], [], []
    for i, (a, b) in enumerate(zip(thin_strokes, other_strokes)):
        P = np.asarray(a["cl"], float); L = np.hypot(*np.diff(P, axis=0).T).sum() if len(P) > 1 else 0
        n = max(2, int(math.ceil(L / STEP)) + 1); fr = np.linspace(0, 1, n)
        S0.append(resample(a["cl"], fr)); S1.append(resample(b["cl"], fr)); sid += [i] * n
    return np.vstack(S0), np.vstack(S1), np.array(sid)

def separation(S0, sid, Wthin, thin=None):
    """boolean function far(a, b): a and b are separate parts in Thin"""
    n = len(S0); rows, cols, vals = [], [], []
    for i in range(n - 1):
        if sid[i] == sid[i + 1]:
            rows.append(i); cols.append(i + 1); vals.append(np.hypot(*(S0[i + 1] - S0[i])) + 1e-6)
    T = cKDTree(S0)
    # touching in Thin: the straight path between the two samples stays inside the Thin ink
    from shapely.prepared import prep
    from shapely import contains_xy
    tink = unary_union([Polygon(s["poly"]).buffer(0) for s in thin if len(s["poly"]) >= 3]).buffer(0.8) if thin else None
    pr = T.query_pairs(Wthin * 0.98, output_type="ndarray")
    if len(pr):
        ok = np.ones(len(pr), bool)
        if tink is not None:
            for t in (0.2, 0.4, 0.5, 0.6, 0.8):
                q = S0[pr[:, 0]] * (1 - t) + S0[pr[:, 1]] * t
                ok &= contains_xy(tink, q[:, 0], q[:, 1])
        for (i, j) in pr[ok]:
            rows.append(i); cols.append(j); vals.append(np.hypot(*(S0[j] - S0[i])) + 1e-6)
    G = coo_matrix((vals, (rows, cols)), shape=(n, n)).tocsr()
    D = dijkstra(G, directed=False)
    def far(a, b):
        e = np.hypot(*(S0[a] - S0[b]))
        g = D[a, b]
        return (not np.isfinite(g)) or (g > LAMBDA * e and g - e > Wthin)
    E = np.hypot(S0[:, None, 0] - S0[None, :, 0], S0[:, None, 1] - S0[None, :, 1])
    far.M = (~np.isfinite(D)) | ((D > LAMBDA * E) & (D - E > Wthin))
    far.touch = G
    return far

def cut_lines(S, far, R=None):
    """Voronoi ridges between separate parts, at the target weight's sample positions"""
    # merge coincident samples (junctions) so Qhull does not choke
    key = np.round(S, 1); _, first, inv = np.unique(key, axis=0, return_index=True, return_inverse=True)
    inv = inv.ravel(); U = S[first]
    if len(U) < 4: return []
    V = Voronoi(U); C = U.mean(axis=0); out = []
    members = {}
    for i, u in enumerate(inv): members.setdefault(u, []).append(i)
    for (p, q), rv in zip(V.ridge_points, V.ridge_vertices):
        a, b = members[p][0], members[q][0]
        if not far(a, b): continue
        if -1 in rv:
            i = rv[0] if rv[1] == -1 else rv[1]
            if i == -1: continue
            t = U[q] - U[p]; nrm = np.array([-t[1], t[0]]) / (np.hypot(*t) or 1)
            mid = (U[p] + U[q]) / 2
            if np.dot(mid - C, nrm) < 0: nrm = -nrm
            ln = LineString([V.vertices[i], V.vertices[i] + nrm * 2000])
        else:
            ln = LineString([V.vertices[rv[0]], V.vertices[rv[1]]])
        # only where both inks really reach the ridge (ridge points are equidistant from p and q)
        if R is not None:
            ln = ln.intersection(Point(U[p]).buffer(R, quad_segs=16))
            if ln.is_empty: continue
        out.append(ln)
    return out

def squircle(cx, cy, a, b, ang, n=3.0, k=72):
    t = np.linspace(0, 2 * math.pi, k, endpoint=False); c, s = np.cos(t), np.sin(t)
    x = a * np.sign(c) * np.abs(c) ** (2 / n); y = b * np.sign(s) * np.abs(s) ** (2 / n)
    return affinity.translate(affinity.rotate(Polygon(np.c_[x, y]), ang, origin=(0, 0)), cx, cy)

def fit_eye(H):
    """the biggest squircle, in the counter's own orientation, that fits inside the counter H"""
    mrr = H.minimum_rotated_rectangle
    xy = np.array(mrr.exterior.coords)[:4]; e1, e2 = xy[1] - xy[0], xy[2] - xy[1]
    L1, L2 = np.hypot(*e1), np.hypot(*e2); v = e1 if L1 >= L2 else e2
    ang = math.degrees(math.atan2(v[1], v[0])); A, B = max(L1, L2) / 2, min(L1, L2) / 2
    best = None
    from shapely.algorithms.polylabel import polylabel
    centres = [(mrr.centroid.x, mrr.centroid.y), (H.centroid.x, H.centroid.y)]
    try: pl = polylabel(H.buffer(0), 1.0); centres.append((pl.x, pl.y))
    except Exception: pass
    Hb = H.buffer(0.5)
    for cx, cy in centres:
        for ra in (1.0, 0.85, 0.7):                # aspect: also try rounder eyes
            lo, hi = 0.0, 1.0
            for _ in range(14):
                m = (lo + hi) / 2; sq = squircle(cx, cy, A * m, B * m / ra if B * m / ra < A * m else A * m, ang)
                if Hb.contains(sq): lo = m
                else: hi = m
            if lo > 0.05:
                sq = squircle(cx, cy, A * lo, min(B * lo / ra, A * lo), ang)
                if best is None or sq.area > best.area: best = sq
    return best

EYE_CLASSES = (0.34, 0.5, 0.72, 1.0, 1.4)     # eye widths, as shares of the weight
def uniform(eye, W):
    """snap a fitted eye to the standard eye widths (never wider than it fits): eyes repeat across glyphs"""
    if eye is None: return None
    mrr = eye.minimum_rotated_rectangle; xy = np.array(mrr.exterior.coords)[:4]
    e1, e2 = xy[1] - xy[0], xy[2] - xy[1]; L1, L2 = np.hypot(*e1), np.hypot(*e2); v = e1 if L1 >= L2 else e2
    ang = math.degrees(math.atan2(v[1], v[0])); A, B = max(L1, L2) / 2, min(L1, L2) / 2
    cls = [c * W / 2 for c in EYE_CLASSES if c * W / 2 <= B + 0.5]
    if not cls: return eye
    b = max(cls); a = max(b, A - (B - b) * 0.6)
    return squircle(eye.centroid.x, eye.centroid.y, a, b, ang)

def kscale(W): return (700 - W) / 602

def thin_eyes(lines, W, Wthin, mineye):
    """every closed counter of Thin must exist in W. lines = the centrelines at W's positions; drawn at the
    Thin weight their holes are the skeleton counters; shrunk by W's half weight they give the eye; if that
    leaves nothing (or too little), a minimum eye sits in the counter's middle"""
    from shapely.algorithms.polylabel import polylabel
    sk_ink = unary_union([LineString(l).buffer(Wthin / 2, quad_segs=8) for l in lines if len(l) >= 2])
    out = []
    for p in polys(sk_ink):
        for r in p.interiors:
            sk = Polygon(r).buffer(0).buffer(Wthin / 2, quad_segs=8)       # counter bounded by the centrelines
            if sk.is_empty or sk.area < 400: continue
            sk = max(polys(sk), key=lambda g: g.area)
            E = sk.buffer(-W / 2, quad_segs=8)
            mrr = sk.minimum_rotated_rectangle; xy = np.array(mrr.exterior.coords)[:4]
            e1, e2 = xy[1] - xy[0], xy[2] - xy[1]; L1, L2 = np.hypot(*e1), np.hypot(*e2); v = e1 if L1 >= L2 else e2
            ang = math.degrees(math.atan2(v[1], v[0])); A, B = max(L1, L2) / 2, min(L1, L2) / 2
            try: pl = polylabel(sk, 1.0)
            except Exception: pl = sk.representative_point()
            room = sk.exterior.distance(pl)
            b = min(max(mineye / 2, B - W / 2), room * 0.62); a = min(max(b, A - W / 2), max(b, A * 0.62))
            eye = squircle(pl.x, pl.y, a, b, ang)
            if not E.is_empty and E.area > eye.area: eye = max(polys(E), key=lambda g: g.area)
            out.append(eye)
    return out

def ring_merge(far, S0, thin):
    """exception (ku): small rings may join the parts around them; only their eye must stay"""
    tink = unary_union([Polygon(s["poly"]).buffer(0) for s in thin if len(s["poly"]) >= 3]); comps = polys(tink)
    from shapely import contains_xy
    lab = np.full(len(S0), -1)
    for c, g in enumerate(comps): lab[contains_xy(g.buffer(1), S0[:, 0], S0[:, 1]) & (lab < 0)] = c
    ring = [len(g.interiors) > 0 and g.area < 60000 for g in comps]
    R = np.array([ring[l] if l >= 0 else False for l in lab])
    diff = lab[:, None] != lab[None, :]
    far.M = far.M & ~(diff & (R[:, None] | R[None, :]))
    f0 = far
    def f(a, b): return bool(f0.M[a, b])
    f.M = far.M; f.touch = far.touch; return f

EXCEPT = {"ku": "rings"}

def build(strokes, thin, W, Wthin, gap, ro, ri, eye_min=0.55, relax=False, key=None):
    S0, S, sid = samples(thin, strokes)
    far = separation(S0, sid, Wthin, thin)
    if W > Wthin and EXCEPT.get(key) == "rings": far = ring_merge(far, S0, thin)
    far.thin = thin
    raw = unary_union([Polygon(s["poly"]).buffer(0) for s in strokes if len(s["poly"]) >= 3])
    lines_w = [s["cl"] for s in strokes]
    if relax:
        import relax as RX
        S, raw, lines_w, alive = RX.relax(S0, S, sid, strokes, far, W, Wthin, gap)
        if not alive.all():                       # retracted ends: drop their samples, keep the index map
            keep = np.where(alive)[0]; f0 = far
            far = lambda a, b: f0(keep[a], keep[b]); S = S[keep]
    ink = raw.buffer(ri, quad_segs=8).buffer(-ri, quad_segs=8) if ri > 0.5 else raw
    lines = [l for l in cut_lines(S, far, W / 2 + gap / 2)]
    cut = None
    if lines:
        ml = unary_union(lines).intersection(raw.buffer(gap))
        if not ml.is_empty: cut = ml.buffer(gap / 2, quad_segs=8)
    A = ink.difference(cut) if cut is not None else ink
    # eyes: closed counters without islands -> squircle negative
    eyes = []
    out = []
    for p in polys(A):
        holes = []
        for r in p.interiors:
            H = Polygon(r)
            island = any(H.contains(q.representative_point()) for q in polys(A) if q is not p)
            eye = None if island or H.area < (0.25 * W) ** 2 else uniform(fit_eye(H), W)
            if eye is not None and eye.area >= eye_min * H.area: holes.append(eye); eyes.append(eye)
            else: holes.append(H)
        out.append(Polygon(p.exterior).difference(unary_union(holes)) if holes else Polygon(p.exterior))
    A = unary_union(out)
    for e in thin_eyes(lines_w, W, Wthin, max(30, 0.42 * W)):
        if not any(h.intersects(e.centroid) for p in polys(A) for h in [Polygon(r) for r in p.interiors]):
            A = A.difference(e)
    if cut is not None: A = A.difference(cut)
    rc = min(0.45 * gap, 1.6 * ri)       # round the mouths of the cuts (stays under half the gap: no cut closes)
    if rc > 0.5: A = A.buffer(rc, quad_segs=8).buffer(-rc, quad_segs=8)
    if cut is not None: A = A.difference(cut.buffer(-0.5))
    if ro > 0.5: A = A.buffer(-ro, quad_segs=8).buffer(ro, quad_segs=8)
    # spines: no stroke may be cut through. Each Thin part keeps its centreline at 0.36 W,
    # kept clear of every other Thin part (so this never joins two parts)
    tink = unary_union([Polygon(s["poly"]).buffer(0) for s in thin if len(s["poly"]) >= 3])
    tparts = polys(tink); owner = []
    for st in thin:
        c = LineString(st["cl"]).interpolate(0.5, normalized=True) if len(st["cl"]) > 1 else Point(st["cl"][0])
        owner.append(min(range(len(tparts)), key=lambda i: tparts[i].distance(c)) if tparts else 0)
    sp = {}
    for i, l in enumerate(lines_w):
        if len(l) >= 2: sp.setdefault(owner[i], []).append(LineString(l).buffer(0.18 * W, cap_style=2, quad_segs=6))
    sp = {k: unary_union(v) for k, v in sp.items()}
    for k, v in sp.items():
        others = [w for j, w in sp.items() if j != k]
        if others: v = v.difference(unary_union(others).buffer(gap + 0.18 * W))
        A = A.union(v.intersection(box(-3000, 0, 4000, 700)))
    A = unary_union([p for p in polys(A.buffer(0)) if p.area > 0.15 * W * W])   # crumbs left by the cuts
    return A.buffer(0), dict(cut=cut, eyes=eyes, raw=raw, S=S, lines=lines)

PRESETS = {  # weight: gap, outer radius, inner radius
    40: dict(gap=14, ro=4, ri=3),
    150: dict(gap=46, ro=20, ri=10, relax=True),
}

def run(path, out):
    D = json.load(open(path)); res = {}
    Wt = min(D["WS"])
    for W in D["WS"]:
        P = PRESETS.get(W) or dict(gap=0.3 * W, ro=0.13 * W, ri=0.07 * W)
        res[W] = {}
        for k in D["keys"]:
            g, _ = build(D["G"][k][str(W)], D["G"][k][str(Wt)], float(W), float(Wt), key=k, **P)
            res[W][k] = [[np.round(np.array(p.exterior.coords), 1).tolist()] + [np.round(np.array(r.coords), 1).tolist() for r in p.interiors] for p in polys(g)]
    json.dump(res, open(out, "w"))

if __name__ == "__main__":
    run(sys.argv[1], sys.argv[2])
