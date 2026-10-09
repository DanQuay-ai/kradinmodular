const TWI = ["a","b","d","e","ɛ","f","g","h","i","k","l","m","n","o","ɔ","p","r","s","t","u","w","y"];
const LOAN = ["c","j","q","v","x","z"];
const key = (l) => (l === "ɛ" ? "E" : l === "ɔ" ? "O" : l);
const cell = (l, cls) => `<div class="cell ${cls || ""}"><div class="g" aria-hidden="true">${key(l)}</div><div class="l">${l}</div><div class="k">key ${key(l)}</div></div>`;
document.getElementById("twi").innerHTML = TWI.map((l) => cell(l, l === "ɛ" || l === "ɔ" ? "open" : "")).join("");
document.getElementById("loan").innerHTML = LOAN.map((l) => cell(l, "loan")).join("");

const ad = (s) => TwiScript.toAdinkra(s);
const DIG = [["ky","kyɛ"],["gy","gyae"],["hy","hyɛ"],["ny","nyame"],["tw","twi"],["dw","dwom"],["hw","hwɛ"],["kw","kwame"],["kp","kpakpa"],["gb","gbe"],["ng","frimpɔng"]];
document.getElementById("dig").innerHTML =
  `<div class="tr head"><span>Sound</span><span>Sign</span><span>Example</span><span>In Adinkra</span></div>` +
  DIG.map(([d, w]) => `<div class="tr"><b>${d}</b><span class="g">${ad(d)}</span><span>${w}</span><span class="g">${ad(w)}</span></div>`).join("");

const WORDS = ["akwaaba", "medaase", "ɛte sɛn", "adinkra", "nyame", "sankɔfa", "kɔradin", "Charles Korankye"];
document.getElementById("words").innerHTML = WORDS.map((w) => `<div class="tr"><span>${w}</span><span class="g">${ad(w)}</span></div>`).join("");

document.getElementById("ref").innerHTML = [..."ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"]
  .map((c) => `<div><div class="g">${c}</div><div class="k">${c}</div></div>`).join("");
