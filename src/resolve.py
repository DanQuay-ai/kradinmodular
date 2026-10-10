import json, sys
sys.path.insert(0, "/home/claude/work/gen")
from ks import move, scale, rev
D = json.load(open("/home/claude/work/site2/glyphs.json"))["glyphs"]
def resolve(k, depth=0):
    d = D[k]
    if d["type"] == "alias": return resolve(d["of"], depth)
    if d["type"] == "radical": return [dict(s, role=s.get("role", "radical")) for s in d["strokes"]]
    out = []
    for ci, c in enumerate(d["comps"]):
        src = [dict(s) for s in resolve(c["ref"], depth + 1)]
        for e in d.get("exts", []):
            if e["c"] == ci and e["i"] < len(src):
                s = src[e["i"]]
                if e["at"] == "start": s = rev(s)
                src[e["i"]] = dict(s, segs=s["segs"] + e["segs"], role="extended")
        for s in src: out.append(dict(move(scale(s, c.get("s", 1)), c.get("dx", 0), c.get("dy", 0)), role=s.get("role") if depth else ("extended" if s.get("role") == "extended" else "base")))
    for s in d["strokes"]: out.append(dict(s, role=s.get("role", "modifier")))
    return out
