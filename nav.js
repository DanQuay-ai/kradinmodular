/* Shared by the NeoAkan pages: phone menu, EN/FR switch, and static translations.
   Static text: put the French on the element as data-fr="…" (innerHTML), data-fr-aria, data-fr-title.
   Scripts read window.NA_LANG ("en" or "fr"). The choice is kept per browser under "na-lang". */
(function () {
  const get = () => { try { return JSON.parse(localStorage.getItem("na-lang")); } catch (e) { return null; } };
  const q = new URLSearchParams(location.search).get("lang");
  let L = q || get() || ((navigator.language || "en").toLowerCase().startsWith("fr") ? "fr" : "en");
  L = L === "fr" ? "fr" : "en";
  try { localStorage.setItem("na-lang", JSON.stringify(L)); } catch (e) {}
  window.NA_LANG = L;
  document.documentElement.lang = L;
  const NAV = { "Archetypes": "Archétypes", "Exhibition": "Exposition" };
  function apply() {
    if (L === "fr") {
      document.querySelectorAll("[data-fr]").forEach(el => { el.innerHTML = el.dataset.fr; });
      document.querySelectorAll("[data-fr-aria]").forEach(el => el.setAttribute("aria-label", el.dataset.frAria));
      document.querySelectorAll("[data-fr-title]").forEach(el => { if (el.tagName === "TITLE") document.title = el.dataset.frTitle; else el.title = el.dataset.frTitle; });
      document.querySelectorAll(".nn nav a").forEach(a => { const t = a.textContent.trim(); if (NAV[t]) a.textContent = NAV[t]; });
      const t = document.querySelector("title[data-fr-title]"); if (t) document.title = t.dataset.frTitle;
    }
    const b = document.getElementById("langbtn");
    if (b) { b.textContent = L === "fr" ? "EN" : "FR"; b.lang = L === "fr" ? "en" : "fr"; b.onclick = e => { e.preventDefault(); try { localStorage.setItem("na-lang", JSON.stringify(L === "fr" ? "en" : "fr")); } catch (x) {} const u = new URL(location.href); u.searchParams.delete("lang"); location.href = u.toString(); }; }
    const m = document.getElementById("menu-btn");
    if (m && !m.dataset.wired) { m.dataset.wired = 1; m.onclick = () => document.body.classList.toggle("menu-open"); }
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", apply); else apply();
})();
