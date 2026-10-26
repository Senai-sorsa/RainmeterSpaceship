import { signal } from '@preact/signals';

// The skin's overlay configs a click opens (!ActivateConfig): the CARGO drawer and the control panel.
/** The CARGO drawer: null when shut, else the folder it opens on (slot.lua openPopup → drawer.lua Focus). */
export const drawerOpen = signal<{ focus?: string } | null>(null);
/** The Control Center over the HUD; the tray's control.open sets it too. */
export const controlOpen = signal(false);
