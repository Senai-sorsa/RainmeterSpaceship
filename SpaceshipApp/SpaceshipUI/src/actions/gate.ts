// Named-action gate (plan section 5, decision 3). Every operating-system change goes through here: the action must be on
// the list, its arguments must match the list's rules, a change waits for a confirm from the user, and the result is the
// real exit code. Model output never reaches this gate: it is refused by source before anything else is checked.

export type ArgRule = { kind: 'enum'; values: readonly string[] } | { kind: 'int'; min: number; max: number };
export type ActionDef = { args: Record<string, ArgRule>; confirm: boolean };
export type Args = Record<string, string | number>;
export type Source = 'user' | 'model';
export type Runner = (action: string, args: Args) => Promise<{ exitCode: number }>;

export type Outcome =
  | { kind: 'refused'; reason: string }
  | { kind: 'pending'; id: number }
  | { kind: 'ran'; ok: boolean; exitCode: number }
  | { kind: 'error'; reason: string };

type Pending = { action: string; args: Args; at: number };

/** Returns why the value breaks its rule, or null when it is fine. */
function checkArg(rule: ArgRule, v: unknown): string | null {
  if (rule.kind === 'enum') return typeof v === 'string' && rule.values.includes(v) ? null : `must be one of ${rule.values.join(', ')}`;
  return Number.isInteger(v) && (v as number) >= rule.min && (v as number) <= rule.max ? null : `must be a whole number from ${rule.min} to ${rule.max}`;
}

export class ActionGate {
  private nextId = 1;
  private pending = new Map<number, Pending>();

  constructor(
    private readonly defs: Record<string, ActionDef>,
    private readonly run: Runner,
    private readonly now: () => number = Date.now,
    private readonly confirmMs = 5000,
  ) {}

  /** A user request. A change returns pending until confirm(id) is called; a read-only action runs at once. */
  async request(action: string, args: Args, source: Source): Promise<Outcome> {
    if (source !== 'user') return { kind: 'refused', reason: 'model output cannot trigger an action' };
    const def = this.defs[action];
    if (!def) return { kind: 'refused', reason: `${action} is not on the action list` };
    const keys = Object.keys(def.args);
    const extra = Object.keys(args).filter((k) => !keys.includes(k));
    if (extra.length) return { kind: 'refused', reason: `unknown argument ${extra[0]}` };
    for (const k of keys) {
      if (!(k in args)) return { kind: 'refused', reason: `missing argument ${k}` };
      const why = checkArg(def.args[k], args[k]);
      if (why) return { kind: 'refused', reason: `${k} ${why}` };
    }
    if (def.confirm) {
      const id = this.nextId++;
      this.pending.set(id, { action, args: { ...args }, at: this.now() });
      return { kind: 'pending', id };
    }
    return this.execute(action, args);
  }

  /** The user's yes for a pending change. An unknown or expired id runs nothing. */
  async confirm(id: number): Promise<Outcome> {
    const p = this.pending.get(id);
    this.pending.delete(id);
    if (!p) return { kind: 'refused', reason: 'no such pending action' };
    if (this.now() - p.at > this.confirmMs) return { kind: 'refused', reason: 'confirmation expired' };
    return this.execute(p.action, p.args);
  }

  cancel(id: number): boolean {
    return this.pending.delete(id);
  }

  private async execute(action: string, args: Args): Promise<Outcome> {
    try {
      const { exitCode } = await this.run(action, args);
      return { kind: 'ran', ok: exitCode === 0, exitCode };
    } catch (e) {
      return { kind: 'error', reason: e instanceof Error ? e.message : String(e) };
    }
  }
}
