import { useEffect, useMemo, useRef, useState } from 'preact/hooks';
import layout from '../generated/layout.json';
import type { Op, Style } from '../draw/canvas';
import { OpsView } from '../draw/ops';
import { scheduler } from '../host/scheduler';
import { readingsFrom, systemMetrics } from '../host/systemMetrics';
import { hudFrame, hudState, type HudState } from './hud';
import { type Readings } from './readings';
import { sphereFrame, sphereState, type SphereState } from './sphere';
import { targetFrame, targetMove, targetState, type TargetState } from './target';

const zoneOf = (id: string) => layout.zones.find((z) => z.id === id);
/** Zones of the centre: the target reticle, the HUD ladders and the sphere. */
const Z = { target: zoneOf('C_target'), hud: zoneOf('C_hud'), sphere: zoneOf('C_sphere') };
const FRAME_MS = 50; // 20 fps, the full tier of target.lua

/**
 * Centre: the target reticle roaming the windscreen, the HUD ladders and the sphere. Behind ?module=center.
 * The reticle and the sphere animate on a 20 fps timer; the HUD eases once per host reading. The reticle and sphere
 * show -- or TEST where the host does not supply the figure yet (speed test, per-process CPU and memory, GPU load).
 */
export function CenterModule({ style }: { style: Style }) {
  const m = systemMetrics.value;
  const r: Readings = useMemo(() => (m ? readingsFrom(m) : {}), [m]);
  const hud = useRef<HudState>(hudState());
  const sph = useRef<SphereState>(sphereState());
  const tgt = useRef<TargetState | null>(Z.target ? targetState(Z.target) : null);
  const [, setTick] = useState(0);
  useEffect(() => {
    return scheduler.every(FRAME_MS, () => {
      if (Z.target && tgt.current) targetMove(tgt.current, Z.target, { cpu: r.mCPU }, 1, Math.random);
      setTick((n) => n + 1);
    });
  }, []);
  // the HUD steps once per host reading, so it lives outside the animation tick
  const hudOps = useMemo(() => Z.hud && hudFrame(hud.current, {
    cpuBaseMHz: 2000, cpuPerf: r.mCpuPerf ?? 100, gpuClockMHz: r.mHwGpuClock, gpuLoad: r.mGpuLoad, load: r.mCPU,
  }, Z.hud, style), [r, style]);
  const targetOps = tgt.current && Z.target && targetFrame(tgt.current, { cpu: r.mCPU }, Z.target, style);
  const sphereOps = Z.sphere && sphereFrame(sph.current, { downBps: r.netDown }, Z.sphere, style);
  const place = (zone: typeof Z.hud, ops: Op[] | null | undefined, name: string, mod: string) =>
    zone && ops && (
      <g transform={`matrix(${zone.matrix.join(' ')})`} data-module={mod}>
        <OpsView ops={ops} name={name} />
      </g>
    );
  return (
    <>
      {place(Z.target, targetOps, 'target', 'center-target')}
      {place(Z.hud, hudOps, 'hud', 'center-hud')}
      {place(Z.sphere, sphereOps, 'sphere', 'center-sphere')}
    </>
  );
}
