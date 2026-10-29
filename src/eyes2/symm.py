"""exact mirror symmetry for the glyphs that are meant to be symmetric: keep one half (the one that keeps every
part and counter) and mirror it about the best axis; done on both masters"""
import json, sys, numpy as np
from shapely.geometry import Polygon, box
from shapely.ops import unary_union
from shapely import affinity
SYM = "do ri ru rɔ rɛ so tu u pu ro su ku de fo te tɛ fu re ka pa".split()
def geom(ps): return unary_union([Polygon(p[0], p[1:]).buffer(0) for p in ps])
def polys(g): return [] if g.is_empty else [p for p in (g.geoms if hasattr(g, "geoms") else [g]) if p.geom_type == "Polygon"]
def axis(g):
    b = g.bounds; best = (9, (b[0] + b[2]) / 2)
    for c in np.linspace(b[0] + 0.35 * (b[2] - b[0]), b[2] - 0.35 * (b[2] - b[0]), 81):
        d = g.symmetric_difference(affinity.scale(g, -1, 1, origin=(c, 0))).area / g.area
        if d < best[0]: best = (d, c)
    return best[1]
def sig(g): return (len(polys(g)), sum(len(p.interiors) for p in polys(g)))
def mirror_half(g, c, side):
    b = g.bounds; half = g.intersection(box(b[0] - 10, b[1] - 10, c, b[3] + 10) if side == 0 else box(c, b[1] - 10, b[2] + 10, b[3] + 10))
    return unary_union([half, affinity.scale(half, -1, 1, origin=(c, 0))]).buffer(0.01).buffer(-0.01)
def main():
    R = json.load(open(sys.argv[1]))
    for k in SYM:
        Ws = sorted(R, key=float); G = {W: geom(R[W][k]) for W in Ws}
        for side in (0, 1):
            out = {W: mirror_half(G[W], axis(G[W]), side) for W in Ws}
            if len({sig(out[W]) for W in Ws}) == 1 and sig(out[Ws[-1]]) == sig(G[Ws[-1]]) and all(out[W].area > 0.8 * G[W].area for W in Ws): break   # both masters agree, Black keeps its parts and counters
        else:
            print(k, "kept as is (no half keeps every part and counter)"); continue
        for W in Ws: R[W][k] = [[np.round(np.array(p.exterior.coords), 1).tolist()] + [np.round(np.array(r.coords), 1).tolist() for r in p.interiors] for p in polys(out[W])]
    json.dump(R, open(sys.argv[2], "w"))

if __name__ == "__main__": main()
