/* Personal studio bar: pick, create, rename, delete and export modular font projects.
   Each project keeps its own glyph edits, builds and serif styles in this browser. Needs kr.js (KR). */
(() => {
  if (typeof KR === "undefined") return;
  const css = `.studio{display:flex;flex-wrap:wrap;align-items:center;gap:8px;padding:8px 14px;background:var(--card);border-bottom:.5px solid var(--sep);font-size:13px;position:relative;z-index:15}
.studio b{font-weight:600;margin-right:4px}.studio .sp{flex:1}
.studio select,.studio button{border:0;border-radius:8px;background:var(--fill);color:var(--label);font:500 13px var(--font);padding:6px 10px;cursor:pointer}
.studio button.pri{background:var(--label);color:var(--bg)}
.studio .tag{font:600 10px var(--font);letter-spacing:.08em;text-transform:uppercase;color:var(--label2);border:1px solid var(--sep);border-radius:99px;padding:2px 8px}`;
  const st = document.createElement("style"); st.textContent = css; document.head.append(st);
  const bar = document.createElement("div"); bar.className = "studio"; bar.setAttribute("aria-label", "Studio");
  const P = KR.projects(), cur = KR.PROJ;
  const main = KR.SCRIPT === "adinkra" ? "Adinkra alphabet" : "Kɔradin Modular";
  const styleOpts = () => (typeof KST !== "undefined" ? [{ id: "regular", name: "Regular" }].concat(KST.PRESETS.map(p => ({ id: p.id, name: p.name }))).concat(KST.saved().map(s => ({ id: s.id, name: s.name }))) : [{ id: "regular", name: "Regular" }]);
  bar.innerHTML = `<span class="tag">Studio</span><b>Font</b>
    <select id="st-p" aria-label="Font project"><option value="">${main}</option>${P.map(p => `<option value="${p.id}">${p.name.replace(/</g, "&lt;")}</option>`).join("")}</select>
    <button id="st-new">New</button><button id="st-dup">Duplicate</button><button id="st-ren"${cur ? "" : " disabled"}>Rename</button><button id="st-del"${cur ? "" : " disabled"}>Delete</button>
    <span class="sp"></span><b>Export</b>
    <select id="st-w" aria-label="Export weight">${[[22, "Thin"], [36, "Light"], [50, "Regular"], [66, "Medium"], [82, "Bold"], [98, "Black"]].map(([w, n]) => `<option value="${w}"${w === 50 ? " selected" : ""}>${n} · ${w}</option>`).join("")}</select>
    <select id="st-s" aria-label="Export style">${styleOpts().map(s => `<option value="${s.id}">${s.name}</option>`).join("")}</select>
    <button class="pri" id="st-x">Download .otf</button>`;
  const nav = document.querySelector(".nav"); (nav ? nav.after.bind(nav) : x => document.body.prepend(x))(bar);
  const $ = id => document.getElementById(id);
  $("st-p").value = cur;
  $("st-p").onchange = e => { KR.useProject(e.target.value); location.reload(); };
  $("st-new").onclick = () => { const n = prompt("Name of the new font (starts from the default glyphs):"); if (!n) return; KR.useProject(KR.createProject(n.trim(), false)); location.reload(); };
  $("st-dup").onclick = () => { const n = prompt("Name of the copy:", KR.projectName() + " copy"); if (!n) return; KR.useProject(KR.createProject(n.trim(), true)); location.reload(); };
  $("st-ren").onclick = () => { const n = prompt("New name:", KR.projectName()); if (!n) return; KR.renameProject(cur, n.trim()); location.reload(); };
  $("st-del").onclick = () => { if (!confirm(`Delete “${KR.projectName()}” and all its glyphs, builds and styles? This cannot be undone.`)) return; KR.deleteProject(cur); location.reload(); };
  $("st-x").onclick = async e => {
    const b = e.currentTarget, t = b.textContent; b.disabled = true; b.textContent = "Building…";
    try {
      await KR.load();
      const sid = $("st-s").value, style = sid === "regular" ? "regular" : (() => { const s = (typeof KST !== "undefined" ? KST.PRESETS.concat(KST.saved()) : []).find(x => x.id === sid); return s ? { ...s, P: { ...KST.DEF, ...s.P } } : "regular"; })();
      const sname = sid === "regular" ? "" : " " + $("st-s").selectedOptions[0].textContent;
      await KR.downloadFont(+$("st-w").value, style, KR.projectName() + sname);
    } catch (err) { alert("Export failed: " + err.message); }
    b.disabled = false; b.textContent = t;
  };
})();
