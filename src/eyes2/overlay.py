"""superposition, Thin: the akrokerri-mod Kɔradin (glyphs.json, stretched to the same body) vs Kɔradin Eyes Thin"""
import json, sys, numpy as np
from shapely.geometry import Polygon, LineString
from shapely.ops import unary_union
from PIL import Image, ImageDraw
R = json.load(open(sys.argv[1])); E = json.load(open(sys.argv[2])); out = sys.argv[3]
keys = R["keys"]; cols, cell = 9, 260; rows = (len(keys) + cols - 1) // cols
im = Image.new("RGB", (cols * cell, rows * cell + 40), "white"); d = ImageDraw.Draw(im); stats = []
for i, k in enumerate(keys):
    ref = unary_union([Polygon(s["poly"]).buffer(0) for s in R["G"][k]["40"]])
    eye = unary_union([Polygon(p[0], p[1:]).buffer(0) for p in E["40"][k]]) if isinstance(E.get("40"), dict) else unary_union([Polygon(s["poly"]).buffer(0) for s in E["G"][k]["40"]])
    iou = ref.intersection(eye).area / ref.union(eye).area; stats.append((round(iou, 3), k))
    ox, oy = (i % cols) * cell, 30 + (i // cols) * cell; s = cell / 1150
    b = ref.union(eye).bounds; x0 = (b[0] + b[2]) / 2
    tf = lambda x, y: (ox + cell / 2 + (x - x0) * s, oy + cell - 25 - y * s)
    for g, col in ((eye, (0, 0, 0)),):
        for p in (g.geoms if hasattr(g, "geoms") else [g]):
            d.polygon([tf(*q) for q in p.exterior.coords], fill=(170, 170, 170))
            for r in p.interiors: d.polygon([tf(*q) for q in r.coords], fill=(255, 255, 255))
    for p in (ref.geoms if hasattr(ref, "geoms") else [ref]):
        d.line([tf(*q) for q in p.exterior.coords], fill=(230, 0, 0), width=2)
        for r in p.interiors: d.line([tf(*q) for q in r.coords], fill=(230, 0, 0), width=2)
    d.text((ox + 4, oy + 2), f"{k} {iou:.2f}", fill=(0, 0, 0))
d.text((6, 6), "red outline: akrokerri mod (glyphs.json, body x1.25)   grey: Kɔradin Eyes Thin", fill=(0, 0, 0))
im.save(out); stats.sort(); print(stats[:25]); print("mean IoU", round(np.mean([s for s, _ in stats]), 3))
