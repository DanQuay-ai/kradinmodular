"""owner's marks applied locally, after the engine (output coordinates):
- rot: 180-degree turn symmetry (keep the left half, turn it onto the right), both masters
- fill: an ink trap inside the mark is filled (closing, only inside the mark)
- open: the narrow negative inside the mark is opened to the full gap
- smooth: a bump inside the mark is opened away"""
import json, sys, numpy as np
from shapely.geometry import Polygon, Point, box
from shapely.ops import unary_union
from shapely import affinity
R = json.load(open(sys.argv[1])); F = json.load(open(sys.argv[2])); BH = 910.0
def geom(ps): return unary_union([Polygon(p[0], p[1:]).buffer(0) for p in ps])
def polys(g): return [] if g.is_empty else [p for p in (g.geoms if hasattr(g, "geoms") else [g]) if p.geom_type == "Polygon"]
def sig(g): P = [p for p in polys(g) if p.area > 50]; return (len(P), sum(1 for p in P for r in p.interiors if Polygon(r).area > 50))
def out(g): return [[np.round(np.array(p.exterior.coords), 1).tolist()] + [np.round(np.array(r.coords), 1).tolist() for r in p.interiors] for p in polys(g)]
def ell(m, grow=1.0): return affinity.scale(Point(m["cx"], BH - m["cy"]).buffer(1, quad_segs=24), m["rx"] * grow, m["ry"] * grow)
def rot_ok(k):
    for W in R:
        g = geom(R[W][k]); b = g.bounds; c = ((b[0] + b[2]) / 2, (b[1] + b[3]) / 2)
        if not any(sig(unary_union([h, affinity.rotate(h, 180, origin=c)]).buffer(0.01).buffer(-0.01)) == sig(g)
                   for h in (g.intersection(box(b[0] - 9, b[1] - 9, c[0], b[3] + 9)), g.intersection(box(c[0], b[1] - 9, b[2] + 9, b[3] + 9)))): return False
    return True
for k, spec in F.items():
    if spec.get("rot") and not rot_ok(k): print(k, "rot skipped: not possible on both masters"); spec["rot"] = 0
    for W in R:
        g = geom(R[W][k]); ref = sig(g)
        if spec.get("rot"):
            b = g.bounds; c = ((b[0] + b[2]) / 2, (b[1] + b[3]) / 2); best = None
            for side in (0, 1):
                half = g.intersection(box(b[0] - 9, b[1] - 9, c[0], b[3] + 9) if side == 0 else box(c[0], b[1] - 9, b[2] + 9, b[3] + 9))
                h = unary_union([half, affinity.rotate(half, 180, origin=c)]).buffer(0.01).buffer(-0.01)
                if sig(h) == ref and (best is None or h.area > best.area): best = h
            if best is not None: g = best
            else: print(k, W, "rot kept as is")
        if W == "140":
            for m in spec.get("marks", []):
                E = ell(m); r = 0.5 * float(W)
                if m["op"] == "fill":
                    add = g.buffer(r, quad_segs=12).buffer(-r, quad_segs=12).difference(g).intersection(E)
                    h = g.union(add).buffer(0)
                elif m["op"] == "open":
                    neg = E.difference(g); gapw = 52 * 0.82
                    h = g.difference(neg.buffer(gapw / 2, quad_segs=8).intersection(E)).buffer(0)
                    h = h.buffer(-6).buffer(6)
                else:
                    o = 0.3 * float(W); h = g.difference(E).union(g.buffer(-o, quad_segs=12).buffer(o, quad_segs=12).intersection(E)).buffer(0)
                if sig(h) == ref: g = h
                else: print(k, m["op"], "refused (would change parts or counters)")
        R[W][k] = out(g)
json.dump(R, open(sys.argv[3], "w"))
