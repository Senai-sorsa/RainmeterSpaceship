import { acceptSystemMetrics } from './systemMetrics';
import { acceptSysInfo } from './sysInfo';
import { acceptJarvisUpdate } from './jarvisFeed';
import { acceptAppsState, acceptNetUpdate, acceptStatusUpdate, acceptTopProcs } from './statusFeed';

// Browser preview only (?preview=1 with no WebView2 host): made-up host messages, sent through the same validators as the
// real ones, so screenshot checks show the filled-in HUD. Generic values only; nothing here reads the machine.
// A plain setInterval, not the scheduler: headless Edge's screenshot mode hardly runs animation frames.

export function startPreviewFeed(): void {
  acceptSysInfo({ type: 'sys.info', user: 'pilot', host: 'preview-pc', os: 'Windows 11', cpu: 'SAMPLE CPU 8C', gpu: 'SAMPLE GPU', display: '2560x1600 @240' });
  acceptNetUpdate({ type: 'net.update', ping: 7, lan: '192.168.1.20', wan: '203.0.113.7' });
  acceptStatusUpdate({ type: 'status.update', kind: 'llt', hybrid: '', power: '', refresh: '', battery: '', dgpu: 'on' });
  acceptAppsState({ type: 'apps.state', states: { 'chrome.exe': 2, 'everything.exe': 1 } });
  acceptTopProcs({ type: 'procs.top', top: [{ name: 'chrome', cpu: 4.2, ram: 477_102_080 }] });
  // ?jarvis=<state> shows another orb state; the validator drops anything else
  acceptJarvisUpdate({ type: 'jarvis.update', state: new URLSearchParams(globalThis.location?.search).get('jarvis') ?? 'idle', level: 0, say: '', err: '' });
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
