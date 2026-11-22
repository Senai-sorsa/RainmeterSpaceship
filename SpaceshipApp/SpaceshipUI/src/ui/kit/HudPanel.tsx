import type { ComponentChildren } from 'preact';
import { StatusPill, type PillState } from './StatusPill';

type P = { index?: string; title: string; pill?: { state: PillState; text?: string }; children?: ComponentChildren; class?: string; id?: string };

/** Glass panel with corner brackets and a mono header strip ("01 // TITLE" and an optional status pill). */
export function HudPanel({ index, title, pill, children, class: cls = '', id }: P) {
  return (
    <section class={`hp ${cls}`} aria-labelledby={id ? `${id}-h` : undefined} id={id}>
      <header class="hp-head">
        {index && <span class="hp-index">{index} //</span>}
        <h2 class="hp-title" id={id ? `${id}-h` : undefined}>{title}</h2>
        {pill && <StatusPill {...pill} />}
      </header>
      <div class="hp-body">{children}</div>
    </section>
  );
}
