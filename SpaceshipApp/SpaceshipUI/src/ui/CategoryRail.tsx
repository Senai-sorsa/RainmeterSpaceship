import { CATEGORIES } from '../settings/registry';
import type { CategoryId } from '../settings/types';

export function CategoryRail({ active, onSelect }: { active: CategoryId; onSelect: (id: CategoryId) => void }) {
  return (
    <nav class="rail" aria-label="Settings categories">
      {CATEGORIES.map((c) => (
        <button type="button" class="label rail-btn" aria-current={c.id === active ? 'page' : undefined} onClick={() => onSelect(c.id)}>{c.label}</button>
      ))}
    </nav>
  );
}
