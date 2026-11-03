// node sheet.cjs out.png cols cellW cellH img1 img2 ...  (labelled contact sheet)
const { chromium } = require('C:/Users/Senai/RainmeterSpaceship/SpaceshipApp/SpaceshipUI/node_modules/@playwright/test');
const fs = require('fs'), path = require('path'); const [,, out, cols, cw, ch, ...imgs] = process.argv;
(async () => {
  const b = await chromium.launch(); const rows = Math.ceil(imgs.length / cols);
  const p = await b.newPage({ viewport: { width: cols * cw, height: rows * (+ch + 18) } });
  const cells = imgs.map((f) => `<div style="width:${cw}px"><div style="font:12px sans-serif;color:#ff0;background:#222;height:18px">${path.basename(f)}</div><img src="data:image/png;base64,${fs.readFileSync(f).toString('base64')}" style="width:${cw}px;height:${ch}px;object-fit:contain;background:#000"></div>`).join('');
  await p.setContent(`<body style="margin:0;display:flex;flex-wrap:wrap;width:${cols * cw}px;background:#111">${cells}</body>`);
  await p.screenshot({ path: out, fullPage: true }); await b.close();
})();
