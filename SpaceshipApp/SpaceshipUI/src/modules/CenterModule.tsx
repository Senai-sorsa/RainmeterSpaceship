import { useEffect, useMemo, useRef, useState } from 'preact/hooks';
import layout from '../generated/layout.json';
import type { JSX } from 'preact';
import type { Op, Style } from '../draw/canvas';
import { OpsView } from '../draw/ops';
import { scheduler, skinMs } from '../host/scheduler';
import { readingsFrom, systemMetrics } from '../host/systemMetrics';
import { speedStatus, spxStatus, todoStatus, topProcs } from '../host/statusFeed';
import { HUD_HITS, hudFrame, hudState, type HudState } from './hud';
import { type Readings } from './readings';
import { speedTip } from './sysinfo';
import { NET_HIT, SPHERE_HIT, sphereFrame, sphereState, type SphereState } from './sphere';
import { reticleBox, targetFrame, targetMove, targetState, targetTip, type TargetState } from './target';
import { HitRect } from './hit';
import { host } from '../settings/instance';
import { visible } from './hidden';

/** hud.lua's S&P caption, condensed: price, day change and whether the market is open. */
const spxTip = (x: { spxPrice?: number; spxPrev?: number; spxOpen?: boolean }) => x.spxPrice === undefined || !x.spxPrev ? 'S&P 500 waiting for data'
  : `S&P 500 ${x.spxPrice.toFixed(1)}   ${((x.spxPrice - x.spxPrev) / x.spxPrev * 100).toFixed(2).replace(/^(?!-)/, '+')}%   ${x.spxOpen ? 'open' : 'closed'}`;
const zoneOf = (id: string) => layout.zones.find((z) => z.id === id);
/** Zones of the centre: the target reticle, the HUD ladders and the sphere. */
const ZONES = { target: zoneOf('C_target'), hud: zoneOf('C_hud'), sphere: zoneOf('C_sphere') };
const FRAME_MS = skinMs(50); // Update=50, ~16 fps in Rainmeter (full tier of target.lua); half on Lite, parked from Low up

/**
 * Centre: the target reticle roaming the windscreen, the HUD ladders and the sphere. Behind ?module=center.
 * The reticle and the sphere animate on a 20 fps timer; the HUD eases once per host reading. The reticle and sphere
 * show -- or TEST where the host does not supply the figure yet (speed test, GPU load).
 */
export function CenterModule({ style, sphere = true, hide = '', link = 0, linkUp = 0 }: { style: Style; sphere?: boolean; hide?: string; link?: number; linkUp?: number }) {
  const speed = speedStatus.value;
  const testing = speed.state === 'testing';
  const Z = useMemo(() => visible(ZONES, hide), [hide]);
  const m = systemMetrics.value;
  const spx = spxStatus.value;
  const todo = todoStatus.value;
  const [rank, setRank] = useState(1); // target.lua OnClick / OnScroll: the 1st to 5th busiest process
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
  const sphereOps = sphere && tier < 3 ? Z.sphere && sphereFrame(sph.current, { downBps: r.netDown, linkDownMbps: link, testing }, Z.sphere, style) : null;
  const place = (zone: typeof ZONES.hud, ops: Op[] | null | undefined, name: string, mod: string, hit?: JSX.Element | false | null) =>
    zone && ops && (
      <g transform={`matrix(${zone.matrix.join(' ')})`} data-module={mod}>
        <OpsView ops={ops} name={name} />
        {hit}
      </g>
    );
  return (
    <>
      {place(Z.target, targetOps, 'target', 'center-target', Z.target && tgt.current && (
        <HitRect zone={Z.target} s={style.s} box={reticleBox(tgt.current)} label={todo.items.length ? 'Open the to-do note' : `Target ${rank}`}
          tip={targetTip({ name: proc?.name, cpu: proc?.cpu, ram: proc?.ram, todos: todo.items, todoCount: todo.count })}
          on={{ click: () => (todo.items.length ? host.send({ type: 'target.open', what: 'todo' }) : setRank((n) => (n % 5) + 1)),
            menu: () => host.send({ type: 'target.open', what: 'taskmgr' }), wheel: (d) => setRank((n) => ((n - 1 + d + 5) % 5) + 1) }} />
      ))}
      {place(Z.hud, hudOps, 'hud', 'center-hud', Z.hud && (
        <>
          <HitRect zone={Z.hud} s={style.s} box={HUD_HITS.gpu} label="Task Manager" on={{ click: () => host.send({ type: 'target.open', what: 'taskmgr' }) }} />
          <HitRect zone={Z.hud} s={style.s} box={HUD_HITS.spx} label="S&P 500" tip={spxTip(spx)} on={{ click: () => host.send({ type: 'target.open', what: 'spx' }) }} />
        </>
      ))}
      {place(Z.sphere, sphereOps, 'sphere', 'center-sphere', Z.sphere && (
        <>
          <HitRect zone={Z.sphere} s={style.s} box={SPHERE_HIT} label="Task Manager" on={{ click: () => host.send({ type: 'target.open', what: 'taskmgr' }) }} />
          <HitRect zone={Z.sphere} s={style.s} box={NET_HIT} label="Speed test" tip={speedTip(speed.state, speed.why, linkUp)} on={{ click: () => { if (!testing) host.send({ type: 'speed.run' }); } }} />
        </>
      ))}
    </>
  );
}
