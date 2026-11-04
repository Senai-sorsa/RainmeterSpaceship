import { expect, test, type Page } from '@playwright/test';

// "Picture (fitted)": the top stat boxes are seated in the picture's stepped band (canvas units 2560 x 1600: x 883..1677, y 147..243, split at
// x 1280 by the centre divider). The side stacks are NOT moved: the user wants them where they were, and the two sides must mirror each other.
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
    const bx = (c: number) => ox + kk * c, by = (c: number) => oy + kk * c;
    // the four stat boxes inside the band, two and two either side of the divider
    for (const n of ['graph-cpu', 'graph-a', 'graph-b', 'graph-ram']) {
      expect(fitted[n].l, n).toBeGreaterThanOrEqual(bx(883) - 4 * kk);
      expect(fitted[n].r, n).toBeLessThanOrEqual(bx(1677) + 4 * kk);
      expect(fitted[n].t, n).toBeGreaterThanOrEqual(by(147) - 4 * kk);
      expect(fitted[n].b, n).toBeLessThanOrEqual(by(243) + 4 * kk);
    }
    expect(fitted['graph-a'].r).toBeLessThanOrEqual(bx(1280) + 3 * kk);
    expect(fitted['graph-b'].l).toBeGreaterThanOrEqual(bx(1280) - 3 * kk);
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
    expect(b!.x).toBeLessThan(500); // the original CPU box starts left of the fitted band (883 canvas units = 589 css px)
  });
}
