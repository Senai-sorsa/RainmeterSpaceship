import { effect } from '@preact/signals';
import { useEffect, useRef } from 'preact/hooks';
import { bloomEntries, type BloomEntry } from '../draw/bloomBus';
import { paintOps, stackBlur, type Ctx2D } from '../draw/bloomPaint';

// The one light canvas (tasks/hyperrealism-plan.md Task 3): the glow ops every OpsView anchor posts, drawn at a quarter of
// the CSS resolution, blurred at three radii and stretched over the HUD in screen blend. It draws only when the light
// changes (one frame at most per change), on resize and once the fonts are ready; nothing runs while idle.
export const SCALE = 0.25;

type Dev = { __bloomLast?: Record<string, BloomEntry['ctm']>; __bloomDraws?: number };

export function BloomLayer({ mode, baseRadius }: { mode: 'canvas' | 'svg' | 'off'; baseRadius: number }) {
  const ref = useRef<HTMLCanvasElement>(null);
  useEffect(() => {
    const cv = ref.current;
    if (!cv) return;
    const src = document.createElement('canvas');
    let queued = 0;
    const draw = () => {
      queued = 0;
      const w = Math.ceil(innerWidth * SCALE), h = Math.ceil(innerHeight * SCALE);
      if (cv.width !== w || cv.height !== h) { cv.width = src.width = w; cv.height = src.height = h; }
      const out = cv.getContext('2d') as unknown as Ctx2D | null, sc = src.getContext('2d') as unknown as Ctx2D | null;
      if (!out || !sc) return;
      out.clearRect(0, 0, w, h);
      const entries = mode === 'canvas' ? bloomEntries.value : new Map<string, BloomEntry>();
      if (import.meta.env.DEV) {
        const d = window as unknown as Dev;
        d.__bloomLast = Object.fromEntries([...entries].map(([k, e]) => [k, e.ctm]));
        d.__bloomDraws = (d.__bloomDraws ?? 0) + 1;
      }
      if (!entries.size) return;
      sc.clearRect(0, 0, w, h);
      paintOps(sc, entries.values(), SCALE);
      stackBlur(out, src, baseRadius);
      out.globalAlpha = 0.5; // the near-field light, unblurred at quarter res: a soft core under the crisp line
      out.drawImage(src, 0, 0);
      out.globalAlpha = 1;
    };
    const schedule = () => { if (!queued) queued = requestAnimationFrame(draw); };
    const stop = effect(() => { void bloomEntries.value; schedule(); });
    addEventListener('resize', schedule);
    document.fonts?.ready.then(schedule);
    return () => { stop(); removeEventListener('resize', schedule); if (queued) cancelAnimationFrame(queued); };
  }, [mode, baseRadius]);
  return <canvas ref={ref} class="bloom-layer" data-mode={mode} aria-hidden="true" />;
}
