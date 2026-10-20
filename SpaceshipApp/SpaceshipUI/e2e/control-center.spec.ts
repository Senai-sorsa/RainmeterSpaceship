import { expect, test, type Page } from '@playwright/test';
import { CATEGORIES } from '../src/settings/registry';

const cc = '/?host=mock&panel=control';
const row = (page: Page, key: string) => page.locator(`[data-key="${key}"]`);
const sent = (page: Page) => page.evaluate(() => (window as unknown as { __host: { sent: Record<string, unknown>[] } }).__host.sent.filter((m) => m.type === 'config.set'));
const search = (page: Page) => page.getByRole('searchbox', { name: 'Search settings' });

test('every registry category is listed in the rail', async ({ page }) => {
  await page.goto(cc);
  for (const c of CATEGORIES) await expect(page.getByRole('navigation', { name: 'Settings categories' }).getByRole('button', { name: c.label, exact: true })).toBeVisible();
  await page.screenshot({ path: 'artifacts/control-center-normal.png' });
});

test('search "scale" shows the Scale row and clicking the result expands its group', async ({ page }) => {
  await page.addInitScript(() => localStorage.setItem('ui.groups.v1', JSON.stringify({ 'display/Size and text': false }))); // start collapsed
  await page.goto(cc);
  await page.getByRole('button', { name: 'Layout', exact: true }).click();
  await search(page).fill('scale');
  const hit = page.getByRole('button', { name: /HUD size/ });
  await expect(hit).toContainText('Display / Size and text');
  await page.screenshot({ path: 'artifacts/control-center-search.png' });
  await hit.click();
  await expect(search(page)).toHaveValue('');
  await expect(page.locator('details[data-group="display/Size and text"]')).toHaveJSProperty('open', true);
  await expect(row(page, 'Scale')).toBeVisible();
});

test('Normal->Advanced reveals advanced rows and tags them', async ({ page }) => {
  await page.goto(cc);
  await expect(row(page, 'ColorDim')).toHaveCount(0);
  await page.getByRole('switch', { name: 'Advanced settings' }).click();
  await expect(row(page, 'ColorDim')).toBeVisible();
  await expect(row(page, 'ColorDim').getByText('adv')).toBeVisible();
  await expect(row(page, 'ColorAccent').getByText('adv')).toHaveCount(0);
  await page.screenshot({ path: 'artifacts/control-center-advanced.png' });
});

test('undo reverts the last change', async ({ page }) => {
  await page.goto(cc);
  const undo = page.getByRole('button', { name: 'Undo' });
  await expect(undo).toBeDisabled();
  const sw = row(page, 'AutoFit').getByRole('switch');
  await sw.click();
  await expect(sw).toHaveAttribute('aria-checked', 'true');
  await undo.click();
  await expect(sw).toHaveAttribute('aria-checked', 'false');
  await page.getByRole('button', { name: 'Redo' }).click();
  await expect(sw).toHaveAttribute('aria-checked', 'true');
  await page.keyboard.press('Control+z');
  await expect(sw).toHaveAttribute('aria-checked', 'false');
});

test('reset group resets only that group', async ({ page }) => {
  await page.goto(cc);
  await row(page, 'AutoFit').getByRole('switch').click();
  await row(page, 'ColorAccent').getByRole('textbox').fill('1,2,3');
  await page.keyboard.press('Enter');
  await expect(page.getByRole('button', { name: 'Reset Auto fit to default' })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Reset Accent colour to default' })).toBeVisible();
  await page.getByRole('button', { name: 'Reset group Size and text' }).click();
  await expect(row(page, 'AutoFit').getByRole('switch')).toHaveAttribute('aria-checked', 'false');
  await expect(page.getByRole('button', { name: 'Reset Auto fit to default' })).toHaveCount(0);
  await expect(page.getByRole('button', { name: 'Reset Accent colour to default' })).toBeVisible();
});

test('Esc clears the query first, then closes', async ({ page }) => {
  await page.addInitScript(() => localStorage.setItem('mockhost.v1', JSON.stringify({ config: {}, setupDone: true, aboutMe: '' })));
  await page.goto('/?host=mock');
  await page.getByRole('button', { name: 'Open Control Center' }).click();
  await page.keyboard.press('/');
  await expect(search(page)).toBeFocused();
  await page.keyboard.type('scale');
  await page.keyboard.press('Escape');
  await expect(search(page)).toHaveValue('');
  await expect(search(page)).toBeVisible();
  await page.keyboard.press('Escape');
  await expect(search(page)).toHaveCount(0);
});

test('a failed write (host failKeys via ?fail=Scale) shows an inline error and reverts', async ({ page }) => {
  await page.goto(cc + '&fail=Scale');
  const slider = row(page, 'Scale').getByRole('slider');
  await expect(slider).toHaveValue('0.67');
  await slider.fill('1.5');
  await expect(row(page, 'Scale').getByRole('alert')).toBeVisible();
  await expect(slider).toHaveValue('0.67');
  expect(await sent(page)).toContainEqual(expect.objectContaining({ key: 'Scale', value: '1.5' }));
});
