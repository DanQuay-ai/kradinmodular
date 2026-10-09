"""Kɔradin stroke model in Python: trace, sample, clearance check (mirrors site2/stroke.js)."""
import math
import numpy as np
R = math.pi / 180
W = 98.0
GAP = 1.4  # centreline distance between separate strokes >= GAP * W  (white >= 0.4 W)


def S(x, y, h, segs, **kw):
    out = []
    for tok in segs.split():
        t, v = tok[0], [float(a) for a in tok[1:].split(",")]
        if t == "L": out.append({"t": "L", "len": v[0]})
        elif t == "C": out.append({"t": "C", "ang": v[0]})
        elif t == "A": out.append({"t": "A", "r": v[0], "ang": v[1]})
        elif t == "P":   # spiral: start radius, half turns, direction (+1 anticlockwise, -1 clockwise)
            r, n, d = v; p = W * GAP
            while n > 1e-6 and r > 59:
                k = min(1, n); out.append({"t": "A", "r": round(r, 1), "ang": 180 * k * d}); r -= p / 2; n -= 1
    st = {"x": x, "y": y, "h": h, "segs": out, "s": 0, "e": 1, "cap0": "auto", "cap1": "auto"}
    st.update(kw)
    return st


def walk(st, step=6.0):
    """dense samples [(x, y, s, kind)] along the centreline; kind 'c' marks a corner vertex"""
    x, y, h = st["x"], st["y"], st["h"]; s = 0.0
    pts = [(x, y, 0.0, "e")]
    for g in st["segs"]:
        if g["t"] == "L":
            n = max(1, int(abs(g["len"]) / step))
            for i in range(1, n + 1):
                t = g["len"] * i / n
                pts.append((x + t * math.cos(h * R), y + t * math.sin(h * R), s + abs(t), ""))
            x += g["len"] * math.cos(h * R); y += g["len"] * math.sin(h * R); s += abs(g["len"])
        elif g["t"] == "C":
            h += g["ang"]; pts[-1] = (pts[-1][0], pts[-1][1], pts[-1][2], "c")
        else:
            sg = 1 if g["ang"] > 0 else -1; r = g["r"]
            cx = x + r * math.cos((h + 90 * sg) * R); cy = y + r * math.sin((h + 90 * sg) * R)
            a0 = math.atan2(y - cy, x - cx); L = r * abs(g["ang"]) * R
            n = max(2, int(L / step))
            for i in range(1, n + 1):
                a = a0 + g["ang"] * R * i / n
                pts.append((cx + r * math.cos(a), cy + r * math.sin(a), s + L * i / n, ""))
            x, y = cx + r * math.cos(a0 + g["ang"] * R), cy + r * math.sin(a0 + g["ang"] * R)
            h += g["ang"]; s += L
    pts[-1] = (pts[-1][0], pts[-1][1], pts[-1][2], "e")
    return pts


def end(st):
    p = walk(st)[-1]
    x, y, h = st["x"], st["y"], st["h"]
    for g in st["segs"]:
        if g["t"] != "L": h += g["ang"]
    return p[0], p[1], h


def rev(st):
    x, y, h = end(st)
    segs = [dict(g, ang=-g["ang"]) if "ang" in g else dict(g) for g in reversed(st["segs"])]
    return dict(st, x=round(x, 2), y=round(y, 2), h=(h + 180) % 360, segs=segs)


def mirror(st, cx):
    return dict(st, x=2 * cx - st["x"], h=(180 - st["h"]) % 360,
                segs=[dict(g, ang=-g["ang"]) if "ang" in g else dict(g) for g in st["segs"]])


def move(st, dx=0, dy=0):
    return dict(st, x=st["x"] + dx, y=st["y"] + dy)


def scale(st, k, ox=0, oy=0):
    return dict(st, x=ox + (st["x"] - ox) * k, y=oy + (st["y"] - oy) * k,
                segs=[dict(g, len=g["len"] * k) if g["t"] == "L" else dict(g, r=g["r"] * k) if g["t"] == "A" else dict(g) for g in st["segs"]])


def _seg_x(p1, p2, q1, q2):
    d = (p2[0] - p1[0]) * (q2[1] - q1[1]) - (p2[1] - p1[1]) * (q2[0] - q1[0])
    if abs(d) < 1e-9: return None
    t = ((q1[0] - p1[0]) * (q2[1] - q1[1]) - (q1[1] - p1[1]) * (q2[0] - q1[0])) / d
    u = ((q1[0] - p1[0]) * (p2[1] - p1[1]) - (q1[1] - p1[1]) * (p2[0] - p1[0])) / d
    if -1e-6 <= t <= 1 + 1e-6 and -1e-6 <= u <= 1 + 1e-6:
        return (p1[0] + t * (p2[0] - p1[0]), p1[1] + t * (p2[1] - p1[1]))
    return None


def check(strokes, w=W, need=None):
    """centreline clearance; returns list of (x, y, shortfall). Junctions, crossings and corners are allowed contacts."""
    need = need or GAP * w
    P = [np.array([(p[0], p[1]) for p in walk(st)]) for st in strokes]
    Sx = [np.array([p[2] for p in walk(st)]) for st in strokes]
    corners = [np.array([(p[0], p[1]) for p in walk(st) if p[3] == "c"]).reshape(-1, 2) for st in strokes]
    # joints: endpoints touching another stroke + crossings + self crossings
    J = []
    for a, A in enumerate(P):
        for e in (A[0], A[-1]):
            for b, B in enumerate(P):
                if a == b: continue
                if np.min(np.linalg.norm(B - e, axis=1)) < 15: J.append(e)
        for b in range(a, len(P)):
            B = P[b]
            for i in range(len(A) - 1):
                for j in range(len(B) - 1):
                    if a == b and abs(i - j) < 3: continue
                    q = _seg_x(A[i], A[i + 1], B[j], B[j + 1])
                    if q is not None: J.append(np.array(q))
    J = np.array(J).reshape(-1, 2)
    bad = []
    for a in range(len(P)):
        for b in range(a, len(P)):
            A, B = P[a], P[b]
            D = np.linalg.norm(A[:, None] - B[None], axis=2)
            I, K = np.nonzero(D < need - 3)
            for i, k in zip(I, K):
                if a == b:
                    if k <= i: continue
                    ds = abs(Sx[a][k] - Sx[a][i])
                    if ds < D[i, k] * 1.3 + 4: continue          # same run of the stroke
                    if len(corners[a]) and min(np.min(np.linalg.norm(corners[a] - A[i], axis=1)), np.min(np.linalg.norm(corners[a] - B[k], axis=1))) < w * 1.2: continue
                mid = (A[i] + B[k]) / 2
                if len(J) and np.min(np.linalg.norm(J - mid, axis=1)) < need * 1.6: continue
                bad.append((float(mid[0]), float(mid[1]), float(need - D[i, k])))
    # thin out
    out = []
    for p in sorted(bad, key=lambda q: -q[2]):
        if all(math.hypot(p[0] - q[0], p[1] - q[1]) > 50 for q in out): out.append(p)
    return out


def bbox(strokes):
    xs = [p[0] for st in strokes for p in walk(st)]; ys = [p[1] for st in strokes for p in walk(st)]
    return min(xs), min(ys), max(xs), max(ys)


def rnd(st):
    st = dict(st); st["x"] = round(st["x"], 1); st["y"] = round(st["y"], 1); st["h"] = round(st["h"] % 360, 2)
    st["segs"] = [{k: (round(v, 1) if isinstance(v, float) else v) for k, v in g.items()} for g in st["segs"]]
    return st
