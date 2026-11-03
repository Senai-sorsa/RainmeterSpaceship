"""Shared sandbox for the golden tools (refactor plan phase 0). No product code is changed by importing this.

Safety (CLAUDE-READ-BEFORE-RUNNING-ANYTHING.md): the guards of tools/semi_live.py are installed by importing it (module
level), BEFORE jarvis is imported: subprocess / os.startfile / os.system blocked, ctypes only read-only calls, every
ACTIONS entry and run_action replaced by a tripwire. Settings, Data, persona: a temp folder (sys.argv[1] = temp RES, so the
real Data\\jarvis.log is never written). No model is ever called: chat_stream / chat_json / interpret trip if reached.

Determinism: the clock is frozen (time.time / localtime / strftime) at FIXED (2026-11-03 15:00 local with TZ=ABC+12);
session state (history, last, undo, did, offer, recent, mood) is reset before every item. datetime.now() is NOT frozen;
in the code the golden tools reach it is only used by interpret() (faked)."""
import os
import shutil
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
JARVIS_DIR = os.path.dirname(HERE)
GOLDEN_DIR = os.path.join(JARVIS_DIR, "tests", "golden")
FIXED = 1793761200                                            # 2026-11-03 03:00 UTC = 15:00 at TZ=ABC+12

sys.path.insert(0, HERE)
import semi_live as SL                                         # noqa: E402  installs the guards at import

_lt, _sf = time.localtime, time.strftime


def freeze_clock():
    time.time = lambda: float(FIXED)
    time.localtime = lambda secs=None: _lt(FIXED if secs is None else secs)
    time.strftime = lambda fmt, t=None: _sf(fmt, _lt(FIXED) if t is None else t)


class Everywhere:                                              # same as test_jarvis.py / semi_live.py
    def __init__(self, main):
        object.__setattr__(self, "_main", main)

    def _mods(self):
        return [self._main] + [m for n, m in sorted(sys.modules.items()) if n.startswith("jarvislib.") and m]

    def __getattr__(self, name):
        for m in self._mods():
            if name in vars(m):
                return vars(m)[name]
        raise AttributeError(name)

    def __setattr__(self, name, value):
        mods = self._mods()
        if not any(name in vars(m) for m in mods):
            raise AttributeError(f"golden fakes {name}, which no jarvis module has")
        old = getattr(self, name)
        for m in mods:
            if name in vars(m) and vars(m)[name] is old:
                setattr(m, name, value)


class Box:
    """The sandbox: temp RES, guards, fakes, frozen clock. Use as `with Box() as b:`; b.jarvis, b.j, b.logs."""

    def __init__(self, settings=None):
        if os.environ.get("TZ") != "ABC+12":
            sys.exit("golden tools must run with TZ=ABC+12 (same as the tests)")
        self.settings = dict(settings or {})

    def __enter__(self):
        res = SL.make_res("none", os.path.join(JARVIS_DIR, "persona.txt"), self.settings)
        self.res = res
        data = os.path.join(res, "Data")
        with open(os.path.join(data, "StartApps.txt"), "w", encoding="utf-8") as f:
            f.write("Google Chrome|Chrome\nVisual Studio Code|Code\nSpotify|Spotify\nNotepad|notepad\nSteam|steam\n"
                    "Discord|Discord\nCalculator|calc\nFile Explorer|explorer\n")
        with open(os.path.join(data, "jarvis_mics.txt"), "w", encoding="utf-8") as f:
            f.write("Microphone (Realtek(R) Audio)\nHeadset Microphone (WH-1000XM4)\n")
        sys.argv[1:] = [res]
        sys.path.insert(0, JARVIS_DIR)

        def guarded_remove(path, *a, **k):
            if not SL._inside(path, res) and not SL._inside(path, tempfile.gettempdir()):
                SL.trip("os.remove", path)
            return SL._real_remove(path, *a, **k)

        def guarded_rmtree(path, *a, **k):
            if not SL._inside(path, res) and not SL._inside(path, tempfile.gettempdir()):
                SL.trip("shutil.rmtree", path)
            return SL._real_rmtree(path, *a, **k)

        os.remove, shutil.rmtree = guarded_remove, guarded_rmtree
        freeze_clock()
        import jarvis                                          # noqa: E402  (after the guards, on purpose)
        self.jarvis = jarvis
        j = self.j = Everywhere(jarvis)
        for attr in ("MEMORY_FILE", "REMIND_FILE", "TOPICS_FILE", "GIST_FILE", "DUCK_FILE", "MICS_FILE", "BT_FILE"):
            setattr(j, attr, os.path.join(data, os.path.basename(getattr(j, attr))))
        from jarvislib import prompt as P
        assert SL._inside(P.PERSONA, res) and SL._inside(j.DATA, res), "persona or Data is not the temp copy"

        self.logs = []
        self.model_calls = []

        def no_model(name):
            def f(*a, **k):
                self.model_calls.append(name)
                SL.trip(f"model:{name}")
            return f

        j.run_action = lambda *a, **k: SL.trip("run_action", a[:1])
        for k in list(j.ACTIONS):
            j.ACTIONS[k] = (lambda name: lambda *a, **kw: SL.trip(f"ACTIONS[{name}]"))(k)
        j.chat_stream, j.chat_json = no_model("chat_stream"), no_model("chat_json")
        j.interpret = lambda model, text: self.model_calls.append("interpret")   # understand(): AI reread -> None
        j.speak_all = lambda sentences: SL.trip("speak_all")
        j.filler = lambda key, quiet: None
        j.bt_devices = lambda: [("A1B2C3D4E5F6", "WH-1000XM4", False), ("0A1B2C3D4E5F", "JBL Flip 5", True)]
        j.log = lambda msg: self.logs.append(str(msg))
        assert jarvis.chat_stream.__name__ == "f" and jarvis.log.__name__ == "<lambda>", "a fake is missing"
        assert all(getattr(f, "__name__", "") == "<lambda>" for f in j.ACTIONS.values()), "an ACTIONS entry is real"
        return self

    def reset(self):
        """A fresh session: the same state semi_live.py resets per case."""
        from jarvislib import mood as M, turnstate, hearing
        self.jarvis.history = []
        self.jarvis.last_turn = 0.0
        M.reset()
        M.state["temp"] = None
        for d in (turnstate.offer, turnstate.last):
            d.clear()
        turnstate.recent.update(you="", me="")
        turnstate.undo.clear()
        turnstate.did.clear()
        hearing.heard_score[0] = 0.0
        for f in (self.j.MEMORY_FILE, self.j.REMIND_FILE, self.j.TOPICS_FILE, self.j.GIST_FILE):
            if os.path.exists(f):
                SL._real_remove(f)
        del self.logs[:]

    def set_setting(self, key, value):
        SL.set_setting_file(self.res, key, value)
        import jarvislib.base as B
        B._settings_cache = (0.0, {})

    def __exit__(self, *exc):
        SL._real_rmtree(self.res, ignore_errors=True)
        return False


def norm(obj):
    """repr with memory addresses removed (stable across runs)."""
    import re
    return re.sub(r" at 0x[0-9A-Fa-f]+", " at 0x", repr(obj))


def diff_lines(path, new_lines, check):
    """Write (default) or compare (--check). Returns the process exit code."""
    if not check:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write("".join(l + "\n" for l in new_lines))
        print(f"wrote {len(new_lines)} lines -> {os.path.relpath(path, JARVIS_DIR)}")
        return 0
    with open(path, encoding="utf-8") as f:
        old = f.read().splitlines()
    bad = [(i, a, b) for i, (a, b) in enumerate(zip(old, new_lines)) if a != b]
    if len(old) != len(new_lines):
        print(f"line count differs: golden {len(old)}, now {len(new_lines)}")
    for i, a, b in bad[:20]:
        print(f"line {i + 1}:\n  golden: {a[:300]}\n  now:    {b[:300]}")
    n = len(bad) + abs(len(old) - len(new_lines))
    print(f"{os.path.basename(path)}: {n} diffs over {len(new_lines)} lines")
    return 1 if n else 0
