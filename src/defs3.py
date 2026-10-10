"""Glyph definitions v3: previous defaults + the user's edits baked in, redrafted radicals, extra glyphs
(digits, punctuation, standalone consonants, nasal marks) and composites redrawn with the rules learned
from the user's approved modifiers. -> site2/glyphs.json"""
import json, sys, math, copy
sys.path.insert(0, "/home/claude/work/gen")
from ks import S, rnd, move, scale, mirror, walk, rev
import numpy as np

PREV = json.load(open("/home/claude/work/gen/glyphs_v2b.json"))["glyphs"]
USER = json.load(open("/home/claude/work/gen/edits3.json"))
VOW = ["a", "e", "ɛ", "i", "o", "ɔ", "u"]
D = copy.deepcopy(PREV)

# ---------------------------------------------------------------- 1. bake the user's edits
for k, e in USER.items():
    if k not in D: continue
    st = "approved" if e.get("approved") else "fix" if e.get("fix") else "draft"
    if D[k]["type"] == "radical":
        D[k]["strokes"] = e["strokes"]
    else:
        D[k]["comps"] = e.get("comps", D[k]["comps"]); D[k]["strokes"] = e["strokes"]
    D[k]["status"] = st
    if e.get("note"): D[k]["note"] = e["note"]

def approved(k): return D.get(k, {}).get("status") == "approved"

# ---------------------------------------------------------------- 2. radicals still to approve
R = {}
R["sɛ"] = [mirror(s, 330) for s in USER["se"]["strokes"]]          # mirror of the approved se
R["na"] = [S(40, 651, 0, "L680"),
           S(420, 651, 270, "L131 C-90 L80 A150,180 L80 C-90 L170"),   # stem, C bowing left, stem again (one stroke)
           S(420, 520, 0, "L150"), S(420, 120, 0, "L150")]
R["nɛ"] = [S(50, 570, 90, "A70,-180 L220 A300,-30 L300"),
           S(330, 0, 90, "L480 A115,-180 L40 A115,-90 L115"),      # stem up into a P bowl that returns to the stem
           S(100, 350, 0, "L230")]
R["ri"] = [S(200, 520, 90, "L41 A80,180 L362 A150,90 L240 A150,90 L362 A80,180 L41")]
R["ro"] = [S(20, 700, 270, "L501 A150,90 L250 A150,90 L501"),
           S(295, 700, 270, "L170"),
           S(230, 235, 90, "L240 A55,270 L240 A55,270 L240 A55,270 L240 A55,270"),   # knot (⌘) on the stem
           S(295, 180, 270, "L131")]
R["ra"] = [S(40, 470, 0, "L60 A90,90 L91 C-90 L110 A120,-120 L314 A100,120 L300"), S(540, 49, 90, "L130")]
R["fa"] = [S(40, 0, 70, "L693 C-155 L452 C155 L480 C-155 L604 C85 L100")]
R["fe"] = [S(420, 651, 180, "L225 A75,180 L105 C-90 L352 A100,-90 L140"), S(180, 364, 0, "L240"), S(140, 227, 0, "L320")]
for k, st in R.items():
    if not approved(k):
        D[k] = {"type": "radical", "strokes": [rnd(s) for s in st], "status": "draft"}

# ---------------------------------------------------------------- 3. extra glyphs (all glyphs of the font)
X = {}
def tri(x0, x1, y0, apx, apy):          # closed triangle: top edge, then down to the apex and back
    L1 = math.hypot(apx - x1, apy - y0); h1 = math.degrees(math.atan2(apy - y0, apx - x1))
    L2 = math.hypot(x0 - apx, y0 - apy); h2 = math.degrees(math.atan2(y0 - apy, x0 - apx))
    return S(x0, y0, 0, f"L{x1-x0} C{h1:.2f} L{L1:.1f} C{(h2-h1+540)%360-180:.2f} L{L2:.1f}")
X["zero"] = [tri(49, 600, 600, 325, 49)]
X["one"] = [S(100, 620, 270, "L620")]
X["two"] = [S(49, 600, 0, "L120 C-60 L250 C-60 L250 C-60 L120")]
X["three"] = [S(49, 120, 90, "L230 A250,-180 L230"), S(299, 0, 90, "L600")]
X["four"] = [S(60, 540, 270, "L190 A120,90 L60 A120,90 L190"), S(300, 0, 90, "L620")]
X["five"] = [S(49, 600, 0, "L80 A120,-60 L260 A120,60 L80"), S(549, 600, 180, "L80 A120,60 L260 A120,-60 L80"), S(300, 300, 0, "L380")]
X["six"] = [S(49, 600, 0, "L80 A120,-60 L260 A120,60 L80"), S(549, 600, 180, "L80 A120,60 L260 A120,-60 L80"), S(49, 300, 0, "L640")]
X["seven"] = [tri(49, 520, 600, 285, 49), S(400, 300, 0, "L300")]
X["eight"] = [S(49, 600, 0, "L150 C-60 L318 C-60 L318 C-60 L150"), S(49, 325, 0, "L250")]
X["nine"] = [S(49, 280, 90, "L70 A250,-180 L70"), S(299, 0, 90, "L600")]
X["period"] = [S(100, 0, 90, "L700")]
X["comma"] = [S(200, 60, 45, "L200 C90 L200 C90 L200 C90 L200")]
X["exclam"] = [S(170, 120, 90, "A70,360"), S(170, 350, 90, "A70,360"), S(170, 580, 90, "A70,360")]
X["question"] = [S(350, 49, 45, "L300 C90 L300 C90 L300 C90 L300"), S(350, 0, 90, "L700")]
# standalone consonants (placeholders from the Adinkra alphabet), drawn in a smaller box (x 49..349, y 160..540)
B0, B1 = 160, 540
X["b"] = [S(49, B0, 90, "L130 A150,-180 L130"), S(199, B1, 90, "L0")]
X["b"][1] = S(199, 620, 270, "L180")
X["c"] = [S(80, B1, 0, "L200 C-130 L200 C130 L200")]
X["d"] = [S(49, 350, 90, "A150,-360"), S(160, 300, 90, "L100")]
X["f"] = [S(60, B1 + 60, 270, "L440"), S(60, B1, 0, "L260"), S(60, 380, 0, "L180")]
X["g"] = [S(49, 440, 90, "A100,-180 L40 A120,90 A100,-180")]
X["h"] = [S(49, B1, 0, "L300"), S(199, B1, 270, "L380"), S(49, 380, 0, "L300"), S(49, 380, 270, "L220"), S(349, 380, 270, "L220")]
X["j"] = [S(49, B1, 300, "L438"), S(349, B1, 240, "L438")]
X["k"] = [S(49, B1, 270, "L380"), S(349, B1, 270, "L380"), S(49, 480, 300, "L346"), S(349, 480, 240, "L346")]
X["l"] = [tri(49, 349, B1, 199, B0), S(49, B0, 0, "L300")]
X["p"] = [S(49, B1, 0, "L300"), S(199, B1, 270, "L380"), S(49, B0, 0, "L300")]
X["q"] = [S(80, B1, 0, "L200 C-130 L200 C130 L200")]
X["r"] = [S(349, B1, 270, "L380"), S(349, 320, 180, "L150 A80,90 A80,90 L150")]
X["s"] = [S(349, 440, 90, "A100,180 L280"), S(149, 350, 300, "L220")]
X["t"] = [S(49, 440, 49.5, "L180 C-99 L180"), S(166, 576, 270, "L416")]
X["v"] = [S(49, B0, 90, "L230 A150,-180 L230"), S(49, B0, 0, "L300")]
X["w"] = [rnd(s) for s in D["ɔ"]["strokes"]]
X["y"] = [S(260, 470, 90, "A60,360"), S(200, 410, 270, "L250"), S(49, 330, 0, "L300"), S(49, 330, 270, "L170"), S(349, 330, 270, "L170")]
X["z"] = [S(49, 400, 0, "L300 C-90 L240 C-90 L300 C-90 L240 C-90"), S(130, 400, 90, "L60 A70,-180 L60")]
X["m"] = [S(49, 49, 0, "L110"), S(239, 49, 0, "L110")]
X["n"] = [S(49, 49, 0, "L110")]
X["ng"] = [S(49, 49, 90, "L60 A90,-180 L60")]
X["m.pre"] = [S(49, 350, 0, "L110"), S(239, 350, 0, "L110")]
X["n.pre"] = [S(49, 350, 0, "L110")]
X["ng.pre"] = [S(49, 300, 90, "L50 A90,-180 L50")]
for k, st in X.items():
    D["@" + k] = {"type": "radical", "group": "other", "strokes": [rnd(s) for s in st], "status": "draft"}

# ---------------------------------------------------------------- 4. composites
def flat(comps):
    out = []
    for c in comps:
        d = D[c["ref"]]
        src = (flat(d["comps"]) + d["strokes"]) if d["type"] == "composite" else d["strokes"]
        if d["type"] == "composite": src = apply_exts(d, src)
        for s in src: out.append(move(scale(s, c.get("s", 1)), c.get("dx", 0), c.get("dy", 0)))
    return out

def apply_exts(d, strokes):
    return strokes  # extensions are applied at resolve time in the site (kr.js); for placement we ignore them

def pts(strokes, step=6):
    return np.array([(p[0], p[1]) for s in strokes for p in walk(s, step)])

def ends(strokes):
    """(index, at, x, y, outward heading) for every free end"""
    out = []
    for i, s in enumerate(strokes):
        P = walk(s); x0, y0 = P[0][0], P[0][1]; x1, y1 = P[-1][0], P[-1][1]
        h = s["h"]
        for g in s["segs"]:
            if g["t"] != "L": h += g["ang"]
        out.append((i, "start", x0, y0, (s["h"] + 180) % 360)); out.append((i, "end", x1, y1, h % 360))
    return out

def crossings(strokes, yb):
    xs = []
    for s in strokes:
        P = [(p[0], p[1]) for p in walk(s, 4)]
        for (x1, y1), (x2, y2) in zip(P, P[1:]):
            if abs(y1 - yb) < 2 and abs(y2 - yb) < 2: xs += [x1, x2]
            elif (y1 - yb) * (y2 - yb) < 0: xs.append(x1 + (yb - y1) * (x2 - x1) / (y2 - y1))
    return xs

AXES = (49, 350, 651)
def axis_for(y): return min(AXES, key=lambda a: abs(a - y))

def bar_modifier(base_strokes, axis, overhang=120):
    """learned from the approved bars: on the axis, from the rightmost element, ~120 past the sign.
    Returns ('ext', i, at, segs) to continue an existing stroke, or ('bar', stroke)."""
    P = pts(base_strokes); xmax = P[:, 0].max(); xe = xmax + overhang
    # a free end on the right near the axis: continue that stroke instead of adding one
    cand = [e for e in ends(base_strokes) if abs(e[3] - axis) <= 30 and e[2] >= xmax - 140]
    if cand:
        i, at, x, y, h = max(cand, key=lambda e: e[2] - abs(e[3] - axis))
        turn = (0 - h + 540) % 360 - 180
        segs = ([] if abs(turn) < 1 else [{"t": "C", "ang": round(turn, 1)}]) + [{"t": "L", "len": round(max(xe, x + 150) - x, 1)}]
        return ("ext", i, at, segs)
    xs = crossings(base_strokes, axis)
    if xs:
        x0 = max(xs); return ("bar", S(round(x0, 1), axis, 0, f"L{max(xe, x0 + 150) - x0:.1f}", role="modifier"))
    # nothing on the axis: start on the rightmost element at the nearest height
    best = None
    for dy in range(0, 200, 4):
        for sg in (1, -1):
            xs = crossings(base_strokes, axis + sg * dy)
            if xs: best = (axis + sg * dy, max(xs)); break
        if best: break
    yb, x0 = best if best else (axis, xmax)
    return ("bar", S(round(x0, 1), yb, 0, f"L{max(xe, x0 + 150) - x0:.1f}", role="modifier"))

def ext_index(comps, ci, local_i):
    return local_i   # strokes are indexed inside the component's own resolved list

def comp_def(kind, comps, strokes=(), exts=(), wait=()):
    return {"type": "composite", "kind": kind, "comps": comps, "strokes": [rnd(dict(s, role=s.get("role", "modifier"))) for s in strokes],
            "exts": list(exts), "wait": list(wait), "status": "draft"}

def mk_bar(key, base_key, level):
    base = flat([{"ref": base_key}])
    r = bar_modifier(base, axis_for(level))
    if r[0] == "ext":
        D[key] = comp_def("bar", [{"ref": base_key}], [], [{"c": 0, "i": r[1], "at": r[2], "segs": r[3]}])
    else:
        D[key] = comp_def("bar", [{"ref": base_key}], [r[1]])

# convert approved bars that start on a stroke end into extensions (twe: continue te instead of a new stroke)
def to_extension(k):
    d = D[k]
    if d["type"] != "composite" or len(d["comps"]) != 1 or len(d["strokes"]) != 1: return False
    b = d["strokes"][0]
    if not (len(b["segs"]) == 1 and b["segs"][0]["t"] == "L" and abs(b["h"] % 360) < 1): return False
    base = flat(d["comps"])
    for i, at, x, y, h in ends(base):
        if math.hypot(x - b["x"], y - b["y"]) <= 25 and x <= b["x"] + 5:
            turn = (0 - h + 540) % 360 - 180
            if abs(turn) > 135: continue
            xe = b["x"] + b["segs"][0]["len"]
            segs = ([] if abs(turn) < 1 else [{"t": "C", "ang": round(turn, 1)}]) + [{"t": "L", "len": round(xe - x, 1)}]
            d["strokes"] = []; d["exts"] = [{"c": 0, "i": i, "at": at, "segs": segs}]
            return True
    return False

LEVEL = {}
for k, d in PREV.items():
    if d["type"] == "composite" and d["kind"] == "bar" and d["strokes"]:
        LEVEL[k] = d["strokes"][0]["y"]
BARS = {"b": "p", "ky": "t", "tw": "t", "gy": "d", "dw": "d", "hy": "s", "z": "s", "v": "f", "hw": "f", "l": "r", "g": "k", "m": "n", "h": ""}
# the level each row used in the source font, snapped to an axis (from the earlier analysis)
sys.path.insert(0, "/home/claude/work/gen")
import compose2 as C2
converted = []
for der, base in BARS.items():
    for v in VOW:
        k = der + v
        D[k].setdefault("exts", []); D[k].setdefault("wait", [])
        if approved(k):
            if to_extension(k): converted.append(k)
            continue
        mk_bar(k, base + v, C2.level_y(base, der, v))

MINI_I = lambda: S(60, 700, 270, "L240", role="glide")
MINI_I_FLAG = lambda: S(60, 651, 0, "L50 A69,-180 L50", role="glide")
def place_right(left, right, gap=100):
    a = pts(left); b0 = pts(right)
    start = int(a[:, 0].max() - b0[:, 0].min() - 250)
    for dx in range(start, 1600, 5):
        b = pts([move(s, dx) for s in right])
        if np.min(np.linalg.norm(a[:, None] - b[None], axis=2)) >= gap: return dx
    return 1400

for v in VOW:
    vs = D[v]["strokes"]
    D["j" + v] = {"type": "alias", "of": "gy" + v}; D["ni" + v] = {"type": "alias", "of": "ny" + v}
    # brackets: closer to the sign (gap 100)
    for der, src in (("kp", "p" + v), ("gb", "b" + v)):
        if approved(der + v): continue
        base = flat([{"ref": src}])
        dx = place_right(base, [S(0, 651, 0, "L40 A100,-90 L171 A100,-90 L40")], gap=110)
        D[der + v] = comp_def("bracket", [{"ref": src}], [S(dx, 651, 0, "L40 A100,-90 L171 A100,-90 L40")], wait=[src] if der == "gb" else [])
    # y-: mini i, vowel tucked closer
    if not approved("y" + v):
        mi = [MINI_I(), MINI_I_FLAG()]
        dx = place_right(mi, vs, gap=105)
        D["y" + v] = comp_def("glide", [{"ref": v, "dx": dx}], mi)
    # w-: mini ɔ whose bar runs on along the top to the vowel (as in your wo)
    if not approved("w" + v):
        hook = S(21, 560, 270, "A69,90 L40 A80,180 L90 C180 L100", role="glide")
        dx = place_right([hook], vs, gap=105)
        vp = pts([move(s, dx) for s in vs]); top = vp[vp[:, 1] > 600]
        reach = (top[:, 0].min() - 21) if len(top) else 160
        hook = S(21, 560, 270, f"A69,90 L40 A80,180 L90 C180 L{max(100, min(reach, 700)):.0f}", role="glide")
        D["w" + v] = comp_def("glide", [{"ref": v, "dx": dx}], [hook])
    # ny- = ni + vowel ; my- = mi + vowel, waits for ny-
    s = 0.72 if v in ("o", "ɔ") else 0.8
    med = [scale(x, s) for x in vs]
    if not approved("ny" + v):
        dx = place_right(D["ni"]["strokes"], med, gap=100)
        D["ny" + v] = comp_def("ny", [{"ref": "ni"}, {"ref": v, "dx": dx, "s": s}])
    if not approved("my" + v):
        mi_strokes = flat([{"ref": "mi"}])
        dx = place_right(mi_strokes, med, gap=100)
        D["my" + v] = comp_def("my", [{"ref": "mi"}, {"ref": v, "dx": dx, "s": s}], wait=["ny" + v])
for v in ("a", "e"):
    if approved("kw" + v): continue
    med = [scale(x, 0.8) for x in D[v]["strokes"]]
    dx = place_right(D["kɔ"]["strokes"], med, gap=100)
    D["kw" + v] = comp_def("kw", [{"ref": "kɔ"}, {"ref": v, "dx": dx, "s": 0.8}])
for k, d in D.items():
    if d["type"] == "composite": d.setdefault("exts", []); d.setdefault("wait", [])

out = {"_version": "2026-10-10c", "glyphs": D}
json.dump(out, open("/home/claude/work/site2/glyphs.json", "w"), ensure_ascii=False, separators=(",", ":"))
import collections
print(collections.Counter((d["type"], d.get("status")) for d in D.values()))
print("bars turned into extensions:", converted)
print("new extensions:", [k for k, d in D.items() if d.get("exts") and k not in converted])
