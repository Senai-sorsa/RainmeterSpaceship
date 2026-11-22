import { expect, test } from '@playwright/test';

test('? on a row with a guide section opens it; Esc closes only the help', async ({ page }) => {
  await page.goto('/?host=mock&panel=control');
  await page.getByRole('button', { name: 'Display', exact: true }).click();
  await page.getByRole('button', { name: 'Help for HUD size' }).click();
  const help = page.getByRole('dialog', { name: 'Help' });
  await expect(help).toHaveAttribute('data-section', 'look');
  await expect(help.locator('.help-title')).toHaveText('Look');
  await page.screenshot({ path: 'artifacts/help.png' });
  await page.keyboard.press('Escape');
  await expect(help).toHaveCount(0);
  await expect(page.getByRole('dialog', { name: 'Control Center' })).toBeVisible();
});

test('rows without a guide section have no ? button', async ({ page }) => {
  await page.goto('/?host=mock&panel=control');
  await page.getByRole('button', { name: 'Display', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Help for HUD size' })).toHaveCount(1);
  await expect(page.getByRole('button', { name: 'Help for Glow width' })).toHaveCount(0);
});
