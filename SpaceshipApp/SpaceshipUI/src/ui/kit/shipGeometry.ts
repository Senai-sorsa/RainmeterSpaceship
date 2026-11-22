/* Symmetric top-view jet, redrawn from the HUD's rasaero_jet line icon (Scripts/icons.lua) on the same 0-100 grid.
   Each part is one half (right side, x > 50) of polylines; `mirror` adds the left side. Nose points up. */
export type PartId = 'fuselage' | 'canopy' | 'wings' | 'tails' | 'engines' | 'wingtips' | 'exhaust';
export type Poly = [number, number][];
type Part = { id: PartId; lines: Poly[]; mirror: boolean };

const PARTS: Part[] = [
  { id: 'fuselage', mirror: true, lines: [[[50, 5], [52.5, 12], [54, 24], [54.5, 46], [55, 66], [54, 84], [51.5, 90], [50, 91]]] },
  { id: 'canopy', mirror: true, lines: [[[50, 15], [52, 20], [52.5, 29], [50, 34]], [[50, 38], [52, 42]]] },
  { id: 'wings', mirror: true, lines: [[[54.5, 40], [84, 66], [85, 70], [55, 68]], [[55, 55], [76, 66]]] },
  { id: 'tails', mirror: true, lines: [[[55, 78], [68, 90], [67, 94], [54, 90]]] },
  { id: 'engines', mirror: true, lines: [[[57, 70], [62, 70], [62, 90], [57, 90], [57, 70]], [[59.5, 73], [59.5, 87]]] },
  { id: 'wingtips', mirror: true, lines: [[[85, 70], [89, 61], [90, 74], [85, 72]]] },
  { id: 'exhaust', mirror: true, lines: [[[58, 92], [58, 97]], [[60.5, 92], [60.5, 97]]] },
];

const flip = (l: Poly): Poly => l.map(([x, y]) => [100 - x, y]);
const d = (l: Poly) => 'M' + l.map(([x, y]) => `${x} ${y}`).join('L');

/** SVG path data per part, both halves joined. */
export const SHIP: { id: PartId; d: string }[] = PARTS.map((p) => ({
  id: p.id,
  d: p.lines.flatMap((l) => (p.mirror ? [l, flip(l)] : [l])).map(d).join(''),
}));
export const SHIP_PARTS = SHIP.map((p) => p.id);
