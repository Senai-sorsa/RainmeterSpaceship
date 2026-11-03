import type { JSX } from 'preact';
import type { Pt } from '../lib/geometry';
import { css } from '../lib/theme';
import { FONT_SCALE, HUD_SCAN, type Grad, type Op } from './canvas';

// Draws Canvas ops as SVG. Canvas already scales the shapes to device units, so the caller only wraps the group in the zone matrix.

export const pathD = (pts: Pt[], closed: boolean) => pts.map(([x, y], i) => `${i ? 'L' : 'M'}${x} ${y}`).join('') + (closed ? 'Z' : '');

/** Rainmeter's FontSize is in points; DirectWrite draws it at 96 DPI, so 1 pt is 4/3 px (svg units are skin pixels). */
export const PT_PX = 4 / 3;


/** Lua alignment such as 'RightCenter' to SVG text-anchor and dominant-baseline. Rainmeter aligns the line box, not the baseline. */
export function textAlign(align: string): { anchor: string; base: string } {
  const anchor = align.startsWith('Right') ? 'end' : align.startsWith('Center') ? 'middle' : 'start';
  const base = align.endsWith('Center') ? 'central' : align.endsWith('Bottom') ? 'text-after-edge' : 'text-before-edge';
  return { anchor, base };
}

/** Shared paint servers for the HUD svg, defined once (K4): a faint horizontal scan texture for display glass.
 *  Static (no animation); its lines are 1 unit every 3 svg units at 4.5 % white so text on top stays crisp. */
export function HudDefs() {
  return (
    <defs>
      <pattern id={HUD_SCAN} patternUnits="userSpaceOnUse" width="3" height="3">
        <rect x="0" y="0" width="3" height="1" fill="rgb(255,255,255)" fill-opacity="0.045" />
      </pattern>
    </defs>
  );
}

/** One gradient element for an op (userSpaceOnUse: its coordinates are the op's device units). */
function GradDef({ g, id }: { g: Grad; id: string }) {
  const stops = g.stops.map(([o, c], i) => <stop key={i} offset={o} stop-color={`rgb(${c[0]},${c[1]},${c[2]})`} stop-opacity={c[3] / 255} />);
  return g.kind === 'linear'
    ? <linearGradient id={id} gradientUnits="userSpaceOnUse" x1={g.x1} y1={g.y1} x2={g.x2} y2={g.y2}>{stops}</linearGradient>
    : <radialGradient id={id} gradientUnits="userSpaceOnUse" cx={g.cx} cy={g.cy} r={g.r}>{stops}</radialGradient>;
}

/** All ops in order. name keeps clip ids unique when several op lists share one page. */
export function OpsView({ ops, name }: { ops: Op[]; name: string }) {
  // a run of bloom ops (the glow layer on FULL) is drawn as one blurred group: one filter pass per module, not per line
  const out: JSX.Element[] = [];
  for (let i = 0; i < ops.length; ) {
    const b = ops[i].bloom;
    // a shimmer op is keyed by its value, so a new value mounts a new element and its CSS flicker plays once
    if (!b) { const sh = ops[i].shimmer; out.push(sh === undefined ? <OpEl key={i} op={ops[i]} id={`${name}-${i}`} /> : <g key={`${i}~${sh}`} class="shimmer"><OpEl op={ops[i]} id={`${name}-${i}`} /></g>); i++; continue; }
    const run: JSX.Element[] = [];
    const start = i;
    for (; i < ops.length && ops[i].bloom === b; i++) run.push(<OpEl key={i} op={ops[i]} id={`${name}-${i}`} />);
    out.push(<g key={`b${start}`} class="bloom" style={{ filter: `blur(${b}px)` }}>{run}</g>);
  }
  return <>{out}</>;
}

function OpEl({ op, id }: { op: Op; id: string }) {
  // plain ops return the svg element itself (no wrapper), exactly as before the gradient fills existed
  if (op.grad) return <><defs><GradDef g={op.grad} id={`gr-${id}`} /></defs>{Shape({ op, id, fill: `url(#gr-${id})` })}</>;
  if (op.pattern) return Shape({ op, id, fill: `url(#${op.pattern})` });
  return Shape({ op, id });
}

function Shape({ op, id, fill }: { op: Op; id: string; fill?: string }) {
  const paint = {
    fill: fill ?? (op.fill ? css(op.fill) : 'none'),
    stroke: op.stroke ? css(op.stroke.color) : undefined,
    'stroke-width': op.stroke?.width,
    'stroke-dasharray': op.stroke?.dash?.join(' '),
  };
  const sh = op.shape;
  switch (sh.kind) {
    case 'poly':
      return <path d={pathD(sh.pts, sh.closed)} {...paint} stroke-linecap="round" stroke-linejoin="round" />;
    case 'ellipse':
      return <ellipse cx={sh.cx} cy={sh.cy} rx={sh.rx} ry={sh.ry} {...paint} />;
    case 'rect':
      return <rect x={sh.x} y={sh.y} width={sh.w} height={sh.h} rx={sh.r} {...paint} />;
    case 'text': {
      const { anchor, base } = textAlign(sh.align);
      const px = sh.size * PT_PX * (FONT_SCALE[sh.font] ?? 1);
      // the skin's Shadow blur is a Direct2D standard deviation, as CSS blur() takes it. The glow copy is only the blurred
      // halo: drop-shadow would also paint the letters, and two anti-aliased copies make every glyph look bold
      // white-space pre: DirectWrite keeps runs of spaces (the slot's '   LAST  '), SVG would collapse them
      // the skin asks for FontWeight 600/700, but Rainmeter draws its bundled fonts at the regular weight (checked
      // against the user's screenshot of 2026-10-26), so the weight is not applied
      const text = (
        <text x={sh.x} y={sh.y} font-size={px} font-family={sh.font} font-weight={FONT_SCALE[sh.font] ? sh.weight : 400} text-anchor={anchor}
          dominant-baseline={base} fill={paint.fill}
          style={sh.blur ? { whiteSpace: 'pre', filter: `blur(${sh.blur}px)` } : { whiteSpace: 'pre' }}>
          {sh.text}
        </text>
      );
      if (sh.clipW === undefined) return text;
      // clip-path on a clipped text: the box runs from the text anchor, back for right-aligned and centred text
      const left = anchor === 'end' ? sh.x - sh.clipW : anchor === 'middle' ? sh.x - sh.clipW / 2 : sh.x;
      return (
        <g clip-path={`url(#clip-${id})`}>
          <clipPath id={`clip-${id}`}><rect x={left} y={sh.y - px} width={sh.clipW} height={px * 2} /></clipPath>
          {text}
        </g>
      );
    }
    case 'image':
      // sRGB: Rainmeter's colour matrix works on the stored values, not linear light
      return (
        <>
          <filter id={`cm-${id}`} color-interpolation-filters="sRGB"><feColorMatrix type="matrix" values={sh.matrix.join(' ')} /></filter>
          <image href={sh.href} x={sh.x} y={sh.y} width={sh.w} height={sh.h} preserveAspectRatio="none" filter={`url(#cm-${id})`} />
        </>
      );
  }
}
