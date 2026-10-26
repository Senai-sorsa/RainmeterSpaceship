// One loop for the page's timers. Each job runs at its own period, like setInterval, and the loop stops when no job is
// left. It sleeps until the next job is due (not every vsync, like Rainmeter's Update=), then lines up with a frame.
// The browser sends no frames to a hidden page, so nothing runs while it is hidden; pause() covers a page the host
// reports as covered by a fullscreen window (still shown, nothing to see).

export type Frame = (cb: (t: number) => void, waitMs: number) => unknown;
export type Scheduler = { every(ms: number, fn: () => void): () => void; pause(on: boolean): void };

const PAUSED_POLL_MS = 500;

/** The clock and frame source are passed in so the tests can run without a window. */
export function createScheduler(frame: Frame, clock: () => number): Scheduler {
  type Job = { ms: number; fn: () => void; last: number };
  const jobs = new Set<Job>();
  let pending = false;
  let paused = false;
  const arm = () => {
    if (!jobs.size || pending) return;
    pending = true;
    const now = clock();
    let wait = paused ? PAUSED_POLL_MS : Infinity;
    if (!paused) for (const j of jobs) wait = Math.min(wait, j.last + j.ms - now);
    frame(tick, Math.max(0, wait));
  };
  const tick = (t: number) => {
    pending = false;
    if (!paused) for (const j of [...jobs]) {
      if (!jobs.has(j)) continue; // stopped by an earlier job in this frame
      if (t - j.last >= j.ms) {
        j.last = t - ((t - j.last) % j.ms); // keep the part past the period, or the rate drops to fit frame edges
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
    pause(on) {
      if (paused === on) return;
      paused = on;
      if (!on) for (const j of jobs) j.last = clock() - j.ms; // run everything once on wake-up
    },
  };
}

// a frame is about 4-16 ms; waking that much early and then waiting for the frame keeps the period without a busy loop
export const scheduler = createScheduler(
  (cb, wait) => (wait > 16 ? setTimeout(() => requestAnimationFrame(cb), wait - 8) : requestAnimationFrame(cb)),
  () => performance.now(),
);
