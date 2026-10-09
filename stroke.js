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
  function svgStroke(st, W, o = {}) {
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
  return { trace, path, svgStroke, guides, AX, elements, autoOrder, f };
})();
