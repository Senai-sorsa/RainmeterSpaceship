import { expect, test, type Page } from '@playwright/test';
import { regionsOf } from '../src/host/hitRegions';

// Regression matrix from the live test (2026-11-04): every frame mode at every window size, display scale and tier must
//  - throw nothing and log no errors (a favicon 404 on the dev server aside),
//  - draw the frame in exactly the area the modules use (the 1.5x frame bug: the frame followed the HUD-size value),
//  - keep the HUD's click-through map within the host's 64 regions with a panel open (the two-panels-unclickable bug),
//  - stay robust to garbage HUD-size values.
const MODES: Record<string, Record<string, string>> = {
  rendered: { UseShipImage: '0', PictureFit: '0' },
  picture: { UseShipImage: '1', PictureFit: '0' },
  fitted: { UseShipImage: '1', PictureFit: '1' },
  none: { FrameOff: '1' },
};
const SIZES: [number, number][] = [[1280, 800], [1707, 1067], [1920, 1080], [2560, 1600], [3440, 1440]];

const boot = async (page: Page, cfg: Record<string, string>, query = '') => {
  const problems: string[] = [];
  page.on('pageerror', (e) => problems.push('pageerror ' + e));
  page.on('console', (m) => { if (m.type() === 'error' && !/favicon|404/.test(m.text())) problems.push('console ' + m.text()); });
  await page.addInitScript((c) => {
    sessionStorage.setItem('cspace.booted', '1');
    localStorage.setItem('mockhost.v1', JSON.stringify({ config: c, setupDone: true, aboutMe: '' }));
  }, cfg);
  await page.goto('/?preview=1&module=all' + query);
  await page.waitForSelector('#hud');
  await page.waitForTimeout(700);
  return problems;
};

const areas = (page: Page) => page.evaluate(() => {
  const svg = document.querySelector('#hud') as SVGSVGElement, vb = svg.viewBox.baseVal, m = svg.getScreenCTM()!;
  const f = document.querySelector('.frame')?.getBoundingClientRect();
  return { x: m.e, y: m.f, w: vb.width * m.a, h: vb.height * m.d, frame: f ? { x: f.left, y: f.top, w: f.width } : null };
});

for (const [mode, cfg] of Object.entries(MODES)) {
  for (const [w, h] of SIZES) {
    test(`${mode} at ${w}x${h}: no errors, and the frame covers the modules' area`, async ({ page }) => {
      await page.setViewportSize({ width: w, height: h });
      const problems = await boot(page, cfg);
      expect(problems).toEqual([]);
      const a = await areas(page);
      if (mode === 'none') { expect(a.frame).toBeNull(); return; }
      expect(a.frame).not.toBeNull();
      expect(Math.abs(a.frame!.w - a.w)).toBeLessThanOrEqual(a.w * 0.01 + 1);
      expect(Math.abs(a.frame!.x - a.x)).toBeLessThanOrEqual(2);
      expect(Math.abs(a.frame!.y - a.y)).toBeLessThanOrEqual(2);
    });
  }
}

for (const mode of ['rendered', 'picture', 'fitted']) {
  for (const scale of ['0.4', '0.67', '1', '2.5', 'abc', '-3', '1e9']) {
    test(`${mode} frame ignores the HUD-size value (${scale}) and never throws`, async ({ page }) => {
      await page.setViewportSize({ width: 1707, height: 1067 });
      const problems = await boot(page, { ...MODES[mode], Scale: scale });
      expect(problems).toEqual([]);
      const a = await areas(page);
      if (Number.isFinite(Number(scale)) && Number(scale) > 0 && Number(scale) < 100) expect(Math.abs(a.frame!.w - a.w)).toBeLessThanOrEqual(a.w * 0.01 + 1);
    });
  }
}

for (const mode of ['rendered', 'picture', 'fitted']) {
  for (const tier of ['0', '1', '2', '3']) {
    test(`${mode} on tier ${tier}: no errors`, async ({ page }) => {
      await page.setViewportSize({ width: 1707, height: 1067 });
      expect(await boot(page, { ...MODES[mode], PerfOverride: tier })).toEqual([]);
    });
  }
}

for (const mode of ['rendered', 'picture', 'fitted']) {
  test(`${mode}: with the CARGO drawer open the click map stays within 64 regions and covers the drawer`, async ({ page }) => {
    await page.setViewportSize({ width: 1707, height: 1067 });
    const problems = await boot(page, MODES[mode], '&drawer=1');
    expect(problems).toEqual([]);
    // the host only sends the click map from WebView2, so run the page's real [data-hit] boxes through the production function
    const boxes = await page.evaluate(() => [...document.querySelectorAll('[data-hit]')].map((e) => { const b = e.getBoundingClientRect(); return { left: b.left, top: b.top, width: b.width, height: b.height }; }));
    const rects = regionsOf(boxes, 1);
    expect(rects.length).toBeGreaterThan(0);
    expect(rects.length).toBeLessThanOrEqual(64);
    const drawer = await page.locator('[data-module="drawer"]').first().boundingBox();
    expect(drawer).not.toBeNull();
    const cx = drawer!.x + drawer!.width / 2, cy = drawer!.y + drawer!.height / 2; // device px at DPR 1 = css px
    expect(rects.some(([x, y, w, hh]) => cx >= x && cx <= x + w && cy >= y && cy <= y + hh), 'a region covers the drawer centre').toBe(true);
  });
}

// Windows display scale: the page sees CSS px, so one window size at several device scales must give the same fit
for (const dpr of [1, 1.25, 1.5, 2]) {
  test.describe(`display scale ${dpr * 100}%`, () => {
    test.use({ deviceScaleFactor: dpr });
    test(`fitted frame covers the modules' area at ${dpr}x`, async ({ page }) => {
      await page.setViewportSize({ width: 1707, height: 1067 });
      const problems = await boot(page, MODES.fitted);
      expect(problems).toEqual([]);
      const a = await areas(page);
      expect(Math.abs(a.frame!.w - a.w)).toBeLessThanOrEqual(a.w * 0.01 + 1);
    });
  });
}

test('each frame mode keeps its own layout: only fitted re-seats the top boxes', async ({ browser }) => {
  const xs: Record<string, number> = {};
  for (const [mode, cfg] of Object.entries(MODES)) {
    const ctx = await browser.newContext({ viewport: { width: 1707, height: 1067 } });
    const page = await ctx.newPage();
    expect(await boot(page, cfg)).toEqual([]);
    xs[mode] = (await page.locator('[data-module="graph-cpu"]').boundingBox())!.x;
    await ctx.close();
  }
  expect(Math.abs(xs.picture - xs.rendered)).toBeLessThanOrEqual(1);
  expect(Math.abs(xs.none - xs.rendered)).toBeLessThanOrEqual(1);
  expect(xs.fitted).toBeGreaterThan(xs.rendered + 60); // seated into the picture's band
});
