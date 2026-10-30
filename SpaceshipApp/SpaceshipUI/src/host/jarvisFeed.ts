import { signal } from '@preact/signals';
import type { Feed } from '../modules/jarvis';

const STATES = new Set(['offline', 'idle', 'listening', 'thinking', 'speaking']);

/** The host's jarvis.update message (read from Data\jarvis.txt), or null for anything else. say and err are not drawn yet. */
export function jarvisFeedFrom(m: unknown): Feed | null {
  if (typeof m !== 'object' || m === null) return null;
  const o = m as Record<string, unknown>;
  if (o.type !== 'jarvis.update' || typeof o.state !== 'string' || !STATES.has(o.state)) return null;
  if (typeof o.level !== 'number' || !(o.level >= 0 && o.level <= 1)) return null;
  return { state: o.state, level: o.level };
}

/** Offline until the host says otherwise. */
export const jarvisFeed = signal<Feed>({ state: 'offline', level: 0 });

/** JARVIS's last "POP <n> open|close" (asking for the log pop-up), '' when none. */
export const jarvisPop = signal('');

export type JarvisLog = { log: string; live: string; muted: boolean };
const MAX_LOG = 70000; // the host sends at most the last 64 KB

/** The host's jarvis.log message (Data\jarvis_log.txt, jarvis_live.txt, jarvis_env.txt), or null for anything else. */
export function jarvisLogFrom(m: unknown): JarvisLog | null {
  if (typeof m !== 'object' || m === null) return null;
  const o = m as Record<string, unknown>;
  if (o.type !== 'jarvis.log' || typeof o.log !== 'string' || typeof o.live !== 'string' || typeof o.muted !== 'boolean') return null;
  if (o.log.length > MAX_LOG || o.live.length > MAX_LOG) return null;
  return { log: o.log, live: o.live, muted: o.muted };
}

export const jarvisLog = signal<JarvisLog>({ log: '', live: '', muted: false });

export function acceptJarvisUpdate(m: unknown): void {
  const f = jarvisFeedFrom(m);
  if (f) {
    jarvisFeed.value = f;
    const pop = (m as { pop?: unknown }).pop;
    if (typeof pop === 'string' && pop.length <= 40) jarvisPop.value = pop;
    return;
  }
  const l = jarvisLogFrom(m);
  if (l) jarvisLog.value = l;
}
