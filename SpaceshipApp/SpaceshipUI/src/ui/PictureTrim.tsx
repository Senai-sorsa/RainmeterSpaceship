// The lit cyan trim of the "Picture (fitted)" frame at the top: lines traced on ship.png's own slot edges (canvas units, 2560 x 1600; measured on the
// picture with a labelled grid), so the HUD's glow lies on the art's grooves instead of running a few pixels beside them. The HUD's own top trim (the
// Decor shapes drawn for the line-art hull) is hidden above y 330, and across the bottom console (x 700..1860, y > 1380), in this mode (FrameLayers).
//
//   groove     the long groove under the top plate, y 103, with the plate's chamfered step up to y 62
//   roofs      the roofs of the two centre pockets: a chamfer up from the band, the flat roof at y 143, a chamfer down
//   wing lines the lit edge of the wing beam and the line above each wing slot
//   divider    the post between the two centre pockets
//   console    the bottom console's curved band as ONE smooth outline (top edge, chamfered end, bottom edge; corners rounded) and the groove that runs on from
//              it to the corner; no node dots on any line (live test, 2026-11-05)
//
// Left half only; the right half is its mirror about x = 1280. Plain strokes (a wide faint one and a thin bright one): no filter, no blur.
type Pts = [number, number][];

const d = (p: Pts) => 'M' + p.map(([x, y]) => `${x} ${y}`).join('L');

/** y = yc + drop * ((1280 - x) / half)^2: the console band's top edge is an arch, symmetric about x 1280. */
const archY = (x: number, yc: number, drop: number, half: number) => yc + drop * ((1280 - x) / half) ** 2;

/** 0 at x = from, 1 at x 1280, with a flat end there: the offsets below ease in from the chamfer and meet their mirror without a kink in the middle. */
const ease = (x: number, from: number) => { const t = Math.min(1, Math.max(0, (x - from) / (1280 - from))); return 1 - (1 - t) ** 2; };

/** The console band's top edge, measured on ship.png, raised a little (live test, 2026-11-05: it sat inside the rim), easing in from the chamfer. */
const TOP_RISE = 6;
const topEdge = (): Pts => { const out: Pts = []; for (let x = 850; x < 1280; x += 60) out.push([x, +(archY(x, 1458, 32, 490) - TOP_RISE * ease(x, 790)).toFixed(1)]); out.push([1280, 1458 - TOP_RISE]); return out; };

/** The measured bottom edge of the band (lit pixels, canvas units; it sits 4 units under a parabola near x 920), lowered in the middle (it sat inside the rim there). */
const BOTTOM_DROP = 8;
const BOTTOM_EDGE: Pts = [[750, 1587], [800, 1578], [860, 1570], [920, 1564], [980, 1559], [1040, 1553], [1100, 1547], [1160, 1543], [1220, 1539], [1280, 1537.5]]
  .map(([x, y]) => [x, +(y + BOTTOM_DROP * ease(x, 700)).toFixed(1)] as [number, number]);

/** The band as ONE outline, from the middle of the top edge, out along it, round the knee, down the chamfer, round the foot and back along the bottom edge to the middle.
 *  Its corners are rounded (roundedPath) so it reads as a single smooth shape, not as separate lines. */
const BAND: Pts = [...topEdge().reverse(), [772, 1493], [748, 1516], [720, 1545], [700, 1572], [676, 1599], ...BOTTOM_EDGE];
/** The groove that runs on from the chamfer to the screen corner, joined to the band's rim where the chamfer starts. */
const GROOVE: Pts = [[362, 1600], [430, 1585], [500, 1570], [600, 1548], [700, 1523], [746, 1517]];

/** The polyline with every corner rounded by a quadratic curve that starts and ends up to r before it (never more than half a segment, so neighbours cannot overlap). */
export const roundedPath = (p: Pts, r: number): string => {
  if (p.length < 3) return d(p);
  let out = `M${p[0][0]} ${p[0][1]}`;
  for (let i = 1; i < p.length - 1; i++) {
    const [px, py] = p[i - 1], [x, y] = p[i], [nx, ny] = p[i + 1];
    const l1 = Math.hypot(x - px, y - py), l2 = Math.hypot(nx - x, ny - y);
    const k1 = Math.min(r, l1 / 2) / l1, k2 = Math.min(r, l2 / 2) / l2;
    out += `L${(x - (x - px) * k1).toFixed(1)} ${(y - (y - py) * k1).toFixed(1)}Q${x} ${y} ${(x + (nx - x) * k2).toFixed(1)} ${(y + (ny - y) * k2).toFixed(1)}`;
  }
  const [lx, ly] = p[p.length - 1];
  return out + `L${lx} ${ly}`;
};

const LEFT: Pts[] = [
  [[900, 172], [935, 143], [1190, 143], [1255, 181]], // centre pocket roof
  [[600, 92], [700, 106], [810, 127], [865, 151]], // wing beam
  [[700, 159], [900, 172]], // wing slot top
];
// the top groove: 115 degree inside corner (slant 65 from the groove), lowered 2 more on 2026-11-08 and 2 again, corner rounded
const SMOOTH: string[] = [roundedPath(BAND, 24), roundedPath(GROOVE, 30), roundedPath([[1031, 66], [1050, 107], [1280, 107]], 18)];
const DIVIDER: Pts = [[1280, 108], [1280, 232]];


export function PictureTrim({ accent, tier }: { accent: string; tier: number }) {
  const half = (
    <>
      {tier < 2 && [...LEFT.map(d), ...SMOOTH].map((p, i) => <path key={'g' + i} d={p} stroke={accent} stroke-width="9" stroke-opacity="0.13" fill="none" stroke-linecap="round" stroke-linejoin="round" />)}
      {[...LEFT.map(d), ...SMOOTH].map((p, i) => <path key={'c' + i} d={p} stroke={accent} stroke-width="2.4" stroke-opacity="0.78" fill="none" stroke-linecap="round" stroke-linejoin="round" />)}
    </>
  );
  return (
    <svg class="frame-parts" data-part="fitted-trim" viewBox="0 0 2560 1600" preserveAspectRatio="none" style={{ position: 'absolute', inset: 0, width: '100%', height: '100%' }}>
      {half}
      <g transform="translate(2560 0) scale(-1 1)">{half}</g>
      <path d={d(DIVIDER)} stroke={accent} stroke-width="1.6" stroke-opacity="0.5" fill="none" />
    </svg>
  );
}
