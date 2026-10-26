import { render } from 'preact';
import './tokens.css';
import './ui/ui.css';
import settings from './generated/settings.json';
import { themeVars } from './lib/theme';
import { DEFS, host, store } from './settings/instance';
import { acceptSystemMetrics } from './host/systemMetrics';
import { acceptJarvisUpdate } from './host/jarvisFeed';
import { acceptNetUpdate, acceptSpxUpdate, acceptStatusUpdate, acceptTodoUpdate } from './host/statusFeed';
import { WebView2Host } from './host/HostBridge';
import { startHitRegions } from './host/hitRegions';
import { scheduler } from './host/scheduler';
import { SettingsPanel } from './ui/SettingsPanel';
import { Shell } from './ui/Shell';
import { Wizard } from './ui/Wizard';
import { shouldShow } from './wizard/wizard';
import { useEffect, useState } from 'preact/hooks';

// on <html>, where tokens.css declares the defaults, so the settings values actually override them
for (const [k, val] of Object.entries(themeVars((settings as { variables: Record<string, string> }).variables)))
  document.documentElement.style.setProperty(k, val);

host.onMessage(acceptSystemMetrics);
host.onMessage(acceptJarvisUpdate);
host.onMessage(acceptStatusUpdate);
host.onMessage(acceptNetUpdate);
host.onMessage(acceptSpxUpdate);
host.onMessage(acceptTodoUpdate);
if (host instanceof WebView2Host) startHitRegions(host, document, scheduler); // the browser and the mock have no click-through
const q = new URLSearchParams(location.search);
const panel = q.get('panel'); // dev routes for the shared components
if (q.get('level') === 'advanced') store.level.value = 'advanced';
/** Shows the wizard while the host says setup is not done; blank until the host answers, wizard if it never does. */
function Root() {
  const [wiz, setWiz] = useState<boolean | null>(null);
  useEffect(() => {
    shouldShow(host).then(setWiz);
    host.onMessage((m) => { if (m.type === 'setup.state') setWiz(m.done !== true); });
  }, []);
  if (wiz === null) return null;
  return wiz && panel !== 'control' ? <Wizard store={store} host={host} defs={DEFS} /> : <Shell standalone={panel === 'control'} />;
}
render(
  panel === 'demo' || panel === 'demo-wizard'
    ? <SettingsPanel store={store} host={host} defs={DEFS} categories={['display']} mode={panel === 'demo' ? 'center' : 'wizard'} />
    : <Root />,
  document.getElementById('app')!,
);
