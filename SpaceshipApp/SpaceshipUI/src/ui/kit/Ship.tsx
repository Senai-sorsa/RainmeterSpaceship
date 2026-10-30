import { SHIP, type PartId } from './shipGeometry';

/** Decorative jet; parts in `lit` glow in the accent colour, the rest stay dim. */
export function Ship({ lit = [], size = 160 }: { lit?: PartId[]; size?: number }) {
  return (
    <svg class="ship" viewBox="0 0 100 100" width={size} height={size} aria-hidden="true" fill="none" stroke-linecap="round" stroke-linejoin="round">
      {SHIP.map((p) => {
        const on = lit.includes(p.id);
        return (
          <g key={p.id} class={on ? 'ship-lit' : 'ship-dim'}>
            {on && <path d={p.d} class="ship-halo" />}
            <path d={p.d} class="ship-line" />
          </g>
        );
      })}
    </svg>
  );
}
