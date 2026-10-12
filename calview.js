/* Calendar view, shared by calendar.html and kradin.html. Needs calendar.js (AK) and kfont.js (KF). */
(() => {
  const $ = id => document.getElementById(id);
  if (!$("cycles")) return;
  const esc = s => String(s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);
  const T = AK.today();
  let Y = AK.yearOf(T);
  const ord = i => ["1st", "2nd", "3rd"][i] || (i + 1) + "th";
  const yl = y => `${y}–${String(y + 1).slice(2)}`;
  const FR = window.NA_LANG === "fr", FRD = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"];
  const wdn = i => FR ? FRD[i] : AK.DAYS[i][2];
  if (FR) { /* ordinals */ }
  const kr = (tw, cls = "") => `<span class="kr-i ${cls}" data-tw="${esc(tw)}"></span>`;

  function legend() {
    if (!$("legend")) return;
    $("legend").innerHTML = [1, 10, 19, 28].map(d => `<span class="lg"><i>${d}</i>${kr(AK.SACRED[d].toLowerCase())}<span class="sub">${AK.SACRED[d]}</span></span>`).join("");
  }

  function todayCard() {
    if (!$("today")) return;
    const L = AK.locate(T), d = AK.DAYS[L.wd], N = AK.NNANSON[L.day - 1];
    const up = [];
    for (let n = T; up.length < 4; n++) { const x = AK.locate(n); if (AK.SACRED[x.day]) up.push([n, x]); }
    $("today").innerHTML = `
      <div class="tl">
        <p class="eyebrow">${FR ? "Aujourd'hui" : "Today"} · ${AK.fmt(T)}</p>
        <div class="big"><span data-tw="${L.c.tw}"></span></div>
        <p class="lat under">${L.c.up}</p>
        <p class="meta">${FR ? "Jour" : "Day"} <b>${L.day}</b> ${FR ? "sur" : "of"} 42 · <b>${N.name}</b> · ${d[1]} (${wdn(L.wd)})${AK.SACRED[L.day] ? ` · <b>${AK.SACRED[L.day]}</b>` : ""}</p>
        <p class="meta">Afe ${yl(L.Y.y)} · ${FR ? (L.c.i ? L.c.i + 1 + "e" : "1er") + " des " + L.Y.count + " adaduanan" : ord(L.c.i) + " of " + L.Y.count + " adaduanan"}</p>
      </div>
      <div class="next">${up.map(([n, x]) => `<div class="nk">${kr(AK.SACRED[x.day].toLowerCase())}</div><div class="nt"><b>${AK.SACRED[x.day]}</b><small>${AK.DAYS[x.wd][1]} ${AK.fmt(n)}</small></div><div class="nw">${FR ? (n === T ? "aujourd'hui" : n - T === 1 ? "demain" : "dans " + (n - T) + " jours") : (n === T ? "today" : n - T === 1 ? "tomorrow" : "in " + (n - T) + " days")}</div>`).join("")}</div>`;
  }

  function cells(c) {
    let h = AK.DAYS.map(d => `<div class="dh" data-lat="${d[1]} · ${d[2]}" tabindex="0">${d[0]}</div>`).join("");
    for (let k = 0; k < 42; k++) {
      const n = c.start + k, day = k + 1, s = AK.SACRED[day], ks = AK.KESE.get(n), N = AK.NNANSON[k];
      const cat = N.cat.split("/")[0];
      const cls = ["d", s ? "s" : "", n === T ? "now" : "", ks ? "kese" : "", cat ? "c-" + cat : ""].join(" ").replace(/ +/g, " ").trim();
      const tip = [N.name + (N.cat ? " · " + N.cat : ""), s, ks ? "Akwasidae Kɛseɛ" : "", AK.DAYS[k % 7][1] + " " + AK.fmt(n)].filter(Boolean).join(" · ");
      h += `<div class="${cls}" data-lat="${esc(tip)}" tabindex="0"><b>${day}</b><small>${AK.fmt(n, { noY: true })}</small></div>`;
    }
    return h;
  }
  const photo = c => c.img === "pattern" ? `<img src="cal/adommere-pattern.svg" alt="">` : `<img src="cal/${c.img}.webp" alt="" loading="lazy">`;

  function cycleCard(c) {
    return `<article class="cyc" id="c${c.i}">
      <header class="ch"><div class="kt" data-tw="${c.tw}"></div><div class="lt">${c.up}</div></header>
      <figure class="ph">${photo(c)}</figure>
      <div class="cal">
        <p class="rg">${AK.fmtUS(c.start)} – ${AK.fmtUS(c.end)}</p>
        <div class="grid">${cells(c)}</div>
      </div>
    </article>`;
  }

  function yearView() {
    const yr = AK.year(Y);
    $("ylabel").textContent = yl(Y);
    $("ymeta").textContent = `${AK.fmtUS(yr.start)} – ${AK.fmtUS(yr.end)} · ${yr.count} adaduanan · ${yr.count * 42} ${FR ? "jours" : "days"}`;
    $("cycles").innerHTML = yr.cycles.map(cycleCard).join("");
    if ($("sacred")) $("sacred").innerHTML = `<thead><tr><th>Adaduanan</th>${[1, 10, 19, 28].map(d => `<th>${kr(AK.SACRED[d].toLowerCase())}<span>${AK.SACRED[d]}</span></th>`).join("")}</tr></thead><tbody>` +
      yr.cycles.map(c => `<tr><td><a href="#c${c.i}">${kr(c.tw)}<span>${c.up}</span></a></td>${[1, 10, 19, 28].map(d => { const n = c.start + d - 1; return `<td class="${n === T ? "now" : ""}${AK.KESE.has(n) ? " kese" : ""}">${AK.fmt(n)}${AK.KESE.has(n) ? " ✦" : ""}</td>`; }).join("")}</tr>`).join("") + "</tbody>";
    KF.paint($("cycles")); if ($("sacred")) KF.paint($("sacred"));
  }

  function anchors() {
    if (!$("anchors")) return;
    $("anchors").innerHTML = `<tr><th>Date</th><th>Event</th><th>Day of the adaduanan</th><th>Source</th></tr>` + AK.ANCHORS.map(a => {
      const L = AK.locate(a.n);
      return `<tr><td>${AK.DAYS[AK.weekday(a.n)][1]} ${AK.fmt(a.n)}</td><td>${a.what}<small>${esc(a.note)}</small></td><td>${L.day} ${AK.NNANSON[L.day - 1].name} ✓ · ${L.c.up} ${yl(L.Y.y)}</td><td>${a.src ? `<a href="${a.src}" target="_blank" rel="noopener">${new URL(a.src).hostname.replace("www.", "")}</a>` : "your graphics"}</td></tr>`;
    }).join("");
  }

  // ---- export the afe
  const pad = x => String(x).padStart(2, "0");
  const ymd = n => { const d = AK.fromDn(n); return d.getUTCFullYear() + pad(d.getUTCMonth() + 1) + pad(d.getUTCDate()); };
  function save(b, name) { const a = document.createElement("a"); a.href = URL.createObjectURL(b); a.download = name; document.body.append(a); a.click(); setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 800); }
  function ics() {
    const yr = AK.year(Y), L = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Merankron//Akan adaduanan calendar//EN", "CALSCALE:GREGORIAN", `X-WR-CALNAME:Afe ${yl(Y)}`];
    yr.cycles.forEach(c => {
      const nm = c.tw[0].toUpperCase() + c.tw.slice(1);
      for (let k = 0; k < 42; k++) {
        const n = c.start + k, N = AK.NNANSON[k], s = AK.SACRED[k + 1];
        L.push("BEGIN:VEVENT", `UID:${ymd(n)}@adaduanan.merankron`, `DTSTAMP:${ymd(T)}T000000Z`, `DTSTART;VALUE=DATE:${ymd(n)}`, `DTEND;VALUE=DATE:${ymd(n + 1)}`,
          `SUMMARY:${s ? s + " · " : ""}${N.name}`, `DESCRIPTION:${nm}\\, day ${k + 1} of 42${N.cat ? " · " + N.cat : ""}`, "TRANSP:TRANSPARENT", "END:VEVENT");
      }
    });
    L.push("END:VCALENDAR");
    save(new Blob([L.join("\r\n")], { type: "text/calendar" }), `afe-${Y}-${String(Y + 1).slice(2)}.ics`);
  }
  async function pdf(btn) {
    const name = `afe-${Y}-${String(Y + 1).slice(2)}.pdf`, base = $("cycles").dataset.base || "";
    btn.disabled = true; const t = btn.textContent; btn.textContent = FR ? "Préparation…" : "Preparing…";
    try {
      const r = await fetch(base + "dl/afe/" + (FR ? "fr/" : "") + name);
      if (r.ok && (r.headers.get("content-type") || "").includes("pdf")) { save(await r.blob(), name); return; }
    } catch (e) {}
    finally { btn.disabled = false; btn.textContent = t; }
    open(base + "afe.html?y=" + Y + "&print=1" + (FR ? "&lang=fr" : ""), "_blank");
  }
  if ($("exp-ics")) $("exp-ics").onclick = ics;
  if ($("exp-pdf")) $("exp-pdf").onclick = e => pdf(e.currentTarget);

  function fontSelect() { const s = $("font"); if (!s) return; s.innerHTML = KF.sources().map(f => `<option value="${f.id}">${esc(f.name)}</option>`).join(""); s.value = KF.src; }
  async function setFont(id) { document.body.classList.add("loading"); await KF.use(id); fontSelect(); KF.paint(); document.body.classList.remove("loading"); }

  $("prev").onclick = () => { Y--; yearView(); };
  $("next").onclick = () => { Y++; yearView(); };
  $("now").onclick = () => { Y = AK.yearOf(T); yearView(); const c = AK.locate(T).c; setTimeout(() => $("c" + c.i).scrollIntoView({ behavior: "smooth", block: "start" }), 30); };
  if ($("font")) $("font").onchange = e => setFont(e.target.value);
  if ($("latin")) {
    $("latin").onchange = e => { document.body.classList.toggle("nolat", !e.target.checked); try { localStorage.setItem("cal-lat", e.target.checked ? "1" : "0"); } catch (x) {} };
    try { if (localStorage.getItem("cal-lat") === "0") { $("latin").checked = false; document.body.classList.add("nolat"); } } catch (x) {}
  }

  legend(); todayCard(); yearView(); anchors();
  const ready = window.KR ? KR.load().catch(() => {}) : Promise.resolve();
  ready.then(() => setFont(KF.src));
})();
