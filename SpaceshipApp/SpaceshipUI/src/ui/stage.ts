import { signal } from '@preact/signals';

// The frame must always cover exactly the area the HUD's SVG canvas covers. They used to be sized separately (the frame by CSS viewport units, the canvas by the
// SVG's own fit), so any moment they disagreed (a settings switch, a window or display change) showed as a frame too large or too small against the HUD.
// Now the frame is sized FROM the canvas: measured here, and re-measured and re-fitted (refitStage) after every settings change, the way the first load does it.

export type StageBox = { left: number; top: number; width: number };

/** The box the HUD canvas (the SVG's viewBox, letterboxed by its own fit) covers on screen, in CSS px; null while it cannot be measured. */
export function canvasBoxOf(svg: { viewBox?: { baseVal?: { width: number } }; getScreenCTM?: () => { a: number; e: number; f: number } | null } | null | undefined): StageBox | null {
  const m = svg?.getScreenCTM?.();
  const vbw = svg?.viewBox?.baseVal?.width;
  if (!m || !vbw || !(m.a > 0)) return null;
  const box = { left: m.e, top: m.f, width: vbw * m.a };
  return Number.isFinite(box.left) && Number.isFinite(box.top) && Number.isFinite(box.width) && box.width > 1 ? box : null;
}

/** The settings of the Control Center's Frame group (and the Frame module switch). Only a change to one of these re-fits the stage; other settings pages do not. */
export const FRAME_KEYS = [
  'UseShipImage', 'FrameOff', 'PictureFit', 'ShipImage', 'Off_Frame', 'FrameBrightness', 'HullAlpha', 'FrameBehindTaskbar',
  'GlassTint', 'GlassGlare', 'ScanLines', 'ScanAlpha', 'ShadeAlpha', 'MistAlpha', 'Frame_DX', 'Frame_DY',
] as const;

/** The frame settings as one string, so a change to any of them (and nothing else) is a changed signature. */
export const frameSignature = (values: Record<string, string>) => FRAME_KEYS.map((k) => k + '=' + (values[k] ?? '')).join('|');

/** The latest measured canvas box; the frame follows it. */
export const stageBox = signal<StageBox | null>(null);

const same = (a: StageBox, b: StageBox) => Math.abs(a.left - b.left) < 0.25 && Math.abs(a.top - b.top) < 0.25 && Math.abs(a.width - b.width) < 0.25;

/** Measure the canvas now; the signal changes only when the box moved by a quarter pixel or more. */
export function measureStage(doc: Pick<Document, 'getElementById'> = document): void {
  const box = canvasBoxOf(doc.getElementById('hud') as unknown as Parameters<typeof canvasBoxOf>[0]);
  if (!box) return;
  const cur = stageBox.peek();
  if (cur && same(cur, box)) return;
  stageBox.value = box;
}

/** Write the measured box onto the frame element itself, whatever its inline style says now. The renderer does not rewrite a style it believes is unchanged, so a frame
 *  that drifted on its own (the live symptom: 1.5x too large) would otherwise stay wrong; this is the "force" in refitStage. */
export function forceFrameBox(doc: Pick<Document, 'querySelectorAll'> = document, box: StageBox | null = stageBox.peek()): void {
  if (!box) return;
  doc.querySelectorAll<HTMLElement>('.frame').forEach((el) => {
    el.style.left = `${box.left}px`;
    el.style.top = `${box.top}px`;
    el.style.width = `${box.width}px`;
  });
}

/** Re-run the layout as the first load does after a settings change: measure the canvas, then send a window `resize` (so the fit, the light canvas, the glass and
 *  the click map all redo their measuring), on the next frame, again after 250 ms and once more after a second, for whatever animates meanwhile. */
export function refitStage(win: Pick<Window, 'requestAnimationFrame' | 'setTimeout' | 'dispatchEvent'> = window, doc: Pick<Document, 'getElementById' | 'querySelectorAll'> = document): void {
  const go = () => { measureStage(doc); forceFrameBox(doc); win.dispatchEvent(new Event('resize')); };
  win.requestAnimationFrame(go);
  win.setTimeout(go, 250);
  win.setTimeout(() => { measureStage(doc); forceFrameBox(doc); }, 1000);
}
