"""Adinkra Alphabet Modular (variable weight) + Adinkra Symbols (from adinkrakit.svg).
python3 -I build_adinkra.py <outdir>"""
import sys, os, math, re
sys.path.insert(0, "/home/claude/work/gen")
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.transformPen import TransformPen
from fontTools.designspaceLib import DesignSpaceDocument, AxisDescriptor, SourceDescriptor
from fontTools import varLib
from fontTools.ttLib import TTFont
from fontTools.feaLib.builder import addOpenTypeFeaturesFromString
from outline import stroke_polygon
from adinkra_glyphs import A, W0
from ks import S

OUT = sys.argv[1]; os.makedirs(OUT, exist_ok=True); TMP = os.path.join(OUT, "_ma"); os.makedirs(TMP, exist_ok=True)
A["comma"] = [S(40, 40, 90, "L60"), S(40, 40, 250, "L100", cap1="butt")]
NAMES = {"ɛ": "eopen", "ɔ": "oopen"}
SB = 60

def gname(k): return NAMES.get(k, k)

def cmap_for(order):
    cm = {32: "space"}
    for k in order:
        n = gname(k)
        if len(k) == 1 and k.isalpha():
            cm[ord(k)] = n; cm[ord(k.upper())] = n
    cm[ord(".")] = "period"; cm[ord(",")] = "comma"; cm[ord("-")] = "hyphen"
    cm[0x025B] = "eopen"; cm[0x0190] = "eopen"; cm[0x0254] = "oopen"; cm[0x0186] = "oopen"
    return cm

def names_table(family, style="Regular"):
    ps = (family + "-" + style).replace(" ", "")
    return {"familyName": family, "styleName": style, "uniqueFontIdentifier": ps + "-2026",
            "fullName": f"{family} {style}", "psName": ps, "version": "Version 1.000",
            "copyright": "Kradin Modular project, 2026"}

def alphabet_master(W):
    k = (700 - W) / (700 - W0)
    order = list(A.keys())
    glyphs = {".notdef": TTGlyphPen(None).glyph(), "space": TTGlyphPen(None).glyph()}
    metrics = {".notdef": (500, 0), "space": (300, 0)}
    for key in order:
        polys = [stroke_polygon(st, W, k, lambda x, y: (x, y)) for st in A[key]]
        xs = [p[0] for poly in polys for p in poly]; x0 = min(xs); x1 = max(xs)
        pen = TTGlyphPen(None)
        for poly in polys:
            pen.moveTo((round(poly[0][0] - x0 + SB), round(poly[0][1])))
            for x, y in poly[1:]: pen.lineTo((round(x - x0 + SB), round(y)))
            pen.closePath()
        g = pen.glyph(); g.flags[0] |= 0x40
        n = gname(key); glyphs[n] = g; metrics[n] = (round(x1 - x0 + 2 * SB), SB)
    gorder = [".notdef", "space"] + [gname(k) for k in order]
    fb = FontBuilder(1000, isTTF=True)
    fb.setupGlyphOrder(gorder); fb.setupCharacterMap(cmap_for(order))
    fb.setupGlyf(glyphs); fb.setupHorizontalMetrics(metrics)
    fb.setupHorizontalHeader(ascent=800, descent=-200)
    fb.setupOS2(sTypoAscender=800, sTypoDescender=-200, usWinAscent=900, usWinDescent=250, sxHeight=700, sCapHeight=700)
    fb.setupNameTable(names_table("Adinkra Alphabet Modular")); fb.setupPost()
    for g in fb.font["glyf"].glyphs.values(): g.recalcBounds(fb.font["glyf"])
    return fb.font

def build_alphabet():
    ds = DesignSpaceDocument()
    a = AxisDescriptor(); a.tag, a.name, a.minimum, a.default, a.maximum = "wght", "Weight", 100, 400, 900
    a.map = [(100, 18.0), (400, 32.25), (900, 56.0)]; ds.addAxis(a)
    for W in (18.0, 32.25, 56.0):
        f = alphabet_master(W); p = os.path.join(TMP, f"ad-{W}.ttf"); f.save(p)
        s = SourceDescriptor(); s.path = p; s.location = {"Weight": W}; ds.addSource(s)
    vf, _, _ = varLib.build(ds, exclude=["STAT"])
    vf.save(os.path.join(OUT, "AdinkraAlphabetModular-VF.ttf"))
    vf.flavor = "woff2"; vf.save(os.path.join(OUT, "AdinkraAlphabetModular-VF.woff2"))
    print("alphabet ok", len(vf.getGlyphOrder()))

# ------------------------------------------------------------------ symbols
TWI = ["a", "b", "d", "e", "ɛ", "f", "g", "h", "i", "k", "l", "m", "n", "o", "ɔ", "p", "r", "s", "t", "u", "w", "y"]
DIG = ["ky", "gy", "hy", "ny", "tw", "dw"]

def build_symbols():
    from fontTools.svgLib.path import parse_path
    src = open("/root/.claude/uploads/095e6311-fc75-5a2c-9c6a-0bc6be907c52/f9858320-adinkrakit.svg").read()
    els = re.findall(r'<(path|polygon)[^>]*?(?:\sd="([^"]+)"|\spoints="([^"]+)")', src, re.S)
    items = []
    for tag, d, ptsx in els:
        if tag == "polygon":
            nums = [float(v) for v in re.split(r"[\s,]+", ptsx.strip()) if v]
            d = "M" + " L".join(f"{nums[i]},{nums[i+1]}" for i in range(0, len(nums), 2)) + "Z"
        d = re.sub(r"\s+", " ", d)
        # bbox from a recording pen
        from fontTools.pens.boundsPen import BoundsPen
        bp = BoundsPen(None); parse_path(d, bp)
        items.append((bp.bounds, d))
    # reading order: rows (y) then columns (x)
    items.sort(key=lambda it: (round(((it[0][1] + it[0][3]) / 2) / 60), it[0][0]))
    keys = TWI + DIG
    glyphs = {".notdef": TTGlyphPen(None).glyph(), "space": TTGlyphPen(None).glyph()}
    metrics = {".notdef": (500, 0), "space": (300, 0)}
    order = [".notdef", "space"]; mapping = []
    S_ = 700 / 86.0
    for i, (bb, d) in enumerate(items[:len(keys)]):
        k = keys[i]; n = "sym_" + gname(k)
        cx, cy = (bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2
        w = (bb[2] - bb[0]) * S_
        import pathops
        path = pathops.Path()
        # svg y down -> font y up; centre each symbol on the mid axis
        tp = TransformPen(path.getPen(), (S_, 0, 0, -S_, 60 + w / 2 - cx * S_, 350 + cy * S_))
        parse_path(d, tp)
        path.fillType = pathops.FillType.EVEN_ODD; path.simplify(fix_winding=True)
        pen = TTGlyphPen(None); path.draw(Cu2QuPen(pen, 0.5, reverse_direction=True))
        glyphs[n] = pen.glyph(); metrics[n] = (round(w + 120), 60); order.append(n); mapping.append((k, n, i))
    cm = {32: "space"}
    for k, n, _ in mapping:
        if len(k) == 1:
            cm[ord(k)] = n
            if k.upper() != k: cm[ord(k.upper())] = n
    fb = FontBuilder(1000, isTTF=True)
    fb.setupGlyphOrder(order); fb.setupCharacterMap(cm); fb.setupGlyf(glyphs); fb.setupHorizontalMetrics(metrics)
    fb.setupHorizontalHeader(ascent=800, descent=-200)
    fb.setupOS2(sTypoAscender=800, sTypoDescender=-200, usWinAscent=900, usWinDescent=250)
    fb.setupNameTable(names_table("Adinkra Symbols Twi")); fb.setupPost()
    f = fb.font
    for g in f["glyf"].glyphs.values(): g.recalcBounds(f["glyf"])
    fea = "languagesystem DFLT dflt;\nlanguagesystem latn dflt;\nfeature liga {\n"
    for k, n, _ in mapping:
        if len(k) == 2:
            a, b = k
            for A_ in (a, a.upper()):
                fea += f"  sub {cm[ord(A_)] if ord(A_) in cm else 'sym_'+A_} {cm[ord(b)]} by {n};\n"
    fea += "} liga;\n"
    addOpenTypeFeaturesFromString(f, fea)
    f.save(os.path.join(OUT, "AdinkraSymbolsTwi.ttf"))
    f.flavor = "woff2"; f.save(os.path.join(OUT, "AdinkraSymbolsTwi.woff2"))
    import json
    json.dump([{"key": k, "glyph": n, "index": i} for k, n, i in mapping], open(os.path.join(OUT, "adinkra-symbols-map.json"), "w"), ensure_ascii=False)
    print("symbols ok", len(mapping))

build_alphabet(); build_symbols()
