import { expect, test, type Page } from '@playwright/test';

// "Picture (fitted)": the four stat boxes sit one per main slot of the picture's top band (canvas units 2560 x 1600: wing slots and centre pockets, pocket
// roofs at y 143), the console rides the groove at y 103, and cyan trim is traced on those edges. The side stacks are NOT moved: the user wants them where
// they were, and the two sides must mirror each other.
const SIZES: [number, number][] = [[1707, 1067], [2560, 1600], [1920, 1200]];

type Box = { l: number; t: number; r: number; b: number };
const SIDE_MODULES = ['left-category', 'left-dots', 'left-slot1', 'left-slot2', 'left-slot3', 'left-slot4', 'right-category', 'right-dots', 'right-sysinfo', 'right-slot5', 'right-slot6', 'right-slot7', 'right-slot8'];

const open = async (page: Page, w: number, h: number, cfg: Record<string, string>) => {
  await page.setViewportSize({ width: w, height: h });
  await page.addInitScript((c) => {
    sessionStorage.setItem('cspace.booted', '1');
    localStorage.setItem('mockhost.v1', JSON.stringify({ config: c, setupDone: true, aboutMe: '' }));
  }, cfg);
  await page.goto('/?preview=1&module=all');
  await page.waitForSelector('[data-module="left-slot4"]');
};

// the boxes of every module, once they stop moving (power-on and boot settle): wait for the state, not for a fixed time
const settledBoxes = async (page: Page) => {
  const read = () => page.evaluate(() => Object.fromEntries([...document.querySelectorAll('[data-module]')].map((e) => {
    const b = e.getBoundingClientRect();
    return [e.getAttribute('data-module'), { l: b.left, t: b.top, r: b.right, b: b.bottom }];
  }))) as Promise<Record<string, Box>>;
  let prev = JSON.stringify(await read());
  await expect.poll(async () => { const cur = JSON.stringify(await read()); const same = cur === prev; prev = cur; return same; }, { intervals: [300], timeout: 8000 }).toBe(true);
  return read();
};

for (const [w, h] of SIZES) {
  test(`fitted at ${w}x${h}: stat boxes sit in the band; the side stacks are where plain picture puts them and mirror each other`, async ({ page }) => {
    await open(page, w, h, { UseShipImage: '1', PictureFit: '1' });
    const fitted = await settledBoxes(page);
    const kk = Math.min(w / 2560, h / 1600), ox = (w - 2560 * kk) / 2, oy = (h - 1600 * kk) / 2; // css px per canvas unit, and the 16:10 area's origin
    const by = (c: number) => oy + kk * c;
    // one stat box per main slot, centred in it: wing (770), pocket (1092), pocket (1468), wing (1790); all between the beams and the band's bottom edge
    const cx = (n: string) => ((fitted[n].l + fitted[n].r) / 2 - ox) / kk, cyc = (n: string) => ((fitted[n].t + fitted[n].b) / 2 - oy) / kk;
    const SLOTS: [string, number][] = [['graph-cpu', 770], ['graph-a', 1092], ['graph-b', 1468], ['graph-ram', 1790]];
    for (const [n, x] of SLOTS) {
      expect(Math.abs(cx(n) - x), n + ' centre x').toBeLessThanOrEqual(22);
      expect(cyc(n), n + ' centre y').toBeGreaterThanOrEqual(170);
      expect(cyc(n), n + ' centre y').toBeLessThanOrEqual(215);
    }
    // the pocket boxes are full size (232 canvas units wide, the skin's own size); no two boxes overlap
    for (const n of ['graph-a', 'graph-b']) expect((fitted[n].r - fitted[n].l) / kk, n + ' width').toBeGreaterThanOrEqual(225);
    const order = SLOTS.map(([n]) => fitted[n]);
    for (let k = 0; k < 3; k++) expect(order[k].r, 'box ' + k + ' vs ' + (k + 1)).toBeLessThanOrEqual(order[k + 1].l);
    // the console's lower row sits above the pocket roofs (y 143)
    expect(fitted['console'].b).toBeLessThanOrEqual(by(150));
    // the traced trim and the lower half of the HUD's own trim are drawn in fitted; plain picture has neither
    expect(await page.locator('[data-part="fitted-trim"] path').count()).toBeGreaterThanOrEqual(8);
    expect(await page.locator('[data-layer="decor-lower"]').count()).toBe(1);
    // the sides did not move: every side module sits exactly where plain picture mode puts it
    await page.evaluate(() => localStorage.setItem('mockhost.v1', JSON.stringify({ config: { UseShipImage: '1', PictureFit: '0' }, setupDone: true, aboutMe: '' })));
    await page.reload();
    await page.waitForSelector('[data-module="left-slot4"]');
    const plain = await settledBoxes(page);
    for (const n of SIDE_MODULES) {
      for (const k of ['l', 't', 'r', 'b'] as const) expect(Math.abs(fitted[n][k] - plain[n][k]), `${n}.${k}`).toBeLessThanOrEqual(1);
    }
    // and the two sides mirror each other, row for row (same heights, same distance from its own edge)
    for (const [a, b] of [['left-slot1', 'right-slot5'], ['left-slot2', 'right-slot6'], ['left-slot3', 'right-slot7'], ['left-slot4', 'right-slot8'], ['left-category', 'right-category'], ['left-dots', 'right-dots']]) {
      expect(Math.abs(fitted[a].t - fitted[b].t), `${a} vs ${b} (top)`).toBeLessThanOrEqual(h * 0.02);
      expect(Math.abs(fitted[a].l - (w - fitted[b].r)), `${a} vs ${b} (edge)`).toBeLessThanOrEqual(w * 0.02);
    }
  });
}

for (const [name, cfg] of [['line-art frame', { UseShipImage: '0' }], ['plain picture', { UseShipImage: '1', PictureFit: '0' }], ['plain picture, PictureFit unset', { UseShipImage: '1' }]] as [string, Record<string, string>][]) {
  test(`${name} keeps the original layout (no picture slots)`, async ({ page }) => {
    await open(page, 1707, 1067, cfg);
    const b = await page.locator('[data-module="graph-cpu"]').boundingBox();
    expect(b!.x).toBeLessThan(500); // the original CPU box is at its skin position (the fitted one is seated in its wing slot)
    expect(await page.locator('[data-part="fitted-trim"]').count()).toBe(0); // no fitted trim outside the fitted frame
    expect(await page.locator('[data-layer="decor-lower"]').count()).toBe(0);
  });
}
