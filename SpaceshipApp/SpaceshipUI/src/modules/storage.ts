import { bytes } from './sources';

// Data side of Skins/Spaceship/@Resources/Scripts/storage.lua: drive fill, the activity peak and the readout text.
// The drawing is not ported yet. The drive names and the SSD temperature come in as values.

const GIB = 1073741824;
const MIB = 1048576;
export const PEAK0 = 50 * MIB;

/** Share of the drive in use, 0..1. An empty or unknown drive reads 0. */
export const usedShare = (total: number, free: number) => (total > 0 ? (total - free) / total : 0);

/** storage.lua short(): H.bytes with the spaces taken out, e.g. 1.5MB. */
export const compact = (b: number) => bytes(b).replace(/ /g, '');

/** The activity peak: decays by 2% a redraw and never drops under 1 MiB. */
export const nextPeak = (peak: number, rd: number, wr: number) => Math.max(peak * 0.98, rd, wr, MIB);

/** Drive row text: used and total in whole GB, e.g. 412/931G. */
export const driveText = (total: number, free: number) =>
  `${((total - free) / GIB).toFixed(0)}/${(total / GIB).toFixed(0)}G`;

/** SSD temperature row: a whole number of degrees, or -- when the sensor is not mapped. */
export const ssdText = (ssd?: number) => (ssd === undefined ? '--' : `${ssd.toFixed(0)}C`);

/** The percent beside a bar. Lua's %d truncates, so this does too. */
export const percentText = (share: number) => `${Math.trunc(share * 100)}`;
