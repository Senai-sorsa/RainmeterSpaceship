import layout from './generated/layout.json';
import icons from './generated/icons.json';
import settings from './generated/settings.json';
import { chamferPath, iconPath, inflateQuad, transformBox, type Matrix, type Prim } from './lib/geometry';
import { num } from './lib/theme';
import { store } from './settings/instance';
import { perfTier } from './host/perfTier';
import { frameStyleOf } from './settings/frameStyle';
import { deriveLabel, validateLabel } from './settings/identity';
import { FrameLayers } from './ui/FrameLayers';
import { Caption } from './ui/Caption';
import { MissionClock } from './modules/MissionClock';
import { calendarFeed } from './modules/calendarSource';
import { TopModule } from './modules/TopModule';
import { BottomModule } from './modules/BottomModule';
import { LeftModule } from './modules/LeftModule';
import { CenterModule } from './modules/CenterModule';
import { RightModule } from './modules/RightModule';
import { DrawerModule } from './modules/DrawerModule';
import { BootModule } from './modules/BootModule';
import { JarvisModule, JarvisLogModule } from './modules/JarvisModule';
import { jarvisFeed, jarvisLog, jarvisPop } from './host/jarvisFeed';
import { styleFrom } from './modules/style';
import { modulesOn } from './modules/modulesOn';
import { hiddenZones } from './modules/hidden';
import { bootReplays, hudHidden } from './modules/overlays';
import { useCallback, useEffect, useRef, useState } from 'preact/hooks';

const v = (settings as { variables: Record<string, string> }).variables;
// Skin glow model (lib.lua Canvas:neon, tier 0): outer halo w*GlowWidth*2.1 at GlowAlpha*0.38, glow w*GlowWidth at GlowAlpha, core w.
const glowA = num(v, 'GlowAlpha', 46) / 255, glowW = num(v, 'GlowWidth', 3.2), LW = 1.6;

const { canvas, margins, safe_area: sa, taskbar } = layout;
const ICONS = ['rocket', 'starship', 'camera', 'book'] as const;
const iconSet = icons.icons as unknown as Record<string, Prim[]>;
// ?debug=1 only: the skin draws no zone outlines (only edit mode: Canvas:flush, fill 255,200,0,18 / stroke 255,200,0,200 / width 2).
const debug = new URLSearchParams(location.search).get('debug') === '1';
// Modules are off until proven (architecture plan rule 4): ?module=clock turns one on, ?module=top,left a few, ?module=all every one.
const on = modulesOn(new URLSearchParams(location.search).get('module'));
const clockOn = on('clock');
const topOn = on('top');
const bottomOn = on('bottom');
const leftOn = on('left');
const rightOn = on('right');
const centerOn = on('center');
const drawerOn = on('drawer');
const bootOn = on('boot');
const jarvisOn = on('jarvis');
const jarvisLogOn = on('jarvislog');
// controller.lua: the start-up sequence plays when the app starts, not on Reload HUD (the tab's sessionStorage survives a reload)
const firstLoad = (() => {
  try {
    if (sessionStorage.getItem('cspace.booted')) return false;
    sessionStorage.setItem('cspace.booted', '1');
  } catch { /* storage blocked: play it */ }
  return true;
})();
const anyOn = [clockOn, topOn, bottomOn, leftOn, rightOn, centerOn, drawerOn, bootOn, jarvisOn, jarvisLogOn].some(Boolean);
const clockZone = layout.zones.find((z) => z.id === 'L_location');
/** The assistant's HUD label: AssistantLabel, or the name dotted like the skin's H.assistant('dots'). */
const hudLabel = (v: Record<string, string>) => {
  const l = validateLabel(v.AssistantLabel ?? '', v.JarvisName || undefined);
  return l.ok ? l.value : deriveLabel(v.JarvisName ?? '');
};

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

// svg units per CSS pixel (the viewBox fits the canvas to the window); Rainmeter is DPI-unaware, so the skin's Scale is in
// logical screen pixels (0.67 fills a 150 % screen) and dividing by the fit draws the same at any display scale or zoom
const fitOf = () => Math.min(innerWidth / canvas.w, innerHeight / canvas.h) || 1;

export function Hud() {
  const pad = margins.module + margins.animationBleed;
  const [fit, setFit] = useState(fitOf);
  // the log is a pop-up in the skin (Overlay\Jarvis): closed until asked for; ?module=jarvislog alone opens it for dev
  const [logOpen, setLogOpen] = useState(() => new URLSearchParams(location.search).get('module') === 'jarvislog');
  // JARVIS's POP <n> open|close (muted speakers, STEALTH, "show me what you said"): the first one after a load is only remembered, as jarvis.lua does
  const popSeen = useRef<string | null>(null);
  const pop = jarvisPop.value;
  useEffect(() => {
    if (popSeen.current !== null && pop !== popSeen.current) {
      const act = pop.split(' ').pop();
      if (act === 'open') setLogOpen(true);
      else if (act === 'close') setLogOpen(false);
    }
    popSeen.current = pop;
  }, [pop]);
  const closeLog = useCallback(() => setLogOpen(false), []);
  useEffect(() => {
    const on = () => setFit(fitOf());
    addEventListener('resize', on); // a display-scale or zoom change resizes the CSS viewport
    return () => removeEventListener('resize', on);
  }, []);
  // the tier the page computes stands in for the skin's saved PerfTier, so every module draws at it
  const values: Record<string, string> = { ...store.values.value, PerfTier: String(perfTier.value) };
  values.Scale = String(num(values, 'Scale', 1) / fit);
  const hide = hiddenZones(values); // the Off_ settings, as the skin's control.lua deactivates configs
  const shown = !hudHidden.value; // the console's OFF tab keeps only the top console
  return (
    <>
    {shown && values.Off_Frame !== '1' && <FrameLayers style={frameStyleOf(values)} values={values} />}
    <svg id="hud" viewBox={`0 0 ${canvas.w} ${canvas.h}`} style={{ width: '100vw', height: '100vh', position: 'relative' }}
      preserveAspectRatio="xMidYMid meet">
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
      {!anyOn && ICONS.map((name, i) => (
        <g transform={`translate(${200 + i * 150} 700) scale(1.2)`} data-icon={name}>
          <Neon d={iconPath(iconSet[name] ?? [])} />
        </g>
      ))}
      {topOn && <TopModule style={styleFrom(values)} values={values} hide={hide} />}
      {shown && bottomOn && <BottomModule style={styleFrom(values)} hide={hide} />}
      {shown && leftOn && <LeftModule style={styleFrom(values)} hide={hide} />}
      {shown && rightOn && <RightModule style={styleFrom(values)} mask={values.IpMask !== '0'} link={Number(values.LinkDownMbps) || 0} linkUp={Number(values.LinkUpMbps) || 0} hide={hide} />}
      {shown && centerOn && <CenterModule style={styleFrom(values)} sphere={!jarvisOn} hide={hide} link={Number(values.LinkDownMbps) || 0} linkUp={Number(values.LinkUpMbps) || 0} />}
      {shown && drawerOn && values.Off_OverlayDrawer !== '1' && <DrawerModule style={styleFrom(values)} />}
      {/* a replay plays whatever BootAnim says, as !ActivateConfig Boot does; the key restarts it */}
      {bootOn && store.loaded.value && (bootReplays.value > 0 || firstLoad && values.BootAnim !== '0') && <BootModule key={bootReplays.value} style={styleFrom(values)} />}
      {shown && jarvisOn && <JarvisModule style={styleFrom(values)} feed={jarvisFeed.value} label={hudLabel(values)} enabled={values.JarvisEnabled !== '0'}
        orb={{ bright: Number(values.JarvisOrbBright), tint: Number(values.JarvisTint), size: Number(values.JarvisOrbSize),
          cols: { idle: values.JarvisColorIdle, listen: values.JarvisColorListen, speak: values.JarvisColorSpeak } }} onMenu={() => setLogOpen((o) => !o)} />}
      {jarvisLogOn && logOpen && <JarvisLogModule style={styleFrom(values)} log={jarvisLog.value.log} live={jarvisLog.value.live} muted={jarvisLog.value.muted}
        assistant={(values.JarvisName ?? '').replace(/[^A-Za-z0-9]/g, '') || 'Clover'} onClose={closeLog} />}
      {shown && clockOn && clockZone && values.Off_LeftLocation !== '1' && <MissionClock zone={clockZone} source={calendarFeed.value} captions={values.CaptionStyle !== '0'} style={styleFrom(values)} />}
    </svg>
    <Caption on={values.CaptionStyle !== '0'} />
    </>
  );
}
