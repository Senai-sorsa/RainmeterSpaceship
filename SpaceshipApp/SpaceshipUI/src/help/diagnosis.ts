import type { HostBridge, Msg } from '../host/HostBridge';
import type { Notice } from '../host/notices';

export type FixId = 'start_jarvis' | 'recheck_mail' | 'recheck_status' | 'reload_hud';
export type Finding = { id: string; level: 'ok' | 'warn' | 'error'; text: string; fix?: FixId };
export type Facts = { jarvis: { state: string; note?: string }; mailWhy?: string; notices: Notice[] };

/** The only things the Help panel can run, each a message the host already allows or a page reload; the user clicks, this code runs it. */
export const FIXES: Record<FixId, { label: string; msg?: Msg }> = {
  start_jarvis: { label: 'Start JARVIS', msg: { type: 'jarvis.cmd', cmd: 'start' } },
  recheck_mail: { label: 'Check mail now', msg: { type: 'status.refresh', kind: 'mail' } },
  recheck_status: { label: 'Re-check status', msg: { type: 'status.refresh' } },
  reload_hud: { label: 'Reload HUD page' },
};

export function runFix(id: FixId, host: HostBridge): void {
  const m = FIXES[id].msg;
  if (m) host.send(m); else location.reload();
}

/** Plain rules over what the page already knows; no model is involved, so nothing here can authorize an action. */
export function diagnose(f: Facts): Finding[] {
  const out: Finding[] = [];
  if (f.jarvis.state === 'offline') {
    if (f.jarvis.note === 'NO PYTHON') out.push({ id: 'jarvis-python', level: 'error', text: 'JARVIS cannot start: Python was not found on this computer.' });
    else if (f.jarvis.note === 'NO SCRIPT') out.push({ id: 'jarvis-script', level: 'error', text: 'JARVIS cannot start: his script is missing from the skin folder.' });
    else out.push({ id: 'jarvis-offline', level: 'warn', text: 'JARVIS is offline.', fix: 'start_jarvis' });
  }
  if (f.mailWhy && f.mailWhy !== 'off' && f.mailWhy !== 'no host data') out.push({ id: 'mail', level: 'warn', text: 'The mail check is failing. If it keeps failing, connect Gmail again in Integrations.', fix: 'recheck_mail' });
  for (const n of f.notices) out.push({ id: `notice-${n.source}`, level: n.level, text: n.text, fix: 'recheck_status' });
  return out.length ? out : [{ id: 'none', level: 'ok', text: 'No problems found.' }];
}
