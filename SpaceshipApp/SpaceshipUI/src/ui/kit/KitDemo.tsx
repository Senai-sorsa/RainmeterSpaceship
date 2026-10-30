import { useState } from 'preact/hooks';
import { HudPanel } from './HudPanel';
import { Reticle } from './Reticle';
import { Ship } from './Ship';
import { StatusPill } from './StatusPill';
import { SHIP_PARTS, type PartId } from './shipGeometry';

/** Dev route ?panel=kit: every kit piece, with the ship parts switchable. */
export function KitDemo() {
  const [lit, setLit] = useState<PartId[]>(['fuselage', 'canopy']);
  const flip = (p: PartId) => setLit((l) => (l.includes(p) ? l.filter((x) => x !== p) : [...l, p]));
  return (
    <div class="kit-demo">
      <HudPanel index="01" title="Ship" pill={{ state: 'linked' }}>
        <Ship lit={lit} size={240} />
        <div style="display:flex;flex-wrap:wrap;gap:6px;margin-top:8px">
          {SHIP_PARTS.map((p) => <button type="button" class="ctl-action" style="width:auto;padding:0 8px" aria-pressed={lit.includes(p)} onClick={() => flip(p)}>{p}</button>)}
        </div>
      </HudPanel>
      <HudPanel index="02" title="Reticle"><Reticle lit={2} /></HudPanel>
      <HudPanel index="03" title="Pills">
        <div style="display:flex;gap:8px;flex-wrap:wrap"><StatusPill state="offline" /><StatusPill state="linked" /><StatusPill state="warn" /><StatusPill state="error" /></div>
      </HudPanel>
    </div>
  );
}
