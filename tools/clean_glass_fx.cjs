// node tools/clean_glass_fx.cjs
// CSpace's picture-frame glare layer, cleaned. The skin's glass_fx_pic.png (made by tools/image_frame.py from the picture) has a clean diagonal
// light shaft in the left window but an odd "lambda" of two streaks with a bright spot in the right window (live test: "a light spot in the window,
// like a triangular structure"). The picture is left/right symmetric, so the right half is the mirror of the left half, and the result is trimmed
// to the picture's windows (ship.png's transparent area) so no glare lands on the hull.
// Writes SpaceshipApp/SpaceshipUI/src/assets/glass_fx_pic_clean.png (a CSpace-only asset; the skin's Images/ are not touched).
// Pillow is not required: the pixels are processed in a headless browser canvas (Playwright from SpaceshipUI/node_modules).
const fs = require('fs');
const path = require('path');
const root = path.resolve(__dirname, '..');
const { chromium } = require(path.join(root, 'SpaceshipApp/SpaceshipUI/node_modules/@playwright/test'));
const img = (n) => fs.readFileSync(path.join(root, 'Skins/Spaceship/@Resources/Images', n)).toString('base64');

(async () => {
  const b = await chromium.launch(); const p = await b.newPage(); await p.setContent('<body></body>');
  const png = await p.evaluate(async ([fx, ship]) => {
    const load = (s) => new Promise((res, rej) => { const i = new Image(); i.onload = () => res(i); i.onerror = rej; i.src = 'data:image/png;base64,' + s; });
    const px = (i) => { const c = document.createElement('canvas'); c.width = i.width; c.height = i.height; const x = c.getContext('2d'); x.drawImage(i, 0, 0); return x.getImageData(0, 0, i.width, i.height); };
    const F = px(await load(fx)), S = px(await load(ship)), W = F.width, H = F.height;
    if (S.width !== W || S.height !== H) throw new Error('size mismatch');
    const out = new ImageData(W, H), half = W / 2;
    for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
      const sx = x < half ? x : W - 1 - x; // the right half mirrors the left half
      const i = (y * W + x) * 4, k = (y * W + sx) * 4;
      const windowShare = 1 - S.data[i + 3] / 255; // 1 in the window, 0 on the hull
      out.data[i] = F.data[k]; out.data[i + 1] = F.data[k + 1]; out.data[i + 2] = F.data[k + 2];
      out.data[i + 3] = Math.round(F.data[k + 3] * windowShare);
    }
    const c = document.createElement('canvas'); c.width = W; c.height = H; c.getContext('2d').putImageData(out, 0, 0);
    return c.toDataURL('image/png').split(',')[1];
  }, [img('glass_fx_pic.png'), img('ship.png')]);
  const dest = path.join(root, 'SpaceshipApp/SpaceshipUI/src/assets/glass_fx_pic_clean.png');
  fs.writeFileSync(dest, Buffer.from(png, 'base64'));
  console.log('wrote', dest, fs.statSync(dest).size, 'bytes');
  await b.close();
})();
