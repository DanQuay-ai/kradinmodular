"""Stroke fitting by optimisation (built for Arnold Böcklin, works for any traced Latin font).

  python3 fitopt.py REF_FONT latin/<id>.json [--chars ...]

Each stroke of the traced draft is turned into a few clean control points along its centre line (a smooth
spline through them), each with a width. The points and widths are then moved, one at a time, to make the
rebuilt letter cover the reference ink as exactly as possible, while a smoothness term keeps the lines clean.
Ink that no stroke covers is read again (its own centre line) and added as a new stroke, then fitted too.
The result is written back as turtle strokes (G1 arc splines) with width profiles, for the lab and buildotf."""
import sys, json, math, argparse
import numpy as np
from scipy import ndimage
from scipy.interpolate import CubicSpline
from skimage.morphology import skeletonize
from PIL import Image, ImageDraw
sys.path.insert(0, "/home/claude/work/gen")
import autotrace as AT
import freetype
import bkplans as PL
PLANNED = set()
from fontTools.ttLib import TTFont
from fontTools.pens.boundsPen import BoundsPen


def stroke_points(st):
    """dense centre line of a turtle stroke, with its width share along it"""
    pts = [(st["x"], st["y"])]; x, y, h = st["x"], st["y"], st["h"]
    for g in st["segs"]:
        if g["t"] == "C": h += g["ang"]; continue
        if g["t"] == "L":
            n = max(1, int(g["len"] / 4))
            for i in range(n): x += g["len"] / n * math.cos(math.radians(h)); y += g["len"] / n * math.sin(math.radians(h)); pts.append((x, y))
        else:
            sg = 1 if g["ang"] > 0 else -1; r = g["r"]
            cx = x + r * math.cos(math.radians(h + 90 * sg)); cy = y + r * math.sin(math.radians(h + 90 * sg))
            a0 = math.atan2(y - cy, x - cx); n = max(2, int(abs(g["ang"]) / 4))
            for i in range(1, n + 1):
                a = a0 + math.radians(g["ang"]) * i / n; x, y = cx + r * math.cos(a), cy + r * math.sin(a); pts.append((x, y))
            h += g["ang"]
    P = np.array(pts); L = np.r_[0, np.cumsum(np.hypot(*np.diff(P, axis=0).T))]; T = L[-1] or 1
    if "wp" in st: wp = np.array(st["wp"]); w = np.interp(L / T, wp[:, 0], wp[:, 1])
    else: w = np.full(len(P), st.get("wk", 1.0))
    return P, w


class Stroke:
    def __init__(self, P, w, W, closed=False, caps=("butt", "butt")):
        P = np.asarray(P, float); L = np.r_[0, np.cumsum(np.hypot(*np.diff(P, axis=0).T))]; T = L[-1] or 1
        n = int(np.clip(round(T / max(45, W * 0.7)) + 1, 3, 24))
        s = np.linspace(0, T, n)
        self.C = np.c_[np.interp(s, L, P[:, 0]), np.interp(s, L, P[:, 1])]
        self.w = np.interp(s, L, w * W)
        self.closed = closed; self.caps = caps; self.over = False; self.halo = 0.16; self.kind = "s"

    def curve(self, m=8):
        n = len(self.C); t = np.arange(n)
        if n < 3: return self.C.copy(), self.w.copy()
        cs = CubicSpline(t, self.C, bc_type="natural"); cw = CubicSpline(t, self.w, bc_type="natural")
        tt = np.linspace(0, n - 1, (n - 1) * m + 1)
        return cs(tt), np.maximum(cw(tt), 2.0)

    def polygon(self, extra=0.0):
        P, w = self.curve(); w = w + extra
        T = np.gradient(P, axis=0); T /= np.maximum(1e-9, np.hypot(*T.T))[:, None]
        N = np.c_[-T[:, 1], T[:, 0]]
        return np.vstack([P + N * (w / 2)[:, None], (P - N * (w / 2)[:, None])[::-1]])


class Glyph:
    def __init__(self, ink, left, top, cuts):
        self.ink = ink; self.left = left; self.top = top; self.cuts = cuts; self.W = 90.0
        self.area = ink.sum()
        # weight map: being wrong far from an edge matters more than a pixel at the edge
        self.din = ndimage.distance_transform_edt(ink); self.dout = ndimage.distance_transform_edt(~ink)

    def raster(self, strokes):
        im = Image.new("L", (self.ink.shape[1], self.ink.shape[0]), 0); dr = ImageDraw.Draw(im)
        for s in strokes:
            if s.over: dr.polygon([(x - self.left, self.top - y) for x, y in s.polygon(2 * s.halo * self.W)], fill=0)
            pg = s.polygon(); dr.polygon([(x - self.left, self.top - y) for x, y in pg], fill=255)
        # flat cuts on the alignment lines: nothing below the baseline unless the reference has ink there
        return np.array(im) > 127

    def cost(self, strokes):
        rb = self.raster(strokes)
        miss = (self.ink & ~rb); extra = (rb & ~self.ink)
        return (np.minimum(self.din[miss], 12).sum() + 1.3 * np.minimum(self.dout[extra], 12).sum()) / self.area


def smooth_pen(strokes, W):
    p = 0.0
    for s in strokes:
        if len(s.C) >= 3:
            d2 = s.C[2:] - 2 * s.C[1:-1] + s.C[:-2]; p += np.sum(d2 ** 2) / (W * W) * 0.004
            w2 = s.w[2:] - 2 * s.w[1:-1] + s.w[:-2]; p += np.sum(w2 ** 2) / (W * W) * 0.002
    return p


def optimise(G, strokes, W, rounds=4):
    best = G.cost(strokes) + smooth_pen(strokes, W)
    for step in (W * 0.25, W * 0.12, W * 0.06, W * 0.03)[:rounds]:
        improved = True; sweeps = 0
        while improved and sweeps < 3:
            improved = False; sweeps += 1
            for s in strokes:
                for i in range(len(s.C)):
                    for kind, delta in (("x", step), ("x", -step), ("y", step), ("y", -step), ("w", step * 0.8), ("w", -step * 0.8)):
                        old = (s.C[i].copy(), s.w[i])
                        if kind == "x": s.C[i, 0] += delta
                        elif kind == "y": s.C[i, 1] += delta
                        else: s.w[i] = max(4.0, s.w[i] + delta)
                        c = G.cost(strokes) + smooth_pen(strokes, W)
                        if c < best - 1e-5: best = c; improved = True
                        else: s.C[i], s.w[i] = old
    return best


def residual_strokes(G, strokes, W, S=1):
    """ink no stroke covers, read again as new strokes"""
    rb = G.raster(strokes); miss = G.ink & ~rb
    miss = ndimage.binary_opening(miss, iterations=max(1, int(W / 10)))
    lab, n = ndimage.label(miss); out = []
    for c in range(1, n + 1):
        m = lab == c
        if m.sum() < (W * W) * 0.4: continue
        sk = skeletonize(m); pts = np.argwhere(sk)
        if len(pts) < W * 0.6: continue
        # order the skeleton points by walking from one end (longest path approximation via PCA)
        cen = pts.mean(0); u = np.linalg.svd(pts - cen)[2][0]; order = np.argsort((pts - cen) @ u)
        P = np.array([[G.left + c_, G.top - r_] for r_, c_ in pts[order]], float)
        P = AT.smooth(P, 3) if len(P) > 5 else P
        dist = ndimage.distance_transform_edt(m)
        wv = np.array([2 * dist[r_, c_] for r_, c_ in pts[order]])
        out.append(Stroke(P, np.maximum(wv, 4) / W, W))
    return out


# letter plans in clean lines, in the letter's box (0..1): used when the traced reading fails
TEMPLATES = {
    "Z": [[(0, 1), (1, 1)], [(1, 1), (0, 0)], [(0, 0), (1, 0)]], "z": [[(0, 1), (1, 1)], [(1, 1), (0, 0)], [(0, 0), (1, 0)]],
    "N": [[(0, 0), (0, 1)], [(0, 1), (1, 0)], [(1, 0), (1, 1)]], "X": [[(0, 1), (1, 0)], [(1, 1), (0, 0)]], "x": [[(0, 1), (1, 0)], [(1, 1), (0, 0)]],
    "V": [[(0, 1), (0.5, 0)], [(0.5, 0), (1, 1)]], "v": [[(0, 1), (0.5, 0)], [(0.5, 0), (1, 1)]],
    "A": [[(0, 0), (0.5, 1)], [(0.5, 1), (1, 0)], [(0.2, 0.35), (0.8, 0.35)]],
    "K": [[(0, 0), (0, 1)], [(1, 1), (0.05, 0.45)], [(0.3, 0.6), (1, 0)]], "k": [[(0, 0), (0, 1)], [(1, 0.7), (0.05, 0.3)], [(0.3, 0.45), (1, 0)]],
    "Y": [[(0, 1), (0.5, 0.45)], [(1, 1), (0.5, 0.45)], [(0.5, 0.45), (0.5, 0)]],
    "W": [[(0, 1), (0.25, 0)], [(0.25, 0), (0.5, 1)], [(0.5, 1), (0.75, 0)], [(0.75, 0), (1, 1)]],
    "w": [[(0, 1), (0.25, 0)], [(0.25, 0), (0.5, 1)], [(0.5, 1), (0.75, 0)], [(0.75, 0), (1, 1)]],
    "M": [[(0, 0), (0, 1)], [(0, 1), (0.5, 0.2)], [(0.5, 0.2), (1, 1)], [(1, 1), (1, 0)]],
    "T": [[(0, 1), (1, 1)], [(0.5, 1), (0.5, 0)]], "L": [[(0, 1), (0, 0)], [(0, 0), (1, 0)]], "H": [[(0, 0), (0, 1)], [(1, 0), (1, 1)], [(0, 0.5), (1, 0.5)]],
    "E": [[(0, 0), (0, 1)], [(0, 1), (1, 1)], [(0, 0.5), (0.8, 0.5)], [(0, 0), (1, 0)]], "F": [[(0, 0), (0, 1)], [(0, 1), (1, 1)], [(0, 0.5), (0.8, 0.5)]],
    "I": [[(0.5, 0), (0.5, 1)]], "l": [[(0.5, 0), (0.5, 1)]], "i": [[(0.5, 0), (0.5, 0.7)], [(0.5, 0.88), (0.5, 1)]],
}


def to_turtle(s, W):
    P, w = s.curve(6)
    st = AT.biarc_turtle(P, W)
    L = np.r_[0, np.cumsum(np.hypot(*np.diff(P, axis=0).T))]; T = L[-1] or 1
    tt = (1 - np.cos(np.linspace(0, np.pi, 33))) / 2
    st["wp"] = [[round(float(a), 3), round(float(b), 3)] for a, b in zip(tt, np.interp(tt * T, L, w) / W)]
    st["cap0"], st["cap1"] = "butt", "butt"
    if s.over: st["over"] = True; st["halo"] = s.halo
    st["part"] = s.kind
    return st


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("font"); ap.add_argument("data"); ap.add_argument("--chars", default=""); ap.add_argument("--out", default=""); ap.add_argument("--plans", action="store_true")
    a = ap.parse_args()
    d = json.load(open(a.data)); m = d["metrics"]; W = m["W"]
    tt = TTFont(a.font); upm = tt["head"].unitsPerEm; gs = tt.getGlyphSet(); cm = tt.getBestCmap()
    cap = getattr(tt["OS/2"], "sCapHeight", 0) or (lambda b: (gs[cm[ord("H")]].draw(b), b.bounds[3])[1])(BoundsPen(gs))
    k = 700 / cap; face = freetype.Face(a.font); face.set_char_size(int(upm * k * 64))
    PUN = {"@period": ".", "@comma": ",", "@hyphen": "-", "@exclam": "!", "@question": "?", "@quote": "'"}
    rep = {}
    for key, g in d["glyphs"].items():
        ch = PUN.get(key, key)
        if a.chars and ch not in a.chars: continue
        if len(ch) != 1 or ord(ch) not in cm: continue
        r = AT.render(face, ch, k, pad=30)
        if r is None: continue
        ink, left, top, adv = r
        G = Glyph(ink, left, top, [m["desc"], 0, m["x"], 700, m["asc"]]); G.W = W
        strokes = []
        for st in g["strokes"]:
            P, w = stroke_points(st)
            if len(P) >= 2 and np.hypot(*(P[-1] - P[0])) + 1 > 2:
                s_ = Stroke(P, w, W)
                if st.get("over"): s_.over = True; s_.halo = st.get("halo", 0.16)
                strokes.append(s_)
        c0 = G.cost(strokes)
        if a.plans and ch in PL.PLANS:
            # standard parts from the letter plan, fitted to the reference; kept unless clearly worse than the trace
            traced = strokes; c_tr = G.cost(traced)
            ys, xs = np.nonzero(ink); x0 = left + xs.min(); x1 = left + xs.max()
            plan = []
            for kind, pts, over in PL.PLANS[ch]:
                P = np.array([[x0 + (x1 - x0) * u, y] for u, y in pts], float)
                if kind == "f": w = np.interp(np.linspace(0, 1, 9), np.linspace(0, 1, len(PL.FOOT_W)), PL.FOOT_W)
                else: w = np.full(2, PL.WIDTH[kind])
                P = np.array([np.interp(np.linspace(0, 1, 9 if kind == "f" else max(3, len(P) * 2)), np.linspace(0, 1, len(P)), P[:, k]) for k in (0, 1)]).T
                s_ = Stroke(P, np.interp(np.linspace(0, 1, len(P)), np.linspace(0, 1, len(w)), w), W); s_.kind = kind; s_.over = over
                plan.append(s_)
            optimise(G, plan, W)
            new = residual_strokes(G, plan, W)
            if new: plan += new; optimise(G, plan, W, rounds=2)
            if G.cost(plan) <= c_tr + 0.12: strokes = plan; c0 = c_tr; PLANNED.add(ch)
            else: optimise(G, strokes, W)
        else:
            optimise(G, strokes, W)
        for _ in range(0 if ch in PLANNED else 2):          # missing parts: read them, add them, fit everything again
            new = residual_strokes(G, strokes, W)
            if not new: break
            strokes += new; optimise(G, strokes, W, rounds=3)
        # a stroke that crosses itself: the later part is the loop that passes over the earlier part
        for s in list(strokes):
            if ch in PLANNED: break
            P, w = s.curve(4); n = len(P); hit = None
            for i in range(0, n - 8, 2):
                for j in range(i + 8, n - 1, 2):
                    if np.hypot(*(P[i] - P[j])) < W * 0.25: hit = (i, j); break
                if hit: break
            if not hit: continue
            j = hit[1]; cut = max(hit[0] + 4, j - int(W / 4))
            a_, b_ = Stroke(P[:cut + 1], w[:cut + 1] / W, W), Stroke(P[cut:], w[cut:] / W, W); b_.over = True
            trial = [x for x in strokes if x is not s] + [a_, b_]
            if G.cost(trial) < G.cost(strokes) - 0.005: strokes = trial
        if ch in PLANNED: pass
        else:
          # loops: try each stroke as one that passes over the others with a white halo (drawn last)
          base = G.cost(strokes) + smooth_pen(strokes, W)
          for s in list(strokes):
            if len(strokes) < 2 or ch in PLANNED: break
            trial = [x for x in strokes if x is not s] + [s]; s.over = True
            for hv in (0.12, 0.2):
                s.halo = hv; c = G.cost(trial) + smooth_pen(trial, W)
                if c < base - 0.01: base = c; strokes = trial; break
            else: s.over = False
        if any(s.over for s in strokes): optimise(G, strokes, W, rounds=2)
        c1 = G.cost(strokes)
        # a reading that went wrong (a Z read as a loop): start again from the letter's plan, in clean lines
        if ch in TEMPLATES and c1 > 0.15 and ch not in PLANNED:
            ys, xs = np.nonzero(ink); x0, x1 = left + xs.min() + W / 2, left + xs.max() - W / 2; y0, y1 = top - ys.max() + W / 2, top - ys.min() - W / 2
            alt = [Stroke(np.array([[x0 + (x1 - x0) * u, y0 + (y1 - y0) * v] for u, v in seg]), np.ones(2), W) for seg in TEMPLATES[ch]]
            optimise(G, alt, W)
            if G.cost(alt) < c1: strokes = alt; c1 = G.cost(alt)
        rb = G.raster(strokes)
        cov = (rb & ink).sum() / ink.sum(); spill = (rb & ~ink).sum() / max(1, rb.sum())
        g["strokes"] = [to_turtle(s, W) for s in strokes]
        g["fit"] = {"covered": round(float(cov), 3), "outside": round(float(spill), 3), "strokes": len(strokes), "method": "optimised"}
        rep[ch] = g["fit"]; print(ch, round(c0, 3), "->", round(c1, 3), "covered", round(cov, 3), "outside", round(spill, 3), len(strokes), flush=True)
    if a.out: json.dump({k_: d["glyphs"][k_] for k_ in d["glyphs"] if PUN.get(k_, k_) in rep}, open(a.out, "w"), ensure_ascii=False, separators=(",", ":"))
    else: json.dump(d, open(a.data, "w"), ensure_ascii=False, separators=(",", ":"))
    if rep:
        print("mean covered %.3f outside %.3f" % (np.mean([r["covered"] for r in rep.values()]), np.mean([r["outside"] for r in rep.values()])))


if __name__ == "__main__":
    main()
