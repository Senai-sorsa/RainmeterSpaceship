import { describe, expect, it } from 'vitest';
import inc from '../../../Skins/Spaceship/@Resources/Settings.inc?raw';
import settings from '../src/generated/settings.json';
import { SKIN_DEFAULTS, css, parseColor, themeVars } from '../src/lib/theme';

const v = (settings as { variables: Record<string, string> }).variables;
const incColors = [...inc.matchAll(/^(Color\w+)=(.*)$/gm)].map((m) => [m[1], m[2].trim()] as const);
const FB: [number, number, number, number] = [9, 9, 9, 9];

describe('rainmeter colour strings', () => {
  it('parses r,g,b and r,g,b,a', () => {
    expect(parseColor('0,210,255', FB)).toEqual([0, 210, 255, 255]);
    expect(parseColor('0,30,45,90', FB)).toEqual([0, 30, 45, 90]);
    expect(parseColor(' 1 , 2 , 3 ', FB)).toEqual([1, 2, 3, 255]);
  });
  it('parses hex forms and falls back on garbage', () => {
    expect(parseColor('#00D2FF', FB)).toEqual([0, 210, 255, 255]);
    expect(parseColor('00d2ff80', FB)).toEqual([0, 210, 255, 128]);
    expect(parseColor('', FB)).toBe(FB);
    expect(parseColor(undefined, FB)).toBe(FB);
  });
  it('every Color* line in Settings.inc parses and matches the exported settings', () => {
    expect(incColors.length).toBeGreaterThan(5);
    for (const [k, val] of incColors) {
      if (!/^\d+,\d+,\d+(,\d+)?$|^#?[0-9a-f]{6,8}$/i.test(val)) continue; // Jarvis* colours are empty by design
      expect(parseColor(val, FB), k).not.toBe(FB);
      expect(v[k], k).toBe(val);
      expect(SKIN_DEFAULTS[k], k).toBe(val); // skin defaults == Settings.inc defaults
    }
  });
  it('css() keeps alpha', () => {
    expect(css([0, 30, 45, 90])).toBe('rgb(0 30 45 / 0.3529)');
  });
});

describe('theme css vars', () => {
  it('resolve to the settings values', () => {
    const t = themeVars(v);
    expect(t['--accent']).toBe('rgb(0,210,255)');
    expect(t['--alert']).toBe('rgb(255,60,70)');
    expect(t['--text']).toBe(css(parseColor(v.ColorText, FB)));
    expect(themeVars({ ColorAccent: '1,2,3' })['--accent']).toBe('rgb(1,2,3)'); // a theme change wins
    expect(themeVars({})['--accent']).toBe('rgb(0,210,255)'); // skin default fallback
  });
});
