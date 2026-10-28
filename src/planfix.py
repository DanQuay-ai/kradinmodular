"""Letter plans, second step: when a traced letter has fewer strokes than its plan (a bowl and stem read as one
line), split it at its sharpest corner, the place where the pen would lift."""
import json, math, sys
sys.path.insert(0, "/home/claude/work/gen")
from autotrace import PLAN
def seglen(g): return g["len"] if g["t"] == "L" else abs(g["ang"]) * math.pi / 180 * g["r"] if g["t"] == "A" else 0
def walk_to(st, n):
    x, y, h = st["x"], st["y"], st["h"]
    for g in st["segs"][:n]:
        if g["t"] == "C": h += g["ang"]
        elif g["t"] == "L": x += g["len"] * math.cos(math.radians(h)); y += g["len"] * math.sin(math.radians(h))
        else:
            sg = 1 if g["ang"] > 0 else -1; r = g["r"]
            cx = x + r * math.cos(math.radians(h + 90 * sg)); cy = y + r * math.sin(math.radians(h + 90 * sg))
            a = math.atan2(y - cy, x - cx) + math.radians(g["ang"]); x, y = cx + r * math.cos(a), cy + r * math.sin(a); h += g["ang"]
    return x, y, h
def split(st):
    cs = [(abs(g["ang"]), i) for i, g in enumerate(st["segs"]) if g["t"] == "C" and 0 < i < len(st["segs"]) - 1]
    if not cs: return None
    a, i = max(cs)
    if a < 45: return None
    L = [seglen(g) for g in st["segs"]]; T = sum(L) or 1; t = sum(L[:i]) / T
    x, y, h = walk_to(st, i + 1)
    s1 = dict(st, segs=st["segs"][:i], cap1="butt"); s2 = dict(st, x=round(x, 1), y=round(y, 1), h=round(h % 360, 2), segs=st["segs"][i + 1:], cap0="butt")
    if "wp" in st:
        wp = st["wp"]
        s1["wp"] = [[round(p / t, 3), w] for p, w in wp if p <= t] or [[0, wp[0][1]], [1, wp[0][1]]]
        s2["wp"] = [[round((p - t) / (1 - t), 3), w] for p, w in wp if p >= t] or [[0, wp[-1][1]], [1, wp[-1][1]]]
        for s_ in (s1, s2):
            if s_["wp"][0][0] > 0: s_["wp"].insert(0, [0, s_["wp"][0][1]])
            if s_["wp"][-1][0] < 1: s_["wp"].append([1, s_["wp"][-1][1]])
    return s1, s2
for path in sys.argv[1:]:
    d = json.load(open(path)); n = 0
    for k, g in d["glyphs"].items():
        want = PLAN.get(k)
        if not want: continue
        sts = g["strokes"]
        while len([s for s in sts if s["segs"]]) < min(want):
            big = max(sts, key=lambda s: sum(seglen(x) for x in s["segs"]))
            r = split(big)
            if not r: break
            i = sts.index(big); sts[i:i + 1] = list(r); n += 1
    json.dump(d, open(path, "w"), ensure_ascii=False, separators=(",", ":")); print(path, n, "splits")
