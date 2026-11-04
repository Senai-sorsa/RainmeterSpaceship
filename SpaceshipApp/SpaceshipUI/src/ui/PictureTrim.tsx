// The lit cyan trim of the "Picture (fitted)" frame at the top: lines traced on ship.png's own slot edges (canvas units, 2560 x 1600; measured on the
// picture with a labelled grid), so the HUD's glow lies on the art's grooves instead of running a few pixels beside them. The HUD's own top trim (the
// Decor shapes drawn for the line-art hull) is hidden above y 330 in this mode (FrameLayers).
//
//   groove     the long groove under the top plate, y 103, with the plate's chamfered steps up to y 50
//   roofs      the roofs of the two centre pockets: a chamfer up from the band, the flat roof at y 143, a chamfer down
//   wing lines the lit edge of the wing beam and the line above each wing slot
//   divider    the post between the two centre pockets
//
// Left half only; the right half is its mirror about x = 1280. Plain strokes (a wide faint one and a thin bright one): no filter, no blur.
type Pts = [number, number][];

const LEFT: Pts[] = [
  [[985, 50], [1040, 103], [1280, 103]], // groove
  [[900, 172], [935, 143], [1190, 143], [1255, 181]], // centre pocket roof
  [[600, 92], [700, 106], [810, 127], [865, 151]], // wing beam
  [[700, 159], [900, 172]], // wing slot top
];
const JOINTS: [number, number][] = [[1040, 103], [935, 143], [1190, 143], [900, 172], [865, 151]];
const DIVIDER: Pts = [[1280, 108], [1280, 232]];

const d = (p: Pts) => 'M' + p.map(([x, y]) => `${x} ${y}`).join('L');

export function PictureTrim({ accent, tier }: { accent: string; tier: number }) {
  const half = (
    <>
      {tier < 2 && LEFT.map((p, i) => <path key={'g' + i} d={d(p)} stroke={accent} stroke-width="9" stroke-opacity="0.13" fill="none" stroke-linecap="round" stroke-linejoin="round" />)}
      {LEFT.map((p, i) => <path key={'c' + i} d={d(p)} stroke={accent} stroke-width="2.4" stroke-opacity="0.78" fill="none" stroke-linecap="round" stroke-linejoin="round" />)}
      {JOINTS.map(([x, y], i) => <circle key={'j' + i} cx={x} cy={y} r="3.2" fill={accent} fill-opacity="0.9" />)}
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
