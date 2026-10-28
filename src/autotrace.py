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
import argparse, json, math
import numpy as np, freetype
from scipy import ndimage
from skimage.morphology import skeletonize
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen

def cross2(v, P):
    P = np.atleast_2d(P); return v[0] * P[:, 1] - v[1] * P[:, 0]


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


def to_turtle(pieces, cap="butt"):
    first = pieces[0][1]
    x, y = first[0]; h = None; segs = []
    def ang(v): return math.degrees(math.atan2(v[1], v[0]))
    def turn(a, b): return ((b - a + 180) % 360) - 180
    for kind, Q, arc in pieces:
        if kind == "L":
            v = Q[-1] - Q[0]; hh = ang(v); L = float(np.hypot(*v))
            if L < 1: continue
            if h is None: h0 = hh; h = hh
            elif abs(turn(h, hh)) > 0.5: segs.append({"t": "C", "ang": round(turn(h, hh), 2)}); h = hh
            segs.append({"t": "L", "len": round(L, 1)})
        else:
            cx, cy, r, _ = arc
            a0 = math.atan2(Q[0][1] - cy, Q[0][0] - cx); a1 = math.atan2(Q[-1][1] - cy, Q[-1][0] - cx)
            mid = Q[len(Q) // 2]; am = math.atan2(mid[1] - cy, mid[0] - cx)
            # direction of travel: anticlockwise if the middle lies between a0 and a1 going +
            d01 = (a1 - a0) % (2 * math.pi); d0m = (am - a0) % (2 * math.pi)
            sweep = d01 if d0m < d01 else d01 - 2 * math.pi
            if len(Q) > 8 and np.hypot(*(Q[0] - Q[-1])) < 2: sweep = 2 * math.pi * (1 if d0m < math.pi else -1)
            sg = 1 if sweep > 0 else -1
            ht = math.degrees(a0) + 90 * sg       # tangent heading at the start
            if h is None: h0 = ht; h = ht
            elif abs(turn(h, ht)) > 0.5: segs.append({"t": "C", "ang": round(turn(h, ht), 2)}); h = ht
            segs.append({"t": "A", "r": round(r, 1), "ang": round(math.degrees(sweep), 2)})
            h += math.degrees(sweep)
    if h is None: return None
    return {"x": round(float(x), 1), "y": round(float(y), 1), "h": round(h0 % 360, 2), "segs": segs,
            "s": 0, "e": 1, "cap0": cap, "cap1": cap}


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


def trace_glyph(face, ch, scale):
    r = render(face, ch, scale)
    if r is None: return None, None, 0
    ink, left, top, adv = r
    dist = ndimage.distance_transform_edt(ink)
    sk = skeletonize(ink)
    W = float(np.median(dist[sk])) * 2 if sk.any() else 0
    sk = prune(sk, W)
    pts, nb = graph(sk)
    if not pts: return [], W, adv
    E = merge(edges_of(pts, nb), nb, W)
    strokes = []
    for e in E:
        if len(e) < max(4, W * 0.35): continue
        P = extend(e, ink, dist, W) if e[0] != e[-1] else [tuple(map(float, p)) for p in e]
        # to design coordinates: x = left + c, y = top - r
        D = np.array([[left + c, top - rr] for rr, c in P])
        st = to_turtle(fit_pieces(D, max(2.0, W / 8), W))
        if st and st["segs"]: strokes.append(st)
    # small separate marks (dots of i, j, punctuation) whose skeleton was pruned away
    lab, n = ndimage.label(ink)
    for c in range(1, n + 1):
        m = lab == c
        if (sk & m).sum() > W * 0.8: continue
        rr, cc = np.nonzero(m); h = rr.max() - rr.min() + 1; w = cc.max() - cc.min() + 1
        x0, y0 = left + (cc.min() + cc.max()) / 2, top - (rr.min() + rr.max()) / 2
        if h >= w: L = float(h); strokes.append({"x": round(float(x0), 1), "y": round(float(y0 - L / 2), 1), "h": 90, "segs": [{"t": "L", "len": round(float(L), 1)}], "s": 0, "e": 1, "cap0": "butt", "cap1": "butt", "w": round(float(w), 1)})
        else: L = float(w); strokes.append({"x": round(float(x0 - L / 2), 1), "y": round(float(y0), 1), "h": 0, "segs": [{"t": "L", "len": round(float(L), 1)}], "s": 0, "e": 1, "cap0": "butt", "cap1": "butt", "w": round(float(h), 1)})
    # writing order: top-left first
    strokes.sort(key=lambda s: (round(s["x"] / 60), -s["y"]))
    return strokes, W, adv


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("font"); ap.add_argument("out")
    ap.add_argument("--chars", default="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789")
    ap.add_argument("--name", default=""); ap.add_argument("--ghost", default="")
    ap.add_argument("--version", default="latin-1")
    a = ap.parse_args()
    tt = TTFont(a.font); upm = tt["head"].unitsPerEm
    cap = getattr(tt["OS/2"], "sCapHeight", 0) or 0.7 * upm
    xh = getattr(tt["OS/2"], "sxHeight", 0) or 0.5 * upm
    k = 700 / cap                                     # design units per font unit
    face = freetype.Face(a.font); face.set_char_size(int(upm * k * 64))   # 1 px = 1 design unit
    glyphs = {}; Ws = []
    gs = tt.getGlyphSet(); cmap = tt.getBestCmap(); ghost = {}
    for ch in a.chars:
        if ord(ch) not in cmap: continue
        st, W, adv = trace_glyph(face, ch, k)
        if st is None: continue
        Ws.append(W)
        key = ch if ch.isalnum() else "@" + {".": "period", ",": "comma", "-": "hyphen", "!": "exclam", "?": "question", "'": "quote"}.get(ch, "u%04x" % ord(ch))
        glyphs[key] = {"type": "radical", "group": "upper" if ch.isupper() else "lower" if ch.islower() else "digit" if ch.isdigit() else "other",
                       "strokes": st, "status": "draft", "adv": round(adv, 1), "W": round(W, 1)}
        sp = SVGPathPen(gs); gs[cmap[ord(ch)]].draw(TransformPen(sp, (k, 0, 0, k, 0, 0)))
        ghost[key] = {"d": sp.getCommands()}
    W = float(np.median(Ws)) if Ws else 60
    out = {"_version": a.version, "name": a.name or tt["name"].getDebugName(1), "metrics": {"cap": 700, "x": round(xh * k), "asc": round(tt["hhea"].ascent * k), "desc": round(tt["hhea"].descent * k), "W": round(W, 1)}, "glyphs": glyphs}
    json.dump(out, open(a.out, "w"), ensure_ascii=False, separators=(",", ":"))
    if a.ghost: json.dump(ghost, open(a.ghost, "w"), separators=(",", ":"))
    print(len(glyphs), "glyphs, stroke weight", round(W, 1), "x-height", out["metrics"]["x"])


if __name__ == "__main__":
    main()
