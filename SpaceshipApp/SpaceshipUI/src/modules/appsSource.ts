import { signal } from '@preact/signals';
import { loadCatalog, type Catalog } from './apps';

// Fixture catalog for a browser without the host: a fixed sample built by the same loadCatalog the real data uses.
// Not the user's apps. The host sends the real ones (apps.catalog) on every page load.
const INI = `[Layout]
Slot1=chrome
Slot2=dev
Slot3=comms
Slot4=creative
Slot5=code
Slot6=mail
Slot7=paint
Slot8=dev
HideMissing=1
[App.chrome]
Name=Chrome
Short=CHROME
Icon=globe
Proc=chrome.exe
Target=start:Google Chrome
[App.code]
Name=VS Code
Short=CODE
Icon=code
Proc=Code.exe
Target=start:Visual Studio Code
[App.mail]
Name=Mail
Short=MAIL
Icon=mail
Proc=HxOutlook.exe
Target=start:Mail
[App.paint]
Name=Paint
Short=PAINT
Icon=palette
Target=start:Paint
[Category.dev]
Name=DEVELOPMENT
Short=DEV
Icon=code
Apps=code
[Category.comms]
Name=COMMUNICATION
Short=COMMS
Icon=chat
Apps=mail
[Category.creative]
Name=CREATIVE
Short=CREATIVE
Icon=palette
Apps=paint
`;

// Start-menu entries in the sample: a Start list with a junk item (the uninstaller) to show the junk filter at work.
const START = [
  { name: 'Google Chrome', id: 'chrome.id' },
  { name: 'Visual Studio Code', id: 'code.id' },
  { name: 'Mail', id: 'mail.id' },
  { name: 'Paint', id: 'paint.id' },
  { name: 'Uninstall Chrome', id: 'uninst.id' },
];

export const fakeCatalog: Catalog = loadCatalog(INI, START, () => false);

/** The host's apps.catalog (the user's Apps.ini, Start menu and which file targets exist) built into a Catalog, or null. */
export function catalogFrom(m: unknown): Catalog | null {
  if (typeof m !== 'object' || m === null) return null;
  const o = m as Record<string, unknown>;
  if (o.type !== 'apps.catalog' || typeof o.ini !== 'string' || !Array.isArray(o.start) || !Array.isArray(o.exists)) return null;
  const start = o.start.filter((e): e is [string, string] => Array.isArray(e) && typeof e[0] === 'string' && typeof e[1] === 'string')
    .map(([name, id]) => ({ name, id }));
  const have = new Set(o.exists.filter((p): p is string => typeof p === 'string'));
  return loadCatalog(o.ini, start, (p) => have.has(p));
}

/** The sample until the host sends the real catalog (a browser without the host keeps the sample). */
export const catalogFeed = signal<Catalog>(fakeCatalog);

export function acceptAppsCatalog(m: unknown): void {
  const c = catalogFrom(m);
  if (c) catalogFeed.value = c;
}
