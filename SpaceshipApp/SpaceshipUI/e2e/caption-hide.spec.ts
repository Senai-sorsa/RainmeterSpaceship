import { expect, test } from '@playwright/test';

// Live test: a hover caption must disappear as soon as the pointer leaves what it describes, not after its 6 s timer.
const open = async (page: import('@playwright/test').Page) => {
  await page.setViewportSize({ width: 1707, height: 1067 });
  await page.addInitScript(() => {
    sessionStorage.setItem('cspace.booted', '1');
    localStorage.setItem('mockhost.v1', JSON.stringify({ config: {}, setupDone: true, aboutMe: '' }));
  });
  await page.goto('/?preview=1&module=all');
  await page.waitForSelector('[data-tip]');
};

const centreOfFirstTip = async (page: import('@playwright/test').Page) => {
  const box = await page.locator('[data-tip]').first().boundingBox();
  return { x: box!.x + box!.width / 2, y: box!.y + box!.height / 2 };
};

test('the caption shows on hover and hides at once when the pointer moves to empty space', async ({ page }) => {
  await open(page);
  const c = await centreOfFirstTip(page);
  await page.mouse.move(c.x, c.y);
  await expect(page.locator('#hud-caption')).toBeVisible();
  await page.mouse.move(850, 700); // the open windscreen: nothing there carries a tip
  await expect(page.locator('#hud-caption')).toHaveCount(0, { timeout: 400 });
});

test('the caption hides at once when the pointer leaves the window', async ({ page }) => {
  await open(page);
  const c = await centreOfFirstTip(page);
  await page.mouse.move(c.x, c.y);
  await expect(page.locator('#hud-caption')).toBeVisible();
  // what the browser sends when the pointer leaves the page (e.g. onto the click-through desktop): pointerout from the element, no related target
  await page.evaluate(() => {
    const el = document.querySelector('[data-tip]')!;
    el.dispatchEvent(new PointerEvent('pointerout', { bubbles: true, relatedTarget: null }));
  });
  await expect(page.locator('#hud-caption')).toHaveCount(0, { timeout: 400 });
});

test('moving inside the same tipped element keeps its caption (no flicker)', async ({ page }) => {
  await open(page);
  const box = await page.locator('[data-tip]').first().boundingBox();
  await page.mouse.move(box!.x + 3, box!.y + 3);
  await expect(page.locator('#hud-caption')).toBeVisible();
  await page.mouse.move(box!.x + box!.width - 3, box!.y + box!.height - 3);
  await expect(page.locator('#hud-caption')).toBeVisible();
});

test('moving straight from one tipped element to another swaps the caption', async ({ page }) => {
  await open(page);
  const tips = page.locator('[data-tip]');
  const n = await tips.count();
  test.skip(n < 2, 'needs two tipped elements');
  const a = await tips.nth(0).boundingBox(), b = await tips.nth(n - 1).boundingBox();
  await page.mouse.move(a!.x + a!.width / 2, a!.y + a!.height / 2);
  await expect(page.locator('#hud-caption')).toBeVisible();
  const first = await page.locator('#hud-caption').textContent();
  await page.mouse.move(b!.x + b!.width / 2, b!.y + b!.height / 2);
  await expect(page.locator('#hud-caption')).toBeVisible();
  const second = await page.locator('#hud-caption').textContent();
  if ((await tips.nth(0).getAttribute('data-tip')) !== (await tips.nth(n - 1).getAttribute('data-tip'))) expect(second).not.toBe(first);
});
