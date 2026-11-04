import { expect, test } from '@playwright/test';

// Live test: the HUD must not be highlightable (and shows the arrow, not the I-beam); the Control Center always allows copying; AllowCopy opens the HUD up.
const boot = (cfg: Record<string, string>) => async ({ page }: { page: import('@playwright/test').Page }) => {
  await page.addInitScript((c) => {
    sessionStorage.setItem('cspace.booted', '1');
    localStorage.setItem('mockhost.v1', JSON.stringify({ config: c, setupDone: true, aboutMe: '' }));
  }, cfg);
};
const selected = (page: import('@playwright/test').Page) => page.evaluate(() => String(getSelection()).length);

test.describe('AllowCopy off (default)', () => {
  test.beforeEach(boot({}));
  test('HUD text cannot be selected and the cursor is the arrow', async ({ page }) => {
    await page.goto('/?preview=1&module=all');
    await page.waitForSelector('[data-module="panel-left"]');
    await page.mouse.dblclick(960, 300);
    await page.keyboard.press('Control+a');
    expect(await selected(page)).toBe(0);
    expect(await page.evaluate(() => getComputedStyle(document.querySelector('svg text')!).cursor)).toBe('default');
  });
  test('the Control Center still allows copying', async ({ page }) => {
    await page.goto('/?preview=1&module=all');
    await page.getByRole('button', { name: 'Open Control Center' }).click({ force: true });
    await page.waitForSelector('.cc');
    await page.keyboard.press('Control+a');
    expect(await selected(page)).toBeGreaterThan(0);
  });
});

test.describe('AllowCopy on', () => {
  test.beforeEach(boot({ AllowCopy: '1' }));
  test('HUD text can be selected', async ({ page }) => {
    await page.goto('/?preview=1&module=all');
    await page.waitForSelector('[data-module="panel-left"]');
    await page.keyboard.press('Control+a');
    expect(await selected(page)).toBeGreaterThan(0);
  });
});
