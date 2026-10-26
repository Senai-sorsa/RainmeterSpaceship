import { useEffect, useRef, useState } from 'preact/hooks';
import layout from '../generated/layout.json';
import type { Style } from '../draw/canvas';
import { OpsView } from '../draw/ops';
import { type Catalog } from './apps';
import { catalogFeed } from './appsSource';
import { clampScroll, drawerFrame, drawerRows, drawerState, ROWS, RH, TOP, type DrawerState } from './drawer';
import { HitRect, launch } from './hit';
import { drawerOpen } from './overlays';

const zone = layout.overlays.find((z) => z.id === 'O_drawer'); // an overlay, not a HUD zone
// drawer.lua closes itself after 20 updates (Update=1000) with no click, scroll or hover
const IDLE_MS = 20_000;

/** CARGO drawer, shown while drawerOpen is set (console CARGO, a side folder). Clicks and scroll as drawer.lua OnClick/OnScroll. */
export function DrawerModule({ style, catalog = catalogFeed.value }: { style: Style; catalog?: Catalog }) {
  const want = drawerOpen.value;
  const [st, setSt] = useState<DrawerState>(drawerState);
  const idle = useRef(0);
  const close = () => { drawerOpen.value = null; };
  const poke = () => { clearTimeout(idle.current); idle.current = window.setTimeout(close, IDLE_MS); };
  // each open starts on its folder (Focus) at the top, with the idle timer running
  useEffect(() => {
    if (!want) return;
    setSt((s) => ({ ...s, focus: want.focus, scroll: 0 }));
    poke();
    return () => clearTimeout(idle.current);
  }, [want]);
  if (!zone || !want) return null;
  const rows = drawerRows(catalog, st);
  const scroll = clampScroll(st.scroll, rows.length);
  const ops = drawerFrame(catalog, st, zone, style);
  const scrollBy = (d: number) => { poke(); setSt((s) => ({ ...s, scroll: clampScroll(s.scroll + d * 3, rows.length) })); };
  const click = (i: number) => {
    poke();
    const row = rows[i + scroll];
    if (!row) return;
    if (row.kind === 'all') setSt((s) => ({ ...s, focus: undefined, scroll: 0 }));
    else if (row.kind === 'cat' && row.jump) setSt((s) => ({ ...s, focus: row.cat.id, scroll: 0 }));
    else if (row.kind === 'cat') setSt((s) => ({ ...s, open: { ...s.open, [row.cat.id]: !s.open[row.cat.id] } }));
    else { launch(row.app); close(); }
  };
  return (
    <g transform={`matrix(${zone.matrix.join(' ')})`} data-module="drawer" onMouseMove={poke}>
      <OpsView ops={ops} name="drawer" />
      {/* the panel takes the wheel and swallows clicks between rows, as the skin's Bounds meter does */}
      <HitRect zone={zone} s={style.s} label="CARGO hold" on={{ wheel: scrollBy }} />
      <HitRect zone={zone} s={style.s} box={{ x: zone.w - 40, y: 8, w: 30, h: 30 }} label="Close" on={{ click: close, wheel: scrollBy }} />
      {rows.slice(scroll, scroll + ROWS).map((row, i) => {
        const y = TOP + i * RH;
        const b = row.kind === 'app' ? { x: 50, y, w: zone.w - 90, h: RH - 2 } : { x: 20, y, w: zone.w - 40, h: RH - 3 };
        const label = row.kind === 'app' ? row.app.name : row.kind === 'all' ? 'Back to all folders' : row.cat.name;
        return <HitRect zone={zone} s={style.s} box={b} label={label} on={{ click: () => click(i), wheel: scrollBy }} />;
      })}
    </g>
  );
}
