import curveJson from '../generated/curve.json';
import type { Pt } from '../lib/geometry';

// Task 10: the long HUD elements (strip, console line, rails) follow the rendered shell's curve. The table is
// tools/frame_src/curve.json: zones[id] = sag in canvas units (positive = the middle sags down, negative = rises).
export type Warp = (p: Pt) => Pt;
export type Curve = { zones: Record<string, number> };
export const CURVE = curveJson as unknown as Curve;

/** y' = y + sag * (1 - (2x/w - 1)^2) in zone units: the ends stay, the middle moves by the sag. */
export function bendFor(zoneId: string | undefined, zone: { w: number }, curve: Curve = CURVE): Warp | undefined {
  const sag = zoneId ? curve.zones[zoneId] : 0;
  if (!sag || !(zone.w > 0)) return undefined;
  return ([x, y]) => {
    const u = 2 * x / zone.w - 1;
    return [x, y + sag * Math.max(0, 1 - u * u)];
  };
}

/** The points of a polyline, with every segment longer than `step` split first so a straight run can bend. */
export function warpPoly(pts: Pt[], warp: Warp, step = 40): Pt[] {
  const out: Pt[] = [];
  pts.forEach((p, i) => {
    const q = pts[i - 1];
    if (q) {
      const n = 2 * Math.ceil(Math.hypot(p[0] - q[0], p[1] - q[1]) / (2 * step)); // even, so a centred peak is sampled
      for (let k = 1; k < n; k++) out.push(warp([q[0] + (p[0] - q[0]) * k / n, q[1] + (p[1] - q[1]) * k / n]));
    }
    out.push(warp(p));
  });
  return out;
}
