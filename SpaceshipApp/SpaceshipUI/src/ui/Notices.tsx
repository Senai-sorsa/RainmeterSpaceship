import { dismissNotice, notices } from '../host/notices';
import { HudPanel } from './kit/HudPanel';

/** The host's problem reports as a small stack over the HUD: a level pill, the text and Dismiss. */
export function Notices() {
  const list = notices.value;
  if (list.length === 0) return null;
  return (
    <div class="notices" data-hit role="region" aria-label="Notices">
      {list.map((n) => (
        <HudPanel key={n.source} title={n.source} pill={{ state: n.level, text: n.level === 'error' ? 'Error' : 'Warning' }} class="notice">
          <p role={n.level === 'error' ? 'alert' : 'status'}>{n.text}</p>
          <button type="button" class="ctl-action" onClick={() => dismissNotice(n.source)}>Dismiss</button>
        </HudPanel>
      ))}
    </div>
  );
}
