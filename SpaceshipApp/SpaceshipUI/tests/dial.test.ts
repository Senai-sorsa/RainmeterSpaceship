import { describe, expect, it } from 'vitest';
import { dialFrame } from '../src/modules/dial';
import { styleFrom } from '../src/modules/style';
import type { Op } from '../src/draw/canvas';

const st = styleFrom({});
const zone = { x: 0, y: 0, w: 189, h: 165 };
const texts = (ops: Op[]) => ops.flatMap((o) => (o.shape.kind === 'text' ? [o.shape.text] : []));

describe('systems dial', () => {
  it('draws with no sensor data and for every selected control', () => {
    for (let sel = 1; sel <= 6; sel++) expect(dialFrame({}, zone, st, sel).length).toBeGreaterThan(0);
  });

  it('shows the unavailable text when a sensor is missing', () => {
    expect(texts(dialFrame({}, zone, st, 1))).toContain('NO PANEL CONTROL');
    expect(texts(dialFrame({}, zone, st, 4))).toContain('NEEDS LEGION TOOLKIT');
    expect(texts(dialFrame({}, zone, st, 3))).toContain('NO DATA');
    expect(texts(dialFrame({}, zone, st, 2))).toContain('0%');
  });

  it('reads a power mode and refresh rate into the stepped labels', () => {
    expect(texts(dialFrame({ power: 'Performance' }, zone, st, 4))).toContain('PERFORM');
    expect(texts(dialFrame({ refresh: '165 Hz' }, zone, st, 5))).toContain('165 HZ');
  });

  it('shows MUTED for a muted mic, and a percentage for brightness', () => {
    expect(texts(dialFrame({ mic: 40, micMuted: true }, zone, st, 3))).toContain('MUTED');
    expect(texts(dialFrame({ bright: 70 }, zone, st, 1))).toContain('70%');
  });
});
