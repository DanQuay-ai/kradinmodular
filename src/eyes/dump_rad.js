const fs = require("fs"), vm = require("vm"), D = "/home/claude/work/site2/";
const store = {}; global.localStorage = { getItem: k => store[k] ?? null, setItem: (k, v) => store[k] = String(v), removeItem: k => delete store[k], key: i => Object.keys(store)[i], get length() { return Object.keys(store).length; } };
global.fetch = async u => ({ json: async () => JSON.parse(fs.readFileSync(D + u, "utf8")) }); global.window = global; global.self = global; global.KR_SCRIPT = "kradin";
for (const f of ["vendor/polygon-clipping.umd.min.js", "twi.js", "stroke.js", "kr.js"]) vm.runInThisContext(fs.readFileSync(D + f, "utf8") + (f === "stroke.js" ? "\nglobalThis.KS = KS;" : ""), { filename: f });
(async () => {
  await KR.load(); const M = await KR.fontmap(); const snap = KR.snapshot();
  const keys = []; for (const r of KR.RAD_ROWS) for (const v of KR.VOW) if (KR.DEF[r + v]) keys.push(r + v);
  const out = { keys, W: {} };
  out.S = {}; for (const W of [40, 115]) { out.S[W] = {}; for (const k of keys) { const polys = []; for (const st of snap[k] || []) for (const s of KS.split(st)) polys.push(KS.polygon(Object.assign({}, s, { wk: 22 / W, wp: undefined }), W)); out.S[W][k] = polys; } }
  for (const W of [40, 115]) { out.W[W] = {}; for (const k of keys) { const polys = []; for (const st of snap[k] || []) for (const s of KS.split(st)) polys.push(KS.polygon(s, W)); out.W[W][k] = polys; } }
  out.pua = {}; M.glyphs.forEach((g, i) => { if (keys.includes(g.k) && out.pua[g.k] === undefined) out.pua[g.k] = 0xE000 + i; });
  out.strokes = Object.fromEntries(keys.map(k => [k, snap[k]]));
  fs.writeFileSync("/tmp/claude-0/rad.json", JSON.stringify(out)); console.log(keys.length, keys.join(" "));
})();
