import { useEffect, useRef, useState } from 'preact/hooks';
import layout from '../generated/layout.json';
import type { Style } from '../draw/canvas';
import { OpsView } from '../draw/ops';
import { scheduler, skinMs } from '../host/scheduler';
import { transformBox, type Matrix } from '../lib/geometry';
import { host } from '../settings/instance';
import { feedFrom, jarvisFrame, jarvisLogFrame, logScrollMax, orbEcho, orbStep, stateColor, type Feed, type JarvisColors, type OrbMotion } from './jarvis';

const FRAME_MS = skinMs(33); // the Lua orb's Update=33, ~21 fps in Rainmeter
const sphere = layout.zones.find((z) => z.id === 'C_sphere');
const offline = feedFrom(undefined, 0);

/**
 * The Jarvis core, behind ?module=jarvis. Centred on the old globe's zone (C_sphere). The Hud gives it the host's
 * jarvis.update feed; with none it shows OFFLINE. A click starts the service, wakes him or cancels the turn (jarvis.lua OnClick).
 */
export function JarvisModule({ style, feed = offline, label = '', orb = {}, enabled = true, onMenu }: {
  style: Style; feed?: Feed; label?: string; orb?: OrbOpts; enabled?: boolean; onMenu?: () => void;
}) {
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
  // the skin draws the name and status at the bottom left of the Sphere window (zone C_sphere), beside the base
  const ops = jarvisFrame(f, feed, style, { x: 0, y: 0, w: layout.canvas.w, h: layout.canvas.h }, cx, cy, label, q[3] as [number, number], orb.cols);
  return (
    <>
      {ORB.length > 0 && <Orb f={f} feed={feed} style={style} cx={cx} cy={cy} opts={orb} />}
      <OpsView ops={ops} name="jarvis" />
      {/* click wakes or cancels; right-click on the hologram toggles the log, as in the skin */}
      <circle cx={cx * style.s} cy={cy * style.s} r={165 * style.s} fill="transparent" data-hit style={{ cursor: 'pointer' }}
        onClick={() => orbClick(enabled, feed.state)} onContextMenu={(e) => { e.preventDefault(); onMenu?.(); }} />
    </>
  );
}

// The plasma orb: the skin's Images\Jarvis\Idle frames (jarvis.lua sprite S1_1) and its voice echo (S1_2, the Active frames,
// else Idle half a loop ahead). One <image> each, swapped per tick, so only the frames on screen are decoded.
type OrbOpts = { bright?: number; tint?: number; size?: number; cols?: JarvisColors };
const frames = (g: Record<string, string>) => Object.entries(g).sort(([a], [b]) => a.localeCompare(b)).map(([, u]) => u);
const ORB = frames(import.meta.glob('../../../../Skins/Spaceship/@Resources/Images/Jarvis/Idle/*.png', { eager: true, query: '?url', import: 'default' }));
const ACTIVE = frames(import.meta.glob('../../../../Skins/Spaceship/@Resources/Images/Jarvis/Active/*.png', { eager: true, query: '?url', import: 'default' }));
const tintMatrix = (k: number, col: number[], tint: number, a: number) =>
  `${k} 0 0 0 ${(col[0] / 255) * tint} 0 ${k} 0 0 ${(col[1] / 255) * tint} 0 0 ${k} 0 ${(col[2] / 255) * tint} 0 0 0 ${a / 255} 0`;

const clampOr = (v: number | undefined, lo: number, hi: number, dflt: number) => (Number.isFinite(v) ? Math.min(hi, Math.max(lo, v!)) : dflt);

function Orb({ f, feed, style, cx, cy, opts }: { f: number; feed: Feed; style: Style; cx: number; cy: number; opts: OrbOpts }) {
  const st = feed.state;
  const mo = useRef<{ f: number; m: OrbMotion }>({ f, m: { lvl: 0, act: 0, fIdle: 0, fAct: 0 } });
  if (mo.current.f !== f) mo.current = { f, m: orbStep(mo.current.m, st, feed.level, Math.max(0, f - mo.current.f)) }; // once per tick
  const m = mo.current.m, lvl = m.lvl;
  const col = stateColor(st, style, opts.cols);
  // jarvis.lua: JarvisOrbBright, JarvisTint and JarvisOrbSize clamped as there; brightness k, additive state tint and alpha per state
  const bright = clampOr(opts.bright, 0.4, 1.6, 1), tintS = clampOr(opts.tint, 0, 0.8, 0.22), size = clampOr(opts.size, 0.8, 1.15, 1);
  const [k0, tint, a] = st === 'listening' ? [0.8, tintS * 0.5, 245] : st === 'speaking' ? [1 + 0.2 * lvl, tintS * 0.8, 245] : st === 'offline' ? [0.7, tintS * 0.3, 190] : [0.9, tintS, 245];
  const s = style.s, d = 330 * size * (1 + 0.1 * lvl) * s;
  const echo = orbEcho(m, col, style.white, size, bright);
  const ef = ACTIVE.length ? ACTIVE[Math.floor(m.fAct) % ACTIVE.length] : ORB[(Math.floor(m.fIdle) + (ORB.length >> 1)) % ORB.length];
  return (
    <>
      <filter id="orb-tint" color-interpolation-filters="sRGB">
        <feColorMatrix type="matrix" values={tintMatrix(k0 * bright, col, tint, a)} />
      </filter>
      <image href={ORB[Math.floor(m.fIdle) % ORB.length]} x={cx * s - d / 2} y={cy * s - d / 2} width={d} height={d} filter="url(#orb-tint)" data-module="jarvis-orb" />
      {echo && <>
        <filter id="orb-echo" color-interpolation-filters="sRGB">
          <feColorMatrix type="matrix" values={tintMatrix(echo.k, echo.col, echo.tint, echo.alpha)} />
        </filter>
        <image href={ef} x={cx * s - (echo.d * s) / 2} y={cy * s - (echo.d * s) / 2} width={echo.d * s} height={echo.d * s} filter="url(#orb-echo)" data-module="jarvis-echo" />
      </>}
    </>
  );
}

let lastCmd = 0;
/** jarvis.lua OnClick: once a second at most; offline starts the service, idle wakes him at the HUD's tier, any other state cancels the turn. */
export function orbClick(enabled: boolean, state: string, now = Date.now()): 'start' | 'wake' | 'cancel' | null {
  if (!enabled || now - lastCmd < 1000) return null;
  lastCmd = now;
  const cmd = state === 'offline' ? 'start' : state === 'idle' ? 'wake' : 'cancel';
  host.send({ type: 'jarvis.cmd', cmd });
  return cmd;
}

const LOG_IDLE_MS = 180000; // jarvislog.lua closes after 3 minutes with nothing new and no hover or scroll

/**
 * The conversation log pop-up (jarvislog.lua): the host's jarvis.log text, newest at the bottom. The wheel scrolls by 3
 * lines, right-click opens the log file in Notepad, X closes it, TYPE opens a text box that asks him (works muted).
 * Placed at the top left of the canvas, as Overlay\Jarvis.
 */
export function JarvisLogModule({ style, log = '', live = '', muted = false, assistant = 'Clover', onClose }: {
  style: Style; log?: string; live?: string; muted?: boolean; assistant?: string; onClose?: () => void;
}) {
  const W = 1200, H = 616, s = style.s;
  const [scroll, setScroll] = useState(0);
  const [poke, setPoke] = useState(0);
  const [typing, setTyping] = useState(false);
  useEffect(() => setScroll(0), [log, live]); // new text jumps back to the newest line
  useEffect(() => {
    if (!onClose) return;
    const t = setTimeout(onClose, LOG_IDLE_MS);
    return () => clearTimeout(t);
  }, [log, live, poke, onClose]);
  const max = logScrollMax(log, live, W, style);
  const ops = jarvisLogFrame(log, live, muted, assistant, style, { x: 0, y: 0, w: W, h: H }, scroll);
  return (
    <g transform="translate(40 40)" data-module="jarvislog" onPointerEnter={() => setPoke((n) => n + 1)}
      onWheel={(e) => { setScroll((v) => Math.min(Math.max(v - (e.deltaY > 0 ? 1 : -1) * 3, 0), max)); setPoke((n) => n + 1); }}
      onContextMenu={(e) => { e.preventDefault(); host.send({ type: 'target.open', what: 'jarvislog' }); }}>
      <rect width={W * s} height={H * s} fill="transparent" data-hit />
      <OpsView ops={ops} name="jarvislog" />
      {/* the X jarvisLogFrame draws at (w-36..w-20, 16..32) */}
      {onClose && <rect x={(W - 44) * s} y={8 * s} width={32 * s} height={32 * s} fill="transparent" data-hit aria-label="Close log"
        style={{ cursor: 'pointer' }} onClick={onClose} />}
      {/* TYPE at (w-330, 8, 90x32) opens Jarvis.ini's mAsk InputText (150, 556, 860x36) */}
      <rect x={(W - 330) * s} y={8 * s} width={90 * s} height={32 * s} fill="transparent" data-hit aria-label={`Type to ${assistant}`}
        style={{ cursor: 'pointer' }} onClick={() => setTyping(true)} />
      {typing && <foreignObject x={150 * s} y={556 * s} width={860 * s} height={36 * s}>
        <input data-hit="keyboard" aria-label={`Ask ${assistant}`} maxLength={500} autoFocus ref={(el) => el?.focus()}
          style={{ width: '100%', height: '100%', boxSizing: 'border-box', border: 0, outline: 0, padding: `0 ${6 * s}px`,
            background: 'rgb(3,9,16)', color: 'rgb(0,210,255)', font: `${14 * (96 / 72) * s}px Rajdhani, sans-serif` }}
          onKeyDown={(e) => {
            const el = e.currentTarget;
            if (e.key === 'Enter') { if (el.value.trim()) host.send({ type: 'jarvis.cmd', cmd: 'ask', text: el.value.slice(0, 500) }); setTyping(false); }
            else if (e.key === 'Escape') setTyping(false);
          }} onBlur={() => setTyping(false)} />
      </foreignObject>}
    </g>
  );
}
