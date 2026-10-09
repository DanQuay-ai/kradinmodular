"""Compose every Kɔradin syllable from the radicals + modifiers (turtle strokes, Black 98).
python3 compose2.py -> glyphs_v2.json {key: {strokes, comp, role per stroke}}"""
import json, math, sys, copy
import numpy as np
sys.path.insert(0, "/home/claude/work/gen")
from ks import S, walk, check, rnd, move, scale, W, GAP
from radicals import build as build_radicals

NEED = GAP * W           # 137.2
JR = 1.6 * NEED          # junction exemption radius
VOW = ["a", "e", "ɛ", "i", "o", "ɔ", "u"]
MOD = json.load(open("/home/claude/work/p1/modifiers.json"))
OLD_AX = {"top": 669.0, "mid": 342.0, "base": 31.0}

def y_new(yo):
    return 49 + (yo - 31) * 301 / 311 if yo <= 342 else 350 + (yo - 342) * 301 / 327

def level_y(base, der, v):
    r = next((x for x in MOD if x["base"] == (base or "∅") and x["der"] == der and x["v"] == v), None)
    if r is None or not r["mods"]: return 651
    big = [c for c in r["mods"] if c["area"] > 4000] or r["mods"]
    c = max(big, key=lambda c: c["area"]); y = y_new((c["box"][1] + c["box"][3]) / 2)
    for a in (49, 350, 651):
        if abs(y - a) < 25: return a
    return round(y)

def pts(strokes):
    return np.array([(p[0], p[1]) for st in strokes for p in walk(st, 8)])

def tag(strokes, role):
    return [dict(s, role=role) for s in strokes]

# ------------------------------------------------------------------ modifier bar
def crossings(strokes, yb):
    xs = []
    for st in strokes:
        P = [(p[0], p[1]) for p in walk(st, 4)]
        for (x1, y1), (x2, y2) in zip(P, P[1:]):
            if abs(y1 - yb) < 2 and abs(y2 - yb) < 2: xs += [x1, x2]
            elif (y1 - yb) * (y2 - yb) < 0: xs.append(x1 + (yb - y1) * (x2 - x1) / (y2 - y1))
    return xs

def bar_mod(strokes, target, overhang=170):
    P = pts(strokes); xmax = P[:, 0].max()
    best = None
    for dy in sorted(range(-200, 201, 4), key=abs):
        yb = target + dy
        if yb < 49 or yb > 651: continue
        xs = crossings(strokes, yb)
        if not xs: continue
        x0 = max(xs); xe = max(xmax, x0) + overhang
        # clearance of the bar from every other centreline point
        far = np.hypot(P[:, 0] - x0, P[:, 1] - yb) > JR
        inx = (P[:, 0] >= x0 - 1) & (P[:, 0] <= xe + NEED)
        dx = np.clip(P[:, 0], x0, xe)
        d = np.hypot(P[:, 0] - dx, P[:, 1] - yb)
        if np.any(far & inx & (d < NEED - 3)): continue
        deep = max(0, xmax - 60 - x0)                     # how far inside the radical the bar starts
        score = abs(dy) + 1.2 * deep
        if best is None or score < best[0]: best = (score, x0, yb, xe)
        if abs(dy) > 120 and best: break
    if best is None:
        yb = target; x0 = xmax + 60; xe = xmax + overhang
        return S(x0, yb, 0, f"L{xe - x0:.1f}"), "floating"
    _, x0, yb, xe = best
    return S(round(x0, 1), round(yb, 1), 0, f"L{xe - x0:.1f}"), f"bar at y {round(yb)}"

def clear(A, B):
    """min centreline distance between two stroke groups"""
    a, b = pts(A), pts(B)
    return float(np.min(np.linalg.norm(a[:, None] - b[None], axis=2)))

def place_right(left, right, start=-400, step=10, need=NEED + 2):
    """shift `right` horizontally until it clears `left`"""
    for dx in range(start, 1200, step):
        R = [move(s, dx) for s in right]
        if clear(left, R) >= need: return R, dx
    return [move(s, 1200) for s in right], 1200

# ------------------------------------------------------------------ parts
BRACKET = lambda x0: [S(x0, 651, 0, "L40 A100,-90 L171 A100,-90 L40")]          # ")"
MINI_I = lambda x0: [S(x0, 700, 270, "L260"), S(x0, 651, 0, "L50 A69,-180 L50")]      # stem + P flag
MINI_O = lambda x0: [S(x0, 651, 0, "L90 A80,-180 L40 A69,-90")]                     # bar + clockwise hook (mini ɔ)

def medium(strokes, v):
    """medium vowel for ny/my: spirals rebuilt with the fixed pitch, others scaled until clear"""
    if v == "o": return [S(560, 651, 180, "L250 P217,3.5,1")]
    if v == "ɔ": return [S(60, 651, 0, "L230 P217,2.5,-1")]
    for k in (0.8, 0.85, 0.9, 0.95, 1.0):
        sc = [scale(s, k) for s in strokes]
        if not check(sc): return sc
    return strokes

def build():
    R = build_radicals()
    rad = {k: tag(v["strokes"], "radical") for k, v in R.items()}
    G = {}
    def put(k, strokes, comp):
        G[k] = {"strokes": [rnd(s) for s in strokes], "comp": comp}
    for k, v in rad.items(): put(k, v, "radical")
    BARS = {"ky": "t", "tw": "t", "gy": "d", "dw": "d", "hy": "s", "z": "s", "v": "f", "hw": "f", "l": "r", "g": "k", "m": "n", "b": "p", "h": ""}
    for der, base in BARS.items():
        for v in VOW:
            src = rad[base + v]; yt = level_y(base, der, v)
            bar, how = bar_mod(src, yt)
            put(der + v, src + tag([bar], "modifier"), f"{base or 'vowel'} {base + v} + modifier ({how}, target {round(yt)})")
    for v in VOW:
        G["j" + v] = dict(G["gy" + v], comp="= gy" + v)
        # brackets: kp = p + ), gb = b + )
        for der, src_k in (("kp", "p" + v), ("gb", "b" + v)):
            src = [dict(s) for s in G[src_k]["strokes"]]
            br, dx = place_right(src, tag(BRACKET(0), "modifier"), start=int(pts(src)[:, 0].max()) - 60)
            put(der + v, src + br, f"{src_k} + bracket )")
        # glides
        vs = rad[v]
        mi = tag(MINI_I(60), "glide")
        vv, dx = place_right(mi, tag(vs, "vowel"), start=0)
        put("y" + v, mi + vv, "mini i + " + v)
        mo = tag(MINI_O(40), "glide")
        vv, dx = place_right(mo, tag(vs, "vowel"), start=0)
        put("w" + v, mo + vv, "mini ɔ + " + v)
        # ny = ni prefix + medium vowel ; my = ny + mid bar
        ni = tag([rad["ni"][0], S(40, 350, 0, "L300")], "prefix")      # ni without its hook: stem + bar
        med = tag(medium(rad[v], v), "vowel")
        vv, dx = place_right(ni, med, start=0)
        xs = [x for x in crossings(vv, 350) if x > 300]
        if xs and min(xs) - 340 < 260:                                     # the bar reaches into the vowel
            ni = ni[:1] + tag([S(40, 350, 0, f"L{min(xs) - 40:.1f}")], "prefix")
        put("ny" + v, ni + vv, "ni + medium " + v)
        G["ni" + v] = dict(G["ny" + v], comp="= ny" + v)
        bar, how = bar_mod(ni + vv, 350, overhang=120)
        put("my" + v, ni + vv + tag([bar], "modifier"), f"ny{v} + mid bar ({how})")
    # kw: kɔ + a's right leg / e's lower element
    kO = rad["kɔ"]
    leg = tag([S(0, 700, 270, "L551 A100,90 L60")], "vowel")
    vv, _ = place_right(kO, leg, start=0); put("kwa", kO + vv, "kɔ + right leg of a")
    el = tag([S(0, 350, 0, "L120 A120,-90 L230")], "vowel")
    vv, _ = place_right(kO, el, start=0); put("kwe", kO + vv, "kɔ + lower element of e")
    G["kɔa"] = dict(G["kwa"], comp="= kwa"); G["kɔe"] = dict(G["kwe"], comp="= kwe")
    return G

if __name__ == "__main__":
    G = build()
    json.dump(G, open("/home/claude/work/gen/glyphs_v2.json", "w"), ensure_ascii=False)
    import collections
    print(len(G), collections.Counter(g["comp"].split(" ")[0] for g in G.values()).most_common(12))
    print("floating:", [k for k, g in G.items() if "floating" in g["comp"]])
