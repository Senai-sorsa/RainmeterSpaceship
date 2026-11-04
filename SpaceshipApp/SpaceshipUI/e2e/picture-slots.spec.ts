import { expect, test } from '@playwright/test';

// Picture frame: the HUD sits in the picture's slots (live test 2026-11-04). Geometry measured on ship.png in canvas units (2560 x 1600):
// the side window is bounded below by the rail, y = 1261 - 0.307 x (left; the right is its mirror); the top stat boxes live in the stepped
// band x 883..1677, y 147..243, split at x 1280 by the centre divider.
const SIZES: [number, number][] = [[1707, 1067], [2560, 1600], [1920, 1200]];

const seed = (cfg: Record<string, string>) => (c: Record<string, string>) => {
  sessionStorage.setItem('cspace.booted', '1');
  localStorage.setItem('mockhost.v1', JSON.stringify({ config: c, setupDone: true, aboutMe: '' }));
};

type Box = { l: number; t: number; r: number; b: number };

for (const [w, h] of SIZES) {
  test(`picture frame at ${w}x${h}: side rows clear the rail and mirror each other; stat boxes sit in the band`, async ({ page }) => {
    await page.setViewportSize({ width: w, height: h });
    await page.addInitScript(seed({}), { UseShipImage: '1', PictureFit: '1' });
    await page.goto('/?preview=1&module=all');
    await page.waitForSelector('[data-module="left-slot4"]');
    const read = () => page.evaluate(() => Object.fromEntries([...document.querySelectorAll('[data-module]')].map((e) => {
      const b = e.getBoundingClientRect();
      return [e.getAttribute('data-module'), { l: b.left, t: b.top, r: b.right, b: b.bottom }];
    }))) as Promise<Record<string, Box>>;
    // wait for the state (the boxes stop moving: power-on and boot settle), not for a fixed time
    let prev = JSON.stringify(await read());
    await expect.poll(async () => { const cur = JSON.stringify(await read()); const same = cur === prev; prev = cur; return same; }, { intervals: [300], timeout: 8000 }).toBe(true);
    const r = await read();
    const kk = Math.min(w / 2560, h / 1600), ox = (w - 2560 * kk) / 2, oy = (h - 1600 * kk) / 2; // css px per canvas unit, and the 16:10 area's origin
    const rail = (xcss: number, right: boolean) => { const X = (right ? w - xcss - ox : xcss - ox) / kk; return oy + kk * (1261 - 0.307 * X); };
    for (const n of ['left-slot1', 'left-slot2', 'left-slot3', 'left-slot4']) expect(r[n].b, n).toBeLessThanOrEqual(rail(r[n].r, false) - 6 * kk);
    for (const n of ['right-slot5', 'right-slot6', 'right-slot7', 'right-slot8']) expect(r[n].b, n).toBeLessThanOrEqual(rail(r[n].l, true) - 6 * kk);
    // left and right rows sit at the same heights
    for (const [a, b] of [['left-slot1', 'right-slot5'], ['left-slot2', 'right-slot6'], ['left-slot3', 'right-slot7'], ['left-slot4', 'right-slot8']])
      expect(Math.abs(r[a].t - r[b].t), `${a} vs ${b}`).toBeLessThanOrEqual(h * 0.02);
    // the first row starts below the page dots
    expect(r['left-slot1'].t).toBeGreaterThanOrEqual(r['left-dots'].b - 4 * kk);
    // the four stat boxes inside the band, two and two either side of the divider
    const bx = (c: number) => ox + kk * c, by = (c: number) => oy + kk * c;
    for (const n of ['graph-cpu', 'graph-a', 'graph-b', 'graph-ram']) {
      expect(r[n].l, n).toBeGreaterThanOrEqual(bx(883) - 4 * kk);
      expect(r[n].r, n).toBeLessThanOrEqual(bx(1677) + 4 * kk);
      expect(r[n].t, n).toBeGreaterThanOrEqual(by(147) - 4 * kk);
      expect(r[n].b, n).toBeLessThanOrEqual(by(243) + 4 * kk);
    }
    expect(r['graph-a'].r).toBeLessThanOrEqual(bx(1280) + 3 * kk);
    expect(r['graph-b'].l).toBeGreaterThanOrEqual(bx(1280) - 3 * kk);
  });
}

for (const [name, cfg] of [['line-art frame', { UseShipImage: '0' }], ['plain picture', { UseShipImage: '1', PictureFit: '0' }], ['plain picture, PictureFit unset', { UseShipImage: '1' }]] as [string, Record<string, string>][]) {
  test(`${name} keeps the original layout (no picture slots)`, async ({ page }) => {
    await page.setViewportSize({ width: 1707, height: 1067 });
    await page.addInitScript(seed({}), cfg);
    await page.goto('/?preview=1&module=all');
    await page.waitForSelector('[data-module="left-slot4"]');
    const b = await page.locator('[data-module="graph-cpu"]').boundingBox();
    expect(b!.x).toBeLessThan(500); // the original CPU box starts left of the fitted band (883 canvas units = 589 css px)
    const s4 = await page.locator('[data-module="left-slot4"]').boundingBox();
    expect(s4!.y + s4!.height).toBeGreaterThan(780); // the original fourth row sits low, below where the fitted layout puts it
  });
}
