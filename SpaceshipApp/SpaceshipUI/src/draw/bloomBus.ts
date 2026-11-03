import { signal } from '@preact/signals';
import type { Op } from './canvas';

// The light bus (tasks/hyperrealism-plan.md D1): each OpsView bloom anchor posts its glow ops with its screen CTM, and
// the one light canvas (ui/BloomLayer) draws them all. Every change replaces the map so subscribers see a new value.

/** SVG user units to CSS px, as getScreenCTM() returns it. */
export type Ctm = { a: number; b: number; c: number; d: number; e: number; f: number };
/** far: the anchor is depth-hazed (BloomLayer draws its tile softer, bloomPaint HAZE_STACK). */
export type BloomEntry = { ops: Op[]; ctm: Ctm; far?: boolean };

export const bloomEntries = signal<ReadonlyMap<string, BloomEntry>>(new Map());

const sameCtm = (x: Ctm, y: Ctm) => x.a === y.a && x.b === y.b && x.c === y.c && x.d === y.d && x.e === y.e && x.f === y.f;

/** Adds or replaces one anchor's light. The same ops array with the same CTM is a no-op (no redraw). */
export function postBloom(key: string, e: BloomEntry) {
  const old = bloomEntries.value.get(key);
  if (old && old.ops === e.ops && sameCtm(old.ctm, e.ctm) && !old.far === !e.far) return;
  const ctm = { a: e.ctm.a, b: e.ctm.b, c: e.ctm.c, d: e.ctm.d, e: e.ctm.e, f: e.ctm.f };
  bloomEntries.value = new Map(bloomEntries.value).set(key, e.far ? { ops: e.ops, ctm, far: true } : { ops: e.ops, ctm });
}

export function dropBloom(key: string) {
  if (!bloomEntries.value.has(key)) return;
  const m = new Map(bloomEntries.value);
  m.delete(key);
  bloomEntries.value = m;
}
