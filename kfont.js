/* Kɔradin text on any page: one font switch for the whole site, and a bubble with the Latin Twi
   over every piece of Kɔradin.
   Markup: <span data-tw="adommerɛ"></span> is filled with Kɔradin in the current font.
           Any element with data-lat="..." shows that Latin in a bubble on hover, focus or tap. */
(function () {
  const LS = { get(k, d) { try { const v = localStorage.getItem(k); return v == null ? d : JSON.parse(v); } catch (e) { return d; } },
    set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} } };
  let src = LS.get("kf-src", "dua"), fam = "KDua", has = null, n = 0;
  const W = 44;
  const css = `@font-face{font-family:"KDua";src:url(fonts/KoradinDua.woff2) format("woff2");font-display:block}
:root{--kr:"KDua"}
.kr{font-family:var(--kr),var(--font);font-feature-settings:"liga","calt";font-weight:400;letter-spacing:0}
[data-lat]{cursor:help}
.kf-tip{position:absolute;z-index:99;pointer-events:none;background:var(--label);color:var(--bg);font:500 13px/1.3 var(--font);
  padding:6px 10px;border-radius:8px;white-space:normal;text-align:center;max-width:min(300px,calc(100vw - 16px));opacity:0;transform:translateY(4px);transition:opacity .12s,transform .12s}
.kf-tip.on{opacity:1;transform:none}
.kf-tip::after{content:"";position:absolute;left:var(--ax,50%);top:100%;margin-left:-6px;border:6px solid transparent;border-top-color:var(--label)}
.kf-tip.below::after{top:auto;bottom:100%;border-top-color:transparent;border-bottom-color:var(--label)}`;
  const st = document.createElement("style"); st.textContent = css; document.head.append(st);

  function sources() {
    const L = [{ id: "dua", name: "Koradin Dua (the original)" }, { id: "km2", name: "Kɔradin Modular 2" }];
    if ((typeof KR !== "undefined") && (typeof opentype !== "undefined")) {
      L.push({ id: "live", name: "Construction lab glyphs (live)" });
      try { KR.fonts().forEach(f => L.push({ id: f.id, name: f.name + (f.test ? " (test)" : "") })); } catch (e) {}
    }
    return L;
  }
  async function use(id) {
    src = id;
    if (id === "dua" || !(typeof KR !== "undefined") || !(typeof opentype !== "undefined")) { fam = "KDua"; has = null; src = id === "km2" ? id : "dua"; }
    if (id === "km2") { fam = "KM2"; has = null; }
    else if (id !== "dua" && (typeof KR !== "undefined") && (typeof opentype !== "undefined")) {
      await KR.load(); await KR.fontmap();
      const g = id === "live" ? KR.snapshot() : (KR.fonts().find(f => f.id === id) || {}).glyphs;
      if (!g) return use("dua");
      fam = "KF-" + (++n);
      await KR.fontFace(g, W, 100, 0, fam, "regular");
      has = new Set(Object.keys(g));
    }
    LS.set("kf-src", src);
    document.documentElement.style.setProperty("--kr", `"${fam}"`);
    await document.fonts.load(`20px "${fam}"`).catch(() => {});
    return src;
  }
  const text = lat => has ? KR.shape(lat, has, fam) : TwiScript.toKradin(lat);
  function paint(root) {
    (root || document).querySelectorAll("[data-tw]").forEach(el => {
      const lat = el.dataset.tw;
      el.textContent = text(lat);
      el.classList.add("kr");
      if (!el.dataset.lat) el.dataset.lat = TwiScript.twiLatin(lat);
      if (!el.hasAttribute("tabindex") && !el.closest("a,button")) el.tabIndex = 0;
      el.setAttribute("aria-label", el.dataset.lat);
    });
  }

  // bubble: positioned in page coordinates (not fixed), so it stays on its word on mobile while the page or the
  // address bar moves. It points at the inked box of the text, not the line box.
  const tip = document.createElement("div"); tip.className = "kf-tip"; tip.setAttribute("role", "tooltip");
  let cur = null, timer = 0;
  function box(el) {
    const r = el.getBoundingClientRect();
    if (!el.classList.contains("kr")) return r;
    const g = el.getClientRects()[0] || r, h = g.height;           // Kɔradin line boxes are tall: trim to the glyphs
    return { left: g.left, width: g.width, top: g.top + h * .18, bottom: g.bottom - h * .12 };
  }
  function show(el, touch) {
    clearTimeout(timer);
    cur = el;
    tip.textContent = el.dataset.lat; if (!tip.isConnected) document.body.append(tip);
    tip.classList.remove("on");
    const r = box(el), t = tip.getBoundingClientRect(), sx = scrollX, sy = scrollY, vw = document.documentElement.clientWidth;
    let x = r.left + r.width / 2 - t.width / 2; x = Math.max(8, Math.min(vw - t.width - 8, x));
    let y = r.top - t.height - 8; const below = y < 8 + (parseFloat(getComputedStyle(document.documentElement).getPropertyValue("--navh")) || 0);
    if (below) y = r.bottom + 8;
    tip.classList.toggle("below", below);
    tip.style.left = (x + sx) + "px"; tip.style.top = (y + sy) + "px";
    tip.style.setProperty("--ax", Math.max(10, Math.min(t.width - 10, r.left + r.width / 2 - x)) + "px");
    requestAnimationFrame(() => tip.classList.add("on"));
    if (touch) timer = setTimeout(hide, 2600);
  }
  function hide() { clearTimeout(timer); cur = null; tip.classList.remove("on"); }
  const find = e => e.target && e.target.closest && e.target.closest("[data-lat]");
  let touching = false;
  document.addEventListener("pointerover", e => { if (e.pointerType !== "mouse") return; const el = find(e); el ? (el !== cur && show(el)) : hide(); });
  document.documentElement.addEventListener("mouseleave", hide);
  document.addEventListener("pointerdown", e => {
    touching = e.pointerType !== "mouse";
    if (!touching) return;
    const el = find(e);
    if (!el || el === cur) return hide();
    show(el, true);
  });
  document.addEventListener("focusin", e => { if (touching) return; const el = find(e); el ? show(el) : hide(); }); // keyboard only
  document.addEventListener("keydown", e => { touching = false; if (e.key === "Escape") hide(); });
  addEventListener("resize", hide);
  document.addEventListener("scroll", e => { if (e.target !== document && cur && e.target.contains && e.target.contains(cur)) hide(); }, { passive: true, capture: true });

  window.KF = { sources, use, text, paint, get src() { return src; }, get fam() { return fam; } };
})();
