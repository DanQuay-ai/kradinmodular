import json, sys
from PIL import Image, ImageDraw
R = json.load(open(sys.argv[1])); K = json.load(open("/tmp/claude-0/rad.json"))["keys"]
cols, cell = 9, 170; rows = (len(K) + cols - 1) // cols
im = Image.new("RGB", (cols * cell * 2 + 40, rows * cell + 60), (92, 58, 33)); d = ImageDraw.Draw(im); cr = (250, 243, 228)
for m, W in enumerate(["40", "115"]):
    for i, k in enumerate(K):
        ox = 20 + m * (cols * cell + 20) + (i % cols) * cell; oy = 40 + (i // cols) * cell; s = cell / 1000 * 1.05
        xs = [x for p in R[W][k] for x, y in p[0]]; x0 = (min(xs) + max(xs)) / 2 if xs else 300
        tf = lambda x, y: (ox + cell / 2 + (x - x0) * s * 0.9, oy + cell - 25 - y * s * 0.9 * 0.9)
        for p in R[W][k]:
            d.polygon([tf(*q) for q in p[0]], fill=cr)
            for r in p[1:]: d.polygon([tf(*q) for q in r], fill=(92, 58, 33))
        d.text((ox + 4, oy + 2), k, fill=(200, 170, 140))
    d.text((20 + m * (cols * cell + 20), 10), f"master W {W}", fill=cr)
im.save(sys.argv[2])
