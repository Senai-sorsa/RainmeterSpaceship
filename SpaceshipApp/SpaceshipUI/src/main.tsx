import { render } from 'preact';
import './tokens.css';
import './ui/ui.css';
import { Hud } from './Hud';
import settings from './generated/settings.json';
import { themeVars } from './lib/theme';
import { DEFS, host, store } from './settings/instance';
import { SettingsPanel } from './ui/SettingsPanel';

// on <html>, where tokens.css declares the defaults, so the settings values actually override them
for (const [k, val] of Object.entries(themeVars((settings as { variables: Record<string, string> }).variables)))
  document.documentElement.style.setProperty(k, val);

host.onMessage(() => {});
const q = new URLSearchParams(location.search);
const panel = q.get('panel'); // dev routes for the shared components
if (q.get('level') === 'advanced') store.level.value = 'advanced';
render(
  panel === 'demo' || panel === 'demo-wizard'
    ? <SettingsPanel store={store} host={host} defs={DEFS} categories={['display']} mode={panel === 'demo' ? 'center' : 'wizard'} />
    : <Hud />,
  document.getElementById('app')!,
);
