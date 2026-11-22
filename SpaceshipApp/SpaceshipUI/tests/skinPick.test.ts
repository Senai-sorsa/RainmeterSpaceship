import { describe, expect, it } from 'vitest';
import { loadCatalog } from '../src/modules/apps';
import { selIndex, skinPick } from '../src/modules/category';

const INI = '[Layout]\nTop1=dev\nTop2=fun\n[App.a]\nName=A\nTarget=C:\\a.exe\n[App.b]\nName=B\nTarget=C:\\b.exe\n[App.c]\nName=C\nTarget=C:\\c.exe\n'
  + '[Category.dev]\nName=DEV\nApps=a,b\n[Category.fun]\nName=FUN\nApps=c\n';
const cat = loadCatalog(INI, [], () => true);

describe('skinPick (category.lua Initialize)', () => {
  it('opens on Layout Top<n> and the first app without saved state', () => {
    expect(skinPick(cat, 1, {})).toEqual({ ci: cat.catOrder.indexOf('dev'), ai: 0 });
    expect(skinPick(cat, 2, {})).toEqual({ ci: cat.catOrder.indexOf('fun'), ai: 0 });
  });
  it('uses TopCat<n> and Sel_<cat> when they are valid, and falls back when they are not', () => {
    expect(skinPick(cat, 2, { TopCat2: 'dev', Sel_dev: '2' })).toEqual({ ci: cat.catOrder.indexOf('dev'), ai: 1 });
    expect(skinPick(cat, 1, { TopCat1: 'gone', Sel_dev: '9' })).toEqual({ ci: cat.catOrder.indexOf('dev'), ai: 0 });
    expect(skinPick(cat, 1, { Sel_dev: 'x' })).toEqual({ ci: cat.catOrder.indexOf('dev'), ai: 0 });
  });
  it('selIndex gives a folder row its saved pick for LAST x', () => {
    expect(selIndex(cat.cats.dev, { Sel_dev: '2' })).toBe(1);
    expect(selIndex(cat.cats.dev, { Sel_dev: '3' })).toBe(0);
    expect(selIndex(undefined, {})).toBe(0);
  });
});
