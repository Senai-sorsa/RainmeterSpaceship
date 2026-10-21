// Data side of Skins/Spaceship/@Resources/Scripts/strip.lua: the warn levels and the compact rate text of the bottom strip.
// The drawing is not ported yet.

/** 0 normal, 1 warn (within the margin of the limit), 2 alert (over the limit). A missing value is normal. */
export function level(v: number | undefined, limit: number, margin: number): 0 | 1 | 2 {
  if (v === undefined) return 0;
  if (v >= limit) return 2;
  if (v >= limit - margin) return 1;
  return 0;
}

/** strip.lua short(): a per-second rate that fits a cell, e.g. 820B/s, 4.1KB/s, 47KB/s, 312MB/s. */
export function rateShort(bytesPerSec: number): string {
  const units = ['B', 'KB', 'MB', 'GB'];
  let b = bytesPerSec, i = 0;
  while (b >= 1000 && i < units.length - 1) { b /= 1024; i++; }
  // Lua's index starts at 1 for B, so the decimal rule is i > 1 here (KB and up), and a value under 10
  return i > 0 && b < 10 ? `${b.toFixed(1)}${units[i]}/s` : `${b.toFixed(0)}${units[i]}/s`;
}
