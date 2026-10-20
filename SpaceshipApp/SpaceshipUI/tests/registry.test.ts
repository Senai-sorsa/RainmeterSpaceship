import { describe, expect, it } from 'vitest';
import { INTERNAL_KEYS, REGISTRY, CATEGORIES, WRITABLE_INTERNAL, allowedKeys } from '../src/settings/registry';
import { moduleDefs } from '../src/settings/dynamic';
import settings from '../src/generated/settings.json';
import modulesJson from '../src/generated/modules.json';

const vars = (settings as { variables: Record<string, string> }).variables;
const modules = modulesJson as { keys: string[] };
const mods = moduleDefs(modules);

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
  it('dynamic defs cover every real module key', () => {
    expect(modules.keys.length).toBeGreaterThan(0);
    for (const k of modules.keys) {
      for (const [key, file] of [[`Off_${k}`, 'State.inc'], [`CT_${k}`, 'State.inc'], [`${k}_DX`, 'Offsets.inc'], [`${k}_DY`, 'Offsets.inc']]) {
        expect([key, mods.find((d) => d.key === key)?.file]).toEqual([key, file]);
      }
    }
    expect(mods.length).toBe(modules.keys.length * 4);
    expect(mods.some((d) => d.key.includes('T_power'))).toBe(false);
  });
  it('text control defaults match their own pattern and max', () => {
    for (const d of REGISTRY) {
      const c = d.control;
      if (c.kind !== 'text') continue;
      expect([d.key, new RegExp(c.pattern).test(d.default) && d.default.length <= c.max]).toEqual([d.key, true]);
    }
  });
  it('allowedKeys excludes virtual, includes modules and writable internals', () => {
    const a = allowedKeys(modules);
    expect(a.has('frameStyle')).toBe(false);
    expect(a.has('Scale') && a.has('UseShipImage') && a.has('FrameOff') && a.has(mods[0].key)).toBe(true);
    expect(a.has(`Off_${modules.keys[0]}`)).toBe(true);
    expect(a.has('Off_T_power')).toBe(false);
    expect(a.has('MasterPrev')).toBe(false);
    expect(WRITABLE_INTERNAL).toEqual(['UseShipImage', 'FrameOff']);
  });
});
