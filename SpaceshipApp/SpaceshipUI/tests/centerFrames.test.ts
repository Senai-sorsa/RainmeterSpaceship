import { describe, expect, it } from 'vitest';
import layout from '../src/generated/layout.json';
import { hudFrame, hudState } from '../src/modules/hud';
import { sphereFrame, sphereState } from '../src/modules/sphere';
import { countdown, inside, pickNext, targetFrame, targetMove, targetState, todoLabel } from '../src/modules/target';
import { styleFrom } from '../src/modules/style';

const st = styleFrom({});
const zone = layout.zones.find((z) => z.id === 'C_target')!;
const zoneOf = (id: string) => layout.zones.find((z) => z.id === id)!;

describe('target reticle', () => {
  it('the zone centre is on the glass, the top-left corner is not', () => {
    expect(inside(zone, zone.w / 2, zone.h / 2)).toBe(true);
    expect(inside(zone, 0, 0)).toBe(false);
  });

  it('pickNext returns a spot the reticle fits in, away from where it is', () => {
    const from: [number, number] = [zone.w / 2, zone.h / 2];
    for (const r of [0, 0.25, 0.5, 0.75, 0.999]) {
      const [x, y] = pickNext(zone, from, () => r);
      expect(inside(zone, x, y)).toBe(true);
    }
  });

  it('a roam glides to its destination and then dwells', () => {
    const s = targetState(zone);
    let i = 0;
    while (i < 2000 && s.to === null) { targetMove(s, zone, {}, 1, () => 0.5); i++; }
    expect(s.to).not.toBeNull();
    const dest = s.to!;
    while (i < 2000 && s.to !== null) { targetMove(s, zone, {}, 1, () => 0.5); i++; }
    expect(s.to).toBeNull();
    expect(s.pos).toEqual(dest);
    expect(inside(zone, s.pos[0], s.pos[1])).toBe(true);
  });

  it('a parked reticle does not move', () => {
    const s = targetState(zone);
    const before = [...s.pos];
    for (let i = 0; i < 200; i++) targetMove(s, zone, {}, 0, () => 0.5);
    expect(s.pos).toEqual(before);
  });

  it('draws with and without a CPU or memory figure', () => {
    const s = targetState(zone);
    expect(targetFrame(s, {}, zone, st).length).toBeGreaterThan(0);
    expect(targetFrame(s, { cpu: 40, ram: 512 * 1048576 }, zone, st).length).toBeGreaterThan(0);
  });

  it('to-do mode shows the count, the countdown and the label like target.lua', () => {
    const todos = [{ text: 'call the dentist about the appointment', due: 7200, timed: false }, { text: 'b', due: 9000, timed: true }, { text: 'c', due: null, timed: false }];
    const ops = JSON.stringify(targetFrame(targetState(zone), { todos, todoCount: 5, nowS: 0 }, zone, st));
    expect(ops).toContain('"5"');
    expect(ops).toContain('2H00');
    expect(ops).toContain('CALL THE DENTIST ABOUT TH.');
    expect(JSON.stringify(targetFrame(targetState(zone), { todos: [todos[2]], nowS: 0 }, zone, st))).toContain('NO DUE');
    expect([countdown(-1), countdown(125), countdown(3600 * 5 + 7 * 60), countdown(86400 * 3)]).toEqual(['LATE', '2M', '5H07', '3D']);
    expect(todoLabel({ text: 'x', due: null, timed: false })).toBe('X');
    expect(todoLabel({ text: 'x', due: 0, timed: true })).toMatch(/^X {2}\| {2}[A-Z]{3} \d\d:\d\d$/);
  });
});

describe('sphere and HUD frames', () => {
  it('the sphere draws with no feeds and with a download rate', () => {
    const z = zoneOf('C_sphere');
    expect(sphereFrame(sphereState(), {}, z, st).length).toBeGreaterThan(0);
    expect(sphereFrame(sphereState(), { downBps: 1250000, linkDownMbps: 100 }, z, st).length).toBeGreaterThan(0);
  });

  it('the NET box says TEST until a speed-test figure exists', () => {
    const z = zoneOf('C_sphere');
    expect(JSON.stringify(sphereFrame(sphereState(), {}, z, st))).toContain('TEST');
    expect(JSON.stringify(sphereFrame(sphereState(), { linkDownMbps: 100 }, z, st))).toContain('100 Mbps');
  });

  it('the HUD draws with and without the GPU clock', () => {
    const z = zoneOf('C_hud');
    const a = hudState();
    expect(hudFrame(a, { cpuBaseMHz: 2000, cpuPerf: 100, load: 10 }, z, st).length).toBeGreaterThan(0);
    expect(hudFrame(hudState(), { cpuBaseMHz: 2000, cpuPerf: 100, gpuClockMHz: 1800, load: 10 }, z, st).length).toBeGreaterThan(0);
  });
});
