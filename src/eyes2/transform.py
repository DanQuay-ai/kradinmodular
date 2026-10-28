"""Skeleton pass for Kɔradin Eyes (both masters share it):
 1. spirals re-spaced: successive turns at least SPACE apart (room for two Black strokes + the gap),
    the innermost turn dropped when the turns no longer fit;
 2. every arc of 85 degrees or more becomes line-arc-line (its tangent polygon with a small corner radius),
    split in quarter-ish pieces: semicircles become rounded U's, rings rounded squares, spirals
    arc-line-arc-line. Junction points and end headings stay where they were."""
import json, math, sys
SPACE = 207          # design units: (140 + 52) / K(140) = 192 / 0.930

def rc_of(r): return min(r, max(45.0, min(110.0, 0.42 * r)))

def square_arc(g):
    r, ang = g["r"], g["ang"]; th = abs(ang)
    if th < 85 or r <= 46: return [g]
    n = int(round(th / 90))
    if abs(th - 90 * n) > 6: return [g]           # only right-angle turns get squared (a 210 or 150 stays round)
    piece = ang / n; rc = rc_of(r)
    a = (r - rc) * math.tan(math.radians(abs(piece)) / 2)
    out = []
    for _ in range(n):
        if a > 0.5: out.append({"t": "L", "len": round(a, 2)})
        out.append({"t": "A", "r": round(rc, 2), "ang": round(piece, 2)})
        if a > 0.5: out.append({"t": "L", "len": round(a, 2)})
    return out

def merge_lines(segs):
    out = []
    for g in segs:
        if g["t"] == "L" and out and out[-1]["t"] == "L": out[-1] = {"t": "L", "len": round(out[-1]["len"] + g["len"], 2)}
        else: out.append(dict(g))
    return out

def respace(segs):
    """runs of >= 2 consecutive same-sign arcs of >= 150 deg (a spiral): radii from the outside in, each turn
    SPACE/2 tighter than the one before (so same-side arms sit SPACE apart, opposite arms too); a turn that
    would get smaller than SPACE/2 is dropped"""
    out, i = [], 0
    while i < len(segs):
        g = segs[i]
        if g["t"] == "A" and abs(g["ang"]) >= 150:
            j = i
            while j + 1 < len(segs) and segs[j + 1]["t"] == "A" and abs(segs[j + 1]["ang"]) >= 150 and segs[j + 1]["ang"] * g["ang"] > 0: j += 1
            if j > i:
                run = segs[i:j + 1]; r = run[0]["r"]; new = [dict(run[0])]
                for h in run[1:]:
                    r2 = min(h["r"], r - SPACE / 2)
                    if r2 < SPACE / 2:
                        if h is run[1]: r2 = SPACE / 2      # keep at least one inner turn, at the minimum size
                        else: break
                    new.append(dict(h, r=round(r2, 2))); r = r2
                out += new; i = j + 1; continue
        out.append(g); i += 1
    return out

def polyline(st, W=40):
    import anatomy
    pts = [p for _, _, P, _ in anatomy.trace(st, W) for p in P]
    return pts

def signature(strokes, W=40):
    """what must not change: which strokes touch, how many parts, how many closed counters, inside the body"""
    from shapely.geometry import LineString
    from shapely.ops import unary_union
    L = [LineString(polyline(st)) for st in strokes if len(polyline(st)) >= 2]
    B = [l.buffer(W / 2) for l in L]
    touch = tuple((i, j) for i in range(len(B)) for j in range(i + 1, len(B)) if B[i].intersects(B[j]))
    U = unary_union(B); parts = list(U.geoms) if hasattr(U, "geoms") else [U]
    holes = sum(len(p.interiors) for p in parts)
    ys = [y for l in L for x, y in l.coords]
    inside = min(ys) > -60 and max(ys) < 760
    return touch, len(parts), holes, inside

def open_hairpins(strokes):
    """U-turns (arcs of 150+ degrees) whose two arms sit closer than SPACE get a bigger radius, when that
    keeps every junction, part and counter (checked on the Thin skeleton)"""
    base = signature(strokes)
    for si, st in enumerate(strokes):
        for gi, g in enumerate(st["segs"]):
            if g["t"] != "A" or abs(g["ang"]) < 150 or g["r"] >= SPACE / 2 or abs(g["ang"]) >= 330: continue
            for r in (SPACE / 2, SPACE * 0.45, SPACE * 0.4):
                if r <= g["r"]: break
                trial = [dict(s, segs=[dict(h) for h in s["segs"]]) for s in strokes]
                trial[si]["segs"][gi]["r"] = round(r, 2)
                if signature(trial) == base: strokes = trial; break
    return strokes

def transform(strokes):
    res = []
    strokes = open_hairpins([dict(st, segs=respace(st["segs"])) for st in strokes])
    for st in strokes:
        segs = st["segs"]
        sq = []
        for g in segs: sq += square_arc(g) if g["t"] == "A" else [g]
        res.append(dict(st, segs=merge_lines(sq)))
    return res

if __name__ == "__main__":
    d = json.load(open(sys.argv[1]))
    out = {k: transform(v) for k, v in d["strokes"].items()}
    json.dump(out, open(sys.argv[2], "w"))
    for k in ("o", "ɔ", "dɔ", "fɔ"): print(k, [(g["t"], g.get("len") or (g.get("r"), g.get("ang"))) for st in out[k] for g in st["segs"]][:14])
