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
    return { c, t, ro: W * (1 - c) * (o.ro ?? (0.2 + 0.18 * t)), ri: W * (o.ri ?? (0.04 + 0.1 * t)) };
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
    const c = params(W).c, polys = [];
    for (const st of strokes) for (const s of KS.split(st)) polys.push(KS.polygon(contrast(s, c), W));
    return soften(root.KR && KR.merge ? KR.merge(polys) : polys, W);
  }
  root.KSOFT = { params, contrast, soften, outline };
})(typeof globalThis !== "undefined" ? globalThis : this);
