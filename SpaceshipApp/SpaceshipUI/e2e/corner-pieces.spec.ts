import { expect, test } from '@playwright/test';

// Plan B: tiny chrome caps on the screen corners, in the Picture (fitted) frame only, and off with CornerPieces=0.
const MODES: Record<string, [Record<string, string>, number]> = {
  rendered: [{ UseShipImage: '0', PictureFit: '0' }, 0],
  picture: [{ UseShipImage: '1', PictureFit: '0' }, 0],
  fitted: [{ UseShipImage: '1', PictureFit: '1' }, 1],
  'fitted, caps off': [{ UseShipImage: '1', PictureFit: '1', CornerPieces: '0' }, 0],
  none: [{ FrameOff: '1' }, 0],
};
const SHOTS = process.env.CORNER_SHOTS; // a folder: also save full-page screenshots of the fitted frame there

for (const [mode, [cfg, want]] of Object.entries(MODES)) {
  test(`${mode}: corner caps shown ${want}`, async ({ page }) => {
    await page.setViewportSize({ width: 1707, height: 1067 });
    await page.addInitScript((c) => {
      sessionStorage.setItem('cspace.booted', '1');
      localStorage.setItem('mockhost.v1', JSON.stringify({ config: c, setupDone: true, aboutMe: '' }));
    }, cfg);
    await page.goto('/?preview=1&module=all');
    await page.waitForSelector('[data-module="panel-right"]');
    await expect(page.locator('[data-part="corner-pieces"]')).toHaveCount(want);
  });
}

for (const [w, h] of [[1920, 1080], [2560, 1600], [3840, 2160]] as [number, number][]) {
  test(`fitted at ${w}x${h}: the caps sit in the frame's corners and stay tiny`, async ({ page }) => {
    await page.setViewportSize({ width: w, height: h });
    await page.addInitScript(() => {
      sessionStorage.setItem('cspace.booted', '1');
      localStorage.setItem('mockhost.v1', JSON.stringify({ config: { UseShipImage: '1', PictureFit: '1' }, setupDone: true, aboutMe: '' }));
    });
    await page.goto('/?preview=1&module=all');
    await page.waitForSelector('[data-part="corner-pieces"]');
    await page.waitForTimeout(600);
    const r = await page.evaluate(() => {
      const f = document.querySelector('.frame')!.getBoundingClientRect();
      const gs = [...document.querySelectorAll('[data-part="corner-pieces"] g')];
      const caps = gs.map((g) => g.getBoundingClientRect());
      // the HUD's click targets (and buttons) that a cap's filled L actually covers: there must be none. Boxes are too coarse: the top-right L wraps
      // around the SETTINGS button without touching it, so sample the overlap every css px and ask the path itself.
      const which: string[] = [];
      for (const e of document.querySelectorAll('[data-hit], button')) {
        const h = e.getBoundingClientRect();
        if (!h.width || !h.height) continue;
        gs.forEach((g, i) => {
          const c = caps[i], path = g.querySelector('path') as SVGPathElement, inv = path.getScreenCTM()!.inverse();
          for (let x = Math.max(h.left, c.left); x <= Math.min(h.right, c.right); x++)
            for (let y = Math.max(h.top, c.top); y <= Math.min(h.bottom, c.bottom); y++)
              if (path.isPointInFill(new DOMPoint(x, y).matrixTransform(inv))) { which.push((e.getAttribute("aria-label") || e.textContent || "?") + " @" + x.toFixed(0) + "," + y.toFixed(0)); return; }
        });
      }
      return { which, f: { l: f.left, t: f.top, r: f.right, b: f.bottom, w: f.width }, caps: caps.map((c) => ({ l: c.left, t: c.top, r: c.right, b: c.bottom })) };
    });
    expect(r.caps).toHaveLength(4);
    expect(r.which, 'click targets under a cap').toEqual([]);
    const k = r.f.w / 2560, near = 2 * k + 1;
    const [tl, tr, bl, br] = r.caps;
    expect(Math.abs(tl.l - r.f.l)).toBeLessThanOrEqual(near); expect(Math.abs(tl.t - r.f.t)).toBeLessThanOrEqual(near);
    expect(Math.abs(tr.r - r.f.r)).toBeLessThanOrEqual(near); expect(Math.abs(tr.t - r.f.t)).toBeLessThanOrEqual(near);
    expect(Math.abs(bl.l - r.f.l)).toBeLessThanOrEqual(near); expect(Math.abs(bl.b - r.f.b)).toBeLessThanOrEqual(near);
    expect(Math.abs(br.r - r.f.r)).toBeLessThanOrEqual(near); expect(Math.abs(br.b - r.f.b)).toBeLessThanOrEqual(near);
    for (const c of r.caps) expect(c.r - c.l).toBeLessThanOrEqual(50 * k + 2); // tiny: about 46 canvas units across
    if (SHOTS) await page.screenshot({ path: `${SHOTS}/fitted_${w}x${h}.png` });
    if (SHOTS) for (const [n, x, y] of [['tl', 0, 0], ['tr', w - 160, 0], ['bl', 0, h - 120], ['br', w - 160, h - 120]] as const) await page.screenshot({ path: `${SHOTS}/zoom_${w}_${n}.png`, clip: { x, y, width: 160, height: 120 } });
  });
}
