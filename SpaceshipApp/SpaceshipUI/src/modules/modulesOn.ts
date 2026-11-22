/** Reads ?module=: one name, a comma list, or "all". Returns a test for each module name. */
export function modulesOn(param: string | null): (name: string) => boolean {
  const names = new Set((param ?? '').split(',').map((s) => s.trim().toLowerCase()).filter(Boolean));
  return (name) => names.has('all') || names.has(name);
}
