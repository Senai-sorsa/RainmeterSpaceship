import guide from '../generated/guide.json';

type Section = { id: string; title: string; level: number; text: string };

/** One section of the HUD guide. Text only: the guide is rendered as plain text nodes, never as HTML. */
export function HelpPanel({ sectionId, onClose }: { sectionId: string; onClose: () => void }) {
  const s = (guide.sections as Section[]).find((x) => x.id === sectionId);
  return (
    <aside class="help" role="dialog" aria-label="Help" data-section={sectionId}>
      <header class="help-head">
        <span class="label help-title">{s?.title ?? 'Help'}</span>
        <button type="button" class="ctl-action cc-btn" aria-label="Close help" onClick={onClose}>Close</button>
      </header>
      <div class="help-body">
        {s ? s.text.split('\n').filter(Boolean).map((p) => <p>{p}</p>) : <p class="label empty">No guide section for this setting.</p>}
      </div>
    </aside>
  );
}
