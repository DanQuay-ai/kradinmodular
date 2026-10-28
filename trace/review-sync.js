'use strict';
// Durable review queue with a browser-local outbox for interrupted connections.
globalThis.KradinReviewSync = class {
  constructor({ initial, onReview, onStatus, transport = (input, init) => globalThis.fetch(input, init) }) {
    this.request = transport; this.state = structuredClone(initial); this.previous = structuredClone(initial);
    this.onReview = onReview; this.onStatus = onStatus; this.ready = false; this.busy = false;
    this.pending = new Map(); this.timer = null;
    try { for (const op of JSON.parse(localStorage.getItem('kradin-review-outbox-v2') || '[]')) this.pending.set(op.slot, op); } catch {}
  }
  queue(slot, op) {
    this.pending.set(slot, { ...op, slot, id: (globalThis.crypto?.randomUUID?.() || Date.now()+'-'+Math.random()) });
    this.saveOutbox(); this.status('saving');
  }
  saveOutbox() { try { localStorage.setItem('kradin-review-outbox-v2', JSON.stringify([...this.pending.values()])); } catch {} }
  status(state) { this.onStatus(state, this.pending.size); }
  update(next) {
    const before = new Map(this.previous.flags.map(f => [f.key, f]));
    for (const flag of next.flags) {
      if (JSON.stringify(before.get(flag.key)) !== JSON.stringify(flag)) this.queue('flag:'+flag.key, { op: 'upsert', record: flag });
      before.delete(flag.key);
    }
    for (const key of before.keys()) this.queue('flag:'+key, { op: 'dismiss', key });
    if (next.preferred !== this.previous.preferred || next.feedback !== this.previous.feedback) this.queue('settings', { op: 'settings', preferred: next.preferred, feedback: next.feedback });
    this.state = structuredClone(next); this.previous = structuredClone(next);
    clearTimeout(this.timer); this.timer = setTimeout(() => this.flush(), 450);
  }
  async start() {
    this.status('connecting');
    try {
      const response = await this.request('/api/review', { cache: 'no-store' });
      if (!response.ok) throw Error('Review unavailable');
      const remote = await response.json();
      if (!Array.isArray(remote.flags)) throw Error('Invalid review');
      const known = new Map(remote.flags.map(f => [f.key, f]));
      const merged = new Map(remote.flags.filter(f => f.status === 'open').map(f => [f.key, f]));
      for (const flag of this.state.flags) {
        const op = this.pending.get('flag:'+flag.key);
        if (op?.op === 'upsert') merged.set(flag.key, flag);
        else if (!known.has(flag.key)) { merged.set(flag.key, flag); this.queue('flag:'+flag.key, { op: 'upsert', record: flag }); }
      }
      for (const op of this.pending.values()) {
        if (op.op === 'dismiss') merged.delete(op.key);
        if (op.op === 'upsert') merged.set(op.record.key, op.record);
      }
      let settings = remote.settings || { preferred: this.state.preferred, feedback: this.state.feedback };
      const pendingSettings = this.pending.get('settings');
      if (pendingSettings) settings = pendingSettings;
      else if (!remote.settings && (this.state.preferred || this.state.feedback)) this.queue('settings', { op: 'settings', ...settings });
      this.state = { history: remote.flags.filter(f=>f.status==='revisited'), flags: [...merged.values()], preferred: settings.preferred || null, feedback: settings.feedback || '' };
      this.previous = structuredClone(this.state); this.ready = true; this.onReview(structuredClone(this.state));
      await this.flush();
    } catch { this.ready = false; this.status('offline'); }
  }
  async flush() {
    if (!this.ready || this.busy) return;
    if (!this.pending.size) { this.status('saved'); return; }
    this.busy = true; this.status('saving');
    const batch = [...this.pending.values()].slice(0, 50);
    try {
      const response = await this.request('/api/review', { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ operations: batch.map(op => op.op === 'upsert' ? { ...op, record: { ...op.record, snapshot: undefined } } : op) }) });
      if (!response.ok) throw Error('Review could not be saved');
      for (const op of batch) if (this.pending.get(op.slot)?.id === op.id) this.pending.delete(op.slot);
      this.saveOutbox(); this.busy = false;
      if (this.pending.size) return this.flush();
      this.status('saved');
    } catch { this.busy = false; this.status('offline'); }
  }
  retry() { return this.ready ? this.flush() : this.start(); }
};
