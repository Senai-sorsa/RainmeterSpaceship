import { useMemo, useState } from 'preact/hooks';
import type { Zone } from '../draw/canvas';
import { host } from '../settings/instance';
import type { App, Cat, Catalog } from './apps';
import { SKIN_STATE } from './appsSource';
import { selIndex, skinPick } from './category';
import { drawerOpen } from './overlays';

// The mouse side of the side columns and the reticle (H.hit + OnClick/OnRightClick/OnScroll in the skin's scripts).

type Box = { x: number; y: number; w: number; h: number };
type On = { click?: (x: number) => void; menu?: (x: number) => void; wheel?: (d: number) => void };

/** Mouse x in zone units, from the left of the zone, through the skewed zone matrix. */
const zoneX = (e: MouseEvent, zone: Box, s: number) => {
  const m = (e.currentTarget as SVGGraphicsElement).getScreenCTM?.();
  return m ? new DOMPoint(e.clientX, e.clientY).matrixTransform(m.inverse()).x / s - zone.x : 0;
};

/** A transparent click target over a zone, or over box (zone units) inside it; drawn in the zone's matrix group. */
export function HitRect({ zone, s, box = { x: 0, y: 0, w: zone.w, h: zone.h }, on, label }: { zone: Zone; s: number; box?: Box; on: On; label: string }) {
  return (
    <rect x={(zone.x + box.x) * s} y={(zone.y + box.y) * s} width={box.w * s} height={box.h * s} fill="transparent" data-hit aria-label={label}
      style={{ cursor: 'pointer' }}
      onClick={(e) => on.click?.(zoneX(e, zone, s))}
      onContextMenu={(e) => { e.preventDefault(); on.menu?.(zoneX(e, zone, s)); }}
      onWheel={(e) => on.wheel?.(e.deltaY > 0 ? 1 : -1)} />
  );
}

/** apps.lua A.launch: the host looks the id up in its own Apps.ini, so the page never names what runs. */
export const launch = (app: App | undefined) => { if (app && !app.missing) host.send({ type: 'app.launch', id: app.id }); };

/** slot.lua OnClick (row style): a folder with apps opens the CARGO drawer on it, an empty one does nothing, an app launches. */
export const openSlot = (e: { kind: 'cat'; cat: Cat } | { kind: 'app'; app: App } | undefined, pick: App | undefined) => {
  if (e?.kind === 'cat') { if (e.cat.apps.length) drawerOpen.value = { focus: e.cat.id }; }
  else launch(pick);
};

const wrap = (i: number, n: number) => ((i % n) + n) % n;

/**
 * A column's page and pick (category.lua): it opens where the skin last was; then the dots and scroll change the page and
 * the tabs, schematic and slot scroll change a category's pick (Sel_<cat>, shared by the tabs and the slots).
 * shortcut: picks last for this run only (not written back to State.inc); persist them if the user misses that.
 */
export function usePanel(catalog: Catalog, panel: 1 | 2) {
  const pick = useMemo(() => skinPick(catalog, panel, SKIN_STATE), [catalog, panel]);
  const [page, setPage] = useState<number | null>(null);
  const [sels, setSels] = useState<Record<string, string>>({});
  const state = useMemo(() => ({ ...SKIN_STATE, ...sels }), [sels]);
  const n = catalog.catOrder.length;
  const ci = page !== null && page < n ? page : pick.ci;
  const cat: Cat | undefined = catalog.cats[catalog.catOrder[ci]];
  const ai = selIndex(cat, state);
  return {
    ci, cat, ai, app: cat?.apps[ai], state,
    choose: (c: Cat | undefined, i: number) => { if (c?.apps.length) setSels((s) => ({ ...s, [`Sel_${c.id}`]: String(wrap(i, c.apps.length) + 1) })); },
    turn: (i: number) => { if (n) setPage(wrap(i, n)); },
  };
}
