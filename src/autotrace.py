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


def trace_glyph(face, ch, scale, S=2):
    r = render(face, ch, scale * S, pad=40 * S)
    if r is None: return None, None, 0, None
    ink, left, top, adv = r
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
            P = resample(P, 2.0 * S)
            P = smooth(P, max(1.0, W / 5 / 2.0))
            P = sharpen_corners(P, W)
            # width profile along the stroke, as a share of the glyph's median weight
            Ls = np.r_[0, np.cumsum(np.hypot(*np.diff(P, axis=0).T))]; T = Ls[-1] or 1
            ws = np.array([2 * dist[min(ink.shape[0]-1, max(0, int(round(p[0])))), min(ink.shape[1]-1, max(0, int(round(p[1]))))] for p in P])
            interior = ws[(Ls > W * 0.6) & (Ls < T - W * 0.6)]
            fill = float(np.median(interior)) if interior.size else float(np.median(ws))
            ws = np.where((Ls < W * 0.6) | (Ls > T - W * 0.6), np.maximum(ws, 0.0), ws)
            # ends: the medial axis thins out before the edge; hold the last interior width
            for idx in np.nonzero(Ls < W * 0.6)[0]: ws[idx] = interior[0] if interior.size else fill
            for idx in np.nonzero(Ls > T - W * 0.6)[0]: ws[idx] = interior[-1] if interior.size else fill
            ws = ndimage.gaussian_filter1d(ws, max(1.0, len(ws) / 40))
            D = np.array([[(left + c) / S, (top - rr) / S] for rr, c in P])
            st = to_turtle(fit_pieces(D, max(1.5, W / S / 12), W / S))
            if not st or not st["segs"]: continue
            n = 16; tt = np.linspace(0, 1, n)
            wp = np.interp(tt * T, Ls, ws) / W
            if wp.max() - wp.min() > 0.08: st["wp"] = [[round(float(a), 3), round(float(b), 3)] for a, b in zip(tt, wp)]
            else: st["wk"] = round(float(np.median(wp)), 3)
            strokes.append(st)
    # small separate marks (dots of i, j, punctuation) whose skeleton was pruned away
    lab, n = ndimage.label(ink)
    for c in range(1, n + 1):
        m = lab == c
        if (sk & m).sum() > W * 0.8: continue
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
    gs = tt.getGlyphSet(); cmap = tt.getBestCmap(); ghost = {}
    for ch in a.chars:
        if ord(ch) not in cmap: continue
        st, W, adv, raster = trace_glyph(face, ch, k)
        if st is None: continue
        Ws.append(W); cov, spill = score(st, W, raster); report[ch] = {"covered": cov, "outside": spill, "strokes": len(st)}
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
