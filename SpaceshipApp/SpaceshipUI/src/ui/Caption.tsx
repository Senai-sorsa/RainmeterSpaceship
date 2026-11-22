import { useEffect, useState } from 'preact/hooks';

const SHOW_MS = 6000; // the skin's caption vanishes after 6 seconds
const GAP = 6;

type Shown = { text: string; x: number; y: number; above: boolean };

/**
 * HUD caption (lib.lua H.caption): the data-tip of the element under the pointer, centred under it (above it near the
 * bottom edge), for 6 seconds or until the pointer moves to something with no tip, and it is gone at once when the pointer leaves the element or
 * the page: over the transparent parts the HUD window is click-through, so no further pointerover reaches the page (live test: captions lingered).
 * on=false (CaptionStyle=0) shows none.
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
    const hide = () => { clearTimeout(timer); setShown(null); };
    const onOut = (e: PointerEvent) => {
      const from = e.target instanceof Element ? e.target.closest('[data-tip]') : null;
      if (!from) return;
      const to = e.relatedTarget instanceof Element ? e.relatedTarget : null;
      if (to && from.contains(to)) return; // still inside the same tipped element
      hide(); // the next element's pointerover shows its own caption straight after
    };
    document.addEventListener('pointerover', onOver);
    document.addEventListener('pointerout', onOut);
    document.documentElement.addEventListener('pointerleave', hide);
    window.addEventListener('blur', hide);
    return () => {
      clearTimeout(timer);
      document.removeEventListener('pointerover', onOver);
      document.removeEventListener('pointerout', onOut);
      document.documentElement.removeEventListener('pointerleave', hide);
      window.removeEventListener('blur', hide);
      setShown(null);
    };
  }, [on]);
  if (!shown) return null;
  // only the placement is inline; the look is .hud-caption in finish.css
  const box = {
    position: 'fixed', left: `clamp(8px, ${shown.x}px, calc(100vw - 8px))`, top: `${shown.y}px`,
    transform: `translate(-50%, ${shown.above ? '-100%' : '0'})`, maxWidth: 'calc(100vw - 16px)', pointerEvents: 'none', whiteSpace: 'pre',
  } as const;
  return <div id="hud-caption" class="hud-caption" role="status" style={box}>{shown.text}</div>;
}
