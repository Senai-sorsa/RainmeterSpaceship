import type { JSX } from 'preact';
import manifest from '../generated/frame/manifest.json';
import parts from '../generated/frameparts.json';
import { useMemo } from 'preact/hooks';
import type { FrameStyle } from '../settings/frameStyle';
import { partShapes } from './frameParts';
import { orbLightBackground, spillBackground } from './spill';
import { jarvisFeed } from '../host/jarvisFeed';
import { PictureTrim } from './PictureTrim';
import { CornerPieces } from './CornerPieces';
import { stageBox } from './stage';
import { blankStrayIcon, blankWingLines, consoleCutout, fixPanelSlabs, type SlabZone } from './panelSlab';
import { seatInPicture } from '../modules/pictureSlots';
import layout from '../generated/layout.json';
import { bootRunning } from './settle';
import { hiddenZones } from '../modules/hidden';
import grainUrl from '../assets/lens/bluenoise.png?url';
import glassFxClean from '../assets/glass_fx_pic_clean.png?url';
import shadePic from '../assets/shade_pic.png?url';

const urls = import.meta.glob('../generated/frame/*.png', { eager: true, query: '?url', import: 'default' }) as Record<string, string>;
const url = (name: string) => urls[`../generated/frame/${(manifest as Record<string, string>)[name]}`];

const n = (v: Record<string, string>, k: string, d: number) => { const x = Number(v[k]); return Number.isFinite(x) ? x : d; };
const alpha = (x: number) => Math.min(255, Math.max(0, x)) / 255;
// the HUD's own trim kept in fitted mode: everything except the top 330 units and the bottom console (x 700..1860, y 1380..1600), which PictureTrim draws on the art's edges
// the cut-out's sides are the bottom panels' slab edges, not a fixed 700 and 1860: the slabs reach into that range and lost a corner to the clip
const decorClip = (zones: SlabZone[], sc = 1) => {
  const { left, right } = consoleCutout(zones, 700, 1860, sc), pc = (x: number) => `${((x / 2560) * 100).toFixed(3)}%`;
  return `polygon(0 20.625%, 100% 20.625%, 100% 100%, ${pc(right)} 100%, ${pc(right)} 86.25%, ${pc(left)} 86.25%, ${pc(left)} 100%, 0 100%)`;
};
const fill = { position: 'absolute', inset: 0, backgroundSize: '100% 100%' } as const;

/** Frame.ini's cockpit, as stacked layers in the skin's drawing order. Alpha formulas are the skin's (GlassGlare*21, ScanAlpha*18, ...). */
export function FrameLayers({ style, values }: { style: FrameStyle; values: Record<string, string> }) {
  // the bottom panels' zones, seated like the modules are, so the glass slab behind each one follows its card (panelSlab.ts)
  const slabZones = useMemo(() => layout.zones.filter((z) => z.id === 'B_panelL' || z.id === 'B_panelR').map((z) => (style === 'fitted' ? seatInPicture(z) : z)) as SlabZone[], [style]);
  // sized from the HUD canvas (stage.ts), so it cannot disagree with it; until the first measurement the CSS rule (the same fit) applies
  const sb = stageBox.value;
  const frameBox = sb ? { left: `${sb.left}px`, top: `${sb.top}px`, width: `${sb.width}px` } : undefined;
  const pic = style === 'picture' || style === 'fitted'; // fitted is the same picture art; only the HUD layout differs
  const rgb = String(values.ColorAccent ?? '').split(',').slice(0, 3).map((x) => Math.min(255, Math.max(0, Number(x) || 0))).join(',');
  const accent = `rgb(${rgb})`;
  const bright = `brightness(${Math.min(100, Math.max(0, n(values, 'FrameBrightness', 25))) / 100})`;
  const hull = alpha(n(values, 'HullAlpha', 255));
  const img = (name: string, a: number, extra: Record<string, string> = {}) => (
    <div class="frame-layer" data-layer={name} style={{ ...fill, backgroundImage: `url(${url(name)})`, opacity: a, ...extra }} />
  );
  // tint layers: the image only supplies the shape (mask); the colour is the live accent, like ImageTint=#ColorAccent#
  const tint = (name: string, a: number, mode: 'alpha' | 'luminance', bg: string, extra: Record<string, string> = {}) => (
    <div class="frame-layer" data-layer={name} style={{ ...fill, ...extra, background: bg, opacity: a, maskImage: `url(${url(name)})`, maskSize: '100% 100%', maskMode: mode, WebkitMaskImage: `url(${url(name)})`, WebkitMaskSize: '100% 100%' }} />
  );
  const tintA = n(values, 'GlassTint', 66);
  const scan = values.ScanLines === '1';
  const tier = n(values, 'PerfTier', 0);
  // Frame.ini's Shape parts: Glass under everything (rendered only), Accents/Spill/Lights/Decor over it (Decor in both styles)
  const vars = { ...values, ColorAccent: rgb };
  // the modules' drawing scale (Hud.tsx), which the panel slabs follow so each card sits centred on its glass (first fixed in fitted; now every frame)
  const sc = n(values, 'Scale', 1);
  // No frame: no art and no glass, but the HUD's own neon trim (Decor: the top, wing and bottom lines and the panel slabs) stays. It is not a .frame element: the
  // frame-mode tests count those, and None still has no frame layers.
  if (style === 'none') return <div class="frame-trim" aria-hidden="true" style={frameBox}><Parts names={['Decor']} vars={vars} zones={slabZones} sc={sc} /></div>;
  return (
    // the frame is the 16:10 area the modules' svg letterboxes into (.frame in ui.css: width min(100vw, 160vh), top-left of that area), from the window
    // size alone. It must NOT follow the HUD-size value: a page Scale other than the design 0.67 made it 1.5x too big against the modules (live test)
    <div class="frame" data-frame={style} aria-hidden="true" style={frameBox}>
      {pic ? tint('glass_pic', alpha(tintA), 'alpha', accent) : <Parts names={['Glass']} vars={vars} zones={slabZones} sc={sc} />}
      {/* picture frames: the glare is CSpace's own cleaned layer (tools/clean_glass_fx.cjs): the skin's had an odd bright triangular spot in the right window */}
      {pic
        ? <div class="frame-layer" data-layer="glass_fx_pic" style={{ ...fill, backgroundImage: `url(${glassFxClean})`, opacity: alpha(n(values, 'GlassGlare', 12) * 21) }} />
        : img('glass_fx', alpha(n(values, 'GlassGlare', 12) * 21))}
      {scan && img(pic ? 'scan_pic' : 'scan', alpha(n(values, 'ScanAlpha', 6) * 18))}
      {/* picture frames: the shade made for the picture's own windows (tools/shade_pic.py); shade.png follows the rendered windows and
          left an unshaded diagonal band across each picture side window, where the rendered hull has a strut */}
      {pic
        ? <div class="frame-layer" data-layer="shade" style={{ ...fill, backgroundImage: `url(${shadePic})`, opacity: alpha(n(values, 'ShadeAlpha', 155)) }} />
        : img('shade', alpha(n(values, 'ShadeAlpha', 155)))}
      {img(pic ? 'ship' : 'hull', hull, { filter: bright })}
      {tint(pic ? 'mist_pic' : 'mist', alpha(n(values, 'MistAlpha', 255)), 'alpha', accent)}
      {!pic && img('corners', hull, { filter: bright })}
      {!pic && <Finish accent={accent} mask={url('window_mask')} glare={alpha(n(values, 'GlassGlare', 12) * 21)} hull={hull}
        spill={spillBackground(accent, tier, hiddenZones(values))}
        orb={tier === 0 && values.StateLight !== '0' && !hiddenZones(values).split(',').includes('C_sphere')} />}
      {!pic && tier < 2 && <TrimSpill vars={vars} mask={url('window_mask')} hull={hull} />}
      {!pic && n(values, 'PerfTier', 0) < 2 && <Grain mask={url('window_mask')} hull={hull} />}
      {style === 'fitted' ? (
        <>
          {/* the top 330 units and the bottom console of the HUD's own trim are hidden: PictureTrim draws them along the picture's slots and band instead */}
          <div class="frame-layer" data-layer="decor-lower" style={{ ...fill, clipPath: decorClip(slabZones, sc) }}><Parts names={['Decor']} vars={vars} zones={slabZones} sc={sc} fitted /></div>
          <PictureTrim accent={accent} tier={tier} />
          {values.CornerPieces !== '0' && <CornerPieces accent={accent} />}
        </>
      ) : <Parts names={pic ? ['Decor'] : ['Accents', 'Spill', 'Lights', 'Decor']} vars={vars} zones={slabZones} sc={sc} />}
    </div>
  );
}

const PARTS = parts as unknown as Record<string, [string, Record<string, string>][]>;

/** The named Parts/*.inc sections as one SVG in the canvas units, stretched over the frame like the layer images. */
function Parts({ names, vars, zones, sc = 1, fitted = false }: { names: string[]; vars: Record<string, string>; zones: SlabZone[]; sc?: number; fitted?: boolean }) {
  const key = names.join();
  // only the variables the parts read, so a clock tick or an unrelated setting does not rebuild a hundred shapes
  const deps = ['ColorAccent', 'GlowAlpha', 'GlowWidth', 'CoreWhite', 'GlassTint'].map((k) => vars[k]);
  const shapes = useMemo(() => names.flatMap((p) => (PARTS[`${p}.inc`] ?? []).flatMap(([, sec]) => partShapes(p === 'Decor' ? fixPanelSlabs(fitted ? blankWingLines(blankStrayIcon(sec)) : blankStrayIcon(sec), zones, sc) : sec, vars))), [key, zones, sc, fitted, ...deps]);
  return (
    <svg class="frame-parts" data-part={key} viewBox="0 0 2560 1600" preserveAspectRatio="none" style={{ position: 'absolute', inset: 0, width: '100%', height: '100%' }}>
      {shapes.map((s, i) => {
        const id = `fp-${key}-${i}`;
        const fill = typeof s.fill === 'string' ? s.fill : `url(#${id})`;
        // the neon tubes are stacked strokes (halo, glow, core, white core); the wide halo and glow strokes are
        // blurred so they fall off like light, as the modules' bloom does, instead of ending in hard bands
        const soft = s.kind === 'path' && fill === 'none' && s.width > 3;
        const common = { fill, stroke: s.stroke, 'stroke-width': s.width, 'stroke-linejoin': s.join, style: soft ? { filter: `blur(${(s.width * 0.42).toFixed(1)}px)` } : undefined };
        return (
          <g key={i}>
            {typeof s.fill !== 'string' && (
              <linearGradient id={id} x1={s.fill.x1} y1={s.fill.y1} x2={s.fill.x2} y2={s.fill.y2}>
                {s.fill.stops.map((st) => <stop key={st.off} offset={st.off} stop-color={st.color} />)}
              </linearGradient>
            )}
            {s.kind === 'ellipse' ? <ellipse {...s.geo} {...common} /> : s.kind === 'rect' ? <rect {...s.geo} {...common} /> : <path {...s.geo} {...common} />}
            {glints(s).map(([x, y], j) => (
              <g key={`g${j}`}>
                <circle cx={x} cy={y} r={7} fill={s.stroke} opacity={0.35} style={{ filter: 'blur(4px)' }} />
                <circle cx={x} cy={y} r={2.1} fill="rgb(235 250 255)" />
              </g>
            ))}
          </g>
        );
      })}
    </svg>
  );
}

/**
 * The cockpit's lighting finish (rendered style only, static, no animation): a soft diagonal reflection on the window
 * glass (window_mask, white = glass), the console's light falling on the lower hull, and a vignette that darkens the
 * hull towards the screen edges but never the windows, so the desktop behind them keeps its colours.
 */
function Finish({ accent, mask, glare, hull, spill, orb = false }: { accent: string; mask: string; glare: number; hull: number; spill: string; orb?: boolean }) {
  const glass = { maskImage: `url(${mask})`, maskSize: '100% 100%', maskMode: 'luminance', WebkitMaskImage: `url(${mask})`, WebkitMaskSize: '100% 100%' } as const;
  // the hull: everything except the glass (a full layer minus the window mask)
  const notGlass = notGlassMask(mask);
  return (
    <>
      <div class="frame-layer" data-layer="sheen" style={{ ...fill, ...glass, opacity: Math.min(1, 0.5 + glare),
        background: 'linear-gradient(112deg, transparent 18%, rgb(255 255 255 / .045) 27%, transparent 34%, transparent 58%, rgb(255 255 255 / .03) 64%, transparent 69%), linear-gradient(180deg, rgb(255 255 255 / .035), transparent 40%)' }} />
      <div class="frame-layer" data-layer="bounce" style={{ ...fill, ...notGlass, opacity: hull, mixBlendMode: 'screen',
        background: `radial-gradient(38% 30% at 50% 74%, color-mix(in srgb, ${accent} 16%, transparent), transparent 70%), radial-gradient(70% 22% at 50% 100%, color-mix(in srgb, ${accent} 9%, transparent), transparent 75%)` }} />
      {/* K6: the lit screens' light on the hull around them (static; never on the glass) */}
      {spill && <div class="frame-layer" data-layer="spill" style={{ ...fill, ...notGlass, opacity: hull, mixBlendMode: 'screen', background: spill }} />}
      {orb && <OrbLight accent={accent} notGlass={notGlass} hull={hull} />}
      <div class="frame-layer" data-layer="vignette" style={{ ...fill, ...notGlass, opacity: hull,
        background: 'radial-gradient(75% 70% at 50% 45%, transparent 55%, rgb(0 0 0 / .38) 100%)' }} />
    </>
  );
}

/** UI-handoff 12 #9: light that follows state. The orb throws more light on the hull while JARVIS listens or speaks: one
 *  static pool whose opacity changes with the state (a few times a minute, a short CSS fade; never the level, never a
 *  blur). FULL only; setting StateLight. */
function OrbLight({ accent, notGlass, hull }: { accent: string; notGlass: ReturnType<typeof notGlassMask>; hull: number }) {
  const st = jarvisFeed.value.state;
  const on = st === 'speaking' || st === 'listening';
  return <div class="frame-layer" data-layer="orblight" data-on={on ? '1' : '0'}
    style={{ ...fill, ...notGlass, opacity: on ? hull : 0, mixBlendMode: 'screen', background: orbLightBackground(accent) }} />;
}

/** The hull: everything except the glass (a full layer minus the window mask, white = glass). */
function notGlassMask(mask: string) {
  return { maskImage: `linear-gradient(#000, #000), url(${mask})`, maskSize: '100% 100%', maskMode: 'alpha, luminance', maskComposite: 'exclude',
    WebkitMaskImage: `linear-gradient(#000, #000), url(${mask})`, WebkitMaskSize: '100% 100%', WebkitMaskComposite: 'xor' } as const;
}

/** K6 along the trim: the Decor tubes' core lines again as one wide, blurred, faint stroke group in screen blend, masked
 *  to the hull, so the trim reads as a lit inlay throwing light on the plating around it. Static; one blur for the group. */
function TrimSpill({ vars, mask, hull }: { vars: Record<string, string>; mask: string; hull: number }) {
  const deps = ['ColorAccent', 'GlowAlpha', 'GlowWidth', 'CoreWhite'].map((k) => vars[k]);
  const cores = useMemo(() => (PARTS['Decor.inc'] ?? []).flatMap(([, sec]) => partShapes(sec, vars))
    .filter((s) => s.kind === 'path' && s.fill === 'none' && s.width >= 1.2 && s.width <= 2.2), deps);
  if (!cores.length) return null;
  return (
    <div class="frame-layer" data-layer="trimspill" style={{ ...fill, ...notGlassMask(mask), opacity: hull * 0.5, mixBlendMode: 'screen' }}>
      <svg viewBox="0 0 2560 1600" preserveAspectRatio="none" style={{ position: 'absolute', inset: 0, width: '100%', height: '100%' }}>
        <g style={{ filter: 'blur(14px)' }} opacity={0.22}>
          {cores.map((s, i) => <path key={i} d={String(s.geo.d)} fill="none" stroke={s.stroke} stroke-width={26} stroke-linejoin="round" />)}
        </g>
      </svg>
    </div>
  );
}

/** White-hot glints at the open ends of a neon tube's core stroke (the opaque ~1.7 wide accent line); none for closed
 *  paths, fills or the halo/glow strokes. */
function glints(s: ReturnType<typeof partShapes>[number]): [number, number][] {
  if (s.kind !== 'path' || s.fill !== 'none' || s.width < 1.2 || s.width > 2.2) return [];
  const d = String(s.geo.d);
  if (d.endsWith('Z')) return [];
  const pts = [...d.matchAll(/[ML]([-\d.]+) ([-\d.]+)/g)].map((m): [number, number] => [Number(m[1]), Number(m[2])]);
  return pts.length >= 2 ? [pts[0], pts[pts.length - 1]] : [];
}

/** H2c: blue-noise grain on the hull (FULL and LITE). Soft-light at a few percent breaks the 8-bit steps in the dark
 *  gradients (spill pools, hull falloff) and gives the metal a film texture; never on the window glass. */
export const GRAIN = 0.07;
function Grain({ mask, hull }: { mask: string; hull: number }) {
  const settled = !bootRunning.value; // #21: off during the start-up sequence, then it fades in (ui.css)
  return <div class="frame-layer" data-layer="grain" data-settled={settled ? '1' : '0'} style={{ ...fill, ...notGlassMask(mask), opacity: settled ? GRAIN * hull : 0, mixBlendMode: 'soft-light',
    backgroundImage: `url(${grainUrl})`, backgroundSize: '128px 128px', backgroundRepeat: 'repeat' }} />;
}
