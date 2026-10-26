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

export function acceptJarvisUpdate(m: unknown): void {
  const f = jarvisFeedFrom(m);
  if (f) jarvisFeed.value = f;
}
