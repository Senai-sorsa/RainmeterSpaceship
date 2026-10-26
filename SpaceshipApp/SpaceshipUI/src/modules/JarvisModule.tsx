import { useEffect, useState } from 'preact/hooks';
import layout from '../generated/layout.json';
import { mix, type Style } from '../draw/canvas';
import { OpsView } from '../draw/ops';
import { scheduler } from '../host/scheduler';
import { transformBox, type Matrix } from '../lib/geometry';
import { feedFrom, jarvisFrame, jarvisLogFrame, type Feed } from './jarvis';

const FRAME_MS = 33; // the Lua orb's 30 fps
const sphere = layout.zones.find((z) => z.id === 'C_sphere');
const offline = feedFrom(undefined, 0);

/**
 * The Jarvis core, behind ?module=jarvis. Centred on the old globe's zone (C_sphere). The Hud gives it the host's
 * jarvis.update feed; with none it shows OFFLINE. The orb sprite, the voice echo and the clicks are not ported.
 */
export function JarvisModule({ style, feed = offline, onMenu }: { style: Style; feed?: Feed; onMenu?: () => void }) {
  const [f, setF] = useState(0);
  const asleep = feed.state === 'offline';
  useEffect(() => {
    // offline the orb turns at 0.3x, so 10 fps in 3-frame steps looks the same and draws a third as often
    const step = asleep ? 3 : 1;
    return scheduler.every(FRAME_MS * step, () => setF((n) => n + step));
  }, [asleep]);
  if (!sphere) return null;
  const q = transformBox(sphere.matrix as Matrix, sphere.x, sphere.y, sphere.w, sphere.h);
  const cx = (q[0][0] + q[2][0]) / 2, cy = (q[0][1] + q[2][1]) / 2;
  const ops = jarvisFrame(f, feed, style, { x: 0, y: 0, w: layout.canvas.w, h: layout.canvas.h }, cx, cy);
  return (
    <>
      {ORB.length > 0 && <Orb f={f} feed={feed} style={style} cx={cx} cy={cy} />}
      <OpsView ops={ops} name="jarvis" />
      {/* right-click on the hologram toggles the log, as in the skin */}
      {onMenu && <circle cx={cx * style.s} cy={cy * style.s} r={165 * style.s} fill="transparent" data-hit
        onContextMenu={(e) => { e.preventDefault(); onMenu(); }} />}
    </>
  );
}

// The plasma orb: the skin's Images\Jarvis\Idle frames (jarvis.lua sprite S1_1), one <image> swapped per tick, so only the
// frame on screen is decoded. shortcut: no voice echo (S1_2) and no JarvisOrb*/JarvisTint settings, upgrade: when those are wired.
const ORB = Object.entries(import.meta.glob('../../../../Skins/Spaceship/@Resources/Images/Jarvis/Idle/*.png', { eager: true, query: '?url', import: 'default' }) as Record<string, string>)
  .sort(([a], [b]) => a.localeCompare(b)).map(([, u]) => u);
const ORB_SPEED: Record<string, number> = { idle: 1, listening: 0.6, thinking: 1.5, offline: 0.35 };

function Orb({ f, feed, style, cx, cy }: { f: number; feed: Feed; style: Style; cx: number; cy: number }) {
  const st = feed.state, lvl = Math.min(1, Math.max(0, feed.level));
  const col = st === 'listening' ? mix(style.accent, [0, 70, 210, 255], 0.55) : st === 'offline' ? mix(style.dim, style.accent, 0.45) : style.accent;
  // jarvis.lua: brightness k, additive state tint and alpha per state
  const [k, tint, a] = st === 'listening' ? [0.8, 0.11, 245] : st === 'speaking' ? [1 + 0.2 * lvl, 0.176, 245] : st === 'offline' ? [0.7, 0.066, 190] : [0.9, 0.22, 245];
  const [tr, tg, tb] = col.map((c) => (c / 255) * tint);
  const speed = st === 'speaking' ? 1 + 1.6 * lvl : ORB_SPEED[st] ?? 1;
  const s = style.s, d = 330 * (1 + 0.1 * lvl) * s;
  return (
    <>
      <filter id="orb-tint" color-interpolation-filters="sRGB">
        <feColorMatrix type="matrix" values={`${k} 0 0 0 ${tr} 0 ${k} 0 0 ${tg} 0 0 ${k} 0 ${tb} 0 0 0 ${a / 255} 0`} />
      </filter>
      <image href={ORB[Math.floor(f * speed) % ORB.length]} x={cx * s - d / 2} y={cy * s - d / 2} width={d} height={d} filter="url(#orb-tint)" data-module="jarvis-orb" />
    </>
  );
}

/**
 * The conversation log, behind ?module=jarvislog. It reads the log and reply text it is given (the Data files are not
 * wired yet, so it shows the empty state). Placed at the top left of the canvas until a zone is set for it.
 */
export function JarvisLogModule({ style, log = '', live = '', muted = false, assistant = 'Clover', onClose }: {
  style: Style; log?: string; live?: string; muted?: boolean; assistant?: string; onClose?: () => void;
}) {
  const W = 1200, s = style.s;
  const ops = jarvisLogFrame(log, live, muted, assistant, style, { x: 0, y: 0, w: W, h: 616 });
  return (
    <g transform="translate(40 40)" data-module="jarvislog">
      <OpsView ops={ops} name="jarvislog" />
      {/* the X jarvisLogFrame draws at (w-36..w-20, 16..32) */}
      {onClose && <rect x={(W - 44) * s} y={8 * s} width={32 * s} height={32 * s} fill="transparent" data-hit aria-label="Close log"
        style={{ cursor: 'pointer' }} onClick={onClose} />}
    </g>
  );
}
