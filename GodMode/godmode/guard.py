"""Mid-generation memory guard (handoff gap: "watchdog only acts between model calls").

A thread samples RAM every 2 s while a model server runs:
  pause  -> proc.freeze(): suspend the server's processes (the generation keeps its state) and give its RAM
            back to Windows. The HTTP request simply waits.
  resume -> proc.thaw(): it continues exactly where it stopped. No work is lost.
  stop   -> proc.kill(): free RAM fell to the critical floor; the job's checkpoint survives.
Pure decision logic is memory.Watchdog; this file only wires it to a Proc."""
import threading
import time


class RunGuard:
    def __init__(self, proc, watchdog, snapshot, interval=2.0, on_change=None, clock=time.monotonic):
        self.proc, self.wd, self.snapshot = proc, watchdog, snapshot
        self.interval, self.on_change, self.clock = interval, on_change, clock
        self.state = "running"          # running | frozen | killed
        self.events = []                # (time, action) for the audit / UI
        self._stop = threading.Event()
        self._thread = None

    def tick(self):
        """One sample. Returns the action taken (none | pause | resume | stop)."""
        a = self.wd.step(self.snapshot())
        if a == "pause" and self.state == "running":
            self.proc.freeze()
            self.state = "frozen"
        elif a == "resume" and self.state == "frozen":
            self.proc.thaw()
            self.state = "running"
        elif a == "stop" and self.state != "killed":
            self.proc.kill()
            self.state = "killed"
        else:
            return "none"
        self.events.append((round(self.clock(), 1), a))
        if self.on_change:
            self.on_change(a, self.state)
        return a

    def start(self):
        def loop():
            while not self._stop.wait(self.interval):
                try:
                    if self.tick() == "stop":
                        break
                except OSError:
                    continue
        self._thread = threading.Thread(target=loop, daemon=True)
        self._thread.start()
        return self

    def close(self):
        self._stop.set()
        if self.state == "frozen":       # never leave a server frozen behind us
            self.proc.thaw()
            self.state = "running"
        if self._thread:
            self._thread.join(5)
