"""Auto-trace a reference font into stroke skeletons for the Construction lab.

  python3 autotrace.py FONT OUT.json --chars "ABC..." [--name "Libre Franklin"] [--ghost GHOST.json]

Method
  1. Render each glyph with the cap height scaled to 700 units (1 px per unit), baseline at y 0.
  2. Measure the stroke weight W: twice the median distance from the medial axis to the edge.
  3. Skeletonise the ink, prune spurs shorter than about one stroke weight, build a graph of
     end points and junctions, and split it into edges.
  4. Rebuild strokes by good continuation: at each junction the two edges that run on most
     straight (within 40 degrees) become one stroke; the rest end on the junction, that is on
     the centreline of the stroke they join.
  5. Free ends are pushed back out to the edge of the ink along their tangent (the medial axis
     stops half a stroke short).
  6. Each stroke is fitted with straight lines and circular arcs (tolerance about W/8) and
     written as turtle segments: L len, A r,ang (+ anticlockwise), C ang for a sharp corner.
Ends are plain ("butt"): Latin glyphs are not cut flat at the baseline/top like Kɔradin.
"""
import argparse, json, math, os
import numpy as np, freetype
from scipy import ndimage
from skimage.morphology import skeletonize
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen

def cross2(v, P):
    P = np.atleast_2d(P); return v[0] * P[:, 1] - v[1] * P[:, 0]


CUTS = []
VARIANT = {}

N8 = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]


def render(face, ch, scale, pad=40):
    face.load_char(ch, freetype.FT_LOAD_NO_HINTING | freetype.FT_LOAD_NO_BITMAP | freetype.FT_LOAD_RENDER)
    g = face.glyph; b = g.bitmap
    if b.width == 0: return None
    a = np.array(b.buffer, dtype=np.uint8).reshape(b.rows, b.pitch)[:, :b.width] > 127
    a = np.pad(a, pad)
    # image row r -> y = top - (r - pad) ; col c -> x = left + c - pad   (in px == design units)
    return a, g.bitmap_left - pad, g.bitmap_top + pad, g.advance.x / 64


def graph(sk):
    pts = set(zip(*np.nonzero(sk)))
    nb = {p: [(p[0] + d[0], p[1] + d[1]) for d in N8 if (p[0] + d[0], p[1] + d[1]) in pts] for p in pts}
    # thin 4-connected corners: drop diagonal links that duplicate an orthogonal path
    for p in pts:
        nb[p] = [q for q in nb[p] if not (abs(q[0] - p[0]) == 1 and abs(q[1] - p[1]) == 1 and
                 ((p[0], q[1]) in pts or (q[0], p[1]) in pts))]
    return pts, nb


def edges_of(pts, nb):
    nodes = {p for p in pts if len(nb[p]) != 2}
    seen = set(); E = []
    for n in nodes:
        for q in nb[n]:
            if (n, q) in seen: continue
            path = [n, q]; seen.add((n, q)); seen.add((q, n)); prev, cur = n, q
            while cur not in nodes:
                nxt = [r for r in nb[cur] if r != prev]
                if not nxt: break
                prev, cur = cur, nxt[0]; path.append(cur); seen.add((prev, cur)); seen.add((cur, prev))
            E.append(path)
    # pure loops (no nodes)
    rest = pts - {p for e in E for p in e}
    while rest:
        s = rest.pop(); path = [s]; prev, cur = None, s
        while True:
            nxt = [r for r in nb[cur] if r != prev and (r in rest or (r == s and len(path) > 2))]
            if not nxt: break
            prev, cur = cur, nxt[0]
            if cur == s: path.append(s); break
            path.append(cur); rest.discard(cur)
        if len(path) > 8: E.append(path)
    return E


def prune(sk, W, rounds=3):
    for _ in range(rounds):
        pts, nb = graph(sk)
        E = edges_of(pts, nb); changed = False
        for e in E:
            a, b = e[0], e[-1]
            if a == b: continue
            da, db = len(nb[a]), len(nb[b])
            if (da == 1) != (db == 1) and len(e) < 0.9 * W:
                for p in (e[:-1] if da == 1 else e[1:]): sk[p] = False
                changed = True
        if not changed: break
        sk = skeletonize(sk)
    return sk


def tangent(path, at_start, L):
    p = path if at_start else path[::-1]
    k = min(len(p) - 1, max(2, int(L)))
    a, b = np.array(p[0], float), np.array(p[k], float)
    v = b - a; n = np.hypot(*v)
    return v / n if n else v   # pointing into the edge, away from the node


def merge(E, nb, W):
    """join edges through junctions by good continuation"""
    E = [list(e) for e in E]
    junction = lambda p: len(nb[p]) >= 3
    while True:
        best = None
        ends = {}
        for i, e in enumerate(E):
            if e[0] == e[-1]: continue
            for at in (0, 1):
                p = e[0] if at == 0 else e[-1]
                if junction(p): ends.setdefault(p, []).append((i, at))
        # junction pixels within a few px count as one node
        keys = list(ends)
        groups = []
        for k in keys:
            for g in groups:
                if math.dist(k, g[0]) < W * 0.7: g.append(k); break
            else: groups.append([k])
        for g in groups:
            items = [it for k in g for it in ends[k]]
            for x in range(len(items)):
                for y in range(x + 1, len(items)):
                    (i, a), (j, b) = items[x], items[y]
                    if i == j: continue
                    ta = tangent(E[i], a == 0, 1.5 * W); tb = tangent(E[j], b == 0, 1.5 * W)
                    straight = -float(ta @ tb)       # 1 = runs straight through
                    if straight > math.cos(math.radians(40)) and (best is None or straight > best[0]):
                        best = (straight, i, a, j, b)
        if not best: break
        _, i, a, j, b = best
        ei = E[i] if a == 1 else E[i][::-1]
        ej = E[j] if b == 0 else E[j][::-1]
        E[i] = ei + ej[1:]; del E[j]
    return E


def extend(path, ink, dist, W):
    """push free ends out to the ink edge"""
    out = [tuple(map(float, p)) for p in path]
    for at in (0, 1):
        p = np.array(out[0] if at == 0 else out[-1])
        t = -tangent(path, at == 0, W)              # outward
        q = p.copy(); steps = 0
        while steps < 2 * W:
            r = q + t
            ri, ci = int(round(r[0])), int(round(r[1]))
            if not (0 <= ri < ink.shape[0] and 0 <= ci < ink.shape[1]) or not ink[ri, ci]: break
            q = r; steps += 1
        if steps:
            if at == 0: out.insert(0, tuple(q))
            else: out.append(tuple(q))
    return out


def rdp(P, eps):
    P = np.asarray(P, float)
    if len(P) < 3: return P
    a, b = P[0], P[-1]; v = b - a; L = np.hypot(*v)
    d = np.abs(cross2(v, P - a)) / L if L else np.hypot(*(P - a).T)
    i = int(np.argmax(d))
    if d[i] > eps: return np.vstack([rdp(P[:i + 1], eps)[:-1], rdp(P[i:], eps)])
    return np.array([a, b])


def circle_fit(P):
    x, y = P[:, 0], P[:, 1]
    A = np.c_[2 * x, 2 * y, np.ones(len(P))]; bb = x * x + y * y
    try: cx, cy, c = np.linalg.lstsq(A, bb, rcond=None)[0]
    except Exception: return None
    r = math.sqrt(max(c + cx * cx + cy * cy, 0))
    err = np.abs(np.hypot(x - cx, y - cy) - r).max()
    return cx, cy, r, err


def resample(P, step):
    P = np.asarray(P, float); d = np.r_[0, np.cumsum(np.hypot(*np.diff(P, axis=0).T))]
    if d[-1] < step: return P
    s = np.arange(0, d[-1], step); s = np.r_[s, d[-1]]
    return np.c_[np.interp(s, d, P[:, 0]), np.interp(s, d, P[:, 1])]


def fit_pieces(P, tol, W):
    """greedy lines and arcs over a densely sampled path (x, y in design units)"""
    P = resample(P, 4.0); out = []; i = 0; n = len(P)
    while i < n - 1:
        best = None
        j = i + 2
        while j <= n:
            Q = P[i:j]; a, b = Q[0], Q[-1]; v = b - a; L = np.hypot(*v)
            line_err = (np.abs(cross2(v, Q - a)) / L).max() if L else 1e9
            arc = circle_fit(Q) if len(Q) >= 4 else None
            ok_line = line_err < tol
            ok_arc = arc is not None and arc[3] < tol and arc[2] > W * 0.45 and arc[2] < 4000
            if ok_line: best = ("L", j)
            elif ok_arc: best = ("A", j, arc)
            elif best and j - best[1] > 3: break
            j += 1
        if not best: best = ("L", min(i + 2, n))
        out.append((best[0], P[i:best[1]], best[2] if best[0] == "A" else None))
        i = best[1] - 1
    # merge consecutive lines that are colinear
    return out


def to_turtle(pieces, cap="butt", corner=28):
    """turtle segments that hit every piece end exactly. Inside a stroke the heading is continuous
    (lines become flat arcs when they would kink); a sharp corner (> corner degrees) stays a corner."""
    def ang(v): return math.degrees(math.atan2(v[1], v[0]))
    def turn(a, b): return ((b - a + 180) % 360) - 180
    P0 = pieces[0][1][0]; pos = np.array(P0, float); segs = []; h = None; h0 = None
    for kind, Q, arc in pieces:
        E = np.array(Q[-1], float); v = E - pos; d = float(np.hypot(*v))
        if d < 0.8: continue
        # the heading the data wants at the start of this piece
        k = min(len(Q) - 1, 3); want = ang(np.array(Q[k]) - np.array(Q[0])) if kind == "A" else ang(v)
        if h is None: h = want; h0 = want
        elif abs(turn(h, want)) > corner: segs.append({"t": "C", "ang": round(turn(h, want), 2)}); h = want
        phi = math.radians(turn(h, ang(v)))
        if abs(math.sin(phi)) < 0.004 or (kind == "L" and abs(math.degrees(phi)) < 0.3):
            segs.append({"t": "L", "len": round(d, 1)})
            h = ang(v) if abs(math.degrees(phi)) < 0.3 else h
        else:
            r = d / (2 * abs(math.sin(phi))); sweep = 2 * math.degrees(phi)
            if r > 20000: segs.append({"t": "L", "len": round(d, 1)})
            else: segs.append({"t": "A", "r": round(r, 1), "ang": round(sweep, 2)}); h += sweep
        pos = E
    if h0 is None: return None
    return {"x": round(float(P0[0]), 1), "y": round(float(P0[1]), 1), "h": round(h0 % 360, 2), "segs": segs,
            "s": 0, "e": 1, "cap0": cap, "cap1": cap}


def biarc_turtle(D, W, corner=40):
    """G1 arc spline: knots every ~W/1.5 along the path (and at sharp corners), a biarc between knots
    matching the data tangent at both ends. Smooth everywhere, exact at every knot, no kinks."""
    D = resample(np.asarray(D, float), 2.0)
    if len(D) < 3:
        v = D[-1] - D[0]; return {"x": round(float(D[0][0]), 1), "y": round(float(D[0][1]), 1), "h": round(math.degrees(math.atan2(v[1], v[0])) % 360, 2), "segs": [{"t": "L", "len": round(float(np.hypot(*v)), 1)}], "s": 0, "e": 1, "cap0": "butt", "cap1": "butt"}
    Ls = np.r_[0, np.cumsum(np.hypot(*np.diff(D, axis=0).T))]; T = Ls[-1]
    win = max(3, int(W / 3 / 2))
    def tan(i, side):
        a = max(0, i - win) if side <= 0 else i; b = min(len(D) - 1, i + win) if side >= 0 else i
        v = D[b] - D[a]; n = np.hypot(*v); return v / n if n else np.array([1.0, 0])
    # corners
    cor = []
    for i in range(1, len(D) - 1):
        ti, to = tan(i, -1), tan(i, 1)
        if math.degrees(math.acos(max(-1, min(1, ti @ to)))) > corner: cor.append(i)
    cor = [c for j, c in enumerate(cor) if not j or c - cor[j - 1] > 2 * win]
    step = max(20.0, W / 1.5)
    knots = sorted(set([0, len(D) - 1] + cor + [int(np.searchsorted(Ls, s_)) for s_ in np.arange(step, T - step / 2, step)]))
    knots = [k for j, k in enumerate(knots) if j == 0 or k - knots[j - 1] >= 3 or k == len(D) - 1]
    def ang(v): return math.degrees(math.atan2(v[1], v[0]))
    def turn(a, b): return ((b - a + 180) % 360) - 180
    segs = []; h = ang(tan(0, 1)); h0 = h; pos = D[0].copy()
    def arc_to(E):
        nonlocal h, pos
        v = E - pos; d = float(np.hypot(*v))
        if d < 0.3: return
        phi = math.radians(turn(h, ang(v)))
        if abs(math.sin(phi)) < 0.003: segs.append({"t": "L", "len": round(d, 1)})
        else:
            r = d / (2 * abs(math.sin(phi))); sw = 2 * math.degrees(phi)
            if r > 30000: segs.append({"t": "L", "len": round(d, 1)})
            else: segs.append({"t": "A", "r": round(r, 1), "ang": round(sw, 2)}); h += sw
        pos = E.copy()
    for a, b in zip(knots, knots[1:]):
        t0 = np.array([math.cos(math.radians(h)), math.sin(math.radians(h))])
        tin = tan(a, 1)
        if a in cor or a == 0:
            want = ang(tin)
            if abs(turn(h, want)) > 0.5 and a != 0: segs.append({"t": "C", "ang": round(turn(h, want), 2)})
            h = want; t0 = tin
        t1 = tan(b, -1) if b in cor or b == len(D) - 1 else tan(b, 0)
        P0, P1 = pos, D[b]; v = P1 - P0; tt = t0 + t1
        c = v @ v; bb = 2 * (v @ tt); aa = 2 * (1 - t0 @ t1)
        if abs(aa) < 1e-6: dd = c / (4 * (v @ t1)) if abs(v @ t1) > 1e-6 else 0
        else:
            disc = bb * bb + 4 * aa * c; dd = (-bb + math.sqrt(max(0, disc))) / (2 * aa)
        if not np.isfinite(dd) or dd <= 0: arc_to(P1); continue
        J = (P0 + P1 + dd * (t0 - t1)) / 2
        arc_to(J); arc_to(P1)
    return {"x": round(float(D[0][0]), 1), "y": round(float(D[0][1]), 1), "h": round(h0 % 360, 2), "segs": segs, "s": 0, "e": 1, "cap0": "butt", "cap1": "butt"}


def walk_end(st):
    x, y, h = st["x"], st["y"], st["h"]
    for g in st["segs"]:
        if g["t"] == "C": h += g["ang"]
        elif g["t"] == "L": x += g["len"] * math.cos(math.radians(h)); y += g["len"] * math.sin(math.radians(h))
        else:
            sg = 1 if g["ang"] > 0 else -1; r = g["r"]
            cx = x + r * math.cos(math.radians(h + 90 * sg)); cy = y + r * math.sin(math.radians(h + 90 * sg))
            a0 = math.atan2(y - cy, x - cx) + math.radians(g["ang"])
            x, y = cx + r * math.cos(a0), cy + r * math.sin(a0); h += g["ang"]
    return x, y


def smooth(P, sigma):
    if len(P) < 5 or sigma < 0.5: return P
    Q = ndimage.gaussian_filter1d(P, sigma, axis=0, mode="nearest")
    Q[0], Q[-1] = P[0], P[-1]
    return Q


def sharpen_corners(P, W):
    """an L corner comes out of the medial axis as a small curve: rebuild it as a sharp vertex"""
    P = np.asarray(P, float)
    if len(P) < 8: return P
    d = np.r_[0, np.cumsum(np.hypot(*np.diff(P, axis=0).T))]
    win = max(3.0, 0.9 * W)
    def head(i, back):
        j = i
        while 0 < j < len(P) - 1 and abs(d[j] - d[i]) < win: j += -1 if back else 1
        v = P[i] - P[j] if back else P[j] - P[i]
        return math.atan2(v[1], v[0]), j
    out = [P[0]]; i = 1
    while i < len(P) - 1:
        a, ja = head(i, True); b, jb = head(i, False)
        turn = abs(((math.degrees(b - a) + 180) % 360) - 180)
        if turn > 55 and ja > 0 and jb < len(P) - 1:
            # intersect the incoming and outgoing lines
            p0, p1 = P[ja], P[jb]; u = np.array([math.cos(a), math.sin(a)]); v = np.array([math.cos(b), math.sin(b)])
            M = np.array([u, -v]).T
            try:
                t = np.linalg.solve(M, p1 - p0); X = p0 + t[0] * u
                if np.hypot(*(X - P[i])) < 1.5 * W:
                    while out and np.hypot(*(out[-1] - P[ja])) > 1e-6 and len(out) > 1 and d[min(len(d)-1, i)] - 0 > 0 and np.hypot(*(out[-1] - X)) < win * 1.2: out.pop()
                    out += [X, X]; i = jb; continue
            except np.linalg.LinAlgError: pass
        out.append(P[i]); i += 1
    out.append(P[-1])
    return np.array(out)


def chord(ink, p, n, lim):
    """distance to the ink edge on each side of p along the normal n (in px)"""
    out = []
    for sg in (1, -1):
        t = 0.0
        while t < lim:
            q = p + n * (t + 0.5) * sg; r, c = int(round(q[0])), int(round(q[1]))
            if not (0 <= r < ink.shape[0] and 0 <= c < ink.shape[1]) or not ink[r, c]: break
            t += 0.5
        out.append(t)
    return out


def chords(ink, P, N, lim):
    """vectorised chord(): distances to the ink edge on both sides for every point"""
    ts = np.arange(0.5, lim + 0.5, 0.5)
    out = []
    for sg in (1, -1):
        Q = P[:, None, :] + sg * N[:, None, :] * ts[None, :, None]
        r = np.clip(np.rint(Q[..., 0]).astype(int), 0, ink.shape[0] - 1); c = np.clip(np.rint(Q[..., 1]).astype(int), 0, ink.shape[1] - 1)
        inside = ink[r, c] & (Q[..., 0] >= 0) & (Q[..., 1] >= 0) & (Q[..., 0] < ink.shape[0]) & (Q[..., 1] < ink.shape[1])
        run = np.cumprod(inside, axis=1)
        out.append(run.sum(axis=1) * 0.5)
    return out[0], out[1]


def normals(P):
    T = np.gradient(P, axis=0); T /= np.maximum(1e-9, np.hypot(*T.T))[:, None]
    return np.c_[-T[:, 1], T[:, 0]], T


def refine(P, ink, W, free, closed):
    """move each centreline point to the middle of the ink chord across it and read the true width there;
    ink chords that run into another stroke (junctions) are ignored. Free ends are then grown along the
    stroke while ink remains, measuring the width as they go: tapers, flares and blobs come out of that."""
    P = np.asarray(P, float).copy()
    ws = np.full(len(P), W)
    for it in range(3):
        N, _ = normals(P); ok = np.zeros(len(P), bool); newP = P.copy()
        med = np.median(ws)
        A, B = chords(ink, P, N, 2.4 * med + 4)
        Wd = A + B
        ok = (Wd < 2.3 * med + 2) & (A < 2.4 * med + 4) & (B < 2.4 * med + 4)
        # a chord that runs into a crossing stroke jumps far above its neighbours: drop it
        loc = ndimage.median_filter(np.where(ok, Wd, med), size=max(5, int(2.5 * W / 1.5) | 1), mode="nearest")
        if VARIANT.get('local', True): ok &= Wd < 1.4 * loc + 2
        newP = np.where(ok[:, None], P + N * ((A - B) / 2)[:, None], P); ws = np.where(ok, Wd, ws)
        if ok.sum() < 2: break
        idx = np.arange(len(P))
        ws = np.interp(idx, idx[ok], ws[ok])
        for k in (0, 1): newP[:, k] = np.interp(idx, idx[ok], newP[ok, k])
        sig = max(1.0, W / 6)
        P = smooth(newP, sig) if not closed else ndimage.gaussian_filter1d(newP, sig, axis=0, mode="wrap")
        ws = ndimage.gaussian_filter1d(ws, max(1.0, W / 10), mode="wrap" if closed else "nearest")
    # free ends: no smoothing of the width there (flares, feet, tapers are short)
    N, _ = normals(P); A, B = chords(ink, P, N, 3 * np.median(ws) + 4); raw = A + B
    Ls = np.r_[0, np.cumsum(np.hypot(*np.diff(P, axis=0).T))]; T = Ls[-1] or 1
    for at in (0, 1):
        if not free[at]: continue
        near = (Ls < W * 0.6) if at == 0 else (Ls > T - W * 0.6)
        raw_ok = near & (raw < 3 * np.median(ws))
        ws = np.where(raw_ok, np.maximum(ws, ndimage.median_filter(raw, 3)), ws)
    # grow free ends
    for at in (0, 1):
        if not free[at]: continue
        seq = P if at == 0 else P[::-1]; wseq = ws if at == 0 else ws[::-1]
        k = min(len(seq) - 1, max(2, int(W / 1.5)))
        t = seq[0] - seq[k]; t /= (np.hypot(*t) or 1); n = np.array([-t[1], t[0]])
        add, aw = [], []; q = seq[0].copy()
        for step in range(int(0.8 * W)):
            q2 = q + t * 1.5
            a, b = chord(ink, q2, n, 3 * W)
            if a + b < 1.0 or (aw and a + b > 1.6 * aw[-1] + 2): break
            q = q2 + n * (a - b) / 2; add.append(q.copy()); aw.append(a + b)
        if add:
            add = np.array(add[::-1]); aw = np.array(aw[::-1])
            if at == 0: P = np.vstack([add, P]); ws = np.r_[aw, ws]
            else: P = np.vstack([P, add[::-1]]); ws = np.r_[ws, aw[::-1]]
    return P, ws


def trace_glyph(face, ch, scale, S=2, lines=()):
    r = render(face, ch, scale * S, pad=40 * S)
    if r is None: return None, None, 0, None
    ink, left, top, adv = r
    lines_px = [top - y * S for y in lines]
    dist = ndimage.distance_transform_edt(ink)
    sk = skeletonize(ink)
    W = float(np.median(dist[sk])) * 2 if sk.any() else 0      # in px (= S per unit)
    sk = prune(sk, W * 1.2)
    pts, nb = graph(sk)
    strokes = []
    if pts:
        E = merge(edges_of(pts, nb), nb, W)
        nodes_deg = {p: len(nb[p]) for p in pts}
        for e in E:
            if len(e) < max(4, W * 0.35): continue
            P = [np.array(p, float) for p in e]
            closed = e[0] == e[-1]
            # junction ends: drop the curl inside the junction, come back in straight along the stroke
            for at in ((0, 1) if not closed else ()):
                node = P[0] if at == 0 else P[-1]
                if nodes_deg.get(tuple(map(int, node)), 1) < 3: continue
                rj = dist[int(node[0]), int(node[1])] * 1.15
                seq = P if at == 0 else P[::-1]
                k = 0
                while k < len(seq) - 3 and np.hypot(*(seq[k] - node)) < rj: k += 1
                if k < 2: continue
                kk = min(len(seq) - 1, k + int(W))
                t = seq[k] - seq[kk]; t /= (np.hypot(*t) or 1)
                L = np.hypot(*(node - seq[k]))
                rebuilt = [seq[k] + t * L * (j / 4) for j in range(4, 0, -1)] + list(seq[k:])
                P = rebuilt if at == 0 else rebuilt[::-1]
            P = np.array(P)
            if not closed:
                P = np.array(extend([tuple(p) for p in P], ink, dist, W))
            P = resample(P, 1.5 * S)
            P = smooth(P, max(1.0, W / 8))
            free = (not closed and nodes_deg.get(tuple(map(int, e[0])), 1) < 3, not closed and nodes_deg.get(tuple(map(int, e[-1])), 1) < 3)
            P, ws = refine(P, ink, W, free, closed)
            if len(P) < 3: continue
            P0_ = P.copy(); P = sharpen_corners(P, W)
            # widths follow the nearest original point (sharpening removes points around corners)
            from scipy.spatial import cKDTree
            ws = ws[cKDTree(P0_).query(P)[1]]
            cap = ["butt", "butt"]
            # serif / foot logic: a free end that stops near an alignment line runs straight on through it
            # and is cut flat on the line; its width there is the ink measured along the line
            for at in (0, 1):
                if not free[at] or not lines_px: continue
                seq = P if at == 0 else P[::-1]; wq = ws if at == 0 else ws[::-1]
                # the medial axis bends into the corner of a foot: drop the last stretch, take the direction
                # from the stretch before it, and come back in straight
                Lq = np.r_[0, np.cumsum(np.hypot(*np.diff(seq, axis=0).T))]
                cut_i = int(np.searchsorted(Lq, 0.9 * W)); far_i = int(np.searchsorted(Lq, 2.2 * W))
                if far_i >= len(seq) - 2: continue
                t = seq[cut_i] - seq[far_i]; t /= (np.hypot(*t) or 1)
                if abs(t[0]) < 0.8: continue                       # rows = vertical; only near-vertical ends get a foot
                Lr = min(lines_px, key=lambda r_: abs(r_ - seq[0][0]))
                if abs(Lr - seq[0][0]) > 0.9 * W or (Lr - seq[0][0]) * t[0] < -0.35 * W: continue
                seq = seq[cut_i:]; wq = wq[cut_i:]
                P = seq if at == 0 else seq[::-1]; ws = wq if at == 0 else wq[::-1]
                steps = (Lr - seq[0][0]) / t[0] + 2.0
                if steps <= 0: continue
                ext = [seq[0] + t * u for u in np.arange(steps, 0, -1.5)]
                # foot width: ink measured along the line just inside it, around the stroke
                rr = int(round(Lr - np.sign(t[0]) * 3)); cc = int(round(seq[0][1] + t[1] * (Lr - seq[0][0]) / t[0]))
                row = ink[min(max(rr, 0), ink.shape[0] - 1)]; cc = min(max(cc, 1), len(row) - 2); l_ = cc; r_ = cc
                while l_ > 0 and row[l_ - 1] and cc - l_ < 3 * W: l_ -= 1
                while r_ < len(row) - 1 and row[r_ + 1] and r_ - cc < 3 * W: r_ += 1
                fw = (r_ - l_ + 1) * abs(t[0]) if row[min(max(cc, 0), len(row) - 1)] else (ws[0] if at == 0 else ws[-1])
                wseq = (ws if at == 0 else ws[::-1]).copy()
                # the foot flares over about one stroke weight above the line
                Lw = np.r_[0, np.cumsum(np.hypot(*np.diff(P if at == 0 else P[::-1], axis=0).T))]
                span = 1.2 * W
                u = np.clip(Lw / span, 0, 1); wseq = np.maximum(wseq, fw + (wseq - fw) * (3 * u * u - 2 * u ** 3))
                if at == 0: ws = wseq
                else: ws = wseq[::-1]
                ramp = np.full(len(ext), fw)
                if at == 0: P = np.vstack([np.array(ext), P]); ws = np.r_[ramp, ws]
                else: P = np.vstack([P, np.array(ext)[::-1]]); ws = np.r_[ws, ramp[::-1]]
                cap[at] = "auto"
            Ls = np.r_[0, np.cumsum(np.hypot(*np.diff(P, axis=0).T))]; T = Ls[-1] or 1
            D = np.array([[(left + c) / S, (top - rr) / S] for rr, c in P])
            st = biarc_turtle(D, W / S)
            if not st or not st["segs"]: continue
            st["cap0"], st["cap1"] = cap
            n = 33; tt = (1 - np.cos(np.linspace(0, np.pi, n))) / 2   # denser near the ends, where flares and tapers live
            wp = np.interp(tt * T, Ls, ws) / W
            if wp.max() - wp.min() > 0.06: st["wp"] = [[round(float(a), 3), round(float(b), 3)] for a, b in zip(tt, wp)]
            else: st["wk"] = round(float(np.median(wp)), 3)
            strokes.append(st)
    # small separate marks (dots of i, j, punctuation) whose skeleton was pruned away
    lab, n = ndimage.label(ink)
    for c in range(1, n + 1):
        m = lab == c
        if (sk & m).sum() > W * 1.6: continue
        rr, cc = np.nonzero(m); h = (rr.max() - rr.min() + 1) / S; w = (cc.max() - cc.min() + 1) / S
        x0, y0 = (left + (cc.min() + cc.max()) / 2) / S, (top - (rr.min() + rr.max()) / 2) / S
        vert = h >= w; L = h if vert else w; thick = (w if vert else h) / (W / S)
        strokes.append({"x": round(float(x0 if vert else x0 - L / 2), 1), "y": round(float(y0 - L / 2 if vert else y0), 1), "h": 90 if vert else 0,
                        "segs": [{"t": "L", "len": round(float(L), 1)}], "s": 0, "e": 1, "cap0": "butt", "cap1": "butt", "wk": round(float(thick), 3)})
    strokes.sort(key=lambda s: (round(s["x"] / 60), -s["y"]))
    return strokes, W / S, adv / S, (ink, left, top, S)


def score(strokes, W, raster):
    """share of the reference ink covered, and share of the rebuild that falls outside it"""
    ink, left, top, S = raster
    from PIL import Image, ImageDraw
    im = Image.new("L", (ink.shape[1], ink.shape[0]), 0); dr = ImageDraw.Draw(im)
    for st in strokes:
        for poly in outline_polys(st, W):
            dr.polygon([(x * S - left, top - y * S) for x, y in poly], fill=255)
    rb = np.array(im) > 127
    inter = (rb & ink).sum(); return round(inter / max(1, ink.sum()), 3), round((rb & ~ink).sum() / max(1, rb.sum()), 3)


def outline_polys(st, W):
    """python mirror of KS.polygon for plain ends with width profile (for scoring)"""
    pts = [(st["x"], st["y"], st["h"])]; x, y, h = st["x"], st["y"], st["h"]
    for g in st["segs"]:
        if g["t"] == "C": h += g["ang"]; pts.append((x, y, h)); continue
        if g["t"] == "L":
            n = max(1, int(g["len"] / 6))
            for i in range(n): x += g["len"] / n * math.cos(math.radians(h)); y += g["len"] / n * math.sin(math.radians(h)); pts.append((x, y, h))
        else:
            sg = 1 if g["ang"] > 0 else -1; r = g["r"]
            cx = x + r * math.cos(math.radians(h + 90 * sg)); cy = y + r * math.sin(math.radians(h + 90 * sg))
            a0 = math.atan2(y - cy, x - cx); n = max(2, int(abs(g["ang"]) / 6))
            for i in range(1, n + 1):
                a = a0 + math.radians(g["ang"]) * i / n; x, y = cx + r * math.cos(a), cy + r * math.sin(a); pts.append((x, y, h + g["ang"] * i / n))
            h += g["ang"]
    P = np.array([(p[0], p[1]) for p in pts]); H = np.array([p[2] for p in pts])
    Ls = np.r_[0, np.cumsum(np.hypot(*np.diff(P, axis=0).T))]; T = Ls[-1] or 1
    if "wp" in st: wp = np.array(st["wp"]); w = np.interp(Ls / T, wp[:, 0], wp[:, 1]) * W
    else: w = np.full(len(P), st.get("wk", 1) * W)
    nx, ny = -np.sin(np.radians(H)), np.cos(np.radians(H))
    Lf = np.c_[P[:, 0] + nx * w / 2, P[:, 1] + ny * w / 2]; Rt = np.c_[P[:, 0] - nx * w / 2, P[:, 1] - ny * w / 2]
    for at, cap in ((0, st.get("cap0")), (-1, st.get("cap1"))):
        if cap != "auto" or not CUTS: continue
        hh = H[at] + (180 if at == 0 else 0); sy = math.sin(math.radians(hh))
        if abs(sy) < 0.2: continue
        cand = [L for L in CUTS if -(W * 1.2) < ((P[at][1] - L) if sy < 0 else (L - P[at][1])) <= 2]
        if not cand: continue
        L = min(cand, key=lambda L: abs(P[at][1] - L)); dx, dy = math.cos(math.radians(H[at])), math.sin(math.radians(H[at]))
        for E in (Lf, Rt):
            if abs(dy) > 1e-6: tt_ = (L - E[at][1]) / dy; E[at] = (E[at][0] + tt_ * dx, L)
    return [np.vstack([Lf, Rt[::-1]]).tolist()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("font"); ap.add_argument("out")
    ap.add_argument("--chars", default="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789")
    ap.add_argument("--name", default=""); ap.add_argument("--ghost", default="")
    ap.add_argument("--version", default="latin-1")
    a = ap.parse_args()
    tt = TTFont(a.font); upm = tt["head"].unitsPerEm
    from fontTools.pens.boundsPen import BoundsPen
    def ybox(ch):
        g = tt.getBestCmap().get(ord(ch)); b = BoundsPen(tt.getGlyphSet()); tt.getGlyphSet()[g].draw(b); return b.bounds
    cap = getattr(tt["OS/2"], "sCapHeight", 0) or ybox("H")[3]
    xh = getattr(tt["OS/2"], "sxHeight", 0) or ybox("x")[3]
    k = 700 / cap                                     # design units per font unit
    face = freetype.Face(a.font); face.set_char_size(int(upm * k * 2 * 64))   # 2 px = 1 design unit (S = 2)
    glyphs = {}; Ws = []; report = {}
    LINES = [round(tt["hhea"].descent * k), 0, round(xh * k), 700, round(tt["hhea"].ascent * k)]
    global CUTS; CUTS = LINES
    gs = tt.getGlyphSet(); cmap = tt.getBestCmap(); ghost = {}
    for ch in a.chars:
        if ord(ch) not in cmap: continue
        best = None
        for var in ({"local": True}, {"local": False}):     # two readings of the junction widths; keep the better fit
            VARIANT.clear(); VARIANT.update(var)
            st_, W_, adv_, raster_ = trace_glyph(face, ch, k, lines=LINES)
            if st_ is None: continue
            cov, spill = score(st_, W_, raster_)
            if best is None or cov - 1.5 * spill > best[0]: best = (cov - 1.5 * spill, st_, W_, adv_, cov, spill, var)
        if best is None: continue
        _, st, W, adv, cov, spill, var = best
        Ws.append(W); report[ch] = {"covered": cov, "outside": spill, "strokes": len(st), "variant": var}
        key = ch if ch.isalnum() else "@" + {".": "period", ",": "comma", "-": "hyphen", "!": "exclam", "?": "question", "'": "quote"}.get(ch, "u%04x" % ord(ch))
        glyphs[key] = {"type": "radical", "group": "upper" if ch.isupper() else "lower" if ch.islower() else "digit" if ch.isdigit() else "other",
                       "strokes": st, "status": "draft", "adv": round(adv, 1), "W": round(W, 1), "fit": report[ch]}
        sp = SVGPathPen(gs); gs[cmap[ord(ch)]].draw(TransformPen(sp, (k, 0, 0, k, 0, 0)))
        ghost[key] = {"d": sp.getCommands()}
    W = float(np.median(Ws)) if Ws else 60
    # each glyph's widths are relative to its own median weight; rescale them to the font's
    for kk, g in glyphs.items():
        r = g["W"] / W
        for st in g["strokes"]:
            if "wp" in st: st["wp"] = [[a, round(b * r, 3)] for a, b in st["wp"]]
            else: st["wk"] = round(st.get("wk", 1) * r, 3)
    # Twi letters missing from the reference: Ɔ ɔ mirror C c, Ɛ ɛ mirror 3 (scaled to the x-height for ɛ)
    def mirror(st, cx):
        m = dict(st); m["x"] = round(2 * cx - st["x"], 1); m["h"] = round((180 - st["h"]) % 360, 2)
        m["segs"] = [dict(g, ang=-g["ang"]) if "ang" in g else dict(g) for g in st["segs"]]; return m
    def scaled_st(st, k):
        m = dict(st); m["x"] = round(st["x"] * k, 1); m["y"] = round(st["y"] * k, 1)
        m["segs"] = [dict(g, len=round(g["len"] * k, 1)) if g["t"] == "L" else dict(g, r=round(g["r"] * k, 1)) if g["t"] == "A" else dict(g) for g in st["segs"]]; return m
    def make(src, key, k=1.0):
        if src not in glyphs or key in glyphs: return
        g = glyphs[src]; cx = g["adv"] / 2
        glyphs[key] = dict(g, strokes=[scaled_st(mirror(s_, cx), k) for s_ in g["strokes"]], status="draft", made=f"mirror of {src}" + (f" x {k:.2f}" if k != 1 else ""))
        if key in ghost or src not in ghost: pass
    make("C", "Ɔ"); make("c", "ɔ"); make("3", "Ɛ", 700 / max(1, ybox("3")[3] * k)); make("3", "ɛ", (xh * k) / max(1, ybox("3")[3] * k))
    out = {"_version": a.version, "name": a.name or tt["name"].getDebugName(1), "metrics": {"cap": 700, "x": round(xh * k), "asc": round(tt["hhea"].ascent * k), "desc": round(tt["hhea"].descent * k), "W": round(W, 1)}, "glyphs": glyphs}
    json.dump(out, open(a.out, "w"), ensure_ascii=False, separators=(",", ":"))
    if a.ghost: json.dump(ghost, open(a.ghost, "w"), separators=(",", ":"))
    json.dump(report, open(a.out.replace(".json", "-fit.json"), "w"), ensure_ascii=False, indent=0)
    cv = [r["covered"] for r in report.values()]; sp = [r["outside"] for r in report.values()]
    print("ink covered %.3f (worst %s %.2f), rebuild outside the ink %.3f" % (np.mean(cv), min(report, key=lambda c: report[c]["covered"]), min(cv), np.mean(sp)))
    print(len(glyphs), "glyphs, stroke weight", round(W, 1), "x-height", out["metrics"]["x"])


if __name__ == "__main__":
    main()
