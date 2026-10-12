/* Kɔradin tab: syllable table, day names, surnames and colours, with tap-to-highlight. Needs twi.js and kfont.js. */
(() => {
  const $ = id => document.getElementById(id);
  if (!$("sy")) return;
  const V = ["a", "e", "ɛ", "i", "o", "ɔ", "u"];
  // families: base first, then its variants (the signs present in Koradin Dua)
  // families as built in the construction lab (glyphs.json): each variant is its base plus a modifier
  const FAM = [["p", "b", "kp", "gb"], ["t", "ky", "tw"], ["d", "dw", "gy", "j"], ["s", "hy", "z"], ["f", "hw", "v"], ["r", "l"], ["k", "g"],
    ["n", "m", "ny", "my"], ["h"], ["w"], ["y"]];
  const ONS = FAM.flat().sort((a, b) => b.length - a.length);
  const HAS = new Set("ba be bi bo bu bɛ bɔ dwa dwe dwi dwo dwu dwɔ dwɛ da de di du do dɔ dɛ fa fe fu fo fɔ fɛ fi gba gbe gbi gbu gbo gya gye gyi gyu gyo gbɔ gyɔ gyɛ gbɛ ga ge gi go gu gɔ gɛ hwa hwe hwi hwu hwo hya hye hyi hyu hyo hwɔ hyɔ hyɛ hwɛ ha he hu hi ho hɔ hɛ ja je ji jo ju jɔ jɛ kpa kpe kpi kpu kpo kwa kwe kya kye kyi kyu kyo kpɔ kyɔ kpɛ kyɛ ka ke ki ko ku kɔ kɛ la le li lu lo lɔ lɛ mya mye myu myo myi myɔ myɛ ma me mi mo mu mɔ mɛ nya nye nyi nyo nyu nyɔ nyɛ na ne ni nu no nɛ nɔ pa pe pi pu po pɔ pɛ ra re ri ro ru rɔ rɛ sa se si su so sɔ sɛ twa twe twi twu two twɔ twɛ ta te ti to tu tɔ tɛ va ve vi vo vu vɔ vɛ wa we wi wu wo wɔ wɛ ya ye yi yo yu yɔ yɛ za ze zi zu zo zɔ zɛ".split(" "));

  let t = `<thead><tr><th></th>${V.map(v => `<th>${v}</th>`).join("")}</tr></thead><tbody>`;
  FAM.forEach(f => f.forEach((o, i) => {
    t += `<tr class="${i ? "var" : "base"}"><th>${o}</th>${V.map(v => { const s = o + v; return HAS.has(s) ? `<td data-s="${s}"><span class="kr-i" data-tw="${s}"></span><small>${s}</small></td>` : "<td></td>"; }).join("")}</tr>`;
  }));
  t += `<tr class="base"><th>—</th>${V.map(v => `<td data-s="${v}"><span class="kr-i" data-tw="${v}"></span><small>${v}</small></td>`).join("")}</tr></tbody>`;
  $("sy").innerHTML = t.replace("<th>—</th>", "<th>∅</th>");

  // split a Latin name into the syllables of the table (nasals are marks, not cells)
  function syllables(name) {
    let w = TwiScript.toKradin(name).toLowerCase().replace(/[^a-zɛɔŋ]/g, ""), out = [];
    while (w) {
      const nas = w.match(/^(ng|ŋ|m|n)(?![aeiouɛɔ])/) || w.match(/^(ng|ŋ)/);
      if (nas && !(w[0] === "n" && /^n[aeiouɛɔy]/.test(w)) && !(w[0] === "m" && /^m[aeiouɛɔy]/.test(w))) { w = w.slice(nas[0].length); continue; }
      const o = ONS.find(x => w.startsWith(x) && V.includes(w[x.length])) || "";
      const v = w[o.length];
      if (V.includes(v)) { out.push(o + v); w = w.slice(o.length + 1); } else w = w.slice(1);
    }
    return out;
  }
  let pressed = null;
  function light(btn, name) {
    document.querySelectorAll("table.sy td.on").forEach(td => td.classList.remove("on"));
    if (pressed) pressed.setAttribute("aria-pressed", "false");
    if (pressed === btn) { pressed = null; return; }
    pressed = btn; btn.setAttribute("aria-pressed", "true");
    const S = syllables(name);
    S.forEach(s => document.querySelectorAll(`table.sy td[data-s="${s}"]`).forEach(td => td.classList.add("on")));
    const first = document.querySelector("table.sy td.on");
    if (first && innerWidth < 800) first.scrollIntoView({ behavior: "smooth", block: "center" });
  }
  const btn = (n, sub) => `<button aria-pressed="false" data-n="${n}"><span class="kr-i" data-tw="${n.toLowerCase()}"></span><b>${n}</b>${sub ? `<small>${sub}</small>` : ""}</button>`;

  const FRD = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"], FR = window.NA_LANG === "fr";
  const DAYS = KRADIN.map((k, i) => ({ m: k.m, f: k.f, day: FR ? FRD[i] : AK.DAYS[i][2] }));
  $("dn").innerHTML = `<h3>${FR ? "Masculin" : "Male"}</h3>${DAYS.map(d => d.m.map(n => btn(n, d.day)).join("")).join("")}<h3>${FR ? "Féminin" : "Female"}</h3>${DAYS.map(d => d.f.map(n => btn(n, d.day)).join("")).join("")}`;
  // surnames: placeholder set, to be replaced by the list on the current page
  const SUR = ["Mensah", "Dontoh", "Frimpong", "Boateng", "Owusu", "Osei", "Agyeman", "Asamoah", "Ofori", "Appiah", "Amoako", "Danquah", "Konadu", "Asante", "Bonsu", "Opoku"];
  $("sn").innerHTML = SUR.map(n => btn(n)).join("");


  document.querySelectorAll("#dn button,#sn button").forEach(b => b.onclick = () => light(b, b.dataset.n));
  if (window.KF) KF.paint(document.getElementById("p-script"));
})();
