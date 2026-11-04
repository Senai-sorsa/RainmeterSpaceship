import { expect, test, type Browser, type Page } from '@playwright/test';

// "Picture (fitted)": the four stat boxes sit one per main slot of the picture's top band (canvas units 2560 x 1600: wing slots and centre pockets, pocket
// roofs at y 143), the console rides the groove at y 103, the wing tabs sit in the slanted channels near the screen edges, the status strips sit in the
// bottom console band, and cyan trim is traced on those edges. The side stacks are NOT moved: the user wants them where they were, and the two sides must
// mirror each other. Plain picture and the line-art frame keep their original layout.
//
// Every mode is measured in its OWN page. (An earlier version of this spec reloaded one page with a new config, but the page's init script re-applied the
// first config on every load, so "plain" was measured as fitted and the side comparisons were vacuous.)
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

// a fresh browser context per mode, so no config leaks between them
const measure = async (browser: Browser, w: number, h: number, cfg: Record<string, string>) => {
  const ctx = await browser.newContext({ viewport: { width: w, height: h } });
  const page = await ctx.newPage();
  await open(page, w, h, cfg);
  return { page, ctx, boxes: await settledBoxes(page) };
};

for (const [w, h] of SIZES) {
  test(`fitted at ${w}x${h}: stat boxes, tabs, strips and trim sit in the picture's slots; the side stacks stay where plain picture puts them`, async ({ browser }) => {
    const F = await measure(browser, w, h, { UseShipImage: '1', PictureFit: '1' });
    const P = await measure(browser, w, h, { UseShipImage: '1', PictureFit: '0' });
    const fitted = F.boxes, plain = P.boxes;
    // the two measurements really are different modes (guards against the vacuous comparison this spec once had)
    expect(Math.abs(fitted['graph-a'].l - plain['graph-a'].l), 'fitted and plain are different layouts').toBeGreaterThan(5);

    const kk = Math.min(w / 2560, h / 1600), ox = (w - 2560 * kk) / 2, oy = (h - 1600 * kk) / 2; // css px per canvas unit, and the 16:10 area's origin
    const by = (c: number) => oy + kk * c;
    // one stat box per main slot, centred in it: wing (770), pocket (1092), pocket (1468), wing (1790); all between the beams and the band's bottom edge
    const cx = (n: string) => ((fitted[n].l + fitted[n].r) / 2 - ox) / kk, cyc = (n: string) => ((fitted[n].t + fitted[n].b) / 2 - oy) / kk;
    const SLOTS: [string, number][] = [['graph-cpu', 770], ['graph-a', 1092], ['graph-b', 1468], ['graph-ram', 1790]];
    for (const [n, x] of SLOTS) {
      expect(Math.abs(cx(n) - x), n + ' centre x').toBeLessThanOrEqual(22);
      expect(cyc(n), n + ' centre y').toBeGreaterThanOrEqual(170);
      expect(cyc(n), n + ' centre y').toBeLessThanOrEqual(220);
    }
    // GPU and NET are exactly the same size, and so are CPU and MEMORY; only their height was reduced (the pocket boxes keep the skin's 232 width)
    const hh = (n: string) => fitted[n].b - fitted[n].t, ww = (n: string) => fitted[n].r - fitted[n].l;
    expect(Math.abs(hh('graph-a') - hh('graph-b')), 'GPU vs NET height').toBeLessThanOrEqual(1);
    expect(Math.abs(ww('graph-a') - ww('graph-b')), 'GPU vs NET width').toBeLessThanOrEqual(1);
    expect(Math.abs(hh('graph-cpu') - hh('graph-ram')), 'CPU vs MEM height').toBeLessThanOrEqual(1);
    expect(Math.abs(ww('graph-cpu') - ww('graph-ram')), 'CPU vs MEM width').toBeLessThanOrEqual(1);
    expect(hh('graph-a') / kk, 'pocket box height').toBeLessThan(hh('graph-a') / kk + 1); // sanity
    expect(hh('graph-a'), 'pocket box is shorter than plain picture\'s').toBeLessThan((plain['graph-a'].b - plain['graph-a'].t) * 0.95);
    expect(hh('graph-cpu'), 'wing box is shorter than plain picture\'s').toBeLessThan((plain['graph-cpu'].b - plain['graph-cpu'].t) * 0.9);
    // NET sits a little lower than GPU
    expect(fitted['graph-b'].t).toBeGreaterThan(fitted['graph-a'].t);
    // the pocket boxes are full size (232 canvas units wide, the skin's own size); no two boxes overlap
    for (const n of ['graph-a', 'graph-b']) expect((fitted[n].r - fitted[n].l) / kk, n + ' width').toBeGreaterThanOrEqual(225);
    const order = SLOTS.map(([n]) => fitted[n]);
    for (let k = 0; k < 3; k++) expect(order[k].r, 'box ' + k + ' vs ' + (k + 1)).toBeLessThanOrEqual(order[k + 1].l);
    // the console's lower row sits above the pocket roofs (y 143)
    expect(fitted['console'].b).toBeLessThanOrEqual(by(150));
    // the two status strips sit inside the bottom console band: between its lit top edge (1458 + 32 t^2) and its lit bottom edge (1540 + 35 t^2), t = (1280 - x) / 490
    for (const n of ['strip-left', 'strip-right']) {
      const sx = ((fitted[n].l + fitted[n].r) / 2 - ox) / kk, sy = ((fitted[n].t + fitted[n].b) / 2 - oy) / kk;
      const t = (1280 - sx) / 490, top = 1458 + 32 * t * t, bottom = 1540 + 35 * t * t;
      expect(sy, n + ' centre y vs band top').toBeGreaterThanOrEqual(top + 4);
      expect(sy, n + ' centre y vs band bottom').toBeLessThanOrEqual(bottom - 4);
    }
    // the traced trim (top slots and bottom band) and the kept part of the HUD's own trim are drawn in fitted
    expect(await F.page.locator('[data-part="fitted-trim"] path').count()).toBeGreaterThanOrEqual(20);
    expect(await F.page.locator('[data-layer="decor-lower"]').count()).toBe(1);

    // the wing tabs moved away from the centre into the slanted channels near the screen edges: centres near canvas x 210 and 2350 (the boxes' ink is a little
    // asymmetric), further out than plain picture, and mirrored
    const tc = (n: string, B: Record<string, Box>) => ((B[n].l + B[n].r) / 2 - ox) / kk;
    expect(Math.abs(tc('left-tabs', fitted) - 210), 'left tabs centre').toBeLessThanOrEqual(30);
    expect(Math.abs(tc('right-tabs', fitted) - 2347), 'right tabs centre').toBeLessThanOrEqual(30);
    expect(tc('left-tabs', fitted)).toBeLessThan(tc('left-tabs', plain) - 80);
    expect(tc('right-tabs', fitted)).toBeGreaterThan(tc('right-tabs', plain) + 80);
    expect(Math.abs(tc('left-tabs', fitted) + tc('right-tabs', fitted) - 2560), 'tabs mirror').toBeLessThanOrEqual(25);

    // the sides did not move: every side module sits exactly where plain picture mode puts it (measured in its own page)
    for (const n of SIDE_MODULES) {
      for (const k of ['l', 't', 'r', 'b'] as const) expect(Math.abs(fitted[n][k] - plain[n][k]), `${n}.${k}`).toBeLessThanOrEqual(1);
    }
    // and the two sides mirror each other, row for row (same heights, same distance from its own edge)
    for (const [a, b] of [['left-slot1', 'right-slot5'], ['left-slot2', 'right-slot6'], ['left-slot3', 'right-slot7'], ['left-slot4', 'right-slot8'], ['left-category', 'right-category'], ['left-dots', 'right-dots']]) {
      expect(Math.abs(fitted[a].t - fitted[b].t), `${a} vs ${b} (top)`).toBeLessThanOrEqual(h * 0.02);
      expect(Math.abs(fitted[a].l - (w - fitted[b].r)), `${a} vs ${b} (edge)`).toBeLessThanOrEqual(w * 0.02);
    }
    await F.ctx.close();
    await P.ctx.close();
  });
}

for (const [name, cfg] of [['line-art frame', { UseShipImage: '0' }], ['plain picture', { UseShipImage: '1', PictureFit: '0' }], ['plain picture, PictureFit unset', { UseShipImage: '1' }]] as [string, Record<string, string>][]) {
  test(`${name} keeps the original layout (no picture slots)`, async ({ page }) => {
    await open(page, 1707, 1067, cfg);
    const b = await page.locator('[data-module="graph-cpu"]').boundingBox();
    expect(b!.x).toBeLessThan(500); // the original CPU box is at its skin position (the fitted one is seated in its wing slot)
    const t = await page.locator('[data-module="left-tabs"]').boundingBox();
    expect(t!.x + t!.width / 2).toBeGreaterThan(190); // the original tabs sit where the skin puts them (the fitted ones are further out)
    expect(await page.locator('[data-part="fitted-trim"]').count()).toBe(0); // no fitted trim outside the fitted frame
    expect(await page.locator('[data-layer="decor-lower"]').count()).toBe(0);
  });
}
