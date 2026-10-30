import { Canvas, type Op, type Style, type Zone } from '../draw/canvas';
import type { ActionDef } from '../actions/gate';

// Port of Skins/Spaceship/@Resources/Scripts/console.lua: the top console with the GPU-mode tabs and the quick settings.
// Clicks run nothing here. consoleIntent() says what the click asks for: a Legion Toolkit switch (lltMessage -> the host's
// llt.set, checked again by its LltGate), a status refresh, a UI change, or nothing.

export type HybridMode = 'ECO' | 'HYBRID' | 'AUTO' | 'DGPU';
/** Status read from the host, lower-cased like console.lua's OnStatus. '' means not known yet. */
export type ConsoleState = { hybrid: string; power: string; refresh: string; battery: string; dgpu: string };
export type ConsoleConfig = {
  powerModes: string[];
  rates: string[];
  conserveWord: string; // a battery status containing this word means conservation is on
  normalWord: string;
  chargeLimit: number;
  perfOverride: number; // -1 is auto
  perfTier: number; // 0 FULL, 1 LITE, 2 LOW, 3 STEALTH
};
/** What the console shows that is not in the status: the armed tab, the HUD toggle and the last message. */
export type ConsoleView = { armed: number | null; hudHidden: boolean; msg: string; msgAt: number };
export type Hit = { id: number; x: number; y: number; w: number; h: number; tip: string };
export type ConsoleFrame = { ops: Op[]; hits: Hit[] };
export type Intent =
  | { kind: 'action'; action: string; args: Record<string, string | number> }
  | { kind: 'ui'; name: 'hud' | 'drawer' | 'control' | 'master' | 'perf'; value?: number }
  | { kind: 'none' };

const TABS: { id: string; mode: HybridMode; tip: string }[] = [
  { id: 'ECO', mode: 'ECO', tip: 'Integrated only, RTX 5070 off' },
  { id: 'HYBRID', mode: 'HYBRID', tip: 'Both GPUs, RTX wakes on demand' },
  { id: 'AUTO', mode: 'AUTO', tip: 'Hybrid on AC, integrated on battery' },
  { id: 'dGPU', mode: 'DGPU', tip: 'Discrete only (MUX), reboot needed' },
];
const TIERS = ['FULL', 'LITE', 'LOW', 'STEALTH'];
const PM: Record<string, string> = { quiet: 'QUIET', balance: 'BAL', balanced: 'BAL', performance: 'PERF', custom: 'CUST', extreme: 'MAX' };

// reference positions (ref pixels inside the console zone 463..797 x 10..57, centred on the axis x = 630)
const SXR = 2560 / 1260, SYR = 1600 / 709;
const RX = (x: number) => (x - 463) * SXR;
const RY = (y: number) => (y - 10) * SYR;
const TABX = [549, 591, 630, 669, 711];
const BOX = [[538, 559], [569, 589]];
const TXT: [number, number][] = [[671, 51], [695, 50], [719, 49], [743, 48], [767, 47]];

/** Hit ids as the Lua draws them. Ids above 5 are remapped to the action they stand for, as HITMAP does. */
const HITMAP: Record<number, number> = { 6: 11, 7: 13, 8: 6, 9: 7, 10: 8, 11: 9, 12: 12, 14: 10 };
/** The accent underline under the lit tab (alpha 160). Exported for the tests, which count it. */
export const isTabUnderline = (o: Op) => o.shape.kind === 'poly' && o.stroke?.width === 1.2 && o.stroke?.color[3] === 160;

/** 1-based tab that matches the status, or 0 when none does. */
const hybridIndex = (st: ConsoleState) => (st.hybrid === '' ? 0 : TABS.findIndex((t) => t.mode.toLowerCase() === st.hybrid) + 1);

const HYBRID_DEFAULTS: Record<HybridMode, string> = { ECO: 'on-igpu-only', HYBRID: 'on', AUTO: 'on-auto', DGPU: 'off' };
/** console.lua hybridIndex: the raw Legion Toolkit value matches a tab through its LltHybrid<MODE> setting; consoleFrame takes the mode name. */
export function withHybridMode(st: ConsoleState, values: Record<string, string>): ConsoleState {
  const t = st.hybrid === '' ? undefined : TABS.find((t) => (values[`LltHybrid${t.mode}`] ?? HYBRID_DEFAULTS[t.mode]).toLowerCase() === st.hybrid);
  return { ...st, hybrid: t?.mode.toLowerCase() ?? '' };
}

function quickButtons(st: ConsoleState, cfg: ConsoleConfig) {
  const tierOv = cfg.perfOverride;
  const tierName = TIERS[cfg.perfTier] ?? 'FULL';
  const pw = st.power !== '' ? PM[st.power] ?? st.power.slice(0, 5).toUpperCase() : '--';
  const hzDigits = st.refresh.match(/\d+/)?.[0];
  const hz = st.refresh !== '' ? `${hzDigits ?? st.refresh}HZ` : '--HZ';
  const cons = st.battery !== '' ? (st.battery.includes(cfg.conserveWord.toLowerCase()) ? 'ON' : 'OFF') : '--';
  return [
    { label: pw, tip: `Modes: ${cfg.powerModes.join(' / ')}`, on: false },
    { label: hz, tip: `Rates: ${cfg.rates.join(' / ')} Hz`, on: false },
    { label: `${cfg.chargeLimit}%`, tip: undefined, on: cons === 'ON' },
    {
      label: tierOv < 0 ? tierName.slice(0, 4) : (TIERS[tierOv] ?? tierName).slice(0, 4),
      tip: tierOv >= 0 ? `Auto picks ${tierName}` : undefined, on: false,
    },
    { label: 'dGPU', light: st.dgpu, tip: `RTX 5070: ${st.dgpu === 'on' ? 'present / powered' : st.dgpu === 'off' ? 'off (ECO mode)' : 'unknown'}`, on: false },
    { label: 'CARGO', tip: undefined, on: false },
    { label: 'MASTER', tip: 'Kill switch: STEALTH / restore', on: tierOv === 3 },
    { label: 'CFG', tip: 'Control Center: modules, layout, theme, apps, sensors, presets', on: false },
  ];
}

export function consoleFrame(st: ConsoleState, cfg: ConsoleConfig, view: ConsoleView, zone: Zone, style: Style, now: number): ConsoleFrame {
  const c = new Canvas(zone, style);
  const hits: Hit[] = [];
  const W = style.white, D = style.dim;
  const active = view.hudHidden ? 5 : hybridIndex(st);
  // tab row (reference: COMBAT STARMAP MINING GROUND OFF); the fifth tab is the HUD toggle
  [...TABS.map((t) => ({ id: t.id, tip: t.tip })), { id: 'OFF', tip: '' }].forEach((t, i) => {
    const x = RX(TABX[i]), y = RY(23), on = i + 1 === active;
    const armed = view.armed === i + 1;
    c.text(x, y, armed ? 'CONFIRM?' : t.id, {
      size: 6.4, weight: 700, align: 'CenterCenter', color: armed ? style.warn : on ? W : [150, 170, 185, 255], alpha: on ? 255 : 200,
    });
    if (on) c.hair(x - 22, y + 9, x + 22, y + 9, style.accent, 1.2, 160);
    if (t.id === 'dGPU' && st.dgpu !== '') c.dot(x + 26, y, 2.6, st.dgpu === 'on' ? style.good : D);
    hits.push({ id: i + 1, x: x - 34, y: y - 12, w: 68, h: 24, tip: t.tip });
  });
  // CARGO and CFG: plain glowing labels with a short underline
  const boxes = [{ label: 'CARGO', hit: 6, tip: '' }, { label: 'CFG', hit: 7, tip: 'Control Center' }];
  boxes.forEach((b, i) => {
    const x0 = RX(BOX[i][0]), x1 = RX(BOX[i][1]), y0 = RY(46), y1 = RY(55), cx = (x0 + x1) / 2;
    c.text(cx, (y0 + y1) / 2, b.label, { size: 5.6, weight: 700, align: 'CenterCenter', color: style.accent });
    c.hair(cx - (x1 - x0) * 0.32, y1 + 2, cx + (x1 - x0) * 0.32, y1 + 2, style.accent, 1.2, 150);
    hits.push({ id: b.hit, x: x0, y: y0, w: x1 - x0, h: y1 - y0, tip: b.tip });
  });
  // quick settings: MISL HEAT CLSN FUEL GFRC, the lit ones highlighted
  const bs = quickButtons(st, cfg);
  [bs[0], bs[1], bs[2], bs[3], bs[6]].forEach((b, i) => {
    const x = RX(TXT[i][0]), y = RY(TXT[i][1]);
    c.text(x, y, b.label, { size: 5.6, weight: 700, clip: 64, align: 'CenterCenter', color: b.on ? style.hi : [160, 180, 195, 255] });
    hits.push({ id: 8 + i, x: x - 24, y: y - 10, w: 48, h: 20, tip: b.tip ?? '' });
  });
  // transient message between the two groups
  if (now - view.msgAt < 6000 && view.msg !== '') {
    c.text(RX(630), RY(49), view.msg, { size: 6.5, weight: 700, align: 'CenterCenter', color: style.warn, clip: 150 });
  }
  hits.push({ id: 14, x: RX(612), y: RY(50), w: RX(648) - RX(612), h: RY(58) - RY(50), tip: `dGPU: ${st.dgpu !== '' ? st.dgpu : 'unknown'}` });
  return { ops: c.flush(), hits };
}

/** A cycle through a list: the entry after the current one, or the first when the current one is not in it. */
function cycle(list: string[], current: string): string {
  const i = list.findIndex((v) => current === v.toLowerCase() || current.includes(v.toLowerCase()));
  return i < 0 ? list[0] : list[(i + 1) % list.length];
}

/** What a click on hit k asks for. Right-click on the tabs and the quick row refreshes the status. */
export function consoleIntent(k: number, st: ConsoleState, cfg: ConsoleConfig, view: ConsoleView, button: 'left' | 'right' = 'left'): Intent {
  if (button === 'right') return k <= 5 ? { kind: 'action', action: 'status.refresh', args: {} } : { kind: 'none' };
  const id = k > 5 ? (HITMAP[k] ?? k) : k;
  if (id <= 4) return { kind: 'action', action: 'llt.hybrid', args: { mode: TABS[id - 1].mode } };
  switch (id) {
    case 5: return { kind: 'ui', name: 'hud' };
    case 6: return { kind: 'action', action: 'llt.power', args: { mode: cycle(cfg.powerModes, st.power) } };
    case 7: return { kind: 'action', action: 'llt.refresh', args: { hz: cycle(cfg.rates, st.refresh.match(/\d+/)?.[0] ?? '') } };
    case 8: {
      const on = st.battery.includes(cfg.conserveWord.toLowerCase());
      return { kind: 'action', action: 'llt.battery', args: { mode: on ? cfg.normalWord : cfg.conserveWord } };
    }
    case 9: {
      const ov = cfg.perfOverride + 1;
      return { kind: 'ui', name: 'perf', value: ov > 3 ? -1 : ov };
    }
    case 10: return { kind: 'action', action: 'status.refresh', args: {} };
    case 11: return { kind: 'ui', name: 'drawer' };
    case 12: return { kind: 'ui', name: 'master' };
    case 13: return { kind: 'ui', name: 'control' };
    default: return { kind: 'none' };
  }
}

/** The action list the console needs. A change confirms first; status.refresh only reads. */
export function consoleActions(cfg: ConsoleConfig): Record<string, ActionDef> {
  return {
    'llt.hybrid': { args: { mode: { kind: 'enum', values: ['ECO', 'HYBRID', 'AUTO', 'DGPU'] } }, confirm: true },
    'llt.power': { args: { mode: { kind: 'enum', values: cfg.powerModes } }, confirm: true },
    'llt.refresh': { args: { hz: { kind: 'enum', values: cfg.rates } }, confirm: true },
    'llt.battery': { args: { mode: { kind: 'enum', values: [cfg.conserveWord, cfg.normalWord] } }, confirm: true },
    'status.refresh': { args: {}, confirm: false },
  };
}

const LLT: Record<string, [feature: string, arg: string]> = {
  'llt.hybrid': ['hybrid', 'mode'], 'llt.power': ['power', 'mode'], 'llt.refresh': ['refresh', 'hz'], 'llt.battery': ['battery', 'mode'],
};
/** The host's llt.set for a Legion Toolkit intent (console.lua runLlt), and its line: "> VALUE", condensed from the skin's
 * "SET FEATURE > VALUE", which its 150-unit message clip cuts off. Null for any other intent. */
export function lltMessage(it: Intent, id: number) {
  const f = it.kind === 'action' ? LLT[it.action] : undefined;
  if (!f || it.kind !== 'action') return null;
  const value = String(it.args[f[1]]);
  return { msg: { type: 'llt.set', id, feature: f[0], value }, say: `> ${value.toUpperCase()}` };
}
