import keys from '../../../../contract/config-keys.json';

/** Mirror of the host's message check (contract/fixtures/ui-to-host.json is the shared test). Returns the problem, or null when the message is well formed. Value rules per key are the store's job, not this one's. */
const KEY = /^[A-Za-z][A-Za-z0-9_]{0,63}$/;
const CTRL = /[\u0000-\u0008\u000b\u000c\u000e-\u001f\u007f]/; // tab and newline stay legal in free text, never in a setting value
const ACTIONS = new Set<string>(keys.actions);
const FLOWS = new Set(['gmail', 'calendars', 'obsidian']);
const DIAL_CONTROLS = new Set(['brightness', 'volume', 'mic', 'power', 'refresh']);
const POWER_MODES = new Set(['quiet', 'balance', 'performance']);
const REFRESH_RATES = new Set(['60', '165']);
// the host's fixed target.open list (Protocol.Targets)
const TARGETS = ['taskmgr', 'taskperf', 'todo', 'sound', 'display', 'power', 'mute', 'prev', 'playpause', 'next',
  'terminal', 'powershell', 'about', 'outlookcal', 'gcal', 'gmail', 'update', 'defender', 'network', 'wifi', 'spx', 'ollama', 'tailscale', 'drive', 'battery'];
const LLT_FEATURES = ['hybrid', 'power', 'refresh', 'battery']; // LltGate.Features
const LONE = /[\ud800-\udbff](?![\udc00-\udfff])|(?<![\ud800-\udbff])[\udc00-\udfff]/; // a lone surrogate is not text the host can read
const isObj = (m: unknown): m is Record<string, unknown> => typeof m === 'object' && m !== null && !Array.isArray(m);

export function messageProblem(m: unknown): string | null {
  if (!isObj(m) || typeof m.type !== 'string') return 'not a message';
  switch (m.type) {
    case 'config.get':
      return Array.isArray(m.keys) && m.keys.length <= 500 && m.keys.every((k) => typeof k === 'string' && KEY.test(k)) ? null : 'bad keys';
    case 'config.set':
      if (typeof m.key !== 'string' || !KEY.test(m.key)) return 'bad key';
      if (typeof m.value !== 'string' || m.value.length > 256 || /[\u0000-\u001f\u007f]/.test(m.value) || LONE.test(m.value)) return 'bad value';
      return Number.isSafeInteger(m.id) && (m.id as number) >= 0 ? null : 'bad id';
    case 'setup.get': case 'aboutme.get': return null;
    case 'setup.finish': return m.mode === 'defaults' || m.mode === 'custom' ? null : 'bad mode';
    case 'aboutme.set': return typeof m.text === 'string' && m.text.length <= 4000 && !CTRL.test(m.text) && !LONE.test(m.text) ? null : 'bad text';
    case 'action': return typeof m.id === 'string' && ACTIONS.has(m.id) ? null : 'action not allowed';
    case 'flow.open': return typeof m.flow === 'string' && FLOWS.has(m.flow) ? null : 'bad flow';
    case 'dial.set': return dialSetProblem(m);
    case 'hit.regions': return hitRegionsProblem(m);
    case 'app.launch': return typeof m.id === 'string' && /^[A-Za-z0-9_.-]{1,64}$/.test(m.id) ? null : 'bad app id';
    case 'target.open': return typeof m.what === 'string' && TARGETS.includes(m.what) ? null : 'bad target';
    case 'llt.set':
      if (typeof m.feature !== 'string' || !LLT_FEATURES.includes(m.feature)) return 'bad feature';
      if (typeof m.value !== 'string' || !/^[A-Za-z0-9-]{1,32}$/.test(m.value)) return 'bad value';
      return Number.isSafeInteger(m.id) && (m.id as number) >= 0 ? null : 'bad id';
    case 'status.refresh': case 'speed.run': return null;
    default: return 'unknown type';
  }
}

const MAX_RECTS = 64, MAX_COORD = 16384;
const within = (n: unknown, lo: number) => Number.isInteger(n) && (n as number) >= lo && (n as number) <= MAX_COORD;

// Up to 64 [x, y, w, h] whole numbers in window pixels, as the C# side.
function hitRegionsProblem(m: Record<string, unknown>): string | null {
  if (typeof m.keyboard !== 'boolean') return 'bad keyboard';
  if (!Array.isArray(m.rects) || m.rects.length > MAX_RECTS) return 'bad rects';
  return m.rects.every((r) => Array.isArray(r) && r.length === 4 && within(r[0], -MAX_COORD) && within(r[1], -MAX_COORD) && within(r[2], 1) && within(r[3], 1))
    ? null : 'bad rects';
}

// Shape only, as the C# side: a percent is a whole number 0..100, a mode and a rate are names. The host checks them again.
function dialSetProblem(m: Record<string, unknown>): string | null {
  if (typeof m.control !== 'string' || !DIAL_CONTROLS.has(m.control)) return 'bad control';
  if (!Number.isSafeInteger(m.id) || (m.id as number) < 0) return 'bad id';
  const v = m.value;
  switch (m.control) {
    case 'power': return typeof v === 'string' && POWER_MODES.has(v) ? null : 'bad value';
    case 'refresh': return typeof v === 'string' && REFRESH_RATES.has(v) ? null : 'bad value';
    default: return Number.isSafeInteger(v) && (v as number) >= 0 && (v as number) <= 100 ? null : 'bad value';
  }
}
