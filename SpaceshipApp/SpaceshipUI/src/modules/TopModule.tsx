import { useMemo, useState } from 'preact/hooks';
import layout from '../generated/layout.json';
import type { Op, Style } from '../draw/canvas';
import { OpsView } from '../draw/ops';
import { num } from '../lib/theme';
import { readingsFrom, systemMetrics } from '../host/systemMetrics';
import { alertFrame, type AlertState } from './alert';
import { batteryFrame, type BatteryState } from './battery';
import { consoleFrame, type ConsoleConfig, type ConsoleState, type ConsoleView } from './console';
import { graphFrame, graphState, selectSource, type GraphState } from './graph';
import { type Readings } from './readings';
import { powerFrame } from './power';

const zoneOf = (id: string) => layout.zones.find((z) => z.id === id);
/** Zones of the top console, read once. Each is drawn in its own skewed matrix. */
const Z = {
  cpu: zoneOf('G1_cpu'), ram: zoneOf('G4_ram'), a: zoneOf('G2_select'), b: zoneOf('G3_select'), power: zoneOf('T_power'),
  battery: zoneOf('T_battery'), alert: zoneOf('T_alert'), settings: zoneOf('T_settings'),
};

// The console has no host status yet (the Legion Toolkit runner is not built): it shows the unknown state, as console.lua does with no status.
const NO_STATUS: ConsoleState = { hybrid: '', power: '', refresh: '', battery: '', dgpu: '' };
const NO_VIEW: ConsoleView = { armed: null, hudHidden: false, msg: '', msgAt: 0 };

type TopState = { cpu: GraphState; ram: GraphState; a: GraphState; b: GraphState; battery: BatteryState; alert: AlertState };

/** Top console: CPU and RAM graphs, two select graphs (GraphA and GraphB sources), power, battery, alert and the console. Behind ?module=top. */
export function TopModule({ style, values }: { style: Style; values: Record<string, string> }) {
  const m = systemMetrics.value;
  const [st, setSt] = useState<TopState>(() => ({
    cpu: graphState('cpu'), ram: graphState('ram'), a: graphState(values.GraphA_Source ?? 'gpu'),
    b: graphState(values.GraphB_Source ?? 'netdown'), battery: { samples: [] }, alert: { blink: 0 },
  }));
  const cfg: ConsoleConfig = {
    powerModes: (values.LltPowerModes ?? 'quiet,balance,performance').split(','),
    rates: (values.LltRefreshRates ?? '60,165').split(','),
    conserveWord: values.LltBatteryConserve ?? 'conservation', normalWord: values.LltBatteryNormal ?? 'normal',
    chargeLimit: num(values, 'ChargeLimit', 80), perfOverride: num(values, 'PerfOverride', -1), perfTier: num(values, 'PerfTier', 0),
  };
  // one sample per host reading: the graph history and the alert blink advance when the reading changes, not on every render
  const ops = useMemo(() => {
    const r: Readings = m ? readingsFrom(m) : {};
    const now = Date.now();
    return {
      cpu: Z.cpu && graphFrame(st.cpu, r, Z.cpu, style, 'fixed').ops,
      ram: Z.ram && graphFrame(st.ram, r, Z.ram, style, 'fixed').ops,
      a: Z.a && graphFrame(st.a, r, Z.a, style, 'select').ops,
      b: Z.b && graphFrame(st.b, r, Z.b, style, 'select').ops,
      power: Z.power && powerFrame({ cpu: r.mHwCpuPower, gpu: r.mHwGpuPower, chargeRate: r.mHwChargeRate }, Z.power, style).ops,
      battery: Z.battery && batteryFrame(r, Z.battery, style, st.battery, now).ops,
      alert: Z.alert && alertFrame(r, Z.alert, style, st.alert).ops,
      settings: Z.settings && consoleFrame(NO_STATUS, cfg, NO_VIEW, Z.settings, style, now).ops,
    };
    // cfg and style are not in the deps: a settings change shows on the next host reading
  }, [m, st]);
  // a click moves a select graph to the next source (right click the previous one); the history starts again
  const step = (k: 'a' | 'b', dir: number) => setSt((s) => (k === 'a' ? { ...s, a: selectSource(s.a, dir) } : { ...s, b: selectSource(s.b, dir) }));
  const place = (zone: typeof Z.cpu, list: Op[] | undefined, name: string, mod: string) =>
    zone && list && (
      <g transform={`matrix(${zone.matrix.join(' ')})`} data-module={mod}>
        <OpsView ops={list} name={name} />
      </g>
    );
  return (
    <>
      {place(Z.cpu, ops.cpu, 'cpu', 'graph-cpu')}
      {place(Z.ram, ops.ram, 'ram', 'graph-ram')}
      {place(Z.a, ops.a, 'ga', 'graph-a')}
      {place(Z.b, ops.b, 'gb', 'graph-b')}
      {place(Z.power, ops.power, 'pw', 'power')}
      {place(Z.battery, ops.battery, 'tb', 'battery')}
      {place(Z.alert, ops.alert, 'ta', 'alert')}
      {place(Z.settings, ops.settings, 'cs', 'console')}
      {Z.a && (
        <rect x={Z.a.x} y={Z.a.y} width={Z.a.w} height={Z.a.h} fill="transparent" style={{ cursor: 'pointer' }}
          onClick={() => step('a', 1)} onContextMenu={(e) => { e.preventDefault(); step('a', -1); }} />
      )}
      {Z.b && (
        <rect x={Z.b.x} y={Z.b.y} width={Z.b.w} height={Z.b.h} fill="transparent" style={{ cursor: 'pointer' }}
          onClick={() => step('b', 1)} onContextMenu={(e) => { e.preventDefault(); step('b', -1); }} />
      )}
    </>
  );
}
