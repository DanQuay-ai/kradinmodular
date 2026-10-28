"""Anatomy of every Kɔradin radical, read on the Thin master: parts, terminals, junctions, counters.
Output: anatomy.json + an annotated sheet. The Black pass reads it (part roles decide what may move, retract,
thin or be cut)."""
import json, math, sys
import numpy as np
from shapely.geometry import Polygon, LineString, Point
from shapely.ops import unary_union

R = math.pi / 180
def K(W): return (700 - W) / 602

def trace(st, W):
    """turtle -> list of (segment index, type, polyline) in the W body"""
    k = K(W); x, y, h = st["x"], st["y"], st["h"]; out = []
    for i, g in enumerate(st["segs"]):
        P = [(x, y)]
        if g["t"] == "C": h += g["ang"]; continue
        if g["t"] == "L":
            x += g["len"] * math.cos(h * R); y += g["len"] * math.sin(h * R); P.append((x, y))
        else:
            sg = 1 if g["ang"] > 0 else -1; r = max(1, g["r"])
            cx, cy = x + r * math.cos((h + 90 * sg) * R), y + r * math.sin((h + 90 * sg) * R)
            a0 = math.atan2(y - cy, x - cx); n = max(2, int(abs(g["ang"]) / 6))
            for j in range(1, n + 1):
                a = a0 + g["ang"] * R * j / n; P.append((cx + r * math.cos(a), cy + r * math.sin(a)))
            x, y = P[-1]; h += g["ang"]
        out.append((i, g, [(px * k, 350 + (py - 350) * k) for px, py in P], h))
    return out

def seg_type(g, P, h_end):
    if g["t"] == "L":
        hh = math.atan2(P[-1][1] - P[0][1], P[-1][0] - P[0][0])
        if abs(math.sin(hh)) > 0.92: return "stem"
        if abs(math.cos(hh)) > 0.92: return "bar"
        return "diagonal"
    return "curve"

def analyse(k, thin, T, W=40.0):
    ink = unary_union([Polygon(s["poly"]).buffer(0) for s in thin if len(s["poly"]) >= 3])
    parts, terminals, junctions, counters = [], [], [], []
    lines = []
    for si, st in enumerate(T[k]):
        tr = trace(st, W)
        if not tr: continue
        turn = sum(g["ang"] for _, g, _, _ in tr if g["t"] == "A")
        pts = [p for _, _, P, _ in tr for p in P]
        closed = math.hypot(pts[0][0] - pts[-1][0], pts[0][1] - pts[-1][1]) < W
        role = "ring" if closed and abs(turn) >= 300 else "spiral" if abs(turn) >= 400 else None
        # bowls: runs of arcs (with lines between) turning >= 150 the same way
        acc, run = 0.0, []
        for i, g, P, h in tr:
            t = seg_type(g, P, h)
            if g["t"] == "A":
                if acc * g["ang"] < 0: acc, run = 0.0, []
                acc += g["ang"]; run.append(len(parts))
            parts.append(dict(stroke=si, seg=i, type=t, pts=[[round(a, 1), round(b, 1)] for a, b in P]))
            if g["t"] == "A" and abs(acc) >= 150:
                for j in run: parts[j]["type"] = "bowl"
                for j in range(run[0], len(parts)):
                    if parts[j]["type"] in ("stem", "bar", "diagonal") and j > run[0]: parts[j]["in_bowl"] = True
                acc, run = 0.0, []
        if role:
            for p in parts:
                if p["stroke"] == si: p["role"] = role
        lines.append((si, LineString(pts)))
        for end, p in (("start", pts[0]), ("end", pts[-1])):
            if closed: continue
            kind = "foot" if p[1] < W * 1.3 else "head" if p[1] > 700 - W * 1.3 else "terminal"
            terminals.append(dict(stroke=si, end=end, at=[round(p[0], 1), round(p[1], 1)], kind=kind))
    # junctions: where two strokes' inks meet
    for a in range(len(lines)):
        for b in range(a + 1, len(lines)):
            la, lb = lines[a][1], lines[b][1]
            if la.distance(lb) > W * 0.9: continue
            ends_a = [Point(la.coords[0]), Point(la.coords[-1])]; ends_b = [Point(lb.coords[0]), Point(lb.coords[-1])]
            ea = [e for e in ends_a if e.distance(lb) < W * 0.9]; eb = [e for e in ends_b if e.distance(la) < W * 0.9]
            if ea and eb and min(x.distance(y) for x in ea for y in eb) < W * 1.2: kind, at = "L", ea[0]
            elif ea: kind, at = "T", ea[0]
            elif eb: kind, at = "T", eb[0]
            else:
                x = la.intersection(lb); kind, at = "X", (x.centroid if not x.is_empty else la.interpolate(la.project(lb.centroid)))
            junctions.append(dict(a=lines[a][0], b=lines[b][0], kind=kind, at=[round(at.x, 1), round(at.y, 1)]))
            for t in terminals:
                if t["stroke"] in (lines[a][0], lines[b][0]) and Point(t["at"]).distance(at) < W * 1.5 and kind in ("T", "L"): t["kind"] = "joint"
    # counters
    hull = ink.convex_hull
    for p in ([ink] if ink.geom_type == "Polygon" else list(ink.geoms)):
        for r in p.interiors:
            H = Polygon(r)
            if H.area < 50: continue
            mrr = H.minimum_rotated_rectangle; xy = np.array(mrr.exterior.coords)[:4]
            L1, L2 = np.hypot(*(xy[1] - xy[0])), np.hypot(*(xy[2] - xy[1]))
            kind = "eye" if min(L1, L2) < 140 else "counter"
            counters.append(dict(kind=kind, area=round(H.area), size=[round(max(L1, L2)), round(min(L1, L2))], ring=[[round(a, 1), round(b, 1)] for a, b in H.exterior.coords]))
    for q in (lambda g: [g] if g.geom_type == "Polygon" else list(g.geoms))(hull.difference(ink.buffer(1))):
        if q.area < 2500: continue
        mouth = q.exterior.intersection(hull.exterior.buffer(1.5)).length
        if mouth < 0.6 * math.sqrt(q.area): counters.append(dict(kind="aperture", area=round(q.area), mouth=round(mouth), ring=[[round(a, 1), round(b, 1)] for a, b in q.exterior.coords]))
    return dict(parts=parts, terminals=terminals, junctions=junctions, counters=counters)

COL = {"stem": (0, 122, 255), "bar": (52, 199, 89), "diagonal": (175, 82, 222), "curve": (255, 149, 0), "bowl": (255, 45, 85),
       "spiral": (90, 200, 250), "ring": (255, 204, 0)}
CNT = {"counter": (255, 220, 225), "eye": (200, 235, 255), "aperture": (235, 235, 235)}
JC = {"T": (0, 0, 0), "L": (120, 120, 120), "X": (255, 59, 48)}

def sheet(A, D, out, cols=9, cell=230):
    from PIL import Image, ImageDraw
    K_ = D["keys"]; rows = (len(K_) + cols - 1) // cols
    im = Image.new("RGB", (cols * cell + 20, rows * cell + 150), "white"); d = ImageDraw.Draw(im)
    for i, k in enumerate(K_):
        a = A[k]; ox, oy = 10 + (i % cols) * cell, 60 + (i // cols) * cell; s = cell / 1000 * 1.0
        xs = [x for p in a["parts"] for x, y in p["pts"]]; x0 = (min(xs) + max(xs)) / 2
        tf = lambda x, y: (ox + cell / 2 + (x - x0) * s * 0.9, oy + cell - 28 - y * s * 0.9 * 0.95)
        for c in a["counters"]: d.polygon([tf(*q) for q in c["ring"]], fill=CNT[c["kind"]])
        for st in D["G"][k]["40"]: d.polygon([tf(*q) for q in st["poly"]], fill=(60, 60, 60))
        for p in a["parts"]:
            col = COL.get(p.get("role")) or COL[p["type"]]
            d.line([tf(*q) for q in p["pts"]], fill=col, width=4)
        for t in a["terminals"]:
            x, y = tf(*t["at"]); r = 4
            if t["kind"] == "terminal": d.ellipse([x - r, y - r, x + r, y + r], outline=(255, 59, 48), width=2)
            elif t["kind"] in ("foot", "head"): d.rectangle([x - r, y - r, x + r, y + r], outline=(0, 0, 0), width=2)
        for j in a["junctions"]:
            x, y = tf(*j["at"]); d.ellipse([x - 4, y - 4, x + 4, y + 4], fill=JC[j["kind"]])
        d.text((ox + 4, oy + 2), k, fill=(0, 0, 0))
    y = rows * cell + 70; x = 14
    for n, c in list(COL.items()) + [("closed counter", CNT["counter"]), ("eye", CNT["eye"]), ("aperture", CNT["aperture"])]:
        d.rectangle([x, y, x + 18, y + 12], fill=c); d.text((x + 24, y), n, fill=(0, 0, 0)); x += 130
    y += 30; x = 14
    for n, c in JC.items(): d.ellipse([x, y, x + 10, y + 10], fill=c); d.text((x + 16, y - 1), n + "-junction", fill=(0, 0, 0)); x += 130
    d.ellipse([x, y, x + 10, y + 10], outline=(255, 59, 48), width=2); d.text((x + 16, y - 1), "free terminal", fill=(0, 0, 0)); x += 130
    d.rectangle([x, y, x + 10, y + 10], outline=(0, 0, 0), width=2); d.text((x + 16, y - 1), "foot / head (cut on a body line)", fill=(0, 0, 0))
    d.text((14, 14), "Kɔradin radicals: anatomy read on the Thin master", fill=(0, 0, 0))
    im.save(out)

if __name__ == "__main__":
    D = json.load(open(sys.argv[1]))
    A = {k: analyse(k, D["G"][k]["40"], D["T"]) for k in D["keys"]}
    json.dump(A, open(sys.argv[2], "w"))
    sheet(A, D, sys.argv[3])
    from collections import Counter
    print("parts", Counter(p.get("role") or p["type"] for a in A.values() for p in a["parts"]))
    print("terminals", Counter(t["kind"] for a in A.values() for t in a["terminals"]))
    print("junctions", Counter(j["kind"] for a in A.values() for j in a["junctions"]))
    print("counters", Counter(c["kind"] for a in A.values() for c in a["counters"]))
