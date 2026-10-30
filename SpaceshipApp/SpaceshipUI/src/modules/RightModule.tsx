import { useMemo } from 'preact/hooks';
import layout from '../generated/layout.json';
import type { JSX } from 'preact';
import type { Style } from '../draw/canvas';
import { OpsView } from '../draw/ops';
import { readingsFrom, systemMetrics } from '../host/systemMetrics';
import { appState, appStates, devStatus, netRows, netStatus, speedStatus } from '../host/statusFeed';
import { entryOf, type Catalog } from './apps';
import { catalogFeed } from './appsSource';
import { dotsFrame, MAXTABS, scanFrame, schematicFrame, selIndex, tabsFrame } from './category';
import { HitRect, launch, openSlot, slotTip, usePanel } from './hit';
import { devFrame } from './dev';
import { type Readings } from './readings';
import { slotRowFrame } from './slot';
import { visible } from './hidden';
import { ipMaskBox, speedBox, speedTip, sysinfoFrame } from './sysinfo';
import { host, store } from '../settings/instance';

const zoneOf = (id: string) => layout.zones.find((z) => z.id === id);
/** Zones of the right column. Same parts as the left, mirrored, plus the network block and the dev block. */
const ZONES = {
  tabs: zoneOf('R_tabs'), category: zoneOf('R_category'), dots: zoneOf('R_dots'), sysinfo: zoneOf('R_sysinfo'), dev: zoneOf('R_dev'),
  slots: [zoneOf('R_app1'), zoneOf('R_app2'), zoneOf('R_app3'), zoneOf('R_app4')],
};

/**
 * Right column: category tabs, app schematic, page dots, slots 5-8 (mirrored), the network block and the dev block.
 * Behind ?module=right. The catalog is the labelled fixture (see appsSource.ts). Feeds that the host does not supply yet
 * (ping, LAN, WAN, WSL, Ollama, speed test) show --. Clicks as the left column (hit.tsx).
 */
export function RightModule({ style, hide = '', catalog = catalogFeed.value, mask = true, link = 0, linkUp = 0 }: { style: Style; hide?: string; catalog?: Catalog; mask?: boolean; link?: number; linkUp?: number }) {
  const speed = speedStatus.value;
  const testing = speed.state === 'testing';
  const Z = useMemo(() => visible(ZONES, hide), [hide]);
  const m = systemMetrics.value;
  const dev = devStatus.value;
  const net = netStatus.value;
  const r: Readings = useMemo(() => (m ? readingsFrom(m) : {}), [m]);
  const { ci, cat, ai, app, state, choose, turn } = usePanel(catalog, 2);
  const nTabs = Math.min(MAXTABS, cat?.apps.length ?? 0);
  const first = Math.max(1, Math.min(ai - 2, (cat?.apps.length ?? 0) - MAXTABS + 1)); // the pick stays on the rail
  const states = appStates.value;
  const slots = useMemo(() => Z.slots.map((_, i) => entryOf(catalog, catalog.layout[`Slot${i + 5}`] ?? '')), [catalog, Z]);
  const ops = useMemo(() => ({
    tabs: Z.tabs && tabsFrame(cat, { first, sel: ai + 1 }, Z.tabs, style),
    cat: Z.category && schematicFrame(app, cat, appState(states, app?.proc) === 2, Z.category, style),
    scan: Z.category && scanFrame(Z.category, style),
    dots: Z.dots && dotsFrame(catalog.catOrder.length, ci + 1, Z.dots, style),
    slots: Z.slots.map((zone, i) => {
      const e = slots[i];
      if (!zone || !e) return undefined;
      const hit = e.kind === 'app' ? e.app : e.cat.apps[selIndex(e.cat, state)];
      return slotRowFrame({ app: hit, cat: e.kind === 'cat' ? e.cat : undefined, state: appState(states, hit?.proc), mirror: true }, zone, style);
    }),
    sysinfo: Z.sysinfo && sysinfoFrame({ wifi: r.mWifi, down: r.netDown, up: r.netUp, link, testing, ...netRows(net, mask) }, Z.sysinfo, style),
    dev: Z.dev && devFrame(dev, Z.dev, style),
  }), [r, states, dev, net, mask, link, testing, ci, ai, first, state, slots, catalog, style, Z]);
  const open = (what: string) => () => host.send({ type: 'target.open', what });
  const place = (zone: typeof ZONES.tabs, list: ReturnType<typeof tabsFrame> | undefined, name: string, mod: string, hit?: JSX.Element | false | null) =>
    zone && list && (
      <g transform={`matrix(${zone.matrix.join(' ')})`} data-module={mod}>
        <OpsView ops={list} name={name} />
        {hit}
      </g>
    );
  return (
    <>
      {place(Z.tabs, ops.tabs, 'tabs', 'right-tabs', Z.tabs && nTabs > 0 && (() => {
        const tab = (x: number) => first - 1 + Math.max(0, Math.min(nTabs - 1, Math.floor(((x - 16) / (Z.tabs!.w - 32)) * nTabs))); // shortcut: equal shares, not the justified label spans
        return <HitRect zone={Z.tabs} s={style.s} label="Category tabs" on={{ click: (x) => choose(cat, tab(x)), menu: (x) => launch(cat?.apps[tab(x)]), wheel: (d) => choose(cat, ai + d) }} />;
      })())}
      {place(Z.category, ops.cat, 'cat', 'right-category', Z.category && (
        <HitRect zone={Z.category} s={style.s} label="Launch the selected app" tip={app && `${app.name}${app.missing ? '   not found' : ''}`} on={{ click: () => launch(app), menu: () => launch(app), wheel: (d) => choose(cat, ai + d) }} />
      ))}
      {Z.category && ops.scan && (
        <g transform={`matrix(${Z.category.matrix.join(' ')})`}>
          <g class="scan" style={`--scan: ${Z.category.h * style.s}px`}><OpsView ops={ops.scan} name="rscan" /></g>
        </g>
      )}
      {place(Z.dots, ops.dots, 'dots', 'right-dots', Z.dots && (
        <HitRect zone={Z.dots} s={style.s} label="Category pages" on={{ click: (x) => { const n = Math.min(catalog.catOrder.length, 12); turn(Math.min(n - 1, Math.floor((x / Z.dots!.w) * n))); }, wheel: (d) => turn(ci + d) }} />
      ))}
      {Z.slots.map((zone, i) => {
        const e = slots[i];
        const pickOf = () => (e?.kind === 'cat' ? e.cat.apps[selIndex(e.cat, state)] : e?.app);
        return place(zone, ops.slots[i], `slot${i + 5}`, `right-slot${i + 5}`, zone && e && (
          <HitRect zone={zone} s={style.s} tip={slotTip(e, i + 5)} label={`Slot ${i + 5}`} on={{ click: () => openSlot(e, pickOf()), menu: () => launch(pickOf()),
            wheel: (d) => e.kind === 'cat' && choose(e.cat, selIndex(e.cat, state) + d) }} />
        ));
      })}
      {/* sysinfo.lua and status_block.lua OnClick, as fixed host targets */}
      {place(Z.sysinfo, ops.sysinfo, 'sys', 'right-sysinfo', Z.sysinfo && (
        <>
          <HitRect zone={Z.sysinfo} s={style.s} label="Network status" on={{ click: open('network'), menu: open('wifi') }} />
          <HitRect zone={Z.sysinfo} s={style.s} box={ipMaskBox(Z.sysinfo.w)} label={mask ? 'Show IP' : 'Mask IP'} on={{ click: () => store.set('IpMask', mask ? '0' : '1'), menu: open('wifi') }} />
          <HitRect zone={Z.sysinfo} s={style.s} box={speedBox(Z.sysinfo.w)} label="Speed test" tip={speedTip(speed.state, speed.why, linkUp)} on={{ click: () => { if (!testing) host.send({ type: 'speed.run' }); }, menu: open('wifi') }} />
        </>
      ))}
      {place(Z.dev, ops.dev, 'dev', 'right-dev', Z.dev && (
        <>
          <HitRect zone={Z.dev} s={style.s} box={{ x: 0, y: 0, w: Z.dev.w, h: Z.dev.h / 2 }} label="Terminal" tip="Running WSL distros" on={{ click: open('terminal'), menu: () => host.send({ type: 'status.refresh', kind: 'dev' }) }} />
          <HitRect zone={Z.dev} s={style.s} box={{ x: 0, y: Z.dev.h / 2, w: Z.dev.w, h: Z.dev.h / 2 }} label="Ollama models" tip="Ollama models loaded" on={{ click: open('ollama'), menu: () => host.send({ type: 'status.refresh', kind: 'dev' }) }} />
        </>
      ))}
    </>
  );
}
