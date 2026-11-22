import { signal } from '@preact/signals';

export type Notice = { source: string; level: 'warn' | 'error'; text: string };
const MAX = 3;

/** Plain-language problems the host reports (a feed failing, the web view giving up). The newest three; one per source. */
export const notices = signal<Notice[]>([]);

/** Keeps a well-formed notice message; text is only ever shown as a text node, never as HTML. */
export function acceptNotice(m: unknown): void {
  const o = m as Record<string, unknown> | null;
  if (typeof o !== 'object' || o === null || o.type !== 'notice') return;
  const { source, level, text } = o;
  if (typeof source !== 'string' || !/^[a-z][a-z0-9_.-]{0,31}$/.test(source)) return;
  if ((level !== 'warn' && level !== 'error') || typeof text !== 'string' || text.length === 0 || text.length > 200) return;
  notices.value = [{ source, level: level as Notice['level'], text }, ...notices.value.filter((n) => n.source !== source)].slice(0, MAX);
}

export const dismissNotice = (source: string) => { notices.value = notices.value.filter((n) => n.source !== source); };
