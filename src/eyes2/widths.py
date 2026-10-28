"""stroke width consistency on the Black master: at every skeleton sample, local width = 2 x distance to the
outline. Reports the share of the skeleton thinner than 80 % of the weight, per glyph."""
import json, sys, numpy as np, engine
from shapely import distance, points
D = json.load(open(sys.argv[1] if len(sys.argv) > 1 else "/tmp/claude-0/rad3.json")); W = 140.0
rows = []
for k in D["keys"]:
    g, dbg = engine.build(D["G"][k]["140"], D["G"][k]["40"], W, 40., key=k, **engine.PRESETS[140])
    from shapely.geometry import LineString
    S = []
    for l in dbg["skel"]:
        L = LineString(l); n = int(L.length / 6)
        for i in range(n + 1):
            t = i * 6.0
            if 0.7 * W < t < L.length - 0.7 * W: S.append(L.interpolate(t).coords[0])
    if not S: continue
    S = np.array(S); b = g.boundary; pts = points(S)
    inside = np.array([g.contains(p) for p in pts]); d = distance(pts, b) * 2
    d = d[inside]
    if not len(d): continue
    thin = (d < 0.8 * W).mean(); rows.append((thin, k, np.percentile(d, 5) / W))
rows.sort(reverse=True)
for t, k, p5 in rows[:20]: print(f"{k:4s} thin share {t:5.2f}  5th pct width {p5:4.2f} W")
print("glyphs with more than 10% thin skeleton:", sum(1 for t, _, _ in rows if t > 0.10), "/", len(rows))
