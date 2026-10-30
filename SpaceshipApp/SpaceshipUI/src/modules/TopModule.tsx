import { useEffect, useMemo, useState } from 'preact/hooks';
import layout from '../generated/layout.json';
import type { Op, Style } from '../draw/canvas';
import { OpsView } from '../draw/ops';
import { num } from '../lib/theme';
import { readingsFrom, systemMetrics } from '../host/systemMetrics';
import { consoleStatus } from '../host/statusFeed';
import { host, store } from '../settings/instance';
import { alertFrame, type AlertState } from './alert';
import { batteryFrame, type BatteryState } from './battery';
import { consoleFrame, consoleIntent, lltMessage, withHybridMode, type ConsoleConfig, type ConsoleView } from './console';
import { graphFrame, graphState, selectSource, type GraphState } from './graph';
import { type Readings } from './readings';
import { powerFrame } from './power';
import { visible } from './hidden';
import { HitRect } from './hit';
import { controlOpen, drawerOpen, hudHidden } from './overlays';

const zoneOf = (id: string) => layout.zones.find((z) => z.id === id);
/** Zones of the top console, read once. Each is drawn in its own skewed matrix. */
const ZONES = {
  cpu: zoneOf('G1_cpu'), ram: zoneOf('G4_ram'), a: zoneOf('G2_select'), b: zoneOf('G3_select'), power: zoneOf('T_power'),
  battery: zoneOf('T_battery'), alert: zoneOf('T_alert'), settings: zoneOf('T_settings'),
};

const NO_VIEW: ConsoleView = { armed: null, hudHidden: false, msg: '', msgAt: 0 };
let lltId = 1;
// controller.lua Master(): the tier before STEALTH, to go back to. shortcut: kept for this run only (the skin saves MasterPrev), add a key if a restart must keep it
let masterPrev = -1;

type TopState = { cpu: GraphState; ram: GraphState; a: GraphState; b: GraphState; battery: BatteryState; alert: AlertState };

/** Top console: CPU and RAM graphs, two select graphs (GraphA and GraphB sources), power, battery, alert and the console. Behind ?module=top. */
export function TopModule({ style, values, hide = '' }: { style: Style; values: Record<string, string>; hide?: string }) {
  const Z = useMemo(() => visible(ZONES, hide), [hide]);
  const m = systemMetrics.value;
  const cs = consoleStatus.value;
  const [st, setSt] = useState<TopState>(() => ({
    cpu: graphState('cpu'), ram: graphState('ram'), a: graphState(values.GraphA_Source ?? 'gpu'),
    b: graphState(values.GraphB_Source ?? 'netdown'), battery: { samples: [] }, alert: { blink: 0 },
  }));
  const [view, setView] = useState(NO_VIEW);
  const say = (msg: string) => setView((v) => ({ ...v, msg, msgAt: Date.now() }));
  useEffect(() => host.onMessage((r) => { if (r.type === 'llt.result') say(r.ran === true ? 'DONE' : 'FAILED'); }) || undefined, []);
  const cfg: ConsoleConfig = {
    powerModes: (values.LltPowerModes ?? 'quiet,balance,performance').split(','),
    rates: (values.LltRefreshRates ?? '60,165').split(','),
    conserveWord: values.LltBatteryConserve ?? 'conservation', normalWord: values.LltBatteryNormal ?? 'normal',
    chargeLimit: num(values, 'ChargeLimit', 80), perfOverride: num(values, 'PerfOverride', -1), perfTier: num(values, 'PerfTier', 0),
  };
  // one sample per host reading: the graph history and the alert blink advance when the reading changes, not on every render.
  // styleFrom builds a new object each Hud render, so the deps key on its contents: a Scale or colour change redraws at once
  const styleKey = JSON.stringify(style);
  const ops = useMemo(() => {
    const r: Readings = m ? readingsFrom(m) : {};
    const now = Date.now();
    return {
      cpu: Z.cpu && graphFrame(st.cpu, r, Z.cpu, style, 'fixed').ops,
      ram: Z.ram && graphFrame(st.ram, r, Z.ram, style, 'fixed').ops,
      a: Z.a && graphFrame(st.a, r, Z.a, style, 'select').ops,
      b: Z.b && graphFrame(st.b, r, Z.b, style, 'select').ops,
      power: Z.power && powerFrame({ cpu: r.mHwCpuPower, gpu: r.mHwGpuPower, chargeRate: r.mHwChargeRate }, Z.power, style),
      battery: Z.battery && batteryFrame(r, Z.battery, style, st.battery, now).ops,
      alert: Z.alert && alertFrame(r, Z.alert, style, st.alert),
      settings: Z.settings && consoleFrame(withHybridMode(cs, values), cfg, { ...view, hudHidden: hudHidden.value }, Z.settings, style, now),
    };
    // cfg is not in the deps: a console setting change shows on the next host reading
  }, [m, st, Z, styleKey, cs, view, hudHidden.value]);
  // console.lua OnClick: a Legion Toolkit switch goes to the host (DONE / SWITCH FAILED when it answers), the rest is the page's own
  const consoleClick = (k: number, button: 'left' | 'right' = 'left') => {
    const it = consoleIntent(k, withHybridMode(cs, values), cfg, view, button);
    const llt = lltMessage(it, lltId++);
    if (llt) { host.send(llt.msg); say(llt.say); return; }
    if (it.kind === 'action' && it.action === 'status.refresh') { host.send({ type: 'status.refresh' }); say('REFRESHING'); return; }
    if (it.kind !== 'ui') return;
    if (it.name === 'drawer') drawerOpen.value = drawerOpen.value ? null : {};
    else if (it.name === 'control') controlOpen.value = true;
    else if (it.name === 'hud') hudHidden.value = !hudHidden.value;
    else if (it.name === 'perf') store.set('PerfOverride', String(it.value));
    else if (it.name === 'master') {
      if (cfg.perfOverride === 3) store.set('PerfOverride', String(masterPrev));
      else { masterPrev = cfg.perfOverride; store.set('PerfOverride', '3'); }
    }
  };
  // a click moves a select graph to the next source (right click the previous one); the history starts again
  const step = (k: 'a' | 'b', dir: number) => setSt((s) => (k === 'a' ? { ...s, a: selectSource(s.a, dir) } : { ...s, b: selectSource(s.b, dir) }));
  const place = (zone: typeof ZONES.cpu, list: Op[] | undefined, name: string, mod: string, on?: { click: () => void; label: string; tip?: string }) =>
    zone && list && (
      <g transform={`matrix(${zone.matrix.join(' ')})`} data-module={mod}>
        <OpsView ops={list} name={name} />
        {on && <HitRect zone={zone} s={style.s} label={on.label} tip={on.tip} on={{ click: on.click }} />}
      </g>
    );
  return (
    <>
      {place(Z.cpu, ops.cpu, 'cpu', 'graph-cpu')}
      {place(Z.ram, ops.ram, 'ram', 'graph-ram')}
      {place(Z.a, ops.a, 'ga', 'graph-a')}
      {place(Z.b, ops.b, 'gb', 'graph-b')}
      {/* power.lua and alert.lua open the Control overlay, battery.lua the battery settings */}
      {place(Z.power, ops.power?.ops, 'pw', 'power', { click: () => { controlOpen.value = true; }, label: 'Control Center', tip: ops.power?.tip })}
      {place(Z.battery, ops.battery, 'tb', 'battery', { click: () => host.send({ type: 'target.open', what: 'battery' }), label: 'Battery settings' })}
      {place(Z.alert, ops.alert?.ops, 'ta', 'alert', { click: () => { controlOpen.value = true; }, label: 'Control Center', tip: ops.alert?.tip })}
      {Z.settings && ops.settings && (
        <g transform={`matrix(${Z.settings.matrix.join(' ')})`} data-module="console">
          <OpsView ops={ops.settings.ops} name="cs" />
          {ops.settings.hits.map((h) => <HitRect zone={Z.settings!} s={style.s} box={h} label={h.tip || (h.id === 6 ? 'CARGO hold' : 'Console')} tip={h.tip} on={{ click: () => consoleClick(h.id), menu: () => consoleClick(h.id, 'right') }} />)}
        </g>
      )}
      {Z.a && (
        <rect x={Z.a.x * style.s} y={Z.a.y * style.s} width={Z.a.w * style.s} height={Z.a.h * style.s} fill="transparent" data-hit style={{ cursor: 'pointer' }}
          onClick={() => step('a', 1)} onContextMenu={(e) => { e.preventDefault(); step('a', -1); }} />
      )}
      {Z.b && (
        <rect x={Z.b.x * style.s} y={Z.b.y * style.s} width={Z.b.w * style.s} height={Z.b.h * style.s} fill="transparent" data-hit style={{ cursor: 'pointer' }}
          onClick={() => step('b', 1)} onContextMenu={(e) => { e.preventDefault(); step('b', -1); }} />
      )}
    </>
  );
}
