import { useState } from 'preact/hooks';
import type { HostBridge } from '../host/HostBridge';
import { messageProblem } from '../host/contract';
import { jarvisFeed } from '../host/jarvisFeed';
import { notices } from '../host/notices';
import { upkeepStatus } from '../host/statusFeed';
import { FIXES, diagnose, runFix } from '../help/diagnosis';
import { HudPanel } from './kit/HudPanel';
import { StatusPill } from './kit/StatusPill';

const ASK_MAX = 400;
const PILL = { ok: 'linked', warn: 'warn', error: 'error' } as const;
const PILL_TEXT = { ok: 'OK', warn: 'Warning', error: 'Error' } as const;

/** Help in the System category: what looks wrong, one-click fixes from a fixed list, and a box that asks JARVIS (his answer shows in his log). */
export function HelpCenter({ host }: { host: HostBridge }) {
  const [q, setQ] = useState('');
  const [sent, setSent] = useState(false);
  const findings = diagnose({ jarvis: jarvisFeed.value, mailWhy: upkeepStatus.value.mailWhy, notices: notices.value });
  const offline = jarvisFeed.value.state === 'offline';
  const ask = () => {
    const msg = { type: 'jarvis.cmd', cmd: 'ask', text: `About CSpace: ${q.trim()}` };
    if (!q.trim() || messageProblem(msg)) return;
    host.send(msg);
    setSent(true); setQ('');
  };
  return (
    <HudPanel index="02" title="Help" class="helpc" id="helpc">
      <ul class="helpc-list" aria-label="Findings">
        {findings.map((f) => (
          <li key={f.id}>
            <StatusPill state={PILL[f.level]} text={PILL_TEXT[f.level]} /> <span>{f.text}</span>
            {f.fix && <button type="button" class="ctl-action" onClick={() => runFix(f.fix!, host)}>{FIXES[f.fix].label}</button>}
          </li>
        ))}
      </ul>
      <div class="helpc-ask">
        <input class="ctl-text" type="text" maxLength={ASK_MAX} aria-label="Ask JARVIS for help" placeholder="Ask JARVIS about CSpace" value={q}
          onInput={(e) => { setQ((e.target as HTMLInputElement).value); setSent(false); }} onKeyDown={(e) => { if (e.key === 'Enter') ask(); }} />
        <button type="button" class="ctl-action" disabled={offline || !q.trim()} onClick={ask}>Ask JARVIS</button>
      </div>
      {offline && <small>JARVIS is offline, so he cannot answer. Start him with the button above.</small>}
      {sent && <small role="status">Sent. His answer shows in the JARVIS log.</small>}
    </HudPanel>
  );
}
