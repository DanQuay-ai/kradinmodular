"""Topology check, Thin vs heavy: same parts (nothing merges, nothing breaks), same number of counters."""
import json, sys, numpy as np, engine
from shapely.geometry import Point, Polygon
from shapely.ops import unary_union
from shapely.strtree import STRtree

def comp_labels(geom, pts, tol):
    G = engine.polys(geom); lab = []
    for x, y in pts:
        p = Point(x, y); best, bd = -1, tol
        for i, g in enumerate(G):
            d = g.distance(p)
            if d < bd: best, bd = i, d
            if d == 0: break
        lab.append(best)
    return np.array(lab), G

def check(k, D, W="150", P=None):
    thin = D["G"][k]["40"]; heavy = D["G"][k][W]
    g, dbg = engine.build(heavy, thin, float(W), 40., key=k, **(P or engine.PRESETS[int(W)]))
    S0, _, sid = engine.samples(thin, thin)
    tink = unary_union([Polygon(s["poly"]).buffer(0) for s in thin])
    lt, Gt = comp_labels(tink, S0, 25); lh, Gh = comp_labels(g, dbg["S"], 90)
    issues = []
    for c in set(lh) - {-1}:
        ts = set(lt[lh == c]) - {-1}
        if len(ts) > 1 and engine.EXCEPT.get(k) != "rings": issues.append(f"merge {sorted(ts)}")
    for c in set(lt) - {-1}:
        hs = set(lh[lt == c]) - {-1}
        if len(hs) > 1: issues.append(f"break t{c}->{len(hs)}")
    ht = sum(len(p.interiors) for p in Gt); hh = sum(len(p.interiors) for p in Gh)
    if hh < ht: issues.append(f"counters {ht}->{hh}")
    return issues, g

if __name__ == "__main__":
    D = json.load(open("/tmp/claude-0/rad2.json")); bad = 0
    ks = sys.argv[1].split(",") if len(sys.argv) > 1 else D["keys"]
    for k in ks:
        iss, _ = check(k, D)
        if iss: bad += 1; print(k, "; ".join(iss))
    print("glyphs with issues:", bad, "/", len(ks))
