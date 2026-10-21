// Sensor readings keyed by the skin's measure names (mCPU, mBattPct, mHwCpuTemp, ...). A missing key is an unavailable sensor.
export type Readings = Partial<Record<string, number>>;

/** H.val: the reading, or the default when it is missing. */
export const val = (r: Readings, name: string, def = 0): number => r[name] ?? def;

/** H.duration: h:mm, or --:-- for no value or a negative one. */
export function duration(sec?: number): string {
  if (sec === undefined || sec < 0) return '--:--';
  const h = Math.floor(sec / 3600), m = Math.floor((sec % 3600) / 60);
  return `${h}:${String(m).padStart(2, '0')}`;
}
