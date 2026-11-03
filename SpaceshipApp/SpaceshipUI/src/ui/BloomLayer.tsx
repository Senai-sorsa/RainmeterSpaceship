import { effect } from '@preact/signals';
import { useEffect, useRef } from 'preact/hooks';
import { bloomEntries, type BloomEntry } from '../draw/bloomBus';
import { BLOOM_STACK, entryBounds, TILE_MS, GLASS_MS, GLASS_SCALE, paintGlass, paintOps, stackBlur, TileCache, type Box, type Ctx2D } from '../draw/bloomPaint';
import dirtUrl from '../assets/lens/dirt.png?url';

// The one light canvas (tasks/hyperrealism-plan.md Task 3): the glow ops every OpsView anchor posts, drawn at a quarter of
// the CSS resolution, blurred at three radii and stretched over the HUD in screen blend. Each anchor's light is a cached
// tile (Task 4): only an anchor whose ops or position changed is painted and blurred again; a frame is then just one
// drawImage per tile. It draws only when the light changes (one frame at most), on resize and once the fonts are ready.
export const SCALE = 0.25;

type Dev = { __glassDraws?: number; __bloomLast?: Record<string, BloomEntry['ctm']>; __bloomDraws?: number; __bloomTileBuilds?: number; __bloomBuiltBy?: Record<string, number> };
type Tile = { box: Box; canvas: HTMLCanvasElement } | null;
const ctx2d = (c: HTMLCanvasElement) => c.getContext('2d') as unknown as Ctx2D | null;

/** lens: the glass layer (Task 6) - lens dirt lit by the HUD's spread light, and a faint soft ghost of it. Over the whole
 *  view, as a camera lens is (a window-only mask left the smudges dark: little HUD light falls on the windows). */
export function BloomLayer({ mode, baseRadius, lens = false }: { mode: 'canvas' | 'svg' | 'off'; baseRadius: number; lens?: boolean }) {
  const ref = useRef<HTMLCanvasElement>(null);
  const glassRef = useRef<HTMLCanvasElement>(null);
  const glassOn = lens && mode === 'canvas';
  useEffect(() => {
    const cv = ref.current;
    if (!cv) return;
    const glass = glassRef.current;
    const dirt = new Image();
    let dirtReady = false;
    if (glass) { dirt.onload = () => { dirtReady = true; schedule(); }; dirt.src = dirtUrl; }
    const scratch = document.createElement('canvas');
    // a blur of radius r spreads about 2.5 r: the widest pass decides the tile margin
    const pad = Math.ceil(baseRadius * BLOOM_STACK[BLOOM_STACK.length - 1][0] * 2.5);
    const dev = import.meta.env.DEV ? (window as unknown as Dev) : null;
    const build = (_k: string, e: BloomEntry): Tile => {
      const box = entryBounds(e, SCALE, pad, cv.width, cv.height);
      if (!box) return null;
      if (scratch.width < box.w) scratch.width = box.w;
      if (scratch.height < box.h) scratch.height = box.h;
      const sc = ctx2d(scratch), canvas = document.createElement('canvas');
      canvas.width = box.w; canvas.height = box.h;
      const out = ctx2d(canvas);
      if (!sc || !out) return null;
      sc.clearRect(0, 0, box.w, box.h);
      paintOps(sc, [e], SCALE, box.x, box.y);
      stackBlur(out, scratch, baseRadius);
      out.globalAlpha = 0.5; // the near-field light, unblurred at quarter res: a soft core under the crisp line
      out.drawImage(scratch, 0, 0);
      out.globalAlpha = 1;
      if (dev) { dev.__bloomTileBuilds = (dev.__bloomTileBuilds ?? 0) + 1; const by = (dev.__bloomBuiltBy ??= {}); by[_k] = (by[_k] ?? 0) + 1; }
      return { box, canvas };
    };
    let cache = new TileCache<Tile>(build, TILE_MS);
    let queued = 0, retry = 0;
    const draw = () => {
      queued = 0;
      const w = Math.ceil(innerWidth * SCALE), h = Math.ceil(innerHeight * SCALE);
      if (cv.width !== w || cv.height !== h) { cv.width = w; cv.height = h; cache = new TileCache<Tile>(build, TILE_MS); }
      const out = ctx2d(cv);
      if (!out) return;
      const entries = mode === 'canvas' ? bloomEntries.value : new Map<string, BloomEntry>();
      const wait = cache.update(entries);
      if (wait && !retry) retry = window.setTimeout(() => { retry = 0; schedule(); }, wait); // the trailing rebuild
      out.clearRect(0, 0, w, h);
      for (const { tile } of cache.tiles.values()) if (tile) out.drawImage(tile.canvas, tile.box.x, tile.box.y);
      paintGlassSoon();
      if (dev) {
        dev.__bloomLast = Object.fromEntries([...entries].map(([k, e]) => [k, e.ctm]));
        dev.__bloomDraws = (dev.__bloomDraws ?? 0) + 1;
      }
    };
    // the glass follows the light at most every GLASS_MS (a trailing repaint catches the last change)
    let glassAt = -Infinity, glassTimer = 0;
    const paintGlassNow = () => {
      glassTimer = 0;
      if (!glass || !dirtReady) return;
      glassAt = performance.now();
      const gw = Math.ceil(cv.width * GLASS_SCALE), gh = Math.ceil(cv.height * GLASS_SCALE);
      if (glass.width !== gw || glass.height !== gh) { glass.width = gw; glass.height = gh; }
      const g = ctx2d(glass);
      if (g) paintGlass(g, cv, dirt, gw, gh);
      if (dev) dev.__glassDraws = (dev.__glassDraws ?? 0) + 1;
    };
    const paintGlassSoon = () => {
      if (!glass || glassTimer) return;
      const wait = glassAt + GLASS_MS - performance.now();
      if (wait <= 0) paintGlassNow(); else glassTimer = window.setTimeout(paintGlassNow, wait);
    };
    const schedule = () => { if (!queued) queued = requestAnimationFrame(draw); };
    const stop = effect(() => { void bloomEntries.value; schedule(); });
    // a resize re-posts every anchor (new CTMs), and the new canvas size drops the cache
    addEventListener('resize', schedule);
    // the fonts arriving changes every text's light: rebuild all tiles once
    document.fonts?.ready.then(() => { cache = new TileCache<Tile>(build, TILE_MS); schedule(); });
    return () => { stop(); removeEventListener('resize', schedule); if (queued) cancelAnimationFrame(queued); if (glassTimer) clearTimeout(glassTimer); if (retry) clearTimeout(retry); };
  }, [mode, baseRadius, glassOn]);
  return (
    <>
      <canvas ref={ref} class="bloom-layer" data-mode={mode} aria-hidden="true" />
      {glassOn && <canvas ref={glassRef} class="glass-layer" aria-hidden="true" />}
    </>
  );
}
