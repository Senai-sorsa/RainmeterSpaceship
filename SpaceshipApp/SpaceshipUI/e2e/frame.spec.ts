import { expect, test, type Page } from '@playwright/test';

const done = () => localStorage.getItem('mockhost.v1') || localStorage.setItem('mockhost.v1', JSON.stringify({ config: {}, setupDone: true, aboutMe: '' }));
const layers = (page: Page) => page.locator('.frame [data-layer]').evaluateAll((els) => els.map((e) => (e as HTMLElement).dataset.layer));
const choose = async (page: Page, style: string) => {
  await page.getByRole('button', { name: 'Open Control Center' }).click();
  await page.getByRole('button', { name: 'Display', exact: true }).click();
  await page.getByRole('combobox', { name: 'Cockpit frame' }).selectOption(style);
  await page.getByRole('button', { name: 'Close Control Center' }).click();
};

test.beforeEach(({ page }) => page.addInitScript(done));

test('rendered has hull and corners; picture has the ship image and no corners; none has no frame layers', async ({ page }) => {
  await page.goto('/?host=mock');
  // polled: on a cold dev server the first render can land after a one-shot read
  await expect.poll(() => layers(page)).toEqual(['glass_fx', 'scan', 'shade', 'hull', 'mist', 'corners', 'sheen', 'bounce', 'spill', 'orblight', 'vignette', 'trimspill', 'grain']); // rendered gets the lighting finish (spill: K6, FULL and LITE; orblight: FULL; grain: H2c)
  await page.screenshot({ path: 'artifacts/frame-rendered.png' });
  await choose(page, 'picture');
  expect(await layers(page)).toEqual(['glass_pic', 'glass_fx_pic', 'scan_pic', 'shade', 'ship', 'mist_pic']);
  await page.screenshot({ path: 'artifacts/frame-picture.png' });
  await choose(page, 'none');
  await expect(page.locator('.frame')).toHaveCount(0);
  await page.screenshot({ path: 'artifacts/frame-none.png' });
});

test('the chosen frame survives a reload and every layer image loads', async ({ page }) => {
  await page.goto('/?host=mock');
  await choose(page, 'picture');
  await page.goto('/?host=mock');
  await expect(page.locator('.frame')).toHaveAttribute('data-frame', 'picture');
  const urls = await page.locator('.frame [data-layer]').evaluateAll((els) => els.map((e) => getComputedStyle(e as HTMLElement).backgroundImage + getComputedStyle(e as HTMLElement).maskImage));
  for (const u of urls) {
    const m = /url\("?([^")]+)"?\)/.exec(u);
    expect(m, u).not.toBeNull();
    expect((await page.request.get(m![1])).status()).toBe(200);
  }
});

// UI-handoff 12 #9: the orb's light on the hull follows JARVIS's state (listening or speaking), by opacity only; FULL only
const orb = (page: Page) => page.locator('.frame [data-layer=orblight]');
const cfg = (c: Record<string, string>) => (j: string) => localStorage.setItem('mockhost.v1', JSON.stringify({ config: JSON.parse(j), setupDone: true, aboutMe: '' }));
test('the orb lights the hull while JARVIS speaks, not while idle', async ({ page }) => {
  await page.goto('/?preview=1&module=all&jarvis=speaking');
  await expect(orb(page)).toHaveAttribute('data-on', '1');
  await expect.poll(() => orb(page).evaluate((e) => Number(getComputedStyle(e).opacity))).toBeGreaterThan(0.5);
  await page.goto('/?preview=1&module=all&jarvis=idle');
  await expect(orb(page)).toHaveAttribute('data-on', '0');
  await expect.poll(() => orb(page).evaluate((e) => Number(getComputedStyle(e).opacity))).toBe(0);
});
test('no orb light on LITE or with StateLight=0', async ({ page }) => {
  await page.addInitScript(cfg({}), JSON.stringify({ PerfOverride: '1' }));
  await page.goto('/?preview=1&module=all&jarvis=speaking');
  await expect(page.locator('.frame [data-layer=spill]')).toHaveCount(1);
  await expect(orb(page)).toHaveCount(0);
});
test('StateLight=0 drops the orb light', async ({ page }) => {
  await page.addInitScript(cfg({}), JSON.stringify({ StateLight: '0' }));
  await page.goto('/?preview=1&module=all&jarvis=speaking');
  await expect(page.locator('.frame [data-layer=spill]')).toHaveCount(1);
  await expect(orb(page)).toHaveCount(0);
});

// UI-handoff 12 #21: the lens (grain, glass) settles last - off while the start-up sequence plays, then fades in
test('grain and glass wait for the boot sequence, then fade in', async ({ page }) => {
  await page.goto('/?preview=1&module=all,boot'); // a fresh tab: the boot plays (no cspace.booted)
  const op = (sel: string) => page.locator(sel).evaluate((e) => Number(getComputedStyle(e).opacity));
  await expect(page.locator('.frame [data-layer=grain]')).toHaveAttribute('data-settled', '0');
  expect(await op('.frame [data-layer=grain]')).toBe(0);
  await expect(page.locator('.frame [data-layer=grain]')).toHaveAttribute('data-settled', '1', { timeout: 15_000 });
  await expect.poll(() => op('.frame [data-layer=grain]'), { timeout: 5_000 }).toBeGreaterThan(0);
  await expect.poll(() => op('canvas.glass-layer'), { timeout: 5_000 }).toBe(1);
});
test('reduced motion: the orb light and the lens settle do not animate', async ({ page }) => {
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await page.addInitScript(() => sessionStorage.setItem('cspace.booted', '1'));
  await page.goto('/?preview=1&module=all&jarvis=speaking');
  const dur = (sel: string) => page.locator(sel).evaluate((e) => getComputedStyle(e).transitionDuration);
  await expect(page.locator('.frame [data-layer=grain]')).toHaveAttribute('data-settled', '1');
  expect(await dur('.frame [data-layer=grain]')).toBe('0s');
  expect(await dur('canvas.glass-layer')).toBe('0s');
  expect(await dur('.frame [data-layer=orblight]')).toBe('0s');
});
