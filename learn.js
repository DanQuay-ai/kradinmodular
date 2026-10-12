/* Sua: the learning game. Needs twi.js, kfont.js, icons.js, mnemonics.js, learn-data.js. */
(() => {
  const $ = id => document.getElementById(id);
  const esc = s => String(s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);
  const shuffle = a => { a = a.slice(); for (let i = a.length - 1; i > 0; i--) { const j = Math.random() * (i + 1) | 0; [a[i], a[j]] = [a[j], a[i]]; } return a; };
  const pick = (a, n) => shuffle(a).slice(0, n);
  const uniq = a => [...new Set(a)];
  const V = ["a", "e", "ɛ", "i", "o", "ɔ", "u"];
  const LS = { get(k, d) { try { const v = localStorage.getItem(k); return v ? JSON.parse(v) : d; } catch (e) { return d; } }, set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} } };
  const S = Object.assign({ done: {}, xp: 0, streak: 0, last: "", script: "latin", dialect: "asante", mute: false }, LS.get("sua", {}));
  const save = () => LS.set("sua", S);

  // ---------------------------------------------------------- language
  let L = window.NA_LANG || "en";
  if (L !== "fr") L = "en";
  const TX = {
    en: { title: "Learn Kɔradin.<br>Learn Akan.", cowries: "cowries", streak: "day streak", krTitle: "Kɔradin", krSub: "Every sign, family by family, until you can read any Akan word.",
      akTitle: "Akan", akSub: "Greetings, numbers, the market and everyday talk.", lessons: "lessons", units: "units", of: "of", literate: "literate", language: "Language", soon: "soon",
      standard: "Standard", final: "Literacy test", finalSub: "Read 15 words with no help", words: "words", newLesson: "New lesson", newSign: "New sign", newWords: "New words",
      start: "Start", gotit: "Got it", check: "Check", cont: "Continue", again: "again", whichSound: "Which sound is this?", whichSign: s => `Which sign is “${s}”?`,
      read: "Read this word", readThis: "Read this", mean: "What does this mean?", say: s => `How do you say “${s}”?`, sayPh: s => `Say “${s}”`, match: "Match the pairs",
      pic: s => `Which one is “${s}”?`, findSign: s => `Tap the sign “${s}” in this word`, spell: s => `Spell “${s}” in Kɔradin`,
      looks: x => `This sign looks like ${x}.`, sound: s => `It represents the sound <b>${s}</b>.`, first: (s, w) => `<b>${s}</b> is the first sound of <b>${w}</b>.`, inw: (s, w) => `You hear <b>${s}</b> in <b>${w}</b>.`,
      grows: (v, b) => `<b>${v}</b> grows from <b>${b}</b>.`, good: ["Ɛyɛ!", "Ampa!", "Papa!", "Ayeekoo!"], notq: "Not quite", answer: "Answer", firstTry: (r, t) => `${r} of ${t} right first time`,
      unlocked: "Next lesson unlocked.", youRead: "You can read Kɔradin.", share: "Every family, every vowel, every mark. Write your name at neoakan.com/kradin.", locked: "Score 85% on the previous lesson first", quit: "Quit", sound_: "Sound", best: "best", need: p => `${p}%. You need 85% to unlock the next lesson.`, passed: p => `${p}%. Lesson passed.`, retry: "Try again" },
    fr: { title: "Apprenez le kɔradin.<br>Apprenez l'akan.", cowries: "cauris", streak: "jours d'affilée", krTitle: "Kɔradin", krSub: "Chaque signe, famille par famille, jusqu'à lire n'importe quel mot akan.",
      akTitle: "Akan", akSub: "Salutations, nombres, le marché et la vie de tous les jours.", lessons: "leçons", units: "unités", of: "sur", literate: "lettré", language: "Langue", soon: "bientôt",
      standard: "Latin", final: "Test de lecture", finalSub: "Lisez 15 mots sans aide", words: "mots", newLesson: "Nouvelle leçon", newSign: "Nouveau signe", newWords: "Nouveaux mots",
      start: "Commencer", gotit: "Compris", check: "Vérifier", cont: "Continuer", again: "à revoir", whichSound: "Quel son est-ce ?", whichSign: s => `Quel signe correspond à « ${s} » ?`,
      read: "Lisez ce mot", readThis: "Lisez ceci", mean: "Que signifie ceci ?", say: s => `Comment dit-on « ${s} » ?`, sayPh: s => `Dites « ${s} »`, match: "Associez les paires",
      pic: s => `Lequel est « ${s} » ?`, findSign: s => `Touchez le signe « ${s} » dans ce mot`, spell: s => `Écrivez « ${s} » en kɔradin`,
      looks: x => `Ce signe ressemble à ${x}.`, sound: s => `Il représente le son <b>${s}</b>.`, first: (s, w) => `<b>${s}</b> est le premier son de <b>${w}</b>.`, inw: (s, w) => `On entend <b>${s}</b> dans <b>${w}</b>.`,
      grows: (v, b) => `<b>${v}</b> dérive de <b>${b}</b>.`, good: ["Ɛyɛ !", "Ampa !", "Papa !", "Ayeekoo !"], notq: "Pas tout à fait", answer: "Réponse", firstTry: (r, t) => `${r} sur ${t} justes du premier coup`,
      unlocked: "Leçon suivante débloquée.", youRead: "Vous savez lire le kɔradin.", share: "Chaque famille, chaque voyelle, chaque marque. Écrivez votre nom sur neoakan.com/kradin.", locked: "Obtenez d'abord 85 % à la leçon précédente", quit: "Quitter", sound_: "Son", best: "record", need: p => `${p} %. Il faut 85 % pour débloquer la leçon suivante.`, passed: p => `${p} %. Leçon réussie.`, retry: "Réessayer" },
  };
  const T = TX[L];
  document.documentElement.lang = L;
  const gloss = it => L === "fr" ? it[2] : it[1];
  const kv = it => it[4] || it[0];
  const lt = (l, k) => (l[L] || l.en)[k];

  // ---------------------------------------------------------- sound (synthesised, no files)
  let AC = null;
  // iPhones play web audio through the ringer channel, so the silent switch mutes it. Asking for the
  // "playback" session (Safari 17+) and starting a silent <audio> on the first touch moves it to the media channel.
  function unlockAudio() {
    try { if (navigator.audioSession) navigator.audioSession.type = "playback"; } catch (e) {}
    try {
      AC = AC || new (window.AudioContext || window.webkitAudioContext)();
      if (AC.state === "suspended") AC.resume();
      const b = AC.createBuffer(1, 1, 22050), src = AC.createBufferSource(); src.buffer = b; src.connect(AC.destination); src.start(0);
    } catch (e) {}
    try { // a real, silent WAV built on the fly
      const n = 800, buf = new ArrayBuffer(44 + n), v = new DataView(buf), w = (o, t) => [...t].forEach((c, i) => v.setUint8(o + i, c.charCodeAt(0)));
      w(0, "RIFF"); v.setUint32(4, 36 + n, true); w(8, "WAVEfmt "); v.setUint32(16, 16, true); v.setUint16(20, 1, true); v.setUint16(22, 1, true);
      v.setUint32(24, 8000, true); v.setUint32(28, 8000, true); v.setUint16(32, 1, true); v.setUint16(34, 8, true); w(36, "data"); v.setUint32(40, n, true);
      for (let i = 0; i < n; i++) v.setUint8(44 + i, 128);
      const a = new Audio(URL.createObjectURL(new Blob([buf], { type: "audio/wav" }))); a.setAttribute("playsinline", ""); a.play().catch(() => {});
    } catch (e) {}
    removeEventListener("pointerdown", unlockAudio, true); removeEventListener("touchend", unlockAudio, true);
  }
  addEventListener("pointerdown", unlockAudio, true); addEventListener("touchend", unlockAudio, true);
  function tone(notes, type = "sine", vol = .14) {
    if (S.mute) return;
    try {
      AC = AC || new (window.AudioContext || window.webkitAudioContext)();
      if (AC.state === "suspended") AC.resume();
      const t0 = AC.currentTime;
      notes.forEach(([f, at, d]) => {
        const o = AC.createOscillator(), g = AC.createGain();
        o.type = type; o.frequency.value = f; o.connect(g); g.connect(AC.destination);
        g.gain.setValueAtTime(0, t0 + at); g.gain.linearRampToValueAtTime(vol, t0 + at + .015); g.gain.exponentialRampToValueAtTime(.0008, t0 + at + d);
        o.start(t0 + at); o.stop(t0 + at + d + .05);
      });
    } catch (e) {}
  }
  const SFX = {
    ok: () => tone([[784, 0, .16], [1175, .09, .28]], "triangle", .16),
    bad: () => tone([[196, 0, .18], [165, .11, .26]], "square", .06),
    tap: () => tone([[1400, 0, .04]], "sine", .05),
    done: () => tone([[523, 0, .2], [659, .12, .2], [784, .24, .2], [1047, .36, .5]], "triangle", .15),
  };

  // ---------------------------------------------------------- Kɔradin words, syllable by syllable
  const ONS = ["kp", "gb", "ky", "gy", "hy", "ny", "tw", "dw", "hw", "kw", "my", "b", "d", "f", "g", "h", "j", "k", "l", "m", "n", "p", "r", "s", "t", "v", "w", "y", "z"];
  const VV = "aeiouɛɔ";
  function seg(lat) {
    const w = TwiScript.toKradin(lat).replace(/[^a-zɛɔŋ]/g, ""), out = []; let i = 0;
    while (i < w.length) {
      let pre = "";
      const m = w.slice(i).match(/^(ng|m|n)(?=[^aeiouɛɔ])/);
      if (m && !ONS.some(o => o.length > 1 && w.startsWith(o, i) && VV.includes(w[i + o.length]))) { pre = m[1]; i += pre.length; }
      const o = ONS.find(x => w.startsWith(x, i) && VV.includes(w[i + x.length])) || "";
      const v = w[i + o.length];
      if (!v || !VV.includes(v)) { out.push({ t: pre + w[i], s: w[i], nas: true }); i++; continue; }
      const s = o + v; i += s.length;
      const r = w.slice(i).match(/^(ng|m|n)(?![aeiouɛɔy])/); let c = ""; if (r) { c = r[1]; i += c.length; }
      out.push({ t: pre + s + c, s, nas: !!(pre || c) });
    }
    return out;
  }
  // a word in Kɔradin, each syllable its own span; hl marks the syllable to highlight
  function krw(lat, hl, cls = "", tap) {
    return `<span class="krw ${cls}">${lat.split(/\s+/).map(word => `<span class="wd">${seg(word).map((c, i) =>
      `<span class="kr-i sy${hl && c.s === hl ? " hl" : ""}"${tap ? ` data-tap="${esc(c.s)}" data-i="${i}"` : ""} data-tw="${esc(c.t)}"></span>`).join("")}</span>`).join("")}</span>`;
  }
  const kr = (lat, cls = "") => `<span class="kr-i ${cls}" data-tw="${esc(lat)}"></span>`;
  const sizeFor = (lat, max = 110) => Math.max(34, Math.min(max, Math.floor(560 / Math.max(1.6, seg(lat).length + (lat.split(" ").length - 1) * .6))));
  const paint = el => KF.paint(el || document.body);

  // the corpus every keyword and reading word is drawn from
  let HAS = new Set();
  const CORPUS = () => uniq(LEARN.twi.flatMap(u => u.items.map(i => i[0])).concat(LEARN.script.flatMap(l => Object.values(l.key || {}))).flatMap(p => p.split(/\s+/)).map(w => w.toLowerCase().replace(/[^a-zɛɔ']/g, "")).filter(w => w.length > 1));
  function keywordFor(s, pref) {
    const has = w => seg(w).some(c => c.s === s);
    if (pref && has(pref.toLowerCase())) return pref;
    const C = CORPUS().filter(has);
    if (!C.length) return null;
    const starts = C.filter(w => seg(w)[0].s === s);
    return (starts.length ? starts : C).sort((a, b) => a.length - b.length)[0];
  }
  const onsetOf = s => s.slice(0, -1);
  const lessonSyl = l => [l.base, ...(l.vars || [])].flatMap(o => V.map(v => o + v)).filter(s => s.length === 1 || HAS.has(s));
  function learned(upto) {
    const set = new Set();
    for (const l of LEARN.script) { if (l.base === undefined) { if (l.id === upto) break; continue; } lessonSyl(l).forEach(s => set.add(s)); if (l.id === upto) break; }
    return set;
  }
  const readable = (w, set, nasOk) => { const g = seg(w); return g.length && g.every(c => set.has(c.s) && (nasOk || !c.nas)); };

  // ---------------------------------------------------------- home
  const icon = (n, s = 22) => ICON(n, s);
  function home() {
    const sDone = LEARN.script.filter(l => S.done["s-" + l.id]).length, tDone = LEARN.twi.filter(l => S.done["t-" + l.id]).length, allS = sDone === LEARN.script.length;
    $("app").innerHTML = `
      <header class="hd rise"><div><p class="ey">NeoAkan · Sua</p><h1>${T.title}</h1></div>
        <div class="stats"><span class="st fl${S.streak ? " on" : ""}">${icon("flame", 20)}<b>${S.streak}</b> ${T.streak}</span><span class="st cw">${icon("cowrie", 20)}<b>${S.xp}</b> ${T.cowries}</span>
        <button class="st mt" id="mute" aria-label="${T.sound_}">${icon(S.mute ? "mute" : "sound", 20)}</button></div></header>
      <div class="mods">
        <section class="mod rise" style="--d:.05s">
          <div class="mh">${kr("kɔradin", "mk")}<div><h2>${T.krTitle}</h2><p>${T.krSub}</p></div></div>
          <div class="bar"><i style="width:${100 * sDone / LEARN.script.length}%"></i></div><p class="sm">${sDone} ${T.of} ${LEARN.script.length} ${T.lessons}${allS ? " · " + T.literate : ""}</p>
          <ol class="path">${LEARN.script.map((l, i) => node("s", l, i, LEARN.script)).join("")}
            <li><button class="nd final${allS ? "" : " lock"}" data-final="1"><span class="ic">${icon("star", 24)}</span><span><b>${T.final}</b><small>${T.finalSub}</small></span></button></li></ol>
        </section>
        <section class="mod rise" style="--d:.12s">
          <div class="mh">${kr("akan", "mk")}<div><h2>${T.akTitle}</h2><p>${T.akSub}</p></div></div>
          <div class="opts">
            <label class="sl"><span>${T.language}</span><select id="dia">${LEARN.dialects.map(d => `<option value="${d.id}" ${d.on ? "" : "disabled"}>${d.name}${d.on ? "" : " · " + T.soon}</option>`).join("")}</select></label>
            <div class="tg" role="group"><button data-sc="latin" aria-pressed="${S.script === "latin"}">${T.standard}</button><button data-sc="kr" aria-pressed="${S.script === "kr"}">Kɔradin</button></div>
          </div>
          <div class="bar"><i style="width:${100 * tDone / LEARN.twi.length}%"></i></div><p class="sm">${tDone} ${T.of} ${LEARN.twi.length} ${T.units}</p>
          <ol class="path">${LEARN.twi.map((l, i) => node("t", l, i, LEARN.twi)).join("")}</ol>
        </section>
      </div>`;
    $("dia").value = S.dialect;
    $("dia").onchange = e => { S.dialect = e.target.value; save(); };
    $("mute").onclick = () => { S.mute = !S.mute; save(); home(); };
    document.querySelectorAll("[data-sc]").forEach(b => b.onclick = () => { S.script = b.dataset.sc; save(); SFX.tap(); home(); });
    document.querySelectorAll(".nd[data-k]").forEach(b => b.onclick = () => { if (b.classList.contains("lock")) return nope(b); SFX.tap(); start(b.dataset.k, b.dataset.id); });
    const f = document.querySelector("[data-final]"); f.onclick = () => f.classList.contains("lock") ? nope(f) : start("f", "final");
    paint($("app"));
  }
  function node(k, l, i, all) {
    const done = S.done[k + "-" + l.id], open = i === 0 || S.done[k + "-" + all[i - 1].id] || done, best = (S.best || {})[k + "-" + l.id];
    const title = k === "s" ? lt(l, "title") : l[L] || l.en;
    const sub = k === "s" ? (l.base !== undefined ? [l.base || "a e ɛ i o ɔ u", ...(l.vars || [])].join(" · ") : "") : l.items.length + " " + T.words;
    const ic = k === "s" ? kr(l.kr) : icon(l.icon, 24);
    return `<li><button class="nd${done ? " done" : ""}${open ? "" : " lock"}" data-k="${k}" data-id="${l.id}" title="${open ? "" : T.locked}"><span class="ic">${ic}</span><span><b>${esc(title)}</b><small>${esc(sub)}</small></span>${best ? `<em class="bs${best[0] / best[1] >= .85 ? " ok" : ""}">${best[0]}/${best[1]}</em>` : ""}${done ? `<i class="ck">${icon("check", 20)}</i>` : open ? "" : `<i class="ck">${icon("lock", 18)}</i>`}</button></li>`;
  }
  function nope(b) { SFX.bad(); b.classList.remove("shk"); void b.offsetWidth; b.classList.add("shk"); }

  // ---------------------------------------------------------- questions
  function scriptQs(l) {
    const Q = [{ t: "card", h: lt(l, "title"), body: lt(l, "intro"), rules: (l.rules || {})[L] || (l.rules || {}).en, show: l.kr }];
    if (l.nasal || l.clusters) {
      const W = l.words.map(w => Array.isArray(w) ? w : [w, w]);
      W.forEach(([lat, k]) => Q.push({ t: "mc", ask: T.read, big: k, kr: true, ans: lat, opts: [lat, ...pick(W.map(x => x[0]).filter(x => x !== lat), 3)] }));
      return Q;
    }
    const mine = lessonSyl(l), set = learned(l.id), M = window.MNEMO || {};
    const groups = [l.base, ...(l.vars || [])];
    groups.forEach(o => {
      const row = V.map(v => o + v).filter(s => mine.includes(s));
      row.forEach(s => Q.push({ t: "learn", s, key: keywordFor(s, (l.key || {})[s]), look: (M[s] || {}).look, base: o === l.base ? null : l.base + s.slice(o.length) }));
      // three quick checks after each row
      pick(row, Math.min(3, row.length)).forEach(s => Q.push({ t: "mc", ask: T.whichSound, big: s, kr: true, ans: s, opts: [s, ...pick(mine.filter(x => x !== s), 3)] }));
    });
    pick(mine, 4).forEach(s => Q.push({ t: "mcg", ask: T.whichSign(s), ans: s, opts: [s, ...pick(mine.filter(x => x !== s), 3)] }));
    // reading: only words made of signs learned so far, with at least one from this lesson
    const words = CORPUS().filter(w => readable(w, set, false) && seg(w).some(c => mine.includes(c.s)));
    pick(words, 4).forEach(w => Q.push({ t: "mc", ask: T.read, big: w, kr: true, ans: w, opts: [w, ...pick(CORPUS().filter(x => x !== w && x.length <= w.length + 3), 3)] }));
    pick(words.filter(w => seg(w).length > 1), 2).forEach(w => { const c = pick(seg(w).filter(c => mine.includes(c.s)), 1)[0]; Q.push({ t: "find", ask: T.findSign(c.s), word: w, ans: c.s }); });
    pick(words.filter(w => seg(w).length > 1 && seg(w).length < 5), 2).forEach(w => Q.push({ t: "spell", ask: T.spell(w), word: w, tiles: shuffle(seg(w).map(c => c.s).concat(pick(mine.filter(x => !seg(w).some(c => c.s === x)), 3))) }));
    return Q;
  }
  function finalQs() {
    const set = learned(null), words = shuffle(CORPUS().filter(w => readable(w, set, true)));
    return words.slice(0, 15).map(w => ({ t: "mc", ask: T.readThis, big: w, kr: true, ans: w, opts: [w, ...pick(words.filter(x => x !== w), 3)] }));
  }
  function twiQs(u) {
    const k = S.script === "kr", items = u.items, Q = [{ t: "words", h: u[L] || u.en, items }];
    const withIcon = items.filter(i => i[3]);
    shuffle(items).forEach((it, i) => {
      const others = items.filter(x => x !== it), m = i % 4;
      if (m === 0) Q.push({ t: "mc", ask: T.mean, big: k ? kv(it) : it[0], kr: k, icon: it[3], ans: gloss(it), opts: [gloss(it), ...pick(others.map(gloss), 3)] });
      else if (m === 1) Q.push({ t: "mc", ask: T.say(gloss(it)), ans: it[0], kropt: k, opts: [it[0], ...pick(others.map(x => x[0]), 3)] });
      else if (m === 2 && it[3] && withIcon.length > 3) Q.push({ t: "pic", ask: T.pic(it[0]), word: it[0], kr: k, ans: it[0], opts: [it, ...pick(withIcon.filter(x => x !== it && x[3] !== it[3]), 3)] });
      else Q.push({ t: "match", pairs: pick(items, Math.min(4, items.length)), kr: k });
    });
    (u.phrases || []).forEach(p => Q.push({ t: "build", ask: T.sayPh(gloss(p)), ans: p[0], kr: k, extra: pick(items.flatMap(x => x[0].split(" ")), 2) }));
    return Q;
  }

  // ---------------------------------------------------------- session
  let Q = [], qi = 0, miss = [], key = "", total = 0, right = 0;
  const graded = q => !["card", "learn", "words"].includes(q.t);
  function start(k, id) {
    key = k === "f" ? "final" : k + "-" + id;
    Q = k === "s" ? scriptQs(LEARN.script.find(l => l.id === id)) : k === "t" ? twiQs(LEARN.twi.find(l => l.id === id)) : finalQs();
    qi = 0; miss = []; total = Q.filter(graded).length; right = 0;
    step();
  }
  function frame(inner, foot) {
    const p = Math.round(100 * qi / Q.length);
    $("app").innerHTML = `<div class="ses"><div class="top"><button class="x" id="quit" aria-label="${T.quit}">✕</button><div class="bar big"><i style="width:${p}%"></i></div><button class="x" id="smute" aria-label="${T.sound_}">${icon(S.mute ? "mute" : "sound", 20)}</button><span class="mini cw">${icon("cowrie", 18)}${S.xp}</span></div>
      <div class="q in">${inner}</div><div class="ft" id="ft">${foot || ""}</div></div>`;
    $("quit").onclick = home;
    $("smute").onclick = () => { S.mute = !S.mute; save(); $("smute").innerHTML = icon(S.mute ? "mute" : "sound", 20); };
    paint($("app"));
    document.querySelectorAll(".q [data-lat]").forEach(e => { e.removeAttribute("data-lat"); e.removeAttribute("tabindex"); });
  }
  const show = (lat, krOn, size) => krOn ? krw(lat, null, "", false).replace('class="krw ', `style="font-size:${size || sizeFor(lat)}px" class="krw `) : `<span class="lt">${esc(lat)}</span>`;
  function step() {
    if (qi >= Q.length) { if (miss.length) { Q = Q.concat(miss.map(m => ({ ...m, again: true }))); miss = []; } else return finish(); }
    const q = Q[qi];
    const go = (label, f) => { $("go").onclick = () => { SFX.tap(); (f || next)(); }; };
    if (q.t === "card") { frame(`<p class="ey">${T.newLesson}</p><div class="hero pop">${kr(q.show, "xl")}</div><h2>${esc(q.h)}</h2><p class="body">${esc(q.body)}</p>${(q.rules || []).map((r, i) => `<p class="rule rise" style="--d:${.15 + i * .08}s">${esc(r)}</p>`).join("")}`, `<button class="go" id="go">${T.start}</button>`); return go(); }
    if (q.t === "learn") {
      const kw = q.key, starts = kw && seg(kw)[0].s === q.s;
      frame(`<p class="ey">${T.newSign}</p>
        <div class="hero pop">${q.base ? `<span class="der">${kr(q.base, "lg dim")}<i>→</i></span>` : ""}${kr(q.s, "xl hlg")}</div>
        <h2 class="snd">${esc(q.s)}</h2>
        ${q.look ? `<p class="body">${T.looks(esc(q.look))}</p>` : ""}
        <p class="body">${T.sound(esc(q.s))}${kw ? " " + (starts ? T.first(esc(q.s), esc(kw)) : T.inw(esc(q.s), esc(kw))) : ""}</p>
        ${q.base ? `<p class="rule">${T.grows(esc(onsetOf(q.s)), esc(onsetOf(q.base)))}</p>` : ""}
        ${kw ? `<div class="kw rise" style="--d:.2s">${krw(kw.toLowerCase(), q.s, "lg")}<span>${esc(kw)}</span></div>` : ""}`, `<button class="go" id="go">${T.gotit}</button>`);
      return go();
    }
    if (q.t === "words") {
      frame(`<p class="ey">${T.newWords}</p><h2>${esc(q.h)}</h2><ul class="wl">${q.items.map((i, n) => `<li class="rise" style="--d:${n * .03}s">${i[3] ? `<span class="wi">${icon(i[3], 26)}</span>` : `<span class="wi"></span>`}<span>${S.script === "kr" ? krw(kv(i), null, "md") + `<small>${esc(i[0])}</small>` : `<b>${esc(i[0])}</b>`}</span><span class="gl">${esc(gloss(i))}</span></li>`).join("")}</ul>`, `<button class="go" id="go">${T.start}</button>`);
      return go();
    }
    if (q.t === "mc" || q.t === "mcg") {
      const opts = shuffle(uniq(q.opts));
      frame(`<p class="ask">${esc(q.ask)}${q.again ? ` <em class="ag">${T.again}</em>` : ""}</p>
        ${q.icon ? `<div class="pi pop">${icon(q.icon, 72)}</div>` : ""}
        ${q.big ? `<div class="big pop">${show(q.big, q.kr)}</div>` : ""}
        <div class="ops${q.t === "mcg" || q.kropt ? " g" : ""}">${opts.map((o, i) => `<button class="op rise" style="--d:${.04 * i}s" data-v="${esc(o)}">${q.t === "mcg" ? kr(o, "lg") : q.kropt ? krw(o, null, "md") + `<small>${esc(o)}</small>` : esc(o)}</button>`).join("")}</div>`);
      document.querySelectorAll(".op").forEach(b => b.onclick = () => judge(b.dataset.v === q.ans, q, b, `.op[data-v="${CSS.escape(q.ans)}"]`));
      return;
    }
    if (q.t === "pic") {
      const opts = shuffle(q.opts);
      frame(`<p class="ask">${q.kr ? esc(q.ask.replace(q.word, "…")) : esc(q.ask)}</p>${q.kr ? `<div class="big pop">${show(q.word, true, 60)}</div>` : ""}
        <div class="ops pics">${opts.map((o, i) => `<button class="op rise" style="--d:${.04 * i}s" data-v="${esc(o[0])}">${icon(o[3], 56)}<small>${esc(gloss(o))}</small></button>`).join("")}</div>`);
      document.querySelectorAll(".op").forEach(b => b.onclick = () => judge(b.dataset.v === q.ans, q, b, `.op[data-v="${CSS.escape(q.ans)}"]`));
      return;
    }
    if (q.t === "find") {
      frame(`<p class="ask">${esc(q.ask)}</p><div class="big pop tapw">${krw(q.word, null, "", true).replace('class="krw ', `style="font-size:${sizeFor(q.word, 96)}px" class="krw `)}</div>`);
      document.querySelectorAll("[data-tap]").forEach(b => b.onclick = () => { const ok = b.dataset.tap === q.ans; b.classList.add(ok ? "okc" : "badc"); if (!ok) document.querySelectorAll(`[data-tap="${CSS.escape(q.ans)}"]`).forEach(x => x.classList.add("okc")); judge(ok, q, null, null, q.ans); });
      return;
    }
    if (q.t === "spell") {
      frame(`<p class="ask">${esc(q.ask)}</p><div class="ln" id="ln"></div><div class="tl">${q.tiles.map((s, i) => `<button class="ti rise" style="--d:${.03 * i}s" data-v="${esc(s)}">${kr(s, "md")}</button>`).join("")}</div>`, `<button class="go" id="go" disabled>${T.check}</button>`);
      wireTiles(() => [...$("ln").children].map(b => b.dataset.v).join("") === seg(q.word).map(c => c.s).join(""), q, q.word);
      return;
    }
    if (q.t === "match") {
      const Lp = shuffle(q.pairs), R = shuffle(q.pairs);
      frame(`<p class="ask">${T.match}</p><div class="mt"><div>${Lp.map((p, i) => `<button class="mp rise" style="--d:${.04 * i}s" data-s="l" data-v="${esc(p[0])}">${q.kr ? krw(kv(p), null, "md") : esc(p[0])}</button>`).join("")}</div><div>${R.map((p, i) => `<button class="mp rise" style="--d:${.04 * i + .02}s" data-s="r" data-v="${esc(p[0])}">${esc(gloss(p))}</button>`).join("")}</div></div>`);
      let sel = null, left = q.pairs.length, err = false;
      document.querySelectorAll(".mp").forEach(b => b.onclick = () => {
        if (b.disabled) return;
        if (!sel || sel.dataset.s === b.dataset.s) { if (sel) sel.classList.remove("on"); sel = b; b.classList.add("on"); SFX.tap(); return; }
        if (sel.dataset.v === b.dataset.v) { SFX.ok(); [sel, b].forEach(x => { x.classList.remove("on"); x.classList.add("ok"); x.disabled = true; }); sel = null; if (--left === 0) setTimeout(() => judge(!err, q, null, null, null, true), 250); }
        else { err = true; SFX.bad(); [sel, b].forEach(x => { x.classList.add("bad", "shk"); setTimeout(() => x.classList.remove("bad", "on", "shk"), 450); }); sel = null; }
      });
      return;
    }
    if (q.t === "build") {
      const words = q.ans.split(" "), tiles = shuffle(words.concat(uniq(q.extra).filter(x => !words.includes(x))));
      frame(`<p class="ask">${esc(q.ask)}</p><div class="ln" id="ln"></div><div class="tl">${tiles.map((w, i) => `<button class="ti rise" style="--d:${.03 * i}s" data-v="${esc(w)}">${q.kr ? krw(w, null, "md") : esc(w)}</button>`).join("")}</div>`, `<button class="go" id="go" disabled>${T.check}</button>`);
      wireTiles(() => [...$("ln").children].map(b => b.dataset.v).join(" ") === q.ans, q, q.ans);
    }
  }
  function wireTiles(test, q, sol) {
    const ln = $("ln"), go = $("go"), tl = document.querySelector(".tl");
    document.querySelectorAll(".ti").forEach(b => b.onclick = () => { SFX.tap(); (b.parentNode === ln ? tl : ln).append(b); go.disabled = !ln.children.length; });
    go.onclick = () => judge(test(), q, null, null, sol);
  }
  function judge(ok, q, btn, sel, sol, quiet) {
    if (graded(q)) { if (ok && !q.again) right++; if (!ok && !q.again) miss.push(q); }
    document.querySelectorAll(".op,.ti,[data-tap]").forEach(b => { b.disabled = true; b.style.pointerEvents = "none"; });
    if (btn) btn.classList.add(ok ? "ok" : "bad", ok ? "bounce" : "shk");
    if (!ok && sel) { const c = document.querySelector(sel); if (c) c.classList.add("ok"); }
    if (!ok) { const qq = document.querySelector(".q"); qq.classList.remove("shk"); void qq.offsetWidth; if (!btn) qq.classList.add("shk"); }
    if (!quiet) (ok ? SFX.ok : SFX.bad)(); else if (ok) {}
    const ans = sol || q.ans;
    const ansHtml = q.kr || q.t === "spell" || q.t === "find" ? `${krw(ans, null, "sm")} <span>${esc(ans)}</span>` : esc(ans);
    $("ft").innerHTML = `<div class="fb ${ok ? "y" : "n"} up"><div class="fbt"><span class="fbi">${icon(ok ? "check" : "left", 22)}</span><div><b>${ok ? pick(T.good, 1)[0] : T.notq}</b>${ok ? "" : `<p>${T.answer}: ${ansHtml}</p>`}</div></div><button class="go" id="go">${T.cont}</button></div>`;
    paint($("ft"));
    $("go").onclick = () => { SFX.tap(); next(); };
  }
  const next = () => { qi++; step(); };
  function finish() {
    const pct = total ? Math.round(100 * right / total) : 100, pass = pct >= 85, wasDone = S.done[key];
    const gain = 5 + right * 2;
    S.best = S.best || {};
    const b = S.best[key];
    if (!b || right / Math.max(1, total) > b[0] / b[1]) S.best[key] = [right, total];
    S.xp += gain; if (pass) S.done[key] = true;
    const d = new Date(), today = d.toISOString().slice(0, 10), y = new Date(d - 864e5).toISOString().slice(0, 10);
    if (S.last !== today) { S.streak = S.last === y ? S.streak + 1 : 1; S.last = today; }
    save(); (pass ? SFX.done : SFX.bad)();
    const lit = key === "final" && pass;
    frame(`${pass ? `<div class="confetti">${Array.from({ length: 18 }, () => `<i style="--x:${(Math.random() * 2 - 1) * 46}vw;--r:${Math.random() * 720 - 360}deg;--d:${Math.random() * .4}s">${icon("cowrie", 20)}</i>`).join("")}</div>` : ""}
      <div class="hero pop">${kr(pass ? (lit ? "ayeekoo" : "ɛyɛ") : "bio", "lg")}</div><h2>${lit ? T.youRead : pass ? "Ayeekoo!" : (L === "fr" ? "Encore une fois" : "Once more")}</h2>
      <div class="wins"><span class="st sc ${pass ? "on" : "low"}"><b>${right}/${total}</b></span><span class="st cw on">${icon("cowrie", 22)}<b>+${gain}</b></span><span class="st fl on">${icon("flame", 22)}<b>${S.streak}</b></span></div>
      <p class="body">${pass ? T.passed(pct) : T.need(pct)}</p>
      ${lit ? `<p class="rule">${T.share}</p>` : ""}${pass && !wasDone && key.startsWith("s-") && !lit ? `<p class="rule">${T.unlocked}</p>` : ""}`,
      pass ? `<button class="go" id="go">${T.cont}</button>` : `<button class="go" id="again">${T.retry}</button><button class="go ghost" id="go">${T.cont}</button>`);
    $("go").onclick = home;
    if ($("again")) $("again").onclick = () => { SFX.tap(); const [k, ...r] = key.split("-"); key === "final" ? start("f", "final") : start(k, r.join("-")); };
  }

  // ---------------------------------------------------------- boot
  fetch("fontmap.json").then(r => r.json()).then(m => {
    m.liga.forEach(([s]) => HAS.add(s.join("").replace(/eopen/g, "ɛ").replace(/oopen/g, "ɔ")));
  }).catch(() => {}).finally(() => KF.use("dua").then(home));
})();
