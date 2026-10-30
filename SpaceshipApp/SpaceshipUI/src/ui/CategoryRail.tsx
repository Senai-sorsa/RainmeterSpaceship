import { CATEGORIES } from '../settings/registry';
import type { CategoryId } from '../settings/types';

export function CategoryRail({ active, onSelect }: { active: CategoryId; onSelect: (id: CategoryId) => void }) {
  return (
    <nav class="rail" aria-label="Settings categories">
      {CATEGORIES.map((c, n) => (
        <button type="button" class="label rail-btn" aria-current={c.id === active ? 'page' : undefined} onClick={() => onSelect(c.id)}><span class="rail-n" aria-hidden="true">{String(n + 1).padStart(2, '0')}</span>{c.label}</button>
      ))}
    </nav>
  );
}
