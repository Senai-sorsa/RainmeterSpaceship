// Picture-frame slots (live test, 2026-11-04), used only by the "Picture (fitted)" frame. Each entry seats a zone of the HUD into a slot of ship.png.
// Numbers are canvas units (2560 x 1600), measured on the picture: the stepped top band x 883..1677, y 147..243, split at x 1280 by the centre divider.
// dx, dy move the zone (from its DRAWN centre; skew moves it), s scales it about that centre.
// The side stacks are deliberately NOT here: the user wants them where they were (not lifted above the rail). Left and right are already mirrors
// of each other (their drawn centres match row for row), and tests/pictureSlots.test.ts and e2e/picture-slots.spec.ts keep it that way.
type Slot = { dx?: number; dy?: number; s?: number };

export const PICTURE_SLOTS: Record<string, Slot> = {
  // top: four stat boxes seated in the stepped band, two and two either side of the centre divider (centres y 195)
  G1_cpu: { dx: 186, dy: 18, s: 0.78 }, G2_select: { dx: 50, dy: 18, s: 0.78 },
  G3_select: { dx: -51, dy: 18, s: 0.78 }, G4_ram: { dx: -187, dy: 18, s: 0.78 },
};

type SeatZone = { id?: string; x: number; y: number; w: number; h: number; matrix: number[] };

/** The zone with its matrix pre-multiplied by "scale s about the zone's drawn centre, then move by dx, dy"; unchanged when it has no slot. */
export function seatInPicture<Z extends SeatZone>(z: Z): Z {
  const slot = z.id ? PICTURE_SLOTS[z.id] : undefined;
  if (!slot || z.matrix.length !== 6) return z;
  const { dx = 0, dy = 0, s = 1 } = slot;
  const [a, b, c, d, e, f] = z.matrix;
  const px = z.x + z.w / 2, py = z.y + z.h / 2;
  const cx = a * px + c * py + e, cy = b * px + d * py + f; // where the zone's centre is drawn now
  return { ...z, matrix: [s * a, s * b, s * c, s * d, s * e + (1 - s) * cx + dx, s * f + (1 - s) * cy + dy] };
}
