"""Turn traced stroke data into a clean static font.

  python3 buildotf.py latin/<id>.json REFERENCE_FONT OUT.otf "Family Name" [--weight 1.0]

1. Every stroke becomes its outline (same geometry as the site: width profile, flat cuts on alignment lines).
2. The strokes of a glyph are merged into one shape (no overlaps).
3. Each contour is redrawn as cubic Béziers by type-design rules:
   - nodes only at horizontal / vertical extrema and at real corners (a split node is added only where a
     single curve cannot follow the shape, and it is smooth: its two handles are colinear);
   - handles at an extremum are exactly horizontal or vertical;
   - all coordinates are integers; outer contours anticlockwise, counters clockwise.
Metrics (advance widths, ascender, descender) follow the reference font.
"""
import sys, json, math, argparse
import numpy as np
from scipy import ndimage
from shapely.geometry import Polygon, MultiPolygon
from shapely.geometry.polygon import orient
from shapely.ops import unary_union
from fontTools.ttLib import TTFont
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.pens.boundsPen import BoundsPen
sys.path.insert(0, "/home/claude/work/gen")
import autotrace


def resample_closed(P, step):
    P = np.vstack([P, P[:1]]); d = np.r_[0, np.cumsum(np.hypot(*np.diff(P, axis=0).T))]
    n = max(8, int(d[-1] / step)); s = np.linspace(0, d[-1], n, endpoint=False)
    return np.c_[np.interp(s, d, P[:, 0]), np.interp(s, d, P[:, 1])]


def fit_cubic(Q, t0, t1):
    """least-squares handle lengths for fixed tangent directions t0 (out of P0) and t1 (into P3)"""
    P0, P3 = Q[0], Q[-1]
    d = np.r_[0, np.cumsum(np.hypot(*np.diff(Q, axis=0).T))]; L = d[-1] or 1; u = d / L
    for _ in range(3):
        b0, b1, b2, b3 = (1 - u) ** 3, 3 * u * (1 - u) ** 2, 3 * u * u * (1 - u), u ** 3
        A1 = b1[:, None] * t0[None]; A2 = -b2[:, None] * t1[None]
        R = Q - (b0 + b1)[:, None] * P0 - (b2 + b3)[:, None] * P3
        M = np.array([[np.sum(A1 * A1), np.sum(A1 * A2)], [np.sum(A1 * A2), np.sum(A2 * A2)]])
        v = np.array([np.sum(A1 * R), np.sum(A2 * R)])
        try: a, b = np.linalg.solve(M, v)
        except np.linalg.LinAlgError: a = b = L / 3
        a = min(max(a, L * 0.02), L * 1.2); b = min(max(b, L * 0.02), L * 1.2)
        C1, C2 = P0 + a * t0, P3 - b * t1
        B = lambda uu: ((1 - uu) ** 3)[:, None] * P0 + (3 * uu * (1 - uu) ** 2)[:, None] * C1 + (3 * uu * uu * (1 - uu))[:, None] * C2 + (uu ** 3)[:, None] * P3
        # reparametrise: nearest parameter for each sample (one Newton step)
        Bu = B(u); dB = (3 * (1 - u) ** 2)[:, None] * (C1 - P0) + (6 * u * (1 - u))[:, None] * (C2 - C1) + (3 * u * u)[:, None] * (P3 - C2)
        u = np.clip(u - np.sum((Bu - Q) * dB, 1) / np.maximum(1e-9, np.sum(dB * dB, 1)), 0, 1); u[0], u[-1] = 0, 1
    err = np.hypot(*(B(u) - Q).T)
    return (P0, C1, C2, P3), float(err.max()), int(err.argmax())


def redraw(ring, tol=1.6, corner=38):
    P = resample_closed(np.asarray(ring, float), 2.0)
    S = ndimage.gaussian_filter1d(P, 1.2, axis=0, mode="wrap"); n = len(S)
    tan = np.roll(S, -2, 0) - np.roll(S, 2, 0); tan /= np.maximum(1e-9, np.hypot(*tan.T))[:, None]
    # corners: direction change over a short window
    w = 4
    tin = S - np.roll(S, w, 0); tout = np.roll(S, -w, 0) - S
    tin /= np.maximum(1e-9, np.hypot(*tin.T))[:, None]; tout /= np.maximum(1e-9, np.hypot(*tout.T))[:, None]
    ang = np.degrees(np.arccos(np.clip(np.sum(tin * tout, 1), -1, 1)))
    cor = [i for i in range(n) if ang[i] > corner and ang[i] >= ang[(i - 1) % n] and ang[i] >= ang[(i + 1) % n]]
    # extrema: tangent crosses horizontal or vertical
    ext = {}
    for i in range(n):
        j = (i + 1) % n
        for k, kind in ((0, "v"), (1, "h")):     # x' = 0 -> vertical tangent; y' = 0 -> horizontal tangent
            if tan[i][k] == 0 or tan[i][k] * tan[j][k] < 0:
                ii = i if abs(tan[i][k]) < abs(tan[j][k]) else j
                if all(min(abs(ii - c), n - abs(ii - c)) > w for c in cor): ext[ii] = kind
    nodes = sorted(set(cor) | set(ext))
    nodes = [a for k, a in enumerate(nodes) if k == 0 or a - nodes[k - 1] > 2]
    if len(nodes) < 2: nodes = [0, n // 2]
    def tdir(i, side):
        if i in ext:
            v = tan[i].copy()
            if ext[i] == "v": v = np.array([0.0, math.copysign(1, v[1])])
            else: v = np.array([math.copysign(1, v[0]), 0.0])
            return v
        if i in cor: return (tout[i] if side > 0 else tin[i])
        return tan[i]
    segs = []
    def span(a, b):
        idx = [(a + k) % n for k in range(((b - a) % n or n) + 1)]
        Q = P[idx]; Q[0], Q[-1] = S[a], S[b]
        ch = Q[-1] - Q[0]; L = np.hypot(*ch)
        if L > 0:
            dev = np.abs(ch[0] * (Q[:, 1] - Q[0][1]) - ch[1] * (Q[:, 0] - Q[0][0])) / L
            if dev.max() < 1.0 and ((a not in ext) or (b not in ext)): segs.append(("L", Q[0], Q[-1])); return
        c, err, at = fit_cubic(Q, tdir(a, 1), tdir(b, -1))
        if err > tol and len(idx) > 12 and 3 < at < len(idx) - 4:
            m = idx[at]; span(a, m); span(m, b)
        else: segs.append(("C",) + c)
    for k in range(len(nodes)):
        span(nodes[k], nodes[(k + 1) % len(nodes)])
    return segs


SNAP = []      # alignment lines in design units (baseline, x-height, cap, ascender, descender)


def snapy(y, tol=14):
    for L in SNAP:
        if abs(y - L) < tol: return L
    return y


def draw(pen, segs, s, dx=0):
    # every point (and the handles that share its height at an extremum) close to an alignment line
    # is put exactly on it, so all glyphs sit on the same baseline, x-height and cap height
    R = lambda p: (int(round(p[0] * s + dx)), int(round(snapy(p[1]) * s)))
    start = R(segs[0][1]); pen.moveTo(start); cur = start
    for g in segs:
        if g[0] == "L":
            q = R(g[2])
            if q != cur: pen.lineTo(q); cur = q
        else:
            p0, c1, c2, p3 = (R(p) for p in g[1:])
            # keep extremum handles exactly horizontal / vertical after rounding
            if abs(c1[0] - p0[0]) <= 1: c1 = (p0[0], c1[1])
            if abs(c1[1] - p0[1]) <= 1: c1 = (c1[0], p0[1])
            if abs(c2[0] - p3[0]) <= 1: c2 = (p3[0], c2[1])
            if abs(c2[1] - p3[1]) <= 1: c2 = (c2[0], p3[1])
            if p3 == cur and c1 == cur and c2 == cur: continue
            pen.curveTo(c1, c2, p3); cur = p3
    pen.closePath()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("data"); ap.add_argument("ref"); ap.add_argument("out"); ap.add_argument("family")
    a = ap.parse_args()
    d = json.load(open(a.data)); m = d["metrics"]; W = m["W"]
    autotrace.CUTS[:] = [m["desc"], 0, m["x"], 700, m["asc"]]
    SNAP[:] = [0, m["x"], 700, m["asc"], m["desc"]]
    ref = TTFont(a.ref); upm = ref["head"].unitsPerEm; cm = ref.getBestCmap(); gs = ref.getGlyphSet()
    cap = getattr(ref["OS/2"], "sCapHeight", 0)
    if not cap: b = BoundsPen(gs); gs[cm[ord("H")]].draw(b); cap = b.bounds[3]
    s = cap / 700.0            # design units -> font units
    PUN = {"@period": ".", "@comma": ",", "@hyphen": "-", "@exclam": "!", "@question": "?", "@quote": "'"}
    order = [".notdef", "space"]; cmap = {32: "space"}; charstrings = {}; metrics = {}
    def blank(width):
        pen = T2CharStringPen(width, None); return pen.getCharString()
    charstrings[".notdef"] = blank(500); metrics[".notdef"] = (500, 0)
    sp = ref["hmtx"][cm[32]][0] if 32 in cm else 250
    charstrings["space"] = blank(sp); metrics["space"] = (sp, 0)
    nodes_total = 0
    for key, g in d["glyphs"].items():
        ch = PUN.get(key, key)
        if len(ch) != 1: continue
        polys = []; acc = None
        def P_(pg):
            p = Polygon(pg); return p if p.is_valid else p.buffer(0)
        for st in g["strokes"]:
            for pg in autotrace.outline_polys(st, W):
                p = P_(pg)
                if p.area <= 1: continue
                polys.append(p)
                if st.get("over") and acc is not None:   # passes over: cut its white halo out of what is already drawn
                    halo = dict(st, over=False, wk=None, wp=[[t, w + 2 * st.get("halo", 0.16)] for t, w in (st.get("wp") or [[0, st.get("wk", 1)], [1, st.get("wk", 1)]])])
                    halo.pop("wk")
                    for hg in autotrace.outline_polys(halo, W): acc = acc.difference(P_(hg))
                acc = p if acc is None else acc.union(p)
        if not polys: continue
        shape = acc
        if shape.is_empty or not shape.is_valid: shape = unary_union([p.buffer(0) for p in polys])
        if hasattr(shape, "geoms") and not isinstance(shape, MultiPolygon): shape = MultiPolygon([g_ for g_ in shape.geoms if isinstance(g_, Polygon)])
        geoms = list(shape.geoms) if isinstance(shape, MultiPolygon) else [shape]
        twin = {"Ɔ": "C", "ɔ": "c", "Ɛ": "3", "ɛ": "3"}
        srcch = ch if ord(ch) in cm else twin.get(ch)
        adv = ref["hmtx"][cm[ord(srcch)]][0] if srcch and ord(srcch) in cm else 500
        name = {"Ɔ": "Oopen", "ɔ": "oopen", "Ɛ": "Eopen", "ɛ": "eopen"}.get(ch) or cm.get(ord(ch)) or "uni%04X" % ord(ch)
        pen = T2CharStringPen(adv, None)
        for gm in geoms:
            if gm.is_empty or gm.area < 4: continue
            gm = orient(gm, 1.0)
            for ring in [gm.exterior] + list(gm.interiors):
                segs = redraw(list(ring.coords)[:-1]); nodes_total += len(segs)
                draw(pen, segs, s)
        cs = pen.getCharString(); charstrings[name] = cs
        if not (srcch == ch):   # made glyphs: space them from their own ink with the twin's side bearings
            xs = [c[0] for gm in geoms if not gm.is_empty for c in gm.exterior.coords]
            if xs and srcch and ord(srcch) in cm:
                bp = BoundsPen(gs); gs[cm[ord(srcch)]].draw(bp); lsb, rsb = bp.bounds[0], adv - bp.bounds[2]
                shift = lsb - min(xs) * s; adv = int(round((max(xs) - min(xs)) * s + lsb + rsb))
                pen = T2CharStringPen(adv, None)
                for gm in geoms:
                    if gm.is_empty or gm.area < 4: continue
                    gm = orient(gm, 1.0)
                    for ring in [gm.exterior] + list(gm.interiors): draw(pen, redraw(list(ring.coords)[:-1]), s, dx=shift)
                charstrings[name] = pen.getCharString()
        b = BoundsPen(None);
        order.append(name); cmap[ord(ch)] = name; metrics[name] = (adv, 0)
    fb = FontBuilder(upm, isTTF=False)
    fb.setupGlyphOrder(order); fb.setupCharacterMap(cmap)
    ps = a.family.replace(" ", "") + "-Regular"
    fb.setupCFF(ps, {"FullName": a.family}, charstrings, {})
    # left side bearings from the drawn outlines
    from fontTools.pens.boundsPen import BoundsPen as BP
    gs2 = {}
    fb.setupHorizontalMetrics(metrics)
    asc, desc = ref["hhea"].ascent, ref["hhea"].descent
    fb.setupHorizontalHeader(ascent=asc, descent=desc)
    fb.setupNameTable({"familyName": a.family, "styleName": "Regular"})
    fb.setupOS2(sTypoAscender=asc, sTypoDescender=desc, usWinAscent=asc, usWinDescent=-desc, sCapHeight=int(cap), sxHeight=int(round(m["x"] * s)))
    fb.setupPost()
    f = fb.font
    # real lsb values
    gset = f.getGlyphSet()
    for gname in f.getGlyphOrder():
        bp = BP(gset); gset[gname].draw(bp)
        if bp.bounds: f["hmtx"][gname] = (f["hmtx"][gname][0], int(bp.bounds[0]))
    f.save(a.out)
    w2 = a.out.rsplit(".", 1)[0] + ".woff2"; f.flavor = "woff2"; f.save(w2)
    print(a.out, len(order), "glyphs,", nodes_total, "segments")


if __name__ == "__main__":
    main()
