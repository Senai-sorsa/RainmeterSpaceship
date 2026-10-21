import { describe, expect, it } from 'vitest';
import { devFrame } from '../src/modules/dev';
import { sysinfoFrame } from '../src/modules/sysinfo';
import { styleFrom } from '../src/modules/style';

const st = styleFrom({});
const zone = { x: 0, y: 0, w: 230, h: 80 };

describe('right column frames', () => {
  it('sysinfo draws with no feeds and with the down and up rates', () => {
    expect(sysinfoFrame({}, zone, st).length).toBeGreaterThan(0);
    expect(sysinfoFrame({ ping: 12, wifi: 80, down: 1250000, up: 125000, lan: '192.168.1.5', wan: '203.0.113.9' }, zone, st).length)
      .toBeGreaterThan(0);
  });

  it('dev draws the diamond and the gear with -- when unknown', () => {
    expect(devFrame({}, zone, st).length).toBeGreaterThan(0);
    expect(devFrame({ wsl: 2, llm: 0 }, zone, st).length).toBeGreaterThan(0);
  });
});
