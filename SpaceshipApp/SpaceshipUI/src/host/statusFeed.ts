import { signal } from '@preact/signals';
import type { UpkeepInput } from '../modules/upkeep';
import type { DevInput } from '../modules/dev';

// The host's status.update messages (Scripts\upkeep.ps1 and dev.ps1 output). -1 = unknown, which the blocks show as --.
const count = (v: unknown) => (Number.isInteger(v) && (v as number) >= -1 ? (v as number) : undefined);

export const upkeepStatus = signal<UpkeepInput>({ mailWhy: 'no host data' });
export const devStatus = signal<DevInput>({});

export function acceptStatusUpdate(m: unknown): void {
  if (typeof m !== 'object' || m === null) return;
  const o = m as Record<string, unknown>;
  if (o.type !== 'status.update') return;
  // mail stays unknown: Gmail needs the DPAPI slice
  if (o.kind === 'upkeep') upkeepStatus.value = { ...upkeepStatus.value, updates: count(o.updates) };
  else if (o.kind === 'dev') devStatus.value = { wsl: count(o.wsl), llm: count(o.llm) };
}
