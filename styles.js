/* Rule-based styles for the stroke skeletons: contrast by direction, shaped ends, serifs.
   Monochrome outlines only: every shape is a filled polygon, all wound the same way.
   P = {
     vert, horz   thickness of vertical / horizontal strokes, as a share of the stroke weight (curves blend by direction)
     ends         "flat" | "taper" | "flare"   what free ends do;  endAmt 0..1, endLen (x stroke weight)
     serif        "none" | "slab" | "wedge" | "bracket" | "hair" | "ball"
     serifLen     how far a serif reaches past the stroke on each side (x stroke weight)
     serifThk     serif thickness (x stroke weight)
     serifSide    "both" | "left" | "right"
     serifWhere   "axes" (ends cut on the baseline or the top) | "vertical" | "free" (every free end) | "terminals" (free curve ends off the axes)
   }
   ov: per glyph overrides from the Serif lab, {"<stroke>:<0|1>": true|false} */
const KST = (() => {
  const R = Math.PI / 180;
  const DEF = { vert: 1, horz: 1, ends: "flat", endAmt: 0, endLen: 2, serif: "none", serifLen: 0.35, serifThk: 0.4, serifSide: "both", serifWhere: "axes" };
  const PRESETS = [
    { id: "slab", name: "Slab", P: { serif: "slab", serifLen: 0.4, serifThk: 0.42, serifWhere: "axes" } },
    { id: "wedge", name: "Wedge", P: { horz: 0.78, serif: "wedge", serifLen: 0.38, serifThk: 0.3, serifWhere: "axes" } },
    { id: "bracket", name: "Bracketed", P: { horz: 0.55, serif: "bracket", serifLen: 0.42, serifThk: 0.24, serifWhere: "axes" } },
    { id: "hair", name: "Hairline", P: { vert: 1.12, horz: 0.3, serif: "hair", serifLen: 0.5, serifThk: 0.5, serifWhere: "axes" } },
    { id: "reverse", name: "Reverse", P: { vert: 0.42, horz: 1.3, serif: "slab", serifLen: 0.28, serifThk: 0.9, serifWhere: "axes" } },
    { id: "flare", name: "Flared", P: { horz: 0.82, ends: "flare", endAmt: 0.45, endLen: 2.4 } },
    { id: "taper", name: "Tapered ends", P: { horz: 0.7, ends: "taper", endAmt: 0.75, endLen: 2.2 } },
    { id: "revtaper", name: "Reverse taper", P: { vert: 0.5, horz: 1.2, ends: "taper", endAmt: 0.7, endLen: 2.0 } },
    { id: "ball", name: "Ball", P: { horz: 0.62, serif: "ball", serifLen: 0.25, serifWhere: "terminals" } },
    { id: "spur", name: "Spur", P: { serif: "slab", serifLen: 0.55, serifThk: 0.36, serifSide: "left", serifWhere: "vertical" } },
  ].map(p => ({ ...p, P: { ...DEF, ...p.P } }));

  const area = pg => { let a = 0; for (let i = 0; i < pg.length; i++) { const p = pg[i], q = pg[(i + 1) % pg.length]; a += p[0] * q[1] - q[0] * p[1]; } return a / 2; };
  const cw = pg => (area(pg) > 0 ? pg.slice().reverse() : pg); // clockwise, like the plain strokes
  function distPoly(p, Q, skip) {
    let best = 1e9;
    for (let i = 0; i < Q.length - 1; i++) {
      if (skip && skip(i)) continue;
      const a = Q[i], b = Q[i + 1], dx = b[0] - a[0], dy = b[1] - a[1], L = dx * dx + dy * dy;
      const t = L ? Math.max(0, Math.min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L)) : 0;
      best = Math.min(best, Math.hypot(a[0] + t * dx - p[0], a[1] + t * dy - p[1]));
    }
    return best;
  }
  // which stroke ends are free (not joined to another stroke) and which are cut on an axis
  function ends(strokes) {
    const CL = strokes.map(s => KS.trimCL(KS.centreline(s), s.s ?? 0, s.e ?? 1));
    const out = [];
    CL.forEach((P, i) => {
      const n = P.length, Ls = [0]; for (let j = 1; j < n; j++) Ls.push(Ls[j - 1] + Math.hypot(P[j][0] - P[j - 1][0], P[j][1] - P[j - 1][1]));
      const T = Ls[n - 1];
      [0, 1].forEach(e => {
        const p = e ? P[n - 1] : P[0];
        let joined = CL.some((Q, j) => j !== i && distPoly(p, Q) < 40);
        if (!joined && T > 300) joined = distPoly(p, P, j => e ? Ls[j + 1] > T - 160 : Ls[j] < 160) < 40;
        const st = strokes[i], cap = e ? st.cap1 : st.cap0;
        const cut = cap !== "butt" ? KS.cutDecision(p, e ? p[2] : p[3], !e) : null;
        const h = e ? p[2] : p[3] + 180;
        const sg = st.segs.filter(g => g.t !== "C"), curve = !!sg.length && (e ? sg[sg.length - 1] : sg[0]).t === "A";
        out.push({ i, e, x: p[0], y: p[1], free: !joined, cut, h, curve });
      });
    });
    return out;
  }
  function wants(E, P, ov) {
    const o = ov && ov[E.i + ":" + E.e];
    if (o === true || o === false) return o;
    if (P.serif === "none" || !E.free) return false;
    const v = Math.abs(Math.sin(E.h * R)) > 0.7;
    return P.serifWhere === "axes" ? E.cut !== null : P.serifWhere === "vertical" ? v : P.serifWhere === "terminals" ? E.cut === null && E.curve : true;
  }
  // one stroke with thickness by direction and shaped free ends; returns the polygon and its two end edges
  function outline(st, W, P, free0, free1) {
    const k = KS.K(W), CLp = KS.trimCL(KS.centreline(st), st.s ?? 0, st.e ?? 1), n = CLp.length;
    const c0 = st.cap0 !== "butt" ? KS.cutDecision(CLp[0], CLp[0][3], true) : null, c1 = st.cap1 !== "butt" ? KS.cutDecision(CLp[n - 1], CLp[n - 1][2], false) : null;
    const C = CLp.map(p => [p[0] * k, 350 + (p[1] - 350) * k]);
    const L = [0]; for (let i = 1; i < n; i++) L.push(L[i - 1] + Math.hypot(C[i][0] - C[i - 1][0], C[i][1] - C[i - 1][1]));
    const T = L[n - 1] || 1, el = Math.min(P.endLen * W, T * 0.45);
    const fdir = h => { const s = Math.sin(h * R) ** 2; return P.horz * (1 - s) + P.vert * s; };
    const shape = d => { if (P.ends === "flat" || !P.endAmt) return 1; const s = Math.max(0, 1 - d / el); return P.ends === "taper" ? 1 - P.endAmt * 0.88 * s : 1 + P.endAmt * s * s; };
    const hw = CLp.map((p, i) => {
      const h = i === 0 ? p[3] : i === n - 1 ? p[2] : (p[2] + p[3]) / 2;
      let f = fdir(h);
      if (free0) f *= shape(L[i]);
      if (free1) f *= shape(T - L[i]);
      return W / 2 * Math.max(f, 0.04);
    });
    const left = [], right = [];
    CLp.forEach((p, i) => {
      let hin = p[2], hout = p[3]; if (i === 0) hin = hout; if (i === n - 1) hout = hin;
      const [x, y] = C[i], a = (((hout - hin) + 180) % 360 + 360) % 360 - 180;
      const bis = (hin + a / 2) * R, m = hw[i] / Math.max(0.25, Math.cos(a / 2 * R)), nx = -Math.sin(bis), ny = Math.cos(bis);
      left.push([x + nx * m, y + ny * m]); right.push([x - nx * m, y - ny * m]);
    });
    const cut = (E, iE, lim, h) => { const dy = Math.sin(h * R), dx = Math.cos(h * R); if (Math.abs(dy) < 1e-6) return; const t = (lim - E[iE][1]) / dy; E[iE] = [E[iE][0] + t * dx, lim]; };
    if (c1 !== null) { cut(left, n - 1, c1, CLp[n - 1][2]); cut(right, n - 1, c1, CLp[n - 1][2]); }
    if (c0 !== null) { cut(left, 0, c0, CLp[0][3]); cut(right, 0, c0, CLp[0][3]); }
    const hs = CLp[0][3] + 180, he = CLp[n - 1][2];
    return {
      poly: left.concat(right.slice().reverse()),
      edge: [{ a: left[0], b: right[0], d: [Math.cos(hs * R), Math.sin(hs * R)], cut: c0, hw: hw[0] },
        { a: left[n - 1], b: right[n - 1], d: [Math.cos(he * R), Math.sin(he * R)], cut: c1, hw: hw[n - 1] }],
    };
  }
  function serif(E, P, W) {
    let a = E.a, b = E.b, inn, u;
    if (E.cut !== null) { inn = [0, E.cut === 0 ? 1 : -1]; if (a[0] > b[0]) [a, b] = [b, a]; u = [1, 0]; }
    else { inn = [-E.d[0], -E.d[1]]; const l = Math.hypot(b[0] - a[0], b[1] - a[1]) || 1; u = [(b[0] - a[0]) / l, (b[1] - a[1]) / l]; }
    const ext = P.serifLen * W, thk = Math.max(0.06 * W, P.serifThk * W);
    // one-sided serifs reach out on the left or the right of the glyph only
    const aLeft = a[0] < b[0] - 1e-6 || (Math.abs(a[0] - b[0]) < 1e-6 && a[1] < b[1]);
    const xa = P.serifSide === "both" || (P.serifSide === "left") === aLeft ? ext : 0;
    const xb = P.serifSide === "both" || (P.serifSide === "left") !== aLeft ? ext : 0;
    const add = (p, v, s) => [p[0] + v[0] * s, p[1] + v[1] * s];
    const ea = add(a, u, -xa), eb = add(b, u, xb);
    if (P.serif === "slab" || P.serif === "hair") { const t = P.serif === "hair" ? Math.max(0.05 * W, thk * 0.32) : thk; return [ea, eb, add(eb, inn, t), add(ea, inn, t)]; }
    if (P.serif === "wedge") { const dp = thk * 2.6; return [ea, eb, add(eb, inn, thk * 0.25), add(b, inn, dp), add(a, inn, dp), add(ea, inn, thk * 0.25)]; }
    if (P.serif === "bracket") {
      const br = Math.max(ext, 0.3 * W) * 1.1, pts = [ea, eb, add(eb, inn, thk)];
      const q = (p0, c, p1) => { for (let s = 1; s <= 8; s++) { const t = s / 8; pts.push([(1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * c[0] + t * t * p1[0], (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * c[1] + t * t * p1[1]]); } };
      q(add(eb, inn, thk), add(b, inn, thk), add(b, inn, thk + br));
      pts.push(add(a, inn, thk + br));
      q(add(a, inn, thk + br), add(a, inn, thk), add(ea, inn, thk));
      return pts;
    }
    if (P.serif === "ball") {
      const half = Math.hypot(b[0] - a[0], b[1] - a[1]) / 2, r = half * (1.12 + P.serifLen * 0.9);
      const m = [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2], c = add(m, inn, r * 0.72), pts = [];
      for (let s = 0; s < 28; s++) { const t = s / 28 * 2 * Math.PI; pts.push([c[0] + r * Math.cos(t), c[1] + r * Math.sin(t)]); }
      return pts;
    }
    return null;
  }
  // every polygon of a glyph in this style; tf(x, y) is applied last (width, slant)
  function glyph(strokes, W, tf, P, ov) {
    P = { ...DEF, ...P };
    const E = ends(strokes), out = [];
    strokes.forEach((st, i) => {
      const e0 = E[2 * i], e1 = E[2 * i + 1];
      const o = outline(st, W, P, e0.free, e1.free);
      out.push(o.poly);
      [e0, e1].forEach((e, j) => { if (wants(e, P, ov)) { const s = serif({ ...o.edge[j] }, P, W); if (s) out.push(s); } });
    });
    return out.map(pg => cw(tf ? pg.map(([x, y]) => tf(x, y)) : pg));
  }
  const svgPath = polys => polys.map(pg => "M" + pg.map(p => p[0].toFixed(1) + " " + p[1].toFixed(1)).join("L") + "Z").join("");
  // saved styles (Serif lab)
  const LS = { get(k, d) { try { const v = localStorage.getItem(k); return v == null ? d : JSON.parse(v); } catch (e) { return d; } }, set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); return true; } catch (e) { return false; } } };
  const saved = () => LS.get("kr-styles", []);
  function save(s) { const L = saved().filter(x => x.id !== s.id); L.push(s); return LS.set("kr-styles", L); }
  function remove(id) { LS.set("kr-styles", saved().filter(x => x.id !== id)); }
  // every style a generated font can take: name -> {P, ov} (null = the built-in Regular / Tapered outlines)
  function all() {
    return [{ id: "regular", name: "Regular", P: null }, { id: "tapered", name: "Tapered", P: null }]
      .concat(PRESETS.map(p => ({ ...p, ov: {} }))).concat(saved().map(s => ({ ...s, P: { ...DEF, ...s.P }, mine: true })));
  }
  return { DEF, PRESETS, ends, wants, outline, glyph, svgPath, saved, save, remove, all };
})();
