import { render } from 'preact';
import { effect } from '@preact/signals';
import './tokens.css';
import './ui/ui.css';
import settings from './generated/settings.json';
import { themeVars } from './lib/theme';
import { DEFS, host, store } from './settings/instance';
import { acceptSystemMetrics, systemMetrics } from './host/systemMetrics';
import { acceptJarvisUpdate } from './host/jarvisFeed';
import { acceptSysInfo } from './host/sysInfo';
import { acceptNotice } from './host/notices';
import { acceptIconsList } from './draw/appIcons';
import { acceptAppsCatalog, catalogFeed, previewCatalog } from './modules/appsSource';
import { acceptCalendarUpdate } from './modules/calendarSource';
import { acceptAppsState, acceptNetUpdate, acceptTopProcs, acceptSpxUpdate, acceptStatusUpdate, acceptTodoUpdate } from './host/statusFeed';
import { WebView2Host } from './host/HostBridge';
import { startPreviewFeed } from './host/previewFeed';
import { startHitRegions } from './host/hitRegions';
import { scheduler } from './host/scheduler';
import { startPerfTier } from './host/perfTier';
import { SettingsPanel } from './ui/SettingsPanel';
import { Shell } from './ui/Shell';
import { Wizard } from './ui/Wizard';
import { KitDemo } from './ui/kit/KitDemo';
import { shouldShow } from './wizard/wizard';
import { useEffect, useState } from 'preact/hooks';

// on <html>, where tokens.css declares the defaults, so the settings values actually override them
// and again whenever a setting changes, so a new ColorAccent re-themes the pages without a reload
effect(() => {
  const v = { ...(settings as { variables: Record<string, string> }).variables, ...store.values.value };
  for (const [k, val] of Object.entries(themeVars(v))) document.documentElement.style.setProperty(k, val);
  document.documentElement.dataset.reduceMotion = v.ReduceMotion === '1' ? '1' : '0';
});

host.onMessage(acceptSystemMetrics);
host.onMessage(acceptJarvisUpdate);
host.onMessage(acceptSysInfo);
host.onMessage(acceptNotice);
host.onMessage(acceptAppsCatalog);
host.onMessage(acceptCalendarUpdate);
host.onMessage(acceptStatusUpdate);
host.onMessage(acceptNetUpdate);
host.onMessage(acceptSpxUpdate);
host.onMessage(acceptTodoUpdate);
host.onMessage(acceptAppsState);
host.onMessage(acceptTopProcs);
host.onMessage(acceptIconsList);
startPerfTier(systemMetrics, store.values);
if (host instanceof WebView2Host) startHitRegions(host, document, scheduler); // the browser and the mock have no click-through
// in the app the desktop wallpaper shows through like the skin; tokens.css's black stays as the stand-in in a browser
if (host instanceof WebView2Host) document.documentElement.style.background = document.body.style.background = 'transparent';
// the host hides the HUD for fullscreen apps and the lock screen; coming back fades in instead of popping
document.addEventListener('visibilitychange', () => {
  if (document.visibilityState === 'visible' && !matchMedia('(prefers-reduced-motion: reduce)').matches && document.documentElement.dataset.reduceMotion !== '1')
    document.documentElement.animate([{ opacity: 0 }, { opacity: 1 }], { duration: 250, easing: 'ease-out' });
});
const q = new URLSearchParams(location.search);
const panel = q.get('panel'); // dev routes for the shared components
if (q.get('level') === 'advanced') store.level.value = 'advanced';
/** Shows the wizard while the host says setup is not done; blank until the host answers, wizard if it never does. */
function Root() {
  const [wiz, setWiz] = useState<boolean | null>(null);
  useEffect(() => {
    // ?preview=1 in a plain browser (no WebView2 host) goes straight to the HUD with the skin's own apps, for screenshot checks
    const preview = q.get('preview') === '1' && !(globalThis as { chrome?: { webview?: unknown } }).chrome?.webview;
    if (preview) { setWiz(false); previewCatalog().then((c) => { catalogFeed.value = c; }); startPreviewFeed(); } else shouldShow(host).then(setWiz);
    host.onMessage((m) => { if (m.type === 'setup.state') setWiz(m.done !== true); });
  }, []);
  if (wiz === null) return null;
  return wiz && panel !== 'control' ? <Wizard store={store} host={host} defs={DEFS} /> : <Shell standalone={panel === 'control'} />;
}
render(
  panel === 'kit'
    ? <KitDemo />
    : panel === 'demo' || panel === 'demo-wizard'
    ? <SettingsPanel store={store} host={host} defs={DEFS} categories={['display']} mode={panel === 'demo' ? 'center' : 'wizard'} />
    : <Root />,
  document.getElementById('app')!,
);
