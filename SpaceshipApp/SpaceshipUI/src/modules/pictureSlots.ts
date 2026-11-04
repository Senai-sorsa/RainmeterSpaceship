// Picture-frame slots (live test, 2026-11-04). The HUD's zones are laid out for the line-art hull. With the picture frame (ship.png) each zone is
// seated into the picture's own slots: its recessed pockets at the top, and the side windows above the rail at the bottom corners. Numbers are
// canvas units (2560 x 1600), measured on ship.png: stepped top band x 883..1677, y 147..243 split at x 1280 by the centre divider; the side
// window is bounded below by the rail, y = 1261 - 0.307 x (left; the right is its mirror). dx, dy move the zone, s scales it about its centre.
type Slot = { dx?: number; dy?: number; s?: number };

export const PICTURE_SLOTS: Record<string, Slot> = {
  // top: four stat boxes seated in the stepped band, two and two either side of the centre divider (centres y 195)
  G1_cpu: { dx: 186, dy: 18, s: 0.78 }, G2_select: { dx: 50, dy: 18, s: 0.78 },
  G3_select: { dx: -51, dy: 18, s: 0.78 }, G4_ram: { dx: -187, dy: 18, s: 0.78 },
  // sides: both stacks sit in the side windows above the rail (y = 1261 - 0.307 x), identical left and right. dy is measured from each zone's DRAWN centre
  // (its skew moves it), so the left and right rows land on the same heights. Rows scale 0.8 so that all four fit between the hologram and the rail.
  L_category: { s: 0.85 }, R_category: { s: 0.85 },
  L_location: { dy: -54, s: 0.85 }, R_sysinfo: { dy: -54, s: 0.85 },
  L_dots: { dy: -90 }, R_dots: { dy: -90 },
  L_app1: { dy: -119, s: 0.8 }, L_app2: { dy: -152, s: 0.8 }, L_app3: { dy: -184, s: 0.8 }, L_app4: { dy: -216, s: 0.8 },
  R_app1: { dy: -119, s: 0.8 }, R_app2: { dy: -152, s: 0.8 }, R_app3: { dy: -184, s: 0.8 }, R_app4: { dy: -216, s: 0.8 },
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
