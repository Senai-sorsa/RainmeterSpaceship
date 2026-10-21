import { useEffect, useState } from 'preact/hooks';

const SHOW_MS = 6000; // the skin's caption vanishes after 6 seconds

/** HUD caption: shows the data-tip of the element under the pointer, for 6 seconds or until the pointer moves to something with no tip. */
export function Caption() {
  const [text, setText] = useState('');
  useEffect(() => {
    let timer = 0;
    const onOver = (e: PointerEvent) => {
      const el = e.target instanceof Element ? e.target.closest('[data-tip]') : null;
      const tip = el?.getAttribute('data-tip') ?? '';
      clearTimeout(timer);
      setText(tip);
      if (tip) timer = window.setTimeout(() => setText(''), SHOW_MS);
    };
    document.addEventListener('pointerover', onOver);
    return () => { clearTimeout(timer); document.removeEventListener('pointerover', onOver); };
  }, []);
  const box = { position: 'fixed', left: '50%', bottom: '4vh', transform: 'translateX(-50%)', padding: '6px 14px', background: 'rgba(0,0,0,.6)', color: 'var(--text)', font: '600 14px system-ui, sans-serif', pointerEvents: 'none', whiteSpace: 'pre' } as const;
  return text ? <div id="hud-caption" role="status" style={box}>{text}</div> : null;
}
