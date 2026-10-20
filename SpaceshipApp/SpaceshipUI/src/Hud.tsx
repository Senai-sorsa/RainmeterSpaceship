import layout from './generated/layout.json';
import icons from './generated/icons.json';
import settings from './generated/settings.json';
import { chamferPath, iconPath, inflateQuad, transformBox, type Matrix, type Prim } from './lib/geometry';
import { num } from './lib/theme';

const v = (settings as { variables: Record<string, string> }).variables;
// Skin glow model (lib.lua Canvas:neon, tier 0): outer halo w*GlowWidth*2.1 at GlowAlpha*0.38, glow w*GlowWidth at GlowAlpha, core w.
const glowA = num(v, 'GlowAlpha', 46) / 255, glowW = num(v, 'GlowWidth', 3.2), LW = 1.6;

const { canvas, margins, safe_area: sa, taskbar } = layout;
const ICONS = ['rocket', 'starship', 'camera', 'book'] as const;
const iconSet = icons.icons as unknown as Record<string, Prim[]>;
// ?debug=1 only: the skin draws no zone outlines (only edit mode: Canvas:flush, fill 255,200,0,18 / stroke 255,200,0,200 / width 2).
const debug = new URLSearchParams(location.search).get('debug') === '1';

function Neon({ d }: { d: string }) {
  const p = { d, fill: 'none', 'stroke-linecap': 'round', 'stroke-linejoin': 'round' } as const;
  return (
    <>
      <path {...p} stroke="var(--accent)" stroke-opacity={glowA * 0.38} stroke-width={LW * glowW * 2.1} />
      <path {...p} stroke="var(--accent)" stroke-opacity={glowA} stroke-width={LW * glowW} />
      <path {...p} stroke="var(--core)" stroke-width={LW} />
    </>
  );
}

export function Hud() {
  const pad = margins.module + margins.animationBleed;
  return (
    <svg id="hud" viewBox={`0 0 ${canvas.w} ${canvas.h}`} style={{ width: '100vw', height: '100vh' }}
      preserveAspectRatio="xMidYMid meet">
      <rect width={canvas.w} height={canvas.h} fill="var(--bg)" />
      {debug && (
        <g id="debug-overlay" data-debug="1">
          <rect x={sa.inset} y={sa.inset} width={canvas.w - 2 * sa.inset} height={canvas.h - 2 * sa.inset - taskbar.height}
            rx={sa.corner_radius} fill="none" stroke="rgb(255,200,0)" stroke-opacity=".4" stroke-dasharray="8 12" />
          <rect x="0" y={canvas.h - taskbar.height} width={canvas.w} height={taskbar.height} fill="rgb(255,200,0)" fill-opacity=".07" />
        </g>
      )}
      {layout.zones.map((z) => {
        const q = transformBox(z.matrix as Matrix, z.x, z.y, z.w, z.h);
        const [lx, ly] = q[0];
        return (
          <g class="zone" data-id={z.id}>
            {debug && (
              <>
                <path d={chamferPath(inflateQuad(q, pad), 12)} fill="none" stroke="rgb(255,200,0)" stroke-opacity=".3" />
                <path d={chamferPath(q, 8)} fill="rgb(255,200,0)" fill-opacity={18 / 255} stroke="rgb(255,200,0)" stroke-opacity={200 / 255} stroke-width="2" />
                <text class="label" x={lx + 10} y={ly + 16} font-size="11" letter-spacing="3.3" style="fill:rgb(255,200,0)">{z.id}</text>
              </>
            )}
          </g>
        );
      })}
      {ICONS.map((name, i) => (
        <g transform={`translate(${200 + i * 150} 700) scale(1.2)`} data-icon={name}>
          <Neon d={iconPath(iconSet[name] ?? [])} />
        </g>
      ))}
    </svg>
  );
}
