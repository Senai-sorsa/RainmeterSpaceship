// Picture-frame slots (live test, 2026-11-04), used only by the "Picture (fitted)" frame. Each entry seats a zone of the HUD into a slot of ship.png.
// Numbers are canvas units (2560 x 1600), measured on the picture: the stepped top band x 883..1677, y 147..243, split at x 1280 by the centre divider.
// dx, dy move the zone (from its DRAWN centre; skew moves it), s scales it about that centre.
// The side stacks are deliberately NOT here: the user wants them where they were (not lifted above the rail). Left and right are already mirrors
// of each other (their drawn centres match row for row), and tests/pictureSlots.test.ts and e2e/picture-slots.spec.ts keep it that way.
type Slot = { dx?: number; dy?: number; s?: number; /** an extra vertical-only scale on top of s (the width stays) */ sy?: number };

export const PICTURE_SLOTS: Record<string, Slot> = {
  // top: one stat box per main slot, at full size, centred in the slot (canvas x 770 / 1092 / 1468 / 1790): the two wing slots, shorter than the pockets so those boxes scale 0.85 to sit under the wing line, under the
  // wing beams and the two centre pockets under the plate (pocket roof at y 143, interior y 150..226). The console (ECO HYBRID ..., CARGO CFG, hz FULL
  // MASTER) drops 37 so its first row sits on the groove at y 103 under the plate; consoleFrame closes the gap between its rows in fitted mode.
  // GPU and NET are the same size (full width, 0.9 tall) and so are CPU and MEMORY (0.85 wide, 0.8 tall); NET sits a little lower than GPU, the rest a little lower than before
  G1_cpu: { dx: -23, dy: 23, s: 0.85, sy: 0.94 }, G2_select: { dx: -26, dy: 15, sy: 0.9 },
  G3_select: { dx: 25, dy: 19, sy: 0.9 }, G4_ram: { dx: 22, dy: 23, s: 0.85, sy: 0.94 },
  // the wing tabs (OROCKET..., SOLIDWORKS...) move away from the centre into the slanted channels near the screen edges (x 20..400 and 2160..2540,
  // falling about 0.2 to the centre); their drawn ink is centred about x 213 and 2347 so the two groups mirror
  L_tabs: { dx: -130, dy: -37 }, R_tabs: { dx: 117, dy: -26 },
  T_settings: { dy: 41 },
  // bottom: the two status strips are seated in the middle of the console band (centre y 1507 at their x); both strips follow the arch with their skew
  B_stripL: { dy: 21 }, B_stripR: { dy: 26 },
};

type SeatZone = { id?: string; x: number; y: number; w: number; h: number; matrix: number[] };

/** The zone with its matrix pre-multiplied by "scale about the zone's drawn centre (s across, s * sy down), then move by dx, dy"; unchanged when it has no slot. */
export function seatInPicture<Z extends SeatZone>(z: Z): Z {
  const slot = z.id ? PICTURE_SLOTS[z.id] : undefined;
  if (!slot || z.matrix.length !== 6) return z;
  const { dx = 0, dy = 0, s = 1, sy = 1 } = slot, sv = s * sy;
  const [a, b, c, d, e, f] = z.matrix;
  const px = z.x + z.w / 2, py = z.y + z.h / 2;
  const cx = a * px + c * py + e, cy = b * px + d * py + f; // where the zone's centre is drawn now
  return { ...z, matrix: [s * a, sv * b, s * c, sv * d, s * e + (1 - s) * cx + dx, sv * f + (1 - sv) * cy + dy] };
}
