import json, sys
from PIL import Image, ImageDraw
R = json.load(open(sys.argv[1])); K = json.load(open(sys.argv[3] if len(sys.argv) > 3 else "/tmp/claude-0/rad2.json"))["keys"]
WS = sorted(R, key=float); cols, cell = 9, 190; rows = (len(K) + cols - 1) // cols
bg, cr = (92, 58, 33), (250, 243, 228)
im = Image.new("RGB", (cols * cell * len(WS) + 20 * (len(WS) + 1), rows * cell + 50), bg); d = ImageDraw.Draw(im)
for m, W in enumerate(WS):
    for i, k in enumerate(K):
        ox = 20 + m * (cols * cell + 20) + (i % cols) * cell; oy = 40 + (i // cols) * cell; s = cell / 1000 * 0.95 * 1.1
        xs = [x for p in R[W][k] for x, y in p[0]]; x0 = (min(xs) + max(xs)) / 2 if xs else 300
        tf = lambda x, y: (ox + cell / 2 + (x - x0) * s * 0.85, oy + cell - 22 - y * s * 0.85 * 0.95)
        for p in R[W][k]:
            d.polygon([tf(*q) for q in p[0]], fill=cr)
            for r in p[1:]: d.polygon([tf(*q) for q in r], fill=bg)
    d.text((20 + m * (cols * cell + 20), 12), f"W {W}", fill=cr)
im.save(sys.argv[2])
