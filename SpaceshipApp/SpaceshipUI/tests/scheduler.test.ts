import { describe, expect, it } from 'vitest';
import { createScheduler } from '../src/host/scheduler';

// A frame source the test steps by hand: each step runs the frames queued so far at the given time.
function fakeFrames() {
  let queue: ((t: number) => void)[] = [];
  return {
    frame: (cb: (t: number) => void) => { queue.push(cb); },
    step(t: number) {
      const q = queue;
      queue = [];
      for (const cb of q) cb(t);
    },
    pending: () => queue.length,
  };
}

describe('scheduler', () => {
  it('runs a job at its own period, not on every frame', () => {
    const f = fakeFrames();
    const s = createScheduler(f.frame, () => 0);
    let calls = 0;
    s.every(50, () => { calls += 1; });
    for (const t of [16, 33, 50, 66, 83, 100]) f.step(t);
    expect(calls).toBe(2);
  });

  it('stops calling a job once it is cancelled, and stops the loop when none is left', () => {
    const f = fakeFrames();
    const s = createScheduler(f.frame, () => 0);
    let calls = 0;
    const stop = s.every(10, () => { calls += 1; });
    f.step(10);
    stop();
    f.step(20);
    expect(calls).toBe(1);
    expect(f.pending()).toBe(0);
  });

  it('a job stopped by an earlier job in the same frame does not run', () => {
    const f = fakeFrames();
    const s = createScheduler(f.frame, () => 0);
    let second = 0;
    let stopSecond = () => {};
    s.every(10, () => stopSecond());
    stopSecond = s.every(10, () => { second += 1; });
    f.step(10);
    expect(second).toBe(0);
  });

  it.each([60, 144, 165])('keeps each job at its own rate on a %i Hz screen', (hz) => {
    const f = fakeFrames();
    const s = createScheduler(f.frame, () => 0);
    const counts = new Map<number, number>();
    for (const ms of [16, 33, 50]) s.every(ms, () => counts.set(ms, (counts.get(ms) ?? 0) + 1));
    for (let i = 1; i <= hz * 10; i++) f.step((i * 1000) / hz);
    for (const ms of [16, 33, 50]) {
      const want = Math.min(1000 / ms, hz); // a job can run at most once per frame
      expect(Math.abs(counts.get(ms)! / 10 - want) / want).toBeLessThan(0.03);
    }
  });

  it('a gap with no frames fires the job once, not once per missed period', () => {
    const f = fakeFrames();
    let now = 0;
    const s = createScheduler(f.frame, () => now);
    let calls = 0;
    s.every(33, () => { calls += 1; });
    now = 500; // the page was hidden for 500 ms; no frames ran
    f.step(500);
    expect(calls).toBe(1);
  });
});
