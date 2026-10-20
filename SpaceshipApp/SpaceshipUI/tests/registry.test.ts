import { describe, expect, it } from 'vitest';
import { INTERNAL_KEYS, REGISTRY, CATEGORIES, WRITABLE_INTERNAL, allowedKeys } from '../src/settings/registry';
import { moduleDefs } from '../src/settings/dynamic';
import settings from '../src/generated/settings.json';
import layoutJson from '../src/generated/layout.json';

const vars = (settings as { variables: Record<string, string> }).variables;
const layout = layoutJson as unknown as { zones: { id: string; content?: string }[] };
const mods = moduleDefs(layout);

describe('settings registry', () => {
  it('every Settings.inc key is registered or internal', () => {
    const reg = new Set(REGISTRY.map((d) => d.key));
    expect(Object.keys(vars).filter((k) => !reg.has(k) && !INTERNAL_KEYS.has(k))).toEqual([]);
  });
  it('every registry key exists in Settings.inc or is optional/virtual', () => {
    expect(REGISTRY.filter((d) => !(d.key in vars) && !d.optional && !d.virtual).map((d) => d.key)).toEqual([]);
  });
  it('defaults equal Settings.inc values for present keys', () => {
    const bad = REGISTRY.filter((d) => d.key in vars && !d.virtual && d.default.trim() !== vars[d.key].trim());
    expect(bad.map((d) => `${d.key}: ${d.default} != ${vars[d.key]}`)).toEqual([]);
  });
  it('keys are unique and categories valid', () => {
    const keys = [...REGISTRY, ...mods].map((d) => d.key);
    expect(keys.length).toBe(new Set(keys).size);
    const ids = new Set(CATEGORIES.map((c) => c.id));
    expect(REGISTRY.filter((d) => !ids.has(d.category)).map((d) => d.key)).toEqual([]);
  });
  it('slider bounds valid (min<max, step>0, default within)', () => {
    for (const d of [...REGISTRY, ...mods]) {
      const c = d.control;
      if (c.kind !== 'slider') continue;
      const n = Number(d.default);
      expect([d.key, c.min < c.max && c.step > 0 && n >= c.min && n <= c.max]).toEqual([d.key, true]);
    }
  });
  it('select default is an option', () => {
    for (const d of REGISTRY) if (d.control.kind === 'select') expect([d.key, d.control.options.some((o) => o.value === d.default)]).toEqual([d.key, true]);
  });
  it('JarvisName default is Jarvis', () => {
    const j = REGISTRY.find((d) => d.key === 'JarvisName');
    expect(j?.default).toBe('Jarvis');
    expect(j?.optional).toBe(true);
    expect(REGISTRY.find((d) => d.key === 'AssistantLabel')?.default).toBe('');
  });
  it('dynamic defs cover every zone', () => {
    for (const z of layout.zones) {
      const k = z.id as string;
      for (const key of [`Off_${k}`, `CT_${k}`, `${k}_DX`, `${k}_DY`]) expect(mods.some((d) => d.key === key)).toBe(true);
    }
    expect(mods.filter((d) => d.file === 'Offsets.inc').length).toBe(layout.zones.length * 2);
  });
  it('allowedKeys excludes virtual, includes modules and writable internals', () => {
    const a = allowedKeys(layout);
    expect(a.has('frameStyle')).toBe(false);
    expect(a.has('Scale') && a.has('UseShipImage') && a.has('FrameOff') && a.has(mods[0].key)).toBe(true);
    expect(a.has('MasterPrev')).toBe(false);
    expect(WRITABLE_INTERNAL).toEqual(['UseShipImage', 'FrameOff']);
  });
});
