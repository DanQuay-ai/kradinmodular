/* Kɔradin data layer: glyph definitions + your edits, resolution of composites, statuses,
   exported font snapshots, text shaping and in-browser font generation (needs opentype.js for fonts). */
(function (root) {
  const LS = {
    get(k, d) { try { const v = localStorage.getItem(k); return v ? JSON.parse(v) : d; } catch (e) { return d; } },
    set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); return true; } catch (e) { return false; } }
  };
  const VOW = ["a", "e", "ɛ", "i", "o", "ɔ", "u"];
  const RAD_ROWS = ["", "p", "t", "d", "k", "f", "s", "n", "r"];
  const COMP_ROWS = [["b", "p + bar"], ["kp", "p + bracket"], ["gb", "b + bracket"], ["ky", "t + bar"], ["tw", "t + bar"], ["gy", "d + bar (= j)"], ["dw", "d + bar"],
    ["hy", "s + bar"], ["z", "s + bar"], ["v", "f + bar"], ["hw", "f + bar"], ["l", "r + bar"], ["g", "k + bar"], ["m", "n + bar"], ["h", "vowel + bar"],
    ["y", "mini i + vowel"], ["w", "mini ɔ + vowel"], ["kw", "kɔ + a / e"], ["ny", "ni + vowel (= ni)"], ["my", "ny + bar"]];
  let DEF = null, VER = "", EDIT = {};

  async function load() {
    const d = await fetch("glyphs.json").then(r => r.json());
    DEF = d.glyphs; VER = d._version;
    EDIT = LS.get("kr-edits", {});
    // migrate: a new set of drafts keeps what you approved and parks the rest
    if (LS.get("kr-ver2", "") !== VER) {
      const back = {};
      for (const k in EDIT) if (!EDIT[k].approved) { back[k] = EDIT[k]; delete EDIT[k]; }
      if (Object.keys(back).length) LS.set("kr-edits-backup-" + (LS.get("kr-ver2", "") || "v1"), back);
      LS.set("kr-ver2", VER); save();
    }
    return api;
  }
  const save = () => LS.set("kr-edits", EDIT);
  const clone = o => JSON.parse(JSON.stringify(o));
  const base = k => DEF[k] && DEF[k].type === "alias" ? DEF[k].of : k;
  function rowKeys(rows) { const o = []; for (const r of rows) for (const v of VOW) if (DEF[r + v]) o.push(r + v); return o; }
  const radicalKeys = () => rowKeys(RAD_ROWS);
  const compositeKeys = () => rowKeys(COMP_ROWS.map(r => r[0])).filter(k => DEF[k].type === "composite");
  const allKeys = () => radicalKeys().concat(compositeKeys());

  // effective definition = default + your edits
  function def(k) {
    k = base(k); const d = DEF[k], e = EDIT[k] || {};
    if (!d) return null;
    if (d.type === "radical") return { type: "radical", strokes: e.strokes || d.strokes, status0: d.status };
    return { type: "composite", kind: d.kind, comps: e.comps || d.comps, strokes: e.strokes || d.strokes, status0: d.status };
  }
  function edit(k) { k = base(k); if (!EDIT[k]) { const d = def(k); EDIT[k] = d.type === "radical" ? { strokes: clone(d.strokes) } : { comps: clone(d.comps), strokes: clone(d.strokes) }; } return EDIT[k]; }
  function status(k) { k = base(k); const e = EDIT[k] || {}, d = DEF[k]; if (e.fix) return "fix"; if (e.approved) return "approved"; if (d && d.type === "radical" && d.status === "approved") return "approved"; return "draft"; }
  function setStatus(k, st) { const e = edit(k); e.approved = st === "approved"; e.fix = st === "fix"; save(); }
  // composites built on another composite wait for it (my waits for ny, gb waits for b)
  function blockedBy(k) { const d = def(k); if (!d || d.type !== "composite") return []; return d.comps.map(c => c.ref).filter(r => DEF[r].type === "composite" && status(r) !== "approved"); }
  // resolved strokes: locked component strokes first (role base), then the glyph's own strokes
  function resolve(k, depth = 0) {
    const d = def(k); if (!d) return [];
    if (d.type === "radical") return d.strokes.map(s => Object.assign({}, s, { role: s.role === "modifier" ? "modifier" : "radical" }));
    const out = [];
    for (const c of d.comps) for (const s of resolve(c.ref, depth + 1)) out.push(Object.assign(KS.place(s, c), { role: depth ? s.role : "base", locked: true, from: c.ref }));
    for (const s of d.strokes) out.push(Object.assign({}, s, { role: depth ? "base" : (s.role || "modifier"), locked: !!depth }));
    return out;
  }
  function progress() { const ks = allKeys(); const ok = ks.filter(k => status(k) === "approved").length; return { ok, total: ks.length, all: ok === ks.length }; }

  // ---------------- exported fonts (snapshots of resolved strokes)
  const fonts = () => LS.get("kr-fonts", []);
  function exportFont(name, test) {
    const glyphs = {};
    for (const k of Object.keys(DEF)) glyphs[k] = resolve(k).map(s => ({ x: s.x, y: s.y, h: s.h, segs: s.segs, s: s.s ?? 0, e: s.e ?? 1, cap0: s.cap0, cap1: s.cap1 }));
    const list = fonts();
    const f = { id: "f" + Date.now().toString(36), name: name || ("Kɔradin build " + (list.length + 1)), date: new Date().toISOString(), test: !!test, glyphs };
    list.push(f);
    if (!LS.set("kr-fonts", list)) { list.pop(); throw new Error("Browser storage is full: delete an older build first."); }
    return f;
  }
  function deleteFont(id) { LS.set("kr-fonts", fonts().filter(f => f.id !== id)); }

  // ---------------- shaping: Latin -> glyph names (the source font's ligatures and prefix rule)
  let MAP = null;
  async function fontmap() { if (!MAP) { MAP = await fetch("fontmap.json").then(r => r.json()); MAP.lig = new Map(MAP.liga.map(([seq, g]) => [seq.join("|"), g])); MAP.idx = new Map(MAP.glyphs.map((g, i) => [g.n, i])); } return MAP; }
  function shape(text) {
    const s = TwiScript.toKradin(text), out = [];
    let names = [];
    const flush = () => {
      // ligatures: longest match first (3, then 2 glyphs)
      const res = [];
      for (let i = 0; i < names.length;) {
        let hit = null;
        for (const L of [3, 2]) { if (i + L > names.length) continue; const g = MAP.lig.get(names.slice(i, i + L).join("|")); if (g) { hit = [g, L]; break; } }
        if (hit) { res.push(hit[0]); i += hit[1]; } else { res.push(names[i]); i++; }
      }
      // prefix rule: m / n / ng not preceded by a letter become prefix marks
      res.forEach((g, i) => { if (["m", "n", "ng.liga"].includes(g) && (i === 0)) res[i] = g === "ng.liga" ? "ng.pre" : g + ".pre"; });
      out.push(...res.map(g => ({ g }))); names = [];
    };
    for (const ch of s) {
      const g = MAP.cmap[ch];
      if (g && g !== "space") names.push(g); else { flush(); out.push({ ch }); }
    }
    flush();
    return out.map(o => o.g ? String.fromCodePoint(0xE000 + MAP.idx.get(o.g)) : o.ch).join("");
  }

  // ---------------- font generation (opentype.js)
  function svgToPath(d, P, dx) {
    const t = d.match(/[MLHVQCZ]|-?\d*\.?\d+(?:e-?\d+)?/gi) || []; let i = 0, c = "", x = 0, y = 0;
    const n = () => +t[i++];
    while (i < t.length) {
      if (/[A-Za-z]/.test(t[i])) c = t[i++].toUpperCase();
      if (c === "M") { x = n(); y = n(); P.moveTo(x + dx, y); c = "L"; }
      else if (c === "L") { x = n(); y = n(); P.lineTo(x + dx, y); }
      else if (c === "H") { x = n(); P.lineTo(x + dx, y); }
      else if (c === "V") { y = n(); P.lineTo(x + dx, y); }
      else if (c === "Q") { const a = n(), b = n(); x = n(); y = n(); P.quadraticCurveTo(a + dx, b, x + dx, y); }
      else if (c === "C") { const a = n(), b = n(), e = n(), f = n(); x = n(); y = n(); P.curveTo(a + dx, b, e + dx, f, x + dx, y); }
      else if (c === "Z") { P.close(); }
      else i++;
    }
  }
  function buildFont(snapshot, W, wdth, slnt, family) {
    const SB = 50, t = Math.tan((-slnt || 0) * Math.PI / 180), xs = (wdth || 100) / 100;
    const tf = (x, y) => [x * xs + (y - 350) * t, y];
    const glyphs = [new opentype.Glyph({ name: ".notdef", unicode: 0, advanceWidth: 500, path: new opentype.Path() }),
      new opentype.Glyph({ name: "space", unicode: 32, advanceWidth: 300, path: new opentype.Path() })];
    MAP.glyphs.forEach((g, i) => {
      const P = new opentype.Path(); let adv;
      if (g.k && snapshot[g.k]) {
        const polys = snapshot[g.k].map(s => KS.polygon(s, W, tf));
        const un = snapshot[g.k].map(s => KS.polygon(s, W, (x, y) => [x * xs, y]));
        let x0 = 1e9, x1 = -1e9; un.forEach(p => p.forEach(([x]) => { x0 = Math.min(x0, x); x1 = Math.max(x1, x); }));
        if (!isFinite(x0)) { x0 = 0; x1 = 300; }
        for (const poly of polys) { poly.forEach(([x, y], j) => j ? P.lineTo(x - x0 + SB, y) : P.moveTo(x - x0 + SB, y)); P.close(); }
        adv = Math.round(x1 - x0 + 2 * SB);
      } else if (g.d !== undefined) { svgToPath(g.d, P, 0); adv = g.adv || 300; if (g.n.endsWith(".pre")) { svgToPath("", P, 0); } }
      else adv = 300;
      if (g.n.endsWith(".pre")) { // prefix marks: draw them as spacing glyphs right before the syllable
        const bb = P.getBoundingBox(); const P2 = new opentype.Path(); svgToPath(g.d, P2, -bb.x1 + 30); adv = Math.round(bb.x2 - bb.x1 + 60);
        glyphs.push(new opentype.Glyph({ name: g.n.replace(/\W/g, "_") + "_" + i, unicode: 0xE000 + i, advanceWidth: adv, path: P2 })); return;
      }
      glyphs.push(new opentype.Glyph({ name: g.n.replace(/\W/g, "_") + "_" + i, unicode: 0xE000 + i, advanceWidth: adv, path: P }));
    });
    return new opentype.Font({ familyName: family, styleName: "Regular", unitsPerEm: 1000, ascender: 900, descender: -250, glyphs });
  }
  async function fontFace(snapshot, W, wdth, slnt, family) {
    await fontmap();
    const f = buildFont(snapshot, W, wdth, slnt, family);
    const ff = new FontFace(family, f.toArrayBuffer());
    await ff.load(); document.fonts.add(ff); return ff;
  }

  const api = { load, save, def, edit, status, setStatus, blockedBy, resolve, progress, radicalKeys, compositeKeys, allKeys, fonts, exportFont, deleteFont,
    fontmap, shape, buildFont, fontFace, VOW, RAD_ROWS, COMP_ROWS, get DEF() { return DEF; }, get EDIT() { return EDIT; }, clone, base };
  root.KR = api;
})(typeof globalThis !== "undefined" ? globalThis : this);
