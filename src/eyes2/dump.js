// dump every radical's strokes at two weights: centrelines (scaled into the body) and stroke polygons
const fs = require("fs"), vm = require("vm"), D = "/home/claude/work/site2/";
const store = {}; global.localStorage = { getItem: k => store[k] ?? null, setItem: (k, v) => store[k] = String(v), removeItem: k => delete store[k], key: i => Object.keys(store)[i], get length() { return Object.keys(store).length; } };
global.fetch = async u => ({ json: async () => JSON.parse(fs.readFileSync(D + u, "utf8")) }); global.window = global; global.self = global; global.KR_SCRIPT = "kradin";
for (const f of ["vendor/polygon-clipping.umd.min.js", "twi.js", "stroke.js", "kr.js"]) vm.runInThisContext(fs.readFileSync(D + f, "utf8") + (f === "stroke.js" ? "\nglobalThis.KS = KS;" : ""), { filename: f });
const WS = (process.argv[2] || "40,140").split(",").map(Number);
const OVR = process.argv[4] ? JSON.parse(fs.readFileSync(process.argv[4], "utf8")) : null;
(async () => {
  await KR.load(); const M = await KR.fontmap(); const snap = KR.snapshot();
  if (OVR) for (const k in OVR) snap[k] = OVR[k];
  const keys = []; for (const r of KR.RAD_ROWS) for (const v of KR.VOW) if (KR.DEF[r + v]) keys.push(r + v);
  const out = { keys, WS, G: {}, pua: {} };
  M.glyphs.forEach((g, i) => { if (keys.includes(g.k) && out.pua[g.k] === undefined) out.pua[g.k] = 0xE000 + i; });
  for (const k of keys) {
    out.G[k] = {};
    for (const W of WS) {
      const kk = KS.K(W), strokes = [];
      for (const st of snap[k] || []) for (const s of KS.split(st)) {
        const P = KS.trimCL(KS.centreline(s), s.s ?? 0, s.e ?? 1).map(p => [p[0] * kk, 350 + (p[1] - 350) * kk]);
        strokes.push({ cl: P, poly: KS.polygon(s, W), wk: s.wk || 1, segs: s.segs, h: s.h });
      }
      out.G[k][W] = strokes; out.T = out.T || {}; out.T[k] = snap[k];
    }
  }
  fs.writeFileSync(process.argv[3] || "/tmp/claude-0/rad2.json", JSON.stringify(out)); console.log(keys.length);
})();
