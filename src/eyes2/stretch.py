"""stretch every radical vertically (x-height / body taller): centrelines y -> y * f, strokes rebuilt around
them at the same weight (so horizontals do not get heavier), ends that were cut on 0 / 700 cut on 0 / 700 f"""
import json, sys, numpy as np
from shapely.geometry import LineString, box, Polygon, Point, mapping
import relax as RX
D = json.load(open(sys.argv[1])); f = float(sys.argv[3]); H = 700 * f
def split_closed(strokes):
    """a stroke that turns more than 200 degrees (a ring, a loop, a spiral) is stored as consecutive pieces of at
    most 200 degrees each: one outline per piece, no piece overlaps itself, so loops keep their counters"""
    out = []
    for gid, st in enumerate(strokes):
        st = dict(st, group=gid)
        Q = np.asarray(st["cl"], float)
        if len(Q) < 4: out.append(st); continue
        h = np.unwrap(np.arctan2(*np.diff(Q, axis=0).T[::-1])); cuts = [0]; acc = 0.0
        for i in range(1, len(h)):
            acc += abs(h[i] - h[i - 1])
            if acc > np.radians(200): cuts.append(i); acc = 0.0
        cuts.append(len(Q) - 1)
        if len(cuts) == 2: out.append(st); continue
        for n, (a, b) in enumerate(zip(cuts, cuts[1:])):
            out.append(dict(st, cl=Q[a:b + 1].tolist(), piece=True, joints=[n > 0, n < len(cuts) - 2], group=gid))
    return out

for k in D["keys"]:
    for W, strokes in D["G"][k].items():
        W = float(W); out = []
        for st in split_closed(strokes):
            cuts = [bool(RX._cut_end(st, 0)), bool(RX._cut_end(st, -1))] if not st.get("piece") else [False, False]
            hw = W / 2 * st.get("wk", 1)
            Q = np.asarray(st["cl"], float).copy(); Q[:, 1] *= f
            if len(Q) < 2: continue
            # Kɔradin clips the glyph to its body: a bowl that dips past a body line runs flat along it
            Q[:, 1] = np.clip(Q[:, 1], hw, H - hw)
            keepcl = Q.copy()
            for end, nb, c in ((0, 1, cuts[0]), (-1, -2, cuts[1])):
                if not c: continue
                t = Q[end] - Q[nb]; t = t / (np.hypot(*t) or 1)
                if abs(t[1]) > 0.2: Q = np.vstack([Q, Q[-1] + t * W]) if end == -1 else np.vstack([Q[0] + t * W, Q])
            P = LineString(Q).buffer(hw, cap_style=2, join_style=1, quad_segs=8)
            for j, at in zip(st.get("joints", [False, False]), (Q[0], Q[-1])):     # a joint between two pieces: round, so the
                if j: P = P.union(Point(at).buffer(hw, quad_segs=16))              # pieces meet without a notch or a corner
            P = P.intersection(box(-3000, 0, 4000, H))
            P = max((P.geoms if hasattr(P, "geoms") else [P]), key=lambda g: g.area)
            cl = keepcl
            out.append(dict(st, cl=cl.round(2).tolist(), poly=np.round(np.array(P.exterior.coords), 2).tolist(), cuts=cuts))
        D["G"][k][str(int(W))] = out
D["H"] = H
json.dump(D, open(sys.argv[2], "w")); print("body", H)
