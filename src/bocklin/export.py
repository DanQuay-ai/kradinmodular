import json, sys, importlib, core
fam = sys.argv[1] if len(sys.argv) > 1 else 'bocklin'
lower = importlib.import_module({'bocklin': 'lower', 'eckmann': 'eck_lower'}[fam]); upper = importlib.import_module({'bocklin': 'upper', 'eckmann': 'eck_upper'}[fam])
d = json.load(open(f'/home/claude/work/site2/latin/{fam}.json'))
G = {}; G.update(upper.build()); G.update(lower.build())
old = d["glyphs"]; new = {}
for k, g in old.items():
    if k in G: new[k] = {"type": "radical", "group": g.get("group", "upper" if k.isupper() else "lower"), "strokes": G[k]}
    elif k in ("Ɛ", "ɛ", "Ɔ", "ɔ"): pass
    else: new[k] = g
# open vowels from C / c, mirrored; Ɛ from a reversed C is left to the old trace
def mirror(strokes, cx):
    out = []
    for st in strokes:
        s = dict(st, x=2 * cx - st["x"], h=(180 - st["h"]) % 360, segs=[dict(g, ang=-g["ang"]) if "ang" in g else dict(g) for g in st["segs"]])
        out.append(s)
    return out
new["Ɔ"] = {"type": "radical", "group": "upper", "strokes": mirror(G["C"], 300)}
new["ɔ"] = {"type": "radical", "group": "lower", "strokes": mirror(G["c"], 190)}
for k in ("Ɛ", "ɛ"):
    if k in old: new[k] = old[k]
d["glyphs"] = new; d["metrics"]["W"] = core.W; d["_version"] = fam + "-hand-1"
json.dump(d, open(f'/home/claude/work/site2/latin/{fam}.json', 'w'), ensure_ascii=False)
print(len(new), "glyphs")
