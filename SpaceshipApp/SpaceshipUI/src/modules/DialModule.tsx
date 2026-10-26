import { useEffect, useRef, useState } from 'preact/hooks';
import layout from '../generated/layout.json';
import type { Style } from '../draw/canvas';
import { OpsView } from '../draw/ops';
import { systemMetrics } from '../host/systemMetrics';
import { CONTROLS, DIAL_CENTRE, DIAL_LABEL_HITS, DIAL_RING, dialFrame, ringValue, stepValue, valueOf, type DialInput } from './dial';
import type { DialSetter } from './dialSetter';
import { host } from '../settings/instance';
import { controlOpen } from './overlays';

// A range change goes out once the scroll has paused, so a wheel does not flood the system. Stepped changes go at once.
const SETTLE_MS = 400;

/**
 * The systems dial in its zone (B_storage). Click a label to select it, click the ring to jump to a value, scroll to step.
 * Writes go through the setter; power and refresh wait for a click on the centre to confirm.
 */
export function DialModule({ zone, style, setter, sel0 = 1 }: { zone: (typeof layout.zones)[number]; style: Style; setter: DialSetter; sel0?: number }) {
  // starts on the skin's saved DialSel, clamped like dial.lua. shortcut: a pick is not saved back (DialSel is not host-writable), upgrade with the host allowlist
  const [sel, setSel] = useState(() => Math.max(1, Math.min(CONTROLS.length, Math.floor(sel0) || 1)));
  const [pending, setPending] = useState<Record<string, number>>({});
  const [note, setNote] = useState('');
  const [confirm, setConfirm] = useState<{ id: number; ctl: string }>();
  const settle = useRef<Record<string, number>>({});
  const m = systemMetrics.value;
  // vol is negative for muted, as the skin's measure is; brightness and the power plan are not read by the host
  const live: DialInput = {
    glowAlpha: style.glowA, vol: m?.volume == null ? undefined : m.volumeMuted ? -1 : m.volume,
    mic: m?.mic ?? undefined, micMuted: m?.micMuted ?? undefined, refresh: m?.refreshHz == null ? undefined : String(m.refreshHz),
  };
  const inp: DialInput = { ...live, pending };
  // a pending value is dropped once the reading reaches it (Lua pending); a failed write is dropped in send
  useEffect(() => {
    const done = Object.keys(pending).filter((id) => {
      const c = CONTROLS.find((x) => x.id === id);
      const v = c && valueOf(c, live);
      return v !== undefined && Math.abs(v - pending[id]) < 0.011;
    });
    if (done.length) setPending((p) => { const next = { ...p }; for (const id of done) delete next[id]; return next; });
  }, [m, style.glowA]);

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
  // dial.lua OnRightClick: the Windows page for the control, the control panel for glow
  const menu = (i: number, e: MouseEvent) => {
    e.preventDefault();
    const id = CONTROLS[i].id;
    const what = id === 'vol' || id === 'mic' ? 'sound' : id === 'bright' || id === 'hz' ? 'display' : id === 'power' ? 'power' : null;
    if (what) host.send({ type: 'target.open', what }); else controlOpen.value = true;
  };
  const confirmClick = async () => {
    if (!confirm) return;
    const r = await setter.confirm(confirm.id);
    setConfirm(undefined);
    setNote(r.note ?? '');
    if (!r.ok) drop(confirm.ctl);
  };

  return (
    <g transform={`matrix(${zone.matrix.join(' ')})`} data-module="dial" data-hit>
      <OpsView ops={dialFrame(inp, zone, style, sel, note)} name="dl" />
      {/* the hit shapes are in zone units; Canvas draws at (zone origin + x) * s, so they get the same offset and scale */}
      <g transform={`translate(${zone.x * style.s} ${zone.y * style.s}) scale(${style.s})`}>
      <circle cx={DIAL_RING.cx} cy={DIAL_RING.cy} r={DIAL_RING.r} fill="transparent" style={{ cursor: 'pointer' }}
        onClick={ringClick} onContextMenu={(e) => menu(sel - 1, e)} onWheel={(e) => wheel(sel - 1, e)} />
      {DIAL_LABEL_HITS.map((h) => (
        <rect x={h.x} y={h.y} width={h.w} height={h.h} fill="transparent" style={{ cursor: 'pointer' }}
          onClick={() => pick(h.i)} onContextMenu={(e) => menu(h.i, e)} onWheel={(e) => wheel(h.i, e)} />
      ))}
      {confirm && (
        <circle cx={DIAL_CENTRE.cx} cy={DIAL_CENTRE.cy} r={DIAL_CENTRE.r} fill="transparent" style={{ cursor: 'pointer' }}
          onClick={confirmClick} />
      )}
      </g>
    </g>
  );
}
