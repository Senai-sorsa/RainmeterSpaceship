import { expect, test } from '@playwright/test';
import { readFileSync } from 'node:fs';
const layout = JSON.parse(readFileSync('src/generated/layout.json', 'utf8'));
const vars = JSON.parse(readFileSync('src/generated/settings.json', 'utf8')).variables;

test('static HUD: skin theme applied, icons drawn, no zone outlines by default', async ({ page }) => {
  await page.goto('/?host=mock');
  await expect(page.locator('g.zone')).toHaveCount(layout.zones.length);
  await expect(page.locator('[data-icon]')).toHaveCount(4);
  await expect(page.locator('#debug-overlay')).toHaveCount(0);
  const [r, g, b] = vars.ColorAccent.split(',');
  // root cause regression: the resolved --accent AND the painted icon stroke must be the settings colour
  expect(await page.evaluate(() => getComputedStyle(document.documentElement).getPropertyValue('--accent').trim())).toBe(`rgb(${r},${g},${b})`);
  const stroke = await page.locator('[data-icon] path').nth(1).evaluate((e) => getComputedStyle(e).stroke);
  expect(stroke).toBe(`rgb(${r}, ${g}, ${b})`);
  await page.screenshot({ path: 'artifacts/hud-static.png' });
});

test('?debug=1 shows the labelled zone overlay', async ({ page }) => {
  await page.goto('/?host=mock&debug=1');
  await expect(page.locator('#debug-overlay')).toHaveCount(1);
});

test('tokens.css defaults are the skin defaults (== Settings.inc)', async ({ request }) => {
  const css = await (await request.get('/src/tokens.css?direct')).text();
  const want = { accent: 'ColorAccent', dim: 'ColorDim', text: 'ColorText', warn: 'ColorWarn', alert: 'ColorAlert', good: 'ColorGood', hi: 'ColorHighlight', white: 'ColorWhite' };
  for (const [n, k] of Object.entries(want)) expect(css).toContain(`--${n}: rgb(${vars[k]});`);
});
