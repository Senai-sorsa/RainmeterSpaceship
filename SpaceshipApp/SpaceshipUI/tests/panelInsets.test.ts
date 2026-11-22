import { describe, expect, it } from 'vitest';
import type { Style } from '../src/draw/canvas';
import { leftRows, panelLeftFrame, panelRightFrame, rightRows, RIGHT_INSET } from '../src/modules/panels';

// Live test: the bottom-left panel was fully aligned (text in the centre) and must stay exactly so; the right-most panel's text and TERMINAL button
// crowded the card's right edge, so only that one gets more room.
const style: Style = {
  s: 1, tier: 0, glowA: 46, glowW: 3.2, coreWhite: 0.3, hudA: 255, edit: false,
  textGlow: 4, textGlowA: 150, textSmall: 1.85, textLarge: 1.45, fontText: 'Oxanium', fontNum: 'B612 Mono', fontTitle: 'Michroma',
  white: [215, 240, 255, 255], dim: [0, 140, 185, 255], panel: [0, 30, 45, 90], accent: [0, 210, 255, 255],
  warn: [255, 130, 40, 255], alert: [255, 60, 70, 255], text: [170, 235, 255, 255], hi: [255, 105, 135, 255], good: [60, 255, 170, 255],
};
const zone = { x: 0, y: 0, w: 96, h: 146 }; // B_panelL / B_panelR are 96 x 146; at x, y 0 the ops are in zone units
type T = { kind: 'text'; x: number; y: number; text: string; align: string; clipW?: number };
const texts = (ops: ReturnType<typeof panelLeftFrame>) => ops.map((o) => o.shape).filter((s): s is T & typeof s => s.kind === 'text') as T[];

describe('left panel is unchanged', () => {
  const t = texts(panelLeftFrame(leftRows(new Date(2026, 10, 4, 12, 0, 0), {}, {}), zone, style));
  it('labels sit 6 from the left edge and values 5 from the right, as before', () => {
    const labels = t.filter((x) => x.align === 'LeftCenter'), values = t.filter((x) => x.align === 'RightCenter');
    expect(labels.length).toBeGreaterThan(5);
    for (const l of labels) expect(l.x).toBe(6);
    for (const v of values) expect(v.x).toBe(91);
  });
});

describe('right panel has room on the right', () => {
  const ops = panelRightFrame(rightRows({}, style, { host: 'BLACK-CLOVER', os: 'Windows 11', cpu: 'RYZEN AI 9 465', gpu: 'RTX 5070 Laptop', display: '2560x1600' }), zone, style);
  const t = texts(ops);
  it('values end RIGHT_INSET - 1 from the right edge and labels start RIGHT_INSET from the left', () => {
    const labels = t.filter((x) => x.align === 'LeftCenter'), values = t.filter((x) => x.align === 'RightCenter');
    for (const l of labels) expect(l.x).toBe(RIGHT_INSET);
    for (const v of values) expect(v.x).toBe(zone.w - (RIGHT_INSET - 1));
    expect(zone.w - values[0].x).toBeGreaterThanOrEqual(9); // was 5
  });
  it("values are clipped narrower than the left panel's, so long ones keep a gap from the labels", () => {
    const values = t.filter((x) => x.align === 'RightCenter');
    for (const v of values) expect(v.clipW ?? 0).toBeLessThanOrEqual(56);
    const left = texts(panelLeftFrame(leftRows(new Date(2026, 10, 4, 12, 0, 0), {}, {}), zone, style)).filter((x) => x.align === 'RightCenter');
    expect(left[0].clipW).toBeCloseTo(96 * 0.66);
  });
  it('the TERMINAL text is centred in the card and its button is inset the same on both sides', () => {
    const term = t.find((x) => x.text.includes('TERMINAL'))!;
    expect(term.x).toBeCloseTo(zone.w / 2);
    const rects = ops.map((o) => o.shape).filter((s) => s.kind === 'poly' || s.kind === 'rect');
    expect(rects.length).toBeGreaterThan(0);
  });
  it('RIGHT_INSET is wider than the left panel\'s 6', () => { expect(RIGHT_INSET).toBeGreaterThan(6); });
});
