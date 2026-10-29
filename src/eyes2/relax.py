"""Heavy master skeleton: the Thin skeleton (scaled into the body) relaxed so that parts that are separate in
Thin get room for two heavy strokes plus the gap. Strokes keep their shape (every edge vector along a stroke,
and every junction offset, is held), the glyph may grow wider, the body lines (0 / 700) hold."""
import math, numpy as np
from body import H as BH
from scipy.spatial import cKDTree
from shapely.geometry import LineString, Polygon, box
from shapely.ops import unary_union
import os
FLARE = float(os.environ.get("EYES_FLARE", 1.0))
SMIN = float(os.environ.get("EYES_SMIN", 0.8))      # a stroke may shrink (about its centre) to fit inside a counter
SHRINK_ALL = False
RETRACT = float(os.environ.get("EYES_RETRACT", 2.0))   # a free end may shorten by up to this many weights to clear a part

def relax(S0, S, sid, strokes, far, W, Wthin, gap, iters=None):
    """every stroke moves as a whole (translate) and may stretch (scale about its centre); junctions hold;
    separate parts are pushed to clearance; least squares. What the stretch cannot solve, the cuts do."""
    from scipy.optimize import least_squares
    P0 = S.copy(); n = len(P0)
    # pieces of one drawn stroke (rings, loops, spirals are stored in pieces) move as one
    gof = np.array([st.get("group", i) for i, st in enumerate(strokes)]); _, gof = np.unique(gof, return_inverse=True)
    sid_s = sid; sid = gof[sid_s]; ns = sid.max() + 1
    hw_s = []
    for st in strokes:
        cl = np.asarray(st["cl"], float); L = np.hypot(*np.diff(cl, axis=0).T).sum() if len(cl) > 1 else 1
        try: A = Polygon(st["poly"]).buffer(0).area
        except Exception: A = W * L
        hw_s.append(min(W / 2 * 1.05, max(W * 0.15, A / (2 * max(L, 1)))))
    hw_s = [W / 2 * st.get("wk", 1) for st in strokes]       # one weight for every stroke (monoline)
    hw = np.array([hw_s[i] for i in sid_s])
    C = np.array([P0[sid == i].mean(axis=0) for i in range(ns)])
    pinB = P0[:, 1] <= W / 2 + 6; pinT = P0[:, 1] >= BH - W / 2 - 6
    hasB = np.array([pinB[sid == i].any() for i in range(ns)]); hasT = np.array([pinT[sid == i].any() for i in range(ns)])
    for i in range(ns):                      # strokes standing on a body line scale from that line, and stay on it
        if hasB[i] and not hasT[i]: C[i, 1] = P0[sid == i][:, 1].min()
        elif hasT[i] and not hasB[i]: C[i, 1] = P0[sid == i][:, 1].max()
    T = far.touch.tocoo(); J = np.array([(i, j) for i, j in zip(T.row, T.col) if sid[i] != sid[j]], int).reshape(-1, 2)
    Jp = set(int(i) for i, j in zip(T.row, T.col) if sid_s[i] != sid_s[j]) | set(int(j) for i, j in zip(T.row, T.col) if sid_s[i] != sid_s[j])
    Jself = set(int(i) for i, j in zip(T.row, T.col) if sid[i] == sid[j] and abs(i - j) > 3) | set(int(j) for i, j in zip(T.row, T.col) if sid[i] == sid[j] and abs(i - j) > 3)
    RJ = P0[J[:, 1]] - P0[J[:, 0]] if len(J) else np.zeros((0, 2))
    need_all = hw[:, None] + hw[None, :] + gap
    pr = cKDTree(P0).query_pairs(float(need_all.max()) * 1.6, output_type="ndarray")
    if len(pr): pr = pr[far.M[pr[:, 0], pr[:, 1]]]
    need = need_all[pr[:, 0], pr[:, 1]] if len(pr) else np.zeros(0)
    pin = (P0[:, 1] <= W / 2 + 6) | (P0[:, 1] >= BH - W / 2 - 6)
    # closed counters of Thin: the samples around each must leave room for two half weights + an eye
    from shapely.geometry import Point
    tink = unary_union([Polygon(st0).buffer(0) for st0 in [st["poly"] for st in far.thin]]) if hasattr(far, "thin") else None
    rings = []
    if tink is not None:
        for pg in ([tink] if tink.geom_type == "Polygon" else list(tink.geoms)):
            for r in pg.interiors:
                H = Polygon(r).buffer(0)
                if H.area < 300: continue
                idx = np.array([i for i in range(n) if H.exterior.distance(Point(*S0[i])) < Wthin / 2 + 4])
                if len(idx) >= 6: rings.append(idx)
    Rneed = W / 2 + max(15, 0.16 * W)
    CP = np.unique(np.sort(sid[J], axis=1), axis=0) if len(J) else np.zeros((0, 2), int)   # strokes joined in Thin move together
    gc = P0.mean(axis=0)
    def place(x):
        g = x[-1]; X = x[:-1].reshape(ns, 4); tx, ty, sx, sy = X[sid, 0], X[sid, 1], X[sid, 2], X[sid, 3]
        Cx = gc[0] + (C[sid, 0] - gc[0]) * g
        Q = np.empty_like(P0); Q[:, 0] = Cx + (P0[:, 0] - C[sid, 0]) * sx * g + tx; Q[:, 1] = C[sid, 1] + (P0[:, 1] - C[sid, 1]) * sy + ty
        return Q
    def res(x):
        Q = place(x); X = x[:-1].reshape(ns, 4); r = []
        if len(pr):
            d = np.hypot(*(Q[pr[:, 1]] - Q[pr[:, 0]]).T); r.append(4.0 * np.maximum(0, need - d) / W)
        if len(J): r.append(25.0 * ((Q[J[:, 1]] - Q[J[:, 0]]) - RJ * np.array([x[-1], 1])).ravel() / W)   # junctions hold: no overshoot
        for idx in rings:
            c = Q[idx].mean(axis=0); r.append(4.0 * np.maximum(0, Rneed - np.hypot(*(Q[idx] - c).T)) / W)
        r.append(10.0 * (Q[pin, 1] - P0[pin, 1]) / W)
        r.append(10.0 * (np.maximum(0, 0.45 * W - Q[:, 1]) + np.maximum(0, Q[:, 1] - (BH - 0.45 * W))) / W)   # stay in the body
        r.append(np.r_[2.5 * X[:, 0] / W, 3.0 * X[:, 1] / W, (X[:, 2] - 1) * 4, (X[:, 3] - 1) * 4, (X[:, 2] - X[:, 3]) * 4, [(x[-1] - 1) * 1.0]])
        if len(CP): r.append(1.5 * (X[CP[:, 0], 0] - X[CP[:, 1], 0]) / W)
        return np.concatenate(r)
    x0 = np.r_[np.tile([0, 0, 1, 1], ns).astype(float), 1.0]
    lo = np.r_[np.tile([-45, -40, 0.95, 0.9], ns), 0.98]
    bb = np.array([[P0[sid == i][:, 0].min(), P0[sid == i][:, 1].min(), P0[sid == i][:, 0].max(), P0[sid == i][:, 1].max()] for i in range(ns)])
    for i in range(ns):                       # a stroke nested inside another (a curl inside a bowl) may shrink to fit
        if SHRINK_ALL or any(j != i and bb[j, 0] < bb[i, 0] and bb[j, 1] < bb[i, 1] and bb[j, 2] > bb[i, 2] and bb[j, 3] > bb[i, 3] for j in range(ns)):
            lo[4 * i + 2] = lo[4 * i + 3] = SMIN
    hi = np.r_[np.tile([45, 40, 1.12, 1.2], ns), 1.45]   # strokes barely drift; the whole glyph may widen
    e = 1e-6
    for i in range(ns):
        if hasB[i] or hasT[i]: lo[4 * i + 1], hi[4 * i + 1] = -e, e            # no vertical shift
        if hasB[i] and hasT[i]: lo[4 * i + 3], hi[4 * i + 3] = 1 - e, 1 + e     # full height: no vertical scale
    x0 = np.clip(x0, lo, hi)
    sol = least_squares(res, x0, bounds=(lo, hi), x_scale=np.r_[np.tile([W, W, 1, 1], ns), 1], max_nfev=300)
    P = place(sol.x)
    # retract free ends that still crowd a separate part (shorter strokes instead of bites)
    gid = gof; CPset = {(int(a), int(b)): True for a, b in CP}
    alive = np.ones(n, bool); tree = cKDTree(P); Jset = set(J.ravel().tolist()) | Jself | Jp
    for i in range(len(strokes)):
        idx = np.where(sid_s == i)[0]
        if len(idx) < 4 or np.hypot(*(P0[idx[0]] - P0[idx[-1]])) < 2 * hw[idx[0]]: continue   # closed strokes (rings) have no ends
        L = np.r_[0, np.cumsum(np.hypot(*np.diff(P[idx], axis=0).T))]
        for end in (0, 1):
            order = idx if end == 0 else idx[::-1]; Lo = L if end == 0 else L[-1] - L[::-1]
            if _cut_end(strokes[i], 0 if end == 0 else -1) or strokes[i].get("joints", [False, False])[end]: continue
            if any(j in Jset for j, l in zip(order, Lo) if l < 0.6 * W): continue     # a junction end: keep
            k = 0
            while k < len(order) - 1 and Lo[k] < RETRACT * W and (L[-1] - Lo[k]) > 1.4 * W:
                e = order[k]; nb = tree.query_ball_point(P[e], hw[e] + hw.max() + gap)
                if not any(alive[j] and far.M[e, j] and np.hypot(*(P[j] - P[e])) < hw[e] + hw[j] + gap for j in nb): break
                alive[e] = False; k += 1
    # rebuild the heavy strokes around the relaxed centrelines
    lines, polys, flares = [], [], []
    for i in range(len(strokes)):
        Q = P[(sid_s == i) & alive]
        if len(Q) < 2: polys.append(Polygon()); continue
        Q = Q.copy()
        for end, nb in ((0, 1), (-1, -2)):            # ends on the body lines: run past, cut flat by the clip
            t = Q[end] - Q[nb]; t = t / (np.hypot(*t) or 1)
            if abs(t[1]) > 0.2 and (Q[end][1] < W * 0.8 or Q[end][1] > BH - W * 0.8) and _cut_end(strokes[i], end):
                Q = np.vstack([Q, Q[-1] + t * W]) if end == -1 else np.vstack([Q[0] + t * W, Q])
        lines.append(Q.tolist())
        pg = LineString(Q).buffer(hw_s[i], cap_style=2, join_style=1, quad_segs=8)
        idx = np.where((sid_s == i) & alive)[0]
        for end, nb in ((0, 1), (-1, -2)):            # free terminals flare: the heavy end keeps its weight to the tip
            if FLARE <= 1 or _cut_end(strokes[i], end) or strokes[i].get("joints", [False, False])[0 if end == 0 else 1]: continue
            if len(idx) < 4 or np.hypot(*(P0[idx[0]] - P0[idx[-1]])) < 2 * hw_s[i]: continue
            Lc = np.r_[0, np.cumsum(np.hypot(*np.diff(Q, axis=0).T))]; Lo = Lc if end == 0 else Lc[-1] - Lc
            near = idx[Lo[:len(idx)] < 0.6 * W] if len(Lo) >= len(idx) else []
            if any(int(j) in Jset for j in near): continue
            if Lc[-1] < 2.2 * W: continue
            t = Q[end] - Q[nb]; t = t / (np.hypot(*t) or 1); nrm = np.array([-t[1], t[0]])
            base = Q[end] - t * 0.75 * W
            tip = Q[Lo <= 0.75 * W]                       # the end runs straight for the flare length only
            if len(tip) < 2 or np.abs((tip - Q[end]) @ nrm).max() > 3: continue
            a, b = hw_s[i], hw_s[i] * FLARE
            fl = Polygon([base + nrm * a, Q[end] + nrm * b, Q[end] - nrm * b, base - nrm * a])
            seg = Q[Lo <= 2.2 * W] if end == 0 else Q[Lo <= 2.2 * W]
            flares.append((i, fl, LineString(seg).buffer(hw_s[i] * 1.6) if len(seg) > 1 else Polygon()))
        from shapely.geometry import Point as _Pt
        for j, at in zip(strokes[i].get("joints", [False, False]), (Q[0], Q[-1])):
            if j: pg = pg.union(_Pt(at).buffer(hw_s[i], quad_segs=16))
        polys.append(pg)
    # a flare is kept only where it leaves every separate part its full clearance
    for i, fl, local in flares:
        others = unary_union([p for j, p in enumerate(polys) if j != i] + [polys[i].difference(local)])
        extra = fl.difference(polys[i])
        if extra.is_empty: continue
        if others.is_empty or extra.distance(others) >= gap: polys[i] = polys[i].union(fl)
    raw = unary_union(polys).intersection(box(-2000, 0, 3000, BH))
    return P, raw, lines, alive

def _cut_end(st, end):
    """the original stroke was cut flat on a body line at this end (its polygon reaches 0 or 700 there)"""
    if "cuts" in st: return st["cuts"][0 if end == 0 else 1]
    cl = np.asarray(st["cl"]); poly = np.asarray(st["poly"]); p = cl[0 if end == 0 else -1]
    near = poly[np.hypot(*(poly - p).T) < 120]
    return len(near) and (np.abs(near[:, 1]).min() < 1.5 or np.abs(near[:, 1] - 700).min() < 1.5)
