import type { Pt } from '../lib/geometry';
import { css } from '../lib/theme';
import type { Op } from './canvas';

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

/** All ops in order. name keeps clip ids unique when several op lists share one page. */
export function OpsView({ ops, name }: { ops: Op[]; name: string }) {
  return <>{ops.map((op, i) => <OpEl key={i} op={op} id={`${name}-${i}`} />)}</>;
}

function OpEl({ op, id }: { op: Op; id: string }) {
  const paint = {
    fill: op.fill ? css(op.fill) : 'none',
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
      const px = sh.size * PT_PX;
      // the skin's Shadow blur is a Direct2D standard deviation; a CSS blur radius is twice that.
      // white-space pre: DirectWrite keeps runs of spaces (the slot's '   LAST  '), SVG would collapse them
      const text = (
        <text x={sh.x} y={sh.y} font-size={px} font-family={sh.font} font-weight={sh.weight} text-anchor={anchor}
          dominant-baseline={base} fill={paint.fill}
          style={sh.blur ? { whiteSpace: 'pre', filter: `drop-shadow(0 0 ${sh.blur * 2}px ${paint.fill})` } : { whiteSpace: 'pre' }}>
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
