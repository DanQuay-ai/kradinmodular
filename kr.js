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
    ["y", "mini i + vowel"], ["w", "mini ɔ + vowel"], ["kw", "kɔ + a / e"], ["ny", "ni + vowel (= ni)"], ["my", "mi + vowel"]];
  const OTHER = [["Numbers", ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]],
    ["Nasal marks", ["m.pre", "n.pre", "ng.pre", "m", "n", "ng"]], ["Punctuation", ["period", "comma", "exclam", "question"]],
    ["Standalone consonants", ["b", "c", "d", "f", "g", "h", "j", "k", "l", "p", "q", "r", "s", "t", "v", "w", "y", "z"]]];
  const LABEL = { zero: "0", one: "1", two: "2", three: "3", four: "4", five: "5", six: "6", seven: "7", eight: "8", nine: "9", period: ".", comma: ",", exclam: "!", question: "?",
    "m.pre": "m-", "n.pre": "n-", "ng.pre": "ŋ-", m: "-m", n: "-n", ng: "-ŋ" };
  const label = k => k.startsWith("@") ? (LABEL[k.slice(1)] || k.slice(1)) : k;
  let DEF = null, VER = "", EDIT = {};

  async function load() {
    const d = await fetch("glyphs.json").then(r => r.json());
    DEF = d.glyphs; VER = d._version;
    EDIT = LS.get("kr-edits", {});
    // a new set of glyphs: your edits so far are baked into it, so park them in a backup and start clean
    if (LS.get("kr-ver2", "") !== VER) {
      if (Object.keys(EDIT).length) LS.set("kr-edits-backup-" + (LS.get("kr-ver2", "") || "v1"), EDIT);
      EDIT = {}; LS.set("kr-ver2", VER); save();
    }
    return api;
  }
  const save = () => LS.set("kr-edits", EDIT);
  const clone = o => JSON.parse(JSON.stringify(o));
  const base = k => DEF[k] && DEF[k].type === "alias" ? DEF[k].of : k;
  function rowKeys(rows) { const o = []; for (const r of rows) for (const v of VOW) if (DEF[r + v]) o.push(r + v); return o; }
  const radicalKeys = () => rowKeys(RAD_ROWS);
  const compositeKeys = () => rowKeys(COMP_ROWS.map(r => r[0])).filter(k => DEF[k].type === "composite");
  const otherKeys = () => OTHER.flatMap(([, ks]) => ks.map(k => "@" + k)).filter(k => DEF[k]);
  const allKeys = () => radicalKeys().concat(compositeKeys(), otherKeys());
  const deleted = k => !!(EDIT[base(k)] || {}).deleted;
  const liveKeys = () => allKeys().filter(k => !deleted(k));

  // effective definition = default + your edits. Unlocked composites keep their own copy of every stroke.
  function def(k) {
    k = base(k); const d = DEF[k], e = EDIT[k] || {};
    if (!d) return null;
    if (d.type === "radical") return { type: "radical", strokes: e.strokes || d.strokes };
    if (e.detached) return { type: "composite", kind: d.kind, detached: true, comps: [], strokes: e.strokes, exts: [], wait: [] };
    return { type: "composite", kind: d.kind, comps: e.comps || d.comps, strokes: e.strokes || d.strokes, exts: e.exts || d.exts || [], wait: d.wait || [] };
  }
  function edit(k) {
    k = base(k);
    if (!EDIT[k] || (!EDIT[k].strokes && !EDIT[k].detached)) {
      const d = def(k), keep = EDIT[k] || {};
      EDIT[k] = Object.assign(keep, d.type === "radical" ? { strokes: clone(d.strokes) } : { comps: clone(d.comps), strokes: clone(d.strokes), exts: clone(d.exts) });
    }
    return EDIT[k];
  }
  function status(k) { k = base(k); const e = EDIT[k] || {}, d = DEF[k]; if (e.fix) return "fix"; if (e.approved) return "approved"; if (e.approved === false) return "draft"; return d && d.status === "approved" ? "approved" : d && d.status === "fix" ? "fix" : "draft"; }
  function setStatus(k, st) { k = base(k); EDIT[k] = EDIT[k] || {}; EDIT[k].approved = st === "approved"; EDIT[k].fix = st === "fix"; save(); }
  function setDeleted(k, on) { k = base(k); EDIT[k] = EDIT[k] || {}; EDIT[k].deleted = !!on; save(); }
  function unlock(k) { k = base(k); const st = resolve(k).map(s => { const c = Object.assign({}, s); delete c.locked; delete c.from; delete c.ext; return c; }); const e = EDIT[k] || {}; EDIT[k] = { detached: true, strokes: st, approved: e.approved, fix: e.fix, note: e.note }; save(); }
  function relock(k) { k = base(k); const e = EDIT[k] || {}; EDIT[k] = { approved: e.approved, fix: e.fix, note: e.note }; save(); }
  // a composite waits for the composite glyphs it is built on (gb for b, my for mi) and for its listed waits (my for ny)
  function blockedBy(k) {
    const d = def(k); if (!d || d.type !== "composite" || d.detached) return [];
    const refs = d.comps.map(c => c.ref).filter(r => DEF[r] && DEF[r].type === "composite").concat(d.wait || []);
    return [...new Set(refs)].filter(r => status(r) !== "approved");
  }
  function reverse(st) {
    const t = KS.trace(st);
    return Object.assign({}, st, { x: t.x, y: t.y, h: ((t.h + 180) % 360 + 360) % 360, segs: st.segs.slice().reverse().map(q => "ang" in q ? Object.assign({}, q, { ang: -q.ang }) : Object.assign({}, q)), cap0: st.cap1, cap1: st.cap0 });
  }
  // resolved strokes: locked component strokes first (extensions continue them), then the glyph's own strokes
  function resolve(k, depth = 0) {
    const d = def(k); if (!d) return [];
    if (d.type === "radical") return d.strokes.map(s => Object.assign({}, s, { role: s.role || "radical" }));
    const out = [];
    d.comps.forEach((c, ci) => {
      const src = resolve(c.ref, depth + 1).map(s => Object.assign({}, s));
      (d.exts || []).forEach((e, ei) => {
        if (e.c !== ci || !src[e.i]) return;
        let s = src[e.i]; if (e.at === "start") s = reverse(s);
        src[e.i] = Object.assign({}, s, { segs: s.segs.concat(e.segs), ext: depth ? undefined : { ei, n: s.segs.length } });
      });
      for (const s of src) out.push(Object.assign(KS.place(s, c), { role: depth ? s.role : (s.ext ? "extended" : "base"), locked: true, from: c.ref }));
    });
    for (const s of d.strokes) out.push(Object.assign({}, s, { role: depth ? "base" : (s.role || "modifier"), locked: !!depth }));
    return out;
  }
  function progress() { const ks = liveKeys(); const ok = ks.filter(k => status(k) === "approved").length; return { ok, total: ks.length, all: ok === ks.length }; }

  // ---------------- exported fonts (snapshots of resolved strokes; deleted glyphs are left out)
  const fonts = () => LS.get("kr-fonts", []);
  function snapshot() {
    const glyphs = {};
    for (const k of Object.keys(DEF)) { if (deleted(k)) continue; glyphs[k] = resolve(k).map(s => ({ x: s.x, y: s.y, h: s.h, segs: s.segs, s: s.s ?? 0, e: s.e ?? 1, cap0: s.cap0, cap1: s.cap1 })); }
    return glyphs;
  }
  function exportFont(name, test) {
    const list = fonts();
    const f = { id: "f" + Date.now().toString(36), name: name || ("Kɔradin build " + (list.length + 1)), date: new Date().toISOString(), test: !!test, glyphs: snapshot() };
    list.push(f);
    if (!LS.set("kr-fonts", list)) { list.pop(); throw new Error("Browser storage is full: delete an older build first."); }
    return f;
  }
  function deleteFont(id) { LS.set("kr-fonts", fonts().filter(f => f.id !== id)); }

  // ---------------- shaping: Latin -> glyph names (the source font's ligatures and prefix rule)
  let MAP = null;
  async function fontmap() { if (!MAP) { MAP = await fetch("fontmap.json").then(r => r.json()); MAP.lig = new Map(MAP.liga.map(([seq, g]) => [seq.join("|"), g])); MAP.idx = new Map(MAP.glyphs.map((g, i) => [g.n, i])); MAP.key = new Map(MAP.glyphs.map(g => [g.n, g.k])); } return MAP; }
  // has: set of glyph keys present in the font (deleted glyphs fall back to plain text)
  function shape(text, has) {
    const s = TwiScript.toKradin(text), out = [];
    let names = [];
    const flush = () => {
      const res = [];
      for (let i = 0; i < names.length;) {
        let hit = null;
        for (const L of [3, 2]) { if (i + L > names.length) continue; const g = MAP.lig.get(names.slice(i, i + L).map(n => n.g).join("|")); if (g) { hit = [g, L]; break; } }
        if (hit) { res.push({ g: hit[0], src: names.slice(i, i + hit[1]).map(n => n.ch).join("") }); i += hit[1]; } else { res.push(names[i]); i++; }
      }
      res.forEach((r, i) => { if (["m", "n", "ng.liga"].includes(r.g) && i === 0) r.g = r.g === "ng.liga" ? "ng.pre" : r.g + ".pre"; });
      out.push(...res); names = [];
    };
    for (const ch of s) { const g = MAP.cmap[ch]; if (g && g !== "space") names.push({ g, ch }); else { flush(); out.push({ ch }); } }
    flush();
    return out.map(o => { if (!o.g) return o.ch; const k = MAP.key.get(o.g); if (k && has && !has.has(k)) return o.src || o.ch; return String.fromCodePoint(0xE000 + MAP.idx.get(o.g)); }).join("");
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
  // style: "regular" (uniform stroke) or "tapered" (brush logic: thin horizontals, thick verticals, decorated ends)
  function buildFont(snapshot, W, wdth, slnt, family, style) {
    const SB = 50, t = Math.tan((-slnt || 0) * Math.PI / 180), xs = (wdth || 100) / 100;
    const tf = (x, y) => [x * xs + (y - 350) * t, y];
    const poly = style === "tapered" ? KS.polygonTapered : KS.polygon;
    const glyphs = [new opentype.Glyph({ name: ".notdef", unicode: 0, advanceWidth: 500, path: new opentype.Path() }),
      new opentype.Glyph({ name: "space", unicode: 32, advanceWidth: 300, path: new opentype.Path() })];
    MAP.glyphs.forEach((g, i) => {
      if (!g.k || !snapshot[g.k]) return;
      const P = new opentype.Path();
      const polys = snapshot[g.k].map(s => poly(s, W, tf));
      const un = snapshot[g.k].map(s => poly(s, W, (x, y) => [x * xs, y]));
      let x0 = 1e9, x1 = -1e9; un.forEach(p => p.forEach(([x]) => { x0 = Math.min(x0, x); x1 = Math.max(x1, x); }));
      if (!isFinite(x0)) { x0 = 0; x1 = 300; }
      for (const pg of polys) { if (pg.length < 3) continue; pg.forEach(([x, y], j) => j ? P.lineTo(x - x0 + SB, y) : P.moveTo(x - x0 + SB, y)); P.close(); }
      glyphs.push(new opentype.Glyph({ name: g.n.replace(/\W/g, "_") + "_" + i, unicode: 0xE000 + i, advanceWidth: Math.round(x1 - x0 + 2 * SB), path: P }));
    });
    return new opentype.Font({ familyName: family, styleName: "Regular", unitsPerEm: 1000, ascender: 900, descender: -250, glyphs });
  }
  async function fontFace(snapshot, W, wdth, slnt, family, style) {
    await fontmap();
    const f = buildFont(snapshot, W, wdth, slnt, family, style);
    const ff = new FontFace(family, f.toArrayBuffer());
    await ff.load(); document.fonts.add(ff); return ff;
  }

  const api = { load, save, def, edit, status, setStatus, setDeleted, deleted, unlock, relock, blockedBy, resolve, progress, radicalKeys, compositeKeys, otherKeys, allKeys, liveKeys,
    fonts, exportFont, deleteFont, snapshot, fontmap, shape, buildFont, fontFace, label, VOW, RAD_ROWS, COMP_ROWS, OTHER,
    get DEF() { return DEF; }, get EDIT() { return EDIT; }, clone, base };
  root.KR = api;
})(typeof globalThis !== "undefined" ? globalThis : this);
