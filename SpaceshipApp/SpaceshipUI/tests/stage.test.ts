import { afterEach, describe, expect, it, vi } from 'vitest';
import { canvasBoxOf, forceFrameBox, frameSignature, FRAME_KEYS, measureStage, refitStage, stageBox } from '../src/ui/stage';

const svgOf = (m: { a: number; e: number; f: number } | null, w = 2560) => ({ viewBox: { baseVal: { width: w } }, getScreenCTM: () => m });
type Fake = { style: { left: string; top: string; width: string } };
const frames: Fake[] = [{ style: { left: '', top: '', width: '' } }];
const docOf = (svg: ReturnType<typeof svgOf> | null) => ({ getElementById: () => svg as unknown as HTMLElement | null, querySelectorAll: () => frames as unknown as NodeListOf<HTMLElement> }) as unknown as Document;

afterEach(() => { stageBox.value = null; vi.useRealTimers(); });

describe('canvasBoxOf', () => {
  it('is the viewBox width through the screen matrix, at the matrix origin', () => {
    expect(canvasBoxOf(svgOf({ a: 0.6668, e: 12, f: 34 }))).toEqual({ left: 12, top: 34, width: 2560 * 0.6668 });
  });
  it('is null when it cannot be measured: no element, no matrix, a zero scale, no viewBox, NaN', () => {
    expect(canvasBoxOf(null)).toBeNull();
    expect(canvasBoxOf(svgOf(null))).toBeNull();
    expect(canvasBoxOf(svgOf({ a: 0, e: 0, f: 0 }))).toBeNull();
    expect(canvasBoxOf(svgOf({ a: 1, e: 0, f: 0 }, 0))).toBeNull();
    expect(canvasBoxOf(svgOf({ a: NaN, e: 0, f: 0 }))).toBeNull();
    expect(canvasBoxOf({ getScreenCTM: () => ({ a: 1, e: 0, f: 0 }) })).toBeNull();
  });
});

describe('measureStage', () => {
  it('publishes the box, ignores sub-quarter-pixel jitter, and follows a real change', () => {
    measureStage(docOf(svgOf({ a: 0.6668, e: 0, f: 0 })));
    const first = stageBox.value!;
    expect(first.width).toBeCloseTo(1707, 0);
    measureStage(docOf(svgOf({ a: 0.6668, e: 0.1, f: 0.1 })));
    expect(stageBox.value).toBe(first); // same object: nothing changed
    measureStage(docOf(svgOf({ a: 0.5, e: 40, f: 10 })));
    expect(stageBox.value).toEqual({ left: 40, top: 10, width: 1280 });
  });
  it('keeps the last good box when the element is missing or unmeasurable', () => {
    measureStage(docOf(svgOf({ a: 0.5, e: 0, f: 0 })));
    const b = stageBox.value;
    measureStage(docOf(null));
    measureStage(docOf(svgOf(null)));
    expect(stageBox.value).toBe(b);
  });
});

describe('refitStage', () => {
  it('measures and sends a window resize on the next frame and after 250 ms, and measures once more after a second', () => {
    vi.useFakeTimers();
    const events: string[] = [];
    let raf: (() => void) | null = null;
    const win = {
      requestAnimationFrame: (cb: () => void) => { raf = cb; return 1; },
      setTimeout: ((cb: () => void, ms: number) => setTimeout(cb, ms)) as unknown as Window['setTimeout'],
      dispatchEvent: (e: Event) => { events.push(e.type); return true; },
    };
    frames[0].style = { left: '0px', top: '0px', width: '2560px' }; // drifted
    refitStage(win as unknown as Window, docOf(svgOf({ a: 0.6668, e: 0, f: 0 })));
    expect(events).toEqual([]);
    raf!();
    expect(events).toEqual(['resize']);
    expect(stageBox.value).not.toBeNull();
    expect(frames[0].style.width).toBe(`${2560 * 0.6668}px`); // forced onto the element
    vi.advanceTimersByTime(250);
    expect(events).toEqual(['resize', 'resize']);
    vi.advanceTimersByTime(800);
    expect(events).toEqual(['resize', 'resize']); // the third pass only measures
  });
});

describe('forceFrameBox', () => {
  it('writes the box onto every .frame element even when its style already says something else', () => {
    const two: Fake[] = [{ style: { left: '9px', top: '9px', width: '9px' } }, { style: { left: '', top: '', width: '' } }];
    forceFrameBox({ querySelectorAll: () => two as unknown as NodeListOf<HTMLElement> } as unknown as Document, { left: 5, top: 6, width: 700 });
    for (const f of two) expect(f.style).toEqual({ left: '5px', top: '6px', width: '700px' });
  });
  it('does nothing before the first measurement', () => {
    const one: Fake[] = [{ style: { left: 'x', top: 'y', width: 'z' } }];
    forceFrameBox({ querySelectorAll: () => one as unknown as NodeListOf<HTMLElement> } as unknown as Document, null);
    expect(one[0].style).toEqual({ left: 'x', top: 'y', width: 'z' });
  });
});

describe('frameSignature: only frame settings count', () => {
  const base = { UseShipImage: '1', FrameOff: '0', PictureFit: '0', Scale: '0.67', ColorAccent: '0,210,255', PerfTier: '0' };
  it('changes for every frame key', () => {
    for (const k of FRAME_KEYS) expect(frameSignature({ ...base, [k]: 'changed' }), k).not.toBe(frameSignature(base));
  });
  it('does not change for other settings (colours, HUD size, the tier, JARVIS, wallpaper ...)', () => {
    for (const k of ['Scale', 'ColorAccent', 'PerfTier', 'WallpaperOn', 'JarvisColorIdle', 'GlowAlpha', 'ReduceMotion', 'BloomEngine', 'LensFx'])
      expect(frameSignature({ ...base, [k]: 'changed' }), k).toBe(frameSignature(base));
  });
});
