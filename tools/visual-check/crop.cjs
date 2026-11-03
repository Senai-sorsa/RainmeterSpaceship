// node crop.cjs in.png out.png x y w h  (crops via a page that draws the image)
const { chromium } = require('C:/Users/Senai/RainmeterSpaceship/SpaceshipApp/SpaceshipUI/node_modules/@playwright/test');
const fs = require('fs'); const [,, inp, out, x, y, w, h] = process.argv;
(async () => {
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: +w, height: +h } });
  const data = fs.readFileSync(inp).toString('base64');
  await p.setContent(`<body style="margin:0;overflow:hidden"><img src="data:image/png;base64,${data}" style="position:absolute;left:${-x}px;top:${-y}px"></body>`);
  await p.screenshot({ path: out }); await b.close();
})();
