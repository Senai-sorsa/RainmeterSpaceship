import { signal } from '@preact/signals';

// The apps' own icons that Scripts/app-icons.ps1 extracts into the skin's @Resources/Icons (gitignored, the user's apps):
// id.png is the greyscale icon, id_glow.png its blurred glow. The host serves that folder on its own name and posts the list
// (icons.list); until it does (and always in a browser) the list is empty and every caller falls back to its line icon, as lib.lua does.
const ORIGIN = 'https://icons.spaceship.local/';
const NAME = /^[A-Za-z0-9_.-]{1,70}$/;
const MAX = 4000;

/** The icon file names the host has (without .png), and a version that changes when app-icons.ps1 rewrites them. */
export const iconList = signal<{ names: Set<string>; v: number } | null>(null);

/** Keeps a valid icons.list message; anything else is ignored. */
export function acceptIconsList(m: unknown): void {
  const o = m as Record<string, unknown> | null;
  if (typeof o !== 'object' || o === null || o.type !== 'icons.list' || !Array.isArray(o.ids) || o.ids.length > MAX) return;
  const v = typeof o.v === 'number' && Number.isFinite(o.v) ? o.v : 0;
  iconList.value = { names: new Set(o.ids.filter((n): n is string => typeof n === 'string' && NAME.test(n))), v };
}

/** The icon and glow URLs for an app id, or undefined when app-icons.ps1 made no icon for it (lib.lua H.hasIcon). */
export function appIconUrls(id: string): { icon: string; glow?: string } | undefined {
  const l = iconList.value;
  if (!l || !l.names.has(id)) return undefined;
  const url = (n: string) => `${ORIGIN}${n}.png?v=${l.v}`;
  return { icon: url(id), glow: l.names.has(`${id}_glow`) ? url(`${id}_glow`) : undefined };
}
