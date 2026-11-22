"""log_stats: timings and route mix from jarvis.log (OpenJarvis idea: `jarvis telemetry stats`; CLAUDE.md section 4 wants a measured baseline).

Read-only. The log holds counts, route names and seconds only (never your words), so this prints nothing personal.
    py -3 -B tools/log_stats.py [path to jarvis.log] [--json]
Reads the file and its .old sibling. Prints n / p50 / p95 / max for each timing line and how often each route kind and result happened."""
import json
import os
import re
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_LOG = os.path.join(os.path.dirname(os.path.dirname(HERE)), "Data", "jarvis.log")
TIMINGS = (("click -> listening", r"timing: click -> listening ([\d.]+)s"),
           ("listening -> end of speech", r"timing: listening -> end of speech ([\d.]+)s"),
           ("end of speech -> text", r"timing: end of speech -> text ([\d.]+)s"),
           ("end of speech -> reply start", r"timing: end of speech -> reply start ([\d.]+)s"),
           ("end of speech -> reply done", r"timing: end of speech -> reply done ([\d.]+)s"),
           ("reply start -> first audio", r"timing: reply start -> first audio ([\d.]+)s"),
           ("alarm due -> ring", r"timing: due -> ring ([\d.]+)s"),
           ("turn total (route line)", r"route: .*total ([\d.]+)s"))
ROUTE = re.compile(r"route: (?:(\w+)\.)?(\w+)(?: (\w+))? via ([\w-]+), total [\d.]+s -> (.+)$")


def pct(values, p):
    s = sorted(values)
    return s[min(len(s) - 1, int(round(p / 100 * (len(s) - 1))))]


def read_lines(path):
    out = []
    for p in (path + ".old", path):
        if os.path.exists(p):
            with open(p, encoding="utf-8", errors="replace") as f:
                out += f.read().splitlines()
    return out


def stats(lines):
    res = {"timings": {}, "routes": Counter(), "results": Counter(), "vias": Counter(), "events": Counter()}
    for name, rx in TIMINGS:
        vals = [float(m.group(1)) for m in (re.search(rx, l) for l in lines) if m]
        if vals:
            res["timings"][name] = {"n": len(vals), "p50": pct(vals, 50), "p95": pct(vals, 95), "max": max(vals)}
    for l in lines:
        m = ROUTE.search(l)
        if m:
            res["routes"][".".join(x for x in (m.group(1), m.group(2), m.group(3)) if x)] += 1
            res["vias"][m.group(4)] += 1
            res["results"][m.group(5)] += 1
        for key in ("turn failed", "watchdog", "turn ignored", "transcript: no words", "pardon:", "player:", "voice gaps", "ear:", "autocorrect"):
            if key in l:
                res["events"][key] += 1
    return res


def main(argv):
    args = [a for a in argv[1:] if not a.startswith("--")]
    path = args[0] if args else DEFAULT_LOG
    lines = read_lines(path)
    if not lines:
        print(f"no log lines at {path}")
        return 1
    res = stats(lines)
    if "--json" in argv:
        print(json.dumps({k: (dict(v) if isinstance(v, Counter) else v) for k, v in res.items()}, indent=1))
        return 0
    print(f"{path}: {len(lines)} lines")
    for name, s in res["timings"].items():
        print(f"  {name:32} n={s['n']:4}  p50 {s['p50']:6.2f}s  p95 {s['p95']:6.2f}s  max {s['max']:6.2f}s")
    for title, key in (("routes", "routes"), ("answered by", "vias"), ("results", "results"), ("events", "events")):
        print(f"{title}: " + ", ".join(f"{k} x{v}" for k, v in res[key].most_common(12)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
