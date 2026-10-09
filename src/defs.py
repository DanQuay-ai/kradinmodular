"""Construction definitions for every Kɔradin glyph: radicals (own strokes) and composites
(locked components {ref, dx, dy, s} + their own modifier strokes). -> site2/glyphs.json"""
import json, sys
sys.path.insert(0, "/home/claude/work/gen")
from ks import S, rnd, move, scale
from radicals import build as build_radicals
import compose2 as C

VOW = C.VOW
R = build_radicals()
rad = {k: v["strokes"] for k, v in R.items()}
D = {}
for k, v in R.items():
    D[k] = {"type": "radical", "strokes": v["strokes"], "status": v["status"]}

def comp(key, comps, own, kind):
    D[key] = {"type": "composite", "kind": kind, "comps": comps, "strokes": [rnd(dict(s, role="modifier")) for s in own], "status": "draft"}

def flat(comps):
    out = []
    for c in comps:
        src = flat(D[c["ref"]]["comps"]) + D[c["ref"]]["strokes"] if D[c["ref"]]["type"] == "composite" else D[c["ref"]]["strokes"]
        for s in src:
            s2 = scale(s, c.get("s", 1)); s2 = move(s2, c.get("dx", 0), c.get("dy", 0)); out.append(s2)
    return out

BARS = {"b": "p", "ky": "t", "tw": "t", "gy": "d", "dw": "d", "hy": "s", "z": "s", "v": "f", "hw": "f", "l": "r", "g": "k", "m": "n", "h": ""}
for der, base in BARS.items():
    for v in VOW:
        src = rad[base + v]; yt = C.level_y(base, der, v)
        bar, how = C.bar_mod(src, yt)
        comp(der + v, [{"ref": base + v}], [bar], "bar")
for v in VOW:
    D["j" + v] = {"type": "alias", "of": "gy" + v}
    for der, src_k in (("kp", "p" + v), ("gb", "b" + v)):
        src = flat([{"ref": src_k}]) if D[src_k]["type"] == "composite" else rad[src_k]
        src = src + (D[src_k]["strokes"] if D[src_k]["type"] == "composite" else [])
        br, dx = C.place_right(src, C.BRACKET(0), start=int(C.pts(src)[:, 0].max()) - 60)
        comp(der + v, [{"ref": src_k}], br, "bracket")
    # glides: the vowel is a locked component, the mini i / mini ɔ are the glyph's own strokes
    for der, mini in (("y", C.MINI_I(60)), ("w", C.MINI_O(40))):
        _, dx = C.place_right(mini, rad[v], start=0)
        comp(der + v, [{"ref": v, "dx": dx}], mini, "glide")
    # ny = ni + vowel (both locked)
    s = 0.72 if v in ("o", "ɔ") else 0.8
    med = [scale(x, s) for x in rad[v]]
    _, dx = C.place_right(rad["ni"], med, start=0)
    comp("ny" + v, [{"ref": "ni"}, {"ref": v, "dx": dx, "s": s}], [], "ny")
    D["ni" + v] = {"type": "alias", "of": "ny" + v}
    # my = ny (locked, waits for ny approval) + mid bar
    bar, how = C.bar_mod(flat([{"ref": "ny" + v}]), 350, overhang=120)
    comp("my" + v, [{"ref": "ny" + v}], [bar], "bar")
for v in ("a", "e"):
    s = 0.8
    med = [scale(x, s) for x in rad[v]]
    _, dx = C.place_right(rad["kɔ"], med, start=0)
    comp("kw" + v, [{"ref": "kɔ"}, {"ref": v, "dx": dx, "s": s}], [], "kw")
D["kɔa"] = {"type": "alias", "of": "kwa"}; D["kɔe"] = {"type": "alias", "of": "kwe"}

out = {"_version": "2026-10-10a", "glyphs": D}
json.dump(out, open("/home/claude/work/site2/glyphs.json", "w"), ensure_ascii=False, separators=(",", ":"))
import collections
print(collections.Counter(d["type"] for d in D.values()), len(D))
