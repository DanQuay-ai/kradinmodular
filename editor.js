/* Stroke editor shared by the Stroke generator (radicals) and the Construction lab (every glyph).
   Radicals: every stroke is editable. Composites: the radical (or vowel, ni, kɔ...) is a locked component that follows
   the approved radical; you place it and add the modifier strokes. */
(function () {
  const MODE = window.EDITOR_MODE || "radicals";
  const $ = id => document.getElementById(id);
  let GH = {}, cur = null, sel = 0, hist = [];
  const W = () => +$("w").value;
  const isComp = k => KR.def(k).type === "composite";
  const own = () => KR.def(cur).strokes;
  const E = () => KR.edit(cur);
  function commit() { hist.push(JSON.stringify(E())); if (hist.length > 80) hist.shift(); }
  function changed() { KR.save(); render(); }
  const locked = () => isComp(cur) && KR.blockedBy(cur).length > 0;

  // ---------------- picker
  function chip(k) {
    const s = KR.status(k), b = isComp(k) && KR.blockedBy(k).length;
    const c = s === "approved" ? "ok" : s === "fix" ? "fix" : "dr";
    return `<button class="${c}${b ? " blk" : ""}" aria-current="${k === cur}" data-k="${k}" title="${b ? "Waiting for " + KR.blockedBy(k).join(", ") : ""}">${k}</button>`;
  }
  function pick() {
    const rows = [["Vowels", ""]].concat(KR.RAD_ROWS.slice(1).map(r => [r, r]));
    let h = rows.map(([n, on]) => `<h3>${n}</h3><div class="chips">${KR.VOW.map(v => KR.DEF[on + v] ? chip(on + v) : "").join("")}</div>`).join("");
    if (MODE === "all") {
      h = `<h3 class="sec">Radicals</h3>` + h + `<h3 class="sec">Composed</h3>` +
        KR.COMP_ROWS.map(([on, how]) => `<h3>${on} <small>${how}</small></h3><div class="chips">${KR.VOW.map(v => KR.DEF[on + v] && KR.DEF[on + v].type === "composite" ? chip(on + v) : "").join("")}</div>`).join("");
    }
    const p = KR.progress();
    $("pick").innerHTML = h + `<p class="hint" style="margin-top:14px">● gold draft · ● green approved · ● orange needs fix${MODE === "all" ? " · 🔒 waits for another glyph" : ""}.</p>`;
    $("pick").querySelectorAll("button[data-k]").forEach(b => b.onclick = () => { location.hash = encodeURIComponent(b.dataset.k); });
    if ($("prog")) {
      $("prog").textContent = `${p.ok} / ${p.total} approved`;
      $("exportAll").disabled = !p.all;
      $("exportAll").title = p.all ? "Export every approved glyph as a font for the type tester" : "Approve every glyph to export the final font";
    }
    const a = $("pick").querySelector('[aria-current="true"]'), pk = $("pick");
    if (a && pk.scrollHeight > pk.clientHeight) { const r = a.getBoundingClientRect(), pr = pk.getBoundingClientRect(); if (r.top < pr.top || r.bottom > pr.bottom) pk.scrollTop += r.top - pr.top - pk.clientHeight / 2 + r.height / 2; }
  }
  function openG(k) {
    k = KR.base(k || "");
    const ok = k && KR.DEF[k] && (MODE === "all" || KR.DEF[k].type === "radical") && KR.DEF[k].type !== "alias";
    cur = ok ? k : "a"; sel = 0; hist = []; pick(); render();
  }

  // ---------------- canvas
  function canvas() {
    const w = W(), res = KR.resolve(cur), lock = res.filter(s => s.locked), mine = own(), L = lock.length, cl = $("cl").checked;
    let xmax = 900; res.forEach(s => KS.trace(KS.scaled(s, w)).joints.forEach(j => { xmax = Math.max(xmax, j.x + 120); }));
    $("cv").setAttribute("viewBox", `-100 -100 ${xmax + 100} 900`);
    let s = `<defs><clipPath id="body"><rect x="-300" y="0" width="${xmax + 600}" height="700"/></clipPath>
      <pattern id="lk" width="16" height="16" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><rect width="16" height="16" fill="var(--ink)" opacity=".55"/><rect width="7" height="16" fill="var(--ink)" opacity=".25"/></pattern></defs>
      <g id="flip" transform="translate(0,700) scale(1,-1)">`;
    for (let x = 0; x <= xmax; x += 100) s += `<line x1="${x}" x2="${x}" y1="-60" y2="760" stroke="var(--sep)" stroke-width="1.5"/><text transform="translate(${x},-90) scale(1,-1)" font-size="20" fill="var(--label2)" text-anchor="middle" font-family="system-ui">${x}</text>`;
    s += KS.guides(w, -100, xmax);
    [["0", 0], ["base", w / 2], ["mid", 350], ["top", 700 - w / 2], ["700", 700]].forEach(([n, y]) => s += `<text transform="translate(-95,${y + 6}) scale(1,-1)" font-size="18" fill="var(--tint)" font-family="system-ui">${n}</text>`);
    if ($("gh").checked && GH[cur]) s += `<path d="${GH[cur].d}" fill="#ff9500" fill-opacity=".22"/>`;
    if (!$("hide").checked) {
      s += `<g clip-path="url(#body)">` + lock.map(t => KS.svgStroke(t, w, { color: "url(#lk)", attr: ' class="stk lockd" pointer-events="none"' })).join("") +
        mine.map((t, i) => KS.svgStroke(t, w, { color: i === sel ? "var(--tint)" : (t.role === "glide" ? "#0a84ff" : isComp(cur) ? "#ff3b30" : "var(--ink)"), attr: ` data-i="${i}" class="stk" style="cursor:pointer" opacity="${i === sel ? 0.92 : 0.85}"` })).join("") + `</g>`;
    }
    const sc = mine.map(t => KS.scaled(t, w)), scl = lock.map(t => KS.scaled(t, w));
    if (cl) s += sc.concat(scl).map(t => `<path d="${KS.trace(t).d}" fill="none" stroke="#ff3b30" stroke-width="3" pointer-events="none"/>`).join("");
    const t = sc[sel];
    if (t && !locked()) {
      const tr = KS.trace(t);
      s += tr.joints.slice(1).map(j => `<circle cx="${j.x}" cy="${j.y}" r="9" fill="#ff3b30" pointer-events="none"/>`).join("");
      s += `<g transform="translate(${tr.x},${tr.y}) rotate(${tr.h})" pointer-events="none"><path d="M0,0 L-26,13 L-26,-13Z" fill="#ff3b30"/></g>`;
      s += `<circle id="hdl" cx="${t.x}" cy="${t.y}" r="22" fill="#fff" stroke="#ff3b30" stroke-width="6" style="cursor:grab"/>`;
    }
    const badge = (t, n, c) => `<g transform="translate(${t.x},${t.y}) scale(1,-1)" pointer-events="none"><circle cx="-34" cy="-34" r="20" fill="${c}"/><text x="-34" y="-27" text-anchor="middle" font-size="22" font-weight="700" fill="#fff" font-family="system-ui">${n}</text></g>`;
    s += scl.map((t, i) => badge(t, i + 1, "#8e8e93")).join("") + sc.map((t, i) => badge(t, L + i + 1, "#ff3b30")).join("");
    if (locked()) s += `<g transform="scale(1,-1)"><rect x="${xmax / 2 - 330}" y="-400" width="660" height="90" rx="20" fill="var(--card)" stroke="var(--sep)"/><text x="${xmax / 2}" y="-342" text-anchor="middle" font-size="30" fill="var(--label)" font-family="system-ui">🔒 Waits for ${KR.blockedBy(cur).join(", ")} to be approved</text></g>`;
    $("cv").innerHTML = s + "</g>";
    $("cv").querySelectorAll(".stk[data-i]").forEach(p => p.addEventListener("pointerdown", e => { if (e.target.id === "hdl" || locked()) return; sel = +p.dataset.i; render(); }));
  }

  // ---------------- inspector
  const num = (lbl, key, v, min, max, step, obj) => `<div class="f"><span>${lbl}</span><input type="range" min="${min}" max="${max}" step="${step}" value="${v}" data-k="${key}" data-o="${obj}"><input type="number" inputmode="decimal" min="${min}" max="${max}" step="${step}" value="${v}" data-k="${key}" data-o="${obj}"></div>`;
  const HEADINGS = Array.from({ length: 12 }, (_, i) => i * 30);
  function inspector() {
    const d = KR.def(cur), mine = own(), t = mine[sel], e = KR.EDIT[cur] || {}, st = KR.status(cur), comp = d.type === "composite", L = comp ? KR.resolve(cur).filter(s => s.locked).length : 0;
    let s = `<h4 class="ttl"><b>${cur}</b><span class="badge ${st}">${{ approved: "approved", fix: "needs fix", draft: "draft" }[st]}</span></h4>`;
    if (comp) {
      s += `<h4>Locked parts <small>follow the approved radical</small></h4>` + d.comps.map((c, i) => `<div class="sg"><div class="hd"><span>🔒</span><a href="#${encodeURIComponent(c.ref)}">${c.ref}</a><span class="grow"></span><span class="r">${KR.status(c.ref)}</span></div>
        ${locked() ? "" : num("Move x", "dx", Math.round(c.dx || 0), -400, 1200, 1, "c" + i) + num("Move y", "dy", Math.round(c.dy || 0), -300, 300, 1, "c" + i) + num("Scale", "s", Math.round((c.s ?? 1) * 100), 40, 120, 1, "c" + i)}</div>`).join("");
      if (locked()) { $("ins").innerHTML = s + `<p class="hint">This glyph is built on ${KR.blockedBy(cur).join(", ")}. Approve ${KR.blockedBy(cur).length > 1 ? "them" : "it"} first, then add the modifier here.</p>`; return; }
    }
    s += `<h4>${comp ? "Modifier strokes" : "Strokes in " + cur}<span class="btns">${comp && d.kind === "bar" ? `<button class="mini" id="autobar" title="Put the bar back where the rightmost element can branch into it">Auto-place bar</button>` : ""}<button class="mini" id="order" title="Left before right, top before bottom, vertical before horizontal">Auto order</button></span></h4><div class="slist">` +
      mine.map((x, i) => `<div class="srow" data-i="${i}" aria-current="${i === sel}"><span class="n">${L + i + 1}</span><span class="e">${KS.elements(x).filter(q => q !== "corner").join(" → ") || "empty"}</span></div>`).join("") +
      `</div><div class="btns" style="margin-top:8px"><button class="mini pri" id="finish" title="Start a new stroke where this one ends">Finish stroke → new</button><button class="mini" id="new">New stroke</button></div>`;
    if (t) {
      const tr = KS.trace(t);
      s += `<h4>Stroke ${L + sel + 1}<span class="btns"><button class="mini" data-a="up">↑</button><button class="mini" data-a="down">↓</button><button class="mini" data-a="dup">Duplicate</button><button class="mini" data-a="mir">Mirror</button><button class="mini" data-a="rev">Reverse</button><button class="mini" data-a="del">Delete</button></span></h4>
      ${num("Start x", "x", t.x, -100, 1400, 1, "s")}${num("Start y", "y", t.y, 0, 700, 1, "s")}${num("Heading", "h", t.h, 0, 359, 1, "s")}
      <div class="hb">${HEADINGS.map(a => `<button data-h="${a}">${a}°</button>`).join("")}</div>
      <h4>Endpoint</h4>${num("Start", "s", Math.round((t.s ?? 0) * 100), 0, 100, 1, "p")}${num("End", "e", Math.round((t.e ?? 1) * 100), 0, 100, 1, "p")}
      <div class="f"><span>Start cap</span><select data-cap="cap0"><option value="auto">Cut flat at 0 / 700</option><option value="butt">Plain</option></select><span></span></div>
      <div class="f"><span>End cap</span><select data-cap="cap1"><option value="auto">Cut flat at 0 / 700</option><option value="butt">Plain</option></select><span></span></div>
      <p class="hint">Ends at x ${Math.round(tr.x)}, y ${Math.round(tr.y)}, heading ${Math.round(((tr.h % 360) + 360) % 360)}° · length ${Math.round(tr.len)}</p>
      <h4>Segments<span class="btns"><button class="mini" data-add="L">+ Line</button><button class="mini" data-add="A">+ Arc</button><button class="mini" data-add="C">+ Corner</button></span></h4>` +
        t.segs.map((q, j) => `<div class="sg"><div class="hd"><span>${j + 1}</span><select data-ty="${j}"><option value="L"${q.t === "L" ? " selected" : ""}>Line</option><option value="A"${q.t === "A" ? " selected" : ""}>Arc</option><option value="C"${q.t === "C" ? " selected" : ""}>Corner</option></select><button class="mini" data-sx="${j}">✕</button></div>
        ${q.t === "L" ? num("Length", "len", q.len, 0, 1000, 1, j) : q.t === "A" ? num("Radius", "r", q.r, 10, 400, 1, j) + num("Turn", "ang", q.ang, -720, 720, 5, j) : num("Turn", "ang", q.ang, -180, 180, 5, j)}</div>`).join("") +
        `<p class="hint">Headings snap to 30° steps. Turn: positive turns left (anticlockwise), negative right. Arc 180 = bowl, 270 = curl, 360 = loop; chain arcs for a spiral.</p>`;
    }
    s += `<h4>Notes for ${cur}</h4><textarea id="note" placeholder="What's wrong, which elements are where…">${e.note || ""}</textarea>
      <div class="btns" style="margin-top:8px;justify-content:flex-start"><button class="mini${st === "approved" ? " pri" : ""}" id="ok">✓ Approve</button><button class="mini${st === "fix" ? " pri" : ""}" id="fix">Needs fix</button><button class="mini" id="reset">Reset to draft</button></div>
      <h4>Data</h4><div class="btns" style="justify-content:flex-start"><button class="mini" id="exp">Download all edits</button><label class="mini" style="cursor:pointer">Import<input type="file" id="imp" accept=".json" hidden></label></div>
      <p class="hint">Edits stay in this browser. Download them to keep a copy or to send them to me.</p>`;
    $("ins").innerHTML = s;
    if (t) $("ins").querySelectorAll("[data-cap]").forEach(x => x.value = t[x.dataset.cap] || "auto");
    wire();
  }
  function wireComps() {
    $("ins").querySelectorAll('input[data-o^="c"]').forEach(inp => {
      inp.onpointerdown = inp.onfocus = () => commit();
      inp.oninput = () => {
        const c = E().comps[+inp.dataset.o.slice(1)], k = inp.dataset.k; let v = +inp.value;
        c[k] = k === "s" ? v / 100 : v;
        $("ins").querySelectorAll(`input[data-k="${k}"][data-o="${inp.dataset.o}"]`).forEach(x => { if (x !== inp) x.value = inp.value; });
        prog(); KR.save(); canvas();
      };
      inp.onchange = () => render();
    });
  }
  function wire() {
    const I = $("ins");
    wireComps();
    I.querySelectorAll(".srow").forEach(r => r.onclick = () => { sel = +r.dataset.i; render(); });
    I.querySelectorAll('input[data-k]:not([data-o^="c"])').forEach(inp => {
      inp.onfocus = () => commit(); inp.onpointerdown = () => commit();
      inp.oninput = () => {
        const v = +inp.value, t = E().strokes[sel], o = inp.dataset.o, k = inp.dataset.k;
        if (o === "s") t[k] = v; else if (o === "p") t[k] = v / 100; else t.segs[+o][k] = v;
        I.querySelectorAll(`input[data-k="${k}"][data-o="${o}"]`).forEach(x => { if (x !== inp) x.value = inp.value; });
        prog(); KR.save(); canvas(); const row = I.querySelectorAll(".srow .e")[sel]; if (row) row.textContent = KS.elements(t).filter(q => q !== "corner").join(" → ");
      };
      inp.onchange = () => render();
    });
    I.querySelectorAll("[data-h]").forEach(b => b.onclick = () => { commit(); E().strokes[sel].h = +b.dataset.h; changed(); });
    I.querySelectorAll("[data-cap]").forEach(x => x.onchange = () => { commit(); E().strokes[sel][x.dataset.cap] = x.value; changed(); });
    I.querySelectorAll("[data-ty]").forEach(x => x.onchange = () => { commit(); const j = +x.dataset.ty; E().strokes[sel].segs[j] = x.value === "L" ? { t: "L", len: 100 } : x.value === "A" ? { t: "A", r: 100, ang: 90 } : { t: "C", ang: 90 }; changed(); });
    I.querySelectorAll("[data-sx]").forEach(x => x.onclick = () => { commit(); E().strokes[sel].segs.splice(+x.dataset.sx, 1); changed(); });
    I.querySelectorAll("[data-add]").forEach(x => x.onclick = () => { commit(); const a = x.dataset.add; E().strokes[sel].segs.push(a === "L" ? { t: "L", len: 100 } : a === "A" ? { t: "A", r: 100, ang: -90 } : { t: "C", ang: 90 }); changed(); });
    I.querySelectorAll("[data-a]").forEach(x => x.onclick = () => {
      commit(); const st = E().strokes, t = st[sel], a = x.dataset.a;
      if (a === "up" && sel > 0) { [st[sel - 1], st[sel]] = [st[sel], st[sel - 1]]; sel--; }
      if (a === "down" && sel < st.length - 1) { [st[sel + 1], st[sel]] = [st[sel], st[sel + 1]]; sel++; }
      if (a === "dup") { st.splice(sel + 1, 0, KR.clone(t)); sel++; }
      if (a === "del") { st.splice(sel, 1); sel = Math.max(0, sel - 1); }
      if (a === "mir") { const xs = KR.resolve(cur).flatMap(s => KS.trace(s).joints.map(j => j.x)), cx = (Math.min(...xs) + Math.max(...xs)) / 2, m = KR.clone(t); m.x = 2 * cx - t.x; m.h = (540 - t.h) % 360; m.segs.forEach(q => { if ("ang" in q) q.ang = -q.ang; }); st.splice(sel + 1, 0, m); sel++; }
      if (a === "rev") { const tr = KS.trace(t); st[sel] = Object.assign(KR.clone(t), { x: Math.round(tr.x * 10) / 10, y: Math.round(tr.y * 10) / 10, h: Math.round(((tr.h + 180) % 360 + 360) % 360), segs: t.segs.slice().reverse().map(q => "ang" in q ? Object.assign({}, q, { ang: -q.ang }) : Object.assign({}, q)), s: 1 - (t.e ?? 1), e: 1 - (t.s ?? 0), cap0: t.cap1, cap1: t.cap0 }); }
      changed();
    });
    $("finish").onclick = () => { commit(); const st = E().strokes, t = st[sel]; const tr = t ? KS.trace(t) : { x: 300, y: 350, h: 0 };
      st.push({ x: Math.round(tr.x), y: Math.round(tr.y), h: Math.round(((tr.h % 360) + 360) % 360), segs: [{ t: "L", len: 100 }], s: 0, e: 1, cap0: "auto", cap1: "auto", role: isComp(cur) ? "modifier" : undefined }); sel = st.length - 1; changed(); };
    $("new").onclick = () => { commit(); const st = E().strokes; st.push({ x: 300, y: 350, h: 0, segs: [{ t: "L", len: 200 }], s: 0, e: 1, cap0: "auto", cap1: "auto", role: isComp(cur) ? "modifier" : undefined }); sel = st.length - 1; changed(); };
    $("order").onclick = () => { commit(); const g = E(), t = g.strokes[sel]; g.strokes = KS.autoOrder(g.strokes); sel = Math.max(0, g.strokes.indexOf(t)); changed(); };
    if ($("autobar")) $("autobar").onclick = () => { commit(); autoBar(); changed(); };
    $("note").oninput = e => { E().note = e.target.value; KR.save(); };
    $("ok").onclick = () => { KR.setStatus(cur, KR.status(cur) === "approved" ? "draft" : "approved"); pick(); render(); };
    $("fix").onclick = () => { KR.setStatus(cur, KR.status(cur) === "fix" ? "draft" : "fix"); pick(); render(); };
    $("reset").onclick = () => { if (confirm(`Reset ${cur} to the draft? Your edits to it are lost.`)) { delete KR.EDIT[cur]; KR.save(); sel = 0; pick(); render(); } };
    $("exp").onclick = () => { const a = document.createElement("a"); a.href = URL.createObjectURL(new Blob([JSON.stringify(KR.EDIT, null, 1)], { type: "application/json" })); a.download = "kradin-edits.json"; a.click(); };
    $("imp").onchange = e => { const f = e.target.files[0]; if (!f) return; f.text().then(t => { try { Object.assign(KR.EDIT, JSON.parse(t)); KR.save(); pick(); render(); } catch (err) { alert("Not a valid edits file"); } }); };
  }

  // the bar starts on the rightmost element at its height and runs past the sign
  function autoBar() {
    const g = E(), bar = g.strokes.find(s => s.segs.length === 1 && s.segs[0].t === "L" && Math.abs(((s.h % 360) + 360) % 360) < 1); if (!bar) return;
    const lock = KR.resolve(cur).filter(s => s.locked), pts = [];
    lock.forEach(s => { const P = KS.centreline(s); for (let i = 1; i < P.length; i++) { const a = P[i - 1], b = P[i], n = Math.max(1, Math.ceil(Math.hypot(b[0] - a[0], b[1] - a[1]) / 6)); for (let j = 0; j <= n; j++) pts.push([a[0] + (b[0] - a[0]) * j / n, a[1] + (b[1] - a[1]) * j / n]); } });
    const xmax = Math.max(...pts.map(p => p[0])), NEED = 137.2, JR = 1.6 * NEED, target = bar.y;
    let best = null;
    for (let dy = 0; dy <= 200; dy += 4) for (const sg of dy ? [1, -1] : [1]) {
      const yb = target + sg * dy; if (yb < 49 || yb > 651) continue;
      let x0 = -1e9;
      for (let i = 1; i < pts.length; i++) { const a = pts[i - 1], b = pts[i]; if ((a[1] - yb) * (b[1] - yb) <= 0 && Math.hypot(b[0] - a[0], b[1] - a[1]) < 10) { const x = a[1] === b[1] ? Math.max(a[0], b[0]) : a[0] + (yb - a[1]) * (b[0] - a[0]) / (b[1] - a[1]); x0 = Math.max(x0, x); } }
      if (x0 < -1e8) continue;
      const xe = Math.max(xmax, x0) + 170;
      const bad = pts.some(([x, y]) => x >= x0 - 1 && Math.hypot(x - x0, y - yb) > JR && Math.hypot(x - Math.min(Math.max(x, x0), xe), y - yb) < NEED - 3);
      if (bad) continue;
      const score = dy + 1.2 * Math.max(0, xmax - 60 - x0);
      if (!best || score < best[0]) best = [score, x0, yb, xe];
    }
    if (best) { bar.x = Math.round(best[1] * 10) / 10; bar.y = Math.round(best[2]); bar.segs[0].len = Math.round(best[3] - best[1]); }
  }

  function render() { canvas(); inspector(); prog(); }
  function prog() { document.querySelectorAll("input[type=range]").forEach(el => el.style.setProperty("--p", (el.value - el.min) / (el.max - el.min) * 100 + "%")); }

  // dragging the start handle, with snapping (to guides and to every joint, locked parts included)
  function pt(e) { const m = $("flip").getScreenCTM().inverse(), p = new DOMPoint(e.clientX, e.clientY).matrixTransform(m), k = KS.K(W()); return { x: p.x / k, y: 350 + (p.y - 350) / k }; }
  function snap(x, y) {
    let sx = Math.round(x / 5) * 5, sy = Math.round(y / 5) * 5;
    for (const a of [0, 49, 350, 651, 700]) if (Math.abs(y - a) < 14) sy = a;
    KR.resolve(cur).forEach((t, i) => { if (!t.locked && i - KR.resolve(cur).filter(s => s.locked).length === sel) return; KS.trace(t).joints.forEach(j => { if (Math.hypot(j.x - x, j.y - y) < 16) { sx = Math.round(j.x * 10) / 10; sy = Math.round(j.y * 10) / 10; } }); });
    return [sx, sy];
  }
  let drag = false;
  function init() {
    const cv = $("cv");
    cv.addEventListener("pointerdown", e => { if (e.target.id !== "hdl") return; commit(); drag = true; cv.setPointerCapture(e.pointerId); e.preventDefault(); });
    cv.addEventListener("pointermove", e => { if (!drag) return; const p = pt(e), t = E().strokes[sel];[t.x, t.y] = snap(p.x, p.y); KR.save(); canvas(); });
    cv.addEventListener("pointerup", () => { if (drag) { drag = false; render(); } });
    document.addEventListener("keydown", e => {
      if (/INPUT|TEXTAREA|SELECT/.test(document.activeElement.tagName) || locked()) return;
      const t = own()[sel]; if (!t) return; const d = e.shiftKey ? 25 : 5, m = { ArrowLeft: [-d, 0], ArrowRight: [d, 0], ArrowUp: [0, d], ArrowDown: [0, -d] }[e.key];
      if (m) { e.preventDefault(); commit(); const g = E().strokes[sel]; g.x += m[0]; g.y += m[1]; changed(); }
      if ((e.metaKey || e.ctrlKey) && e.key === "z") { e.preventDefault(); $("undo").click(); }
    });
    $("undo").onclick = () => { if (!hist.length) return; KR.EDIT[cur] = JSON.parse(hist.pop()); changed(); };
    $("play").onclick = () => {
      const ps = [...$("cv").querySelectorAll(".stk")]; let t = 0;
      ps.forEach(p => { p.setAttribute("pathLength", "1000"); p.style.strokeDasharray = "1000 3000"; p.style.strokeDashoffset = "1000"; });
      ps.forEach(p => { p.animate([{ strokeDashoffset: 1000 }, { strokeDashoffset: 0 }], { duration: 650, delay: t, fill: "forwards", easing: "ease-in-out" }); t += 800; });
      setTimeout(render, t + 400);
    };
    ["w", "gh", "cl", "hide"].forEach(i => $(i).oninput = () => { $("wv").textContent = W(); prog(); canvas(); });
    if ($("exportAll")) {
      const doExport = test => {
        const name = prompt(test ? "Name this test build" : "Name this font", test ? "Test " + new Date().toLocaleString() : "Kɔradin " + new Date().toLocaleDateString());
        if (name === null) return;
        try { KR.exportFont(name, test); location.href = "index.html#font=latest"; } catch (err) { alert(err.message); }
      };
      $("exportAll").onclick = () => doExport(false);
      $("exportTest").onclick = () => doExport(true);
    }
    addEventListener("hashchange", () => openG(decodeURIComponent(location.hash.slice(1))));
  }
  Promise.all([KR.load(), fetch("radicals-ghost.json").then(r => r.json())]).then(([_, g]) => { GH = g; init(); openG(decodeURIComponent(location.hash.slice(1)) || "a"); });
})();
