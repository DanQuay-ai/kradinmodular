/* Kɔradin data layer: glyph definitions + your edits, resolution of composites, statuses,
   exported font snapshots, text shaping and in-browser font generation (needs opentype.js for fonts). */
(function (root) {
 function make(SCRIPT) {
  const AD = SCRIPT === "adinkra", LAT = SCRIPT.startsWith("latin:"), LID = LAT ? SCRIPT.slice(6) : "";
  const P0 = AD ? "ad-" : LAT ? "lt-" + LID + "-" : "kr-";
  let BODYDEF = null; // Latin: baseline 0, cap height 700, glyphs keep their position as the weight changes
  // studio projects: each named font keeps its own edits, builds and styles under its own prefix
  const PROJ = (() => { try { return JSON.parse(localStorage.getItem("studio-cur-" + P0)) || ""; } catch (e) { return ""; } })();
  const P = P0 + (PROJ ? PROJ + "-" : "");
  const LS = {
    get(k, d) { try { const v = localStorage.getItem(k); return v ? JSON.parse(v) : d; } catch (e) { return d; } },
    set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); return true; } catch (e) { return false; } }
  };
  const VOW = LAT ? [] : AD ? ["a", "b", "d", "e", "ɛ", "f", "g", "h", "i", "k", "l", "m", "n", "o", "ɔ", "p", "r", "s", "t", "u", "w", "y", "c", "j", "q", "v", "x", "z"] : ["a", "e", "ɛ", "i", "o", "ɔ", "u"];
  const RAD_ROWS = AD || LAT ? [""] : ["", "p", "t", "d", "k", "f", "s", "n", "r"];
  const FIRST_ROW = AD || LAT ? "Letters" : "Vowels";
  const COMP_ROWS = AD || LAT ? [] : [["b", "p + bar"], ["kp", "p + bracket"], ["gb", "b + bracket"], ["ky", "t + bar"], ["tw", "t + bar"], ["gy", "d + bar (= j)"], ["dw", "d + bar"],
    ["hy", "s + bar"], ["z", "s + bar"], ["v", "f + bar"], ["hw", "f + bar"], ["l", "r + bar"], ["g", "k + bar"], ["m", "n + bar"], ["h", "vowel + bar"],
    ["y", "mini i + vowel"], ["w", "mini ɔ + vowel"], ["kw", "kɔ + a / e"], ["ny", "ni + vowel (= ni)"], ["my", "mi + vowel"]];
  const OTHER = LAT ? [["Punctuation", ["period", "comma", "hyphen", "exclam", "question", "quote"]]] : AD ? [["Punctuation", ["period", "comma", "hyphen", "exclam", "question"]]] : [["Numbers", ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]],
    ["Nasal marks", ["m.pre", "n.pre", "ng.pre", "m", "n", "ng"]], ["Punctuation", ["period", "comma", "exclam", "question"]],
    ["Standalone consonants", ["b", "c", "d", "f", "g", "h", "j", "k", "l", "p", "q", "r", "s", "t", "v", "w", "y", "z"]]];
  const LABEL = { zero: "0", one: "1", two: "2", three: "3", four: "4", five: "5", six: "6", seven: "7", eight: "8", nine: "9", period: ".", comma: ",", exclam: "!", question: "?",
    "m.pre": "m-", "n.pre": "n-", "ng.pre": "ŋ-", m: "-m", n: "-n", ng: "-ŋ", hyphen: "-" };
  const label = k => k.startsWith("@") ? (LABEL[k.slice(1)] || k.slice(1)) : k;
  let DEF = null, VER = "", EDIT = {};

  const META = { name: "", W: 98 };
  const useBody = () => (BODYDEF ? KS.setBody(BODYDEF) : KS.setBody());
  async function load() {
    const d = await fetch(AD ? "adinkra.json" : LAT ? "latin/" + LID + ".json" : "glyphs.json").then(r => r.json());
    if (LAT) {
      const m = d.metrics; META.name = d.name; META.W = m.W;
      BODYDEF = { fixed: true, cuts: [m.desc, 0, m.x, 700, m.asc], cutTol: m.W * 1.2, lo: m.desc - 40, hi: Math.max(m.asc, 760) + 40, lines: [["desc", m.desc], ["base", 0], ["x-height", m.x], ["cap", 700], ["asc", m.asc]] };
      const rank = k => /^[A-ZƐƆ]$/.test(k) ? 0 : /^\d$/.test(k) ? 2 : 1;
      VOW.length = 0; Object.keys(d.glyphs).filter(k => !k.startsWith("@")).sort((a, b) => rank(a) - rank(b)).forEach(k => VOW.push(k));
    }
    DEF = d.glyphs; VER = d._version;
    EDIT = LS.get(P + "edits", {});
    if (PROJ && LS.get(P + "fresh", false)) { EDIT = {}; LS.set(P + "fresh", false); save(); }
    // a new set of glyphs: your edits so far are baked into it, so park them in a backup and start clean
    const VK = (AD ? "ad-ver" : LAT ? P0 + "ver" : "kr-ver2") + (PROJ ? "-" + PROJ : "");
    if (LS.get(VK, "") !== VER) {
      if (Object.keys(EDIT).length) LS.set(P + "edits-backup-" + (LS.get(VK, "") || "v1"), EDIT);
      EDIT = {}; LS.set(VK, VER); save();
    }
    return api;
  }
  const save = () => LS.set(P + "edits", EDIT);
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
    if (d.detached && !e.comps) return { type: "composite", kind: d.kind, detached: true, comps: [], strokes: e.strokes || d.strokes, exts: [], wait: [] };
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
  const fonts = () => LS.get(P + "fonts", []);
  function snapshot() {
    const glyphs = {};
    for (const k of Object.keys(DEF)) { if (deleted(k)) continue; glyphs[k] = resolve(k).map(s => ({ x: s.x, y: s.y, h: s.h, segs: s.segs, s: s.s ?? 0, e: s.e ?? 1, cap0: s.cap0, cap1: s.cap1 })); }
    return glyphs;
  }
  function exportFont(name, test) {
    const list = fonts();
    const f = { id: "f" + Date.now().toString(36), name: name || ("Kɔradin build " + (list.length + 1)), date: new Date().toISOString(), test: !!test, glyphs: snapshot() };
    list.push(f);
    if (!LS.set(P + "fonts", list)) { list.pop(); throw new Error("Browser storage is full: delete an older build first."); }
    return f;
  }
  function deleteFont(id) { LS.set(P + "fonts", fonts().filter(f => f.id !== id)); }

  // ---------------- shaping: Latin -> glyph names (the source font's ligatures and prefix rule)
  let MAP = null;
  async function fontmap() { if (!MAP) { MAP = await fetch("fontmap.json").then(r => r.json()); MAP.lig = new Map(MAP.liga.map(([seq, g]) => [seq.join("|"), g])); MAP.idx = new Map(MAP.glyphs.map((g, i) => [g.n, i])); MAP.key = new Map(MAP.glyphs.map(g => [g.n, g.k])); } return MAP; }
  // has: set of glyph keys present in the font (deleted glyphs fall back to plain text)
  function shape(text, has, half) {
    const s = TwiScript.toKradin(text.replace(/ŋ/g, "ng").replace(/Ŋ/g, "Ng")), out = [];
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
    // coda nasals (m, n, ŋ after a syllable) are marks centred under the glyph before them (the source font's GPOS rule)
    const H = half && HALF[half];
    let prev = null;
    return out.map(o => {
      if (!o.g) { prev = null; return o.ch; }
      const k = MAP.key.get(o.g); if (k && has && !has.has(k)) { prev = null; return o.src || o.ch; }
      const i = MAP.idx.get(o.g), mi = CODA.indexOf(o.g);
      if (mi >= 0 && H) { const h = prev != null && H.has(prev) ? H.get(prev) : H.get(-1); if (h != null) return String.fromCodePoint(0xF0000 + mi * 0x1000 + h); }
      if (mi < 0) prev = i;
      return String.fromCodePoint(0xE000 + i);
    }).join("");
  }
  const CODA = ["m", "n", "ng.liga"], HALF = {};

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
  // overlapping strokes (and strokes that fold over themselves in tight turns) are merged into one clean
  // shape, so no overlap can cancel out and leave a hole. Needs vendor/polygon-clipping (falls back to raw polygons).
  function merge(polys) {
    const PC = root.polygonClipping; if (!PC) return polys;
    const prep = (q, r) => { const p = q.map(([x, y]) => [Math.round(x * r) / r, Math.round(y * r) / r]).filter((pt, i, a) => !i || pt[0] !== a[i - 1][0] || pt[1] !== a[i - 1][1]); return p.length >= 3 ? [p.concat([p[0]])] : null; };
    const rings = mp => { const out = []; for (const poly of mp) for (const ring of poly) out.push(ring.slice(0, -1)); return out; };
    const hasOver = polys.some(p => p.knock);
    for (const r of [1000, 100, 10]) {          // the library can trip on near-coincident points: retry coarser
      try {
        if (!hasOver) { const g = polys.map(q => q.mp || prep(q, r)).filter(Boolean); return g.length ? rings(PC.union(...g)) : []; }
        let acc = [];
        for (const q of polys) {
          const g = q.mp ? q.mp : prep(q, r); if (!g) continue;
          if (q.knock && acc.length) { const k = prep(q.knock, r); if (k) acc = PC.difference(acc, k); }
          acc = acc.length ? PC.union(acc, g) : [g];
        }
        return rings(acc);
      } catch (e) {}
    }
    // last resort: add the strokes one by one, keeping any that refuse to merge as they are
    let acc = null; const loose = [];
    for (const q of polys) { const g = q.mp || prep(q, 10); if (!g) continue;
      try { acc = acc ? PC.union(acc, g) : [g]; } catch (e) { loose.push(q); } }
    return (acc ? rings(acc) : []).concat(loose);
  }
  // style: "regular" (uniform stroke) or "tapered" (brush logic: thin horizontals, thick verticals, decorated ends)
  function buildFont(snapshot, W, wdth, slnt, family, style) {
    const SB = 50, t = Math.tan((-slnt || 0) * Math.PI / 180), xs = (wdth || 100) / 100;
    const tf = (x, y) => [x * xs + (y - 350) * t, y];
    // style: "regular" | "tapered" | {P, ov} (a rule-based style from styles.js / the Serif lab)
    const rule = style && typeof style === "object" && style.P && typeof KST !== "undefined" ? style : null;
    const poly = style === "tapered" ? KS.polygonTapered : KS.polygon;
    // a stroke marked "over" passes over what was drawn before it with a white halo around it (Böcklin's loops):
    // its halo (the same stroke, wider by 2 x halo) is cut out of the earlier strokes before it is added
    const haloOf = s => { const c = Math.min(0.3, 1.2 * W / (KS.trace(s).len || 1)); return Object.assign({}, s, { over: false, wk: undefined, s: c, e: 1 - c, cap0: "butt", cap1: "butt", wp: (s.wp || [[0, s.wk || 1], [1, s.wk || 1]]).map(([t, w]) => [t, w + 2 * (s.halo ?? 0.16)]) }); }; // ends trimmed: the halo never bites where the stroke joins
    const polysOf = (key, strokes, tfn) => {
      if (rule) return KST.glyph(strokes.flatMap(KS.split), W, tfn, rule.P, (rule.ov || {})[key]);
      const out = [];
      for (const st of strokes) { if (st.loop && st.loop.at > 0) { const mp = KS.selfLoop(st, W, tfn, poly); const p = mp[0][0].slice(0, -1); p.mp = mp; out.push(p); continue; } for (const s of KS.split(st)) { const p = poly(s, W, tfn); if (st.over) p.knock = poly(haloOf(s), W, tfn); out.push(p); } }
      return out;
    };
    const glyphs = [new opentype.Glyph({ name: ".notdef", unicode: 0, advanceWidth: 500, path: new opentype.Path() }),
      new opentype.Glyph({ name: "space", unicode: 32, advanceWidth: 300, path: new opentype.Path() })];
    const prevBody = Object.assign({}, KS.BODY); useBody();
    try { return buildInner(); } finally { KS.setBody(prevBody); }
    function buildInner() {
    if (AD || LAT) { // Adinkra alphabet / Latin: one glyph per letter, on the Latin letters themselves (both cases)
      const PUN = { "@period": ".", "@comma": ",", "@hyphen": "-", "@exclam": "!", "@question": "?", "@quote": "'" };
      Object.keys(snapshot).forEach((k, i) => {
        const ch = PUN[k] || k; if (ch.length !== 1 || !snapshot[k].length) return;
        const P = new opentype.Path(), polys = polysOf(k, snapshot[k], tf), un = polysOf(k, snapshot[k], (x, y) => [x * xs, y]);
        let x0 = 1e9, x1 = -1e9; un.forEach(p => p.forEach(([x]) => { x0 = Math.min(x0, x); x1 = Math.max(x1, x); }));
        if (!isFinite(x0)) { x0 = 0; x1 = 300; }
        for (const pg of merge(polys)) { if (pg.length < 3) continue; pg.forEach(([x, y], j) => j ? P.lineTo(x - x0 + SB, y) : P.moveTo(x - x0 + SB, y)); P.close(); }
        const up = ch.toUpperCase(), adv = Math.round(x1 - x0 + 2 * SB);
        glyphs.push(new opentype.Glyph({ name: "ad" + i, unicode: ch.codePointAt(0), advanceWidth: adv, path: P }));
        if (AD && up !== ch) glyphs.push(new opentype.Glyph({ name: "adU" + i, unicode: up.codePointAt(0), advanceWidth: adv, path: P }));
      });
      return new opentype.Font({ familyName: family, styleName: "Regular", unitsPerEm: 1000, ascender: 900, descender: -250, glyphs });
    }
    const half = new Map(), marks = [];
    MAP.glyphs.forEach((g, i) => {
      if (!g.k || !snapshot[g.k]) return;
      const P = new opentype.Path();
      const polys = polysOf(g.k, snapshot[g.k], tf);
      const un = polysOf(g.k, snapshot[g.k], (x, y) => [x * xs, y]);
      let x0 = 1e9, x1 = -1e9; un.forEach(p => p.forEach(([x]) => { x0 = Math.min(x0, x); x1 = Math.max(x1, x); }));
      if (!isFinite(x0)) { x0 = 0; x1 = 300; }
      for (const pg of merge(polys)) { if (pg.length < 3) continue; pg.forEach(([x, y], j) => j ? P.lineTo(x - x0 + SB, y) : P.moveTo(x - x0 + SB, y)); P.close(); }
      const adv = Math.round(x1 - x0 + 2 * SB);
      if (CODA.includes(g.n)) { marks.push([CODA.indexOf(g.n), g, i, un]); return; }
      half.set(i, Math.round(adv / 2));
      glyphs.push(new opentype.Glyph({ name: g.n.replace(/\W/g, "_") + "_" + i, unicode: 0xE000 + i, advanceWidth: adv, path: P }));
    });
    // coda nasal marks: zero width, one copy per distinct half advance of the glyph they sit under,
    // centred under it, a little under the baseline
    const hs = [...new Set(half.values())]; half.set(-1, hs.length ? hs.sort((a, b) => a - b)[hs.length >> 1] : 200);
    const gap = Math.max(36, 0.55 * W);
    for (const [mi, g, i, un] of marks) {
      let x0 = 1e9, x1 = -1e9, y1 = -1e9; un.forEach(p => p.forEach(([x, y]) => { x0 = Math.min(x0, x); x1 = Math.max(x1, x); y1 = Math.max(y1, y); }));
      if (!isFinite(x0)) continue;
      const cx = (x0 + x1) / 2, dy = -gap - y1;
      for (const h of new Set(half.values())) {
        const P = new opentype.Path();
        for (const pg of un) { if (pg.length < 3) continue; pg.forEach(([x, y], j) => { const Y = y + dy, X = x - cx - h + (Y - 350) * t; j ? P.lineTo(X, Y) : P.moveTo(X, Y); }); P.close(); }
        glyphs.push(new opentype.Glyph({ name: "mark" + mi + "_" + h, unicode: 0xF0000 + mi * 0x1000 + h, advanceWidth: 0, path: P }));
      }
      // plain PUA code keeps a centred fallback
      const P = new opentype.Path(), h = half.get(-1);
      for (const pg of un) { if (pg.length < 3) continue; pg.forEach(([x, y], j) => { const Y = y + dy, X = x - cx - h + (Y - 350) * t; j ? P.lineTo(X, Y) : P.moveTo(X, Y); }); P.close(); }
      glyphs.push(new opentype.Glyph({ name: g.n.replace(/\W/g, "_") + "_" + i, unicode: 0xE000 + i, advanceWidth: 0, path: P }));
    }
    HALF[family] = half;
    return new opentype.Font({ familyName: family, styleName: "Regular", unitsPerEm: 1000, ascender: 900, descender: -250, glyphs });
    }
  }
  async function fontFace(snapshot, W, wdth, slnt, family, style) {
    await fontmap();
    const f = buildFont(snapshot, W, wdth, slnt, family, style);
    const ff = new FontFace(family, f.toArrayBuffer());
    await ff.load(); document.fonts.add(ff); return ff;
  }

  // ---------------- studio
  const projects = () => LS.get("studio-proj-" + P0, []);
  function createProject(name, copy) {
    const id = "p" + Date.now().toString(36), L = projects(); L.push({ id, name: name || "Untitled", date: new Date().toISOString() }); LS.set("studio-proj-" + P0, L);
    const np = P0 + id + "-";
    if (copy) { LS.set(np + "edits", EDIT); LS.set(np + "styles", LS.get(P + "styles", LS.get("kr-styles", []))); }
    else LS.set(np + "fresh", true);
    LS.set((AD ? "ad-ver" : LAT ? P0 + "ver" : "kr-ver2") + "-" + id, VER);
    return id;
  }
  function useProject(id) { LS.set("studio-cur-" + P0, id || ""); }
  function renameProject(id, name) { LS.set("studio-proj-" + P0, projects().map(p => p.id === id ? { ...p, name } : p)); }
  function deleteProject(id) {
    LS.set("studio-proj-" + P0, projects().filter(p => p.id !== id));
    try { Object.keys(localStorage).filter(k => k.startsWith(P0 + id + "-")).forEach(k => localStorage.removeItem(k)); } catch (e) {}
    if (PROJ === id) useProject("");
  }
  function projectName() { return PROJ ? (projects().find(p => p.id === PROJ) || {}).name || "Untitled" : (AD ? "Adinkra alphabet" : "Kɔradin Modular"); }
  async function downloadFont(W, style, fname) {
    await fontmap();
    const fam = (fname || projectName()).replace(/[^\w\s-]/g, "").trim() || "Modular";
    const f = buildFont(snapshot(), W, 100, 0, fam, style || "regular");
    const a = document.createElement("a"); a.href = URL.createObjectURL(new Blob([f.toArrayBuffer()], { type: "font/otf" }));
    a.download = fam.replace(/\s+/g, "") + "-" + W + ".otf"; document.body.append(a); a.click(); setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 800);
  }

  const api = { projects, createProject, useProject, renameProject, deleteProject, projectName, downloadFont, get PROJ() { return PROJ; }, PREFIX: P, load, save, def, edit, status, setStatus, setDeleted, deleted, unlock, relock, blockedBy, resolve, progress, radicalKeys, compositeKeys, otherKeys, allKeys, liveKeys,
    fonts, exportFont, deleteFont, snapshot, fontmap, shape, buildFont, merge, fontFace, label, VOW, RAD_ROWS, COMP_ROWS, OTHER,
    get DEF() { return DEF; }, get EDIT() { return EDIT; }, clone, base, SCRIPT, FIRST_ROW, GHOST: AD ? "adinkra-ghost.json" : LAT ? "latin/" + LID + "-ghost.json" : "radicals-ghost.json", META, useBody };
  return api;
 }
 root.KR = make(/^(adinkra|latin:\w+)$/.test(root.KR_SCRIPT || "") ? root.KR_SCRIPT : "kradin");
 root.KRA = root.KR.SCRIPT === "adinkra" ? root.KR : make("adinkra");
 root.KRK = root.KR.SCRIPT === "kradin" ? root.KR : make("kradin");
 // every script the lab can draw. Latin fonts are rebuilt from a reference font by gen/autotrace.py.
 root.KR_SCRIPTS = [{ id: "kradin", name: "Kɔradin" }, { id: "adinkra", name: "Adinkra alphabet" },
   { id: "latin:franklin", name: "Franklin Gothic", ref: "traced from Libre Franklin (OFL), after Morris Fuller Benton, 1902" },
   { id: "latin:eckmann", name: "Eckmannschrift", ref: "Otto Eckmann, 1900" },
   { id: "latin:auriol", name: "Auriol", ref: "George Auriol, 1901" },
   { id: "latin:bocklin", name: "Arnold Böcklin", ref: "Otto Weisert, 1904" }];
 const cache = {}; root.KRL = id => cache[id] || (cache[id] = root.KR.SCRIPT === "latin:" + id ? root.KR : make("latin:" + id));
})(typeof globalThis !== "undefined" ? globalThis : this);
