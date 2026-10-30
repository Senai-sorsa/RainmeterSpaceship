import { useMemo } from 'preact/hooks';
import layout from '../generated/layout.json';
import type { JSX } from 'preact';
import type { Style } from '../draw/canvas';
import { OpsView } from '../draw/ops';
import { appState, appStates, upkeepStatus } from '../host/statusFeed';
import { entryOf, type Catalog } from './apps';
import { catalogFeed } from './appsSource';
import { dotsFrame, MAXTABS, scanFrame, schematicFrame, selIndex, tabsFrame } from './category';
import { HitRect, launch, openSlot, slotTip, usePanel } from './hit';
import { slotRowFrame } from './slot';
import { visible } from './hidden';
import { upkeepFrame } from './upkeep';
import { host } from '../settings/instance';

const zoneOf = (id: string) => layout.zones.find((z) => z.id === id);
/** Zones of the left column. The mission clock (L_location) is its own module and is not drawn here. */
const ZONES = {
  tabs: zoneOf('L_tabs'), category: zoneOf('L_category'), dots: zoneOf('L_dots'), upkeep: zoneOf('L_upkeep'),
  slots: [zoneOf('L_app1'), zoneOf('L_app2'), zoneOf('L_app3'), zoneOf('L_app4')],
};

/**
 * Left column: the category tabs, the app schematic, the page dots, four slots and the upkeep block.
 * Behind ?module=left. The catalog is the labelled fixture until the host supplies Apps.ini; the RUNNING state is real
 * (from the host's process list). Clicks launch through the host (hit.tsx); the page and picks are local state.
 */
export function LeftModule({ style, hide = '', catalog = catalogFeed.value }: { style: Style; hide?: string; catalog?: Catalog }) {
  const Z = useMemo(() => visible(ZONES, hide), [hide]);
  const up = upkeepStatus.value;
  const { ci, cat, ai, app, state, choose, turn } = usePanel(catalog, 1);
  const nTabs = Math.min(MAXTABS, cat?.apps.length ?? 0);
  const first = Math.max(1, Math.min(ai - 2, (cat?.apps.length ?? 0) - MAXTABS + 1)); // the pick stays on the rail
  const states = appStates.value;
  const slots = useMemo(() => Z.slots.map((_, i) => entryOf(catalog, catalog.layout[`Slot${i + 1}`] ?? '')), [catalog, Z]);
  const ops = useMemo(() => ({
    tabs: Z.tabs && tabsFrame(cat, { first, sel: ai + 1 }, Z.tabs, style),
    cat: Z.category && schematicFrame(app, cat, appState(states, app?.proc) === 2, Z.category, style),
    scan: Z.category && scanFrame(Z.category, style),
    dots: Z.dots && dotsFrame(catalog.catOrder.length, ci + 1, Z.dots, style),
    slots: Z.slots.map((zone, i) => {
      const e = slots[i];
      if (!zone || !e) return undefined;
      // a folder row names its saved pick (LAST x), as slot.lua current() does
      const hit = e.kind === 'app' ? e.app : e.cat.apps[selIndex(e.cat, state)];
      return slotRowFrame({ app: hit, cat: e.kind === 'cat' ? e.cat : undefined, state: appState(states, hit?.proc), mirror: false }, zone, style);
    }),
    upkeep: Z.upkeep && upkeepFrame(up, Z.upkeep, style),
  }), [states, up, ci, ai, first, state, slots, catalog, style, Z]);
  const place = (zone: typeof ZONES.tabs, list: ReturnType<typeof tabsFrame> | undefined, name: string, mod: string, hit?: JSX.Element | false | null) =>
    zone && list && (
      <g transform={`matrix(${zone.matrix.join(' ')})`} data-module={mod}>
        <OpsView ops={list} name={name} />
        {hit}
      </g>
    );
  return (
    <>
      {place(Z.tabs, ops.tabs, 'tabs', 'left-tabs', Z.tabs && nTabs > 0 && (() => {
        const tab = (x: number) => first - 1 + Math.max(0, Math.min(nTabs - 1, Math.floor(((x - 16) / (Z.tabs!.w - 32)) * nTabs))); // shortcut: equal shares, not the justified label spans
        return <HitRect zone={Z.tabs} s={style.s} label="Category tabs" on={{ click: (x) => choose(cat, tab(x)), menu: (x) => launch(cat?.apps[tab(x)]), wheel: (d) => choose(cat, ai + d) }} />;
      })())}
      {place(Z.category, ops.cat, 'cat', 'left-category', Z.category && (
        <HitRect zone={Z.category} s={style.s} label="Launch the selected app" tip={app && `${app.name}${app.missing ? '   not found' : ''}`} on={{ click: () => launch(app), menu: () => launch(app), wheel: (d) => choose(cat, ai + d) }} />
      ))}
      {Z.category && ops.scan && (
        <g transform={`matrix(${Z.category.matrix.join(' ')})`}>
          <g class="scan" style={`--scan: ${Z.category.h * style.s}px`}><OpsView ops={ops.scan} name="scan" /></g>
        </g>
      )}
      {place(Z.dots, ops.dots, 'dots', 'left-dots', Z.dots && (
        <HitRect zone={Z.dots} s={style.s} label="Category pages" on={{ click: (x) => { const n = Math.min(catalog.catOrder.length, 12); turn(Math.min(n - 1, Math.floor((x / Z.dots!.w) * n))); }, wheel: (d) => turn(ci + d) }} />
      ))}
      {Z.slots.map((zone, i) => {
        const e = slots[i];
        const pickOf = () => (e?.kind === 'cat' ? e.cat.apps[selIndex(e.cat, state)] : e?.app);
        return place(zone, ops.slots[i], `slot${i + 1}`, `left-slot${i + 1}`, zone && e && (
          <HitRect zone={zone} s={style.s} tip={slotTip(e, i + 1)} label={`Slot ${i + 1}`} on={{ click: () => openSlot(e, pickOf()), menu: () => launch(pickOf()),
            wheel: (d) => e.kind === 'cat' && choose(e.cat, selIndex(e.cat, state) + d) }} />
        ));
      })}
      {/* status_block.lua OnClick: row 1 Windows Update, row 2 Gmail */}
      {place(Z.upkeep, ops.upkeep, 'upkeep', 'left-upkeep', Z.upkeep && (
        <>
          <HitRect zone={Z.upkeep} s={style.s} box={{ x: 0, y: 0, w: Z.upkeep.w, h: Z.upkeep.h / 2 }} label="Windows Update" tip="Pending Windows updates" on={{ click: () => host.send({ type: 'target.open', what: 'update' }), menu: () => host.send({ type: 'status.refresh', kind: 'upkeep' }) }} />
          <HitRect zone={Z.upkeep} s={style.s} box={{ x: 0, y: Z.upkeep.h / 2, w: Z.upkeep.w, h: Z.upkeep.h / 2 }} label="Gmail" tip={up.mail !== undefined ? undefined : up.mailWhy === 'off' ? 'Gmail not set up' : `Gmail: ${up.mailWhy ?? '?'}`} on={{ click: () => host.send({ type: 'target.open', what: 'gmail' }), menu: () => host.send({ type: 'status.refresh', kind: 'mail' }) }} />
        </>
      ))}
    </>
  );
}
