import type { HostBridge } from './HostBridge';
import type { Scheduler } from './scheduler';

// Tells the host where the page takes the mouse. Elements marked data-hit take clicks; data-hit="keyboard" also takes
// typing (the host gives the window focus on a click there). Everywhere else the click goes through to the desktop.

type Box = { left: number; top: number; width: number; height: number };
const PAD = 6; // device pixels around each box, so a hover glow or a near miss still lands
const MAX = 64; // the host refuses more

/** Device-pixel rects [x, y, w, h], padded, empty boxes dropped. A box wholly inside another is redundant (the bigger one already takes the click),
 *  and duplicates collapse. Over the host's cap nothing is dropped: the two boxes whose union adds the least area are merged until the count fits
 *  (a dropped box is a dead button: with a drawer or log open the first boxes, the top console, stopped answering; a merged one only takes a few extra pixels). */
export function regionsOf(boxes: Box[], dpr: number): number[][] {
  const all: number[][] = [];
  for (const b of boxes) {
    if (!(b.width > 0 && b.height > 0)) continue;
    const x = Math.floor(b.left * dpr) - PAD, y = Math.floor(b.top * dpr) - PAD;
    const r = Math.ceil((b.left + b.width) * dpr) + PAD, btm = Math.ceil((b.top + b.height) * dpr) + PAD;
    all.push([clamp(x), clamp(y), Math.min(r - x, 16384), Math.min(btm - y, 16384)]);
  }
  const inside = (a: number[], o: number[]) => a[0] >= o[0] && a[1] >= o[1] && a[0] + a[2] <= o[0] + o[2] && a[1] + a[3] <= o[1] + o[3];
  const kept = all.filter((a, i) => !all.some((o, j) => j !== i && inside(a, o) && (!inside(o, a) || j < i)));
  while (kept.length > MAX) {
    let bi = 0, bj = 1, best = Infinity;
    for (let i = 0; i < kept.length; i++) for (let j = i + 1; j < kept.length; j++) {
      const cost = unionArea(kept[i], kept[j]) - kept[i][2] * kept[i][3] - kept[j][2] * kept[j][3];
      if (cost < best) { best = cost; bi = i; bj = j; }
    }
    kept[bi] = union(kept[bi], kept[bj]);
    kept.splice(bj, 1);
  }
  return kept;
}
const union = (a: number[], b: number[]): number[] => {
  const x = Math.min(a[0], b[0]), y = Math.min(a[1], b[1]);
  return [x, y, Math.min(Math.max(a[0] + a[2], b[0] + b[2]) - x, 16384), Math.min(Math.max(a[1] + a[3], b[1] + b[3]) - y, 16384)];
};
const unionArea = (a: number[], b: number[]) => { const u = union(a, b); return u[2] * u[3]; };
const clamp = (n: number) => Math.max(-16384, Math.min(16384, n));

/** Sends hit.regions every 250 ms, only when they changed. Returns the stop function. */
export function startHitRegions(host: HostBridge, doc: Document, sched: Scheduler, dpr = () => globalThis.devicePixelRatio || 1): () => void {
  let last = '';
  const send = () => {
    const els = [...doc.querySelectorAll('[data-hit]')];
    const rects = regionsOf(els.map((e) => e.getBoundingClientRect()), dpr());
    const keyboard = els.some((e) => e.getAttribute('data-hit') === 'keyboard');
    const key = JSON.stringify([rects, keyboard]);
    if (key === last) return;
    last = key;
    host.send({ type: 'hit.regions', rects, keyboard });
  };
  send();
  return sched.every(250, send);
}
