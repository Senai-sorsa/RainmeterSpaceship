// Picture-frame slots (live test, 2026-11-04), used only by the "Picture (fitted)" frame. Each entry seats a zone of the HUD into a slot of ship.png.
// Numbers are canvas units (2560 x 1600), measured on the picture: the stepped top band x 883..1677, y 147..243, split at x 1280 by the centre divider.
// dx, dy move the zone (from its DRAWN centre; skew moves it), s scales it about that centre.
// The side stacks are deliberately NOT here: the user wants them where they were (not lifted above the rail). Left and right are already mirrors
// of each other (their drawn centres match row for row), and tests/pictureSlots.test.ts and e2e/picture-slots.spec.ts keep it that way.
type Slot = { dx?: number; dy?: number; s?: number };

export const PICTURE_SLOTS: Record<string, Slot> = {
  // top: one stat box per main slot, at full size, centred in the slot (canvas x 770 / 1092 / 1468 / 1790): the two wing slots, shorter than the pockets so those boxes scale 0.85 to sit under the wing line, under the
  // wing beams and the two centre pockets under the plate (pocket roof at y 143, interior y 150..226). The console (ECO HYBRID ..., CARGO CFG, hz FULL
  // MASTER) drops 37 so its first row sits on the groove at y 103 under the plate; consoleFrame closes the gap between its rows in fitted mode.
  G1_cpu: { dx: -23, dy: 19, s: 0.85 }, G2_select: { dx: -26, dy: 11 }, G3_select: { dx: 25, dy: 11 }, G4_ram: { dx: 22, dy: 19, s: 0.85 },
  T_settings: { dy: 37 },
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
