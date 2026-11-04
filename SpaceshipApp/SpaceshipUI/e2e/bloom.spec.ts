import { expect, test, type Page } from '@playwright/test';

// The quarter-res light canvas (tasks/hyperrealism-plan.md Task 3): on FULL the glow is one canvas, not blurred svg groups.
const boot = (config: Record<string, string> = {}) => (c: string) => {
  sessionStorage.setItem('cspace.booted', '1');
  localStorage.setItem('mockhost.v1', JSON.stringify({ config: JSON.parse(c), setupDone: true, aboutMe: '' }));
};
const open = async (page: Page, config: Record<string, string> = {}) => {
  await page.addInitScript(boot(), JSON.stringify(config));
  await page.goto('/?preview=1&module=all');
};
type W = { __bloomLast?: Record<string, { a: number; b: number; c: number; d: number; e: number; f: number }>; __bloomDraws?: number };
const lightSum = (page: Page) => page.locator('canvas.bloom-layer').evaluate((c: HTMLCanvasElement) => {
  const d = c.getContext('2d')!.getImageData(0, 0, c.width, c.height).data;
  let s = 0;
  for (let i = 3; i < d.length; i += 4) s += d[i];
  return s;
});
const keys = (page: Page) => page.evaluate(() => Object.keys((window as W).__bloomLast ?? {}).length);

test('FULL draws light on one canvas and no blurred svg groups', async ({ page }) => {
  await open(page);
  await expect(page.locator('canvas.bloom-layer[data-mode=canvas]')).toHaveCount(1);
  await expect.poll(() => lightSum(page)).toBeGreaterThan(0);
  await expect(page.locator('#hud g.bloom')).toHaveCount(0);
});

test('light follows a resize', async ({ page }) => {
  await open(page);
  await expect.poll(() => lightSum(page)).toBeGreaterThan(0);
  await page.setViewportSize({ width: 960, height: 600 });
  await expect.poll(() => page.evaluate(() => {
    const last = (window as W).__bloomLast ?? {};
    const els = [...document.querySelectorAll<SVGGElement>('[data-bloom-anchor]')];
    return els.length > 0 && els.every((g) => {
      const m = g.getScreenCTM()!, l = last[g.dataset.bloomKey!];
      return !!l && Math.abs(l.a - m.a) < 1e-6 && Math.abs(l.e - m.e) < 1e-3 && Math.abs(l.f - m.f) < 1e-3;
    });
  })).toBe(true);
  const c = await page.locator('canvas.bloom-layer').evaluate((el: HTMLCanvasElement) => [el.width, el.height]);
  expect(c).toEqual([240, 150]);
});

test('a hidden module\'s light goes away', async ({ page }) => {
  await open(page);
  await expect.poll(() => keys(page)).toBeGreaterThan(3);
  const before = await keys(page);
  await page.locator('[data-module=console] [data-hit]').nth(4).dispatchEvent('click'); // the fifth console tab, OFF
  await expect.poll(() => keys(page)).toBeLessThan(before);
  // every remaining anchor is still mounted: no stale light for an unmounted module
  expect(await page.evaluate(() => Object.keys((window as W).__bloomLast ?? {}).every((k) => document.querySelector(`[data-bloom-key="${k}"]`)))).toBe(true);
});

test('LITE clears the canvas; FULL draws again', async ({ page }) => {
  await open(page, { PerfOverride: '1' });
  await expect(page.locator('canvas.bloom-layer')).toHaveAttribute('data-mode', 'off');
  expect(await lightSum(page)).toBe(0);
  await expect(page.locator('#hud g.bloom')).toHaveCount(0);
});

test('fonts ready triggers a redraw', async ({ page }) => {
  await open(page);
  await page.evaluate(() => document.fonts.ready);
  await expect.poll(() => page.evaluate(() => (window as W).__bloomDraws ?? 0)).toBeGreaterThanOrEqual(2);
});

test('idle light is not re-blurred when nothing changed', async ({ page }) => {
  await open(page);
  await page.evaluate(() => document.fonts.ready); // a late web-font load reflows the text and legitimately rebuilds every tile once; wait for it (load-sensitivity, not a regression)
  type B = { __bloomBuiltBy?: Record<string, number> };
  const snap = () => page.evaluate(() => ({ ...(window as B).__bloomBuiltBy }));
  // wait for the state (the three timer-driven anchors have built their tiles), not for a fixed time
  const timed = (m: Record<string, number>) => Object.keys(m).filter((k) => ['cs', 'pw', 'tabs'].includes(k.split('#')[0]));
  await expect.poll(async () => timed(await snap()).length).toBeGreaterThanOrEqual(3);
  const sig = async () => { const m = await snap(); return JSON.stringify(timed(m).sort().map((k) => [k, m[k]])); };
  let prev = await sig();
  await expect.poll(async () => { const cur = await sig(); const same = cur === prev; prev = cur; return same; }, { intervals: [400] }).toBe(true);
  const a = await snap();
  await page.waitForTimeout(3000);
  const b = await snap();
  // the console, power rail and tabs redraw on a timer tick with equal ops: their tiles must not be rebuilt for that
  const still = Object.keys(b).filter((k) => ['cs', 'pw', 'tabs'].includes(k.split('#')[0]));
  expect(still.length).toBeGreaterThanOrEqual(3); // cs, pw and both sides' tabs
  expect(still.filter((k) => b[k] !== a[k])).toEqual([]);
});

test('glass layer only on FULL with LensFx', async ({ page }) => {
  await open(page);
  await expect(page.locator('canvas.glass-layer')).toHaveCount(1);
  await page.close();
});
test('no glass layer with LensFx=0', async ({ page }) => {
  await open(page, { LensFx: '0' });
  await expect(page.locator('canvas.bloom-layer')).toHaveCount(1);
  await expect(page.locator('canvas.glass-layer')).toHaveCount(0);
});
test('no glass layer on LITE', async ({ page }) => {
  await open(page, { PerfOverride: '1' });
  await expect(page.locator('canvas.bloom-layer')).toHaveCount(1);
  await expect(page.locator('canvas.glass-layer')).toHaveCount(0);
});

// Task 13: which of the new layers each tier gets. FULL: light + glass + grain; LITE: grain only (the light canvas stays
// mounted but draws nothing); LOW and STEALTH: none.
for (const [tier, want] of [['0', { light: true, glass: true, grain: true }], ['1', { light: false, glass: false, grain: true }],
  ['2', { light: false, glass: false, grain: false }], ['3', { light: false, glass: false, grain: false }]] as const) {
  test(`tier ${tier} layers`, async ({ page }) => {
    await open(page, { PerfOverride: tier });
    await expect(page.locator('canvas.bloom-layer')).toHaveAttribute('data-mode', want.light ? 'canvas' : 'off');
    await expect(page.locator('canvas.glass-layer')).toHaveCount(want.glass ? 1 : 0);
    await expect(page.locator('.frame [data-layer=grain]')).toHaveCount(want.grain ? 1 : 0);
  });
}

test('the glass repaints at most 4 times a second, at half the light canvas size', async ({ page }) => {
  await page.addInitScript(boot(), '{}');
  await page.goto('/?preview=1&module=all&audio=demo');
  await expect.poll(() => page.evaluate(() => (window as { __glassDraws?: number }).__glassDraws ?? 0)).toBeGreaterThan(0);
  const a = await page.evaluate(() => (window as { __glassDraws?: number }).__glassDraws ?? 0);
  await page.waitForTimeout(3000);
  const b = await page.evaluate(() => (window as { __glassDraws?: number }).__glassDraws ?? 0);
  expect(b - a).toBeLessThanOrEqual(13);
  const [lw, gw] = await page.evaluate(() => [document.querySelector<HTMLCanvasElement>('canvas.bloom-layer')!.width, document.querySelector<HTMLCanvasElement>('canvas.glass-layer')!.width]);
  expect(gw).toBe(Math.ceil(lw / 2));
});

test('a fast anchor (the audio ring with music) is re-blurred at most 10 times a second', async ({ page }) => {
  await page.addInitScript(boot(), '{}');
  await page.goto('/?preview=1&module=all&audio=demo');
  type B = { __bloomBuiltBy?: Record<string, number> };
  const au = () => page.evaluate(() => Object.entries((window as B).__bloomBuiltBy ?? {}).filter(([k]) => k.startsWith('au#')).reduce((s, [, n]) => s + n, 0));
  await expect.poll(au).toBeGreaterThan(0);
  const a = await au();
  await page.waitForTimeout(3000);
  expect(await au() - a).toBeLessThanOrEqual(33);
});

// K8 depth haze: the hologram out in the windscreen (target, hud, sphere) gets the softer far tile; the dash does not.
type F = { __bloomFar?: Record<string, boolean> };
const farKeys = (page: Page) => page.evaluate(() => Object.entries((window as F).__bloomFar ?? {}).filter(([, f]) => f).map(([k]) => k.split('#')[0]).sort());
// with JARVIS on (module=all) the orb takes the centre and the sphere is not drawn: the sphere shows with JARVIS off
test('depth haze softens only the hologram light', async ({ page }) => {
  await page.addInitScript(boot(), JSON.stringify({}));
  await page.goto('/?preview=1&module=center,top');
  await expect.poll(() => farKeys(page)).toEqual(['sphere']);
  // the dash light on screen is built too, and stays near (tiles off the 1280x720 view are never built)
  await expect.poll(() => page.evaluate(() => Object.values((window as F).__bloomFar ?? {}).filter((f) => !f).length)).toBeGreaterThan(0);
  expect(await farKeys(page)).toEqual(['sphere']);
});
test('DepthHaze=0 builds every tile near', async ({ page }) => {
  await page.addInitScript(boot(), JSON.stringify({ DepthHaze: '0' }));
  await page.goto('/?preview=1&module=center,top');
  await expect.poll(() => page.evaluate(() => Object.keys((window as F).__bloomFar ?? {}).some((k) => k.startsWith('sphere#')))).toBe(true);
  expect(await farKeys(page)).toEqual([]);
});

// UI-handoff 12 #29: the anchors read getScreenCTM (a forced layout) only when their position can have changed - the
// viewport, the viewBox or an ancestor's transform - not on every timer redraw (it was ~65 reads a second while idle).
test('an idle HUD does not re-read the screen CTM on every redraw, and a resize still moves the light', async ({ page }) => {
  await page.addInitScript(() => {
    const orig = SVGGraphicsElement.prototype.getScreenCTM;
    (window as unknown as { __ctmReads: number }).__ctmReads = 0;
    SVGGraphicsElement.prototype.getScreenCTM = function () { (window as unknown as { __ctmReads: number }).__ctmReads++; return orig.call(this); };
  });
  await open(page);
  await expect.poll(() => lightSum(page)).toBeGreaterThan(0);
  await page.waitForTimeout(1000);
  const reads = () => page.evaluate(() => (window as unknown as { __ctmReads: number }).__ctmReads);
  const r0 = await reads();
  await page.waitForTimeout(3000); // the preview metrics redraw every module twice a second
  expect(await reads() - r0).toBeLessThan(10);
  // the cache assumes no light anchor moves by a CSS animation (placeKey reads attributes only)
  expect(await page.locator('.scan [data-bloom-anchor]').count()).toBe(0);
  const before = await page.evaluate(() => JSON.stringify((window as W).__bloomLast));
  await page.setViewportSize({ width: 1100, height: 700 });
  await expect.poll(() => page.evaluate(() => JSON.stringify((window as W).__bloomLast))).not.toBe(before);
});
