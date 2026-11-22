import { describe, expect, it } from 'vitest';
import { acceptAppsCatalog, catalogFeed, catalogFrom, fakeCatalog } from '../src/modules/appsSource';

const INI = '[Layout]\nTop1=dev\n[App.a]\nName=A\nTarget=C:\\a.exe\n[App.b]\nName=B\nTarget=C:\\b.exe\n[Category.dev]\nName=DEV\nApps=a,b\n';

describe('apps.catalog from the host', () => {
  it('builds the catalog with only the file targets the host says exist', () => {
    const c = catalogFrom({ type: 'apps.catalog', ini: INI, start: [['X', 'x.id'], 'junk'], exists: ['C:\\a.exe'] })!;
    expect(c.layout.Top1).toBe('dev');
    expect(c.apps.a.target).toEqual({ kind: 'file', value: 'C:\\a.exe' });
    expect(c.apps.b?.target ?? null).toBeNull();
  });

  it('ignores other and malformed messages, keeping the sample', () => {
    expect(catalogFrom({ type: 'apps.catalog', ini: 1, start: [], exists: [] })).toBeNull();
    acceptAppsCatalog({ type: 'system.metrics' });
    expect(catalogFeed.value).toBe(fakeCatalog);
  });
});
