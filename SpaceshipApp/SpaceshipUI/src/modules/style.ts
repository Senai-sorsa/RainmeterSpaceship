import type { Style } from '../draw/canvas';
import { num, parseColor, SKIN_DEFAULTS } from '../lib/theme';

/** The draw Style from the settings values, with the defaults H.init uses in Scripts/lib.lua. */
export function styleFrom(v: Record<string, string>): Style {
  const c = (k: string) => parseColor(v[k] ?? SKIN_DEFAULTS[k], [0, 0, 0, 255]);
  return {
    s: num(v, 'Scale', 1), tier: num(v, 'PerfTier', 0), glowA: num(v, 'GlowAlpha', 46), glowW: num(v, 'GlowWidth', 3.2),
    coreWhite: num(v, 'CoreWhite', 0.3), hudA: num(v, 'HudAlpha', 255), edit: num(v, 'EditMode', 0) > 0,
    textGlow: num(v, 'TextGlow', 4), textGlowA: num(v, 'TextGlowAlpha', 150), textSmall: num(v, 'TextScaleSmall', 1.85),
    textLarge: num(v, 'TextScaleLarge', 1.45), fontText: v.FontText || 'Oxanium',
    white: c('ColorWhite'), dim: c('ColorDim'), panel: c('ColorPanel'), accent: c('ColorAccent'), warn: c('ColorWarn'),
    alert: c('ColorAlert'), text: c('ColorText'), hi: c('ColorHighlight'), good: c('ColorGood'),
  };
}
