// mirror of SpectrumBands.Compute (Hann, band energy, dB -70..-6) to check the C# test expectations
const N = 1024, R = 48000;
function fft(re) { const n = re.length, a = re.map((x) => [x, 0]); const bits = Math.log2(n);
  const b = new Array(n); for (let i = 0; i < n; i++) { let j = 0; for (let k = 0; k < bits; k++) j |= ((i >> k) & 1) << (bits - 1 - k); b[j] = a[i]; }
  for (let len = 2; len <= n; len <<= 1) { const ang = -2 * Math.PI / len; for (let i = 0; i < n; i += len) for (let j = 0; j < len / 2; j++) {
    const w = [Math.cos(ang * j), Math.sin(ang * j)], u = b[i + j], v0 = b[i + j + len / 2], v = [v0[0] * w[0] - v0[1] * w[1], v0[0] * w[1] + v0[1] * w[0]];
    b[i + j] = [u[0] + v[0], u[1] + v[1]]; b[i + j + len / 2] = [u[0] - v[0], u[1] - v[1]]; } } return b; }
function compute(s, bands, minHz = 40, maxHz = 16000) { const n = s.length; const w = s.map((x, i) => x * (0.5 - 0.5 * Math.cos(2 * Math.PI * i / (n - 1))));
  const bins = fft(w), ny = Math.min(maxHz, R / 2), out = [];
  for (let b = 0; b < bands; b++) { const lo = minHz * (ny / minHz) ** (b / bands), hi = minHz * (ny / minHz) ** ((b + 1) / bands);
    let from = Math.max(1, Math.ceil(lo * n / R)), to = Math.min(n / 2 - 1, Math.floor(hi * n / R));
    if (from > to) from = to = Math.min(n / 2 - 1, Math.max(1, Math.round(Math.sqrt(lo * hi) * n / R)));
    let p = 0; for (let k = from; k <= to; k++) p += bins[k][0] ** 2 + bins[k][1] ** 2;
    const amp = Math.sqrt(p * 32 / 3) / n, db = amp > 0 ? 20 * Math.log10(amp) : -Infinity; out.push(Math.min(1, Math.max(0, (db + 70) / 64))); } return out; }
const tone = (hz, a) => Array.from({ length: N }, (_, i) => a * Math.sin(2 * Math.PI * hz * i / R));
const loud = compute(tone(1000, 1), 24), quiet = compute(tone(1000, 0.01), 24), half = compute(tone(1000, 0.5), 24), bass = compute(tone(60, 0.5), 24);
const top = half.indexOf(Math.max(...half));
console.log('loud max', Math.max(...loud).toFixed(3), '| quiet max', Math.max(...quiet).toFixed(3), '| far max', Math.max(...half.filter((_, i) => Math.abs(i - top) > 2)).toFixed(3), '| bass low4', Math.max(...bass.slice(0, 4)).toFixed(3));
console.log('8-band old test: loud', Math.max(...compute(tone(1000, 1), 8)).toFixed(3), 'silence', Math.max(...compute(new Array(N).fill(0), 8)));
