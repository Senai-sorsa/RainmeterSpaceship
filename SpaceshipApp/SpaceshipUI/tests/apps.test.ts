import { describe, expect, it } from 'vitest';
import { entryOf, loadCatalog, parseIni } from '../src/modules/apps';
import { fakeCatalog } from '../src/modules/appsSource';

const start = [
  { name: 'Google Chrome', id: 'c' },
  { name: 'Uninstall Chrome', id: 'u' },
  { name: 'Notepad', id: 'n' },
];

describe('apps catalog', () => {
  it('parseIni keeps sections in order and skips comments and blank lines', () => {
    const { data, order } = parseIni('; note\n[A]\nk = v\n\n[B]\nx=1=2\n');
    expect(order).toEqual(['A', 'B']);
    expect(data.A.k).toBe('v');
    expect(data.B.x).toBe('1=2');
  });

  it('a Start target resolves by name, and a missing one hides the app', () => {
    const ini = '[App.a]\nName=A\nTarget=start:Google Chrome\n[App.b]\nName=B\nTarget=start:Nope\n[Category.x]\nApps=a,b\n';
    const cat = loadCatalog(ini, start, () => false);
    expect(cat.apps.a.missing).toBe(false);
    expect(cat.apps.b.missing).toBe(true);
    expect(cat.cats.x.apps.map((a) => a.id)).toEqual(['a']);
  });

  it('junk entries (uninstallers) never join the installed list', () => {
    const cat = loadCatalog('', start, () => false);
    expect(cat.cats.all.apps.map((a) => a.name)).toEqual(['Google Chrome', 'Notepad']);
  });

  it('installed apps outside the catalog go to OTHER APPS and auto apps get a line icon', () => {
    const cat = loadCatalog('', start, () => false);
    expect(cat.catOrder).toContain('other');
    expect(cat.cats.other.apps.map((a) => a.name)).toEqual(['Google Chrome', 'Notepad']);
    expect(cat.apps[cat.cats.other.apps[0].id].auto).toBe(true);
  });

  it('a file target resolves through the existence check', () => {
    const ini = '[App.f]\nName=F\nTarget=C:/x/f.exe||C:/y.exe\n';
    const cat = loadCatalog(ini, [], (p) => p === 'C:/y.exe');
    expect(cat.apps.f.target).toEqual({ kind: 'file', value: 'C:/y.exe' });
  });

  it('entryOf prefers a category id, then an app id', () => {
    expect(entryOf(fakeCatalog, 'dev')?.kind).toBe('cat');
    expect(entryOf(fakeCatalog, 'chrome')?.kind).toBe('app');
    expect(entryOf(fakeCatalog, 'nothing')).toBeNull();
  });
});
