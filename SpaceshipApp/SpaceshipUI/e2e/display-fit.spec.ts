import { expect, test } from '@playwright/test';

// The HUD must fill the screen at any Windows display scale, resolution or window shape (live test U10).
// CSS px are what the page sees: 2560x1600 @100 % = 2560x1600, @125 % = 2048x1280, @150 % = 1707x1067, @200 % = 1280x800.
const SIZES: [number, number][] = [[1280, 800], [1707, 1067], [2048, 1280], [2560, 1600], [1920, 1080], [3440, 1440], [1600, 1200]];

for (const [w, h] of SIZES) {
  test(`frame fills the 16:10 box that fits a ${w}x${h} window`, async ({ page }) => {
    await page.setViewportSize({ width: w, height: h });
    await page.addInitScript(() => { sessionStorage.setItem('cspace.booted', '1'); localStorage.setItem('mockhost.v1', JSON.stringify({ config: { Scale: '0.67' }, setupDone: true, aboutMe: '' })); });
    await page.goto('/?preview=1&module=all');
    await page.waitForSelector('.frame');
    const box = await page.locator('.frame').boundingBox();
    const want = Math.min(w, h * 1.6);
    expect(Math.abs(box!.width - want)).toBeLessThanOrEqual(want * 0.01 + 1); // within 1 % (the skin overhangs 0.5 % at 0.67)
  });
}

test('the fill follows a live resize without a reload', async ({ page }) => {
  await page.addInitScript(() => { sessionStorage.setItem('cspace.booted', '1'); localStorage.setItem('mockhost.v1', JSON.stringify({ config: { Scale: '0.67' }, setupDone: true, aboutMe: '' })); });
  await page.setViewportSize({ width: 1707, height: 1067 });
  await page.goto('/?preview=1&module=all');
  await page.waitForSelector('.frame');
  await page.setViewportSize({ width: 2560, height: 1600 });
  await page.waitForTimeout(400);
  const box = await page.locator('.frame').boundingBox();
  expect(Math.abs(box!.width - 2560)).toBeLessThanOrEqual(26);
});

// the modules (svg, letterboxed xMidYMid) and the frame art (CSS box) must cover the same 16:10 area on any window shape
for (const [w, h] of [[1920, 1080], [3440, 1440], [1600, 1200], [1707, 1067]] as [number, number][]) {
  test(`modules and frame share one area at ${w}x${h}`, async ({ page }) => {
    await page.setViewportSize({ width: w, height: h });
    await page.addInitScript(() => { sessionStorage.setItem('cspace.booted', '1'); localStorage.setItem('mockhost.v1', JSON.stringify({ config: { Scale: '0.67' }, setupDone: true, aboutMe: '' })); });
    await page.goto('/?preview=1&module=all');
    await page.waitForSelector('.frame');
    const r = await page.evaluate(() => {
      const svg = document.querySelector('#hud') as SVGSVGElement;
      const vb = svg.viewBox.baseVal, m = svg.getScreenCTM()!;
      const f = document.querySelector('.frame')!.getBoundingClientRect();
      return { x: m.e, y: m.f, w: vb.width * m.a, h: vb.height * m.d, fx: f.left, fy: f.top, fw: f.width, fh: f.height };
    });
    // the frame overhangs right and down by the skin's 0.5 % at Scale 0.67, so compare the top-left corner and the size with a small tolerance
    expect(Math.abs(r.x - r.fx)).toBeLessThanOrEqual(2); // the frame is anchored at the canvas top-left, like Frame.ini
    expect(Math.abs(r.y - r.fy)).toBeLessThanOrEqual(2);
    expect(Math.abs(r.w - r.fw)).toBeLessThanOrEqual(r.w * 0.012 + 1);
  });
}
