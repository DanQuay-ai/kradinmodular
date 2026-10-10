/* Akan calendar: 42-day adaduanan, 8 or 9 to a year.
   Day numbers are counted in UTC days so daylight saving never shifts a date. */
const AK = (() => {
  const DAY = 864e5;
  const dn = (y, m, d) => Math.floor(Date.UTC(y, m - 1, d) / DAY);
  const fromDn = n => new Date(n * DAY);
  // Anchor: the first day (Fɔdwoo, a Monday) of Adommerɛ 2025, from your calendar graphics
  const S0 = dn(2025, 7, 21);
  // A year opens with the adaduanan whose first day falls nearest 28 July. That gives 9 adaduanan in two
  // years out of three and 8 in the third, and puts Adommerɛ's Akwasidae between late July and mid September.
  const TARGET = [7, 28];
  // Names in order. In a year of 8 the last one is skipped. Rename freely: the page reads this list.
  const CYCLES = [
    { tw: "adommerɛ", up: "ADOMMERƐ", theme: "nsaguo", th: "NSAGUO", img: "adommere" },
    { tw: "ɔbesaa", up: "ƆBESAA", theme: "siwdo", th: "SIWDO", img: "obesaa" },
    { tw: "ɔbubuɔ", up: "ƆBUBUƆ", theme: "adwini", th: "ADWINI", img: "obubuo" },
    { tw: "ofupɛ", up: "OFUPƐ", theme: "posuban", th: "POSUBAN", img: "ofupe" },
    { tw: "ɔpɛpɔn", up: "ƆPƐPƆN", theme: "ɔko", th: "ƆKO", img: "opepon" },
    { tw: "mpɛnua", up: "MPƐNUA", theme: "ɛfie", th: "ƐFIE", img: "mpenua" },
    { tw: "oforisuo", up: "OFORISUO", theme: "asafo", th: "ASAFO", img: "oforisuo" },
    { tw: "asusuo", up: "ASUSUO", theme: "aduane", th: "ADUANE", img: "asusuo" },
    { tw: "odwira", up: "ODWIRA", theme: "", th: "", img: "", provisional: true },
  ];
  const DAYS = [["D", "Dwoada", "Monday"], ["B", "Benada", "Tuesday"], ["W", "Wukuada", "Wednesday"], ["Y", "Yawoada", "Thursday"],
    ["F", "Fiada", "Friday"], ["M", "Memeneda", "Saturday"], ["K", "Kwasiada", "Sunday"]];
  const SACRED = { 1: "Fɔdwoo", 10: "Awukudae", 19: "Fofie", 28: "Akwasidae" };
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
  ].map(a => ({ ...a, n: dn(...a.d) }));
  const KESE = new Map(ANCHORS.filter(a => a.kese).map(a => [a.n, a]));

  const yearStart = y => { const t = dn(y, ...TARGET); return S0 + 42 * Math.round((t - S0) / 42); };
  function yearOf(n) { let y = fromDn(n).getUTCFullYear(); while (yearStart(y) > n) y--; while (yearStart(y + 1) <= n) y++; return y; }
  function year(y) {
    const a = yearStart(y), b = yearStart(y + 1), k = (b - a) / 42;
    const names = k === 9 ? CYCLES : CYCLES.slice(0, 8);
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
  return { dn, fromDn, S0, CYCLES, DAYS, SACRED, ANCHORS, KESE, yearStart, yearOf, year, locate, weekday, today, fmt, fmtUS };
})();

// ---------------------------------------------------------------- page
(() => {
  const $ = id => document.getElementById(id);
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
      const tip = [s, ks ? "Akwasidae Kɛseɛ" : "", AK.DAYS[k % 7][1] + " " + AK.fmt(n)].filter(Boolean).join(" · ");
      cells.push(`<div class="${cls}" title="${esc(tip)}"><b>${String(day).padStart(2, "0")}</b><small>${AK.fmt(n, { pad: true, noY: true })}</small></div>`);
    }
    const ph = c.img ? `<img src="cal/${c.img}.webp" alt="" loading="lazy">` : `<div class="noimg"><i class="emb"></i></div>`;
    return `<article class="cyc${c.img ? "" : " plain"}" id="c${c.i}">
      <header class="ch">
        <div><div class="kt" data-tw="${c.tw}"></div><div class="lt">${c.up}</div></div>
        ${c.theme ? `<div class="th"><div class="kt sm" data-tw="${c.theme}"></div><div class="lt it">${c.th}</div></div>` : `<div class="th"><div class="lt it">${c.provisional ? "9th adaduanan<br>name to confirm" : ""}</div></div>`}
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
      return `<tr><td>${AK.DAYS[AK.weekday(a.n)][1]} ${AK.fmt(a.n)}</td><td>${a.what}<small>${esc(a.note)}</small></td><td>${L.day === 28 ? "28 ✓" : L.day} · ${L.c.up} ${L.Y.y}–${String(L.Y.y + 1).slice(2)}</td><td>${a.src ? `<a href="${a.src}" target="_blank" rel="noopener">${new URL(a.src).hostname.replace("www.", "")}</a>` : "your graphics"}</td></tr>`;
    }).join("");
  }

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
