// The glass backing slab behind each bottom info panel (B_panelL, B_panelR). The skin's Decor draws them as four fixed paths (P39/P40 left, P41/P42 right)
// whose corners were set for an older panel size: the right slab's top edge sat on the panel's but its sides ran about 50 units past the panel's bottom
// (the pale plate hanging under the TERMINAL button), and the left one was a few units off the card. Here the slab is computed from the panel's own zone,
// so it hugs the card exactly, in every frame mode and wherever the panel sits. CSpace only: the skin's Decor.inc is not touched.

export type SlabZone = { id?: string; x: number; y: number; w: number; h: number; matrix: number[] };

// the skin's original slab paths (exact text from Decor.inc, mirrored left/right); only a section that still has them is rewritten
const ORIGINAL = {
  B_panelL: { keys: ['P39', 'P40'], text: '604.0,1381.1 | LineTo 692.8,1345.0 | LineTo 731.4,1566.1 | LineTo 646.1,1600.0 | ClosePath 1' },
  B_panelR: { keys: ['P41', 'P42'], text: '1956.0,1381.1 | LineTo 1867.2,1345.0 | LineTo 1828.6,1566.1 | LineTo 1913.9,1600.0 | ClosePath 1' },
} as const;

/** The zone's rectangle grown by pad (zone units) on every side, through the zone's matrix, in the skin's vertex order: top-right, top-left, bottom-left, bottom-right. */
export function slabPath(z: SlabZone, pad = 7): string {
  const [a, b, c, d, e, f] = z.matrix;
  const P = (x: number, y: number) => `${(a * x + c * y + e).toFixed(1)},${(b * x + d * y + f).toFixed(1)}`;
  const x0 = z.x - pad, y0 = z.y - pad, x1 = z.x + z.w + pad, y1 = z.y + z.h + pad;
  return `${P(x1, y0)} | LineTo ${P(x0, y0)} | LineTo ${P(x0, y1)} | LineTo ${P(x1, y1)} | ClosePath 1`;
}

/** The slab's corners in canvas units (the same four points slabPath draws). */
function slabCorners(z: SlabZone, pad = 7): [number, number][] {
  const [a, b, c, d, e, f] = z.matrix;
  const x0 = z.x - pad, y0 = z.y - pad, x1 = z.x + z.w + pad, y1 = z.y + z.h + pad;
  return [[x1, y0], [x0, y0], [x0, y1], [x1, y1]].map(([x, y]) => [a * x + c * y + e, b * x + d * y + f]);
}

/** Where the bottom console's cut-out in the fitted Decor clip may start and end: the left slab's right-most corner and the right slab's left-most one, so the
 *  slabs (which reach into the console's x range, 700..1860) keep all four corners. Falls back to the console's own edges. */
export function consoleCutout(zones: SlabZone[], left = 700, right = 1860): { left: number; right: number } {
  const edge = (id: string, pick: (xs: number[]) => number, fallback: number) => {
    const z = zones.find((q) => q.id === id);
    return z && z.matrix.length === 6 ? pick(slabCorners(z).map((p) => p[0])) : fallback;
  };
  return { left: Math.max(left, edge('B_panelL', (xs) => Math.max(...xs), left)), right: Math.min(right, edge('B_panelR', (xs) => Math.min(...xs), right)) };
}

/** The Decor section with the two slabs rebuilt from the panels' zones. A section without the skin's original slab paths, or a missing zone, is left as it is. */
export function fixPanelSlabs<S extends Record<string, string>>(sec: S, zones: SlabZone[]): S {
  let out: Record<string, string> | null = null;
  for (const [id, { keys, text }] of Object.entries(ORIGINAL)) {
    const z = zones.find((q) => q.id === id);
    if (!z || z.matrix.length !== 6 || !keys.every((k) => String(sec[k] ?? '').trim() === text)) continue;
    out ??= { ...sec };
    for (const k of keys) out[k] = slabPath(z);
  }
  return (out ?? sec) as S;
}

// A small decor icon at about canvas (640, 840), a circle with a gap and an arrow inside it (Shape43..Shape50 of the skin's Decor.inc: four stroke layers each for
// the arc P43..P46 and the chevron P47..P50). It does not belong to any module and does nothing; the user asked for it gone (live test, 2026-11-04).
const STRAY_ICON = [43, 44, 45, 46, 47, 48, 49, 50];
const BLANK = 'Rectangle 0,0,0,0 | Fill Color 0,0,0,0 | StrokeWidth 0'; // the skin's own no-op shape (Shape33..Shape38)

/** The Decor section with the stray icon's eight shapes blanked (not deleted: the shape list is walked in order and must stay unbroken). A section whose
 *  Shape43..Shape50 are not the icon's paths is left as it is. */
export function blankStrayIcon<S extends Record<string, string>>(sec: S): S {
  const isIcon = (n: number) => new RegExp(`^\\s*Path P${n}\\b`).test(String(sec['Shape' + n] ?? ''));
  if (!STRAY_ICON.every(isIcon)) return sec;
  const out: Record<string, string> = { ...sec };
  for (const n of STRAY_ICON) out['Shape' + n] = BLANK;
  return out as S;
}
