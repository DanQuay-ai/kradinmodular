"""Kɔradin Modular 2: variable fonts from the stroke-generator glyphs.
python3 -I build3.py glyphs_v2.json <outdir>"""
import sys, os, json, math, copy
sys.path.insert(0, "/home/claude/work/gen"); sys.path.insert(0, "/home/claude/work/stroke")
from fontTools.ttLib import TTFont
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.designspaceLib import DesignSpaceDocument, AxisDescriptor, SourceDescriptor
from fontTools import varLib
from fontTools.varLib import instancer
from outline import stroke_polygon, round_cap_polygon

SRC = "/home/claude/work/in/f2f3efd1-Koradin.otf"
GJ, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True); TMP = os.path.join(OUT, "_m"); os.makedirs(TMP, exist_ok=True)
G = json.load(open(GJ))
SB = 50
VK = {"a": "a", "e": "e", "eopen": "ɛ", "i": "i", "o": "o", "oopen": "ɔ", "u": "u"}

def key_of(name):
    if name in VK: return VK[name]
    if name.endswith(".liga") and name != "ng.liga":
        return name[:-5].replace("oopen", "ɔ").replace("eopen", "ɛ")
    return None

# the source font's CFF -> glyf conversion (keeps cmap, GSUB, GPOS, marks)
def otf_to_ttf_(p):
    from fontTools.ttLib import newTable
    from fontTools.pens.cu2quPen import Cu2QuPen
    f = TTFont(p); gs = f.getGlyphSet()
    glyf = newTable("glyf"); glyf.glyphOrder = f.getGlyphOrder(); glyf.glyphs = {}
    for name in f.getGlyphOrder():
        pen = TTGlyphPen(None); gs[name].draw(Cu2QuPen(pen, max_err=1.0, reverse_direction=True)); glyf[name] = pen.glyph()
    f["loca"] = newTable("loca"); f["glyf"] = glyf; del f["CFF "]
    f["maxp"].tableVersion = 0x00010000
    for kk in ("maxZones", "maxTwilightPoints", "maxStorage", "maxFunctionDefs", "maxInstructionDefs",
               "maxStackElements", "maxSizeOfInstructions", "maxComponentElements", "maxComponentDepth"):
        setattr(f["maxp"], kk, 0)
    f["maxp"].maxZones = 1; f["head"].glyphDataFormat = 0
    f["post"].formatType = 2.0; f["post"].extraNames = []; f["post"].mapping = {}
    f.sfntVersion = "\x00\x01\x00\x00"
    return f

def glyph_from_polys(polys):
    pen = TTGlyphPen(None)
    for poly in polys:
        pts = [(round(x), round(y)) for x, y in poly]
        clean = [pts[0]]
        for p in pts[1:]: clean.append(p)
        pen.moveTo(clean[0])
        for p in clean[1:]: pen.lineTo(p)
        pen.closePath()
    g = pen.glyph()
    if g.numberOfContours > 0: g.flags[0] |= 0x40          # overlapping contours: nonzero fill
    return g

def set_names(f, family, style="Regular"):
    nm = f["name"]
    for nid in (1, 2, 3, 4, 6, 16, 17, 25): nm.removeNames(nameID=nid)
    ps = (family + "-" + style).replace(" ", "").replace("ɔ", "o")
    for nid, val in ((1, family), (2, style), (3, ps + "-2026.2"), (4, f"{family} {style}"), (6, ps)):
        nm.setName(val, nid, 3, 1, 0x409); nm.setName(val, nid, 1, 0, 0)

def master(base, W, xs, sl, rounded):
    f = copy.deepcopy(base); glyf, hmtx = f["glyf"], f["hmtx"]
    k = (700 - W) / 602; t = math.tan(math.radians(sl))
    tf = lambda x, y: (x * xs + (y - 350) * t, y)
    ga = {}
    for name in f.getGlyphOrder():
        kk = key_of(name)
        if kk is None or kk not in G: continue
        polys = [(round_cap_polygon if rounded else stroke_polygon)(st, W, k, tf) for st in G[kk]["strokes"]]
        # metrics from the unslanted ink so the advance does not jump with the slant
        un = [stroke_polygon(st, W, k, lambda x, y: (x * xs, y)) for st in G[kk]["strokes"]]
        xsn = [p[0] for poly in un for p in poly]
        x0, x1 = min(xsn), max(xsn)
        polys = [[(x - x0 + SB, y) for x, y in poly] for poly in polys]
        g = glyph_from_polys(polys); glyf[name] = g; g.recalcBounds(glyf)
        adv = round(x1 - x0 + 2 * SB); hmtx[name] = (adv, g.xMin); ga[name] = adv
    gpos = f["GPOS"].table
    for lk in gpos.LookupList.Lookup:
        for stb in lk.SubTable:
            if lk.LookupType == 4:
                for gname, rec in zip(stb.BaseCoverage.glyphs, stb.BaseArray.BaseRecord):
                    for a in rec.BaseAnchor:
                        if a is not None and gname in ga: a.XCoordinate = round(ga[gname] / 2)
    return f

def main():
    base = otf_to_ttf_(SRC)
    WMIN, WDEF, WMAX = 22.0, 50.5, 98.0
    for style, rounded in (("Regular", False), ("Rounded", True)):
        fam = "Koradin Modular 2" if style == "Regular" else "Koradin Modular 2 Rounded"
        ds = DesignSpaceDocument()
        for tag, nm_, mn, df, mx in (("wght", "Weight", 100, 400, 900), ("wdth", "Width", 100, 100, 125), ("slnt", "Slant", -10, 0, 0)):
            a = AxisDescriptor(); a.tag, a.name, a.minimum, a.default, a.maximum = tag, nm_, mn, df, mx
            if tag == "wght": a.map = [(100, WMIN), (400, WDEF), (900, WMAX)]
            ds.addAxis(a)
        for W in (WMIN, WDEF, WMAX):
            for wd in (100, 125):
                for sl in (0, -10):
                    m = master(base, W, wd / 100, -sl, rounded)
                    set_names(m, fam)
                    p = os.path.join(TMP, f"{style}-{W}-{wd}-{sl}.ttf"); m.save(p)
                    s = SourceDescriptor(); s.path = p; s.location = {"Weight": W, "Width": wd, "Slant": sl}; s.name = f"{W}-{wd}-{sl}"
                    ds.addSource(s)
        vf, _, _ = varLib.build(ds, exclude=["STAT"])
        set_names(vf, fam)
        stem = "KoradinModular2" + ("" if style == "Regular" else "-Rounded")
        vp = os.path.join(OUT, f"{stem}-VF.ttf"); vf.save(vp)
        vf.flavor = "woff2"; vf.save(os.path.join(OUT, f"{stem}-VF.woff2"))
        for wname, wv in (("Thin", 100), ("Regular", 400), ("Bold", 700), ("Black", 900)):
            inst = instancer.instantiateVariableFont(TTFont(vp), {"wght": wv, "wdth": 100, "slnt": 0})
            set_names(inst, fam, wname); inst.save(os.path.join(OUT, f"{stem}-{wname}.ttf"))
        print("built", style, os.path.getsize(vp), flush=True)

main()
