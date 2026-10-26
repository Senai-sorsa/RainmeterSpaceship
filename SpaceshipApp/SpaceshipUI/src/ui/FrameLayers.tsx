import manifest from '../generated/frame/manifest.json';
import parts from '../generated/frameparts.json';
import { useMemo } from 'preact/hooks';
import type { FrameStyle } from '../settings/frameStyle';
import { partShapes } from './frameParts';

const urls = import.meta.glob('../generated/frame/*.png', { eager: true, query: '?url', import: 'default' }) as Record<string, string>;
const url = (name: string) => urls[`../generated/frame/${(manifest as Record<string, string>)[name]}`];

const n = (v: Record<string, string>, k: string, d: number) => { const x = Number(v[k]); return Number.isFinite(x) ? x : d; };
const alpha = (x: number) => Math.min(255, Math.max(0, x)) / 255;
const fill = { position: 'absolute', inset: 0, backgroundSize: '100% 100%' } as const;

/** Frame.ini's cockpit, as stacked layers in the skin's drawing order. Alpha formulas are the skin's (GlassGlare*21, ScanAlpha*18, ...). */
export function FrameLayers({ style, values }: { style: FrameStyle; values: Record<string, string> }) {
  if (style === 'none') return null;
  const pic = style === 'picture';
  const rgb = String(values.ColorAccent ?? '').split(',').slice(0, 3).map((x) => Math.min(255, Math.max(0, Number(x) || 0))).join(',');
  const accent = `rgb(${rgb})`;
  const bright = `brightness(${Math.min(100, Math.max(0, n(values, 'FrameBrightness', 25))) / 100})`;
  const hull = alpha(n(values, 'HullAlpha', 255));
  const img = (name: string, a: number, extra: Record<string, string> = {}) => (
    <div class="frame-layer" data-layer={name} style={{ ...fill, backgroundImage: `url(${url(name)})`, opacity: a, ...extra }} />
  );
  // tint layers: the image only supplies the shape (mask); the colour is the live accent, like ImageTint=#ColorAccent#
  const tint = (name: string, a: number, mode: 'alpha' | 'luminance', bg: string) => (
    <div class="frame-layer" data-layer={name} style={{ ...fill, background: bg, opacity: a, maskImage: `url(${url(name)})`, maskSize: '100% 100%', maskMode: mode, WebkitMaskImage: `url(${url(name)})`, WebkitMaskSize: '100% 100%' }} />
  );
  const tintA = n(values, 'GlassTint', 66);
  const scan = values.ScanLines === '1';
  // Frame.ini's Shape parts: Glass under everything (rendered only), Accents/Spill/Lights/Decor over it (Decor in both styles)
  const vars = { ...values, ColorAccent: rgb };
  return (
    // the skin draws the frame at 2560*Scale logical px from the screen's top-left (0.67 overhangs a 150 % screen by
    // ~0.5 %), where the modules sit too; Hud passes Scale already divided by the fit, so 1 means "fills the window"
    <div class="frame" data-frame={style} aria-hidden="true" style={{ width: `calc(min(100vw, 160vh) * ${n(values, 'Scale', 1)})` }}>
      {pic ? tint('glass_pic', alpha(tintA), 'alpha', accent) : <Parts names={['Glass']} vars={vars} />}
      {img(pic ? 'glass_fx_pic' : 'glass_fx', alpha(n(values, 'GlassGlare', 12) * 21))}
      {scan && img(pic ? 'scan_pic' : 'scan', alpha(n(values, 'ScanAlpha', 6) * 18))}
      {img('shade', alpha(n(values, 'ShadeAlpha', 155)))}
      {img(pic ? 'ship' : 'hull', hull, { filter: bright })}
      {tint(pic ? 'mist_pic' : 'mist', alpha(n(values, 'MistAlpha', 255)), 'alpha', accent)}
      {!pic && img('corners', hull, { filter: bright })}
      <Parts names={pic ? ['Decor'] : ['Accents', 'Spill', 'Lights', 'Decor']} vars={vars} />
    </div>
  );
}

const PARTS = parts as unknown as Record<string, [string, Record<string, string>][]>;

/** The named Parts/*.inc sections as one SVG in the canvas units, stretched over the frame like the layer images. */
function Parts({ names, vars }: { names: string[]; vars: Record<string, string> }) {
  const key = names.join();
  // only the variables the parts read, so a clock tick or an unrelated setting does not rebuild a hundred shapes
  const deps = ['ColorAccent', 'GlowAlpha', 'GlowWidth', 'CoreWhite', 'GlassTint'].map((k) => vars[k]);
  const shapes = useMemo(() => names.flatMap((p) => (PARTS[`${p}.inc`] ?? []).flatMap(([, sec]) => partShapes(sec, vars))), [key, ...deps]);
  return (
    <svg class="frame-parts" data-part={key} viewBox="0 0 2560 1600" preserveAspectRatio="none" style={{ position: 'absolute', inset: 0, width: '100%', height: '100%' }}>
      {shapes.map((s, i) => {
        const id = `fp-${key}-${i}`;
        const fill = typeof s.fill === 'string' ? s.fill : `url(#${id})`;
        const common = { fill, stroke: s.stroke, 'stroke-width': s.width, 'stroke-linejoin': s.join };
        return (
          <g key={i}>
            {typeof s.fill !== 'string' && (
              <linearGradient id={id} x1={s.fill.x1} y1={s.fill.y1} x2={s.fill.x2} y2={s.fill.y2}>
                {s.fill.stops.map((st) => <stop key={st.off} offset={st.off} stop-color={st.color} />)}
              </linearGradient>
            )}
            {s.kind === 'ellipse' ? <ellipse {...s.geo} {...common} /> : s.kind === 'rect' ? <rect {...s.geo} {...common} /> : <path {...s.geo} {...common} />}
          </g>
        );
      })}
    </svg>
  );
}
