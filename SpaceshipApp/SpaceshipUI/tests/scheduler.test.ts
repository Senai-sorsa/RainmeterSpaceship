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
