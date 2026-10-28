/* Kɔradin Soft: rules computed on the stroke skeletons, nothing drawn by hand.
   1. Optical contrast: a stroke gets thinner the more horizontal it runs: width = W * (1 - c * cos²(heading)).
   2. Soft corners: the merged outline is closed (inner corners filled with radius ri) then opened
      (outer corners rounded with radius ro), both with exact circular offsets (Clipper).
   All three numbers grow with the weight: light reads like Ojuju (open, slightly soft), Black like Oja (blobby). */
(function (root) {
  const R = Math.PI / 180;
  function params(W, o = {}) {
    // t: 0 at a light 50 (Ojuju), 1 at an ultra 150 (Oja). The outer radius stays under half the thinnest
    // stroke (a horizontal, thinned by the contrast), so the opening can never cut a stroke away.
    const t = Math.max(0, Math.min(1, (W - 50) / 100)), c = o.c ?? (0.04 + 0.12 * t);
    return { c, t, g: o.g ?? 0.55, ro: Math.min(W * (1 - c) * (o.ro ?? (0.2 + 0.18 * t)), 0.42 * W * 0.55 * (1 - c)), ri: W * (o.ri ?? (0.03 + 0.05 * t)) };
  }
  // contrast as a width profile along the stroke, from its headings
  function contrast(st, c) {
    if (!c) return st;
    const P = KS.centreline(st); if (P.length < 2) return st;
    const L = [0]; for (let i = 1; i < P.length; i++) L.push(L[i - 1] + Math.hypot(P[i][0] - P[i - 1][0], P[i][1] - P[i - 1][1]));
    const T = L[L.length - 1] || 1, base = st.wk || 1;
    const wp = P.map((p, i) => { const h = (i === P.length - 1 ? p[2] : p[3]) * R; return [L[i] / T, +(base * (1 - c * Math.cos(h) ** 2)).toFixed(4)]; });
    return Object.assign({}, st, { wp, wk: undefined });
  }
  // 3. Counter keeper (Ojuju, not Oja): wherever two strokes that are not joined run closer than
  //    stroke + gap, both thin down locally so the white between them never drops under the gap.
  //    gap = g * W. Strokes that meet at a junction are ignored near that junction; a stroke that curls
  //    back on itself counts as two strokes when the two parts are far apart along it.
  function samples(st) {
    const P = KS.centreline(st), k = KS.K(W_), out = [];
    let L = 0;
    for (let i = 0; i < P.length; i++) {
      if (i) { const a = P[i - 1], b = P[i], d = Math.hypot(b[0] - a[0], b[1] - a[1]), n = Math.max(1, Math.ceil(d / 12));
        for (let j = 1; j <= n; j++) out.push({ x: (a[0] + (b[0] - a[0]) * j / n) * k, y: (350 + (a[1] + (b[1] - a[1]) * j / n - 350) * k), L: (L + d * j / n) * k }); L += d; }
      else out.push({ x: P[0][0] * k, y: 350 + (P[0][1] - 350) * k, L: 0 });
    }
    out.forEach(q => q.t = q.L / (L * k || 1)); return out;
  }
  let W_ = 98; const FLOOR = 0.55;   // a stroke never thins below 55 % of the weight
  function keepCounters(strokes, W, g) {
    W_ = W; const S = strokes.map(samples), gap = g * W, near = 1.6 * W, touch = 0.8 * W;
    const share = st => q => st.wp ? KS.wpAt(st.wp, q.t) : (st.wk || 1);
    // junctions: two strokes whose centrelines come within 0.8 W overlap there (they are joined).
    // JP[a][b] = samples of a near its junction with b
    const JP = S.map(() => S.map(() => null));
    for (let a = 0; a < S.length; a++) for (let b = 0; b < S.length; b++) {
      if (a === b) continue; const js = [];
      for (const p of S[a]) for (const q of S[b]) { const dx = p.x - q.x, dy = p.y - q.y; if (dx * dx + dy * dy < touch * touch) { js.push(p); break; } }
      if (js.length) JP[a][b] = S[a].map(p => js.some(j => Math.hypot(p.x - j.x, p.y - j.y) < near));
    }
    return strokes.map((st, a) => {
      const w = share(st), f = S[a].map((p, ip) => {
        let lim = Infinity;
        for (let b = 0; b < S.length; b++) { const ja = b !== a && JP[a][b], jb = b !== a && JP[b][a]; S[b].forEach((q, iq) => {
          if (b === a && Math.abs(q.L - p.L) < 3 * W) return;
          if (ja && jb && ja[ip] && jb[iq]) return;
          const d = Math.hypot(p.x - q.x, p.y - q.y); if (d > 3 * W) return;
          // half widths of both strokes + gap must fit in d
          const wb = share(strokes[b])(q), room = (d - gap) / (W * 0.5 * (w(p) + wb));
          lim = Math.min(lim, room);
        }); }
        return Math.max(FLOOR, Math.min(1, lim));
      });
      if (f.every(v => v >= 0.999)) return st;
      // smooth the limit along the stroke so the thinning is gradual
      const sm = f.map((v, i) => { let m = v; for (let j = Math.max(0, i - 6); j <= Math.min(f.length - 1, i + 6); j++) m = Math.min(m, f[j] + Math.abs(i - j) * 0.04); return m; });
      const wp = S[a].filter((_, i) => i % 2 === 0 || i === S[a].length - 1).map((p, i, arr) => { const ix = S[a].indexOf(p); return [+p.t.toFixed(4), +(w(p) * sm[ix]).toFixed(4)]; });
      return Object.assign({}, st, { wp, wk: undefined });
    });
  }
  const S = 100;
  function offset(paths, d) {
    const CL = root.ClipperLib, co = new CL.ClipperOffset(2, 0.25 * S), out = new CL.Paths();
    co.AddPaths(paths, CL.JoinType.jtRound, CL.EndType.etClosedPolygon); co.Execute(out, d * S); return out;
  }
  function soften(rings, W, o) {
    const CL = root.ClipperLib; if (!CL || !rings.length) return rings;
    const p = params(W, o);
    let paths = rings.map(r => r.map(([x, y]) => ({ X: Math.round(x * S), Y: Math.round(y * S) })));
    const c = new CL.Clipper(), u = new CL.Paths(); c.AddPaths(paths, CL.PolyType.ptSubject, true); c.Execute(CL.ClipType.ctUnion, u, CL.PolyFillType.pftNonZero, CL.PolyFillType.pftNonZero); paths = u;
    if (p.ri > 0.5) paths = offset(offset(paths, p.ri), -p.ri);   // closing: inner corners
    if (p.ro > 0.5) paths = offset(offset(paths, -p.ro), p.ro);   // opening: outer corners
    return paths.map(pa => pa.map(q => [q.X / S, q.Y / S]));
  }
  // the soft outline of a set of (resolved) strokes, for the lab preview
  function outline(strokes, W) {
    const p = params(W), polys = [];
    for (const s of prep(strokes, W)) polys.push(KS.polygon(s, W));
    return soften(root.KR && KR.merge ? KR.merge(polys) : polys, W);
  }
  // contrast + counter keeper on a glyph's strokes (split at reversals)
  function prep(strokes, W) { const p = params(W); return keepCounters(strokes.flatMap(st => KS.split(st)).map(s => contrast(s, p.c)), W, p.g); }
  root.KSOFT = { params, contrast, soften, outline, prep, keepCounters };
})(typeof globalThis !== "undefined" ? globalThis : this);
