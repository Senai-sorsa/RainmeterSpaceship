import { describe, expect, it } from 'vitest';
import { PICTURE_SLOTS, seatInPicture } from '../src/modules/pictureSlots';
import { visible } from '../src/modules/hidden';
import { styleFrom } from '../src/modules/style';
import layout from '../src/generated/layout.json';

const zone = (id: string, over: Partial<{ x: number; y: number; w: number; h: number; matrix: number[] }> = {}) =>
  ({ id, x: 100, y: 200, w: 200, h: 100, matrix: [1, 0, 0, 1, 0, 0], ...over });
const centre = (z: ReturnType<typeof zone>) => {
  const [a, b, c, d, e, f] = z.matrix, px = z.x + z.w / 2, py = z.y + z.h / 2;
  return [a * px + c * py + e, b * px + d * py + f];
};

describe('seatInPicture', () => {
  it('leaves a zone with no slot untouched (same object)', () => {
    const z = zone('T_alert');
    expect(seatInPicture(z)).toBe(z);
  });
  it('moves the drawn centre by exactly dx, dy and scales about it', () => {
    PICTURE_SLOTS.__t = { dx: 30, dy: -20, s: 0.5 };
    const z = zone('__t');
    const out = seatInPicture(z);
    const [cx0, cy0] = centre(z), [cx1, cy1] = centre(out);
    expect(cx1).toBeCloseTo(cx0 + 30);
    expect(cy1).toBeCloseTo(cy0 - 20);
    expect(out.matrix[0]).toBeCloseTo(0.5);
    expect(out.matrix[3]).toBeCloseTo(0.5);
    // a point 100 right of the centre ends up 50 right of the new centre
    const [a, , c, , e] = out.matrix;
    const x = a * (z.x + z.w / 2 + 100) + c * (z.y + z.h / 2) + e;
    expect(x - cx1).toBeCloseTo(50);
    delete PICTURE_SLOTS.__t;
  });
  it('gw lengthens the zone evenly about its centre', () => {
    PICTURE_SLOTS.__t = { gw: 40 };
    const z = zone('__t');
    const out = seatInPicture(z);
    expect(out.w).toBe(z.w + 40);
    expect(out.x + out.w / 2).toBeCloseTo(z.x + z.w / 2);
    expect(out.matrix).toEqual(z.matrix);
    delete PICTURE_SLOTS.__t;
  });
  it("keeps a skewed zone's centre on the shift (the skew does not move it)", () => {
    PICTURE_SLOTS.__t = { dy: -50 };
    const z = zone('__t', { matrix: [1, -0.15, 0, 1, 2, 30] });
    const out = seatInPicture(z);
    expect(centre(out)[1]).toBeCloseTo(centre(z)[1] - 50);
    expect(out.matrix.slice(0, 4)).toEqual([1, -0.15, 0, 1]);
    delete PICTURE_SLOTS.__t;
  });
  it('sy scales only the height about the drawn centre: width and the centre x stay, height shrinks, the centre moves by dy', () => {
    PICTURE_SLOTS.__t = { dy: 10, sy: 0.5 };
    const z = zone('__t');
    const out = seatInPicture(z);
    expect(out.matrix[0]).toBeCloseTo(1); // x scale untouched
    expect(out.matrix[3]).toBeCloseTo(0.5); // y scale halved
    const [cx0, cy0] = centre(z), [cx1, cy1] = centre(out);
    expect(cx1).toBeCloseTo(cx0);
    expect(cy1).toBeCloseTo(cy0 + 10);
    delete PICTURE_SLOTS.__t;
  });
  it('GPU and NET share one size, and CPU and MEMORY share another (only the height differs from before)', () => {
    const { G1_cpu: c, G2_select: g, G3_select: n, G4_ram: m } = PICTURE_SLOTS;
    expect(g.s ?? 1).toBe(n.s ?? 1); expect(g.sy).toBe(n.sy);
    expect(c.s).toBe(m.s); expect(c.sy).toBe(m.sy);
    expect(g.s ?? 1).toBe(1); // the pocket boxes keep their width
    expect(n.dy!).toBeGreaterThan(g.dy!); // NET a little lower
  });
  it('ignores a malformed matrix instead of throwing', () => {
    PICTURE_SLOTS.__t = { dy: 5 };
    const z = zone('__t', { matrix: [1, 0, 0] });
    expect(seatInPicture(z)).toBe(z);
    delete PICTURE_SLOTS.__t;
  });
  it('the side stacks are never moved: every left/right zone of the real layout except the wing tabs and the app symbol displays comes back untouched', () => {
    const sides = layout.zones.filter((z) => /^(L_|R_)/.test(z.id) && !/_tabs$|_category$/.test(z.id));
    expect(sides.length).toBeGreaterThan(12);
    for (const z of sides) expect(seatInPicture(z as never), z.id).toBe(z);
  });
  it("the wing tabs are seated away from the centre: the left one moves left, the right one right, by the same distance up to the layout's own asymmetry", () => {
    const L = seatInPicture(zone('L_tabs')), R = seatInPicture(zone('R_tabs')), l0 = zone('L_tabs'), r0 = zone('R_tabs');
    expect(L.matrix[4] - l0.matrix[4]).toBeLessThan(-100);
    expect(R.matrix[4] - r0.matrix[4]).toBeGreaterThan(100);
    expect(Math.abs((L.matrix[4] - l0.matrix[4]) + (R.matrix[4] - r0.matrix[4]))).toBeLessThanOrEqual(20); // the skin lays the right tabs out 17 units differently
  });
  it('the real layout mirrors left and right: matching zones are drawn at the same height', () => {
    const drawn = (id: string) => { const z = layout.zones.find((q) => q.id === id)!, [a, b, c, d, e, f] = z.matrix, px = z.x + z.w / 2, py = z.y + z.h / 2; return b * px + d * py + f + 0 * (a + c + e); };
    for (const [l, r] of [['L_app1', 'R_app1'], ['L_app2', 'R_app2'], ['L_app3', 'R_app3'], ['L_app4', 'R_app4'], ['L_category', 'R_category'], ['L_location', 'R_sysinfo'], ['L_dots', 'R_dots']])
      expect(Math.abs(drawn(l) - drawn(r)), l + ' vs ' + r).toBeLessThanOrEqual(1);
  });
});

describe('visible with the picture frame', () => {
  const Z = { a: zone('G1_cpu'), b: zone('T_alert'), list: [zone('G2_select'), zone('G3_select')] };
  it('does nothing extra without pic', () => {
    expect(visible(Z, '')).toBe(Z);
    expect(visible(Z, '', false)).toBe(Z);
  });
  it('seats the zones that have a slot when pic is on, and keeps the others', () => {
    const out = visible(Z, '', true);
    expect(out.a.matrix).not.toEqual(Z.a.matrix);
    expect(out.b).toBe(Z.b);
    expect(out.list[0].matrix).not.toEqual(Z.list[0].matrix);
  });
  it('hidden zones stay hidden with pic on', () => {
    const out = visible(Z, 'G1_cpu,G3_select', true) as { a?: unknown; list: (unknown | undefined)[] };
    expect(out.a).toBeUndefined();
    expect(out.list[1]).toBeUndefined();
    expect(out.list[0]).toBeDefined();
  });
});

describe('Style.fitted', () => {
  it('is on only for the fitted picture; plain picture, rendered and none keep the original layout', () => {
    expect(styleFrom({ UseShipImage: '1', PictureFit: '1' }).fitted).toBe(true);
    expect(styleFrom({ UseShipImage: '1', PictureFit: '0' }).fitted).toBe(false); // the picture as it always was
    expect(styleFrom({ UseShipImage: '1' }).fitted).toBe(false);
    expect(styleFrom({ UseShipImage: '0', PictureFit: '1' }).fitted).toBe(false);
    expect(styleFrom({ UseShipImage: '1', PictureFit: '1', FrameOff: '1' }).fitted).toBe(false);
    expect(styleFrom({}).fitted).toBe(false);
  });
});
