import { Canvas, type Op, type Style, type Zone } from '../draw/canvas';

// Port of Skins/Spaceship/@Resources/Scripts/power.lua: the power draw in the top-left bar. Sensor values come in as plain
// numbers (undefined when there is no reading). The frame is returned, not drawn, and the click (TopModule.tsx) opens the Control Center in place of a Rainmeter config.

export type PowerInput = { cpu?: number; gpu?: number; chargeRate?: number };
export type PowerFrame = { ops: Op[]; watts: number; tip: string };

const HWINFO_HINT = 'Power draw needs HWiNFO: Control Center > SENSORS > DETECT';

/** CPU plus GPU when either reads; otherwise battery discharge counts as draw. Lua's 0 is truthy, so 0 W is a reading. */
function watts(inp: PowerInput): number | undefined {
  if (inp.cpu !== undefined || inp.gpu !== undefined) return (inp.cpu ?? 0) + (inp.gpu ?? 0);
  if (inp.chargeRate !== undefined && inp.chargeRate < 0) return -inp.chargeRate;
  return undefined;
}

const fmt = (n?: number) => (n === undefined ? '--' : n.toFixed(0));

export function powerFrame(inp: PowerInput, zone: Zone, st: Style): PowerFrame {
  const c = new Canvas(zone, st);
  const w = watts(inp);
  const v = w !== undefined ? Math.min(1, Math.max(0, w / 160)) : 0;
  const y = zone.h * 0.5, x0 = 22, x1 = zone.w - 26, xv = x0 + (x1 - x0) * v;
  // letter, thin rail, hot segment, end tick, readout
  c.text(0, y, 'P', { size: 8.5, weight: 700, align: 'LeftCenter', color: st.white });
  c.line(x0, y, x1, y, st.white, 1.3, 210);
  if (v > 0) c.line(x0, y, xv, y, st.hi, 2.6);
  c.line(xv, y - 6, xv, y + 2, st.white, 1.3);
  c.text(zone.w, y, w !== undefined ? `${w.toFixed(0)}W` : 'W', { size: 8.5, weight: 700, align: 'RightCenter', color: st.white });
  const tip = w !== undefined ? `CPU ${fmt(inp.cpu)} W, GPU ${fmt(inp.gpu)} W` : HWINFO_HINT;
  return { ops: c.flush(), watts: w ?? 0, tip };
}
