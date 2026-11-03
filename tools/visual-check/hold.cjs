const { chromium } = require('C:/Users/Senai/RainmeterSpaceship/SpaceshipApp/SpaceshipUI/node_modules/@playwright/test');
const css = process.argv[2] || '';
(async () => {
  const b = await chromium.launch({ args: ['--enable-gpu-rasterization'] }); const p = await b.newPage({ viewport: { width: 1707, height: 1067 }, deviceScaleFactor: 1.5 });
  await p.addInitScript(() => { sessionStorage.setItem('cspace.booted', '1'); localStorage.setItem('mockhost.v1', JSON.stringify({ config: {}, setupDone: true, aboutMe: '' })); });
  await p.goto('http://localhost:5199/?preview=1&module=all'); if (css) await p.addStyleTag({ content: css });
  console.log('ready'); await p.waitForTimeout(26000); await b.close();
})();
