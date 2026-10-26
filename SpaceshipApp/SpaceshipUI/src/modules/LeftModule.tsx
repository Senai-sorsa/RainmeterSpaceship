import { useMemo, useState } from 'preact/hooks';
import layout from '../generated/layout.json';
import type { Style } from '../draw/canvas';
import { OpsView } from '../draw/ops';
import { appState, appStates, upkeepStatus } from '../host/statusFeed';
import { entryOf, type Catalog } from './apps';
import { catalogFeed, SKIN_STATE } from './appsSource';
import { dotsFrame, scanFrame, schematicFrame, selIndex, skinPick, tabsFrame } from './category';
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
  const up = upkeepStatus.value;
  // the page (index into catalog.catOrder) and app the skin last showed; ai stays null until a pick of its own
  const pick = useMemo(() => skinPick(catalog, 1, SKIN_STATE), [catalog]);
  const ci = pick.ci;
  const [picked, setAi] = useState<number | null>(null);
  const ai = picked ?? pick.ai;
  const catId = catalog.catOrder[ci];
  const cat = catId ? catalog.cats[catId] : undefined;
  const app = cat?.apps[ai];
  const states = appStates.value;
  const ops = useMemo(() => ({
    tabs: Z.tabs && tabsFrame(cat, { first: 1, sel: ai + 1 }, Z.tabs, style),
    cat: Z.category && schematicFrame(app, cat, appState(states, app?.proc) === 2, Z.category, style),
    scan: Z.category && scanFrame(Z.category, style),
    dots: Z.dots && dotsFrame(catalog.catOrder.length, ci + 1, Z.dots, style),
    slots: Z.slots.map((zone, i) => {
      const e = entryOf(catalog, catalog.layout[`Slot${i + 1}`] ?? '');
      if (!zone || !e) return undefined;
      // a folder row names its saved pick (LAST x), as slot.lua current() does
      const hit = e.kind === 'app' ? e.app : e.cat.apps[selIndex(e.cat, SKIN_STATE)];
      return slotRowFrame({ app: hit, cat: e.kind === 'cat' ? e.cat : undefined, state: appState(states, hit?.proc), mirror: false }, zone, style);
    }),
    upkeep: Z.upkeep && upkeepFrame(up, Z.upkeep, style),
  }), [states, up, ci, ai, catalog, style, Z]);
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
