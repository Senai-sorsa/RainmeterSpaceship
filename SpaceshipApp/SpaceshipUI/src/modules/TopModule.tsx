import { useMemo, useState } from 'preact/hooks';
import layout from '../generated/layout.json';
import type { Style } from '../draw/canvas';
import { OpsView } from '../draw/ops';
import { readingsFrom, systemMetrics } from '../host/systemMetrics';
import { alertFrame, type AlertState } from './alert';
import { batteryFrame, type BatteryState } from './battery';
import { graphFrame, graphState, type GraphState } from './graph';

const zoneOf = (id: string) => layout.zones.find((z) => z.id === id);

/** Top console: the CPU graph, the battery readout and the alert count, fed by the host's system.metrics. Behind ?module=top. */
export function TopModule({ style }: { style: Style }) {
  const m = systemMetrics.value;
  const [state] = useState(() => ({ graph: graphState('cpu') as GraphState, battery: { samples: [] } as BatteryState, alert: { blink: 0 } as AlertState }));
  // one frame per host message: the graph history and the alert blink advance when the reading changes, not on every render
  const frames = useMemo(() => {
    const r = m ? readingsFrom(m) : {};
    const now = Date.now();
    const g = zoneOf('G1_cpu'), b = zoneOf('T_battery'), a = zoneOf('T_alert');
    return {
      graph: g && graphFrame(state.graph, r, g, style, 'fixed'),
      battery: b && batteryFrame(r, b, style, state.battery, now),
      alert: a && alertFrame(r, a, style, state.alert),
    };
  }, [m]);
  const g = zoneOf('G1_cpu'), b = zoneOf('T_battery'), a = zoneOf('T_alert');
  return (
    <>
      {g && frames.graph && <g transform={`matrix(${g.matrix.join(' ')})`} data-module="graph-cpu"><OpsView ops={frames.graph.ops} name="g1" /></g>}
      {b && frames.battery && <g transform={`matrix(${b.matrix.join(' ')})`} data-module="battery"><OpsView ops={frames.battery.ops} name="tb" /></g>}
      {a && frames.alert && <g transform={`matrix(${a.matrix.join(' ')})`} data-module="alert"><OpsView ops={frames.alert.ops} name="ta" /></g>}
    </>
  );
}
