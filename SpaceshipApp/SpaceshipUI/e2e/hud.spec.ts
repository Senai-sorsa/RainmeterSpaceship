import { expect, test } from '@playwright/test';
import { readFileSync } from 'node:fs';
const layout = JSON.parse(readFileSync('src/generated/layout.json', 'utf8'));

test('static HUD draws every zone', async ({ page }) => {
  await page.goto('/?host=mock');
  await expect(page.locator('g.zone')).toHaveCount(layout.zones.length);
  await expect(page.locator('[data-icon]')).toHaveCount(4);
  await page.screenshot({ path: 'artifacts/hud-static.png' });
});
