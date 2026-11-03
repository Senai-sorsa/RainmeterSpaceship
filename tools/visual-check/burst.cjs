const { chromium } = require('C:/Users/Senai/RainmeterSpaceship/SpaceshipApp/SpaceshipUI/node_modules/@playwright/test');
(async () => {
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1707, height: 1067 }, deviceScaleFactor: 1.5 });
  await p.addInitScript(() => { sessionStorage.setItem('cspace.booted', '1'); localStorage.setItem('mockhost.v1', JSON.stringify({ config: {}, setupDone: true, aboutMe: '' })); });
  await p.goto('http://localhost:5199/?preview=1&module=all&audio=demo'); await p.waitForTimeout(2500);
  const sig = [];
  for (let i = 0; i < 4; i++) {
    await p.screenshot({ path: `${process.argv[2]}-${i}.png`, clip: { x: 1060, y: 820, width: 180, height: 150 } });
    sig.push(await p.locator('g[data-module="audio"]').evaluate((g) => g.innerHTML.length));
    await p.waitForTimeout(150);
  }
  console.log('markup sizes per frame', sig.join(' ')); await b.close();
})();
