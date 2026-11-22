// Port of the catalog part of Skins/Spaceship/@Resources/Scripts/apps.lua: Apps.ini parsing, the categories, the
// installed-app list (Start menu entries that are not junk) and what each slot shows. Launching is not ported: it is
// an OS action and goes through the action gate. The file check and the Start-menu list are passed in (the host
// does not supply them yet).
// %ENV% in file targets is expanded by the host (AppsFeed.cs), which sends back the target text of each one that exists.

export type Target = { kind: 'start'; value: string; label: string } | { kind: 'file' | 'cmd'; value: string };
export type App = {
  id: string; name: string; short: string; icon: string; info: string; proc: string;
  target: Target | null; missing: boolean; auto?: boolean;
};
export type Cat = { id: string; name: string; short: string; icon: string; apps: App[] };
export type Catalog = { apps: Record<string, App>; cats: Record<string, Cat>; catOrder: string[]; layout: Record<string, string> };
export type StartApp = { name: string; id: string };
export type Entry = { kind: 'app'; app: App } | { kind: 'cat'; cat: Cat };

const trim = (s: string) => s.trim();

/** Apps.ini into sections of key=value, plus the section order. Comments (;) and blank lines are skipped. */
export function parseIni(text: string): { data: Record<string, Record<string, string>>; order: string[] } {
  const data: Record<string, Record<string, string>> = {}, order: string[] = [];
  let sec: string | null = null;
  for (const raw of text.replace(/^﻿/, '').split(/\r?\n/)) {
    const line = trim(raw);
    if (line === '' || line.startsWith(';')) continue;
    const head = line.match(/^\[(.+)\]$/);
    if (head) {
      sec = head[1];
      if (!data[sec]) { data[sec] = {}; order.push(sec); }
    } else if (sec) {
      const kv = line.match(/^([^=]+)=(.*)$/);
      if (kv) data[sec][trim(kv[1])] = trim(kv[2]);
    }
  }
  return { data, order };
}

const JUNK = ['uninstall', 'readme', 'read me', 'help', 'documentation', 'website', 'release notes', 'license',
  'manual', 'changelog', "what's new", 'support', 'faq', 'troubleshoot', 'repair'];

// a line icon guessed from the name, for apps that are not in the catalog (apps.lua GUESS, in order)
const GUESS: [string, string][] = [['code', 'code'], ['terminal', 'terminal'], ['shell', 'terminal'], ['python', 'code'],
  ['java', 'code'], ['git', 'git'], ['docker', 'box'], ['camera', 'camera'], ['photo', 'camera'], ['video', 'film'],
  ['player', 'film'], ['music', 'music'], ['audio', 'music'], ['sound', 'music'], ['mail', 'mail'], ['calendar', 'note'],
  ['note', 'note'], ['word', 'pen'], ['excel', 'matrix'], ['powerpoint', 'window'], ['pdf', 'pdf'], ['zip', 'archive'],
  ['drive', 'cloud'], ['cloud', 'cloud'], ['game', 'game'], ['steam', 'game'], ['xbox', 'game'], ['chat', 'chat'],
  ['team', 'chat'], ['monitor', 'gauge'], ['disk', 'disk'], ['usb', 'usb'], ['nvidia', 'gpu'], ['amd', 'gpu'],
  ['lenovo', 'gear'], ['settings', 'gear'], ['paint', 'palette'], ['map', 'map'], ['browser', 'globe'], ['edge', 'globe'],
  ['firefox', 'globe'], ['store', 'box'], ['clock', 'gauge'], ['calculator', 'matrix']];

const guessIcon = (lname: string) => GUESS.find(([k]) => lname.includes(k))?.[1] ?? 'window';

/** The first Start-menu entry that matches: exact, then starts-with, then contains; the shortest name wins. */
function findStart(start: StartApp[], q: string): StartApp | undefined {
  const lq = q.toLowerCase();
  const exact = start.find((e) => e.name.toLowerCase() === lq);
  if (exact) return exact;
  const byLen = (a: StartApp, b: StartApp) => a.name.length - b.name.length;
  const starts = start.filter((e) => e.name.toLowerCase().startsWith(lq)).sort(byLen)[0];
  return starts ?? start.filter((e) => e.name.toLowerCase().includes(lq)).sort(byLen)[0];
}

/** The first target that resolves wins. Targets are split on ||. */
function resolve(targets: string | undefined, start: StartApp[], exists: (p: string) => boolean): Target | null {
  for (const part of (targets ?? '').split('||')) {
    const t = trim(part);
    if (t === '') continue;
    if (t.startsWith('start:')) {
      const e = findStart(start, trim(t.slice(6)));
      if (e) return { kind: 'start', value: e.id, label: e.name };
    } else if (t.startsWith('cmd:')) {
      return { kind: 'cmd', value: trim(t.slice(4)) };
    } else if (exists(t)) {
      return { kind: 'file', value: t };
    }
  }
  return null;
}

/** Builds the catalog from Apps.ini text, the Start-menu list and a file-existence check. */
export function loadCatalog(ini: string, start: StartApp[], exists: (p: string) => boolean): Catalog {
  const { data, order } = parseIni(ini);
  const layout = data.Layout ?? {};
  const hideMissing = (layout.HideMissing ?? '1') !== '0';
  const apps: Record<string, App> = {};
  for (const sec of order) {
    const id = sec.match(/^App\.(.+)$/)?.[1];
    if (!id) continue;
    const kv = data[sec];
    const target = resolve(kv.Target, start, exists);
    apps[id] = {
      id, name: kv.Name ?? id, short: (kv.Short ?? kv.Name ?? id).toUpperCase(), icon: kv.Icon ?? 'gear',
      info: kv.Info ?? '', proc: kv.Proc ?? '', target, missing: target === null,
    };
  }
  const cats: Record<string, Cat> = {}, catOrder: string[] = [];
  for (const sec of order) {
    const id = sec.match(/^Category\.(.+)$/)?.[1];
    if (!id) continue;
    const kv = data[sec];
    const list: App[] = [];
    for (const a of (kv.Apps ?? '').split(',').map(trim)) {
      const app = apps[a];
      if (app && !(hideMissing && app.missing)) list.push(app);
    }
    cats[id] = { id, name: kv.Name ?? id, short: (kv.Short ?? kv.Name ?? id).toUpperCase(), icon: kv.Icon ?? 'box', apps: list };
    catOrder.push(id);
  }
  addInstalled(apps, cats, catOrder, start);
  return { apps, cats, catOrder, layout };
}

/** Every installed app joins the catalog: catalog apps keep their folders, the rest go to OTHER APPS, ALL lists A-Z. */
function addInstalled(apps: Record<string, App>, cats: Record<string, Cat>, catOrder: string[], start: StartApp[]) {
  const claimed = new Map<string, App>();
  for (const app of Object.values(apps)) if (app.target?.kind === 'start') claimed.set(app.target.value, app);
  const used = new Set<string>(), all: App[] = [], other: App[] = [];
  for (const e of start) {
    const lname = e.name.toLowerCase();
    if (JUNK.some((j) => lname.includes(j)) || used.has(e.id)) continue;
    used.add(e.id);
    let app = claimed.get(e.id);
    if (!app) {
      const base = 's_' + lname.replace(/[^a-z0-9]/g, '').slice(0, 40);
      let sid = base, n = 2;
      while (apps[sid]) sid = base + n++;
      app = {
        id: sid, name: e.name, short: (e.name.split(/\s+/)[0] || e.name).toUpperCase().slice(0, 10), icon: guessIcon(lname),
        info: '', proc: '', target: { kind: 'start', value: e.id, label: e.name }, missing: false, auto: true,
      };
      apps[sid] = app;
      other.push(app);
    }
    all.push(app);
  }
  // catalog apps found by file path (not in the Start menu) are installed too
  for (const app of Object.values(apps)) if (app.target && app.target.kind === 'file') all.push(app);
  const byName = (a: App, b: App) => (a.name.toLowerCase() < b.name.toLowerCase() ? -1 : a.name.toLowerCase() > b.name.toLowerCase() ? 1 : 0);
  all.sort(byName); other.sort(byName);
  cats.all = { id: 'all', name: 'ALL INSTALLED APPS', short: 'ALL', icon: 'search', apps: all };
  if (other.length > 0) {
    cats.other = { id: 'other', name: 'OTHER APPS', short: 'OTHER', icon: 'box', apps: other };
    catOrder.push('other');
  }
}

/** What a slot shows: a single app, or a category (the id is looked up as a category first). */
export function entryOf(cat: Catalog, id: string): Entry | null {
  if (cat.cats[id]) return { kind: 'cat', cat: cat.cats[id] };
  if (cat.apps[id]) return { kind: 'app', app: cat.apps[id] };
  return null;
}
