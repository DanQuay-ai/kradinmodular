import json, sys, engine
from PIL import Image, ImageDraw
D = json.load(open("/tmp/claude-0/rad4.json")); k = sys.argv[1]; W = sys.argv[2] if len(sys.argv) > 2 else "140"
P = engine.PRESETS[int(W)]
g, dbg = engine.build(D["G"][k][W], D["G"][k]["40"], float(W), 40., key=k, **P)
im = Image.new("RGB", (900, 900), (255, 255, 255)); d = ImageDraw.Draw(im); s = 0.95
tf = lambda x, y: (100 + x * s, 830 - y * s)
for p in engine.polys(dbg["raw"]): d.polygon([tf(*q) for q in p.exterior.coords], fill=(230, 200, 170))
for p in engine.polys(g):
    d.line([tf(*q) for q in p.exterior.coords], fill=(0, 0, 0), width=2)
    for r in p.interiors: d.line([tf(*q) for q in r.coords], fill=(0, 0, 0), width=2)
if dbg["cut"] is not None:
    for p in engine.polys(dbg["cut"]): d.line([tf(*q) for q in p.exterior.coords], fill=(255, 0, 0), width=1)
for x, y in dbg["S"]: d.point(tf(x, y), fill=(0, 0, 255))
im.save("/tmp/claude-0/dbg.png")
# spines + final polygons coloured
im2 = Image.new("RGB", (900, 900), (255, 255, 255)); d2 = ImageDraw.Draw(im2)
cols = [(200, 80, 80), (80, 160, 80), (80, 80, 200), (200, 160, 40)]
for i, p in enumerate(engine.polys(g)):
    d2.polygon([tf(*q) for q in p.exterior.coords], fill=cols[i % 4])
    for r in p.interiors: d2.polygon([tf(*q) for q in r.coords], fill=(255, 255, 255))
for x, y in dbg["S"]: d2.point(tf(x, y), fill=(0, 0, 0))
im2.save("/tmp/claude-0/dbg2.png")
