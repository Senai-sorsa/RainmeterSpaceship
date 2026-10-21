import { Canvas, type Op, type Style, type Zone } from '../draw/canvas';
import { type RGBA } from '../lib/theme';
import { type Readings, val } from './readings';
import { bytes } from './sources';

// Port of Skins/Spaceship/@Resources/Scripts/storage.lua: the drive screen with the C: and D: fill bars and the
// READ, WRITE and SSD rows. Drive labels are fixed to C: and D: (shortcut: the skin reads Drive1 and Drive2 from settings).
// A missing reading shows -- instead of the skin's 0. The skin's activity peak is computed but never drawn, so it is not kept.
// Click and right click (Explorer, WinDirStat) are not ported.

const GIB = 1073741824;
const SXR = 2560 / 1260, SYR = 1600 / 709;
const X = (rx: number) => (rx - 395) * SXR;
const Y = (ry: number) => (ry - 565) * SYR;

/** Share of the drive in use, 0..1. An empty or unknown drive reads 0. */
export const usedShare = (total: number, free: number) => (total > 0 ? (total - free) / total : 0);

/** storage.lua short(): H.bytes with the spaces taken out, e.g. 1.5MB. */
export const compact = (b: number) => bytes(b).replace(/ /g, '');

/** Drive row text: used and total in whole GB, e.g. 412/931G. */
export const driveText = (total: number, free: number) =>
  `${((total - free) / GIB).toFixed(0)}/${(total / GIB).toFixed(0)}G`;

/** SSD temperature row: a whole number of degrees, or -- when the sensor is not mapped. */
export const ssdText = (ssd?: number) => (ssd === undefined ? '--' : `${ssd.toFixed(0)}C`);

/** The percent beside a bar. Lua's %d truncates, so this does too. */
export const percentText = (share: number) => `${Math.trunc(share * 100)}`;

export type StorageFrame = { ops: Op[]; used: number };

export function storageFrame(r: Readings, zone: Zone, st: Style): StorageFrame {
  const tot = r.mD1Total, free = r.mD1Free ?? 0;
  const t2 = r.mD2Total ?? 0, f2 = r.mD2Free ?? 0;
  const used = usedShare(tot ?? 0, free), used2 = usedShare(t2, f2);
  const c = new Canvas(zone, st);
  const A1 = st.accent, W = st.white, D = st.dim;
  const rows: [number, string, string, RGBA][] = [
    [584, 'C:', tot === undefined ? '--' : driveText(tot, free), W],
    [600, 'READ', r.mRead === undefined ? '--' : compact(r.mRead), W],
    [616, 'WRITE', r.mWrite === undefined ? '--' : compact(r.mWrite), W],
    [627, 'SSD', ssdText(r.mHwSsdTemp), D],
  ];
  for (const [ry, label, value, col] of rows) {
    const y = Y(ry);
    c.line(X(402), y, X(405), y, col, 1.4);
    c.dot(X(407), y, 2.2, col);
    c.text(X(410), y, `${label}  ${value}`, { size: 4.4, weight: 700, align: 'LeftCenter', color: col, clip: X(455) - X(410) });
  }
  // two vertical bars (C, D) with the letter under each
  const top = Y(578), bot = Y(620);
  for (const b of [{ rx: 462, share: used, label: 'C:' }, { rx: 471, share: used2, label: t2 > 0 ? 'D:' : '--' }]) {
    const x = X(b.rx);
    c.hair(x, top, x, bot, D, 3, 140);
    c.line(x, bot, x, bot - (bot - top) * b.share, A1, 3.4);
    c.text(x, Y(625), b.label.slice(0, 1), { size: 4.6, weight: 700, align: 'CenterCenter', color: W });
  }
  c.text(X(458), Y(596), tot === undefined ? '--' : percentText(used), { size: 4.6, weight: 700, align: 'RightCenter', color: W });
  c.text(X(458), Y(604), t2 > 0 ? percentText(used2) : '', { size: 4.6, weight: 700, align: 'RightCenter', color: D });
  return { ops: c.flush(), used };
}
