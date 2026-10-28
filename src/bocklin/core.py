"""Böcklin, drawn by hand in the Kɔradin stroke model. A turtle DSL, the passover/passunder loop, outlines
(mirror of stroke.js incl. s/e trims), overlay renders against the reference, export to latin/bocklin.json."""
import math, json, numpy as np
from shapely.geometry import Polygon, MultiPolygon
from shapely.ops import unary_union
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import DecomposingRecordingPen
import os
REF = os.environ.get("BKREF", "/mnt/user-data/attachments/095e6311-fc75-5a2c-9c6a-0bc6be907c52/fd01f856-ArnoldBoecklinStd.ttf")
W = float(os.environ.get("BKW", 125.0)); XH = 516; CAP = 700; CUTS = [float(v) for v in os.environ.get("BKCUTS", "0,516,700,-200").split(",")]

class S:
    def __init__(s, x, y, h, w=1.0):
        s.d = {"x": x, "y": y, "h": h, "segs": [], "s": 0, "e": 1, "cap0": "butt", "cap1": "butt"}; s.wk = w
    def L(s, n): s.d["segs"].append({"t": "L", "len": round(n, 1)}); return s
    def A(s, r, a): s.d["segs"].append({"t": "A", "r": round(r, 1), "ang": round(a, 2)}); return s
    def C(s, a): s.d["segs"].append({"t": "C", "ang": round(a, 2)}); return s
    def w(s, *prof): s.d["wp"] = [[float(t), float(v)] for t, v in prof]; return s
    def cut(s, a=True, b=True): s.d["cap0"] = "auto" if a else "butt"; s.d["cap1"] = "auto" if b else "butt"; return s
    def over(s, at, halo=0.16): s.d["loop"] = {"at": at, "mode": "over", "halo": halo}; return s
    def under(s, at, halo=0.16): s.d["loop"] = {"at": at, "mode": "under", "halo": halo}; return s
    def part(s, p): s.d["part"] = p; return s
    def out(s):
        d = dict(s.d)
        if "wp" not in d and s.wk != 1: d["wk"] = s.wk
        return d

def centre(st):
    x, y, h = st["x"], st["y"], st["h"]; pts = [(x, y, h)]
    for g in st["segs"]:
        if g["t"] == "C": h += g["ang"]; pts.append((x, y, h)); continue
        if g["t"] == "L":
            n = max(1, int(abs(g["len"]) / 5))
            for i in range(n): x += g["len"] / n * math.cos(math.radians(h)); y += g["len"] / n * math.sin(math.radians(h)); pts.append((x, y, h))
        else:
            sg = 1 if g["ang"] > 0 else -1; r = g["r"]
            cx = x + r * math.cos(math.radians(h + 90 * sg)); cy = y + r * math.sin(math.radians(h + 90 * sg))
            a0 = math.atan2(y - cy, x - cx); n = max(2, int(abs(g["ang"]) / 4))
            for i in range(1, n + 1):
                a = a0 + math.radians(g["ang"]) * i / n; x, y = cx + r * math.cos(a), cy + r * math.sin(a); pts.append((x, y, h + g["ang"] * i / n))
            h += g["ang"]
    return pts

def length(st): P = np.array([(p[0], p[1]) for p in centre(st)]); return float(np.hypot(*np.diff(P, axis=0).T).sum()) if len(P) > 1 else 0.0

def outline(st):
    pts = centre(st); P = np.array([(p[0], p[1]) for p in pts]); H = np.array([p[2] for p in pts])
    Ls = np.r_[0, np.cumsum(np.hypot(*np.diff(P, axis=0).T))]; T = Ls[-1] or 1; u = Ls / T
    if st.get("wp"): wp = np.array(st["wp"]); w = np.interp(u, wp[:, 0], wp[:, 1]) * W
    else: w = np.full(len(P), st.get("wk", 1) * W)
    s0, e0 = st.get("s", 0), st.get("e", 1)
    keep = (u >= s0 - 1e-9) & (u <= e0 + 1e-9)
    P, H, w = P[keep], H[keep], w[keep]
    if len(P) < 2: return None
    nx, ny = -np.sin(np.radians(H)), np.cos(np.radians(H))
    Lf = np.c_[P[:, 0] + nx * w / 2, P[:, 1] + ny * w / 2]; Rt = np.c_[P[:, 0] - nx * w / 2, P[:, 1] - ny * w / 2]
    for at, cap in ((0, st.get("cap0")), (-1, st.get("cap1"))):
        if cap != "auto": continue
        hh = H[at] + (180 if at == 0 else 0); sy = math.sin(math.radians(hh))
        if abs(sy) < 0.2: continue
        cand = [L for L in CUTS if -(W * 1.2) < ((P[at][1] - L) if sy < 0 else (L - P[at][1])) <= 2]
        if not cand: continue
        L = min(cand, key=lambda L: abs(P[at][1] - L)); dx, dy = math.cos(math.radians(H[at])), math.sin(math.radians(H[at]))
        for E in (Lf, Rt):
            if abs(dy) > 1e-6: t_ = (L - E[at][1]) / dy; E[at] = (E[at][0] + t_ * dx, L)
    p = Polygon(np.vstack([Lf, Rt[::-1]]))
    return p if p.is_valid else p.buffer(0)

def sub(st, a, b):
    T = length(st) or 1; pre = dict(st, segs=st["segs"][:a]); t0 = length(pre) / T; t1 = length(dict(st, segs=st["segs"][:b])) / T
    c = centre(pre)[-1]; o = dict(st, x=c[0], y=c[1], h=c[2], segs=st["segs"][a:b], s=0, e=1); o.pop("loop", None)
    if st.get("wp"): wp = np.array(st["wp"]); o["wp"] = [[u, float(np.interp(t0 + u * (t1 - t0), wp[:, 0], wp[:, 1]))] for u in np.linspace(0, 1, 11)]
    if a > 0: o["cap0"] = "butt"
    if b < len(st["segs"]): o["cap1"] = "butt"
    return o

def halo(s, hw, from_end):
    L = length(s) or 1; c = min(0.45, 1.5 * W / L)
    wp = s.get("wp") or [[0, s.get("wk", 1)], [1, s.get("wk", 1)]]
    h = dict(s, wp=[[t, v + 2 * hw] for t, v in wp], s=0 if from_end else c, e=1 - c if from_end else 1, cap0="butt", cap1="butt"); h.pop("wk", None)
    return h

def shape_of(st):
    lp = st.get("loop")
    if lp and 0 < lp["at"] < len(st["segs"]):
        A, B = sub(st, 0, lp["at"]), sub(st, lp["at"], len(st["segs"]))
        pa, pb = outline(A), outline(B)
        if lp["mode"] == "under": return pa.union(pb.difference(outline(halo(A, lp.get("halo", .16), True))))
        return pa.difference(outline(halo(B, lp.get("halo", .16), False))).union(pb)
    return outline(st)

def glyph_shape(strokes):
    acc = None
    for st in strokes:
        p = shape_of(st)
        if p is None or p.is_empty: continue
        if st.get("over") and acc is not None:      # crosses earlier strokes: its white outline (ends trimmed) is cut out of them
            L = length(st) or 1; c = min(0.3, 1.2 * W / L); wp = st.get("wp") or [[0, st.get("wk", 1)], [1, st.get("wk", 1)]]
            h = dict(st, wp=[[t, v + 2 * st.get("halo", .16)] for t, v in wp], s=c, e=1 - c, cap0="butt", cap1="butt"); h.pop("wk", None); h.pop("loop", None)
            hp = outline(h)
            if hp is not None: acc = acc.difference(hp)
        acc = p if acc is None else acc.union(p)
    return acc

_f = TTFont(REF); _gs = _f.getGlyphSet(); _cm = _f.getBestCmap()
_cap = getattr(_f["OS/2"], "sCapHeight", 0)
if not _cap:
    from fontTools.pens.boundsPen import BoundsPen
    _b = BoundsPen(_gs); _gs[_cm[ord("H")]].draw(_b); _cap = _b.bounds[3]
SC = 700.0 / _cap
def ref_shape(ch):
    pen = DecomposingRecordingPen(_gs); _gs[_cm[ord(ch)]].draw(pen)
    from fontTools.pens.basePen import BasePen
    rings = []; cur = []
    for op, args in pen.value:
        if op == "moveTo": cur = [args[0]]
        elif op == "lineTo": cur.append(args[0])
        elif op in ("qCurveTo", "curveTo"):
            p0 = cur[-1]; pts = [p0] + list(args)
            if op == "curveTo":
                for t in np.linspace(0, 1, 12)[1:]:
                    a, b, c, d = map(np.array, pts); cur.append(tuple((1-t)**3*a + 3*(1-t)**2*t*b + 3*(1-t)*t*t*c + t**3*d))
            else:
                ctrl = list(args[:-1]); end = args[-1]
                # implied on-curve points
                seq = [p0]
                for i, c in enumerate(ctrl):
                    nxt = end if i == len(ctrl) - 1 else tuple((np.array(c) + np.array(ctrl[i + 1])) / 2)
                    a, b, d = map(np.array, (seq[-1], c, nxt))
                    for t in np.linspace(0, 1, 8)[1:]: cur.append(tuple((1-t)**2*a + 2*(1-t)*t*b + t*t*d))
                    seq.append(nxt)
        elif op in ("closePath", "endPath"):
            if len(cur) > 2: rings.append(Polygon([(x * SC, y * SC) for x, y in cur]).buffer(0))
            cur = []
    # even-odd assemble
    acc = None
    for r in sorted(rings, key=lambda p: -p.area):
        acc = r if acc is None else acc.symmetric_difference(r)
    return acc, _f["hmtx"][_cm[ord(ch)]][0] * SC

def score(ch, strokes):
    r, _ = ref_shape(ch); g = glyph_shape(strokes)
    if g is None: return 0, 1
    return r.intersection(g).area / r.area, g.difference(r).area / r.area

def _arc(P, T, Q):
    v = Q - P; L = float(np.hypot(*v))
    if L < 1e-6: return []
    c = T[0] * v[1] - T[1] * v[0]; dt = (T @ v) / L
    half = math.atan2(c / L, dt)                 # angle from T to chord
    if abs(half) < 1e-4: return [{"t": "L", "len": round(L, 1)}]
    ang = 2 * math.degrees(half); r = L / (2 * abs(math.sin(half)))
    return [{"t": "A", "r": round(r, 1), "ang": round(ang, 2)}]

def K(*knots, cut=(False, False), w=None):
    """a clean stroke through knots (x, y, heading[, width share]): one biarc (two circle arcs) between knots,
    the heading given at every knot, so the curve is smooth and has few segments. Widths interpolate between knots."""
    segs = []; lens = [0.0]
    for a, b in zip(knots, knots[1:]):
        P0 = np.array(a[:2], float); P1 = np.array(b[:2], float)
        T0 = np.array([math.cos(math.radians(a[2])), math.sin(math.radians(a[2]))]); T1 = np.array([math.cos(math.radians(b[2])), math.sin(math.radians(b[2]))])
        v = P1 - P0; tt = T0 + T1; den = 2 * (1 - T0 @ T1)
        if abs(den) < 1e-6:
            if abs(T0[0] * v[1] - T0[1] * v[0]) < 1e-3 * (np.hypot(*v) + 1): seg = [{"t": "L", "len": round(float(np.hypot(*v)), 1)}]
            else: d = (v @ v) / (4 * (v @ T1)); M = (P0 + d * T0 + P1 - d * T1) / 2; seg = _arc(P0, T0, M) + _arc(M, -(T1 * -1), P1) if False else _arc(P0, T0, M) + _arc(M, (M - (P0 + d * T0)) / (np.hypot(*(M - (P0 + d * T0))) or 1), P1)
        else:
            d = (-(v @ tt) + math.sqrt((v @ tt) ** 2 + den * (v @ v))) / den
            M = (P0 + d * T0 + P1 - d * T1) / 2; Tm = M - (P0 + d * T0); Tm = Tm / (np.hypot(*Tm) or 1)
            seg = _arc(P0, T0, M) + _arc(M, Tm, P1)
        segs += seg
        lens.append(lens[-1] + 1)
    st = {"x": knots[0][0], "y": knots[0][1], "h": knots[0][2] % 360, "segs": segs, "s": 0, "e": 1, "cap0": "auto" if cut[0] else "butt", "cap1": "auto" if cut[1] else "butt"}
    # widths at knots, placed at their length fraction along the centreline
    if any(len(k) > 3 for k in knots):
        C = np.array([(p[0], p[1]) for p in centre(st)]); Ls = np.r_[0, np.cumsum(np.hypot(*np.diff(C, axis=0).T))]; fr = []; lo = 0
        for k in knots:
            dd = np.hypot(C[lo:, 0] - k[0], C[lo:, 1] - k[1]); i = lo + int(np.argmin(dd)); fr.append(Ls[i] / (Ls[-1] or 1)); lo = i
        fr[0], fr[-1] = 0.0, 1.0
        kw = [(f, (k[3] if len(k) > 3 else 1.0)) for f, k in zip(fr, knots)]
        # smooth (smoothstep) between knots: no kinks in the outline where the width changes
        out = []
        for (f0, w0), (f1, w1) in zip(kw, kw[1:]):
            for u in np.linspace(0, 1, 9)[:-1]: out.append([round(f0 + u * (f1 - f0), 4), round(w0 + (w1 - w0) * (3 * u * u - 2 * u ** 3), 4)])
        out.append([1.0, kw[-1][1]]); st["wp"] = out
    if w is not None: st["wk"] = w
    return st

def over(st, halo=0.16): st["over"] = True; st["halo"] = halo; return st
def loop(st, mode, at, halo=0.16):
    """passover / passunder from segment index at"""
    st["loop"] = {"at": at, "mode": mode, "halo": halo}; return st

def lens(x, y, l=118, r=118, t=0.62, up=False):
    """the shared Böcklin foot / top serif: a lens lying on the line, its tips lifting off it (one shape everywhere):
    a single shallow circular arc, thick in the middle, thin at the tips"""
    s = -1 if up else 1; ks = []
    if l: ks.append((x - l, y + s * 30, -s * 9, .26))
    ks.append((x, y + s * 38, 0, t))
    if r: ks.append((x + r, y + s * 30, s * 9, .26))
    if not l: ks.insert(0, (x - 40, y + s * 38, 0, t))
    if not r: ks.append((x + 40, y + s * 38, 0, t))
    return K(*ks)
