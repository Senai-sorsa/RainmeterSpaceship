import { loadCatalog, type Catalog } from './apps';

// Fixture catalog for the left column. The real Apps.ini and the Start-menu list come from the host, which has no channel
// for them yet, so this is a fixed sample built by the same loadCatalog the real data will use. Not the user's apps.
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
