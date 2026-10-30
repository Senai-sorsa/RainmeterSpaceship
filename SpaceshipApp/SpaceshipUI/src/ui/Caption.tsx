import { useEffect, useState } from 'preact/hooks';

const SHOW_MS = 6000; // the skin's caption vanishes after 6 seconds
const GAP = 6;

type Shown = { text: string; x: number; y: number; above: boolean };

/**
 * HUD caption (lib.lua H.caption): the data-tip of the element under the pointer, centred under it (above it near the
 * bottom edge), for 6 seconds or until the pointer moves to something with no tip. on=false (CaptionStyle=0) shows none.
 */
export function Caption({ on = true }: { on?: boolean }) {
  const [shown, setShown] = useState<Shown | null>(null);
  useEffect(() => {
    if (!on) return;
    let timer = 0;
    const onOver = (e: PointerEvent) => {
      const el = e.target instanceof Element ? e.target.closest('[data-tip]') : null;
      const text = el?.getAttribute('data-tip') ?? '';
      clearTimeout(timer);
      if (!el || !text) { setShown(null); return; }
      const r = el.getBoundingClientRect();
      const above = r.bottom + GAP + 40 > window.innerHeight;
      setShown({ text, x: r.left + r.width / 2, y: above ? r.top - GAP : r.bottom + GAP, above });
      timer = window.setTimeout(() => setShown(null), SHOW_MS);
    };
    document.addEventListener('pointerover', onOver);
    return () => { clearTimeout(timer); document.removeEventListener('pointerover', onOver); setShown(null); };
  }, [on]);
  if (!shown) return null;
  const box = {
    position: 'fixed', left: `clamp(8px, ${shown.x}px, calc(100vw - 8px))`, top: `${shown.y}px`,
    transform: `translate(-50%, ${shown.above ? '-100%' : '0'})`, maxWidth: 'calc(100vw - 16px)', padding: '4px 10px',
    background: 'rgba(2,14,22,.85)', border: '1px solid var(--accent, currentColor)', clipPath: 'polygon(6px 0, 100% 0, 100% calc(100% - 6px), calc(100% - 6px) 100%, 0 100%, 0 6px)',
    color: 'var(--text)', font: "700 13px 'B612 Mono', monospace", textTransform: 'uppercase', pointerEvents: 'none', whiteSpace: 'pre',
  } as const;
  return <div id="hud-caption" role="status" style={box}>{shown.text}</div>;
}
