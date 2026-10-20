import { useState } from 'preact/hooks';
import type { ComponentChildren } from 'preact';

const KEY = 'ui.groups.v1';
const mem: Record<string, boolean> = {}; // keeps collapse working for the session when storage is blocked

function read(): Record<string, boolean> {
  try {
    const o = JSON.parse(localStorage.getItem(KEY) ?? '{}');
    return o && typeof o === 'object' && !Array.isArray(o) ? o : {};
  } catch { return {}; }
}
function write(id: string, open: boolean) {
  mem[id] = open;
  try { localStorage.setItem(KEY, JSON.stringify({ ...read(), [id]: open })); } catch { /* storage blocked: session only */ }
}
function isOpen(id: string, dflt: boolean) {
  if (id in mem) return mem[id];
  const v = read()[id];
  return typeof v === 'boolean' ? v : dflt;
}

/** Collapsible group; `id` is "<category>/<group>". Open state is read once at mount and persisted on toggle. */
export function GroupSection({ id, title, children, attr = 'data-group', defaultOpen = true }: { id: string; defaultOpen?: boolean; title: string; children: ComponentChildren; attr?: 'data-group' | 'data-advanced' }) {
  const [open] = useState(() => isOpen(id, defaultOpen));
  const a = { [attr]: attr === 'data-group' ? id : '' };
  return (
    <details class="group" open={open} {...a} onToggle={(e) => write(id, (e.currentTarget as HTMLDetailsElement).open)}>
      <summary class="label">{title}</summary>
      <div class="group-body">{children}</div>
    </details>
  );
}
