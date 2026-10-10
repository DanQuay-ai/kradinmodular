"""Adinkra Alphabet Modular (v2): stroke skeletons after the original Adinkra Alphabet font, drawn
twice as tall as wide: ink 350 x 700 at the boldest weight (W 98), same axes as Kɔradin (49 / 350 / 651).
Writes site2/adinkra.json and site2/adinkra-ghost.json (the original glyphs squeezed to 350 x 700)."""
import json, math, sys
sys.path.insert(0, "/home/claude/work/gen")
from ks import S
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.boundsPen import BoundsPen

def stadium(straight=350, r=126, cy=350):
    return S(175 - r, cy, 90, f"L{straight/2} A{r},-180 L{straight} A{r},-180 L{straight/2}")
def rect(x0, y0, x1, y1):
    w, h = x1 - x0, y1 - y0
    return S(x0, y0 + h / 2, 90, f"L{h/2} C-90 L{w} C-90 L{h} C-90 L{w} C-90 L{h/2}")
def seg(x0, y0, x1, y1):
    return S(x0, y0, round(math.degrees(math.atan2(y1 - y0, x1 - x0)) % 360, 2), f"L{round(math.hypot(x1-x0, y1-y0), 1)}")
def poly(*pts):
    """open polyline with sharp corners"""
    hs = [math.degrees(math.atan2(b[1]-a[1], b[0]-a[0])) for a, b in zip(pts, pts[1:])]
    toks = []
    for i, (a, b) in enumerate(zip(pts, pts[1:])):
        if i: toks.append(f"C{round(((hs[i]-hs[i-1]+180) % 360) - 180, 2)}")
        toks.append(f"L{round(math.hypot(b[0]-a[0], b[1]-a[1]), 1)}")
    return S(pts[0][0], pts[0][1], round(hs[0] % 360, 2), " ".join(toks))
def closed(*pts):
    """closed polygon, started half way along its first side so the ends meet flush"""
    m = ((pts[0][0] + pts[1][0]) / 2, (pts[0][1] + pts[1][1]) / 2)
    return poly(m, *pts[1:], pts[0], m)
def arcthru(x0, y0, x1, y1, sag, up=True):
    """circular arc between two points bulging by sag (to the left of travel when up)"""
    c = math.hypot(x1 - x0, y1 - y0); r = (c * c / 4 + sag * sag) / (2 * sag); half = math.degrees(math.asin(min(1, c / 2 / r)))
    if sag > c / 2: half = 180 - half
    h = math.degrees(math.atan2(y1 - y0, x1 - x0))
    return S(x0, y0, round((h + half if up else h - half) % 360, 2), f"A{round(r,1)},{round(-2*half if up else 2*half, 2)}")

L_, R_, C_, B_, T_ = 49, 301, 175, 49, 651
A = {
 "a": [stadium(), S(175, 320, 90, "L60")],
 "b": [S(175, 700, 270, "L350"), S(49, 0, 90, "L224 A126,-180 L224")],
 "c": [S(0, 651, 0, "L175 A126,-90 L350 A126,-90 L175")],
 "d": [stadium(), rect(129, 290, 221, 410)],
 "e": [S(301, 651, 180, "L126 A75,90 L151 A75,90"), S(175, 350, 180, "A75,90 L151 A75,90 L126")],
 "ɛ": [closed((53, 350), (175, 575), (297, 350), (175, 125))],
 "f": [S(49, 0, 90, "L590 A61,-90 L191"), S(49, 380, 0, "L190")],
 "g": [S(60, 470, 90, "A100,-180 L60 A110,-90 A100,180 L80 A80,50")],
 "h": [S(0, 651, 0, "L350"), S(175, 651, 270, "L651"), S(0, 390, 0, "L350"), S(49, 390, 270, "L390"), S(301, 390, 270, "L390")],
 "i": [S(175, 700, 270, "L651"), arcthru(10, 130, 340, 130, 81, up=False)],
 "j": [poly((30, 700), (230, 350), (30, 0)), poly((320, 700), (120, 350), (320, 0))],
 "k": [S(49, 700, 270, "L700"), S(301, 700, 270, "L700"), arcthru(49, 350, 301, 350, 95), arcthru(49, 350, 301, 350, 95, up=False)],
 "l": [S(0, 651, 0, "L350"), seg(49, 651, 175, 49), seg(301, 651, 175, 49), S(0, 49, 0, "L350")],
 "m": [S(129, 130, 90, "L480 A40,270 L172 A40,270 L520 A40,270 L172 A40,270 L40")],
 "n": [rect(49, 49, 301, 651)],
 "o": [stadium()],
 "ɔ": [S(0, 651, 0, "L350"), S(0, 49, 0, "L350"), stadium(98)],
 "p": [S(0, 651, 0, "L350"), S(0, 49, 0, "L350"), S(175, 651, 270, "L602")],
 "q": [S(49, 700, 270, "L300"), S(301, 700, 270, "L300"), S(175, 700, 270, "L700"), S(0, 400, 0, "L350")],
 "r": [S(301, 700, 270, "L350 C-90 L126 A75,90 L151 A75,90 L175")],
 "s": [S(283, 588, 120, "A125,240 L126"), S(140, 401, 270, "L401"), seg(250, 401, 320, 0)],
 "t": [S(175, 700, 270, "L700"), poly((14, 520), (175, 630), (336, 520))],
 "u": [rect(49, 49, 301, 651), S(0, 350, 0, "L350")],
 "v": [S(49, 49, 90, "L476 A126,-180 L476"), S(0, 49, 0, "L350")],
 "w": [stadium(), S(175, 700, 270, "L700")],
 "x": [S(110, 700, 270, "L700"), S(0, 350, 0, "L270"), arcthru(250, 700, 250, 0, 51, up=False)],
 "y": [S(125, 600, 90, "A50,-360"), S(175, 550, 270, "L550"), S(0, 360, 0, "L350"), S(49, 360, 270, "L360"), S(301, 360, 270, "L360")],
 "z": [rect(49, 49, 301, 441), S(110, 441, 90, "L120 A65,-180 L120")],
}
A["@period"] = [S(175, 0, 90, "L60")]
A["@comma"] = [S(175, 60, 90, "L40"), S(175, 60, 250, "L90")]
A["@hyphen"] = [S(40, 350, 0, "L270")]
A["@exclam"] = [S(175, 700, 270, "L420"), S(175, 0, 90, "L60")]
A["@question"] = [S(75, 520, 90, "A100,-180 L40 A100,90 L60"), S(175, 0, 90, "L60")]

out = {"_version": "ad-2026-10-10a", "glyphs": {}}
for k, st in A.items():
    out["glyphs"][k] = {"type": "radical", "group": "other" if k.startswith("@") else "letter", "strokes": st, "status": "draft"}
json.dump(out, open("/home/claude/work/site2/adinkra.json", "w"), ensure_ascii=False, separators=(",", ":"))

# ghost: original glyphs squeezed into 350 x 700
f = TTFont("/home/claude/work/site2/adinkra/fonts/AdinkraAlphabet.ttf"); cm = f.getBestCmap(); gs = f.getGlyphSet()
gh = {}
for k in A:
    ch = {"ɛ": "E", "ɔ": "O"}.get(k, k)
    if ch.startswith("@") or ord(ch) not in cm: continue
    g = gs[cm[ord(ch)]]; b = BoundsPen(gs); g.draw(b); x0, y0, x1, y1 = b.bounds
    sp = SVGPathPen(gs); tp = TransformPen(sp, (350 / (x1 - x0), 0, 0, 700 / (y1 - y0), -x0 * 350 / (x1 - x0), -y0 * 700 / (y1 - y0))); g.draw(tp)
    gh[k] = {"d": sp.getCommands()}
json.dump(gh, open("/home/claude/work/site2/adinkra-ghost.json", "w"), separators=(",", ":"))
print(len(A), "glyphs;", len(gh), "ghosts")
