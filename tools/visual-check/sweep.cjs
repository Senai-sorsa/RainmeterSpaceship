const { chromium } = require('C:/Users/Senai/RainmeterSpaceship/SpaceshipApp/SpaceshipUI/node_modules/@playwright/test');
const out = process.argv[2], B = 'http://localhost:5199';
const done = { config: {}, setupDone: true, aboutMe: '' }, fresh = { config: {}, setupDone: false, aboutMe: '' };
const cats = ['display', 'layout', 'apps', 'sensors', 'performance', 'assistant', 'integrations', 'system'];
const jobs = [
  ...[0, 1, 2, 3].map((n) => ({ name: `wiz-${n + 1}`, url: '/', host: fresh, w: 1600, h: 1000, act: async (p) => { await p.locator('.wiz-mod').nth(n).click(); } })),
  ...cats.map((c) => ({ name: `cc-${c}`, url: '/?panel=control', host: done, cat: c, w: 1600, h: 1000 })),
  { name: 'cc-advanced', url: '/?panel=control&level=advanced', host: done, cat: 'display', w: 1600, h: 1000 },
  { name: 'cc-search', url: '/?panel=control', host: done, cat: 'display', w: 1600, h: 1000, act: async (p) => { await p.locator('.cc-search').fill('glow'); } },
  { name: 'cc-helpsheet', url: '/?panel=control', host: done, cat: 'display', w: 1600, h: 1000, act: async (p) => { await p.locator('.help-btn').first().click(); } },
  { name: 'cc-rowtip', url: '/?panel=control', host: done, cat: 'display', w: 1600, h: 1000, act: async (p) => { await p.locator('.row-label').first().hover(); } },
  { name: 'notices', url: '/?preview=1&module=all&notices=demo', host: done, w: 1707, h: 1067 },
  { name: 'kit', url: '/?panel=kit', host: done, w: 1600, h: 1000 },
  { name: 'demo', url: '/?panel=demo', host: done, w: 1600, h: 1000 },
  { name: 'demo-wizard', url: '/?panel=demo-wizard', host: done, w: 1600, h: 1000 },
  { name: 'log-muted', url: '/?preview=1&module=jarvislog&jarvislog=demo', host: done, w: 1707, h: 1067 },
];
(async () => {
  const b = await chromium.launch();
  for (const j of jobs) {
    const p = await b.newPage({ viewport: { width: j.w, height: j.h } });
    await p.addInitScript(([h, c]) => { sessionStorage.setItem('cspace.booted', '1'); localStorage.setItem('mockhost.v1', JSON.stringify(h)); if (c) localStorage.setItem('ui.cat.v1', c); }, [j.host, j.cat]);
    const errs = []; p.on('pageerror', (e) => errs.push(String(e)));
    await p.goto(B + j.url); await p.waitForTimeout(1800);
    try { if (j.act) { await j.act(p); await p.waitForTimeout(500); } } catch (e) { errs.push('ACT ' + String(e).slice(0, 120)); }
    await p.screenshot({ path: `${out}/${j.name}.png` });
    if (errs.length) console.log(j.name, errs.join(' | '));
    await p.close();
  }
  await b.close(); console.log('done', jobs.length);
})();
