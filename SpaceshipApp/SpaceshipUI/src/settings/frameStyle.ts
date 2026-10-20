import type { Virtual } from './store';

export type FrameStyle = 'rendered' | 'picture' | 'none';

/** FrameOff wins over UseShipImage, like Frame.ini (every frame layer is hidden when FrameOff=1). */
export function frameStyleOf(values: Record<string, string>): FrameStyle {
  return values.FrameOff === '1' ? 'none' : values.UseShipImage === '1' ? 'picture' : 'rendered';
}

export function applyFrameStyle(style: FrameStyle): { UseShipImage: string; FrameOff: string } {
  return { UseShipImage: style === 'picture' ? '1' : '0', FrameOff: style === 'none' ? '1' : '0' };
}

/** Store mapping for the virtual `frameStyle` row; the store has already checked the value is one of the select's options. */
export const frameVirtuals: Record<string, Virtual> = {
  frameStyle: { read: frameStyleOf, write: (v) => applyFrameStyle(v as FrameStyle) },
};
