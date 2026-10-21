import { useEffect, useMemo, useState } from 'preact/hooks';
import layout from '../generated/layout.json';
import type { Style } from '../draw/canvas';
import { OpsView } from '../draw/ops';
import { readingsFrom, systemMetrics } from '../host/systemMetrics';
import { scheduler } from '../host/scheduler';
import { bootFrame, bootRows, bootTimeline, FRAME_MS } from './boot';

const tl = bootTimeline();

/**
 * Start-up sequence, behind ?module=boot. It runs once from mount (about 2.7 s) and then renders nothing. The system
 * check reads the host once, when the check starts.
 */
export function BootModule({ style }: { style: Style }) {
  const [f, setF] = useState(0);
  useEffect(() => {
    let n = 0;
    const stop = scheduler.every(FRAME_MS, () => {
      n += 1;
      setF(n);
      if (n >= tl.done) stop();
    });
    return stop;
  }, []);
  const checking = f >= tl.c0;
  const rows = useMemo(() => {
    const m = systemMetrics.value;
    const r = m ? readingsFrom(m) : {};
    return bootRows({ cpu: r.mCPU, mem: r.mRamPct, onAc: m?.onAc ?? undefined, bat: r.mBattPct });
  }, [checking]);
  if (f >= tl.done) return null;
  const fade = f >= tl.fade ? Math.max(0, (tl.done - f) / (tl.done - tl.fade)) : 1;
  const ops = bootFrame(f, rows, tl, { w: layout.canvas.w, h: layout.canvas.h }, style);
  return (
    <g opacity={fade} data-module="boot">
      <OpsView ops={ops} name="boot" />
    </g>
  );
}
