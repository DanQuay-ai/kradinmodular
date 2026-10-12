/* Sua: the learning game. Needs twi.js, kfont.js, learn-data.js. */
(() => {
  const $ = id => document.getElementById(id);
  const esc = s => String(s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);
  const shuffle = a => { a = a.slice(); for (let i = a.length - 1; i > 0; i--) { const j = Math.random() * (i + 1) | 0; [a[i], a[j]] = [a[j], a[i]]; } return a; };
  const pick = (a, n) => shuffle(a).slice(0, n);
  const V = ["a", "e", "ɛ", "i", "o", "ɔ", "u"];
  const LS = { get(k, d) { try { const v = localStorage.getItem(k); return v ? JSON.parse(v) : d; } catch (e) { return d; } }, set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} } };

  const S = LS.get("sua", { done: {}, xp: 0, streak: 0, last: "", script: "latin", dialect: "asante" });
  const save = () => LS.set("sua", S);
  let HAS = new Set();
  const kr = (lat, cls = "") => `<span class="kr-i ${cls}" data-tw="${esc(lat)}"></span>`;
  const paint = el => KF.paint(el || document.body);

  // ---------------------------------------------------------- home
  function home() {
    const sDone = LEARN.script.filter(l => S.done["s-" + l.id]).length, tDone = LEARN.twi.filter(l => S.done["t-" + l.id]).length;
    $("app").innerHTML = `
      <header class="hd"><div><p class="ey">NeoAkan · Sua</p><h1>Learn Kɔradin.<br>Learn Twi.</h1></div>
        <div class="stats"><span><b>${S.xp}</b> cowries</span><span><b>${S.streak}</b> day streak</span></div></header>
      <div class="mods">
        <section class="mod">
          <div class="mh">${kr("kɔradin", "mk")}<div><h2>Kɔradin</h2><p>Every sign, family by family, until you can read any Twi word.</p></div></div>
          <div class="bar"><i style="width:${100 * sDone / LEARN.script.length}%"></i></div><p class="sm">${sDone} of ${LEARN.script.length} lessons${sDone === LEARN.script.length ? " · literate" : ""}</p>
          <ol class="path">${LEARN.script.map((l, i) => node("s", l, i, LEARN.script)).join("")}
            <li><button class="nd final${sDone === LEARN.script.length ? "" : " lock"}" data-final="1"><span class="ic">✦</span><span><b>Literacy test</b><small>Read 15 words with no help</small></span></button></li></ol>
        </section>
        <section class="mod">
          <div class="mh">${kr("twi", "mk")}<div><h2>Twi</h2><p>Greetings, numbers, the market and everyday talk.</p></div></div>
          <div class="opts">
            <label class="sl"><span>Language</span><select id="dia">${LEARN.dialects.map(d => `<option value="${d.id}" ${d.on ? "" : "disabled"}>${d.name}${d.on ? "" : " · soon"}</option>`).join("")}</select></label>
            <div class="tg" role="group" aria-label="Script"><button data-sc="latin" aria-pressed="${S.script === "latin"}">Standard</button><button data-sc="kr" aria-pressed="${S.script === "kr"}">Kɔradin</button></div>
          </div>
          <div class="bar"><i style="width:${100 * tDone / LEARN.twi.length}%"></i></div><p class="sm">${tDone} of ${LEARN.twi.length} units</p>
          <ol class="path">${LEARN.twi.map((l, i) => node("t", l, i, LEARN.twi)).join("")}</ol>
        </section>
      </div>
      <p class="credit">Twi vocabulary after Peace Corps Ghana, “Twi For All”. Progress is saved on this device.</p>`;
    $("dia").value = S.dialect;
    $("dia").onchange = e => { S.dialect = e.target.value; save(); };
    document.querySelectorAll("[data-sc]").forEach(b => b.onclick = () => { S.script = b.dataset.sc; save(); home(); });
    document.querySelectorAll(".nd[data-k]").forEach(b => b.onclick = () => { if (b.classList.contains("lock")) return shake(b); start(b.dataset.k, b.dataset.id); });
    const f = document.querySelector("[data-final]"); f.onclick = () => f.classList.contains("lock") ? shake(f) : start("f", "final");
    paint($("app"));
  }
  function node(k, l, i, all) {
    const done = S.done[k + "-" + l.id], open = i === 0 || S.done[k + "-" + all[i - 1].id] || done;
    const n = k === "s" ? (l.onsets ? l.onsets.filter(Boolean).join(" ") || "a e ɛ i o ɔ u" : "") : l.items.length + " words";
    return `<li><button class="nd${done ? " done" : ""}${open ? "" : " lock"}" data-k="${k}" data-id="${l.id}"><span class="ic">${kr(l.kr || l.icon)}</span><span><b>${esc(l.title)}</b><small>${esc(n)}</small></span>${done ? '<i class="ck">✓</i>' : ""}</button></li>`;
  }
  const shake = b => { b.classList.remove("shk"); void b.offsetWidth; b.classList.add("shk"); };

  // ---------------------------------------------------------- building questions
  const syl = l => l.onsets.flatMap(o => V.map(v => o + v)).filter(s => HAS.has(s) || s.length === 1);
  const allSyl = () => [...HAS].filter(s => /^[a-zɛɔ]+$/.test(s)).concat(V);
  function scriptQs(l) {
    const Q = [];
    if (l.nasal || l.clusters) {
      Q.push({ t: "card", h: l.title, body: l.intro, rules: l.rules, show: l.kr });
      const W = l.words.map(w => Array.isArray(w) ? w : [w, w]);
      W.forEach(([lat, k]) => Q.push({ t: "mc", ask: "Read this word", big: k, kr: true, ans: lat, opts: [lat, ...pick(W.map(x => x[0]).filter(x => x !== lat), 3)] }));
      return Q;
    }
    const S1 = syl(l);
    Q.push({ t: "card", h: l.title, body: l.intro, rules: l.rules, show: l.kr });
    // teach in groups of the onset's forms, each with its mnemonic
    S1.forEach(s => {
      const key = l.key[s];
      const m = (window.MNEMO || {})[s] || {};
      Q.push({ t: "learn", s, key, look: m.look });
    });
    const pool = shuffle(S1);
    pool.forEach(s => Q.push({ t: "mc", ask: "Which sound is this?", big: s, kr: true, ans: s, opts: [s, ...pick(S1.filter(x => x !== s), 3)] }));
    pick(S1, Math.min(4, S1.length)).forEach(s => Q.push({ t: "mcg", ask: `Which sign is “${s}”?`, ans: s, opts: [s, ...pick(S1.filter(x => x !== s), 3)] }));
    const keys = Object.entries(l.key).filter(([s]) => S1.includes(s));
    keys.forEach(([s, w]) => Q.push({ t: "mc", ask: "Read this word", big: w.toLowerCase(), kr: true, ans: w, opts: [w, ...pick(Object.values(LEARN.script.flatMap(x => Object.values(x.key || {}))).filter(x => x !== w), 3)] }));
    return Q;
  }
  function finalQs() {
    const words = shuffle(LEARN.twi.flatMap(u => u.items.map(i => i[0])).filter(w => w.split(" ").length <= 2));
    return words.slice(0, 15).map(w => ({ t: "mc", ask: "Read this", big: w, kr: true, ans: w, opts: [w, ...pick(words.filter(x => x !== w), 3)] }));
  }
  function twiQs(u) {
    const kr = S.script === "kr", items = u.items, Q = [];
    Q.push({ t: "words", h: u.title, items });
    shuffle(items).forEach((it, i) => {
      const others = items.filter(x => x !== it);
      if (i % 3 === 0) Q.push({ t: "mc", ask: "What does this mean?", big: it[0], kr, ans: it[1], opts: [it[1], ...pick(others.map(x => x[1]), 3)] });
      else if (i % 3 === 1) Q.push({ t: "mc", ask: `How do you say “${it[1]}”?`, ans: it[0], kropt: kr, opts: [it[0], ...pick(others.map(x => x[0]), 3)] });
      else Q.push({ t: "match", pairs: pick(items, Math.min(4, items.length)), kr });
    });
    (u.phrases || []).forEach(p => Q.push({ t: "build", ask: `Say “${p[1]}”`, ans: p[0], kr, extra: pick(items.flatMap(x => x[0].split(" ")), 2) }));
    return Q;
  }

  // ---------------------------------------------------------- session
  let Q = [], qi = 0, miss = [], key = "", total = 0, right = 0;
  function start(k, id) {
    key = k === "f" ? "final" : k + "-" + id;
    Q = k === "s" ? scriptQs(LEARN.script.find(l => l.id === id)) : k === "t" ? twiQs(LEARN.twi.find(l => l.id === id)) : finalQs();
    qi = 0; miss = []; total = Q.filter(q => !["card", "learn", "words"].includes(q.t)).length; right = 0;
    step();
  }
  function frame(inner, foot) {
    const p = Math.round(100 * qi / Q.length);
    $("app").innerHTML = `<div class="ses"><div class="top"><button class="x" id="quit" aria-label="Quit">✕</button><div class="bar"><i style="width:${p}%"></i></div></div>
      <div class="q">${inner}</div><div class="ft" id="ft">${foot || ""}</div></div>`;
    $("quit").onclick = home;
    paint($("app"));
    // no Latin bubbles inside a session: they would give the answer away
    document.querySelectorAll(".q [data-lat]").forEach(e => { e.removeAttribute("data-lat"); e.removeAttribute("tabindex"); });
  }
  const show = (lat, krOn, cls = "") => krOn ? `${kr(lat, cls)}` : `<span class="lt ${cls}">${esc(lat)}</span>`;
  function step() {
    if (qi >= Q.length) { if (miss.length) { Q = Q.concat(miss.map(m => ({ ...m, again: true }))); miss = []; } else return finish(); }
    const q = Q[qi];
    if (q.t === "card") return frame(`<p class="ey">New lesson</p><div class="hero">${kr(q.show, "xl")}</div><h2>${esc(q.h)}</h2><p class="body">${esc(q.body)}</p>${(q.rules || []).map(r => `<p class="rule">${esc(r)}</p>`).join("")}`, `<button class="go" id="go">Start</button>`), $("go").onclick = next;
    if (q.t === "learn") return frame(`<p class="ey">New sign</p><div class="hero">${kr(q.s, "xl")}</div><h2 class="snd">${esc(q.s)}</h2>
      ${q.look ? `<p class="body">This sign looks like ${esc(q.look)}.</p>` : ""}
      <p class="body">It is the sound <b>${esc(q.s)}</b>${q.key ? `, as in <b>${esc(q.key)}</b>` : ""}.</p>
      ${q.key ? `<div class="kw">${kr(q.key.toLowerCase(), "lg")}<span>${esc(q.key)}</span></div>` : ""}`, `<button class="go" id="go">Got it</button>`), $("go").onclick = next;
    if (q.t === "words") return frame(`<p class="ey">New words</p><h2>${esc(q.h)}</h2><ul class="wl">${q.items.map(i => `<li>${S.script === "kr" ? kr(i[0], "md") + `<small>${esc(i[0])}</small>` : `<b>${esc(i[0])}</b>`}<span>${esc(i[1])}</span></li>`).join("")}</ul>`, `<button class="go" id="go">Start</button>`), $("go").onclick = next;
    if (q.t === "mc" || q.t === "mcg") {
      const opts = shuffle([...new Set(q.opts)]);
      frame(`<p class="ask">${esc(q.ask)}${q.again ? " · again" : ""}</p>${q.big ? `<div class="big">${show(q.big, q.kr, "xl")}</div>` : ""}
        <div class="ops${q.t === "mcg" || q.kropt ? " g" : ""}">${opts.map(o => `<button class="op" data-v="${esc(o)}">${q.t === "mcg" ? kr(o, "lg") : q.kropt ? kr(o, "md") + `<small>${esc(o)}</small>` : esc(o)}</button>`).join("")}</div>`);
      document.querySelectorAll(".op").forEach(b => b.onclick = () => judge(b.dataset.v === q.ans, q, b, `.op[data-v="${CSS.escape(q.ans)}"]`));
      return;
    }
    if (q.t === "match") {
      const L = shuffle(q.pairs), R = shuffle(q.pairs);
      frame(`<p class="ask">Match the pairs</p><div class="mt"><div>${L.map(p => `<button class="mp" data-s="l" data-v="${esc(p[0])}">${show(p[0], q.kr, "md")}</button>`).join("")}</div><div>${R.map(p => `<button class="mp" data-s="r" data-v="${esc(p[0])}">${esc(p[1])}</button>`).join("")}</div></div>`);
      let sel = null, left = q.pairs.length, err = false;
      document.querySelectorAll(".mp").forEach(b => b.onclick = () => {
        if (b.disabled) return;
        if (!sel || sel.dataset.s === b.dataset.s) { if (sel) sel.classList.remove("on"); sel = b; b.classList.add("on"); return; }
        if (sel.dataset.v === b.dataset.v) { [sel, b].forEach(x => { x.classList.remove("on"); x.classList.add("ok"); x.disabled = true; }); sel = null; if (--left === 0) judge(!err, q, null, null, true); }
        else { err = true; [sel, b].forEach(x => { x.classList.add("bad"); setTimeout(() => x.classList.remove("bad", "on"), 450); }); sel = null; }
      });
      return;
    }
    if (q.t === "build") {
      const words = q.ans.split(" "), tiles = shuffle(words.concat(q.extra.filter(x => !words.includes(x))));
      frame(`<p class="ask">${esc(q.ask)}</p><div class="ln" id="ln"></div><div class="tl">${tiles.map((w, i) => `<button class="ti" data-i="${i}" data-v="${esc(w)}">${show(w, q.kr, "md")}</button>`).join("")}</div>`, `<button class="go" id="go" disabled>Check</button>`);
      const ln = $("ln"), go = $("go");
      document.querySelectorAll(".ti").forEach(b => b.onclick = () => { (b.parentNode === ln ? document.querySelector(".tl") : ln).append(b); go.disabled = !ln.children.length; });
      go.onclick = () => judge([...ln.children].map(b => b.dataset.v).join(" ") === q.ans, q, null, null, false, q.ans);
    }
  }
  function judge(ok, q, btn, sel, silent, sol) {
    if (q.t !== "card") { if (ok && !q.again) right++; if (!ok) miss.push(q); }
    document.querySelectorAll(".op,.ti").forEach(b => b.disabled = true);
    if (btn) btn.classList.add(ok ? "ok" : "bad");
    if (!ok && sel) { const c = document.querySelector(sel); if (c) c.classList.add("ok"); }
    const ans = sol || q.ans;
    $("ft").innerHTML = `<div class="fb ${ok ? "y" : "n"}"><div><b>${ok ? pick(["Ɛyɛ!", "Ampa!", "Papa!", "Ayeekoo!"], 1)[0] : "Not quite"}</b>${ok ? "" : `<span>Answer: ${S.script === "kr" && q.kr ? kr(ans, "sm") + " " : ""}${esc(ans)}</span>`}</div><button class="go" id="go">Continue</button></div>`;
    paint($("ft"));
    $("go").onclick = next;
  }
  const next = () => { qi++; step(); };
  function finish() {
    const gain = 10 + right * 2, wasDone = S.done[key];
    S.xp += gain; S.done[key] = true;
    const d = new Date(), today = d.toISOString().slice(0, 10), y = new Date(d - 864e5).toISOString().slice(0, 10);
    if (S.last !== today) { S.streak = S.last === y ? S.streak + 1 : 1; S.last = today; }
    save();
    const lit = key === "final";
    frame(`<div class="hero">${kr(lit ? "ayeekoo" : "ɛyɛ", "xl")}</div><h2>${lit ? "You can read Kɔradin." : "Ayeekoo!"}</h2>
      <p class="body">${right} of ${total} right first time · +${gain} cowries${S.streak > 1 ? ` · ${S.streak} day streak` : ""}</p>
      ${lit ? `<p class="rule">Every family, every vowel, every mark. Share your name in Kɔradin at neoakan.com/kradin.</p>` : ""}
      ${!wasDone && key.startsWith("s-") ? `<p class="rule">Next lesson unlocked.</p>` : ""}`, `<button class="go" id="go">Continue</button>`);
    $("go").onclick = home;
  }

  // ---------------------------------------------------------- boot
  fetch("fontmap.json").then(r => r.json()).then(m => {
    m.liga.forEach(([seq]) => HAS.add(seq.join("").replace(/eopen/g, "ɛ").replace(/oopen/g, "ɔ")));
  }).catch(() => {}).finally(() => KF.use("dua").then(home));
})();
