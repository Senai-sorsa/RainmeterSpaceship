import { useEffect, useState } from 'preact/hooks';
import { WebView2Host } from '../host/HostBridge';
import { Hud } from '../Hud';
import { DEFS, host, store } from '../settings/instance';
import { ControlCenter } from './ControlCenter';

/**
 * The HUD plus the Control Center over it, opened from the tray (control.open) like the skin's control panel; a browser
 * without a host keeps a small button. `?panel=control` starts open without the HUD.
 */
export function Shell({ standalone }: { standalone: boolean }) {
  const [open, setOpen] = useState(standalone);
  useEffect(() => host.onMessage((m) => { if (m.type === 'control.open') setOpen(true); }), []);
  return (
    <>
      {!standalone && <Hud />}
      {!open && !(host instanceof WebView2Host) && <button type="button" class="ctl-action cc-open" data-hit aria-label="Open Control Center" onClick={() => setOpen(true)}>Settings</button>}
      {open && <ControlCenter store={store} host={host} defs={DEFS} onClose={() => setOpen(false)} />}
    </>
  );
}
