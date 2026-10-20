import { render } from 'preact';
import './tokens.css';
import { Hud } from './Hud';
import settings from './generated/settings.json';
import { themeVars } from './lib/theme';
import { chooseHost } from './host/HostBridge';

// on <html>, where tokens.css declares the defaults, so the settings values actually override them
for (const [k, val] of Object.entries(themeVars((settings as { variables: Record<string, string> }).variables)))
  document.documentElement.style.setProperty(k, val);

const host = chooseHost(); // UI code only ever sees HostBridge
host.onMessage(() => {});
render(<Hud />, document.getElementById('app')!);
