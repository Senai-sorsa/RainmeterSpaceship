import { useEffect, useLayoutEffect, useMemo, useState } from 'preact/hooks';
import layout from '../generated/layout.json';
import type { Style } from '../draw/canvas';
import { OpsView } from '../draw/ops';
import { readingsFrom, systemMetrics } from '../host/systemMetrics';
import { scheduler } from '../host/scheduler';
import { bootFrame, bootRows, bootTimeline, FRAME_MS } from './boot';
import { bootRunning } from '../ui/settle';

const tl = bootTimeline();

/**
 * Start-up sequence, behind ?module=boot. It runs once from mount (about 2.7 s) and then renders nothing. The system
 * check reads the host once, when the check starts.
 */
// ?bootat=<frame> in a plain browser holds the sequence on one frame, for screenshot checks (headless runs few animation frames)
const hold = (() => {
  const v = Number(new URLSearchParams(globalThis.location?.search).get('bootat'));
  return Number.isFinite(v) && v > 0 && !(globalThis as { chrome?: { webview?: unknown } }).chrome?.webview ? v : null;
})();

export function BootModule({ style }: { style: Style }) {
  const [f, setF] = useState(hold ?? 0);
  // the lens waits for the sequence (set before the first paint, so it never shows and then fades out)
  useLayoutEffect(() => { bootRunning.value = true; return () => { bootRunning.value = false; }; }, []);
  useEffect(() => {
    if (hold !== null) return;
    let n = 0;
    const stop = scheduler.every(FRAME_MS, () => {
      n += 1;
      setF(n);
      if (n >= tl.done) { stop(); bootRunning.value = false; }
    });
    return stop;
  }, []);
  const checking = f >= tl.c0;
  const rows = useMemo(() => {
    const m = systemMetrics.value;
    const r = m ? readingsFrom(m) : {};
    return bootRows({
      cpu: r.mCPU, gpu: r.mGPU, mem: r.mRamPct, onAc: m?.onAc ?? undefined, bat: r.mBattPct,
      driveTotal: r.mD1Total, driveFree: r.mD1Free, netDown: r.netDown, netUp: r.netUp, volume: m?.volume ?? undefined, muted: m?.volumeMuted ?? undefined,
    });
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
