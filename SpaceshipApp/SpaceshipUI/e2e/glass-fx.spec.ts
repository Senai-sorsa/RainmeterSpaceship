import { expect, test, type Page } from '@playwright/test';

// Live test: "there is a light spot in the window, like a triangular structure". The skin's glare layer for the picture had an odd bright spot and a
// lambda of two streaks in the right window. CSpace's picture frames (Picture and Picture (fitted)) now use a cleaned layer (tools/clean_glass_fx.cjs):
// mirror-symmetric, and with nothing on the hull.
const MODES: Record<string, Record<string, string>> = { picture: { UseShipImage: '1', PictureFit: '0' }, fitted: { UseShipImage: '1', PictureFit: '1' } };

const analyse = (page: Page) => page.evaluate(async () => {
  const urlOf = (sel: string) => (getComputedStyle(document.querySelector(sel)!).backgroundImage.match(/url\("?([^")]+)"?\)/) ?? [])[1];
  const load = (u: string) => new Promise<HTMLImageElement>((res, rej) => { const i = new Image(); i.onload = () => res(i); i.onerror = rej; i.src = u; });
  const px = (i: HTMLImageElement) => { const c = document.createElement('canvas'); c.width = i.width; c.height = i.height; const x = c.getContext('2d')!; x.drawImage(i, 0, 0); return x.getImageData(0, 0, i.width, i.height); };
  const fxUrl = urlOf('[data-layer="glass_fx_pic"]'), shipUrl = urlOf('[data-layer="ship"]');
  const F = px(await load(fxUrl)), S = px(await load(shipUrl)), W = F.width, H = F.height;
  let mirrorOff = 0, mirrorN = 0, onHull = 0, hull = 0, lit = 0, brightest = 0;
  for (let y = 0; y < H; y += 2) for (let x = 0; x < W / 2; x += 2) {
    const a = F.data[(y * W + x) * 4 + 3], b = F.data[(y * W + (W - 1 - x)) * 4 + 3];
    mirrorN++;
    if (Math.abs(a - b) > 6) mirrorOff++; // the windows' own edges are not pixel-symmetric, so count, do not take the maximum
  }
  for (let i = 0; i < W * H; i += 3) {
    const sa = S.data[i * 4 + 3], fa = F.data[i * 4 + 3];
    if (sa > 250) { hull++; if (fa > 2) onHull++; }
    if (fa > 0) lit++;
    brightest = Math.max(brightest, fa);
  }
  return { fxUrl, W, H, mirrorShare: mirrorOff / mirrorN, onHull, hull, lit, brightest };
});

for (const [mode, cfg] of Object.entries(MODES)) {
  test(`${mode}: the glare layer is the cleaned one, mirror-symmetric, and does not touch the hull`, async ({ page }) => {
    await page.setViewportSize({ width: 1707, height: 1067 });
    await page.addInitScript((c) => {
      sessionStorage.setItem('cspace.booted', '1');
      localStorage.setItem('mockhost.v1', JSON.stringify({ config: c, setupDone: true, aboutMe: '' }));
    }, cfg);
    await page.goto('/?preview=1&module=all');
    await page.waitForSelector('[data-layer="glass_fx_pic"]');
    const r = await analyse(page);
    expect(r.fxUrl, 'the cleaned asset').toContain('glass_fx_pic_clean');
    expect([r.W, r.H]).toEqual([2560, 1600]);
    expect(r.mirrorShare, 'share of pixels where the left half and the mirrored right half differ by more than 6 alpha levels').toBeLessThan(0.002);
    expect(r.onHull / r.hull, 'share of the opaque hull that carries glare').toBeLessThan(0.0005);
    expect(r.lit, 'there is still glare in the windows').toBeGreaterThan(20000);
    expect(r.brightest, 'and no blown-out spot').toBeLessThan(120);
  });
}

test('the line-art frame keeps the skin glare layer (this fix is for the picture frames)', async ({ page }) => {
  await page.setViewportSize({ width: 1707, height: 1067 });
  await page.addInitScript(() => {
    sessionStorage.setItem('cspace.booted', '1');
    localStorage.setItem('mockhost.v1', JSON.stringify({ config: { UseShipImage: '0' }, setupDone: true, aboutMe: '' }));
  });
  await page.goto('/?preview=1&module=all');
  await page.waitForSelector('[data-layer="glass_fx"]');
  expect(await page.locator('[data-layer="glass_fx_pic"]').count()).toBe(0);
});
