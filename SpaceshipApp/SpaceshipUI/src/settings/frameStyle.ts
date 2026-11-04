import type { Virtual } from './store';

/** 'fitted' is the picture frame with the HUD laid out to its slots (modules/pictureSlots.ts); 'picture' is the picture as it always was. */
export type FrameStyle = 'rendered' | 'picture' | 'fitted' | 'none';

/** FrameOff wins over UseShipImage, like Frame.ini (every frame layer is hidden when FrameOff=1). */
export function frameStyleOf(values: Record<string, string>): FrameStyle {
  if (values.FrameOff === '1') return 'none';
  if (values.UseShipImage !== '1') return 'rendered';
  return values.PictureFit === '1' ? 'fitted' : 'picture';
}

export function applyFrameStyle(style: FrameStyle): { UseShipImage: string; FrameOff: string; PictureFit: string } {
  const pic = style === 'picture' || style === 'fitted';
  return { UseShipImage: pic ? '1' : '0', FrameOff: style === 'none' ? '1' : '0', PictureFit: style === 'fitted' ? '1' : '0' };
}

/** Store mapping for the virtual `frameStyle` row; the store has already checked the value is one of the select's options. */
export const frameVirtuals: Record<string, Virtual> = {
  frameStyle: { read: frameStyleOf, write: (v) => applyFrameStyle(v as FrameStyle) },
};
