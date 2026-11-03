import layout from '../generated/layout.json';
import { transformBox, type Matrix } from '../lib/geometry';

// Realism kit K6: lit screens throw light on the hull around them. One static layer of soft radial pools, one per lit
// feature, drawn with screen blend and masked to the hull (never the window glass) by FrameLayers. FULL and LITE only.

/** The lit features and how strongly each spills (percent of the accent at the pool's centre). */
export const SPILL: Record<string, number> = {
  G1_cpu: 9, G2_select: 9, G3_select: 9, G4_ram: 9, L_location: 7, R_sysinfo: 7,
  B_storage: 11, B_audio: 11, B_panelL: 8, B_panelR: 8, C_sphere: 13,
};

type Z = { id: string; x: number; y: number; w: number; h: number; matrix: number[] };

/** CSS background for the spill layer: radial pools at each visible feature's centre, in percent of the canvas. Empty on
 *  LOW and STEALTH (tier >= 2). hide is the comma list from hiddenZones(). */
export function spillBackground(accent: string, tier: number, hide = ''): string {
  if (tier >= 2) return '';
  const off = new Set(hide.split(',').filter(Boolean)), { w: CW, h: CH } = layout.canvas;
  return (layout.zones as Z[])
    .filter((z) => SPILL[z.id] && !off.has(z.id))
    .map((z) => {
      const q = transformBox(z.matrix as Matrix, z.x, z.y, z.w, z.h);
      const cx = q.reduce((s, p) => s + p[0], 0) / q.length, cy = q.reduce((s, p) => s + p[1], 0) / q.length;
      const rx = (z.w * 0.75 / CW) * 100, ry = (z.h * 0.9 / CH) * 100;
      return `radial-gradient(${rx.toFixed(2)}% ${ry.toFixed(2)}% at ${(cx / CW * 100).toFixed(2)}% ${(cy / CH * 100).toFixed(2)}%, color-mix(in srgb, ${accent} ${SPILL[z.id]}%, transparent), transparent 100%)`;
    })
    .join(', ');
}
