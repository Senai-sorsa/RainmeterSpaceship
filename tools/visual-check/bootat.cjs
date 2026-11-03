const { chromium } = require('C:/Users/Senai/RainmeterSpaceship/SpaceshipApp/SpaceshipUI/node_modules/@playwright/test');
const [,, out, fr, mods = 'boot'] = process.argv;
(async () => {
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1707, height: 1067 }, deviceScaleFactor: 1.5 });
  await p.addInitScript(() => { localStorage.setItem('mockhost.v1', JSON.stringify({ config: {}, setupDone: true, aboutMe: '' })); });
  p.on('pageerror', (e) => console.log('ERR', String(e)));
  await p.goto(`http://localhost:5199/?preview=1&module=${mods}&bootat=${fr}`); await p.waitForTimeout(2500);
  await p.screenshot({ path: out }); await b.close();
})();
