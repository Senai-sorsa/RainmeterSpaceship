import layout from './generated/layout.json';
import icons from './generated/icons.json';
import settings from './generated/settings.json';
import { chamferPath, iconPath, inflateQuad, transformBox, type Matrix, type Prim } from './lib/geometry';

const rgb = (s?: string) => (s ? `rgb(${s.split(',').slice(0, 3).join(',')})` : undefined);
const v = (settings as { variables: Record<string, string> }).variables;
const theme = {
  '--theme-accent': rgb(v.ColorAccent), '--theme-dim': rgb(v.ColorDim),
  '--theme-alert': rgb(v.ColorAlert), '--theme-text': rgb(v.ColorText),
} as Record<string, string | undefined>;

const { canvas, margins, safe_area: sa, taskbar } = layout;
const ICONS = ['rocket', 'starship', 'camera', 'book'] as const;
const iconSet = icons.icons as unknown as Record<string, Prim[]>;

export function Hud() {
  const pad = margins.module + margins.animationBleed;
  return (
    <svg id="hud" viewBox={`0 0 ${canvas.w} ${canvas.h}`} style={{ width: '100vw', height: '100vh', ...theme }}
      preserveAspectRatio="xMidYMid meet">
      <rect width={canvas.w} height={canvas.h} fill="var(--bg)" />
      <rect x={sa.inset} y={sa.inset} width={canvas.w - 2 * sa.inset} height={canvas.h - 2 * sa.inset - taskbar.height}
        rx={sa.corner_radius} fill="none" stroke="var(--line)" stroke-opacity=".25" stroke-dasharray="8 12" />
      <rect x="0" y={canvas.h - taskbar.height} width={canvas.w} height={taskbar.height} fill="var(--alert)" fill-opacity=".15" />
      {layout.zones.map((z) => {
        const q = transformBox(z.matrix as Matrix, z.x, z.y, z.w, z.h);
        const [lx, ly] = q[0];
        return (
          <g class="zone" data-id={z.id}>
            <path d={chamferPath(inflateQuad(q, pad), 12)} fill="none" stroke="var(--line)" stroke-opacity=".12" />
            <path d={chamferPath(q, 8)} fill="none" stroke="var(--line)" stroke-width="1.5"
              style="filter:drop-shadow(0 0 4px var(--glow))" />
            <text class="label" x={lx + 10} y={ly + 16} font-size="11" letter-spacing="3.3">{z.id}</text>
          </g>
        );
      })}
      {ICONS.map((name, i) => (
        <g transform={`translate(${200 + i * 150} 700) scale(1.2)`} fill="none" stroke="var(--line)" stroke-width="1.5" data-icon={name}>
          <path d={iconPath(iconSet[name] ?? [])} />
        </g>
      ))}
    </svg>
  );
}
