const { chromium } = require('C:/Users/Senai/RainmeterSpaceship/SpaceshipApp/SpaceshipUI/node_modules/@playwright/test');
const fs = require('fs'); const [,, a, b2, out] = process.argv;
(async () => {
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 560, height: 225 } });
  const u = (f) => 'data:image/png;base64,' + fs.readFileSync(f).toString('base64');
  await p.setContent(`<body style="margin:0;background:#000;display:flex;gap:10px"><img src="${u(a)}" width="270"><img src="${u(b2)}" width="270"></body>`);
  await p.screenshot({ path: out }); await b.close();
})();
