"""Stroke -> outline polygon, with a point structure that does not depend on the weight (masters stay compatible).
Mirrors site2/stroke.js: weight scaling about the mid axis, flat cuts at 0 / 700, mitred corners."""
import math
R = math.pi / 180
CUT_TOL = 0.75 * 98


def centreline(st):
    """design-space samples [(x, y, heading_in, heading_out, kind)] with a fixed count per segment"""
    x, y, h = st["x"], st["y"], st["h"]
    P = [[x, y, h, h, "end"]]
    for g in st["segs"]:
        if g["t"] == "C":
            h += g["ang"]; P[-1][3] = h; P[-1][4] = "corner"; continue
        if g["t"] == "L":
            if abs(g["len"]) < 1e-6: continue
            x += g["len"] * math.cos(h * R); y += g["len"] * math.sin(h * R)
            P.append([x, y, h, h, "pt"])
        else:
            sg = 1 if g["ang"] > 0 else -1; r = g["r"]
            cx = x + r * math.cos((h + 90 * sg) * R); cy = y + r * math.sin((h + 90 * sg) * R)
            a0 = math.atan2(y - cy, x - cx)
            n = max(2, int(math.ceil(abs(g["ang"]) / 9)))
            for i in range(1, n + 1):
                a = a0 + g["ang"] * R * i / n
                hh = h + g["ang"] * i / n
                P.append([cx + r * math.cos(a), cy + r * math.sin(a), hh, hh, "pt"])
            x, y = P[-1][0], P[-1][1]; h += g["ang"]
    P[-1][4] = "end"
    # merge duplicate consecutive points (zero-length lines between a corner and an arc)
    Q = [P[0]]
    for p in P[1:]:
        if math.hypot(p[0] - Q[-1][0], p[1] - Q[-1][1]) < 1e-6:
            Q[-1][3] = p[3]
            if p[4] == "corner": Q[-1][4] = "corner"
        else: Q.append(p)
    return Q


def trim(P, s, e):
    if s <= 0.0005 and e >= 0.9995: return P
    L = [0.0]
    for a, b in zip(P, P[1:]): L.append(L[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    T = L[-1]; s *= T; e *= T
    out = []
    for i in range(len(P) - 1):
        a, b = P[i], P[i + 1]
        for t0 in (s, e):
            if L[i] <= t0 <= L[i + 1] and L[i + 1] > L[i]:
                u = (t0 - L[i]) / (L[i + 1] - L[i])
                out.append([a[0] + u * (b[0] - a[0]), a[1] + u * (b[1] - a[1]), b[2], b[2], "end", t0])
        if s < L[i] < e: out.append(a + [L[i]])
    if s < L[-1] <= e: out.append(P[-1] + [L[-1]])
    out.sort(key=lambda p: p[-1])
    out = [p[:5] for p in out]
    out[0][4] = out[-1][4] = "end"
    return out


def cut_decision(p, h_out, back):
    """does this free end run past the baseline (0) or the top (700)?  decided in design space"""
    hh = h_out + (180 if back else 0)
    sy = math.sin(hh * R)
    if abs(sy) < 0.2: return None
    if sy < 0 and p[1] <= CUT_TOL: return 0.0
    if sy > 0 and p[1] >= 700 - CUT_TOL: return 700.0
    return None


def stroke_polygon(st, W, k, tf):
    """tf(x, y) -> (x, y) final transform (width, slant). Returns a clockwise polygon [(x, y)]."""
    P = trim(centreline(st), st.get("s", 0), st.get("e", 1))
    c0 = cut_decision(P[0], P[0][3], True) if st.get("cap0", "auto") == "auto" else None
    c1 = cut_decision(P[-1], P[-1][2], False) if st.get("cap1", "auto") == "auto" else None
    # weight scaling about the mid axis
    C = [(p[0] * k, 350 + (p[1] - 350) * k) for p in P]
    hw = W / 2
    left, right = [], []
    n = len(P)
    for i, p in enumerate(P):
        hin, hout = p[2], p[3]
        if i == 0: hin = hout
        if i == n - 1: hout = hin
        x, y = C[i]
        if abs(((hout - hin) + 180) % 360 - 180) < 1e-6:
            nx, ny = -math.sin(hin * R), math.cos(hin * R)
            left.append((x + nx * hw, y + ny * hw)); right.append((x - nx * hw, y - ny * hw))
        else:   # mitre: offset lines meet; length clamped
            a = ((hout - hin) + 180) % 360 - 180
            bis = (hin + a / 2) * R
            m = hw / max(0.25, math.cos(a / 2 * R))
            nx, ny = -math.sin(bis), math.cos(bis)
            left.append((x + nx * m, y + ny * m)); right.append((x - nx * m, y - ny * m))
    # flat cuts: move each edge's end point along the edge to the cut line
    def cut(edge_pts, end_idx, nb_idx, lim, h):
        (x0, y0), (x1, y1) = edge_pts[nb_idx], edge_pts[end_idx]
        dx, dy = math.cos(h * R), math.sin(h * R)
        if abs(dy) < 1e-6: return
        t = (lim - y1) / dy
        edge_pts[end_idx] = (x1 + t * dx, lim)
    if c1 is not None:
        cut(left, -1, -2, c1, P[-1][2]); cut(right, -1, -2, c1, P[-1][2])
    if c0 is not None:
        cut(left, 0, 1, c0, P[0][3]); cut(right, 0, 1, c0, P[0][3])
    poly = left + right[::-1]
    return [tf(x, y) for x, y in poly]


def round_cap_polygon(st, W, k, tf, steps=6):
    """Rounded style: free ends get semicircular caps (cuts at 0 / 700 stay flat)"""
    P = trim(centreline(st), st.get("s", 0), st.get("e", 1))
    base = stroke_polygon(st, W, k, lambda x, y: (x, y))
    n = len(P); hw = W / 2
    c0 = cut_decision(P[0], P[0][3], True) if st.get("cap0", "auto") == "auto" else None
    c1 = cut_decision(P[-1], P[-1][2], False) if st.get("cap1", "auto") == "auto" else None
    left, right = base[:n], base[n:][::-1]
    def cap(p, h, flat):
        x, y = p[0] * k, 350 + (p[1] - 350) * k
        if flat: return [None] * (steps - 1)
        return [(x + hw * math.cos((h + 90 - 180 * j / steps) * R), y + hw * math.sin((h + 90 - 180 * j / steps) * R)) for j in range(1, steps)]
    end_cap = cap(P[-1], P[-1][2], c1 is not None)
    start_cap = cap(P[0], P[0][3] + 180, c0 is not None)
    # keep the point count constant: flat caps repeat the midpoint of the cut
    if end_cap[0] is None:
        m = ((left[-1][0] + right[-1][0]) / 2, (left[-1][1] + right[-1][1]) / 2); end_cap = [m] * (steps - 1)
    if start_cap[0] is None:
        m = ((left[0][0] + right[0][0]) / 2, (left[0][1] + right[0][1]) / 2); start_cap = [m] * (steps - 1)
    poly = left + end_cap + right[::-1] + start_cap
    return [tf(x, y) for x, y in poly]
