export type Matrix = [number, number, number, number, number, number]; // [a,b,c,d,tx,ty]
export type Pt = [number, number];
export type Prim = (string | number)[];

export const applyMatrix = (m: Matrix, [x, y]: Pt): Pt =>
  [m[0] * x + m[2] * y + m[4], m[1] * x + m[3] * y + m[5]];

export const boxCorners = (x: number, y: number, w: number, h: number): Pt[] =>
  [[x, y], [x + w, y], [x + w, y + h], [x, y + h]];

export const transformBox = (m: Matrix, x: number, y: number, w: number, h: number): Pt[] =>
  boxCorners(x, y, w, h).map((p) => applyMatrix(m, p));

export function quadArea(q: Pt[]): number {
  let s = 0;
  q.forEach((p, i) => { const n = q[(i + 1) % q.length]; s += p[0] * n[1] - n[0] * p[1]; });
  return Math.abs(s) / 2;
}

/** Push each corner outward from the centroid so every edge moves out by ~margin. */
export function inflateQuad(q: Pt[], margin: number): Pt[] {
  const cx = q.reduce((a, p) => a + p[0], 0) / q.length;
  const cy = q.reduce((a, p) => a + p[1], 0) / q.length;
  return q.map(([x, y]) => {
    const dx = x - cx, dy = y - cy, d = Math.hypot(dx, dy) || 1;
    return [x + (dx / d) * margin, y + (dy / d) * margin] as Pt;
  });
}

/** Chamfer each corner by c (clamped to half the shorter adjacent edge) -> SVG path. */
export function chamferPath(q: Pt[], c: number): string {
  const n = q.length, pts: Pt[] = [];
  for (let i = 0; i < n; i++) {
    const p = q[i], a = q[(i + n - 1) % n], b = q[(i + 1) % n];
    const la = Math.hypot(a[0] - p[0], a[1] - p[1]) || 1, lb = Math.hypot(b[0] - p[0], b[1] - p[1]) || 1;
    const k = Math.min(c, la / 2, lb / 2);
    pts.push([p[0] + ((a[0] - p[0]) / la) * k, p[1] + ((a[1] - p[1]) / la) * k]);
    pts.push([p[0] + ((b[0] - p[0]) / lb) * k, p[1] + ((b[1] - p[1]) / lb) * k]);
  }
  return 'M' + pts.map((p) => p[0].toFixed(2) + ' ' + p[1].toFixed(2)).join('L') + 'Z';
}

const f = (n: number) => +n.toFixed(2);
/** Icon primitive (icons.lua ops l,p,c,a,e) -> SVG path data; throws on unknown op. */
export function primToPath(p: Prim): string {
  const [op, ...v] = p; const n = v as number[];
  const poly = (z: boolean) => 'M' + n.reduce<string[]>((o, _, i) => i % 2 ? o : [...o, f(n[i]) + ' ' + f(n[i + 1])], []).join('L') + (z ? 'Z' : '');
  switch (op) {
    case 'l': return poly(false);
    case 'p': return poly(true);
    case 'c': return ellipse(n[0], n[1], n[2], n[2]);
    case 'e': return ellipse(n[0], n[1], n[2], n[3]);
    case 'a': {
      const [cx, cy, rx, a0, a1, ry = rx] = n;
      const pt = (a: number) => `${f(cx + rx * Math.cos((a * Math.PI) / 180))} ${f(cy + ry * Math.sin((a * Math.PI) / 180))}`;
      const sweep = a1 - a0;
      return `M${pt(a0)}A${f(rx)} ${f(ry)} 0 ${Math.abs(sweep) > 180 ? 1 : 0} ${sweep >= 0 ? 1 : 0} ${pt(a1)}`;
    }
    default: throw new Error('unknown icon op ' + String(op));
  }
}
function ellipse(cx: number, cy: number, rx: number, ry: number) {
  return `M${f(cx - rx)} ${f(cy)}A${f(rx)} ${f(ry)} 0 1 0 ${f(cx + rx)} ${f(cy)}A${f(rx)} ${f(ry)} 0 1 0 ${f(cx - rx)} ${f(cy)}Z`;
}
export const iconPath = (prims: Prim[]) => prims.map(primToPath).join('');
