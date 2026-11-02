import { acceptSystemMetrics } from './systemMetrics';
import { acceptSysInfo } from './sysInfo';
import { acceptJarvisUpdate } from './jarvisFeed';
import { drawerOpen } from '../modules/overlays';
import { acceptAudioSpectrum } from './audioFeed';
import { acceptAppsState, acceptNetUpdate, acceptStatusUpdate, acceptTopProcs } from './statusFeed';

// Browser preview only (?preview=1 with no WebView2 host): made-up host messages, sent through the same validators as the
// real ones, so screenshot checks show the filled-in HUD. Generic values only; nothing here reads the machine.
// A plain setInterval, not the scheduler: headless Edge's screenshot mode hardly runs animation frames.

export function startPreviewFeed(): void {
  acceptSysInfo({ type: 'sys.info', user: 'pilot', host: 'preview-pc', os: 'Windows 11', cpu: 'SAMPLE CPU 8C', gpu: 'SAMPLE GPU', display: '2560x1600 @240', version: '0.1.0' });
  acceptNetUpdate({ type: 'net.update', ping: 7, lan: '192.168.1.20', wan: '203.0.113.7' });
  acceptStatusUpdate({ type: 'status.update', kind: 'llt', hybrid: 'on', power: '', refresh: '', battery: '', dgpu: 'on' });
  acceptAppsState({ type: 'apps.state', states: { 'chrome.exe': 2, 'everything.exe': 1 } });
  acceptTopProcs({ type: 'procs.top', top: [{ name: 'chrome', cpu: 4.2, ram: 477_102_080 }] });
  // ?jarvis=<state> shows another orb state; the validator drops anything else
  acceptJarvisUpdate({ type: 'jarvis.update', state: new URLSearchParams(globalThis.location?.search).get('jarvis') ?? 'idle', level: 0, say: '', err: '' });
  // ?jarvislog=demo fills the conversation log with made-up lines, for screenshot checks of the pop-up
  if (new URLSearchParams(globalThis.location?.search).get('jarvislog') === 'demo') acceptJarvisUpdate({ type: 'jarvis.log', muted: false, live: '',
    log: 'U|1|What is on my calendar today?\nJ|2|You have a team sync now, a dentist appointment at a quarter to seven, and the launch review on Thursday.\nU|3|Set a timer for ten minutes.\nJ|4|Timer set for ten minutes.\nS|5|Microphone was busy; retried once.\nU|6|How warm is the GPU?\nJ|7|Sixty-one degrees, well within its limits. The fans are at forty percent.\n' });
  // ?drawer=1 opens the CARGO drawer (?drawer=<folder id> opens on that folder), for screenshot checks
  const dr = new URLSearchParams(globalThis.location?.search).get('drawer');
  if (dr) drawerOpen.value = dr === '1' ? {} : { focus: dr };
  // ?audio=demo plays a made-up 24-band spectrum at 20 frames a second (a kick, a bass line, hats), for checking the ring
  if (new URLSearchParams(globalThis.location?.search).get('audio') === 'demo') {
    let t = 0;
    setInterval(() => {
      t += 1;
      const kick = Math.max(0, 1 - (t % 10) / 4), hat = t % 5 === 0 ? 1 : 0.3;
      acceptAudioSpectrum({ type: 'audio.spectrum', bands: Array.from({ length: 24 }, (_, i) => {
        const bass = i < 5 ? 0.45 + 0.5 * kick * (1 - i / 5) : 0, mid = i >= 5 && i < 16 ? 0.35 + 0.25 * Math.sin(t / 7 + i) : 0, top = i >= 16 ? 0.2 + 0.35 * hat * (i / 24) : 0;
        return Math.min(1, Math.max(0, bass + mid + top));
      }) });
    }, 50);
  }
  let seq = 0;
  const tick = () => {
    seq += 1;
    const w = (k: number) => 0.5 + 0.5 * Math.sin(seq / k);
    acceptSystemMetrics({
      type: 'system.metrics', seq, cpuPercent: 15 + 20 * w(3), memoryPercent: 62, uptimeMs: 445_680_000 + seq * 500,
      onAc: false, batteryPercent: 44, netDown: 40_000 * w(2), netUp: 9_000 * w(5), spectrum: null, processes: {},
      gpuPercent: 10 + 25 * w(4), memoryTotal: 33_285_996_544, memoryUsed: 20_615_843_840, idleMs: 0,
      driveTotal: 1_000_000_000_000, driveFree: 460_000_000_000, diskIo: 5_100_000, refreshHz: 240,
      volume: 0, volumeMuted: true, audioDevice: 'Speakers', mic: 50, micMuted: false, batteryLife: 3480, wifi: 85, hw: {},
    });
  };
  tick();
  setInterval(tick, 500);
}
