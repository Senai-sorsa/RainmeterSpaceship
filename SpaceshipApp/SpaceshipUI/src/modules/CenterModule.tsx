import { useEffect, useMemo, useRef, useState } from 'preact/hooks';
import layout from '../generated/layout.json';
import type { Op, Style } from '../draw/canvas';
import { OpsView } from '../draw/ops';
import { scheduler, skinMs } from '../host/scheduler';
import { readingsFrom, systemMetrics } from '../host/systemMetrics';
import { spxStatus, todoStatus, topProcs } from '../host/statusFeed';
import { hudFrame, hudState, type HudState } from './hud';
import { type Readings } from './readings';
import { sphereFrame, sphereState, type SphereState } from './sphere';
import { targetFrame, targetMove, targetState, type TargetState } from './target';
import { visible } from './hidden';

const zoneOf = (id: string) => layout.zones.find((z) => z.id === id);
/** Zones of the centre: the target reticle, the HUD ladders and the sphere. */
const ZONES = { target: zoneOf('C_target'), hud: zoneOf('C_hud'), sphere: zoneOf('C_sphere') };
const FRAME_MS = skinMs(50); // Update=50, ~16 fps in Rainmeter (full tier of target.lua); half on Lite, parked from Low up

/**
 * Centre: the target reticle roaming the windscreen, the HUD ladders and the sphere. Behind ?module=center.
 * The reticle and the sphere animate on a 20 fps timer; the HUD eases once per host reading. The reticle and sphere
 * show -- or TEST where the host does not supply the figure yet (speed test, GPU load).
 */
export function CenterModule({ style, sphere = true, hide = '' }: { style: Style; sphere?: boolean; hide?: string }) {
  const Z = useMemo(() => visible(ZONES, hide), [hide]);
  const m = systemMetrics.value;
  const spx = spxStatus.value;
  const todo = todoStatus.value;
  const rank = 1; // shortcut: rank 1 only, the click/scroll rank change of target.lua comes with the targeter's clicks
  const proc = topProcs.value[rank - 1];
  const pNow = useRef(proc);
  pNow.current = proc; // the timer below is set once, so it reads the latest process through this ref
  const r: Readings = useMemo(() => (m ? readingsFrom(m) : {}), [m]);
  const hud = useRef<HudState>(hudState());
  const sph = useRef<SphereState>(sphereState());
  const tgt = useRef<TargetState | null>(ZONES.target ? targetState(ZONES.target) : null);
  const [, setTick] = useState(0);
  const tier = style.tier;
  useEffect(() => {
    if (tier >= 2 || (!Z.target && !Z.sphere)) return; // nothing left to animate
    return scheduler.every(FRAME_MS * (tier === 1 ? 2 : 1), () => {
      if (Z.target && tgt.current) targetMove(tgt.current, Z.target, { name: pNow.current?.name }, 1, Math.random);
      setTick((n) => n + 1);
    });
  }, [tier, Z]);
  // the HUD steps once per host reading, so it lives outside the animation tick
  const hudOps = useMemo(() => Z.hud && hudFrame(hud.current, {
    cpuBaseMHz: 2000, cpuPerf: r.mCpuPerf ?? 100, gpuClockMHz: r.mHwGpuClock, gpuLoad: r.mGpuLoad, load: r.mCPU, ...spx,
  }, Z.hud, style), [r, spx, style, Z]);
  const targetOps = tgt.current && Z.target && targetFrame(tgt.current, { rank, cpu: proc?.cpu, ram: proc?.ram, todos: todo.items, todoCount: todo.count }, Z.target, style);
  const sphereOps = sphere && tier < 3 ? Z.sphere && sphereFrame(sph.current, { downBps: r.netDown }, Z.sphere, style) : null;
  const place = (zone: typeof ZONES.hud, ops: Op[] | null | undefined, name: string, mod: string) =>
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
