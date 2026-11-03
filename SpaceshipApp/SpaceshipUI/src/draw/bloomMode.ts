/** Where the glow is drawn (tasks/hyperrealism-plan.md D3/D6): one quarter-res light canvas on FULL, the old per-group
 *  SVG blur when BloomEngine=svg, nothing below FULL (only FULL blooms, as before). */
export function bloomMode(tier: number, values: Record<string, string>): 'canvas' | 'svg' | 'off' {
  if (tier >= 1) return 'off';
  return values.BloomEngine === 'svg' ? 'svg' : 'canvas';
}
