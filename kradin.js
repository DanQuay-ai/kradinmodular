/* What's your Kradin? Date finder. Needs calendar.js (AK) and kfont.js (KF).
   Ɔkra, names and praise names (mmrane) exactly as in Konadu 2012, Table 2; character after his text. */
const KRADIN = [
  { okra: "Adwo", m: ["Kwadwo"], f: ["Adwoa"], pm: ["Okoto", "Asere"], pf: ["Akoto", "Badwo", "Adae"],
    trait: "calm, a peacemaker, protector and supplicant, so sure of themselves that they are slow to take outside advice" },
  { okra: "Bena", m: ["Kwabena"], f: ["Abena", "Abenaa"], pm: ["Ogyam", "Ɛbo"], pf: ["Kosia", "Atobiaa", "Gyamaa"],
    trait: "ɔbarima, courageous, with some arrogance; once tempered, nurturing, balancing strength and compassion" },
  { okra: "Wuku", m: ["Kwaku"], f: ["Akua"], pm: ["Ntoni", "Odaakuo", "Atobi"], pf: ["Dompo", "Ɛkuseɛ", "Obisi"],
    trait: "a champion of other people's causes and so a hero, tenacious, and at times dark-hearted" },
  { okra: "Yaw, Awuo", m: ["Yaw", "Kwaw"], f: ["Yaa", "Aba"], pm: ["Preko", "Barima", "Kwaw"], pf: ["Prekowaa", "Bosuo"],
    trait: "brave and assertive in a warlike way, guarded and judgmental, and often feeling unthanked" },
  { okra: "Afi", m: ["Kofi", "Kwafi"], f: ["Afia", "Afua"], pm: ["Kyin", "Otuo", "Okyini", "Fiifi"], pf: ["Kyimmaa", "Nkɔso", "Beefi"],
    trait: "an adventurer born to wander, slow to settle, but highly motivated and competent" },
  { okra: "Amen", m: ["Kwame"], f: ["Amma", "Amba"], pm: ["Atoapem", "Atoapoma"], pf: ["Atoapemaa", "Nyamekyɛ"],
    trait: "talented and wise, the one born on the day of creation" },
  { okra: "Ayisi, Awusi, Asi", m: ["Kwasi"], f: ["Akosua", "Esi"], pm: ["Bodua", "Obue-akwan"], pf: ["Adampo", "Awusi", "Dapaa"],
    trait: "a leader people look to for guidance, obue-akwan, the one who clears the way; curious and easily drawn into whatever interests them" },
];

(() => {
  const $ = id => document.getElementById(id);
  const esc = s => String(s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);
  const tw = s => s.toLowerCase().replace(/-/g, "");
  const CAT = { dapaa: "a dapaa, a good day", "dabɔne": "a dabɔne, a sacred and restricted day", dahunu: "a dahunu, an ordinary day" };
  const chip = (n, main) => `<span class="chip${main ? " first" : ""}"><span class="kr-i" data-tw="${esc(tw(n))}"></span><b>${esc(n)}</b></span>`;
  const list = a => a.length < 2 ? a.join("") : a.slice(0, -1).join(", ") + " and " + a[a.length - 1];

  function show() {
    const v = $("bd").value; if (!v) return;
    const [y, m, d] = v.split("-").map(Number);
    const n = AK.dn(y, m, d);
    const wd = AK.weekday(n), D = AK.DAYS[wd], K = KRADIN[wd], L = AK.locate(n), N = AK.NNANSON[L.day - 1], s = AK.SACRED[L.day];
    const cname = L.c.tw[0].toUpperCase() + L.c.tw.slice(1);
    const cats = N.cat ? N.cat.split("/").map(c => CAT[c]).join(", or ") : "";
    // names a child born that day could carry: the kradin, its praise names, and names drawn from the day itself
    const fromDay = [N.name];
    if (s) fromDay.push(s === "Akwasidae" || s === "Awukudae" ? "Adae" : s);
    if (N.cat.startsWith("dapaa")) fromDay.push("Dapaa");
    const uniq = [...new Set(fromDay)];
    $("res").innerHTML = `
      <p class="eyebrow">${D[1]} · ${D[2]} · ${AK.fmt(n)}</p>
      <div class="pair">
        <div><h3>Male</h3><div class="chips">${K.m.map((x, i) => chip(x, i === 0)).join("")}</div></div>
        <div><h3>Female</h3><div class="chips">${K.f.map((x, i) => chip(x, i === 0)).join("")}</div></div>
      </div>
      <p class="para">A child born on ${D[1]} carries the ɔkra of <b>${esc(K.okra)}</b>. ${D[2]}-born people are said to be ${esc(K.trait)}.</p>
      <p class="para">Possible names: <b>Nana ${esc(K.m[0])} ${esc(K.pm[0])}</b>, with the praise names ${list(K.pm.map(esc))}; <b>Nana ${esc(K.f[0])} ${esc(K.pf[0])}</b>, with ${list(K.pf.map(esc))}. From the day itself: ${list(uniq.map(x => `<b>${esc(x)}</b>`))}.</p>
      <p class="para">In the 42-day count it was <b>${esc(N.name)}</b>, day ${L.day} of ${esc(cname)}, afe ${L.Y.y}–${String(L.Y.y + 1).slice(2)}${s ? `, the sacred day of <b>${s}</b>` : ""}.${cats ? ` It is ${cats}.` : ""}</p>
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
  const mb = $("menu-btn"); if (mb) mb.onclick = () => document.body.classList.toggle("menu-open");

  KF.use("dua").then(() => { show(); KF.paint(); });
})();
