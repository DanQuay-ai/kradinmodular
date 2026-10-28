import json, sys, numpy as np, engine
from shapely.geometry import LineString, Point
from PIL import Image, ImageDraw
D = json.load(open("/tmp/claude-0/rad3.json")); ks = sys.argv[1].split(","); W = 140.0; cell = 600
im = Image.new("RGB", (cell * len(ks), cell), "white"); d = ImageDraw.Draw(im)
for n, k in enumerate(ks):
    g, dbg = engine.build(D["G"][k]["140"], D["G"][k]["40"], W, 40., key=k, **engine.PRESETS[140])
    xs = [x for p in engine.polys(g) for x, y in p.exterior.coords]; x0 = min(xs); s = cell / 1250
    tf = lambda x, y: (n * cell + 20 + (x - x0) * s, cell - 60 - y * s)
    for p in engine.polys(g):
        d.polygon([tf(*q) for q in p.exterior.coords], fill=(225, 225, 225))
        for r in p.interiors: d.polygon([tf(*q) for q in r.coords], fill=(255, 255, 255))
    b = g.boundary
    for l in dbg["skel"]:
        L = LineString(l)
        for i in range(int(L.length / 6)):
            q = L.interpolate(i * 6.0); w = 2 * b.distance(q) / W if g.contains(q) else 0
            c = (220, 0, 0) if w < 0.8 else (0, 160, 0)
            x, y = tf(q.x, q.y); d.ellipse([x - 2, y - 2, x + 2, y + 2], fill=c)
    d.text((n * cell + 8, 8), k, fill=(0, 0, 0))
im.save("/tmp/claude-0/wdbg.png")
