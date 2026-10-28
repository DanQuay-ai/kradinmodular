import sys, importlib, core
from PIL import Image, ImageDraw
def draw_shape(d, g, tf, fill):
    if g is None or g.is_empty: return
    for p in (g.geoms if hasattr(g, "geoms") else [g]):
        if p.geom_type != "Polygon": continue
        d.polygon([tf(x, y) for x, y in p.exterior.coords], fill=fill)
        for i in p.interiors: d.polygon([tf(x, y) for x, y in i.coords], fill=(255, 255, 255))
def sheet(G, chars, out, cell=480, cols=4, mode="overlay"):
    rows = (len(chars) + cols - 1) // cols; k = cell / 1100
    im = Image.new("RGB", (cols * cell, rows * cell), "white"); d = ImageDraw.Draw(im)
    for i, ch in enumerate(chars):
        ox, oy = (i % cols) * cell, (i // cols) * cell
        tf = lambda x, y: (ox + 20 + (x + 80) * k, oy + cell - 50 - (y + 230) * k + 230 * k * 0 )
        tf = lambda x, y, ox=ox, oy=oy: (ox + 25 + (x + 60) * k, oy + 30 + (760 - y) * k)
        d.line([tf(-60, 0), tf(900, 0)], fill=(200, 200, 255)); d.line([tf(-60, 516), tf(900, 516)], fill=(220, 220, 255)); d.line([tf(-60, 700), tf(900, 700)], fill=(220, 220, 255))
        r, _ = core.ref_shape(ch)
        strokes = G.get(ch)
        if mode == "overlay":
            draw_shape(d, r, tf, (255, 200, 150))
            if strokes:
                g = core.glyph_shape(strokes)
                if g is not None:
                    for p in (g.geoms if hasattr(g, "geoms") else [g]):
                        d.line([tf(x, y) for x, y in p.exterior.coords], fill=(0, 0, 0), width=2)
                        for it in p.interiors: d.line([tf(x, y) for x, y in it.coords], fill=(0, 0, 160), width=2)
        else:
            if strokes: draw_shape(d, core.glyph_shape(strokes), tf, (0, 0, 0))
        if strokes:
            c, o = core.score(ch, strokes); d.text((ox + 4, oy + 4), f"{ch} {c:.2f}/{o:.2f}", fill=(0, 0, 0))
        else: d.text((ox + 4, oy + 4), ch, fill=(0, 0, 0))
    im.save(out)
if __name__ == "__main__":
    m = importlib.import_module(sys.argv[1]); sheet(m.build(), sys.argv[2], sys.argv[3], mode=(sys.argv[4] if len(sys.argv) > 4 else "overlay"))
