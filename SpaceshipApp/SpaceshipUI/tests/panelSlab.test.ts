import { describe, expect, it } from 'vitest';
import { fixPanelSlabs, slabPath, type SlabZone } from '../src/ui/panelSlab';
import parts from '../src/generated/frameparts.json';
import layout from '../src/generated/layout.json';

const decor = (parts as unknown as Record<string, [string, Record<string, string>][]>)['Decor.inc'][0][1];
const zone = (id: string) => layout.zones.find((z) => z.id === id) as SlabZone;
const num = (s: string) => (s.match(/-?\d+(\.\d+)?/g) ?? []).map(Number);
// the four vertices of a slab path, as [x, y]
const verts = (p: string) => { const n = num(p.replace(/ClosePath 1/, '')); return [0, 2, 4, 6].map((i) => [n[i], n[i + 1]] as [number, number]); };
const card = (z: SlabZone) => { const [a, b, c, d, e, f] = z.matrix, T = (x: number, y: number): [number, number] => [a * x + c * y + e, b * x + d * y + f]; return { tr: T(z.x + z.w, z.y), tl: T(z.x, z.y), bl: T(z.x, z.y + z.h), br: T(z.x + z.w, z.y + z.h) }; };
const dist = (p: [number, number], q: [number, number]) => Math.hypot(p[0] - q[0], p[1] - q[1]);

describe('slabPath', () => {
  it('is the zone rectangle grown by the padding, through an identity matrix', () => {
    expect(slabPath({ x: 100, y: 200, w: 50, h: 80, matrix: [1, 0, 0, 1, 0, 0] }, 5)).toBe('155.0,195.0 | LineTo 95.0,195.0 | LineTo 95.0,285.0 | LineTo 155.0,285.0 | ClosePath 1');
  });
  it('through a skewed matrix every corner is the transformed padded corner', () => {
    const z = { x: 0, y: 0, w: 10, h: 10, matrix: [1, 0.5, -0.2, 1, 3, 4] };
    const [tr, tl, bl, br] = verts(slabPath(z, 0));
    expect(tl).toEqual([3, 4]); expect(tr).toEqual([13, 9]); expect(bl).toEqual([1, 14]); expect(br).toEqual([11, 19]);
  });
});

describe('the real bottom panels', () => {
  for (const id of ['B_panelL', 'B_panelR']) {
    it(`${id}: the slab hugs the card, every corner within about the padding (it used to hang about 50 units below)`, () => {
      const c = card(zone(id));
      const [tr, tl, bl, br] = verts(slabPath(zone(id)));
      for (const [name, got, want] of [['tr', tr, c.tr], ['tl', tl, c.tl], ['bl', bl, c.bl], ['br', br, c.br]] as const)
        expect(dist(got, want), `${id} ${name}`).toBeLessThanOrEqual(14);
    });
  }
  it('the original skin slabs were NOT this close (the reason for the fix)', () => {
    const old = verts('1956.0,1381.1 | LineTo 1867.2,1345.0 | LineTo 1828.6,1566.1 | LineTo 1913.9,1600.0 | ClosePath 1');
    const c = card(zone('B_panelR'));
    expect(dist(old[3], c.br)).toBeGreaterThan(50);
  });
});

describe('fixPanelSlabs', () => {
  it('rewrites exactly the four slab paths of the real Decor section and nothing else', () => {
    const out = fixPanelSlabs(decor, [zone('B_panelL'), zone('B_panelR')]);
    expect(out).not.toBe(decor);
    const changed = Object.keys(decor).filter((k) => out[k] !== decor[k]).sort();
    expect(changed).toEqual(['P39', 'P40', 'P41', 'P42']);
    expect(out.P39).toBe(out.P40); expect(out.P41).toBe(out.P42);
  });
  it('leaves a section without the skin slabs untouched (same object), and a missing zone alone', () => {
    const other = { P1: '0,0 | LineTo 1,1' };
    expect(fixPanelSlabs(other, [zone('B_panelR')])).toBe(other);
    const out = fixPanelSlabs(decor, [zone('B_panelR')]); // only the right zone given
    expect(out.P41).not.toBe(decor.P41);
    expect(out.P39).toBe(decor.P39);
    expect(fixPanelSlabs(decor, [])).toBe(decor);
  });
  it('ignores a zone with a malformed matrix', () => {
    expect(fixPanelSlabs(decor, [{ ...zone('B_panelR'), matrix: [1, 0] }])).toBe(decor);
  });
});
