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
  await page.waitForTimeout(3000);
  type B = { __bloomBuiltBy?: Record<string, number> };
  const snap = () => page.evaluate(() => ({ ...(window as B).__bloomBuiltBy }));
  const a = await snap();
  await page.waitForTimeout(3000);
  const b = await snap();
  // the console, power rail and tabs redraw on a timer tick with equal ops: their tiles must not be rebuilt for that
  const still = Object.keys(b).filter((k) => ['cs', 'pw', 'tabs'].includes(k.split('#')[0]));
  expect(still.length).toBeGreaterThanOrEqual(3); // cs, pw and both sides' tabs
  expect(still.filter((k) => b[k] !== a[k])).toEqual([]);
});
