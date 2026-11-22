"""settings_check: validate Settings.inc against the table in jarvislib/config.py (OpenJarvis idea: `jarvis config` checks its file).

Read-only, no model, no network, imports only jarvislib/config.py (pure data), so it is safe to run any time:
    py -3 -B tools/settings_check.py [path to Settings.inc]        exit 0 = nothing wrong, 1 = problems printed

It reports (a) keys that are one typo away from a setting the code reads (the setting would silently do nothing; the HUD's own Jarvis* keys are not in the table and are ignored),
(b) values whose type does not match the code default (a number key holding text, "inf", "nan"), (c) a count of keys left at the default.
Keys that are not Jarvis* (the HUD's own layout keys) are ignored."""
import difflib
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
JARVIS_DIR = os.path.dirname(HERE)
sys.path.insert(0, JARVIS_DIR)
from jarvislib.config import DEFAULTS  # noqa: E402

PREFIXES = ("Jarvis", "PerfTier", "ObsidianTodo")


def read_settings(path):
    raw = open(path, "rb").read()
    text = raw.decode("utf-16") if raw[:2] in (b"\xff\xfe", b"\xfe\xff") else raw.decode("utf-8", errors="ignore")
    out = {}
    for n, line in enumerate(text.splitlines(), 1):
        m = re.match(r"\s*([A-Za-z0-9_]+)\s*=\s*(.*?)\s*$", line)
        if m:
            out[m.group(1)] = (m.group(2), n)
    return out


def number(value):
    try:
        x = float(value)
    except ValueError:
        return None
    return x if math.isfinite(x) else None


def check(path):
    problems, set_count = [], 0
    for key, (value, line) in read_settings(path).items():
        if not key.startswith(PREFIXES):
            continue
        if key not in DEFAULTS:
            near = difflib.get_close_matches(key, DEFAULTS, n=1, cutoff=0.85)
            if near:                                           # the HUD's own Jarvis* keys (colours, orb...) are not in the table: only near-misses are typos
                problems.append(f"line {line}: {key} is not a setting the code reads - did you mean {near[0]}?")
            continue
        if value == "":
            continue
        set_count += 1
        default = DEFAULTS[key]
        looks_numeric = isinstance(default, (int, float)) or (isinstance(default, str) and number(default) is not None)
        if looks_numeric and number(value) is None:
            problems.append(f"line {line}: {key}={value!r} is not a finite number (default {default!r})")
    return problems, set_count


def main(argv):
    path = argv[1] if len(argv) > 1 else os.path.join(os.path.dirname(JARVIS_DIR), "Settings.inc")
    if not os.path.exists(path):
        print(f"no Settings.inc at {path}")
        return 1
    problems, set_count = check(path)
    for p in problems:
        print("PROBLEM", p)
    print(f"{path}: {set_count} Jarvis keys set, {len(DEFAULTS) - set_count} at the code default, {len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
