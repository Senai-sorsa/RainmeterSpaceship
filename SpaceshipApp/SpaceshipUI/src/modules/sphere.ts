import { Canvas, mix, type Op, type Style, type Zone } from '../draw/canvas';
import type { Pt } from '../lib/geometry';

// Port of Skins/Spaceship/@Resources/Scripts/sphere.lua: the tilted disk, the level plane, the orange sweep, the base
// ring and the NET box with its load bar. Not ported: the two sphere sprites (the body is a filled circle here, the
// rim glow is left out), the process blips, the ISS and YOU markers (no host feed), the hover text and the speed-test
// action (an OS action, goes through the action gate later).

const SXR = 2560 / 1260, SYR = 1600 / 709;
const X = (rx: number) => (rx - 514) * SXR;
const Y = (ry: number) => (ry - 407) * SYR;
const CX = ((746 - 514) / 2) * SXR, CY = Y(491), R = 180; // centred in the zone, on the screen axis
/** sphere.lua H.hit 1: the radar disc (Task Manager). shortcut: hit 2, the speed test, is not ported (no host speedtest yet). */
export const SPHERE_HIT = { x: CX - R, y: CY - R, w: 2 * R, h: 2 * R };
const TILT = 0.17, TA = -9; // disk aspect and tilt (degrees)
const FLAT = 0.22; // the level plane's aspect

export type SphereState = { frame: number; rot: number };
export type SphereInput = { downBps?: number; linkDownMbps?: number; testing?: boolean };

export const sphereState = (): SphereState => ({ frame: 0, rot: 0 });

/** An ellipse as a polyline, rotated by rot degrees. Angles in degrees, 0 = right (lib.lua H.ellipsePts). */
export function ellipsePts(cx: number, cy: number, rx: number, ry: number, rot: number, a0 = 0, a1 = 360, segs = 40): Pt[] {
  const cr = Math.cos((rot * Math.PI) / 180), sr = Math.sin((rot * Math.PI) / 180);
  const pts: Pt[] = [];
  for (let i = 0; i <= segs; i++) {
    const a = ((a0 + ((a1 - a0) * i) / segs) * Math.PI) / 180;
    const x = rx * Math.cos(a), y = ry * Math.sin(a);
    pts.push([cx + x * cr - y * sr, cy + x * sr + y * cr]);
  }
  return pts;
}

const clamp = (v: number, a: number, b: number) => Math.max(a, Math.min(b, v));

export function sphereFrame(state: SphereState, input: SphereInput, zone: Zone, st: Style, step = 1): Op[] {
  state.frame += 1;
  state.rot = (state.rot + 1.1 * step) % 360;
  const c = new Canvas(zone, st);
  const A1 = st.accent, W = st.white, O = st.warn;
  const deep = mix(A1, [10, 55, 150, 255], 0.8);
  c.fillCircle(CX, CY, R, deep, 220); // stands in for sphere_body.png
  c.circle(CX, CY, R, A1, 1.2, 90);
  const ey = CY + 6;
  // the level plane: far half behind the tilted disk, near half in front
  c.fillPoly(ellipsePts(CX, ey, R * 0.99, R * 0.99 * FLAT, 0), A1, 14);
  c.poly(ellipsePts(CX, ey, R * 0.99, R * 0.99 * FLAT, 0, 180, 360, 32), A1, 1.6, 120);
  const disk = ellipsePts(CX, ey, R * 0.97, R * 0.97 * TILT, TA, 0, 360, 64);
  c.fillPoly(disk, mix(A1, W, 0.4), 30);
  c.poly(disk, W, 2.2, 235);
  c.poly(ellipsePts(CX, ey, R * 0.42, R * 0.42 * TILT, TA, 0, 360, 36), W, 1.3, 160);
  c.poly(ellipsePts(CX, ey, R * 0.97, R * 0.97 * TILT, TA, state.rot * 1.5, state.rot * 1.5 + 55, 14), O, 3, 235);
  c.poly(ellipsePts(CX, ey, R * 0.99, R * 0.99 * FLAT, 0, 0, 180, 32), mix(A1, W, 0.3), 1.8, 215);
  // base ring under the sphere
  c.poly(ellipsePts(CX, CY + R * 0.9, R * 0.55, R * 0.1, 0, 0, 360, 40), A1, 1.6, 200);
  // NET box: last speed test's download, with the bar showing how much of it is in use now
  const link = input.linkDownMbps ?? 0;
  const testing = input.testing === true;
  const bx0 = X(687), bx1 = X(744), by = Y(541);
  c.text(bx0, Y(536), 'NET', { size: 5.4, weight: 700, align: 'LeftBottom', color: mix(A1, W, 0.3) });
  const dots = '.'.repeat(Math.floor(state.frame / 10) % 4);
  const val = testing ? `TEST${dots}` : link > 0 ? `${link} Mbps` : 'TEST';
  c.text(bx1, Y(536), val, { size: 5.2, weight: 700, align: 'RightBottom', color: testing ? O : W, font: st.fontNum });
  const use = clamp(((input.downBps ?? 0) * 8) / 1000000 / Math.max(1, link > 0 ? link : 200), 0, 1);
  c.hair(bx0, by, bx1, by, W, 1, 120);
  if (use > 0.002) c.line(bx0, by, bx0 + (bx1 - bx0) * Math.max(use, 0.03), by, use > 0.8 ? O : A1, 2.4);
  return c.flush();
}
