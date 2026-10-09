/* Twi engine: detection + Latin -> Kɔradin input + Latin -> Adinkra
   Shared by kradinmodular site and the browser extension. No dependencies. */
(function (root) {
  const V = "aeiouɛɔ";
  const OPEN = /[ɛɔƐƆ]/;

  // Unambiguous Twi words (after shortcut + lowercase normalisation)
  const STRONG = new Set(`
    yɛ ye ɛyɛ eye ɛnyɛ ennye ɔno ono wɔn won yɛn yen mo hwan ɛhe ehe ɛhefa sɛn sen dɛn den adɛn aden ɛdeɛn
    deɛ dee nyinaa nso nanso ɛna ena enti ɛno eno ɛsɛ ese ɛwɔ ewo wɔ ɛde ede bɛ bɛyɛ beye mɛ mɛkɔ meko kɔ ko kɔɔ
    ba bae aba mepa mepaakyɛw paakyɛw kyɛw medaase medaase meda ase ayekoo ayeekoo akwaaba yoo ampa saa paa
    ɛte ete ɛyɛ deɛn ɔhene ohene ahene ɔbaa obaa mmaa ɔbarima obarima mmarima abofra mmofra nnipa onipa ɔnipa
    nyame onyame ɔdomankoma odomankoma asase abosom ɔbosom nananom nana sika fie efie ɔkwan okwan ɛkwan
    adwuma adwene adwenem nsɛm nsem asɛm asem kasa twi akan akanfoɔ asante asanteman abusua ɔdɔ odo mepɛ mepe
    ɛpɛ wopɛ wope ɔpɛ ope hwɛ hwe hunu hu nim mennim minim mekɔ mɛba meba mewɔ mewo wowɔ ɔwɔ owo yɛwɔ
    dwom ndwom agorɔ agoro aduane aduan nsuo nsu ɛnnɛ nnɛ ɛnne ɔkyena okyena ɛnnora nnora daa bere ɛbere
    ahoɔden ahoɔfɛ ahofɛ ahoofɛ nkwa ɔdehyeɛ odehyee adehyeɛ ɔman oman aman ɛkɔm ekom nkɔm abɛ adinkra
    kente ɔsɛe ose kyerɛ kyere kyerɛw kyerew kenkan bisa ka kae kasaa ɔkasa sua suaa sukuu ɔkyerɛkyerɛfoɔ
    biribi biribiara ɛbɛyɛ ebeye bɛn ben ahe dodoɔ dodow kakra ketewa kɛseɛ kese tenten tiaa fɛ fɛfɛ
    awo awoɔ papa maame agya ɛna nua nuabarima nuabaa ɔyere oyere kunu ɔba oba mma nanabaa
    yaa akosua kwaku kwabena kwadwo kofi kwame kwasi kwesi akua amma abena adwoa afua akwasi esi efua
    yaw ama kwaw kwame ɛkwan nkra nkɔsoɔ nkoso mpaebɔ mpae nyansa nyansafoɔ ahenfie ahemfie ohemmaa ɔhemmaa
    sɛnea senea ɛsiane esiane ɛfiri efiri firi fi wɔhɔ woho ɛhɔ eho ha ɛha ehɔ ɔkɔɔ ɛkɔ eko ɛba eba
    ɛmmom mmom anaa anaasɛ anaase sɛdeɛ sedee ɛsɛ ɛmu emu akyi anim ase so soro fam mfinimfini
    akɔm frimpɔŋ frimpong mensah mɛnsa dontoh boateng owusu osei agyeman asamoah ofori mensa
    `.trim().split(/\s+/));

  // Short words that also exist in English/French: weak evidence only
  const WEAK = new Set("me wo no na ne se de a ho mu ma yi ɛ ɔ o e so to da di fa kɔ ko bo".split(" "));

  const ENG = new Set(`the and is are was were be been to of in on at for with that this it you he she they we i
    not but or as by from have has had do does did will would can could should what which who how when where
    why all any my your his her our their its an if then than there here about into over just like more most
    very also new one two get got make made out up down so no yes it's i'm don't`.split(/\s+/));
  const FRA = new Set(`le la les des du un une et est sont pour pas dans sur avec que qui ce cette il elle ils
    nous vous je tu au aux par plus mais ou son sa ses leur tout comme bien être avoir fait c'est j'ai`.split(/\s+/));

  const SYL = new RegExp(
    "^(?:(?:ng|[mn])(?![" + V + "]))?(?:(?:kp|gb|ky|gy|hy|ny|tw|dw|hw|kw|my|[pbtdkgfshmnwyrljvz])?[" + V +
    "]+(?:(?:ng|[mn])(?![" + V + "]))?)+$");

  function stripMarks(s) {
    return s.normalize("NFD").replace(/[̀-ͯ]/g, "").normalize("NFC");
  }

  // Online typing shortcuts: 3 = ɛ, ) = ɔ, inside or at the end of words (Y3, fo), m3ko)
  function shortcuts(s) {
    return s
      .replace(/(?<=\p{L})3|3(?=\p{L})/gu, (m) => "ɛ")
      .replace(/(?<=\p{L})\)/gu, "ɔ");
  }

  function words(s) {
    return (stripMarks(shortcuts(s)).toLowerCase().match(/[\p{L}']+/gu) || []);
  }

  /* Returns {isTwi, score, n} for a block of text. */
  function detect(text) {
    const w = words(text);
    const n = w.length;
    if (!n) return { isTwi: false, score: 0, n };
    let twi = 0, foreign = 0, seg = 0, open = 0;
    for (const x of w) {
      if (OPEN.test(x)) open++;
      if (STRONG.has(x)) twi += 1;
      else if (WEAK.has(x)) twi += 0.35;
      if (ENG.has(x) || FRA.has(x)) foreign += WEAK.has(x) ? 0.5 : 1;
      if (SYL.test(kradinWord(x).replace(/w$/, ""))) seg++;
    }
    const score = (twi + open * 1.2) / n;
    const segRatio = seg / n;
    const foreignRatio = foreign / n;
    let isTwi;
    if (n <= 2) isTwi = (open > 0 || twi >= 1) && foreignRatio < 0.5 && segRatio === 1;
    else isTwi = score >= 0.3 && foreignRatio < 0.18 && segRatio >= 0.8;
    return { isTwi, score: +score.toFixed(2), seg: +segRatio.toFixed(2), foreign: +foreignRatio.toFixed(2), n };
  }

  /* Latin -> string to be typed in the Koradin font (its ligatures draw the syllables). */
  function kradinWord(w) {
      w = w.replace(/'/g, "");
      w = w.replace(/oh$/, "ɔ").replace(/ah$/, "a");                    // Dontoh -> dontɔ, Mensah -> mensa
      w = w.replace(/([bdfgkpts])r([aeiouɛɔ])/g, "$1$2r$2");             // Brafo -> barafo
      w = w.replace(/kw([iouɔɛ])/g, "kɔ$1");                             // kw only before a, e
      w = w.replace(/c/g, "k").replace(/x/g, "ks").replace(/q/g, "k");   // loan letters absent from the font
      return w;
  }
  function toKradin(s) {
    s = stripMarks(shortcuts(s)).toLowerCase();
    return s.replace(/[\p{L}']+/gu, kradinWord);
  }

  /* Latin -> string to be typed in the Adinkra Alphabet font. ɛ and ɔ use the capital forms. */
  function toAdinkra(s) {
    s = stripMarks(shortcuts(s)).toLowerCase();
    return s.replace(/ɛ/g, "E").replace(/ɔ/g, "O").replace(/ŋ/g, "ng");
  }

  const api = { detect, toKradin, toAdinkra, shortcuts, words, SYL };
  if (typeof module !== "undefined") module.exports = api;
  root.TwiScript = api;
})(typeof globalThis !== "undefined" ? globalThis : this);
