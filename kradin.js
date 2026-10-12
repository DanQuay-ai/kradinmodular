/* What's your Kradin? Date finder. Needs calendar.js (AK) and kfont.js (KF).
   Ɔkra, names and praise names (mmrane) exactly as in Konadu 2012, Table 2; character after his text. */
const KRADIN = [
  { okra: "Adwo", m: ["Kwadwo"], f: ["Adwoa"], pm: ["Okoto", "Asere"], pf: ["Akoto", "Badwo", "Adae"],
    trait_fr: "calme, artisan de paix, protecteur et intercesseur, si sûr de lui qu'il écoute peu les conseils extérieurs", trait: "calm, a peacemaker, protector and supplicant, so sure of themselves that they are slow to take outside advice" },
  { okra: "Bena", m: ["Kwabena"], f: ["Abena", "Abenaa"], pm: ["Ogyam", "Ɛbo"], pf: ["Kosia", "Atobiaa", "Gyamaa"],
    trait_fr: "ɔbarima, courageux, avec une part d'arrogance ; une fois apaisé, protecteur, alliant force et compassion", trait: "ɔbarima, courageous, with some arrogance; once tempered, nurturing, balancing strength and compassion" },
  { okra: "Wuku", m: ["Kwaku"], f: ["Akua"], pm: ["Ntoni", "Odaakuo", "Atobi"], pf: ["Dompo", "Ɛkuseɛ", "Obisi"],
    trait_fr: "un défenseur des causes d'autrui, donc un héros, tenace, et parfois sombre", trait: "a champion of other people's causes and so a hero, tenacious, and at times dark-hearted" },
  { okra: "Yaw, Awuo", m: ["Yaw", "Kwaw"], f: ["Yaa", "Aba"], pm: ["Preko", "Barima", "Kwaw"], pf: ["Prekowaa", "Bosuo"],
    trait_fr: "brave et affirmé, d'un tempérament guerrier, réservé et prompt à juger, se sentant souvent peu remercié", trait: "brave and assertive in a warlike way, guarded and judgmental, and often feeling unthanked" },
  { okra: "Afi", m: ["Kofi", "Kwafi"], f: ["Afia", "Afua"], pm: ["Kyin", "Otuo", "Okyini", "Fiifi"], pf: ["Kyimmaa", "Nkɔso", "Beefi"],
    trait_fr: "un aventurier né pour errer, lent à se fixer, mais très motivé et compétent", trait: "an adventurer born to wander, slow to settle, but highly motivated and competent" },
  { okra: "Amen", m: ["Kwame"], f: ["Amma", "Amba"], pm: ["Atoapem", "Atoapoma"], pf: ["Atoapemaa", "Nyamekyɛ"],
    trait_fr: "talentueux et sage, né le jour de la création", trait: "talented and wise, the one born on the day of creation" },
  { okra: "Ayisi, Awusi, Asi", m: ["Kwasi"], f: ["Akosua", "Esi"], pm: ["Bodua", "Obue-akwan"], pf: ["Adampo", "Awusi", "Dapaa"],
    trait_fr: "un meneur vers qui l'on se tourne, obue-akwan, celui qui ouvre la voie ; curieux et vite captivé par ce qui l'intéresse", trait: "a leader people look to for guidance, obue-akwan, the one who clears the way; curious and easily drawn into whatever interests them" },
];

(() => {
  const $ = id => document.getElementById(id);
  const esc = s => String(s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);
  const tw = s => s.toLowerCase().replace(/-/g, "");
  const FR = window.NA_LANG === "fr";
  const CAT = FR ? { dapaa: "un dapaa, un jour faste", "dabɔne": "un dabɔne, un jour sacré et restreint", dahunu: "un dahunu, un jour ordinaire" }
    : { dapaa: "a dapaa, a good day", "dabɔne": "a dabɔne, a sacred and restricted day", dahunu: "a dahunu, an ordinary day" };
  const FRD = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"];
  const FRM = ["janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc."];
  const chip = (n, main) => `<span class="chip${main ? " first" : ""}"><span class="kr-i" data-tw="${esc(tw(n))}"></span><b>${esc(n)}</b></span>`;
  const list = a => a.length < 2 ? a.join("") : a.slice(0, -1).join(", ") + (FR ? " et " : " and ") + a[a.length - 1];

  function show() {
    const v = $("bd").value; if (!v) return;
    const [y, m, d] = v.split("-").map(Number);
    const n = AK.dn(y, m, d);
    const wd = AK.weekday(n), D = AK.DAYS[wd], K = KRADIN[wd], L = AK.locate(n), N = AK.NNANSON[L.day - 1], s = AK.SACRED[L.day];
    const cname = L.c.tw[0].toUpperCase() + L.c.tw.slice(1);
    const cats = N.cat ? N.cat.split("/").map(c => CAT[c]).join(FR ? ", ou " : ", or ") : "";
    // names a child born that day could carry: the kradin, its praise names, and names drawn from the day itself
    const fromDay = [N.name];
    if (s) fromDay.push(s === "Akwasidae" || s === "Awukudae" ? "Adae" : s);
    if (N.cat.startsWith("dapaa")) fromDay.push("Dapaa");
    const uniq = [...new Set(fromDay)];
    const dt = AK.fromDn(n), dfr = `${dt.getUTCDate()} ${FRM[dt.getUTCMonth()]} ${dt.getUTCFullYear()}`;
    const afe = `${L.Y.y}–${String(L.Y.y + 1).slice(2)}`;
    $("res").innerHTML = FR ? `
      <p class="eyebrow">${D[1]} · ${FRD[wd]} · ${dfr}</p>
      <div class="pair">
        <div><h3>Masculin</h3><div class="chips">${K.m.map((x, i) => chip(x, i === 0)).join("")}</div></div>
        <div><h3>Féminin</h3><div class="chips">${K.f.map((x, i) => chip(x, i === 0)).join("")}</div></div>
      </div>
      <p class="para">Un enfant né un ${D[1]} porte l'ɔkra de <b>${esc(K.okra)}</b>. On dit des personnes nées un ${FRD[wd]} qu'elles sont ${esc(K.trait_fr)}.</p>
      <p class="para">Noms possibles : <b>Nana ${esc(K.m[0])} ${esc(K.pm[0])}</b>, avec les noms de louange ${list(K.pm.map(esc))} ; <b>Nana ${esc(K.f[0])} ${esc(K.pf[0])}</b>, avec ${list(K.pf.map(esc))}. Tirés du jour lui-même : ${list(uniq.map(x => `<b>${esc(x)}</b>`))}.</p>
      <p class="para">Dans le cycle de 42 jours, c'était <b>${esc(N.name)}</b>, jour ${L.day} de ${esc(cname)}, afe ${afe}${s ? `, jour sacré de <b>${s}</b>` : ""}.${cats ? ` C'est ${cats}.` : ""}</p>
      <div class="kname"><span class="kr-i" data-tw="${esc(tw(N.name))}"></span><span class="kr-i" data-tw="${L.c.tw}"></span></div>
      <p class="src">Ɔkra, noms et noms de louange d'après Kwasi Konadu, « The Calendrical Factor in Akan History », 2012, tableau 2.</p>` : `
      <p class="eyebrow">${D[1]} · ${D[2]} · ${AK.fmt(n)}</p>
      <div class="pair">
        <div><h3>Male</h3><div class="chips">${K.m.map((x, i) => chip(x, i === 0)).join("")}</div></div>
        <div><h3>Female</h3><div class="chips">${K.f.map((x, i) => chip(x, i === 0)).join("")}</div></div>
      </div>
      <p class="para">A child born on ${D[1]} carries the ɔkra of <b>${esc(K.okra)}</b>. ${D[2]}-born people are said to be ${esc(K.trait)}.</p>
      <p class="para">Possible names: <b>Nana ${esc(K.m[0])} ${esc(K.pm[0])}</b>, with the praise names ${list(K.pm.map(esc))}; <b>Nana ${esc(K.f[0])} ${esc(K.pf[0])}</b>, with ${list(K.pf.map(esc))}. From the day itself: ${list(uniq.map(x => `<b>${esc(x)}</b>`))}.</p>
      <p class="para">In the 42-day count it was <b>${esc(N.name)}</b>, day ${L.day} of ${esc(cname)}, afe ${afe}${s ? `, the sacred day of <b>${s}</b>` : ""}.${cats ? ` It is ${cats}.` : ""}</p>
      <div class="kname"><span class="kr-i" data-tw="${esc(tw(N.name))}"></span><span class="kr-i" data-tw="${L.c.tw}"></span></div>
      <p class="src">Ɔkra, names and praise names after Kwasi Konadu, “The Calendrical Factor in Akan History”, 2012, Table 2.</p>`;
    KF.paint($("res"));
    try { history.replaceState(null, "", "#" + v); } catch (e) {}
  }
  $("bd").addEventListener("change", show);
  const h = location.hash.slice(1);
  const iso = d => d.getFullYear() + "-" + String(d.getMonth() + 1).padStart(2, "0") + "-" + String(d.getDate()).padStart(2, "0");
  $("bd").value = /^\d{4}-\d\d-\d\d$/.test(h) ? h : iso(new Date());

  // tabs
  const tabs = [...document.querySelectorAll("[role=tab]")];
  function go(id) {
    tabs.forEach(t => { const on = t.dataset.p === id; t.setAttribute("aria-selected", on); $(t.dataset.p).hidden = !on; });
    try { localStorage.setItem("kd-tab", id); } catch (e) {}
  }
  tabs.forEach(t => t.onclick = () => go(t.dataset.p));
  let start = "p-kradin"; try { start = localStorage.getItem("kd-tab") || start; } catch (e) {}
  if (location.hash === "#calendar") start = "p-cal";
  go(start);

  // nav menu on phones


  KF.use("dua").then(() => { show(); KF.paint(); });
})();
