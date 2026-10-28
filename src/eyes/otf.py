import json, sys
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.t2CharStringPen import T2CharStringPen
R = json.load(open(sys.argv[1])); D = json.load(open("/tmp/claude-0/rad.json"))
for W, name in (("40", "Thin"), ("115", "Black")):
    fb = FontBuilder(1000, isTTF=False); order = [".notdef", "space"]; cs = {}; mt = {}; cmap = {32: "space"}
    for n, adv in ((".notdef", 500), ("space", 300)): p = T2CharStringPen(adv, None); cs[n] = p.getCharString(); mt[n] = (adv, 0)
    for k in D["keys"]:
        polys = R[W][k]; xs = [x for p in polys for x, y in p[0]]
        if not xs: continue
        x0, x1 = min(xs), max(xs); sb = 50; adv = int(x1 - x0 + 2 * sb); n = "rad_" + str(D["pua"][k])
        pen = T2CharStringPen(adv, None)
        for p in polys:
            for r in p:
                r = r[:-1] if r[0] == r[-1] else r
                pen.moveTo((round(r[0][0] - x0 + sb), round(r[0][1])))
                for x, y in r[1:]: pen.lineTo((round(x - x0 + sb), round(y)))
                pen.closePath()
        cs[n] = pen.getCharString(); mt[n] = (adv, 0); order.append(n); cmap[D["pua"][k]] = n
    fb.setupGlyphOrder(order); fb.setupCharacterMap(cmap)
    fb.setupCFF("KoradinEyes-" + name, {"FullName": "Koradin Eyes " + name}, cs, {})
    fb.setupHorizontalMetrics(mt); fb.setupHorizontalHeader(ascent=900, descent=-250)
    fb.setupNameTable({"familyName": "Koradin Eyes", "styleName": name}); fb.setupOS2(); fb.setupPost()
    fb.save(f"/home/claude/work/site2/fonts/kradin-eyes/KoradinEyes-{name}.otf"); print(name, len(order))
