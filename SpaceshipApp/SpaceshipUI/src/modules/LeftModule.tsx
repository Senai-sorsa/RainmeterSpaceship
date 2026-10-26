import { useMemo, useState } from 'preact/hooks';
import layout from '../generated/layout.json';
import type { Style } from '../draw/canvas';
import { OpsView } from '../draw/ops';
import { systemMetrics } from '../host/systemMetrics';
import { upkeepStatus } from '../host/statusFeed';
import { entryOf, type Catalog } from './apps';
import { catalogFeed } from './appsSource';
import { dotsFrame, scanFrame, schematicFrame, tabsFrame } from './category';
import { slotRowFrame } from './slot';
import { visible } from './hidden';
import { upkeepFrame } from './upkeep';

const zoneOf = (id: string) => layout.zones.find((z) => z.id === id);
/** Zones of the left column. The mission clock (L_location) is its own module and is not drawn here. */
const ZONES = {
  tabs: zoneOf('L_tabs'), category: zoneOf('L_category'), dots: zoneOf('L_dots'), upkeep: zoneOf('L_upkeep'),
  slots: [zoneOf('L_app1'), zoneOf('L_app2'), zoneOf('L_app3'), zoneOf('L_app4')],
};

/**
 * Left column: the category tabs, the app schematic, the page dots, four slots and the upkeep block.
 * Behind ?module=left. The catalog is the labelled fixture until the host supplies Apps.ini; the RUNNING state is real
 * (from the host's process list). Panel selection is local state; clicks are not wired yet.
 */
export function LeftModule({ style, hide = '', catalog = catalogFeed.value }: { style: Style; hide?: string; catalog?: Catalog }) {
  const Z = useMemo(() => visible(ZONES, hide), [hide]);
  const m = systemMetrics.value;
  const up = upkeepStatus.value;
  // index into catalog.catOrder, the page shown: Apps.ini Layout Top1 (apps.lua)
  const ci = Math.max(0, catalog.catOrder.indexOf(catalog.layout.Top1 ?? ''));
  const [ai, setAi] = useState(0); // index into the category's apps, the app shown
  const catId = catalog.catOrder[ci];
  const cat = catId ? catalog.cats[catId] : undefined;
  const app = cat?.apps[ai];
  const running = (proc: string) => proc !== '' && m?.processes[proc] === true;
  const ops = useMemo(() => ({
    tabs: Z.tabs && tabsFrame(cat, { first: 1, sel: ai + 1 }, Z.tabs, style),
    cat: Z.category && schematicFrame(app, cat, app ? running(app.proc) : false, Z.category, style),
    scan: Z.category && scanFrame(Z.category, style),
    dots: Z.dots && dotsFrame(catalog.catOrder.length, ci + 1, Z.dots, style),
    slots: Z.slots.map((zone, i) => {
      const e = entryOf(catalog, catalog.layout[`Slot${i + 1}`] ?? '');
      if (!zone || !e) return undefined;
      const hit = e.kind === 'app' ? e.app : undefined;
      return slotRowFrame({ app: hit, cat: e.kind === 'cat' ? e.cat : undefined, running: hit ? running(hit.proc) : false, mirror: false }, zone, style);
    }),
    upkeep: Z.upkeep && upkeepFrame(up, Z.upkeep, style),
  }), [m, up, ci, ai, catalog, style, Z]);
  const place = (zone: typeof ZONES.tabs, list: ReturnType<typeof tabsFrame> | undefined, name: string, mod: string) =>
    zone && list && (
      <g transform={`matrix(${zone.matrix.join(' ')})`} data-module={mod}>
        <OpsView ops={list} name={name} />
      </g>
    );
  return (
    <>
      {place(Z.tabs, ops.tabs, 'tabs', 'left-tabs')}
      {place(Z.category, ops.cat, 'cat', 'left-category')}
      {Z.category && ops.scan && (
        <g transform={`matrix(${Z.category.matrix.join(' ')})`}>
          <g class="scan" style={`--scan: ${Z.category.h * style.s}px`}><OpsView ops={ops.scan} name="scan" /></g>
        </g>
      )}
      {place(Z.dots, ops.dots, 'dots', 'left-dots')}
      {Z.slots.map((zone, i) => place(zone, ops.slots[i], `slot${i + 1}`, `left-slot${i + 1}`))}
      {place(Z.upkeep, ops.upkeep, 'upkeep', 'left-upkeep')}
    </>
  );
}
