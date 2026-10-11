/* Akan calendar: 42-day adaduanan, 8 or 9 to a year.
   Day numbers are counted in UTC days so daylight saving never shifts a date. */
const AK = (() => {
  const DAY = 864e5;
  const dn = (y, m, d) => Math.floor(Date.UTC(y, m - 1, d) / DAY);
  const fromDn = n => new Date(n * DAY);
  // Anchor: the first day (Fɔdwoo, a Monday) of Adɔmmerɛ 2025, from your calendar graphics
  const S0 = dn(2025, 7, 21);
  // A year opens with the adaduanan whose first day falls nearest 10 August. That gives 9 adaduanan in two
  // years out of three and 8 in the third (one dropped every three years, Danquah via Konadu 2012), and keeps
  // the year's opening within the Odwira season of August to September.
  const TARGET = [8, 10];
  // Names in order, after the nine seasonal periods in Konadu 2012, Table 5.
  // In a year of 8, ɔpɛnimaa (the small dry season, the one without its own page) is skipped.
  const CYCLES = [
    { tw: "adɔmmerɛ", up: "ADƆMMERƐ", m: "second rains; peak harvest, storage in the sanaa, dew and fog. Odwira falls here." },
    { tw: "ɔbɛsaa", up: "ƆBƐSAA", m: "harvest under rain and sunshine, between the rains and the harmattan." },
    { tw: "obubuo", up: "OBUBUO", m: "the last of the harvest; from bu, bubu, to break off: the yam stem withers and breaks." },
    { tw: "ofupɛ", up: "OFUPƐ", m: "between the rains and the dry season; ɔpɛ-bere, when the harmattan blows." },
    { tw: "ɔpɛnimaa", up: "ƆPƐNIMAA", m: "the small dry season (ɔpɛ, dry season; nimaa, small); land is prepared for farming.", optional: true },
    { tw: "ɔpɛpɔn", up: "ƆPƐPƆN", m: "the great dry season of the harmattan (pɔn, great); harsh on plants and skin." },
    { tw: "mpɛnoa", up: "MPƐNOA", m: "end of the harmattan; rain is awaited and the land made ready." },
    { tw: "oforisuo", up: "OFORISUO", m: "yam mounds are made and planted; fre osuo, calling the rain." },
    { tw: "asusuo", up: "ASUSUO", m: "the great rains; then kitawonsa, hold your hands, the lean weeks before harvest." },
  ];
  // Photos from your graphics, in order. In a year of 9 the first card gets the emblem pattern and the photos move on by one.
  const PHOTOS = ["adommere", "obesaa", "obubuo", "ofupe", "opepon", "mpenua", "oforisuo", "asusuo"];
  const DAYS = [["D", "Dwoada", "Monday"], ["B", "Benada", "Tuesday"], ["W", "Wukuada", "Wednesday"], ["Y", "Yawoada", "Thursday"],
    ["F", "Fiada", "Friday"], ["M", "Memeneda", "Saturday"], ["K", "Kwasiada", "Sunday"]];
  const SACRED = { 1: "Fodwoɔ", 10: "Awukudae", 19: "Fofie", 28: "Akwasidae" };
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
    { d: [2025, 8, 17], what: "Akwasidae", note: "day 28 of Adɔmmerɛ in your 2025 graphics", src: "" },
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
    const img = i => k === 9 ? (i === 0 ? "pattern" : PHOTOS[i - 1]) : PHOTOS[i];
    return { y, start: a, end: b - 1, count: k, cycles: names.map((c, i) => ({ ...c, i, img: img(i), start: a + 42 * i, end: a + 42 * i + 41 })) };
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

