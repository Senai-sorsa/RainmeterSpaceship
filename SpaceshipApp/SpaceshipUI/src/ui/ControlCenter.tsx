import { useEffect, useState } from 'preact/hooks';
import type { HostBridge } from '../host/HostBridge';
import { CATEGORIES } from '../settings/registry';
import type { SettingsStore } from '../settings/store';
import type { CategoryId, SettingDef } from '../settings/types';
import { CategoryRail } from './CategoryRail';
import { SettingsPanel } from './SettingsPanel';

type P = { store: SettingsStore; host: HostBridge; defs: SettingDef[]; onClose: () => void };
const typing = (t: EventTarget | null) => t instanceof HTMLElement && (t.isContentEditable || /^(INPUT|TEXTAREA|SELECT)$/.test(t.tagName) && (t as HTMLInputElement).type !== 'range');

export function ControlCenter({ store, host, defs, onClose }: P) {
  const [cat, setCat] = useState<CategoryId>(CATEGORIES[0].id);
  const [jump, setJump] = useState<string | null>(null);
  const q = store.query.value;
  const adv = store.level.value === 'advanced';
  const results = q.trim() ? store.search(q).filter((d) => adv || d.level !== 'advanced').slice(0, 30) : [];
  const groups = [...new Set(defs.filter((d) => d.category === cat && (adv || d.level !== 'advanced')).map((d) => d.group))];

  // After the panel re-renders for a clicked result: open its group, then scroll to and focus its primary control.
  useEffect(() => {
    if (!jump) return;
    const el = [...document.querySelectorAll<HTMLElement>('.cc [data-key]')].find((n) => n.dataset.key === jump);
    el?.closest('details')?.setAttribute('open', '');
    el?.scrollIntoView({ block: 'center' });
    el?.querySelector<HTMLElement>('[data-primary]')?.focus();
    setJump(null);
  }, [jump]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') { if (store.query.value) store.query.value = ''; else onClose(); e.preventDefault(); return; }
      if (e.key === '/' && !typing(e.target)) { e.preventDefault(); document.querySelector<HTMLInputElement>('.cc-search')?.focus(); return; }
      if (!e.ctrlKey || typing(e.target)) return; // inside a text field Ctrl+Z stays the browser's own
      const k = e.key.toLowerCase();
      if (k === 'z' && !e.shiftKey) { store.undo(); e.preventDefault(); }
      else if (k === 'y' || (k === 'z' && e.shiftKey)) { store.redo(); e.preventDefault(); }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [store, onClose]);

  const pick = (d: SettingDef) => { setCat(d.category); store.query.value = ''; setJump(d.key); };
  const label = (id: string) => CATEGORIES.find((c) => c.id === id)?.label ?? id;

  return (
    <div class="cc" role="dialog" aria-label="Control Center">
      <header class="cc-head">
        <span class="label cc-title">Control Center</span>
        <input class="ctl-text cc-search" type="search" placeholder="Search settings ( / )" aria-label="Search settings" value={q}
          onInput={(e) => { store.query.value = (e.target as HTMLInputElement).value; }} />
        <button type="button" class="ctl-action cc-btn" aria-label="Undo" disabled={!store.canUndo.value} onClick={() => store.undo()}>Undo</button>
        <button type="button" class="ctl-action cc-btn" aria-label="Redo" disabled={!store.canRedo.value} onClick={() => store.redo()}>Redo</button>
        <span class="label cc-level">Advanced
          <button type="button" class="ctl-switch" role="switch" aria-checked={adv} aria-label="Advanced settings"
            onClick={() => { store.level.value = adv ? 'normal' : 'advanced'; }}><i /></button>
        </span>
        <button type="button" class="ctl-action cc-btn" aria-label="Close Control Center" onClick={onClose}>Close</button>
      </header>
      <div class="cc-body">
        <CategoryRail active={cat} onSelect={(id) => { setCat(id); store.query.value = ''; }} />
        <div class="cc-pane">
          {q.trim() ? (
            <ul class="cc-results" aria-label="Search results">
              {results.map((d) => (
                <li><button type="button" class="rail-btn" onClick={() => pick(d)}>
                  <span class="label">{d.label}</span> <small>{label(d.category)} / {d.group}</small>
                </button></li>
              ))}
              {results.length === 0 && <li class="label empty">No settings match.</li>}
            </ul>
          ) : (
            <>
              <div class="cc-resets">
                {groups.map((g) => <button type="button" class="ctl-action cc-btn" aria-label={`Reset group ${g}`} onClick={() => store.resetGroup(cat, g)}>Reset {g}</button>)}
              </div>
              <SettingsPanel store={store} host={host} defs={defs} categories={[cat]} mode="center" />
            </>
          )}
        </div>
      </div>
    </div>
  );
}
