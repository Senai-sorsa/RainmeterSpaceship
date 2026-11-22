/** Decorative segmented ring with cardinal ticks. `lit` lights that many of the 4 quarter arcs. */
const arc = (r: number, a0: number, a1: number) => {
  const p = (a: number) => `${(60 + r * Math.cos(a)).toFixed(2)} ${(60 + r * Math.sin(a)).toFixed(2)}`;
  return `M${p(a0)}A${r} ${r} 0 0 1 ${p(a1)}`;
};
const Q = Math.PI / 2, GAP = 0.18;

export function Reticle({ lit = 0, size = 220 }: { lit?: number; size?: number }) {
  return (
    <svg class="reticle" viewBox="0 0 120 120" width={size} height={size} aria-hidden="true" fill="none" stroke-linecap="round">
      {[0, 1, 2, 3].map((q) => <path key={q} d={arc(54, q * Q - Q / 2 + GAP, q * Q + Q / 2 - GAP)} class={q < lit ? 'ret-on' : 'ret-off'} />)}
      <circle cx="60" cy="60" r="44" class="ret-thin" />
      {[0, 1, 2, 3].map((q) => <path key={`t${q}`} class="ret-thin" d={`M${60 + 58 * Math.cos(q * Q)} ${60 + 58 * Math.sin(q * Q)}L${60 + 64 * Math.cos(q * Q)} ${60 + 64 * Math.sin(q * Q)}`} />)}
    </svg>
  );
}
