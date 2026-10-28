import sys, core
from shapely.geometry import LineString
def iv(g, line):
    x = g.intersection(line); out = []
    for p in (x.geoms if hasattr(x, "geoms") else [x]):
        if p.is_empty or p.geom_type != "LineString": continue
        c = list(p.coords); out.append((round(c[0][0]), round(c[-1][0])) if line.coords[0][1] == line.coords[1][1] else (round(c[0][1]), round(c[-1][1])))
    return sorted(out)
for ch in sys.argv[1]:
    g, adv = core.ref_shape(ch); b = g.bounds
    print(f"== {ch} adv {adv:.0f} bounds {[round(v) for v in b]}")
    ys = [int(v) for v in sys.argv[2].split(",")] if len(sys.argv) > 2 else [5, 30, 60, 120, 200, 260, 330, 400, 450, 490, 540, 600, 650, 690]
    for y in ys:
        if b[1] <= y <= b[3]: print(f" y{y:4d}:", iv(g, LineString([(-200, y), (1200, y)])))
    for x in range(int(b[0]) + 10, int(b[2]), 40): print(f" x{x:4d}:", iv(g, LineString([(x, -300), (x, 900)])))
