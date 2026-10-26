// The apps' own icons that Scripts/app-icons.ps1 extracts into the skin's @Resources/Icons (gitignored, the user's apps):
// id.png is the greyscale icon, id_glow.png its blurred glow. URLs only; the browser fetches the ones on screen.
// A fresh clone has no Icons folder, so the map is empty and every caller falls back to its line icon, as lib.lua does.
const files = import.meta.glob('../../../../Skins/Spaceship/@Resources/Icons/*.png', { eager: true, query: '?url', import: 'default' }) as Record<string, string>;
const byName = new Map(Object.entries(files).map(([p, url]) => [p.slice(p.lastIndexOf('/') + 1, -4), url]));

/** The icon and glow URLs for an app id, or undefined when app-icons.ps1 made no icon for it (lib.lua H.hasIcon). */
export function appIconUrls(id: string): { icon: string; glow?: string } | undefined {
  const icon = byName.get(id);
  return icon ? { icon, glow: byName.get(`${id}_glow`) } : undefined;
}
