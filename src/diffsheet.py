"""Diff sheet: reference ink vs rebuild. black = both, red = missing from the rebuild, blue = rebuild outside the ink."""
import sys, json, numpy as np, freetype
sys.path.insert(0, '/home/claude/work/gen')
from autotrace import render, outline_polys
from PIL import Image, ImageDraw
from fontTools.ttLib import TTFont
font, data, out = sys.argv[1:4]
d = json.load(open(data)); tt = TTFont(font); upm = tt['head'].unitsPerEm
from fontTools.pens.boundsPen import BoundsPen
gs = tt.getGlyphSet(); cm = tt.getBestCmap()
cap = getattr(tt['OS/2'], 'sCapHeight', 0) or (lambda b: (gs[cm[ord('H')]].draw(b), b.bounds[3])[1])(BoundsPen(gs))
k = 700 / cap; face = freetype.Face(font); face.set_char_size(int(upm * k * 64))
W = d['metrics']['W']; tiles = []
import autotrace; m = d['metrics']; autotrace.CUTS[:] = [m['desc'], 0, m['x'], 700, m['asc']]
for key, g in d['glyphs'].items():
    if len(key) != 1: continue
    try: r = render(face, key, k, pad=30)
    except Exception: continue
    if r is None: continue
    ink, left, top, adv = r
    im = Image.new('L', (ink.shape[1], ink.shape[0]), 0); dr = ImageDraw.Draw(im)
    for st in g['strokes']:
        for poly in outline_polys(st, W): dr.polygon([(x - left, top - y) for x, y in poly], fill=255)
    rb = np.array(im) > 127
    rgb = np.full(ink.shape + (3,), 255, np.uint8)
    rgb[ink & rb] = (20, 20, 20); rgb[ink & ~rb] = (230, 60, 50); rgb[rb & ~ink] = (60, 120, 230)
    t = Image.fromarray(rgb); t.thumbnail((150, 150)); tiles.append(t)
cols = 12; rows = (len(tiles) + cols - 1) // cols
S = Image.new('RGB', (cols * 155, rows * 155), 'white')
for i, t in enumerate(tiles): S.paste(t, ((i % cols) * 155, (i // cols) * 155))
S.save(out)
