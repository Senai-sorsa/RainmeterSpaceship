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
  expect(await layers(page)).toEqual(['window_mask', 'glass_fx', 'scan', 'shade', 'hull', 'mist', 'corners']);
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
