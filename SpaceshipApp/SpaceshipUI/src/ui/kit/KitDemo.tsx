import { useState } from 'preact/hooks';
import { HudPanel } from './HudPanel';
import { Reticle } from './Reticle';
import { Ship } from './Ship';
import { StatusPill } from './StatusPill';
import { SHIP_PARTS, type PartId } from './shipGeometry';
import { Canvas, heat } from '../../draw/canvas';
import { HudDefs, OpsView } from '../../draw/ops';
import { styleFrom } from '../../modules/style';

/** The realism kit (K1-K4) on one canvas per tier: lit displays from each edge, gradient fills and hot cores. */
function RealismKit({ tier }: { tier: number }) {
  const st = { ...styleFrom({}), tier };
  const c = new Canvas({ x: 0, y: 0, w: 240, h: 150 }, st);
  c.screen(6, 6, 108, 60, { from: 'bottom', cut: 8, lit: 0.8 });
  c.text(60, 36, '72%', { size: 16, align: 'CenterCenter', color: heat(st, st.accent, 0.8), font: st.fontNum });
  c.screen(126, 6, 108, 60, { from: 'left', lit: 0.4, col: st.warn });
  c.text(180, 36, 'WARN', { size: 10, align: 'CenterCenter', color: st.warn });
  c.gradRect(6, 80, 228, 10, { kind: 'linear', x1: 6, y1: 0, x2: 234, y2: 0, stops: [[0, [0, 210, 255, 30]], [0.7, [0, 210, 255, 200]], [1, [255, 255, 255, 255]]] }, 2);
  c.gradPoly([[60, 100], [100, 144], [20, 144]], { kind: 'radial', cx: 60, cy: 130, r: 40, stops: [[0, [255, 255, 255, 220]], [0.4, [0, 210, 255, 160]], [1, [0, 210, 255, 0]]] });
  c.line(126, 120, 234, 120, st.accent, 2);
  return (
    <svg viewBox="0 0 240 150" width="100%" data-tier={tier} style="background:#02080c">
      <HudDefs />
      <OpsView ops={c.flush()} name={`kit${tier}`} />
    </svg>
  );
}

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
      {[0, 1, 2].map((t) => <HudPanel index={`0${4 + t}`} title={`Realism kit ${['FULL', 'LITE', 'LOW'][t]}`}><RealismKit tier={t} /></HudPanel>)}
    </div>
  );
}
