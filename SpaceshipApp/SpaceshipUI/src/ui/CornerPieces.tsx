// Tiny cool-chrome caps on the four screen corners of the "Picture (fitted)" frame only (plan B; the user: "really tiny, only an addition for fitted
// mode"). Canvas units (2560 x 1600) like PictureTrim. Each cap is a small chamfered L bracket hugging the corner, with one rivet, a bright edge and a
// faint accent line on the side that faces the screen. Plain fills and strokes: no filter, no blur, nothing animated.
type Pt = [number, number];

/** Leg length and thickness of a cap, in canvas units. */
export const LEG = 46, THICK = 6;

// the top-left cap; the others are its mirrors
const TL: Pt[] = [[0, 0], [LEG, 0], [LEG - 6, THICK], [THICK + 3, THICK], [THICK, THICK + 3], [THICK, LEG - 6], [0, LEG]];
const INNER: Pt[] = [[LEG - 6, THICK], [THICK + 3, THICK], [THICK, THICK + 3], [THICK, LEG - 6]];
const RIVET: Pt = [THICK / 2, THICK / 2];

const flip = (p: Pt, fx: boolean, fy: boolean): Pt => [fx ? 2560 - p[0] : p[0], fy ? 1600 - p[1] : p[1]];

/** The four caps (outline, screen-facing edge, rivet centre) in canvas units: top-left, top-right, bottom-left, bottom-right. */
export function cornerPieces() {
  return ([[false, false], [true, false], [false, true], [true, true]] as const).map(([fx, fy]) => ({
    outline: TL.map((p) => flip(p, fx, fy)), inner: INNER.map((p) => flip(p, fx, fy)), rivet: flip(RIVET, fx, fy),
  }));
}

const d = (p: Pt[], close = false) => 'M' + p.map(([x, y]) => `${x} ${y}`).join('L') + (close ? 'Z' : '');

export function CornerPieces({ accent }: { accent: string }) {
  return (
    <svg class="frame-parts" data-part="corner-pieces" viewBox="0 0 2560 1600" preserveAspectRatio="none" style={{ position: 'absolute', inset: 0, width: '100%', height: '100%' }}>
      <defs>
        {/* cool chrome: the darkest stop is the art's navy, the brightest its blue-white highlight */}
        <linearGradient id="cp-chrome" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stop-color="#1b2a3b" /><stop offset="0.35" stop-color="#6f8397" /><stop offset="0.5" stop-color="#dbe7f3" />
          <stop offset="0.65" stop-color="#7a8ea3" /><stop offset="1" stop-color="#1f3044" />
        </linearGradient>
      </defs>
      {cornerPieces().map((c, i) => (
        <g key={i}>
          <path d={d(c.outline, true)} fill="url(#cp-chrome)" stroke="#e8f2ff" stroke-opacity="0.55" stroke-width="0.8" stroke-linejoin="round" />
          <path d={d(c.inner)} stroke={accent} stroke-width="4" stroke-opacity="0.14" fill="none" stroke-linecap="round" stroke-linejoin="round" />
          <path d={d(c.inner)} stroke={accent} stroke-width="1" stroke-opacity="0.7" fill="none" stroke-linecap="round" stroke-linejoin="round" />
          <circle cx={c.rivet[0]} cy={c.rivet[1]} r="1.6" fill="#0e1824" stroke="#cfe0f0" stroke-opacity="0.6" stroke-width="0.5" />
        </g>
      ))}
    </svg>
  );
}
