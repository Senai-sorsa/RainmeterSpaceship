// Rainmeter 'r,g,b[,a]' colour strings -> CSS. Defaults are the skin's own (Scripts/lib.lua H.init), not reference-image values.
export type RGBA = [number, number, number, number];
export const SKIN_DEFAULTS: Record<string, string> = {
  ColorAccent: '0,210,255', ColorDim: '0,110,150', ColorText: '170,235,255', ColorWarn: '255,130,40',
  ColorAlert: '255,60,70', ColorGood: '60,255,170', ColorHighlight: '255,105,135', ColorWhite: '215,240,255',
  ColorPanel: '0,30,45,90',
};
// same pattern as lib.lua parseColor; also accepts #RRGGBB[AA] (Rainmeter hex form, not used in Settings.inc today)
export function parseColor(s: string | undefined, fallback: RGBA): RGBA {
  const t = (s ?? '').trim();
  const h = /^#?([0-9a-f]{6})([0-9a-f]{2})?$/i.exec(t);
  if (h) return [0, 2, 4].map((i) => parseInt(h[1].slice(i, i + 2), 16)).concat(h[2] ? parseInt(h[2], 16) : 255) as RGBA;
  const m = /^\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,?\s*(\d*)/.exec(t);
  if (!m) return fallback;
  return [+m[1], +m[2], +m[3], m[4] === '' ? 255 : +m[4]];
}
export const css = ([r, g, b, a]: RGBA) => (a === 255 ? `rgb(${r},${g},${b})` : `rgb(${r} ${g} ${b} / ${+(a / 255).toFixed(4)})`);

const NAMES: Record<string, string> = {
  ColorAccent: '--accent', ColorDim: '--dim', ColorText: '--text', ColorWarn: '--warn', ColorAlert: '--alert',
  ColorGood: '--good', ColorHighlight: '--hi', ColorWhite: '--white', ColorPanel: '--panel',
};
/** CSS custom properties for the skin theme: settings variables win, skin defaults fill gaps. */
export function themeVars(v: Record<string, string>): Record<string, string> {
  const out: Record<string, string> = {};
  for (const [k, name] of Object.entries(NAMES)) out[name] = css(parseColor(v[k], parseColor(SKIN_DEFAULTS[k], [0, 0, 0, 255])));
  // neon core = accent pulled toward white by CoreWhite (lib.lua H.mix, floor per channel)
  const acc = parseColor(v.ColorAccent, parseColor(SKIN_DEFAULTS.ColorAccent, [0, 0, 0, 255]));
  const wh = parseColor(v.ColorWhite, parseColor(SKIN_DEFAULTS.ColorWhite, [0, 0, 0, 255]));
  const t = Math.max(0, Math.min(1, num(v, 'CoreWhite', 0.3)));
  out['--core'] = css([0, 1, 2].map((i) => Math.floor(acc[i] + (wh[i] - acc[i]) * t)).concat(255) as RGBA);
  return out;
}
// Glow knobs the skin uses (lib.lua Canvas:neon): halo stroke = w*GlowWidth, alpha = GlowAlpha/255 (outer halo 0.38x, 2.1x wide).
export const num = (v: Record<string, string>, k: string, d: number) => (Number.isFinite(parseFloat(v[k])) ? parseFloat(v[k]) : d);
