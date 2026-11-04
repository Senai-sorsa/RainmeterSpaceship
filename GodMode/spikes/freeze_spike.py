"""Spike: pause a model mid-answer without losing work (freeze/thaw), on a private capped Ollama.
Uses the installed llama3.2:3b. Checks:
 1. a long generation is running when we freeze;
 2. while frozen, the request does not finish and the server's working set drops (RAM handed back);
 3. after thaw, the SAME request completes with a full answer;
 4. RunGuard drives freeze/thaw from (fake) low-RAM samples on the real server.
Kills only its own job. Run: py -3 -I GodMode/spikes/freeze_spike.py"""
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from godmode import memory  # noqa: E402
from godmode.guard import RunGuard  # noqa: E402
from godmode.servers import PrivateOllama  # noqa: E402

MB, G = 1 << 20, memory.GiB


def total_ws(proc):
    return sum(v[0] for v in proc.working_sets().values())


def generate(srv, result, tokens):
    c = srv.client("llama3.2:3b", options={"num_predict": tokens, "num_ctx": 2048, "temperature": 0})
    t0 = time.monotonic()
    r = c.chat([{"role": "user", "content": "Count from 1 to 400, separated by spaces."}], None)
    result.update(text=r["content"], seconds=time.monotonic() - t0, done=time.monotonic())


def main():
    checks = []
    with PrivateOllama(working_set_cap=4 << 30) as srv:
        warm = {}
        generate(srv, warm, 4)                       # load the model first
        res = {}
        th = threading.Thread(target=generate, args=(srv, res, 600), daemon=True)
        th.start()
        time.sleep(1.5)
        running_before = th.is_alive()
        ws_before = total_ws(srv.proc)
        n = srv.proc.freeze()
        time.sleep(4)
        ws_frozen = total_ws(srv.proc)
        still_waiting = th.is_alive() and "text" not in res
        t_thaw = time.monotonic()
        srv.proc.thaw()
        th.join(300)
        print(f"froze {n} processes; working set {ws_before / MB:.0f} MB -> {ws_frozen / MB:.0f} MB while frozen")
        print(f"answer: {len(res.get('text', '').split())} words, finished {res.get('done', 0) - t_thaw:.1f}s after thaw")
        checks.append(("generation was running when frozen", running_before))
        checks.append(("request waits while frozen", still_waiting))
        checks.append(("RAM handed back while frozen (working set at least halved)", ws_frozen < ws_before / 2))
        checks.append(("same request completes after thaw", len(res.get("text", "").split()) > 100))

        # RunGuard on the real server with fake RAM samples: low x3 -> pause, high x5 -> resume
        samples = iter([3.5, 3.5, 3.5] + [8.0] * 5)
        g = RunGuard(srv.proc, memory.Watchdog(),
                     lambda: memory.Snapshot(32 * G, int(next(samples) * G), 0, 0, 12 * G, 0))
        acts = [g.tick() for _ in range(8)]
        checks.append(("RunGuard: pause then resume on the real server", acts.count("pause") == 1
                       and acts.count("resume") == 1 and g.state == "running"))
        res2 = {}
        generate(srv, res2, 8)
        checks.append(("server healthy after guard cycle", bool(res2.get("text"))))
        g.close()
    for name, ok in checks:
        print(("PASS " if ok else "FAIL ") + name)
    return 0 if all(ok for _, ok in checks) else 1


if __name__ == "__main__":
    sys.exit(main())
