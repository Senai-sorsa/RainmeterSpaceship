import { useMemo, useState } from 'preact/hooks';
import layout from '../generated/layout.json';
import type { Style } from '../draw/canvas';
import { OpsView } from '../draw/ops';
import { readingsFrom, systemMetrics } from '../host/systemMetrics';
import { devStatus, netRows, netStatus } from '../host/statusFeed';
import { entryOf, type Catalog } from './apps';
import { catalogFeed } from './appsSource';
import { dotsFrame, schematicFrame, tabsFrame } from './category';
import { devFrame } from './dev';
import { type Readings } from './readings';
import { slotRowFrame } from './slot';
import { visible } from './hidden';
import { sysinfoFrame } from './sysinfo';

const zoneOf = (id: string) => layout.zones.find((z) => z.id === id);
/** Zones of the right column. Same parts as the left, mirrored, plus the network block and the dev block. */
const ZONES = {
  tabs: zoneOf('R_tabs'), category: zoneOf('R_category'), dots: zoneOf('R_dots'), sysinfo: zoneOf('R_sysinfo'), dev: zoneOf('R_dev'),
  slots: [zoneOf('R_app1'), zoneOf('R_app2'), zoneOf('R_app3'), zoneOf('R_app4')],
};

/**
 * Right column: category tabs, app schematic, page dots, slots 5-8 (mirrored), the network block and the dev block.
 * Behind ?module=right. The catalog is the labelled fixture (see appsSource.ts). Feeds that the host does not supply yet
 * (ping, LAN, WAN, WSL, Ollama, speed test) show --. Clicks are not wired.
 */
export function RightModule({ style, hide = '', catalog = catalogFeed.value, mask = true }: { style: Style; hide?: string; catalog?: Catalog; mask?: boolean }) {
  const Z = useMemo(() => visible(ZONES, hide), [hide]);
  const m = systemMetrics.value;
  const dev = devStatus.value;
  const net = netStatus.value;
  const r: Readings = useMemo(() => (m ? readingsFrom(m) : {}), [m]);
  // the page shown: Apps.ini Layout Top2 (apps.lua)
  const ci = Math.max(0, catalog.catOrder.indexOf(catalog.layout.Top2 ?? ''));
  const [ai, setAi] = useState(0);
  const catId = catalog.catOrder[ci];
  const cat = catId ? catalog.cats[catId] : undefined;
  const app = cat?.apps[ai];
  const running = (proc: string) => proc !== '' && m?.processes[proc] === true;
  const ops = useMemo(() => ({
    tabs: Z.tabs && tabsFrame(cat, { first: 1, sel: ai + 1 }, Z.tabs, style),
    cat: Z.category && schematicFrame(app, cat, app ? running(app.proc) : false, Z.category, style),
    dots: Z.dots && dotsFrame(catalog.catOrder.length, ci + 1, Z.dots, style),
    slots: Z.slots.map((zone, i) => {
      const e = entryOf(catalog, catalog.layout[`Slot${i + 5}`] ?? '');
      if (!zone || !e) return undefined;
      const hit = e.kind === 'app' ? e.app : undefined;
      return slotRowFrame({ app: hit, cat: e.kind === 'cat' ? e.cat : undefined, running: hit ? running(hit.proc) : false, mirror: true }, zone, style);
    }),
    sysinfo: Z.sysinfo && sysinfoFrame({ wifi: r.mWifi, down: r.netDown, up: r.netUp, ...netRows(net, mask) }, Z.sysinfo, style),
    dev: Z.dev && devFrame(dev, Z.dev, style),
  }), [m, dev, net, mask, ci, ai, catalog, style, Z]);
  const place = (zone: typeof ZONES.tabs, list: ReturnType<typeof tabsFrame> | undefined, name: string, mod: string) =>
    zone && list && (
      <g transform={`matrix(${zone.matrix.join(' ')})`} data-module={mod}>
        <OpsView ops={list} name={name} />
      </g>
    );
  return (
    <>
      {place(Z.tabs, ops.tabs, 'tabs', 'right-tabs')}
      {place(Z.category, ops.cat, 'cat', 'right-category')}
      {place(Z.dots, ops.dots, 'dots', 'right-dots')}
      {Z.slots.map((zone, i) => place(zone, ops.slots[i], `slot${i + 5}`, `right-slot${i + 5}`))}
      {place(Z.sysinfo, ops.sysinfo, 'sys', 'right-sysinfo')}
      {place(Z.dev, ops.dev, 'dev', 'right-dev')}
    </>
  );
}
