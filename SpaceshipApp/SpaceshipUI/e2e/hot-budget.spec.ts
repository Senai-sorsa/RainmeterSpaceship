import { expect, test } from '@playwright/test';

// Composition rule (tasks/hyperrealism-plan.md Task 11, research A3): the references keep only one to three things
// white-hot per cluster. Hot highlights (Canvas.hot / hotDot) are the bloom groups blurred three times wider than the
// rest, so the old SVG engine shows them per module. Limit: 2 per module, 3 per side column.
const LIMIT = { module: 2, column: 3 };

test('few hot highlights per cluster', async ({ page }) => {
  await page.addInitScript(() => {
    sessionStorage.setItem('cspace.booted', '1');
    localStorage.setItem('mockhost.v1', JSON.stringify({ config: { BloomEngine: 'svg' }, setupDone: true, aboutMe: '' }));
  });
  await page.goto('/?preview=1&module=all');
  await expect(page.locator('#hud g.bloom').first()).toBeAttached();
  const hot = await page.evaluate(() => {
    const out: Record<string, number> = {};
    for (const g of document.querySelectorAll<SVGGElement>('#hud [data-module]')) {
      const groups = [...g.querySelectorAll<SVGGElement>(':scope g.bloom')].map((e) => [parseFloat(/blur\(([\d.]+)/.exec(e.style.filter)![1]), e.childElementCount]);
      if (!groups.length) continue;
      const max = Math.max(...groups.map((x) => x[0])), min = Math.min(...groups.map((x) => x[0]));
      const n = max > min * 2 ? groups.filter((x) => x[0] === max).reduce((s, x) => s + x[1], 0) : 0;
      out[g.dataset.module!] = (out[g.dataset.module!] ?? 0) + n;
    }
    return out;
  });
  expect(Object.keys(hot).length).toBeGreaterThan(10);
  for (const [m, n] of Object.entries(hot)) expect.soft(n, m).toBeLessThanOrEqual(LIMIT.module);
  for (const side of ['left', 'right']) {
    const sum = Object.entries(hot).filter(([m]) => m.startsWith(side + '-')).reduce((s, [, n]) => s + n, 0);
    expect.soft(sum, side).toBeLessThanOrEqual(LIMIT.column);
  }
});
