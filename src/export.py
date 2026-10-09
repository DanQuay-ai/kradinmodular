"""site data: radicals.json (generator, with statuses) and glyphs.json (every syllable)."""
import json, sys
sys.path.insert(0, "/home/claude/work/gen")
from radicals import build as build_radicals
from compose2 import build
R = build_radicals()
G = build()
VER = "2026-10-09b"
rad = {"_version": VER}
for k, v in R.items():
    rad[k] = {"strokes": v["strokes"], "status": v["status"], "note": ""}
json.dump(rad, open("/home/claude/work/site2/radicals.json", "w"), ensure_ascii=False, separators=(",", ":"))
GH = json.load(open("/home/claude/work/gen/ghost_all.json"))
out = {"_version": VER, "glyphs": {}}
for k, g in G.items():
    out["glyphs"][k] = {"strokes": g["strokes"], "comp": g["comp"], "status": R[k]["status"] if k in R else "composed"}
json.dump(out, open("/home/claude/work/site2/glyphs.json", "w"), ensure_ascii=False, separators=(",", ":"))
# ghosts for every key we show
gh = {k: {"d": GH[k]["d"]} for k in G if k in GH}
json.dump(gh, open("/home/claude/work/site2/radicals-ghost.json", "w"), ensure_ascii=False, separators=(",", ":"))
print(len(rad) - 1, len(out["glyphs"]), len(gh))
