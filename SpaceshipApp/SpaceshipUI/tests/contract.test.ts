import { readFileSync, writeFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';
import modules from '../src/generated/modules.json';
import { allowedKeys, REGISTRY } from '../src/settings/registry';
import { moduleDefs } from '../src/settings/dynamic';
import { messageProblem } from '../src/host/contract';

const GOLDEN = new URL('../../../contract/config-keys.json', import.meta.url);
const FIXTURES = new URL('../../../contract/fixtures/ui-to-host.json', import.meta.url);

/** What the C# host may write: every real (non-virtual, non-action) key with its file and control. Generated from the registry; the C# and Python sides read this same file. */
function derive() {
  const defs = [...REGISTRY, ...moduleDefs(modules)];
  const allowed = allowedKeys(modules);
  const keys = defs.filter((d) => allowed.has(d.key) && d.control.kind !== 'action')
    .map((d) => ({ key: d.key, file: d.file, control: d.control, default: d.default }))
    .sort((a, b) => a.key.localeCompare(b.key));
  const actions = [...new Set(REGISTRY.flatMap((d) => (d.control.kind === 'action' ? [d.control.id] : [])))].sort();
  return { schema: 1, generator: 'SpaceshipApp/SpaceshipUI/tests/contract.test.ts (UPDATE_CONTRACT=1)', keys, actions };
}

describe('contract', () => {
  it('config-keys.json matches the registry (UPDATE_CONTRACT=1 regenerates it)', () => {
    const want = JSON.stringify(derive(), null, 2) + '\n';
    if (process.env.UPDATE_CONTRACT === '1') writeFileSync(GOLDEN, want);
    expect(readFileSync(GOLDEN, 'utf8')).toBe(want);
  });
  it('every UI-to-host fixture gets the verdict it declares', () => {
    const fx = JSON.parse(readFileSync(FIXTURES, 'utf8')) as { name: string; valid: boolean; msg: unknown }[];
    expect(fx.length).toBeGreaterThan(20);
    expect(fx.map((f) => [f.name, messageProblem(f.msg) === null])).toEqual(fx.map((f) => [f.name, f.valid]));
  });
});
