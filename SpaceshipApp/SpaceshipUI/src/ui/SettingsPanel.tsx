import type { HostBridge } from '../host/HostBridge';
import type { SettingsStore } from '../settings/store';
import type { CategoryId, SettingDef } from '../settings/types';
import { CATEGORIES } from '../settings/registry';
import { GroupSection } from './GroupSection';
import { SettingRow } from './SettingRow';

type P = {
  store: SettingsStore;
  host: HostBridge;
  defs: SettingDef[]; // wizard mode lists from these (the store only exposes level-filtered defs)
  categories: CategoryId[];
  mode: 'center' | 'wizard';
  only?: (d: SettingDef) => boolean;
  onHelp?: (key: string) => void;
};

function Groups({ list, p }: { list: SettingDef[]; p: P }) {
  const order = new Map<string, SettingDef[]>();
  for (const d of list) { const id = `${d.category}/${d.group}`; order.set(id, [...(order.get(id) ?? []), d]); }
  return <>{[...order].map(([id, ds]) => (
    <GroupSection key={id} id={id} title={id.split('/')[1]}>
      {ds.map((d) => <SettingRow key={d.key} def={d} store={p.store} host={p.host} onHelp={p.onHelp} />)}
    </GroupSection>
  ))}</>;
}

/** ArrowUp/Down move focus between rows' primary controls (sliders and selects keep native arrow behaviour). */
function onKeyDown(e: KeyboardEvent) {
  if (e.key !== 'ArrowUp' && e.key !== 'ArrowDown') return;
  const t = e.target as HTMLElement;
  if (t.closest('[data-native-arrows]') || !t.hasAttribute('data-primary')) return;
  const all = [...e.currentTarget instanceof HTMLElement ? e.currentTarget.querySelectorAll<HTMLElement>('[data-primary]') : []].filter((n) => n.offsetParent !== null);
  const next = all[all.indexOf(t) + (e.key === 'ArrowDown' ? 1 : -1)];
  if (next) { e.preventDefault(); next.focus(); }
}

export function SettingsPanel(p: P) {
  const cats = new Set<string>(p.categories);
  const pass = (d: SettingDef) => cats.has(d.category) && (!p.only || p.only(d));
  const wizard = p.mode === 'wizard';
  const main = wizard ? p.defs.filter((d) => pass(d) && d.level !== 'advanced') : p.store.visibleDefs().filter(pass);
  const adv = wizard ? p.defs.filter((d) => pass(d) && d.level === 'advanced') : [];
  const known = CATEGORIES.map((c) => c.id as string);
  main.sort((a, b) => known.indexOf(a.category) - known.indexOf(b.category)); // stable: keeps registry order inside a category
  return (
    <div class="panel" data-mode={p.mode} onKeyDown={onKeyDown}>
      <Groups list={main} p={p} />
      {adv.length > 0 && <GroupSection id="wizard/Advanced" title="Advanced" attr="data-advanced" defaultOpen={false}><Groups list={adv} p={p} /></GroupSection>}
      {main.length === 0 && adv.length === 0 && <p class="label empty">No settings match.</p>}
    </div>
  );
}
