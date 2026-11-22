import { expect, test } from '@playwright/test';

const SETUP_DONE = () => localStorage.setItem('mockhost.v1', JSON.stringify({ config: {}, setupDone: true, aboutMe: '' }));
const SETUP_DONE_NO_CAPTIONS = () => localStorage.setItem('mockhost.v1', JSON.stringify({ config: { CaptionStyle: '0' }, setupDone: true, aboutMe: '' }));

test('mission clock is off by default', async ({ page }) => {
  await page.addInitScript(SETUP_DONE);
  await page.goto('/?host=mock');
  await expect(page.locator('[data-module="clock"]')).toHaveCount(0);
});

test('?module=clock gives only the cut title a hover row, and it shows its full text', async ({ page }) => {
  await page.addInitScript(SETUP_DONE);
  await page.goto('/?host=mock&module=clock');
  await expect(page.locator('[data-module="clock"] [data-row]')).toHaveCount(1);
  await page.screenshot({ path: 'artifacts/mission-clock.png' });

  await page.locator('[data-row="2"]').hover();
  await expect(page.locator('#hud-caption')).toHaveText(/^Dentist appointment and a long title\s+[A-Z]{3} \d{2} [A-Z]{3}\s+\d{2}:\d{2}\s+Personal$/);
});

test('a short title shows no caption', async ({ page }) => {
  await page.addInitScript(SETUP_DONE);
  await page.goto('/?host=mock&module=clock');
  // the zone's own click target, near its top edge (above the rows): no row tip there
  await page.locator('[data-module="clock"] rect[aria-label="Google Calendar"]').hover({ position: { x: 20, y: 3 }, force: true });
  await expect(page.locator('#hud-caption')).toHaveCount(0);
});

test('CaptionStyle=0 uses native tooltips and no HUD caption', async ({ page }) => {
  await page.addInitScript(SETUP_DONE_NO_CAPTIONS);
  await page.goto('/?host=mock&module=clock');
  await expect(page.locator('[data-module="clock"] [data-row="2"] title')).toHaveCount(1);
  await page.locator('[data-row="2"]').hover();
  await expect(page.locator('#hud-caption')).toHaveCount(0);
});
