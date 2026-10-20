import { useState } from 'preact/hooks';
import { Hud } from '../Hud';
import { DEFS, host, store } from '../settings/instance';
import { ControlCenter } from './ControlCenter';

/** The HUD plus a small button that opens the Control Center over it. `?panel=control` starts open without the HUD. */
export function Shell({ standalone }: { standalone: boolean }) {
  const [open, setOpen] = useState(standalone);
  return (
    <>
      {!standalone && <Hud />}
      {!open && <button type="button" class="ctl-action cc-open" aria-label="Open Control Center" onClick={() => setOpen(true)}>Settings</button>}
      {open && <ControlCenter store={store} host={host} defs={DEFS} onClose={() => setOpen(false)} />}
    </>
  );
}
