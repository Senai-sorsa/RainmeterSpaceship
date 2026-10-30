import { signal } from '@preact/signals';

// The skin's overlay configs a click opens (!ActivateConfig): the CARGO drawer and the control panel.
/** The CARGO drawer: null when shut, else the folder it opens on (slot.lua openPopup → drawer.lua Focus). */
export const drawerOpen = signal<{ focus?: string } | null>(null);
/** The Control Center over the HUD; the tray's control.open sets it too. */
export const controlOpen = signal(false);
/** A category the tray asked the Control Center to open on (About CSpace), or null. */
export const controlCat = signal<string | null>(null);
/** The console's OFF tab (console.lua toggleHud): every module but the top console hidden. */
export const hudHidden = signal(false);
/** How many times the tray asked to replay the start-up sequence (Common.inc "Play startup sequence"). */
export const bootReplays = signal(0);
