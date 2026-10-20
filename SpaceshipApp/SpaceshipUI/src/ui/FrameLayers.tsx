import manifest from '../generated/frame/manifest.json';
import type { FrameStyle } from '../settings/frameStyle';

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
  // shortcut: Rainmeter fades each window shape on its own; this fades the whole frame top to bottom. Upgrade if the per-window look matters.
  const glassGrad = `linear-gradient(to bottom, rgb(${rgb} / ${Math.min(255, tintA * 0.75) / 255}), rgb(${rgb} / ${(tintA * 0.12) / 255}) 55%, rgb(${rgb} / ${Math.min(255, tintA * 0.3) / 255}))`;
  const scan = values.ScanLines === '1';
  return (
    <div class="frame" data-frame={style} aria-hidden="true">
      {pic ? tint('glass_pic', alpha(tintA), 'alpha', accent) : tint('window_mask', 1, 'luminance', glassGrad)}
      {img(pic ? 'glass_fx_pic' : 'glass_fx', alpha(n(values, 'GlassGlare', 12) * 21))}
      {scan && img(pic ? 'scan_pic' : 'scan', alpha(n(values, 'ScanAlpha', 6) * 18))}
      {img('shade', alpha(n(values, 'ShadeAlpha', 155)))}
      {img(pic ? 'ship' : 'hull', hull, { filter: bright })}
      {tint(pic ? 'mist_pic' : 'mist', alpha(n(values, 'MistAlpha', 255)), 'alpha', accent)}
      {!pic && img('corners', hull, { filter: bright })}
    </div>
  );
}
