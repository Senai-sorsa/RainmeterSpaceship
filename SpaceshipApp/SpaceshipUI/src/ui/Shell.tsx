import { useEffect } from 'preact/hooks';
import { WebView2Host } from '../host/HostBridge';
import { Hud } from '../Hud';
import { DEFS, host, store } from '../settings/instance';
import { ControlCenter } from './ControlCenter';
import { Notices } from './Notices';
import { scheduler } from '../host/scheduler';
import { bootReplays, controlCat, controlOpen, drawerOpen } from '../modules/overlays';

/**
 * The HUD plus the Control Center over it, opened from the tray (control.open) like the skin's control panel; a browser
 * without a host keeps a small button. `?panel=control` starts open without the HUD.
 */
export function Shell({ standalone }: { standalone: boolean }) {
  useEffect(() => { if (standalone) controlOpen.value = true; }, [standalone]);
  const open = controlOpen.value, setOpen = (v: boolean) => { controlOpen.value = v; }; // HUD clicks open it too (console CFG, dial)
  useEffect(() => host.onMessage((m) => {
    if (m.type === 'control.open') { const cat = (m as { cat?: unknown }).cat; controlCat.value = typeof cat === 'string' ? cat : null; setOpen(true); }
    // the skin's other right-click items, from the tray: the CARGO drawer and the start-up sequence
    if (m.type === 'drawer.open') drawerOpen.value = {};
    if (m.type === 'boot.play') bootReplays.value += 1;
    // a fullscreen window covers the HUD: it stays shown (no flicker) but stops animating
    if (m.type === 'host.occluded') scheduler.pause((m as { on?: boolean }).on === true);
  }), []);
  return (
    <>
      {!standalone && <Hud />}
      {!open && !(host instanceof WebView2Host) && <button type="button" class="ctl-action cc-open" data-hit aria-label="Open Control Center" onClick={() => setOpen(true)}>Settings</button>}
      {!open && <Notices />}
      {open && <ControlCenter store={store} host={host} defs={DEFS} onClose={() => setOpen(false)} />}
    </>
  );
}
