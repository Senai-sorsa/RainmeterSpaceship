import { useEffect } from 'preact/hooks';
import { WebView2Host } from '../host/HostBridge';
import { Hud } from '../Hud';
import { DEFS, host, store } from '../settings/instance';
import { ControlCenter } from './ControlCenter';
import { scheduler } from '../host/scheduler';
import { controlOpen } from '../modules/overlays';

/**
 * The HUD plus the Control Center over it, opened from the tray (control.open) like the skin's control panel; a browser
 * without a host keeps a small button. `?panel=control` starts open without the HUD.
 */
export function Shell({ standalone }: { standalone: boolean }) {
  useEffect(() => { if (standalone) controlOpen.value = true; }, [standalone]);
  const open = controlOpen.value, setOpen = (v: boolean) => { controlOpen.value = v; }; // HUD clicks open it too (console CFG, dial)
  useEffect(() => host.onMessage((m) => {
    if (m.type === 'control.open') setOpen(true);
    // a fullscreen window covers the HUD: it stays shown (no flicker) but stops animating
    if (m.type === 'host.occluded') scheduler.pause((m as { on?: boolean }).on === true);
  }), []);
  return (
    <>
      {!standalone && <Hud />}
      {!open && !(host instanceof WebView2Host) && <button type="button" class="ctl-action cc-open" data-hit aria-label="Open Control Center" onClick={() => setOpen(true)}>Settings</button>}
      {open && <ControlCenter store={store} host={host} defs={DEFS} onClose={() => setOpen(false)} />}
    </>
  );
}
