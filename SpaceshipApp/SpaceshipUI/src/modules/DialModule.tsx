import { useRef, useState } from 'preact/hooks';
import layout from '../generated/layout.json';
import type { Style } from '../draw/canvas';
import { OpsView } from '../draw/ops';
import { CONTROLS, DIAL_CENTRE, DIAL_LABEL_HITS, DIAL_RING, dialFrame, ringValue, stepValue, valueOf, type DialInput } from './dial';
import type { DialSetter } from './dialSetter';

// A range change goes out once the scroll has paused, so a wheel does not flood the system. Stepped changes go at once.
const SETTLE_MS = 400;

/**
 * The systems dial in its zone (B_storage). Click a label to select it, click the ring to jump to a value, scroll to step.
 * Writes go through the setter; power and refresh wait for a click on the centre to confirm.
 */
export function DialModule({ zone, style, setter }: { zone: (typeof layout.zones)[number]; style: Style; setter: DialSetter }) {
  const [sel, setSel] = useState(1);
  const [pending, setPending] = useState<Record<string, number>>({});
  const [note, setNote] = useState('');
  const [confirm, setConfirm] = useState<{ id: number; ctl: string }>();
  const settle = useRef<Record<string, number>>({});
  const inp: DialInput = { glowAlpha: style.glowA, pending };

  const drop = (ctl: string) => setPending((p) => { const next = { ...p }; delete next[ctl]; return next; });
  const send = async (i: number, v: number) => {
    const ctl = CONTROLS[i].id;
    const r = await setter.set(ctl, v);
    setNote(r.note ?? '');
    if (!r.ok) drop(ctl);
    if (r.pending !== undefined) setConfirm({ id: r.pending, ctl });
  };
  const change = (i: number, v: number) => {
    const ctl = CONTROLS[i].id;
    setPending((p) => ({ ...p, [ctl]: v }));
    clearTimeout(settle.current[ctl]);
    if (CONTROLS[i].steps) void send(i, v);
    else settle.current[ctl] = window.setTimeout(() => void send(i, v), SETTLE_MS);
  };
  const pick = (i: number) => { setSel(i + 1); setNote(''); };
  const wheel = (i: number, e: WheelEvent) => {
    e.preventDefault();
    const v = stepValue(i, inp, e.deltaY < 0 ? 1 : -1);
    if (CONTROLS[i].steps && v === valueOf(CONTROLS[i], inp)) return;
    change(i, v);
  };
  const ringClick = (e: MouseEvent) => {
    const el = e.currentTarget as SVGGraphicsElement;
    const m = el.getScreenCTM()?.inverse();
    if (!m) return;
    const p = new DOMPoint(e.clientX, e.clientY).matrixTransform(m);
    const v = ringValue(sel - 1, p.x - DIAL_RING.cx, p.y - DIAL_RING.cy);
    if (v !== undefined) change(sel - 1, v);
  };
  const confirmClick = async () => {
    if (!confirm) return;
    const r = await setter.confirm(confirm.id);
    setConfirm(undefined);
    setNote(r.note ?? '');
    if (!r.ok) drop(confirm.ctl);
  };

  return (
    <g transform={`matrix(${zone.matrix.join(' ')})`} data-module="dial">
      <OpsView ops={dialFrame(inp, zone, style, sel, note)} name="dl" />
      <circle cx={DIAL_RING.cx} cy={DIAL_RING.cy} r={DIAL_RING.r} fill="transparent" style={{ cursor: 'pointer' }}
        onClick={ringClick} onWheel={(e) => wheel(sel - 1, e)} />
      {DIAL_LABEL_HITS.map((h) => (
        <rect x={h.x} y={h.y} width={h.w} height={h.h} fill="transparent" style={{ cursor: 'pointer' }}
          onClick={() => pick(h.i)} onWheel={(e) => wheel(h.i, e)} />
      ))}
      {confirm && (
        <circle cx={DIAL_CENTRE.cx} cy={DIAL_CENTRE.cy} r={DIAL_CENTRE.r} fill="transparent" style={{ cursor: 'pointer' }}
          onClick={confirmClick} />
      )}
    </g>
  );
}
