import keys from '../../../../contract/config-keys.json';

/** Mirror of the host's message check (contract/fixtures/ui-to-host.json is the shared test). Returns the problem, or null when the message is well formed. Value rules per key are the store's job, not this one's. */
const KEY = /^[A-Za-z][A-Za-z0-9_]{0,63}$/;
const CTRL = /[\u0000-\u0008\u000b\u000c\u000e-\u001f\u007f]/; // tab and newline stay legal in free text, never in a setting value
const ACTIONS = new Set<string>(keys.actions);
const FLOWS = new Set(['gmail', 'calendars', 'obsidian']);
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
    default: return 'unknown type';
  }
}
