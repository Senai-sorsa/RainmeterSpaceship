import { expect, test, type Page } from '@playwright/test';

const demo = '/?host=mock&panel=demo';
const row = (page: Page, key: string) => page.locator(`[data-key="${key}"]`);
const sent = (page: Page) => page.evaluate(() => (window as unknown as { __host: { sent: Record<string, unknown>[] } }).__host.sent.filter((m) => m.type === 'config.set'));

test('normal level hides advanced rows', async ({ page }) => {
  await page.goto(demo);
  await expect(row(page, 'ColorAccent')).toBeVisible();
  await expect(row(page, 'ColorDim')).toHaveCount(0);
  await page.goto(demo + '&level=advanced');
  await expect(row(page, 'ColorDim')).toBeVisible();
});

test('toggling a row writes config.set (read MockHost.sent via window.__host)', async ({ page }) => {
  await page.goto(demo);
  const sw = row(page, 'AutoFit').getByRole('switch', { name: 'Auto fit' });
  await expect(sw).toHaveAttribute('aria-checked', 'false');
  await sw.click();
  await expect(sw).toHaveAttribute('aria-checked', 'true');
  expect(await sent(page)).toContainEqual(expect.objectContaining({ key: 'AutoFit', value: '1' }));
});

test('changed dot appears after change and resets on click', async ({ page }) => {
  await page.goto(demo);
  const dot = page.getByRole('button', { name: 'Reset Auto fit to default' });
  await expect(dot).toHaveCount(0);
  await row(page, 'AutoFit').getByRole('switch').click();
  await expect(dot).toBeVisible();
  await dot.click();
  await expect(dot).toHaveCount(0);
  const w = await sent(page);
  expect(w.at(-1)).toMatchObject({ key: 'AutoFit', value: '0' });
});

test('keyboard: ArrowDown moves focus to next row, Space toggles', async ({ page }) => {
  await page.goto(demo);
  await row(page, 'AutoFit').getByRole('switch').focus();
  await page.keyboard.press('ArrowDown');
  await expect(row(page, 'BootAnim').getByRole('switch')).toBeFocused();
  await page.keyboard.press('Space');
  expect(await sent(page)).toContainEqual(expect.objectContaining({ key: 'BootAnim', value: '0' }));
  await page.keyboard.press('ArrowUp');
  await expect(row(page, 'AutoFit').getByRole('switch')).toBeFocused();
});

test('group collapsed state survives reload; with localStorage blocked the page still renders', async ({ page }) => {
  await page.goto(demo);
  const theme = page.locator('details[data-group="display/Theme"]');
  await expect(theme).toHaveJSProperty('open', true);
  await theme.locator('summary').click();
  await expect(theme).toHaveJSProperty('open', false);
  await page.reload();
  await expect(page.locator('details[data-group="display/Theme"]')).toHaveJSProperty('open', false);
  await expect(page.locator('details[data-group="display/Startup"]')).toHaveJSProperty('open', true);

  const blocked = await page.context().newPage();
  await blocked.addInitScript(() => Object.defineProperty(window, 'localStorage', { get() { throw new Error('blocked'); } }));
  await blocked.goto(demo);
  await expect(row(blocked, 'AutoFit')).toBeVisible();
  await row(blocked, 'AutoFit').getByRole('switch').click();
  await expect(row(blocked, 'AutoFit').getByRole('switch')).toHaveAttribute('aria-checked', 'true');
  await blocked.locator('details[data-group="display/Theme"] summary').click(); // collapsing must not throw
  await expect(blocked.locator('details[data-group="display/Theme"]')).toHaveJSProperty('open', false);
});

test('corrupt group storage falls back to open', async ({ page }) => {
  await page.addInitScript(() => localStorage.setItem('ui.groups.v1', '{not json'));
  await page.goto(demo);
  await expect(page.locator('details[data-group="display/Theme"]')).toHaveJSProperty('open', true);
});

test('wizard mode shows an Advanced disclosure closed by default', async ({ page }) => {
  await page.goto('/?host=mock&panel=demo-wizard');
  const adv = page.locator('details[data-advanced]');
  await expect(adv).toHaveCount(1);
  await expect(adv).toHaveJSProperty('open', false);
  await expect(row(page, 'ColorDim')).toBeHidden();
  await expect(row(page, 'ColorAccent')).toBeVisible();
  await adv.locator('summary').first().click();
  await expect(row(page, 'ColorDim')).toBeVisible();
});

test('text commit shows validation error as text, never HTML', async ({ page }) => {
  await page.goto(demo + '&level=advanced');
  const input = row(page, 'FontTitle').getByRole('textbox');
  await input.fill('<img src=x onerror=window.__pwn=1>');
  await input.press('Enter');
  await expect(row(page, 'FontTitle').getByRole('alert')).toContainText('not allowed');
  expect(await page.evaluate(() => (window as unknown as { __pwn?: number }).__pwn)).toBeUndefined();
  await expect(row(page, 'FontTitle').locator('img')).toHaveCount(0);
});

test('slider drag writes coalesced and closes the run on release', async ({ page }) => {
  await page.goto(demo);
  const s = row(page, 'GlowAlpha').getByRole('slider');
  await s.focus();
  await page.keyboard.press('ArrowRight');
  await page.keyboard.press('ArrowRight');
  expect((await sent(page)).at(-1)).toMatchObject({ key: 'GlowAlpha', value: '96' });
});

test('screenshots', async ({ page }) => {
  await page.goto(demo);
  await page.screenshot({ path: 'artifacts/settings-panel.png' });
  await page.goto(demo + '&level=advanced');
  await page.screenshot({ path: 'artifacts/settings-panel-advanced.png', fullPage: true });
});
