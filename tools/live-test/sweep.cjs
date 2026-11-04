// node sweep.cjs <outdir> [seconds=8]   Port 5199 dev server must be running (npx vite --port 5199 --strictPort in SpaceshipApp/SpaceshipUI).
// Runs the real HUD UI in GPU-enabled Chrome, one fresh browser per case, changes settings through the mock host (never touches your live app or settings.json),
// screenshots each case and measures CPU / RAM / GPU of that browser's process tree. Writes results.json, results.md and PNGs to <outdir>.
const { chromium } = require('C:/Users/Senai/RainmeterSpaceship/SpaceshipApp/SpaceshipUI/node_modules/@playwright/test');
const { execFileSync, spawn } = require('child_process'); const fs = require('fs'); const path = require('path');
const out = process.argv[2]; const secs = +(process.argv[3] || 8); fs.mkdirSync(out, { recursive: true });
const VIS = process.env.VISIBLE === '1';
const URL = process.env.URL || 'http://localhost:5199';
const ONLY = process.env.ONLY ? process.env.ONLY.split('|') : null, ROUNDS = +(process.env.ROUNDS || 1);
const base = {};
const M = '/?preview=1&module=all&audio=demo';
const ALL = [
  ['base FULL idle', base],
  ['base FULL music', base, M],
  ['BloomEngine=svg', { BloomEngine: 'svg' }],
  ['LensFx=0', { LensFx: 0 }],
  ['DepthHaze=0', { DepthHaze: 0 }],
  ['ScreenBezel=0', { ScreenBezel: 0 }],
  ['StateLight=0', { StateLight: 0 }],
  ['LensFx+Haze+Bezel+Light all 0', { LensFx: 0, DepthHaze: 0, ScreenBezel: 0, StateLight: 0 }],
  ['frame=picture', { UseShipImage: 1 }],
  ['frame=none', { FrameOff: 1 }],
  ['hide css-gradient layers', base, undefined, '[data-layer=sheen],[data-layer=bounce],[data-layer=spill],[data-layer=orblight],[data-layer=vignette],[data-layer=trimspill],[data-layer=grain]{display:none!important}'],
  ['hide hull+corners+shade images', base, undefined, '[data-layer=hull],[data-layer=corners],[data-layer=shade]{display:none!important}'],
  ['hide glass_fx+scan+mist', base, undefined, '[data-layer=glass_fx],[data-layer=scan],[data-layer=mist]{display:none!important}'],
  ['hide all frame layers (css only)', base, undefined, '.frame{display:none!important}'],
  ['ReduceMotion=1', { ReduceMotion: 1 }],
  ['FrameBrightness=60', { FrameBrightness: 60 }],
  ['tier LITE', { PerfOverride: 1 }],
  ['tier LOW', { PerfOverride: 2 }],
  ['tier STEALTH', { PerfOverride: 3 }],
];
const cases = Array.from({ length: ROUNDS }, () => ALL.filter(c => !ONLY || ONLY.includes(c[0]))).flat();
(async () => {
  const rows = [];
  for (const [name, cfg, url = '/?preview=1&module=all', css = ''] of cases) {
    const port = 9300 + rows.length; const udd = fs.mkdtempSync(path.join(require('os').tmpdir(), 'lt-'));
    const proc = spawn('C:/Program Files/Google/Chrome/Application/chrome.exe', [...(VIS ? ['--window-position=0,0','--window-size=1707,1067'] : ['--headless=new']), '--remote-debugging-port=' + port, '--user-data-dir=' + udd, '--enable-gpu', '--use-angle=d3d11', '--ignore-gpu-blocklist', '--enable-gpu-rasterization', '--no-first-run', 'about:blank'], { stdio: 'ignore' });
    const pid = proc.pid; let b;
    for (let i = 0; i < 40 && !b; i++) { await new Promise(r => setTimeout(r, 250)); try { b = await chromium.connectOverCDP('http://127.0.0.1:' + port); } catch {} }
    const ctx = VIS ? b.contexts()[0] : await b.newContext({ viewport: { width: 1707, height: 1067 }, deviceScaleFactor: 1.5 });
    const p = VIS ? (ctx.pages()[0] || await ctx.newPage()) : await ctx.newPage(); p.on('response', r => { if (r.status() >= 400) msgs.push(r.status() + ' ' + r.url().slice(0, 100)); }); const msgs = [];
    p.on('console', m => { if (['warning', 'error'].includes(m.type())) msgs.push(m.type() + ': ' + m.text().slice(0, 120)); }); p.on('pageerror', e => msgs.push('pageerror ' + String(e).slice(0, 120)));
    p.on('requestfailed', r => msgs.push('reqfail ' + r.url().slice(0, 100)));
    await p.addInitScript((c) => { sessionStorage.setItem('cspace.booted', '1'); localStorage.setItem('mockhost.v1', JSON.stringify({ config: Object.fromEntries(Object.entries(c).map(([k, v]) => [k, String(v)])), setupDone: true, aboutMe: '' })); }, cfg);
    await p.goto(URL + url); if (css) await p.addStyleTag({ content: css }); await p.waitForTimeout(4000);
    const slug = name.replace(/[^a-z0-9]+/gi, '_');
    await p.screenshot({ path: path.join(out, slug + '.png') });
    const layers = await p.evaluate(() => [...document.querySelectorAll('.frame [data-layer]')].map(e => e.getAttribute('data-layer')).join(','));
    let m; try { m = JSON.parse(execFileSync('powershell', ['-NoProfile', '-File', path.join(__dirname, 'sample.ps1'), '-RootPid', String(pid), '-Seconds', String(secs)]).toString().trim()); } catch (e) { m = { error: String(e).slice(0, 100) }; }
    rows.push({ name, ...m, layers, msgs: [...new Set(msgs)] }); console.log(JSON.stringify(rows[rows.length - 1]));
    await b.close().catch(() => {}); try { execFileSync('taskkill', ['/PID', String(pid), '/T', '/F'], { stdio: 'ignore' }); } catch {} try { fs.rmSync(udd, { recursive: true, force: true }); } catch {}
  }
  fs.writeFileSync(path.join(out, 'results.json'), JSON.stringify(rows, null, 1));
  const f = (n) => rows.find(r => r.name === n);
  let md = '| case | CPU % of 1 core | d vs base | RAM MB | GPU 3D % | d GPU vs base | msgs |\n|---|---|---|---|---|---|---|\n';
  for (const r of rows) { const b0 = r.name.includes('music') ? f(r.name.startsWith('Hull') ? 'base FULL music' : 'base FULL music') : f('base FULL idle');
    md += `| ${r.name} | ${r.cpu} | ${(r.cpu - b0.cpu).toFixed(1)} | ${r.ram} | ${r.gpu_3D} | ${(r.gpu_3D - b0.gpu_3D).toFixed(2)} | ${r.msgs.length} |\n`; }
  fs.writeFileSync(path.join(out, 'results.md'), md); console.log(md);
})();
