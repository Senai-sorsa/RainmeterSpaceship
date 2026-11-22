import { expect, test, type Page } from '@playwright/test';

// Task 13 (user, 2026-11-04): "window shading issues when switching from rendered to picture". The rendered hull and the picture have
// different windows (the rendered side windows are split by a diagonal strut, the picture's are one pane), so every window-shaped layer
// must come from the ACTIVE frame's own art. The measured bug: shade.png (made from the rendered windows) left a ~170 px unshaded diagonal
// band across each picture side window at 1707x1067.
const MODES: Record<string, Record<string, string>> = {
  rendered: { UseShipImage: '0', PictureFit: '0' },
  picture: { UseShipImage: '1', PictureFit: '0' },
  fitted: { UseShipImage: '1', PictureFit: '1' },
};
// the art each mode is drawn from, and which layers may only appear with it
const RENDERED_ONLY = ['glass_fx', 'scan', 'hull', 'mist', 'corners', 'sheen', 'bounce', 'spill', 'orblight', 'vignette', 'trimspill', 'grain'];
const PICTURE_ONLY = ['glass_pic', 'glass_fx_pic', 'scan_pic', 'ship', 'mist_pic'];

const boot = async (page: Page, cfg: Record<string, string>) => {
  await page.addInitScript((c) => {
    sessionStorage.setItem('cspace.booted', '1');
    localStorage.setItem('mockhost.v1', JSON.stringify({ config: c, setupDone: true, aboutMe: '' }));
  }, cfg);
  await page.goto('/?preview=1&module=all');
  await page.waitForSelector('.frame [data-layer="shade"]');
};

const layers = (page: Page) => page.evaluate(() => {
  const f = document.querySelector('.frame')!.getBoundingClientRect();
  return { frame: { x: f.left, y: f.top, w: f.width, h: f.height },
    list: [...document.querySelectorAll<HTMLElement>('.frame [data-layer]')].map((e) => {
      const b = e.getBoundingClientRect(), cs = getComputedStyle(e);
      return { name: e.dataset.layer!, x: b.left, y: b.top, w: b.width, h: b.height, src: `${cs.backgroundImage} ${cs.maskImage}` };
    }) };
});

// The shade must tint all of the active art's visible side-window glass: sample columns near both screen edges (the side windows; the
// centre window is clear on purpose) and count glass pixels (art alpha < 10) the shade leaves untinted (alpha <= 8). Read from the
// images the layers actually use, at the art's own 2560x1600.
const unshadedGlass = (page: Page) => page.evaluate(async () => {
  const urlOf = (name: string) => {
    const e = document.querySelector<HTMLElement>(`.frame [data-layer="${name}"]`);
    const m = e && /url\("?([^")]+)"?\)/.exec(getComputedStyle(e).backgroundImage);
    return m ? m[1] : null;
  };
  const art = urlOf('ship') ?? urlOf('hull'), shade = urlOf('shade');
  if (!art || !shade) throw new Error(`missing layer art=${art} shade=${shade}`);
  const alpha = async (src: string) => {
    const i = new Image(); i.src = src; await i.decode();
    const c = document.createElement('canvas'); c.width = i.naturalWidth; c.height = i.naturalHeight;
    const x = c.getContext('2d')!; x.drawImage(i, 0, 0);
    return x.getImageData(0, 0, c.width, c.height);
  };
  const A = await alpha(art), S = await alpha(shade);
  if (A.width !== S.width || A.height !== S.height) throw new Error('shade and art differ in size');
  let glass = 0, bare = 0;
  for (let k = 40; k <= 300; k += 20) for (const x of [k, A.width - 1 - k]) for (let y = 0; y < A.height; y++) {
    const i = (y * A.width + x) * 4 + 3;
    if (A.data[i] < 10) { glass++; if (S.data[i] <= 8) bare++; }
  }
  return { glass, bare };
});

const check = async (page: Page, mode: string) => {
  // the visible defect first: glass the shade does not reach
  const g = await unshadedGlass(page);
  expect(g.glass).toBeGreaterThan(10000);
  expect(g.bare, `side-window glass left unshaded in ${mode} (of ${g.glass})`).toBe(0);
  const { frame, list } = await layers(page);
  const names = list.map((l) => l.name);
  if (mode === 'rendered') expect(names.filter((n) => PICTURE_ONLY.includes(n)), 'no picture layer in rendered').toEqual([]);
  else expect(names.filter((n) => RENDERED_ONLY.includes(n)), `no rendered-only layer in ${mode}`).toEqual([]);
  // no picture-mode layer may draw a rendered window asset (window_mask, or a rendered layer image), and vice versa
  const renderedArt = /\/(window_mask|shade|glass_fx|scan|mist|hull|corners)\.[0-9a-f]{8}\.png/;
  for (const l of list) {
    if (mode !== 'rendered') expect(l.src, `${l.name} uses the rendered windows in ${mode}`).not.toMatch(renderedArt);
    else expect(l.src, `${l.name} uses picture art in rendered`).not.toMatch(/_pic|\/ship\./);
    for (const [k, v] of [['x', l.x - frame.x], ['y', l.y - frame.y], ['w', l.w - frame.w], ['h', l.h - frame.h]] as const)
      expect(Math.abs(v), `${l.name} ${k} on the .frame box`).toBeLessThanOrEqual(1);
  }
};

for (const [w, h] of [[1707, 1067], [2560, 1600]] as [number, number][]) {
  for (const [mode, cfg] of Object.entries(MODES)) {
    test(`${mode} at ${w}x${h}: every window layer comes from the ${mode === 'rendered' ? 'rendered hull' : 'picture'} and sits on the frame`, async ({ page }) => {
      await page.setViewportSize({ width: w, height: h });
      await boot(page, cfg);
      await check(page, mode);
    });
  }
}

test('switching rendered -> picture -> rendered -> fitted in the Control Center re-draws every window layer from the new frame', async ({ page }) => {
  await page.setViewportSize({ width: 1707, height: 1067 });
  await boot(page, MODES.rendered);
  await check(page, 'rendered');
  await page.locator('[aria-label="Control Center"]').first().click({ force: true });
  await page.waitForSelector('.cc');
  const sel = page.locator('.row', { hasText: 'Cockpit frame' }).locator('select');
  for (const v of ['picture', 'rendered', 'fitted', 'picture']) {
    await sel.selectOption(v);
    await expect(page.locator('.frame')).toHaveAttribute('data-frame', v);
    // the frame box is re-fitted after a frame-setting change; wait for the layers to settle on it
    await expect.poll(async () => { const { frame, list } = await layers(page); return Math.max(...list.map((l) => Math.abs(l.w - frame.w) + Math.abs(l.x - frame.x))); }, { timeout: 4000 }).toBeLessThanOrEqual(1);
    await check(page, v);
  }
});
