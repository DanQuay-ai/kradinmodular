/* Akan calendar: 42-day adaduanan, 8 or 9 to a year.
   Day numbers are counted in UTC days so daylight saving never shifts a date. */
const AK = (() => {
  const DAY = 864e5;
  const dn = (y, m, d) => Math.floor(Date.UTC(y, m - 1, d) / DAY);
  const fromDn = n => new Date(n * DAY);
  // Anchor: the first day (Fɔdwoo, a Monday) of Adommerɛ 2025, from your calendar graphics
  const S0 = dn(2025, 7, 21);
  // A year opens with the adaduanan whose first day falls nearest 10 August. That gives 9 adaduanan in two
  // years out of three and 8 in the third (one dropped every three years, Danquah via Konadu 2012), and keeps
  // the year's opening within the Odwira season of August to September.
  const TARGET = [8, 10];
  // Names in order, after the nine seasonal periods in Konadu 2012, Table 5.
  // In a year of 8, ɔpɛnimaa (the small dry season, the one without its own page) is skipped.
  const CYCLES = [
    { tw: "adommerɛ", up: "ADOMMERƐ", theme: "nsaguo", th: "NSAGUO", img: "adommere" },
    { tw: "ɔbesaa", up: "ƆBESAA", theme: "siwdo", th: "SIWDO", img: "obesaa" },
    { tw: "ɔbubuɔ", up: "ƆBUBUƆ", theme: "adwini", th: "ADWINI", img: "obubuo" },
    { tw: "ofupɛ", up: "OFUPƐ", theme: "posuban", th: "POSUBAN", img: "ofupe" },
    { tw: "ɔpɛnimaa", up: "ƆPƐNIMAA", theme: "", th: "", img: "", optional: true },
    { tw: "ɔpɛpɔn", up: "ƆPƐPƆN", theme: "ɔko", th: "ƆKO", img: "opepon" },
    { tw: "mpɛnoa", up: "MPƐNOA", theme: "ɛfie", th: "ƐFIE", img: "mpenua" },
    { tw: "oforisuo", up: "OFORISUO", theme: "asafo", th: "ASAFO", img: "oforisuo" },
    { tw: "asusuo", up: "ASUSUO", theme: "aduane", th: "ADUANE", img: "asusuo" },
  ];
  const DAYS = [["D", "Dwoada", "Monday"], ["B", "Benada", "Tuesday"], ["W", "Wukuada", "Wednesday"], ["Y", "Yawoada", "Thursday"],
    ["F", "Fiada", "Friday"], ["M", "Memeneda", "Saturday"], ["K", "Kwasiada", "Sunday"]];
  const SACRED = { 1: "Fɔdwoo", 10: "Awukudae", 19: "Fofie", 28: "Akwasidae" };
  // The 42 named days (nnanson), day 1 = Fodwoɔ, the Takyiman/Kwawu start. Prefixes and stems after
  // Konadu 2012, Tables 3 and 4; category = dapaa (good), dabɔne (sacred/restricted), dahunu (ordinary), "" = no data.
  const PRE = { fo: "rest and generosity", nwona: "care and wellness", nkyi: "an open day in passing", kuru: "sacred and complete", kwa: "ordinary and free", mono: "fresh and new" };
  const STEM = { dwoɔ: "peace and calm", bena: "strength with compassion", wukuo: "cleansing and advocacy", yaw: "courage and the earth", fie: "travel and trade", memene: "fullness and creation", kwasi: "purification and freedom" };
  const NNANSON = ["fo dwoɔ dabɔne", "nwona bena", "nkyi wukuo dapaa/dahunu", "kuru yaw dabɔne", "kwa fie dabɔne", "mono memene dapaa", "fo kwasi",
    "nwona dwoɔ dabɔne", "nkyi bena dapaa", "kuru wukuo dabɔne", "kwa yaw dabɔne", "mono fie dabɔne", "fo memene dabɔne", "nwona kwasi dahunu",
    "nkyi dwoɔ dapaa", "kuru bena dabɔne", "kwa wukuo dabɔne", "mono yaw dabɔne", "fo fie dabɔne", "nwona memene dapaa", "nkyi kwasi dapaa",
    "kuru dwoɔ dapaa/dahunu", "kwa bena dapaa", "mono wukuo dabɔne", "fo yaw dabɔne", "nwona fie dabɔne", "nkyi memene dapaa", "kuru kwasi dabɔne",
    "kwa dwoɔ dapaa", "mono bena dahunu/dabɔne", "fo wukuo dabɔne", "nwona yaw dabɔne", "nkyi fie dabɔne", "kuru memene dapaa", "kwa kwasi dabɔne",
    "mono dwoɔ dapaa", "fo bena", "nwona wukuo dabɔne", "nkyi yaw dabɔne", "kuru fie dabɔne", "kwa memene dapaa/dabɔne", "mono kwasi"]
    .map(s => { const [p, st, cat = ""] = s.split(" "); const name = p + st; return { p, st, name: name[0].toUpperCase() + name.slice(1), tw: name, cat, gloss: `${PRE[p]}, ${STEM[st]}` }; });
  // Dates reported online. Every one falls on day 28 of an adaduanan counted from the anchor above.
  const ANCHORS = [
    { d: [1978, 1, 8], what: "Akwasidae", note: "first of 1978 in Wikipedia's worked example", src: "https://en.wikipedia.org/wiki/Akan_calendar" },
    { d: [2004, 5, 9], what: "Akwasidae Kɛseɛ", note: "Kumasi Sports Stadium, 5th anniversary of Otumfuo Osei Tutu II", src: "https://www.ghanaweb.com/GhanaHomePage/NewsArchive/Asanteman-to-celebrate-Akwasidae-Kese-on-May-9-55396", kese: true },
    { d: [2019, 4, 21], what: "Akwasidae Kɛseɛ", note: "Manhyia, Kumasi", src: "https://www.graphic.com.gh/news/general-news/ghana-news-akufo-addo-touts-asantehene-s-peace-building-efforts-at-akwasidae-k-se.html", kese: true },
    { d: [2023, 11, 26], what: "Akwasidae", note: "last of 2023, Manhyia", src: "https://bawumia.com/news/veep-joins-asantehene-and-asanteman-for-final-akwasidae/" },
    { d: [2024, 1, 7], what: "Akwasidae", note: "first of 2024, Manhyia", src: "https://graphiconline.com/news/general-news/asantehene.html" },
    { d: [2025, 1, 19], what: "Akwasidae", note: "first of 2025, Manhyia", src: "https://gna.org.gh/2025/01/hundreds-join-asantehene-to-celebrate-first-akwasidae-of-the-year" },
    { d: [2025, 8, 17], what: "Akwasidae", note: "day 28 of Adommerɛ in your 2025 graphics", src: "" },
    { d: [2025, 12, 21], what: "Akwasidae", note: "9th of 2025, Manhyia", src: "https://www.citinewsroom.com/2025/12/pictures-asantehene-celebrates-9th-akwasidae-in-grand-splendour/" },
    { d: [2026, 8, 30], what: "Akwasidae Kɛseɛ", note: "Asante diaspora durbar, Bowie State University", src: "https://yen.com.gh/entertainment/celebrities/311002-2026-akwasidae-kese-otumfuo-osei-tutu-iis-wife-lady-julia-children-pay-homage-durbar/", kese: true },
    // Konadu 2012 (IJAHS 45:2), 19th-century Asante events dated by their adaduanan day; all fall on the named day
    ...[[[1817, 11, 6], "Nwonayaw", "Asante council plans the Gyaman intervention"], [[1818, 1, 7], "Awukudae", "rites for an Asante campaign"],
      [[1834, 3, 25], "Nkyibena", "messengers bring news of Osei Yaw's death to the coast, held back on this good day"],
      [[1842, 1, 27], "Monoyaw", "H.J. Pel arrives in Kumase"], [[1857, 8, 16], "Akwasidae", "the 'big Adai' seen by the Dutch envoy Graves"],
      [[1874, 7, 23], "Nkyiyaw", "C.C. Lees arrives in Kumase"], [[1883, 4, 26], "Kuruyaw", "Barrow and Kirby arrive in Kumase"],
      [[1891, 4, 2], "Kuruyaw", "H.M. Hull arrives in Kumase"]].map(([d, what, note]) => ({ d, what, note, src: "https://www.jstor.org/stable/23267008", konadu: true })),
  ].sort((a, b) => dn(...a.d) - dn(...b.d)).map(a => ({ ...a, n: dn(...a.d) }));
  const KESE = new Map(ANCHORS.filter(a => a.kese).map(a => [a.n, a]));

  const yearStart = y => { const t = dn(y, ...TARGET); return S0 + 42 * Math.round((t - S0) / 42); };
  function yearOf(n) { let y = fromDn(n).getUTCFullYear(); while (yearStart(y) > n) y--; while (yearStart(y + 1) <= n) y++; return y; }
  function year(y) {
    const a = yearStart(y), b = yearStart(y + 1), k = (b - a) / 42;
    const names = k === 9 ? CYCLES : CYCLES.filter(c => !c.optional);
    return { y, start: a, end: b - 1, count: k, cycles: names.map((c, i) => ({ ...c, i, start: a + 42 * i, end: a + 42 * i + 41 })) };
  }
  function locate(n) {
    const Y = year(yearOf(n)), c = Y.cycles[Math.floor((n - Y.start) / 42)];
    return { Y, c, day: n - c.start + 1, wd: (n - c.start) % 7 };
  }
  const weekday = n => (((n + 3) % 7) + 7) % 7; // 0 = Monday
  const today = () => { const d = new Date(); return dn(d.getFullYear(), d.getMonth() + 1, d.getDate()); };
  const M3 = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  const fmt = (n, o = {}) => { const d = fromDn(n), s = `${o.pad ? String(d.getUTCDate()).padStart(2, "0") : d.getUTCDate()} ${M3[d.getUTCMonth()]}`; return o.noY ? s : s + " " + d.getUTCFullYear(); };
  const fmtUS = n => { const d = fromDn(n); return `${M3[d.getUTCMonth()]} ${d.getUTCDate()}, ${d.getUTCFullYear()}`; };
  return { NNANSON, PRE, STEM, dn, fromDn, S0, CYCLES, DAYS, SACRED, ANCHORS, KESE, yearStart, yearOf, year, locate, weekday, today, fmt, fmtUS };
})();

// ---------------------------------------------------------------- page
(() => {
  const $ = id => document.getElementById(id);
  if (!$("cycles")) return;
  const esc = s => String(s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);
  const T = AK.today();
  let Y = AK.yearOf(T);
  const ord = i => ["1st", "2nd", "3rd"][i] || (i + 1) + "th";

  function todayCard() {
    const L = AK.locate(T), d = AK.DAYS[L.wd];
    const up = [];
    for (let n = T; up.length < 4; n++) { const x = AK.locate(n); if (AK.SACRED[x.day]) up.push([n, x]); }
    $("today").innerHTML = `
      <div class="tl">
        <p class="eyebrow">Today · ${AK.fmt(T)}</p>
        <div class="big"><span data-tw="${L.c.tw}"></span></div>
        <p class="lat under">${L.c.up}</p>
        <p class="meta">Day <b>${L.day}</b> of 42 · <span data-tw="${d[1].toLowerCase()}" class="inl"></span> ${d[1]} (${d[2]})${AK.SACRED[L.day] ? ` · <b class="gold">${AK.SACRED[L.day]}</b>` : ""}</p>
        <p class="meta">Akan year ${L.Y.y}–${String(L.Y.y + 1).slice(2)} · ${ord(L.c.i)} of ${L.Y.count} adaduanan</p>
      </div>
      <ul class="next">${up.map(([n, x]) => `<li><span class="kr-s" data-tw="${AK.SACRED[x.day].toLowerCase()}"></span><span><b>${AK.SACRED[x.day]}</b><small>${AK.DAYS[x.wd][1]} ${AK.fmt(n)}</small></span><em>${n === T ? "today" : n - T === 1 ? "tomorrow" : "in " + (n - T) + " days"}</em></li>`).join("")}</ul>`;
  }

  function cycleCard(c, Yr) {
    const cells = [];
    for (let k = 0; k < 42; k++) {
      const n = c.start + k, day = k + 1, s = AK.SACRED[day], ks = AK.KESE.get(n);
      const cls = ["d", s ? "s" : "", n === T ? "now" : "", ks ? "kese" : ""].join(" ").trim();
      const N = AK.NNANSON[k];
      const tip = [N.name + (N.cat ? " (" + N.cat + ")" : ""), s, ks ? "Akwasidae Kɛseɛ" : "", AK.DAYS[k % 7][1] + " " + AK.fmt(n)].filter(Boolean).join(" · ");
      cells.push(`<div class="${cls} c-${(N.cat.split("/")[0]) || "x"}" data-lat="${esc(tip)}" tabindex="0"><b>${String(day).padStart(2, "0")}</b><small>${AK.fmt(n, { pad: true, noY: true })}</small></div>`);
    }
    const ph = c.img ? `<img src="cal/${c.img}.webp" alt="" loading="lazy">` : `<div class="noimg"><i class="emb"></i></div>`;
    return `<article class="cyc${c.img ? "" : " plain"}" id="c${c.i}">
      <header class="ch">
        <div><div class="kt" data-tw="${c.tw}"></div><div class="lt">${c.up}</div></div>
        ${c.theme ? `<div class="th"><div class="kt sm" data-tw="${c.theme}"></div><div class="lt it">${c.th}</div></div>` : `<div class="th"><div class="lt it">${c.optional ? "small dry season<br>only in years of 9" : ""}</div></div>`}
      </header>
      <figure class="ph">${ph}</figure>
      <div class="cal">
        <h3>${c.up}</h3>
        <p class="rg">${AK.fmtUS(c.start)} – ${AK.fmtUS(c.end)}</p>
        <div class="grid">${AK.DAYS.map(d => `<div class="dh" data-lat="${d[1]} · ${d[2]}" tabindex="0">${d[0]}</div>`).join("")}${cells.join("")}</div>
      </div>
    </article>`;
  }

  function yearView() {
    const yr = AK.year(Y);
    $("ylabel").textContent = `${Y}–${String(Y + 1).slice(2)}`;
    $("ymeta").textContent = `${AK.fmtUS(yr.start)} – ${AK.fmtUS(yr.end)} · ${yr.count} adaduanan · ${yr.count * 42} days`;
    $("cycles").innerHTML = yr.cycles.map(c => cycleCard(c, yr)).join("");
    $("sacred").innerHTML = `<tr><th>Adaduanan</th>${[1, 10, 19, 28].map(d => `<th><span class="kr-s" data-tw="${AK.SACRED[d].toLowerCase()}"></span>${AK.SACRED[d]}</th>`).join("")}</tr>` +
      yr.cycles.map(c => `<tr><td><a href="#c${c.i}"><span class="kr-s" data-tw="${c.tw}"></span>${c.up}</a></td>${[1, 10, 19, 28].map(d => { const n = c.start + d - 1; return `<td class="${n === T ? "now" : ""}${AK.KESE.has(n) ? " kese" : ""}">${AK.fmt(n)}${AK.KESE.has(n) ? " ✦" : ""}</td>`; }).join("")}</tr>`).join("");
    KF.paint($("cycles")); KF.paint($("sacred"));
  }

  function anchors() {
    $("anchors").innerHTML = `<tr><th>Date</th><th>Event</th><th>Day of the adaduanan</th><th>Source</th></tr>` + AK.ANCHORS.map(a => {
      const L = AK.locate(a.n);
      return `<tr><td>${AK.DAYS[AK.weekday(a.n)][1]} ${AK.fmt(a.n)}</td><td>${a.what}<small>${esc(a.note)}</small></td><td>${L.day} ${AK.NNANSON[L.day - 1].name} ✓ · ${L.c.up} ${L.Y.y}–${String(L.Y.y + 1).slice(2)}</td><td>${a.src ? `<a href="${a.src}" target="_blank" rel="noopener">${new URL(a.src).hostname.replace("www.", "")}</a>` : "your graphics"}</td></tr>`;
    }).join("");
  }

  // ---- export the afe
  const pad = x => String(x).padStart(2, "0");
  const ymd = n => { const d = AK.fromDn(n); return d.getUTCFullYear() + pad(d.getUTCMonth() + 1) + pad(d.getUTCDate()); };
  function ics() {
    const yr = AK.year(Y), L = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Kradin Modular//Akan calendar//EN", "CALSCALE:GREGORIAN", `X-WR-CALNAME:Afe ${Y}-${String(Y + 1).slice(2)}`];
    const ev = (n, title, desc) => L.push("BEGIN:VEVENT", `UID:${ymd(n)}-${title.replace(/\W/g, "")}@kradinmodular`, `DTSTAMP:${ymd(AK.today())}T000000Z`,
      `DTSTART;VALUE=DATE:${ymd(n)}`, `DTEND;VALUE=DATE:${ymd(n + 1)}`, `SUMMARY:${title}`, `DESCRIPTION:${desc}`, "TRANSP:TRANSPARENT", "END:VEVENT");
    yr.cycles.forEach(c => {
      const nm = c.tw[0].toUpperCase() + c.tw.slice(1);
      for (let k = 0; k < 42; k++) {
        const N = AK.NNANSON[k], s = AK.SACRED[k + 1];
        ev(c.start + k, (s ? s + " · " : "") + N.name, `${nm}, day ${k + 1} of 42${N.cat ? " · " + N.cat : ""} · ${N.gloss}`);
      }
    });
    L.push("END:VCALENDAR");
    save(new Blob([L.join("\r\n")], { type: "text/calendar" }), `afe-${Y}-${String(Y + 1).slice(2)}.ics`);
  }
  function save(b, name) { const a = document.createElement("a"); a.href = URL.createObjectURL(b); a.download = name; document.body.append(a); a.click(); setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 500); }
  function pdf() { document.body.classList.add("printing"); const t = document.title; document.title = `Afe ${Y}-${String(Y + 1).slice(2)}`; print(); document.title = t; document.body.classList.remove("printing"); }
  if ($("exp-ics")) $("exp-ics").onclick = ics;
  if ($("exp-pdf")) $("exp-pdf").onclick = pdf;

  function fontSelect() {
    const s = $("font"); s.innerHTML = KF.sources().map(f => `<option value="${f.id}">${esc(f.name)}</option>`).join(""); s.value = KF.src;
  }
  async function setFont(id) { document.body.classList.add("loading"); await KF.use(id); fontSelect(); KF.paint(); document.body.classList.remove("loading"); }

  $("prev").onclick = () => { Y--; yearView(); };
  $("next").onclick = () => { Y++; yearView(); };
  $("now").onclick = () => { Y = AK.yearOf(T); yearView(); const c = AK.locate(T).c; setTimeout(() => document.getElementById("c" + c.i).scrollIntoView({ behavior: "smooth", block: "start" }), 30); };
  $("font").onchange = e => setFont(e.target.value);
  $("latin").onchange = e => { document.body.classList.toggle("nolat", !e.target.checked); try { localStorage.setItem("cal-lat", e.target.checked ? "1" : "0"); } catch (x) {} };
  try { if (localStorage.getItem("cal-lat") === "0") { $("latin").checked = false; document.body.classList.add("nolat"); } } catch (x) {}

  todayCard(); yearView(); anchors();
  const ready = window.KR ? KR.load().catch(() => {}) : Promise.resolve();
  ready.then(() => setFont(KF.src));
})();
