import json, sys
from PIL import Image, ImageDraw
R = json.load(open(sys.argv[1])); ks = sys.argv[2].split(",") if sys.argv[2] else list(R[sorted(R)[0]]); WS = sorted(R, key=float)
cell = 560; bg, cr = (92, 58, 33), (250, 243, 228)
im = Image.new("RGB", (cell * len(ks), cell * len(WS)), bg); d = ImageDraw.Draw(im)
for m, W in enumerate(WS):
    for i, k in enumerate(ks):
        ox, oy = i * cell, m * cell; s = cell / 1250
        xs = [x for p in R[W][k] for x, y in p[0]]; x0 = (min(xs) + max(xs)) / 2
        tf = lambda x, y: (ox + cell / 2 + (x - x0) * s, oy + cell - 40 - y * s)
        for p in R[W][k]:
            d.polygon([tf(*q) for q in p[0]], fill=cr)
            for r in p[1:]: d.polygon([tf(*q) for q in r], fill=bg)
        d.text((ox + 6, oy + 6), f"{k} {W}", fill=cr)
im.save(sys.argv[3])
