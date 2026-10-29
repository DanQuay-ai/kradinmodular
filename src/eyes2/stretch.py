"""stretch every radical vertically (x-height / body taller): centrelines y -> y * f, strokes rebuilt around
them at the same weight (so horizontals do not get heavier), ends that were cut on 0 / 700 cut on 0 / 700 f"""
import json, os, sys, numpy as np
from shapely.geometry import LineString, box, Polygon, Point, mapping
import relax as RX
from shapely import affinity
import body as BODY
D = json.load(open(sys.argv[1])); f = float(sys.argv[3]); H = 700 * f; BODYH = H
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

def _tan(Q, end):
    nb = 1 if end == 0 else -2; t = Q[end] - Q[nb]; return t / (np.hypot(*t) or 1)

def _run_on(Q, end, e):
    t = _tan(Q, end); return np.vstack([Q, Q[-1] + t * e]) if end == -1 else np.vstack([Q[0] + t * e, Q])

def _ray_hit(Q, end, other, reach):
    t = _tan(Q, end); h = LineString([Q[end], Q[end] + t * reach]).intersection(LineString(other))
    if h.is_empty: return None
    return min(Point(Q[end]).distance(g) for g in (h.geoms if hasattr(h, "geoms") else [h]))

def _trim_at(Q, end, other, limit):
    """walk in from the end; the first crossing of the other stroke's centreline within `limit` -> cut there"""
    O = LineString(other); R = Q if end == -1 else Q[::-1]; acc = 0.0
    for k in range(len(R) - 1, 0, -1):
        seg = LineString([R[k - 1], R[k]])
        if seg.distance(O) < 0.5:                       # crossing (or passing through the other stroke's end point)
            from shapely.ops import nearest_points
            h = seg.intersection(O)
            if not h.is_empty and h.geom_type == "Point": q = np.array(h.coords[0])
            else: q = np.array(nearest_points(seg, O)[0].coords[0])
            out = np.vstack([R[:k], q]); s_ = acc + np.hypot(*(R[k] - q))
            if s_ > limit: return None, None
            return out if end == -1 else out[::-1], s_
        acc += seg.length
        if acc > limit: break
    return None, None

def plan(strokes, W=40.0, tol=30.0):
    """read on Thin, before the stretch. Per free end (not cut on a body line, not a joint between pieces):
    'run'  the end stops a hair short of another stroke (ink gap under tol): it runs on to that stroke's centreline
    'trim' the end pokes past a crossing stroke by less than 1.5 W (an overshoot): it stops on that stroke's centreline
    'cap'  after that, two ends meet in an L corner: each runs on by the other's half weight (square, full corner)"""
    from shapely.ops import unary_union
    Qs = [np.asarray(st["cl"], float) for st in strokes]; ops = {}
    # an end cut on a body line is one that crosses it; a stroke lying along the baseline has a free end there
    free = lambda i, end: len(Qs[i]) >= 2 and not strokes[i].get("joints", [False, False])[0 if end == 0 else 1] \
        and not (RX._cut_end(strokes[i], end) and abs(_tan(Qs[i], end)[1]) > 0.2)
    B = [LineString(Q).buffer(W / 2, cap_style=2) if len(Q) > 1 else None for Q in Qs]
    for i in range(len(Qs)):
        for end in (0, -1):
            if not free(i, end): continue
            Q = Qs[i]; others = [j for j in range(len(Qs)) if j != i and len(Qs[j]) > 1]
            # overshoot
            best = None
            for j in others:
                q, s_ = _trim_at(Q, end, Qs[j], 2.5 * W)
                if q is not None and len(q) >= 2:
                    at = q[end]; Lcorner = min(np.hypot(*(at - Qs[j][0])), np.hypot(*(at - Qs[j][-1]))) < 0.75 * W
                    if s_ > (2.5 if Lcorner else 1.5) * W: continue      # past the end of the other stroke: an L corner overshoot, up to 2.5 W
                if q is not None and s_ > W / 2 + 2 and len(q) >= 2:
                    c = abs(_tan(Q, end) @ _tan(q, end)) if len(q) > 1 else 1
                    if best is None or s_ < best[1]: best = (j, s_)
            if best: ops[(i, end)] = ("trim", best[0]); continue
            # near miss (free ends of pieces too: a hook curling back to its own stroke)
            near = B[i].intersection(Point(Q[end]).buffer(W * 0.6))
            d = min((near.distance(B[j]) for j in others), default=1e9)
            if 0 < d < tol:
                hits = [(j, _ray_hit(Q, end, Qs[j], tol + 2 * W)) for j in others]; hits = [h for h in hits if h[1] is not None]
                if hits: ops[(i, end)] = ("run", min(hits, key=lambda h: h[1])[0])
    Q2 = apply(Qs, ops, None)
    E = [(i, end, Q2[i][end], _tan(Q2[i], end)) for i in range(len(Q2)) for end in (0, -1) if free(i, end) and len(Q2[i]) >= 2]
    for a_ in E:
        for b_ in E:
            if a_[0] != b_[0] and np.hypot(*(a_[2] - b_[2])) < 0.75 * W and abs(a_[3] @ b_[3]) < 0.87:
                ops.setdefault((a_[0], a_[1]), ("cap", b_[0]))
                if ops[(a_[0], a_[1])][0] != "cap": ops[(a_[0], a_[1], "cap")] = ("cap", b_[0])
    return ops

FORCE = json.load(open(os.environ["EYES_FORCE"])) if os.environ.get("EYES_FORCE") else {}
def forced(k, strokes, W=40.0):
    """owner marks -> ops: 'cut' (end runs to the nearest body line, cut flat), 'run' (end runs on to the nearest stroke)"""
    ops = {}
    Qs = [np.asarray(st["cl"], float) for st in strokes]
    for f in FORCE.get(k, []):
        if f.get("op") == "pull":                          # the end gets shorter by d (Thin units, scaled with the weight)
            ops[(f["stroke"], f["end"], "pull")] = ("pull", f["d"], f.get("w")); continue
        if f.get("op") == "foot":                          # a foot: the end runs past the stroke it stops on
            ops[(f["stroke"], f["end"], "foot")] = ("foot", f["f"], None); continue
        if "stroke" in f:                                  # named end: run on to the stroke its tangent meets
            i, end = f["stroke"], f["end"]; Qe = Qs[i]
            hits = [(j, _ray_hit(Qe, end, Qs[j], 400)) for j in range(len(Qs)) if j != i and len(Qs[j]) > 1]
            hits = [h for h in hits if h[1] is not None]
            if hits: ops[(i, end)] = ("run", min(hits, key=lambda h: h[1])[0], f.get("w"))
            continue
        p = np.array([f["x"], 20 + (f["y"] - 20) * 660 / (700 * 1.3 - 40)])
        best = min(((np.hypot(*(Qs[i][end] - p)), i, end) for i in range(len(Qs)) if len(Qs[i]) > 1 for end in (0, -1)
                    if not strokes[i].get("joints", [False, False])[0 if end == 0 else 1]), default=None)
        if best is None: continue
        _, i, end = best
        if f["op"] == "cut": ops[(i, end)] = ("cut", -1)
        else:
            hits = [(j, _ray_hit(Qs[i], end, Qs[j], 300)) for j in range(len(Qs)) if j != i and len(Qs[j]) > 1]
            hits = [h for h in hits if h[1] is not None]
            if hits: ops[(i, end)] = ("run", min(hits, key=lambda h: h[1])[0])
            else:
                j = min((j for j in range(len(Qs)) if j != i and len(Qs[j]) > 1), key=lambda j: LineString(Qs[j]).distance(Point(Qs[i][end])))
                ops[(i, end)] = ("link", j)
    return ops

def st_piece(st): return bool(st.get("piece"))

def apply(Qs, ops, caps):
    """run / trim on the given centrelines (any weight); caps = (hw, hv) per stroke to also apply the caps"""
    Qs = [Q.copy() for Q in Qs]
    for key, v in ops.items():
        op, j = v[0], v[1]
        i, end = key[0], key[1]
        if op == "trim":
            q, _ = _trim_at(Qs[i], end, Qs[j], 3.0 * 60)
            if q is not None and len(q) >= 2: Qs[i] = q
        elif op == "link":                               # straight on to the nearest point of the other stroke
            O = LineString(Qs[j]); q = O.interpolate(O.project(Point(Qs[i][end]))); q = np.array(q.coords[0])
            Qs[i] = np.vstack([Qs[i], q]) if end == -1 else np.vstack([q, Qs[i]])
        elif op == "cut":
            t = _tan(Qs[i], end); y = Qs[i][end][1]
            if abs(t[1]) > 0.15:
                tgt = 0.0 if t[1] < 0 else BODYH
                Qs[i] = _run_on(Qs[i], end, (tgt - y) / t[1] + 40)
        elif op == "run":
            d = _ray_hit(Qs[i], end, Qs[j], 400)
            if d is not None: Qs[i] = _run_on(Qs[i], end, d)
    if caps is not None:
        for key, v in ops.items():
            op, j = v[0], v[1]
            if op == "pull":
                i, end = key[0], key[1]; Q = Qs[i]; d = j * (700 - caps[i][0] * 2) / 660
                R_ = Q if end == -1 else Q[::-1]; acc = 0.0; k_ = len(R_) - 1
                while k_ > 1 and acc + np.hypot(*(R_[k_] - R_[k_ - 1])) < d: acc += np.hypot(*(R_[k_] - R_[k_ - 1])); k_ -= 1
                seg = R_[k_] - R_[k_ - 1]; L_ = np.hypot(*seg) or 1; q = R_[k_] - seg / L_ * (d - acc)
                R_ = np.vstack([R_[:k_], q]); Qs[i] = R_ if end == -1 else R_[::-1]; continue
            if op == "foot":
                i, end = key[0], key[1]; hw, hv = caps[i]; t = _tan(Qs[i], end)
                Qs[i] = _run_on(Qs[i], end, hw + j * hw * 2); continue
            if op != "cap": continue
            i, end = key[0], key[1]; hw, hv = caps[i]; t = _tan(Qs[i], end)
            Qs[i] = _run_on(Qs[i], end, hw * abs(t[0]) + hv * abs(t[1]))
    return Qs

for k in D["keys"]:
    OPS = {} if os.environ.get("EYES_NOPLAN") else plan(split_closed(D["G"][k]["40"]))
    OPS.update(forced(k, split_closed(D["G"][k]["40"])))
    if OPS: print(k, {kk: v[0] for kk, v in OPS.items()})
    for W, strokes in D["G"][k].items():
        W = float(W); out = []; cn = BODY.contrast(W)
        S = split_closed(strokes); Qs, CAP = [], []
        for st in S:
            hw = W / 2 * st.get("wk", 1); hv = hw * cn      # vertical half thickness (elliptical nib)
            Q = np.asarray(st["cl"], float).copy()
            if len(Q) >= 2:
                Q[:, 1] = cn * W / 2 + (Q[:, 1] - W / 2) * (H - cn * W) / (700 - W)   # strokes on a body line stay on it
                Q[:, 1] = np.clip(Q[:, 1], hv, H - hv)     # Kɔradin clips the glyph to its body: a bowl dipping past a body line runs flat along it
            Qs.append(Q); CAP.append((hw, hv))
        Qs = apply(Qs, {kk: v[:2] for kk, v in OPS.items() if len(v) < 3 or v[2] in (None, str(int(W)))}, CAP)
        for si, st in enumerate(S):
            Q = Qs[si]
            if len(Q) < 2: continue
            fc = [OPS.get((si, 0), ("",))[0] == "cut", OPS.get((si, -1), ("",))[0] == "cut"]
            if not st.get("piece"): cuts = [bool(RX._cut_end(st, 0)), bool(RX._cut_end(st, -1))]
            else:                                     # a piece's free end can be cut on a body line too (a stem on top of a loop)
                c0 = np.asarray(st["cl"], float)[[0, -1], 1]; jn = st.get("joints", [False, False])
                cuts = [bool(not jn[n] and (c0[n] >= 700 - W / 2 - 1 or c0[n] <= W / 2 + 1) and RX._cut_end(st, 0 if n == 0 else -1)) for n in (0, 1)]
            cuts = [cuts[0] or fc[0], cuts[1] or fc[1]]
            hw, hv = CAP[si]; keepcl = Q.copy()
            for end, nb, c in ((0, 1, cuts[0]), (-1, -2, cuts[1])):
                if not c: continue
                t = Q[end] - Q[nb]; t = t / (np.hypot(*t) or 1)
                if abs(t[1]) > 0.2: Q = np.vstack([Q, Q[-1] + t * W]) if end == -1 else np.vstack([Q[0] + t * W, Q])
            Qe = Q * [1, 1 / cn]                                                    # the nib is an ellipse: drawn round in a space
            P = LineString(Qe).buffer(hw, cap_style=2, join_style=1, quad_segs=8)  # squashed by the contrast, then scaled back
            for j, at in zip(st.get("joints", [False, False]), (Qe[0], Qe[-1])):   # a joint between two pieces: round, so the
                if j: P = P.union(Point(at).buffer(hw, quad_segs=16))              # pieces meet without a notch or a corner
            P = affinity.scale(P, 1, cn, origin=(0, 0))
            P = P.intersection(box(-3000, 0, 4000, H))
            P = max((P.geoms if hasattr(P, "geoms") else [P]), key=lambda g: g.area)
            out.append(dict(st, cl=keepcl.round(2).tolist(), poly=np.round(np.array(P.exterior.coords), 2).tolist(), cuts=cuts))
        D["G"][k][str(int(W))] = out
D["H"] = H
json.dump(D, open(sys.argv[2], "w")); print("body", H)
