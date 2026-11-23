import { expect, test } from '@playwright/test';

// Live test (user screenshot of the bottom-right panel): the glass slab behind each bottom info panel must hug its card in every frame mode,
// not hang below it. Measured in the page: the slab path in the frame's Decor SVG against the panel's own drawing.
const MODES: Record<string, Record<string, string>> = {
  rendered: { UseShipImage: '0', PictureFit: '0' },
  picture: { UseShipImage: '1', PictureFit: '0' },
  fitted: { UseShipImage: '1', PictureFit: '1' },
  none: { FrameOff: '1' },
};

for (const [mode, cfg] of Object.entries(MODES)) {
  for (const [w, h] of [[1707, 1067], [2560, 1600]] as [number, number][]) {
    test(`${mode} at ${w}x${h}: both bottom slabs hug their panel cards`, async ({ page }) => {
      await page.setViewportSize({ width: w, height: h });
      await page.addInitScript((c) => {
        sessionStorage.setItem('cspace.booted', '1');
        localStorage.setItem('mockhost.v1', JSON.stringify({ config: c, setupDone: true, aboutMe: '' }));
      }, cfg);
      await page.goto('/?preview=1&module=all');
      await page.waitForSelector('[data-module="panel-right"]');
      await page.waitForTimeout(800);
      const r = await page.evaluate(() => {
        const box = (e: Element) => { const b = e.getBoundingClientRect(); return { l: b.left, t: b.top, r: b.right, b: b.bottom }; };
        // the cards: the panels' own drawing (the first non-empty child group's rect is enough: take the whole module's ink)
        const L = document.querySelector('[data-module="panel-left"]')!, R = document.querySelector('[data-module="panel-right"]')!;
        // the slabs: filled 4-vertex paths in the Decor SVG that start inside the bottom third and are tall and narrow
        const slabs = [...document.querySelectorAll('.frame-parts[data-part$="Decor"] path')].filter((p) => {
          const d = p.getAttribute('d') || '', b = p.getBoundingClientRect();
          return /^M[\d. -]+L[\d. -]+L[\d. -]+L[\d. -]+Z$/.test(d) && b.height > innerHeight * 0.1 && b.width > innerWidth * 0.03 && b.width < innerWidth * 0.1 && b.top > innerHeight * 0.75 && p.getAttribute('fill') !== 'none';
        }).map(box);
        return { L: box(L), R: box(R), slabs };
      });
      expect(r.slabs.length, 'two filled slab paths').toBe(2);
      const k = Math.min(w / 2560, h / 1600);
      const slabOf = (panel: { l: number; r: number }) => r.slabs.find((s) => s.l < panel.r && s.r > panel.l)!;
      for (const [name, panel] of [['left', r.L], ['right', r.R]] as const) {
        const s = slabOf(panel);
        expect(s, name + ' slab found').toBeTruthy();
        // the slab covers the card and extends past it by about the padding only (7 canvas units, plus ink and skew), never by 50
        expect(s.b - panel.b, name + ' slab bottom vs panel bottom').toBeLessThanOrEqual(22 * k);
        expect(panel.t - s.t, name + ' slab top vs panel top').toBeLessThanOrEqual(22 * k);
        expect(s.t, name + ' slab top').toBeLessThanOrEqual(panel.t + 2 * k);
        expect(s.b, name + ' slab bottom').toBeGreaterThanOrEqual(panel.b - 22 * k);
        // centred across: the card sat about 9 units to one side of its slab at Scale 1.005 (the fitted-mode fix, now in every mode)
        expect(Math.abs((s.l + s.r) / 2 - (panel.l + panel.r) / 2), name + ' slab centre vs panel centre').toBeLessThanOrEqual(4 * k);
      }
    });
  }
}

// Live test: "remove this random arrow and cut circle" (a decor icon near canvas (640, 840) that belonged to no module). Gone in every frame mode.
for (const [mode, cfg] of Object.entries(MODES)) {
  test(`${mode}: the stray circle-with-arrow icon is gone`, async ({ page }) => {
    await page.setViewportSize({ width: 1707, height: 1067 });
    await page.addInitScript((c) => {
      sessionStorage.setItem('cspace.booted', '1');
      localStorage.setItem('mockhost.v1', JSON.stringify({ config: c, setupDone: true, aboutMe: '' }));
    }, cfg);
    await page.goto('/?preview=1&module=all');
    await page.waitForSelector('[data-module="panel-right"]');
    await page.waitForTimeout(600);
    // canvas (640, 840) is css (427, 560) at this size; no drawn decor element may sit there (size-zero shapes are fine)
    const n = await page.evaluate(() => [...document.querySelectorAll('.frame-parts *')].filter((e) => {
      const r = e.getBoundingClientRect();
      return r.width > 1 && r.width < 45 && r.height > 1 && r.height < 45 && Math.abs((r.left + r.right) / 2 - 427) < 14 && Math.abs((r.top + r.bottom) / 2 - 560) < 14;
    }).length);
    expect(n).toBe(0);
  });
}
