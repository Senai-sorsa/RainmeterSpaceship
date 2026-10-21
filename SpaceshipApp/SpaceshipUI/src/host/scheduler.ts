// One requestAnimationFrame loop for the page's timers. Each job runs at its own period, like setInterval, and the loop
// stops when no job is left. The browser sends no frames to a hidden page, so nothing runs while it is hidden.

export type Frame = (cb: (t: number) => void) => unknown;
export type Scheduler = { every(ms: number, fn: () => void): () => void };

/** The clock and frame source are passed in so the tests can run without a window. */
export function createScheduler(frame: Frame, clock: () => number): Scheduler {
  type Job = { ms: number; fn: () => void; last: number };
  const jobs = new Set<Job>();
  let pending = false;
  const arm = () => {
    if (jobs.size && !pending) {
      pending = true;
      frame(tick);
    }
  };
  const tick = (t: number) => {
    pending = false;
    for (const j of [...jobs]) {
      if (!jobs.has(j)) continue; // stopped by an earlier job in this frame
      if (t - j.last >= j.ms) {
        j.last = t;
        j.fn();
      }
    }
    arm();
  };
  return {
    every(ms, fn) {
      const job: Job = { ms, fn, last: clock() };
      jobs.add(job);
      arm();
      return () => { jobs.delete(job); };
    },
  };
}

export const scheduler = createScheduler((cb) => requestAnimationFrame(cb), () => performance.now());
