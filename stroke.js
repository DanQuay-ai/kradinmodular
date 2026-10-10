// Kɔradin stroke model: a stroke is a turtle path.
// start {x,y}, heading h (deg, 0 = right, 90 = up), segments:
//   L {len}            straight
//   A {r, ang}         circular arc, ang > 0 turns left (anticlockwise), < 0 right
//   C {ang}            sharp corner (mitred)
// s / e  : trim start / end, 0..1 of the stroke length (endpoint control)
// cap0 / cap1 : "auto" (cut flat where the stroke runs past baseline 0 or top 700), "butt"
const KS = (() => {
  const R = Math.PI / 180, f = v => Math.round(v * 100) / 100;
  const AX = W => ({ base: W / 2, mid: 350, top: 700 - W / 2 });
  function trace(st) {
    let x = st.x, y = st.y, h = st.h, d = `M${f(x)},${f(y)}`, len = 0;
    const joints = [{ x, y, h, i: -1 }];
    st.segs.forEach((g, i) => {
      if (g.t === "L") {
        x += g.len * Math.cos(h * R); y += g.len * Math.sin(h * R); d += ` L${f(x)},${f(y)}`; len += Math.abs(g.len);
      } else if (g.t === "C") { h += g.ang; }
      else if (g.t === "A") {
        const sg = Math.sign(g.ang) || 1, r = Math.max(1, g.r);
        const cx = x + r * Math.cos((h + 90 * sg) * R), cy = y + r * Math.sin((h + 90 * sg) * R);
        let a0 = Math.atan2(y - cy, x - cx) / R, left = Math.abs(g.ang);
        while (left > 1e-6) {
          const step = Math.min(left, 170); a0 += sg * step; left -= step;
          x = cx + r * Math.cos(a0 * R); y = cy + r * Math.sin(a0 * R);
          d += ` A${f(r)},${f(r)} 0 0 ${sg > 0 ? 1 : 0} ${f(x)},${f(y)}`;
        }
        h += g.ang; len += r * Math.abs(g.ang) * R;
      }
      joints.push({ x, y, h, i });
    });
    return { d, x, y, h, len, joints };
  }
  // extend a free end that runs past y=0 or y=700 so the whole width crosses it: the clip then cuts it flat (2 points)
  function ext(x, y, h, W, back) {
    const hh = back ? h + 180 : h, sy = Math.sin(hh * R), cx = Math.cos(hh * R);
    if (Math.abs(sy) < 0.2) return null;
    const lim = sy < 0 ? 0 : 700, tol = W * 0.75;
    if ((sy < 0 && y > lim + tol) || (sy > 0 && y < lim - tol)) return null;
    const target = sy < 0 ? -(W / 2) * Math.abs(cx) - 2 : 700 + (W / 2) * Math.abs(cx) + 2; // both edges past the line
    const t = (target - y) / sy; if (t <= 0) return null;
    return { x: x + t * cx, y: y + t * sy };
  }
  function path(st, W) {
    const t = trace(st);
    let d = t.d, pre = "", tot = t.len;
    if (st.cap1 !== "butt" && st.e >= 0.999) { const p = ext(t.x, t.y, t.h, W, false); if (p) { d += ` L${f(p.x)},${f(p.y)}`; tot += Math.hypot(p.x - t.x, p.y - t.y); } }
    if (st.cap0 !== "butt" && st.s <= 0.001) { const p = ext(st.x, st.y, st.h, W, true); if (p) { pre = `M${f(p.x)},${f(p.y)} L${f(st.x)},${f(st.y)}`; d = pre + d.replace(/^M[^A-Z]*/, " "); tot += Math.hypot(p.x - st.x, p.y - st.y); } }
    return { d, t, tot };
  }
  // weight scaling: designs are drawn at Black (98). At other weights the centrelines scale about the mid axis
  // so the outer edges still sit on the baseline and the top (circles stay circles).
  const K = W => (700 - W) / 602;
  function scaled(st, W) {
    const k = K(W); if (Math.abs(k - 1) < 1e-6) return st;
    return Object.assign({}, st, { x: st.x * k, y: 350 + (st.y - 350) * k,
      segs: st.segs.map(g => g.t === "L" ? Object.assign({}, g, { len: g.len * k }) : g.t === "A" ? Object.assign({}, g, { r: g.r * k }) : g) });
  }
  function svgStroke(st, W, o = {}) {
    st = scaled(st, W);
    const { d, t } = path(st, W), s = st.s ?? 0, e = st.e ?? 1;
    const dash = (s > 0 || e < 1) ? ` pathLength="1000" stroke-dasharray="0 ${f(s * 1000)} ${f((e - s) * 1000)} 3000"` : "";
    return `<path d="${d}" fill="none" stroke="${o.color || "var(--ink)"}" stroke-width="${W}" stroke-linecap="butt" stroke-linejoin="miter" stroke-miterlimit="10"${dash}${o.attr || ""}/>`;
  }
  function guides(W, x0 = -100, x1 = 1000) {
    const a = AX(W);
    return [0, 700].map(y => `<line x1="${x0}" x2="${x1}" y1="${y}" y2="${y}" stroke="var(--tint)" stroke-opacity=".55" stroke-width="3"/>`).join("") +
      [a.base, a.mid, a.top].map(y => `<line x1="${x0}" x2="${x1}" y1="${y}" y2="${y}" stroke="var(--tint)" stroke-opacity=".35" stroke-width="2" stroke-dasharray="12 10"/>`).join("");
  }
  // element name for each segment
  function tag(g, h) {
    if (g.t === "C") return "corner";
    if (g.t === "L") {
      const m = ((h % 360) + 360) % 360, near = a => Math.abs(((m - a + 540) % 360) - 180) < 1;
      return near(90) || near(270) ? "stem" : near(0) || near(180) ? "bar" : [60, 120, 240, 300].some(near) ? "diagonal 60°" : "line (free angle)";
    }
    const a = Math.abs(g.ang);
    return a <= 100 ? "arc" : a <= 200 ? "bowl" : a < 330 ? "curl" : a <= 390 ? "loop" : "spiral";
  }
  function elements(st) { // consecutive arcs turning the same way read as one element (a spiral is a chain of half-turns)
    let h = st.h; const out = []; let run = null;
    st.segs.forEach(g => {
      if (g.t === "A") { if (run && Math.sign(run.ang) === Math.sign(g.ang)) run.ang += g.ang; else { if (run) out.push(tag(run, 0)); run = { t: "A", ang: g.ang }; } h += g.ang; return; }
      if (run) { out.push(tag(run, 0)); run = null; }
      out.push(tag(g, h)); if (g.t === "C") h += g.ang;
    });
    if (run) out.push(tag(run, 0)); return out; }
  // stroke order: left before right, top before bottom, vertical before horizontal
  function autoOrder(strokes) {
    const key = st => { const t = trace(st); const xs = t.joints.map(j => j.x), ys = t.joints.map(j => j.y);
      const vert = Math.abs(Math.sin(st.h * R)) > 0.7 ? 0 : 1;
      return [Math.round(Math.min(...xs) / 120), -Math.round(Math.max(...ys) / 120), vert]; };
    return strokes.map((s, i) => [key(s), i, s]).sort((a, b) => { for (let k = 0; k < 3; k++) if (a[0][k] !== b[0][k]) return a[0][k] - b[0][k]; return a[1] - b[1]; }).map(x => x[2]);
  }

  // ---------- outline polygon for fonts (port of gen/outline.py): fixed point structure, flat cuts at 0 / 700
  function centreline(st) {
    let x = st.x, y = st.y, h = st.h; const P = [[x, y, h, h, "end"]];
    for (const g of st.segs) {
      if (g.t === "C") { h += g.ang; P[P.length - 1][3] = h; P[P.length - 1][4] = "corner"; continue; }
      if (g.t === "L") { if (Math.abs(g.len) < 1e-6) continue; x += g.len * Math.cos(h * R); y += g.len * Math.sin(h * R); P.push([x, y, h, h, "pt"]); continue; }
      const sg = g.ang > 0 ? 1 : -1, r = Math.max(1, g.r);
      const cx = x + r * Math.cos((h + 90 * sg) * R), cy = y + r * Math.sin((h + 90 * sg) * R), a0 = Math.atan2(y - cy, x - cx);
      const n = Math.max(2, Math.ceil(Math.abs(g.ang) / 9));
      for (let i = 1; i <= n; i++) { const a = a0 + g.ang * R * i / n, hh = h + g.ang * i / n; P.push([cx + r * Math.cos(a), cy + r * Math.sin(a), hh, hh, "pt"]); }
      x = P[P.length - 1][0]; y = P[P.length - 1][1]; h += g.ang;
    }
    P[P.length - 1][4] = "end";
    const Q = [P[0]];
    for (const p of P.slice(1)) { const q = Q[Q.length - 1]; if (Math.hypot(p[0] - q[0], p[1] - q[1]) < 1e-6) { q[3] = p[3]; if (p[4] === "corner") q[4] = "corner"; } else Q.push(p); }
    return Q;
  }
  function trimCL(P, s, e) {
    if (s <= 0.0005 && e >= 0.9995) return P;
    const L = [0]; for (let i = 1; i < P.length; i++) L.push(L[i - 1] + Math.hypot(P[i][0] - P[i - 1][0], P[i][1] - P[i - 1][1]));
    const T = L[L.length - 1]; s *= T; e *= T; const out = [];
    for (let i = 0; i < P.length - 1; i++) {
      const a = P[i], b = P[i + 1];
      for (const t0 of [s, e]) if (L[i] <= t0 && t0 <= L[i + 1] && L[i + 1] > L[i]) { const u = (t0 - L[i]) / (L[i + 1] - L[i]); out.push([a[0] + u * (b[0] - a[0]), a[1] + u * (b[1] - a[1]), b[2], b[2], "end", t0]); }
      if (s < L[i] && L[i] < e) out.push(a.concat([L[i]]));
    }
    if (s < T && T <= e) out.push(P[P.length - 1].concat([T]));
    out.sort((p, q) => p[5] - q[5]);
    const o = out.map(p => p.slice(0, 5)); o[0][4] = "end"; o[o.length - 1][4] = "end"; return o;
  }
  const CUT_TOL = 0.75 * 98;
  function cutDecision(p, hOut, back) {
    const hh = hOut + (back ? 180 : 0), sy = Math.sin(hh * R);
    if (Math.abs(sy) < 0.2) return null;
    if (sy < 0 && p[1] <= CUT_TOL) return 0; if (sy > 0 && p[1] >= 700 - CUT_TOL) return 700; return null;
  }
  // returns a clockwise polygon [[x,y]...]; tf(x,y) -> [x,y] is applied last (width, slant)
  function polygon(st, W, tf) {
    const k = K(W), P = trimCL(centreline(st), st.s ?? 0, st.e ?? 1), n = P.length, hw = W / 2;
    const c0 = st.cap0 !== "butt" ? cutDecision(P[0], P[0][3], true) : null, c1 = st.cap1 !== "butt" ? cutDecision(P[n - 1], P[n - 1][2], false) : null;
    const C = P.map(p => [p[0] * k, 350 + (p[1] - 350) * k]); const left = [], right = [];
    P.forEach((p, i) => {
      let hin = p[2], hout = p[3]; if (i === 0) hin = hout; if (i === n - 1) hout = hin;
      const [x, y] = C[i], a = (((hout - hin) + 180) % 360 + 360) % 360 - 180;
      if (Math.abs(a) < 1e-6) { const nx = -Math.sin(hin * R), ny = Math.cos(hin * R); left.push([x + nx * hw, y + ny * hw]); right.push([x - nx * hw, y - ny * hw]); }
      else { const bis = (hin + a / 2) * R, m = hw / Math.max(0.25, Math.cos(a / 2 * R)), nx = -Math.sin(bis), ny = Math.cos(bis); left.push([x + nx * m, y + ny * m]); right.push([x - nx * m, y - ny * m]); }
    });
    const cut = (E, iE, iN, lim, h) => { const dy = Math.sin(h * R), dx = Math.cos(h * R); if (Math.abs(dy) < 1e-6) return; const t = (lim - E[iE][1]) / dy; E[iE] = [E[iE][0] + t * dx, lim]; };
    if (c1 !== null) { cut(left, n - 1, n - 2, c1, P[n - 1][2]); cut(right, n - 1, n - 2, c1, P[n - 1][2]); }
    if (c0 !== null) { cut(left, 0, 1, c0, P[0][3]); cut(right, 0, 1, c0, P[0][3]); }
    return left.concat(right.reverse()).map(([x, y]) => tf ? tf(x, y) : [x, y]);
  }

  // Tapered (brush / Mincho logic): thickness follows the stroke direction (thin horizontals, thick verticals),
  // curves and diagonals sweep out to a point at a free end, horizontals end in a triangular scale (uroko),
  // verticals end with an angled cut. Ends that run past the baseline or the top are still cut flat.
  function polygonTapered(st, W, tf) {
    const k = K(W), P = trimCL(centreline(st), st.s ?? 0, st.e ?? 1), n = P.length;
    const c0 = st.cap0 !== "butt" ? cutDecision(P[0], P[0][3], true) : null, c1 = st.cap1 !== "butt" ? cutDecision(P[n - 1], P[n - 1][2], false) : null;
    const C = P.map(p => [p[0] * k, 350 + (p[1] - 350) * k]);
    const L = [0]; for (let i = 1; i < n; i++) L.push(L[i - 1] + Math.hypot(C[i][0] - C[i - 1][0], C[i][1] - C[i - 1][1]));
    const T = L[n - 1] || 1;
    const fdir = h => 0.3 + 0.7 * Math.abs(Math.sin(h * R));
    const hEnd = P[n - 1][2], hStart = P[0][3];
    const curvedEnd = st.segs.length && st.segs[st.segs.length - 1].t === "A";
    const diagEnd = Math.abs(Math.sin(hEnd * R)) > 0.25 && Math.abs(Math.cos(hEnd * R)) > 0.25;
    const taperEnd = c1 === null && (curvedEnd || diagEnd);
    const curvedStart = st.segs.length && st.segs[0].t === "A";
    const taperStart = c0 === null && curvedStart && Math.abs(Math.sin(hStart * R)) > 0.25;
    const tl = Math.min(0.4 * T, 2.2 * W);
    const hw = P.map((p, i) => {
      const h = i === 0 ? p[3] : i === n - 1 ? p[2] : (p[2] + p[3]) / 2;
      let f = fdir(h);
      if (taperEnd && T - L[i] < tl) f *= Math.max(0.1, (T - L[i]) / tl);
      if (taperStart && L[i] < tl * 0.6) f *= Math.max(0.35, L[i] / (tl * 0.6));
      return W / 2 * Math.max(f, 0.06);
    });
    const left = [], right = [];
    P.forEach((p, i) => {
      let hin = p[2], hout = p[3]; if (i === 0) hin = hout; if (i === n - 1) hout = hin;
      const [x, y] = C[i], a = (((hout - hin) + 180) % 360 + 360) % 360 - 180;
      if (Math.abs(a) < 1e-6) { const nx = -Math.sin(hin * R), ny = Math.cos(hin * R); left.push([x + nx * hw[i], y + ny * hw[i]]); right.push([x - nx * hw[i], y - ny * hw[i]]); }
      else { const bis = (hin + a / 2) * R, m = hw[i] / Math.max(0.25, Math.cos(a / 2 * R)), nx = -Math.sin(bis), ny = Math.cos(bis); left.push([x + nx * m, y + ny * m]); right.push([x - nx * m, y - ny * m]); }
    });
    const cut = (E, iE, lim, h) => { const dy = Math.sin(h * R), dx = Math.cos(h * R); if (Math.abs(dy) < 1e-6) return; const t = (lim - E[iE][1]) / dy; E[iE] = [E[iE][0] + t * dx, lim]; };
    if (c1 !== null) { cut(left, n - 1, c1, hEnd); cut(right, n - 1, c1, hEnd); }
    if (c0 !== null) { cut(left, 0, c0, hStart); cut(right, 0, c0, hStart); }
    let L2 = left.slice(), R2 = right.slice();
    const dx = Math.cos(hEnd * R), dy = Math.sin(hEnd * R);
    if (c1 === null && !taperEnd && Math.abs(dy) < 0.2) {
      // uroko: a small triangle on the upper side, just before the end of a horizontal
      const up = dx > 0 ? L2 : R2, e = up[n - 1], hwE = hw[n - 1], base = W * 0.95, peak = W * 0.42;
      const p1 = [e[0] - dx * base, e[1]], p2 = [e[0] - dx * peak * 0.6, e[1] + W * 0.48], p3 = [e[0], e[1] - hwE * 0.2];
      up.splice(n - 1, 1, p1, p2, p3);
    } else if (c1 === null && !taperEnd && Math.abs(dx) < 0.3) {
      // vertical end: angled cut, the right side runs a little longer
      const sideLong = dy < 0 ? R2 : L2, e = sideLong[sideLong.length - 1];
      sideLong[sideLong.length - 1] = [e[0] + dx * W * 0.25, e[1] + dy * W * 0.25];
    }
    return L2.concat(R2.reverse()).map(([x, y]) => tf ? tf(x, y) : [x, y]);
  }
  // components: {ref, dx, dy, s} applied to a stroke (scale about the origin, then move)
  function place(st, c) {
    const s = c.s ?? 1;
    return Object.assign({}, st, { x: st.x * s + (c.dx || 0), y: st.y * s + (c.dy || 0),
      segs: st.segs.map(g => g.t === "L" ? Object.assign({}, g, { len: g.len * s }) : g.t === "A" ? Object.assign({}, g, { r: g.r * s }) : Object.assign({}, g)) });
  }
  // whole-glyph SVG with an automatic viewBox. o: {ghost (path d), nums, guides, color(i), cl (centrelines), cls, order}
  let _id = 0;
  function glyphSVG(strokes, W, o = {}) {
    const sc = strokes.map(s => scaled(s, W));
    let x1 = 0;
    sc.forEach(s => trace(s).joints.forEach(j => { x1 = Math.max(x1, j.x); }));
    const r = Math.max(700, x1 + W / 2 + 60), id = "c" + (++_id);
    let g = "";
    if (o.guides !== false) g += guides(W, -60, r + 40);
    if (o.ghost) g += `<path d="${o.ghost}" fill="#ff9500" fill-opacity=".25"/>`;
    g += `<g clip-path="url(#${id})">` + strokes.map((s, i) => svgStroke(s, W, { color: o.color ? o.color(i, s) : "var(--ink)", attr: o.attr ? o.attr(i, s) : "" })).join("") + `</g>`;
    if (o.cl) g += sc.map(s => `<path d="${trace(s).d}" fill="none" stroke="#ff3b30" stroke-width="3"/>`).join("");
    if (o.nums) g += sc.map((s, i) => `<g transform="translate(${s.x},${s.y}) scale(1,-1)"><circle r="30" fill="#ff3b30"/><text y="11" text-anchor="middle" font-size="32" font-weight="700" fill="#fff" font-family="system-ui,sans-serif">${i + 1}</text></g>`).join("");
    return `<svg viewBox="-60 -60 ${r + 100} 820" class="${o.cls || ""}" role="img"><defs><clipPath id="${id}"><rect x="-300" y="0" width="${r + 600}" height="700"/></clipPath></defs><g transform="translate(0,700) scale(1,-1)">${g}</g></svg>`;
  }
  return { polygon, polygonTapered, place, centreline, glyphSVG, K, scaled, trace, path, svgStroke, guides, AX, elements, autoOrder, f };
})();
