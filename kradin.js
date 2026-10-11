/* What's your Kradin? Date finder for neoakan.com. Needs calendar.js (AK) and kfont.js (KF).
   Names, ɔkra and praise names after Konadu 2012, Table 2; spelling variants are common Twi and Fante forms. */
const KRADIN = [
  { okra: "Adwo", m: ["Kwadwo", "Kojo", "Jojo", "Kwodwo"], f: ["Adwoa", "Adjoa", "Ajoa"], pm: ["Okoto", "Asere"], pf: ["Akoto", "Badwo", "Adae"],
    trait: "calm and unassuming, a peacemaker who protects and pleads for others, sure enough of themselves to resist outside advice" },
  { okra: "Bena", m: ["Kwabena", "Kobina", "Ebo", "Kabenla"], f: ["Abena", "Abenaa", "Araba"], pm: ["Ogyam", "Ɛbo"], pf: ["Kosia", "Atobiaa", "Gyamaa"],
    trait: "bold, ɔbarima; strength that becomes nurturing once tempered, holding force and compassion together" },
  { okra: "Wuku", m: ["Kwaku", "Kweku", "Kuuku"], f: ["Akua", "Ekua"], pm: ["Ntoni", "Odaakuo", "Atobi"], pf: ["Dompo", "Ɛkuseɛ", "Obisi"],
    trait: "a champion of other people's causes, tenacious, with a darker edge to watch" },
  { okra: "Yaw", m: ["Yaw", "Kwaw", "Ekow", "Yao"], f: ["Yaa", "Aba"], pm: ["Preko", "Barima", "Kwaw"], pf: ["Prekowaa", "Bosuo"],
    trait: "courageous and assertive, guarded, quick to judge, often feeling unthanked" },
  { okra: "Afi", m: ["Kofi", "Kwafi", "Fiifi"], f: ["Afia", "Afua", "Efua"], pm: ["Kyin", "Otuo", "Okyini", "Fiifi"], pf: ["Kyimmaa", "Nkɔso", "Beefi"],
    trait: "a wanderer and adventurer, slow to settle but driven and capable" },
  { okra: "Amen", m: ["Kwame", "Kwamena", "Ato"], f: ["Amma", "Ama", "Amba"], pm: ["Atoapem", "Atoapoma"], pf: ["Atoapemaa", "Nyamekyɛ"],
    trait: "gifted, wise, a problem-solver, with a flair for drama and a healthy appetite" },
  { okra: "Ayisi, Awusi", m: ["Kwasi", "Akwasi", "Kwesi", "Akwesi"], f: ["Akosua", "Esi", "Akos"], pm: ["Bodua", "Obue-akwan"], pf: ["Adampo", "Awusi", "Dapaa"],
    trait: "a leader, obue-akwan, the one who clears the way; curious, and easily drawn into whatever catches their interest" },
];

(() => {
  const $ = id => document.getElementById(id);
  const esc = s => String(s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);
  const tw = s => s.toLowerCase().replace(/-/g, "");
  const CAT = { dapaa: "dapaa, a good day", "dabɔne": "dabɔne, a sacred and restricted day", dahunu: "dahunu, an ordinary day" };
  const chips = (L, big) => L.map((n, i) => `<span class="chip${big && i === 0 ? " main" : ""}"><span data-tw="${tw(n)}"></span><b>${esc(n)}</b></span>`).join("");

  function show() {
    const v = $("bd").value; if (!v) return;
    const [y, m, d] = v.split("-").map(Number);
    let n = AK.dn(y, m, d);
    const dawn = $("dawn").checked; if (dawn) n -= 1;
    const wd = AK.weekday(n), D = AK.DAYS[wd], K = KRADIN[wd], L = AK.locate(n), N = AK.NNANSON[L.day - 1], s = AK.SACRED[L.day];
    const cname = L.c.tw[0].toUpperCase() + L.c.tw.slice(1);
    const cats = N.cat ? N.cat.split("/").map(c => CAT[c]).join(", or ") : "";
    $("res").innerHTML = `
      <p class="eyebrow">${dawn ? "Born before dawn, so counted as the day before: " : ""}${D[1]} · ${D[2]} · ${AK.fmt(n)}</p>
      <div class="pair">
        <div><h3>Male</h3><div class="chips">${chips(K.m, true)}</div><p class="pr">Praise names: ${K.pm.map(esc).join(", ")}</p></div>
        <div><h3>Female</h3><div class="chips">${chips(K.f, true)}</div><p class="pr">Praise names: ${K.pf.map(esc).join(", ")}</p></div>
      </div>
      <p class="para">A child born on ${D[1]} serves the ɔkra <b>${esc(K.okra)}</b>, the soul of the day. ${D[2]}-born people are said to be ${esc(K.trait)}.
      In full, a ${D[2]}-born man can be <b>Nana ${esc(K.m[0])}</b>, ${esc(K.pm[0])}; a woman <b>Nana ${esc(K.f[0])}</b>, ${esc(K.pf[0])}.</p>
      <p class="para">In the 42-day count, that day was <b data-lat="${esc(N.name)}">${esc(N.name)}</b>, day ${L.day} of ${esc(cname)} in the year ${L.Y.y}–${String(L.Y.y + 1).slice(2)}${s ? `, the sacred day of <b>${s}</b>` : ""}.
      ${cats ? `It is ${cats}.` : ""} Its name joins <i>${esc(N.p)}</i> (${AK.PRE[N.p]}) and <i>${esc(N.st)}</i> (${AK.STEM[N.st]}).</p>
      <p class="kname"><span data-tw="${tw(N.name)}"></span><span data-tw="${L.c.tw}"></span></p>
      <p class="src">Names, ɔkra and praise names after Kwasi Konadu, “The Calendrical Factor in Akan History”, 2012. Spellings vary between Twi and Fante.</p>`;
    KF.paint($("res"));
    try { history.replaceState(null, "", "#" + v); } catch (e) {}
  }
  $("bd").addEventListener("change", show);
  $("dawn").addEventListener("change", show);
  const h = location.hash.slice(1);
  $("bd").value = /^\d{4}-\d\d-\d\d$/.test(h) ? h : (() => { const d = new Date(); return d.getFullYear() + "-" + String(d.getMonth() + 1).padStart(2, "0") + "-" + String(d.getDate()).padStart(2, "0"); })();

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

  KF.use("dua").then(() => { show(); KF.paint(); });
})();
