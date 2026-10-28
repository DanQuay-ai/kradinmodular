"""two masters -> KoradinEyes-Thin.otf / -Black.otf (PUA codepoints of the radicals, as in the live font)"""
import json, sys
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.t2CharStringPen import T2CharStringPen
from shapely.geometry import Polygon
R = json.load(open(sys.argv[1])); D = json.load(open(sys.argv[2])); out = sys.argv[3]
for W, name in ((str(min(map(int, R))), "Thin"), (str(max(map(int, R))), "Black")):
    fb = FontBuilder(1000, isTTF=False); order = [".notdef", "space"]; cs = {}; mt = {}; cmap = {32: "space"}
    for n, adv in ((".notdef", 500), ("space", 300 if name == "Thin" else 340)): p = T2CharStringPen(adv, None); cs[n] = p.getCharString(); mt[n] = (adv, 0)
    sb = 50 if name == "Thin" else 60
    for k in D["keys"]:
        polys = R[W][k]; xs = [x for p in polys for x, y in p[0]]
        if not xs: continue
        x0, x1 = min(xs), max(xs); adv = int(round(x1 - x0 + 2 * sb)); gn = "uni%04X" % D["pua"][k]
        pen = T2CharStringPen(adv, None)
        for p in polys:
            P = Polygon(p[0], p[1:]).simplify(0.6)
            for ring in [P.exterior] + list(P.interiors):
                r = list(ring.coords)[:-1]
                if len(r) < 3: continue
                pen.moveTo((round(r[0][0] - x0 + sb), round(r[0][1])))
                for x, y in r[1:]: pen.lineTo((round(x - x0 + sb), round(y)))
                pen.closePath()
        cs[gn] = pen.getCharString(); mt[gn] = (adv, 0); order.append(gn); cmap[D["pua"][k]] = gn
    fb.setupGlyphOrder(order); fb.setupCharacterMap(cmap)
    fb.setupCFF("KoradinEyes-" + name, {"FullName": "Koradin Eyes " + name}, cs, {})
    fb.setupHorizontalMetrics(mt); fb.setupHorizontalHeader(ascent=900, descent=-250)
    fb.setupNameTable({"familyName": "Koradin Eyes", "styleName": name}); fb.setupOS2(sTypoAscender=900, sTypoDescender=-250, usWinAscent=950, usWinDescent=250); fb.setupPost()
    fb.save(f"{out}/KoradinEyes-{name}.otf"); print(name, len(order) - 2, "glyphs")
