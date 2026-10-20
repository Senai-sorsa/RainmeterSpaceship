import { render } from 'preact';
import './tokens.css';
import './ui/ui.css';
import settings from './generated/settings.json';
import { themeVars } from './lib/theme';
import { DEFS, host, store } from './settings/instance';
import { SettingsPanel } from './ui/SettingsPanel';
import { Shell } from './ui/Shell';

// on <html>, where tokens.css declares the defaults, so the settings values actually override them
for (const [k, val] of Object.entries(themeVars((settings as { variables: Record<string, string> }).variables)))
  document.documentElement.style.setProperty(k, val);

host.onMessage(() => {});
const q = new URLSearchParams(location.search);
// ?host=mock&fail=<Key> makes the mock host reject writes to that key (e2e failure injection).
if (q.get('host') === 'mock' && q.get('fail')) (host as unknown as { o: { failKeys?: Set<string> } }).o.failKeys = new Set([q.get('fail')!]);
const panel = q.get('panel'); // dev routes for the shared components
if (q.get('level') === 'advanced') store.level.value = 'advanced';
render(
  panel === 'demo' || panel === 'demo-wizard'
    ? <SettingsPanel store={store} host={host} defs={DEFS} categories={['display']} mode={panel === 'demo' ? 'center' : 'wizard'} />
    : <Shell standalone={panel === 'control'} />,
  document.getElementById('app')!,
);
