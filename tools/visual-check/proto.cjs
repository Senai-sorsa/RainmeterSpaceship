// node proto.cjs <out.png> '<json config>' [url] [w h dpr] [clip x y w h]
const { chromium } = require('C:/Users/Senai/RainmeterSpaceship/SpaceshipApp/SpaceshipUI/node_modules/@playwright/test');
const [,, out, cfg = '{}', url = '/?preview=1&module=all', w = '1707', h = '1067', dpr = '1.5', cx, cy, cw, ch] = process.argv;
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: +w, height: +h }, deviceScaleFactor: +dpr });
  await p.addInitScript((c) => { sessionStorage.setItem('cspace.booted', '1'); localStorage.setItem('mockhost.v1', JSON.stringify({ config: JSON.parse(c), setupDone: true, aboutMe: '' })); }, cfg);
  p.on('pageerror', (e) => console.log('ERR', String(e)));
  await p.goto('http://localhost:5199' + url); await p.waitForTimeout(3000);
  await p.screenshot({ path: out, ...(cx ? { clip: { x: +cx, y: +cy, width: +cw, height: +ch } } : {}) });
  await b.close();
})();
