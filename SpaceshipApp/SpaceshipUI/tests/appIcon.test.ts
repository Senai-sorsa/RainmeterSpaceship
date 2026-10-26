import { describe, expect, it, vi } from 'vitest';
import type { Style } from '../src/draw/canvas';

// The Icons folder is the user's (gitignored), so the lookup is faked: 'chrome' has an icon and a glow, nothing else does.
vi.mock('../src/draw/appIcons', () => ({
  appIconUrls: (id: string) => (id === 'chrome' ? { icon: 'chrome.png', glow: 'chrome_glow.png' } : undefined),
}));
const { Canvas } = await import('../src/draw/canvas');

const st = (tier: number): Style => ({
  s: 2, tier, glowA: 46, glowW: 3.2, coreWhite: 0, hudA: 255, edit: false, textGlow: 4, textGlowA: 150, textSmall: 1.85, textLarge: 1.45,
  fontText: 'Oxanium', fontNum: 'B612 Mono', fontTitle: 'Michroma', white: [255, 255, 255, 255], dim: [0, 110, 150, 255], panel: [0, 30, 45, 90],
  accent: [0, 255, 51, 255], warn: [255, 130, 40, 255], alert: [255, 60, 70, 255], text: [200, 240, 255, 255], hi: [255, 105, 135, 255], good: [60, 255, 170, 255],
});

// expected numbers from lib.lua H.image: ColorMatrix1 = 1-accent, ColorMatrix5 = accent, glow ImageAlpha floor(a * 0.8), 1.25x size
describe('app icon (lib.lua H.image)', () => {
  it('draws the glow under the recoloured icon, centred, in device units', () => {
    const c = new Canvas({ x: 10, y: 0, w: 100, h: 100 }, st(0));
    expect(c.appIcon('chrome', 20, 20, 16)).toBe(true);
    const [glow, icon] = c.flush();
    expect(glow.shape).toMatchObject({ kind: 'image', href: 'chrome_glow.png', x: 40, y: 20, w: 40, h: 40 });
    expect(glow.shape.kind === 'image' && glow.shape.matrix).toEqual([0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0.2, 0, 0, 0, 0, 0, 204 / 255, 0]);
    expect(icon.shape).toMatchObject({ kind: 'image', href: 'chrome.png', x: 44, y: 24, w: 32, h: 32 });
    expect(icon.shape.kind === 'image' && icon.shape.matrix).toEqual([1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0.8, 0, 0, 0, 0.2, 0, 0, 0, 1, 0]);
  });

  it('LOW drops the glow; no icon file draws nothing and says so', () => {
    const c = new Canvas({ x: 0, y: 0, w: 100, h: 100 }, st(2));
    expect(c.appIcon('chrome', 20, 20, 16)).toBe(true);
    expect(c.appIcon('nope', 20, 20, 16)).toBe(false);
    expect(c.flush().map((o) => o.shape.kind === 'image' && o.shape.href)).toEqual(['chrome.png']);
  });
});
