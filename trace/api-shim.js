(() => {
  // trace-model.ts
  function validatePoints(input, normalized = false) {
    if (!Array.isArray(input) || input.length < 2 || input.length > 1e3) throw Error("Supply 2\u20131000 points");
    return input.map((p) => {
      if (!Array.isArray(p) || p.length !== 2 || p.some((x) => !Number.isFinite(x) || x < (normalized ? -0.3 : -400) || x > (normalized ? 1.3 : 2200))) throw Error("Invalid point coordinates");
      return [+p[0], +p[1]];
    });
  }
  function fitCubic(points) {
    const a = points[0], b = points.at(-1), v0 = [points[Math.min(3, points.length - 1)][0] - a[0], points[Math.min(3, points.length - 1)][1] - a[1]], v1 = [b[0] - points[Math.max(0, points.length - 4)][0], b[1] - points[Math.max(0, points.length - 4)][1]], n0 = Math.max(1e-3, Math.hypot(...v0)), n1 = Math.max(1e-3, Math.hypot(...v1));
    const t0 = v0.map((x) => x / n0), t1 = v1.map((x) => x / n1), d = [0];
    for (let i = 1; i < points.length; i++) d.push(d[i - 1] + Math.hypot(points[i][0] - points[i - 1][0], points[i][1] - points[i - 1][1]));
    const length = Math.max(1e-3, d.at(-1));
    let aa = 0, ab = 0, bb = 0, ar = 0, br = 0;
    for (let i = 0; i < points.length; i++) {
      const t = d[i] / length, u = 1 - t, fa = 3 * u * u * t, fb = 3 * u * t * t;
      for (let k = 0; k < 2; k++) {
        const A = fa * t0[k], B = -fb * t1[k], base2 = (u * u * u + fa) * a[k] + (t * t * t + fb) * b[k], r = points[i][k] - base2;
        aa += A * A;
        ab += A * B;
        bb += B * B;
        ar += A * r;
        br += B * r;
      }
    }
    const det = aa * bb - ab * ab;
    let alpha = det > 1e-9 ? (ar * bb - br * ab) / det : length / 3, beta = det > 1e-9 ? (br * aa - ar * ab) / det : length / 3;
    alpha = Math.max(0, Math.min(length * 1.5, alpha));
    beta = Math.max(0, Math.min(length * 1.5, beta));
    const controls = [a, [a[0] + alpha * t0[0], a[1] + alpha * t0[1]], [b[0] - beta * t1[0], b[1] - beta * t1[1]], b];
    let error = 0, split = 0;
    for (let i = 0; i < points.length; i++) {
      const t = d[i] / length, u = 1 - t, p = [0, 1].map((k) => u ** 3 * controls[0][k] + 3 * u * u * t * controls[1][k] + 3 * u * t * t * controls[2][k] + t ** 3 * controls[3][k]), e = Math.hypot(p[0] - points[i][0], p[1] - points[i][1]);
      if (e > error) {
        error = e;
        split = i;
      }
    }
    return { controls, error, split };
  }
  function cubicChain(points, depth = 0) {
    const fit = fitCubic(points);
    if (fit.error > 6 && depth < 4 && points.length > 8 && fit.split > 2 && fit.split < points.length - 3) return [...cubicChain(points.slice(0, fit.split + 1), depth + 1), ...cubicChain(points.slice(fit.split), depth + 1)];
    return [fit.controls];
  }
  function refitPart(part, points, suffix) {
    const p = structuredClone(part), a = points[0], b = points.at(-1), dx = b[0] - a[0], dy = b[1] - a[1], len = Math.max(1, Math.hypot(dx, dy));
    const error = Math.max(...points.map((q) => Math.abs(dx * (q[1] - a[1]) - dy * (q[0] - a[0])) / len));
    p.points = points;
    p.id = suffix;
    p.length = points.slice(1).reduce((s, q, i) => s + Math.hypot(q[0] - points[i][0], q[1] - points[i][1]), 0);
    if (error < 5 && Math.hypot(dx, dy) > 20) {
      p.kind = Math.abs(dx) < 6 ? "vertical" : Math.abs(dy) < 6 ? "horizontal" : "diagonal";
      if (p.kind === "vertical") {
        const x = (a[0] + b[0]) / 2;
        p.points = points.map((q) => [x, q[1]]);
      }
      if (p.kind === "horizontal") {
        const y = (a[1] + b[1]) / 2;
        p.points = points.map((q) => [q[0], y]);
      }
      p.error = error;
      delete p.beziers;
    } else {
      p.kind = "compoundArc";
      p.beziers = cubicChain(points);
      p.error = null;
    }
    p.recomputed = true;
    return p;
  }
  function fitStroke(points, strokeId, tag) {
    const segments = [];
    let start = 0, i = 0;
    while (i < points.length - 1) {
      let best = null;
      for (const axis of [0, 1]) {
        let min = points[i][axis], max = min;
        for (let j = i + 1; j < points.length; j++) {
          min = Math.min(min, points[j][axis]);
          max = Math.max(max, points[j][axis]);
          if (max - min > 7) break;
          if (Math.abs(points[j][1 - axis] - points[i][1 - axis]) > 90 && (!best || j > best.end)) best = { end: j, axis };
        }
      }
      if (best) {
        if (i > start) segments.push(points.slice(start, i + 1));
        segments.push(points.slice(i, best.end + 1));
        i = best.end;
        start = i;
      } else i++;
    }
    if (start < points.length - 1) segments.push(points.slice(start));
    if (!segments.length) segments.push(points);
    return segments.map((ps, j) => ({ ...refitPart({}, ps, strokeId + "__" + tag + "_P" + (j + 1)), stroke: strokeId, displayId: "P" + (j + 1), revision: 2, patch: true }));
  }
  function neighbourhood(g, targetType, targetId) {
    const selected = targetType === "stroke" ? g.parts.filter((p) => p.stroke === targetId) : targetType === "part" ? g.parts.filter((p) => p.id === targetId) : g.parts;
    const strokeIds = new Set(selected.map((p) => p.stroke));
    const ends = selected.flatMap((p) => p.points);
    for (const s of g.strokes) if (s.points.filter((_, i) => i % 3 === 0).some((a) => ends.some((b) => Math.hypot(a[0] - b[0], a[1] - b[1]) < 70))) strokeIds.add(s.id);
    return { strokeIds: [...strokeIds], partIds: g.parts.filter((p) => strokeIds.has(p.stroke)).map((p) => p.id), componentIds: [...new Set(g.strokes.filter((s) => strokeIds.has(s.id) && s.componentId).map((s) => s.componentId))], rule: "Whole source path plus all adjoining junction paths; revisit shared bases rather than duplicating corrections." };
  }
  function harmonizeRemovals(g, flags) {
    const removals = flags.filter((f) => f.name === g.name && f.action === "remove" && f.status === "open"), changes = [];
    if (!removals.length) return changes;
    const removed = /* @__PURE__ */ new Set();
    for (const f of removals) {
      for (const p of g.parts) if (f.targetType === "stroke" ? p.stroke === f.targetId : p.id === f.targetId) removed.add(p.id);
    }
    for (const f of removals) {
      const scope = neighbourhood(g, f.targetType, f.targetId);
      for (const sid of scope.strokeIds) {
        const parts = g.parts.filter((p) => p.stroke === sid);
        for (let i = 0; i < parts.length; i++) {
          const p = parts[i];
          if (removed.has(p.id)) continue;
          const adjacent = [parts[i - 1], parts[i + 1]].filter((q2) => q2 && removed.has(q2.id));
          const selectedParts = g.parts.filter((q2) => removed.has(q2.id));
          const near = selectedParts.some((q2) => [p.points[0], p.points.at(-1)].some((a) => q2.points.some((b) => Math.hypot(a[0] - b[0], a[1] - b[1]) < 70)));
          if (!adjacent.length && !near) continue;
          const q = refitPart(p, p.points, p.id);
          q.autoRevision = { reason: "Adjacent removed part", sourceKeys: [f.key], scope };
          Object.assign(p, q);
          changes.push({ glyph: g.name, part: p.id, sourceFlag: f.key, operation: "Refit neighbouring support and recompute its endpoint tangents" });
        }
      }
    }
    g.autoRevisions = changes;
    g.counts = {};
    for (const p of g.parts) g.counts[p.kind] = (g.counts[p.kind] || 0) + 1;
    return changes;
  }

  // shim.ts
  var BASE_URL = "trace/radicals.json";
  var LEGACY_URL = "trace/v1-radicals.json";
  var K = { patches: "trace-patches", rev: "trace-rev", events: "trace-events", reviews: "trace-reviews", settings: "trace-settings" };
  var ls = { get(k, d) {
    try {
      const v = localStorage.getItem(k);
      return v == null ? d : JSON.parse(v);
    } catch {
      return d;
    }
  }, set(k, v) {
    localStorage.setItem(k, JSON.stringify(v));
  } };
  var base = null;
  var legacy = null;
  async function load() {
    if (!base) base = await (await realFetch(BASE_URL)).json();
    if (!legacy) {
      try {
        legacy = await (await realFetch(LEGACY_URL)).json();
      } catch {
        legacy = base;
      }
    }
  }
  var realFetch = globalThis.fetch.bind(globalThis);
  function readReview() {
    const incorporated = new Map(base.revisionReport.reviewedFlags.map((f) => [f.key, f]));
    const rows = ls.get(K.reviews, {});
    return { flags: Object.values(rows).map((r) => {
      const f = r.payload, seen = incorporated.get(f.key);
      return { ...f, status: r.status === "open" && seen && Date.parse(r.updatedAt) <= Date.parse(seen.updatedAt) ? "revisited" : r.status, originalStatus: r.status, retracePass: seen ? 2 : null };
    }), settings: ls.get(K.settings, null), reference: base.sha256 };
  }
  function resamplePoints(points, count) {
    const lengths = [0];
    for (let i = 1; i < points.length; i++) lengths.push(lengths[i - 1] + Math.hypot(points[i][0] - points[i - 1][0], points[i][1] - points[i - 1][1]));
    const total = lengths[lengths.length - 1];
    if (total < 0.01) throw Error("Component has no length");
    return Array.from({ length: count }, (_, j) => {
      const d = total * j / (count - 1);
      let k = 1;
      while (k < lengths.length - 1 && lengths[k] < d) k++;
      const t = (d - lengths[k - 1]) / Math.max(1e-3, lengths[k] - lengths[k - 1]);
      return [0, 1].map((a) => points[k - 1][a] + (points[k][a] - points[k - 1][a]) * t);
    });
  }
  function replaceStroke(data, name, id, points, tag) {
    const g = data.items.find((g2) => g2.name === name), s = g?.strokes.find((s2) => s2.id === id);
    if (!s) return;
    s.points = points;
    s.patch = tag;
    const parts = fitStroke(points, id, tag.slice(0, 8));
    g.parts = g.parts.filter((p) => p.stroke !== id);
    g.parts.push(...parts);
    s.parts = parts.map((p) => p.id);
    g.counts = {};
    for (const p of g.parts) g.counts[p.kind] = (g.counts[p.kind] || 0) + 1;
  }
  function getAnalysis() {
    const dataset = structuredClone(base);
    const patches = ls.get(K.patches, []).filter((p) => p.status === "active");
    dataset.projectRevision = ls.get(K.rev, 0);
    dataset.patchHistory = [];
    for (const patch of patches) {
      const data = patch.payload;
      if (patch.kind === "stroke") replaceStroke(dataset, data.glyph, data.strokeId, data.points, patch.id);
      else if (patch.kind === "component") {
        const component = dataset.componentLibrary.find((c) => c.id === data.componentId);
        if (!component) continue;
        component.points = data.points;
        for (const inst of component.instances) {
          const g = dataset.items.find((g2) => g2.name === inst.glyph), s = g?.strokes.find((s2) => s2.id === inst.strokeId), t = inst.transform;
          if (!s || !t) continue;
          let normalized = resamplePoints(data.points, t.range ? t.range[1] - t.range[0] + 1 : s.points.length);
          if (t.reverse) normalized.reverse();
          if (t.mirror) normalized = normalized.map((p) => [1 - p[0], p[1]]);
          let rep = normalized.map((p) => [p[0] * t.scale[0] + t.translate[0], p[1] * t.scale[1] + t.translate[1]]);
          const da = t.anchorStart.map((x, i) => x - rep[0][i]), de = t.anchorEnd.map((x, i) => x - rep[rep.length - 1][i]);
          rep = rep.map((p, i) => p.map((x, j) => x + da[j] * (1 - i / (rep.length - 1)) + de[j] * i / (rep.length - 1)));
          const points = t.range ? [...s.points.slice(0, t.range[0]), ...rep, ...s.points.slice(t.range[1] + 1)] : rep;
          replaceStroke(dataset, g.name, s.id, points, patch.id);
        }
      }
      dataset.patchHistory.push({ id: patch.id, author: patch.author, rationale: patch.rationale, createdAt: patch.createdAt, target: patch.target });
    }
    const review = readReview();
    dataset.autoRevisions = dataset.items.flatMap((g) => harmonizeRemovals(g, review.flags));
    return dataset;
  }
  function log(actor, operation, target, payload) {
    const ev = ls.get(K.events, []);
    ev.unshift({ id: ev.length + 1, created_at: (/* @__PURE__ */ new Date()).toISOString(), actor, operation, target, payload });
    ls.set(K.events, ev.slice(0, 1e3));
  }
  function eventLog() {
    return { pass: base.revisionReport, events: ls.get(K.events, []) };
  }
  function uuid() {
    return globalThis.crypto?.randomUUID?.() || Date.now().toString(36) + Math.random().toString(36).slice(2);
  }
  function applyPatch(args, actor = "owner (browser)") {
    const expected = Number(args.expectedRevision);
    if (!Number.isInteger(expected) || expected < 0) throw Error("Supply the current expectedRevision");
    if (args.sourceHash !== base.sha256 || args.analysisVersion !== base.version) throw Error("Source font or analysis version mismatch");
    if (!String(args.rationale || "").trim()) throw Error("Explain the purpose of this change");
    const data = getAnalysis(), kind = args.kind || "stroke";
    if (expected !== data.projectRevision) throw Error("Revision conflict. Read the current study before retrying.");
    let payload, target;
    if (kind === "component") {
      const c = data.componentLibrary.find((c2) => c2.id === args.componentId);
      if (!c) throw Error("Unknown component");
      payload = { componentId: c.id, points: validatePoints(args.points, true) };
      target = c.id;
    } else {
      const g = data.items.find((g2) => g2.name === args.glyph), s = g?.strokes.find((s2) => s2.id === args.strokeId);
      if (!s) throw Error("Unknown stroke");
      if (s.componentId && data.componentLibrary.some((c) => c.id === s.componentId && c.instances.length > 1)) throw Error("This support is shared; use a component patch for " + s.componentId);
      payload = { glyph: g.name, strokeId: s.id, points: validatePoints(args.points) };
      target = g.name + "/" + s.id;
    }
    const id = uuid(), now = (/* @__PURE__ */ new Date()).toISOString(), author = String(args.author || actor).slice(0, 120), rationale = String(args.rationale).slice(0, 5e3);
    const list = ls.get(K.patches, []);
    list.push({ id, applied_revision: expected + 1, kind, target, payload, author, rationale, status: "active", createdAt: now });
    ls.set(K.patches, list);
    ls.set(K.rev, expected + 1);
    log(actor, "apply_patch", target, { id, kind, rationale, authorLabel: author, expectedRevision: expected, ...payload });
    return { patchId: id, revision: expected + 1, target, kind, affectedInstances: kind === "component" ? data.componentLibrary.find((c) => c.id === args.componentId).instances.length : 1 };
  }
  function revertPatch(id, expected, actor = "owner (browser)") {
    const list = ls.get(K.patches, []), p = list.find((x) => x.id === id && x.status === "active");
    if (!p) throw Error("Active patch not found");
    if (expected !== ls.get(K.rev, 0)) throw Error("Revision conflict");
    p.status = "reverted";
    ls.set(K.patches, list);
    ls.set(K.rev, expected + 1);
    log(actor, "revert_patch", p.target, { id, expectedRevision: expected });
    return { reverted: id, revision: expected + 1 };
  }
  var directions = /* @__PURE__ */ new Set(["Gothic", "Rounded", "Angular", "Heavy condensed"]);
  function normalize(record, current) {
    const present = current.items.find((g) => g.name === record.name);
    const isCurrent = present && (record.targetType === "glyph" || (record.targetType === "stroke" ? present.strokes : present.parts).some((p) => p.id === record.targetId));
    const dataset = isCurrent ? current : legacy;
    const glyph = dataset.items.find((g) => g.name === record.name);
    if (!glyph) throw Error("Unknown radical");
    const type = record.targetType, id = record.targetId;
    const stroke = type === "stroke" ? glyph.strokes.find((s) => s.id === id) : null, part = type === "part" ? glyph.parts.find((p) => p.id === id) : null;
    const now = (/* @__PURE__ */ new Date()).toISOString();
    return {
      key: `${glyph.name}/${type}:${id}`,
      name: glyph.name,
      label: `${glyph.label}${type === "glyph" ? "" : " / " + id}`,
      targetType: type,
      targetId: id,
      part: type === "part" ? id : null,
      action: record.action,
      status: "open",
      note: String(record.note || "").slice(0, 4e3),
      direction: directions.has(record.direction) ? record.direction : "Gothic",
      createdAt: record.createdAt || now,
      updatedAt: now,
      snapshot: { reference: dataset.reference, sha256: dataset.sha256, analysisVersion: dataset.version, glyph: { name: glyph.name, label: glyph.label, row: glyph.row, vowel: glyph.vowel, outline: glyph.outline, bounds: glyph.bounds }, strokes: stroke ? [stroke] : part ? glyph.strokes.filter((s) => s.id === part.stroke) : glyph.strokes, parts: part ? [part] : stroke ? glyph.parts.filter((p) => p.stroke === stroke.id) : glyph.parts, neighbourhood: neighbourhood(glyph, type, id) }
    };
  }
  function reviewPost(ops) {
    const rows = ls.get(K.reviews, {}), current = getAnalysis();
    for (const op of ops) {
      if (op.op === "upsert") {
        const r = normalize(op.record, current);
        rows[r.key] = { status: "open", payload: r, updatedAt: r.updatedAt };
        log("owner", op.op, r.key, r);
      } else if (op.op === "dismiss") {
        if (rows[op.key]) {
          rows[op.key].status = "dismissed";
          rows[op.key].updatedAt = (/* @__PURE__ */ new Date()).toISOString();
        }
        log("owner", "dismiss", op.key, op);
      } else if (op.op === "settings") {
        ls.set(K.settings, { preferred: directions.has(op.preferred) ? op.preferred : null, feedback: String(op.feedback || "").slice(0, 2e4) });
        log("owner", "settings", "workspace", op);
      }
    }
    ls.set(K.reviews, rows);
    return { ok: true, accepted: ops.length };
  }
  var J = (v, s = 200) => new Response(JSON.stringify(v), { status: s, headers: { "content-type": "application/json" } });
  globalThis.fetch = async (input, init = {}) => {
    const url = typeof input === "string" ? input : input.url;
    const path = url.replace(location.origin, "");
    if (!path.startsWith("/api/")) return realFetch(input, init);
    await load();
    const method = (init.method || "GET").toUpperCase();
    try {
      if (path.startsWith("/api/analysis")) return J(getAnalysis());
      if (path.startsWith("/api/collaboration")) {
        if (method === "POST") {
          const a = JSON.parse(init.body);
          return J(a.operation === "revert" ? revertPatch(a.patchId, a.expectedRevision) : applyPatch(a));
        }
        return J({ analysis: getAnalysis(), reviews: readReview(), logs: eventLog() });
      }
      if (path.startsWith("/api/logs")) return J({ ...eventLog(), reviews: readReview().flags });
      if (path.startsWith("/api/review")) {
        if (method === "POST") return J(reviewPost(JSON.parse(init.body).operations));
        return J(readReview());
      }
      return J({ error: "Unknown route" }, 404);
    } catch (e) {
      return J({ error: e.message }, 400);
    }
  };
  globalThis.TraceStudio = {
    getAnalysis: async () => {
      await load();
      return getAnalysis();
    },
    applyPatch: async (a) => {
      await load();
      return applyPatch(a, a.author || "agent");
    },
    revertPatch: async (id, rev) => {
      await load();
      return revertPatch(id, rev);
    },
    exportState: () => ({ patches: ls.get(K.patches, []), revision: ls.get(K.rev, 0), reviews: ls.get(K.reviews, {}), settings: ls.get(K.settings, null), events: ls.get(K.events, []) }),
    importState: (s) => {
      if (s.patches) ls.set(K.patches, s.patches);
      if (s.revision != null) ls.set(K.rev, s.revision);
      if (s.reviews) ls.set(K.reviews, s.reviews);
      if (s.settings) ls.set(K.settings, s.settings);
      if (s.events) ls.set(K.events, s.events);
    }
  };
})();
