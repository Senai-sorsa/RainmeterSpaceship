import { useState } from 'preact/hooks';
import layout from '../generated/layout.json';
import type { Style } from '../draw/canvas';
import { OpsView } from '../draw/ops';
import { type Catalog } from './apps';
import { catalogFeed } from './appsSource';
import { clampScroll, drawerFrame, drawerRows, drawerState, type DrawerState } from './drawer';

const zone = layout.zones.find((z) => z.id === 'O_drawer');

/** CARGO drawer, behind ?module=drawer. Scroll and the folder accordion are local state; clicks that launch are not wired. */
export function DrawerModule({ style, catalog = catalogFeed.value }: { style: Style; catalog?: Catalog }) {
  const [st, setSt] = useState<DrawerState>(drawerState);
  if (!zone) return null;
  const ops = drawerFrame(catalog, st, { x: 0, y: 0, w: zone.w, h: zone.h }, style);
  const scrollBy = (d: number) => setSt((s) => ({ ...s, scroll: clampScroll(s.scroll + d * 3, drawerRows(catalog, s).length) }));
  return (
    <g transform={`matrix(${zone.matrix.join(' ')})`} data-module="drawer" data-hit onWheel={(e: WheelEvent) => scrollBy(e.deltaY > 0 ? 1 : -1)}>
      <OpsView ops={ops} name="drawer" />
    </g>
  );
}
