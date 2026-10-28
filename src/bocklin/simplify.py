"""Turn a traced stroke (many tiny arcs) into a few clean knots (x, y, heading, width) and redraw it with K()."""
import json, math, sys, numpy as np, core
def knots_of(st, W, turn=32, maxlen=2.4):
    C = np.array([(p[0], p[1]) for p in core.centre(st)]); H = np.array([p[2] for p in core.centre(st)])
    if len(C) < 3: return None
    Ls = np.r_[0, np.cumsum(np.hypot(*np.diff(C, axis=0).T))]; T = Ls[-1]
    if T < 5: return None
    wp = np.array(st["wp"]) if st.get("wp") else np.array([[0, st.get("wk", 1)], [1, st.get("wk", 1)]])
    # smooth heading
    k = max(1, len(H) // 40); Hs = np.convolve(np.unwrap(np.radians(H)), np.ones(2 * k + 1) / (2 * k + 1), mode="same"); Hs[:k] = np.radians(H[:k]); Hs[-k:] = np.radians(H[-k:])
    idx = [0]; acc = 0
    for i in range(1, len(C) - 1):
        acc = abs(math.degrees(Hs[i] - Hs[idx[-1]]))
        if acc > turn or Ls[i] - Ls[idx[-1]] > maxlen * W: idx.append(i)
    if T - Ls[idx[-1]] < 0.35 * W and len(idx) > 1: idx[-1] = len(C) - 1
    else: idx.append(len(C) - 1)
    out = []
    for i in idx:
        h = math.degrees(Hs[i]) % 360
        for a in (0, 90, 180, 270, 360):          # near-vertical / horizontal tangents snap
            if abs(h - a) < 6: h = a % 360
        out.append((round(C[i][0], 1), round(C[i][1], 1), round(h, 1), round(float(np.interp(Ls[i] / T, wp[:, 0], wp[:, 1])), 3)))
    return out
def simplify(g, W):
    out = []
    for st in g["strokes"]:
        ks = knots_of(st, W)
        if not ks: continue
        n = core.K(*ks, cut=(st.get("cap0") == "auto", st.get("cap1") == "auto"))
        for k in ("over", "halo", "loop"):
            if k in st: n[k] = st[k]
        out.append(n)
    return out
if __name__ == "__main__":
    d = json.load(open(sys.argv[1])); W = d["metrics"]["W"]; core.W = W
    G = {k: simplify(g, W) for k, g in d["glyphs"].items()}
    json.dump(G, open(sys.argv[2], "w"))
