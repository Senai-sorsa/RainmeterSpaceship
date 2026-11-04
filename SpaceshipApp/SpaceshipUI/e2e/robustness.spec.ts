import { expect, test } from '@playwright/test';

// Random-logic and error cases from the live test (U11): garbage settings and rapid panel toggling must never throw or blank the HUD.
const seed = (config: Record<string, string>) => (c: Record<string, string>) => {
  sessionStorage.setItem('cspace.booted', '1');
  localStorage.setItem('mockhost.v1', JSON.stringify({ config: c, setupDone: true, aboutMe: '' }));
};

const BAD: Record<string, string>[] = [
  { Scale: 'abc' }, { Scale: '-5' }, { Scale: '1e9' }, { Scale: '0' }, { PerfOverride: '99' }, { PerfOverride: '-7' }, { HullRender: 'x' },
  { ColorAccent: 'zzz' }, { ColorAccent: '300,-5,1e3' }, { ColorDim: '' }, { FrameBrightness: '-50' }, { FrameBrightness: '9999' },
  { GlowAlpha: 'NaN' }, { GlowWidth: 'Infinity' }, { UseShipImage: '1', FrameOff: '1' }, { ShipImage: '../../etc/passwd' }, { BloomEngine: 'nope' },
];

for (const cfg of BAD) {
  test(`bad config ${JSON.stringify(cfg)} does not throw and the HUD still draws`, async ({ page }) => {
    const errors: string[] = [];
    page.on('pageerror', (e) => errors.push(String(e)));
    await page.addInitScript(seed(cfg), cfg);
    await page.goto('/?preview=1&module=all');
    await page.waitForSelector('#hud');
    await page.waitForTimeout(600);
    expect(errors).toEqual([]);
    expect(await page.locator('#hud g[data-module]').count()).toBeGreaterThan(5);
  });
}

test('rapid CARGO open/close and a resize in between never throws', async ({ page }) => {
  const errors: string[] = [];
  page.on('pageerror', (e) => errors.push(String(e)));
  await page.addInitScript(seed({}), {});
  await page.goto('/?preview=1&module=all');
  await page.waitForSelector('#hud');
  const cargo = page.getByText('CARGO', { exact: true }).first();
  for (let i = 0; i < 12; i++) {
    await cargo.click({ force: true, timeout: 2000 }).catch(() => {});
    if (i === 5) await page.setViewportSize({ width: 1280, height: 800 });
  }
  await page.keyboard.press('Escape');
  await page.waitForTimeout(400);
  expect(errors).toEqual([]);
  await expect(page.locator('#hud')).toBeVisible();
});
