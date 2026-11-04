"""Semi-live test: the REAL model and the real prompt and routing, but no microphone, no speakers and no Windows actions.
Each case is typed in as if Whisper heard it perfectly; every reply, route and requested action is recorded.

Run from the JARVIS venv (Ollama must be running):
    python -B tools/semi_live.py --model llama3.1:8b --cases tools/semi_live_cases.jsonl --out semi-live-results/run.jsonl

Safety (CLAUDE-READ-BEFORE-RUNNING-ANYTHING.md): the fakes and the guards are installed BEFORE jarvis is imported.
  - subprocess, os.startfile, os.system: blocked (raise and are recorded as a tripwire).
  - ctypes.windll / ctypes.WinDLL: only a list of read-only calls passes; anything else (lock, sleep, recycle bin,
    key presses, monitor off) raises and is recorded as a tripwire.
  - run_action and every ACTIONS entry: recorders that never act.
  - Data, Settings.inc, persona, memory, reminders, topics: a temp folder. The real ones are never read or written.
  - No profile or vault is read: a made-up profile and to-do note in the temp folder are used instead.
A run that finds one fake missing stops before the first case."""
import argparse
import builtins
import ctypes
import json
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile
import time

for _s in (sys.stdout, sys.stderr):                            # a reply with "→" or an emoji must not crash the print
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
HERE = os.path.dirname(os.path.abspath(__file__))
JARVIS_DIR = os.path.dirname(HERE)

# ------------------------------------------------------------------ guards (before anything of jarvis is imported)
TRIPS = []                                                     # what was blocked: (what, detail)
READ_ONLY = {"kernel32": {"GetSystemTimes", "GlobalMemoryStatusEx", "GetSystemPowerStatus", "GetLogicalDrives",
                          "GetDriveTypeW", "GetLastError", "CreateFileW", "CloseHandle", "WaitNamedPipeW",
                          "GetCurrentProcessId", "GetDiskFreeSpaceExW", "GetTickCount64", "QueryPerformanceCounter"},
             "user32": {"FindWindowW", "GetAsyncKeyState", "GetForegroundWindow", "GetWindowTextW", "GetSystemMetrics"},
             "ole32": {"CoInitialize", "CoInitializeEx", "CoUninitialize"},
             "shell32": {"SHGetFolderPathW"}}


class Tripwire(Exception):
    pass


def trip(what, detail=""):
    TRIPS.append((what, str(detail)[:120]))
    raise Tripwire(f"semi-live blocked {what} {detail}")


class _Dll:
    def __init__(self, name, real_get):
        self._name, self._get = name.lower().replace(".dll", ""), real_get

    def __getattr__(self, fn):
        if fn.startswith("_"):
            raise AttributeError(fn)
        if fn in READ_ONLY.get(self._name, ()):
            return getattr(self._get(), fn)
        return lambda *a, **k: trip(f"{self._name}.{fn}")


class _Windll:
    def __init__(self, real):
        self._real = real

    def __getattr__(self, name):
        if name.startswith("_"):
            raise AttributeError(name)
        return _Dll(name, lambda: getattr(self._real, name))


_real_windll, _real_WinDLL = ctypes.windll, ctypes.WinDLL
ctypes.windll = _Windll(_real_windll)


def _guard_WinDLL(name, *a, **k):
    base = os.path.basename(str(name)).lower().replace(".dll", "")
    if base not in READ_ONLY:
        return _Dll(base, lambda: None)                        # every call on it trips
    real = _real_WinDLL(name, *a, **k)
    return _Dll(base, lambda: real)


ctypes.WinDLL = _guard_WinDLL
for _fn in ("run", "Popen", "call", "check_call", "check_output"):
    setattr(subprocess, _fn, (lambda n: lambda *a, **k: trip(f"subprocess.{n}", a[0] if a else ""))(_fn))
os.startfile = lambda *a, **k: trip("os.startfile", a[0] if a else "")
os.system = lambda *a, **k: trip("os.system", a[0] if a else "")
_real_rmtree, _real_remove = shutil.rmtree, os.remove


def _inside(path, root):
    return os.path.abspath(str(path)).lower().startswith(os.path.abspath(root).lower() + os.sep)


# ------------------------------------------------------------------ the temp @Resources folder
def make_res(model, persona_path, settings_extra):
    res = tempfile.mkdtemp(prefix="semi-live-")
    data = os.path.join(res, "Data")
    os.makedirs(os.path.join(res, "Jarvis"))
    os.makedirs(data)
    shutil.copy(persona_path, os.path.join(res, "Jarvis", "persona.txt"))
    shutil.copy(os.path.join(JARVIS_DIR, "pronounce.txt"), os.path.join(res, "Jarvis", "pronounce.txt"))
    now = int(time.time())
    todo = os.path.join(res, "todo.md")
    with open(todo, "w", encoding="utf-8") as f:
        f.write("- [ ] Finish the physics lab report\n- [ ] Email Professor Lim about the exam\n- [x] Buy groceries\n"
                "- [ ] Renew the parking permit\n")
    profile = os.path.join(res, "about-me.md")
    with open(profile, "w", encoding="utf-8") as f:
        f.write("I'm an aerospace engineering student. I like rockets, flight sims and coding. I usually study late.\n")
    settings = {"JarvisModel": model, "JarvisModelFast": "", "JarvisContext": "2048", "JarvisKeepAlive": "10",
                "JarvisCallMe": "Mr. Sorsa", "JarvisPersonality": "mirror", "JarvisWakeWord": "0", "JarvisFollowUp": "1",
                "JarvisProfile": profile, "ObsidianTodo": todo, "PerfTier": "0"}
    settings.update(settings_extra)
    with open(os.path.join(res, "Settings.inc"), "w", encoding="utf-8") as f:
        f.write("[Variables]\n" + "".join(f"{k}={v}\n" for k, v in settings.items()))
    fixtures = {
        "calendar.txt": f"C 3\nE {now + 3 * 3600}|{now + 4 * 3600}|0||Physics quiz\n"
                        f"E {now + 26 * 3600}|{now + 27 * 3600}|0|Zoom|Study group\n"
                        f"E {now + 50 * 3600}|{now + 52 * 3600}|0||POLS 207 exam\n",
        "mail.txt": "UNREAD 4\n",
        "windows.txt": "W chrome.exe\nW Code.exe\nW Spotify.exe\nW explorer.exe\n",
        "net.txt": "DOWN 5200000\nUP 900000\n",
    }
    for name, text in fixtures.items():
        with open(os.path.join(data, name), "w", encoding="utf-8") as f:
            f.write(text)
    return res


def set_setting_file(res, key, value):
    path = os.path.join(res, "Settings.inc")
    with open(path, encoding="utf-8") as f:
        lines = [l for l in f.read().splitlines() if not l.startswith(key + "=")]
    lines.append(f"{key}={value}")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


# ------------------------------------------------------------------ the run
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--cases", default=os.path.join(HERE, "semi_live_cases.jsonl"))
    ap.add_argument("--persona", default=os.path.join(JARVIS_DIR, "persona.txt"))
    ap.add_argument("--opts", default="{}", help='extra Ollama options, e.g. {"repeat_penalty": 1.1}')
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--repeat", type=int, default=1)
    ap.add_argument("--only", default="", help="comma list of tags or ids")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    extra_opts = json.loads(args.opts)
    res = make_res(args.model, args.persona, {})
    sys.argv[1:] = [res]
    sys.path.insert(0, JARVIS_DIR)

    def guarded_remove(path, *a, **k):
        if not _inside(path, res) and not _inside(path, tempfile.gettempdir()):
            trip("os.remove", path)
        return _real_remove(path, *a, **k)

    def guarded_rmtree(path, *a, **k):
        if not _inside(path, res) and not _inside(path, tempfile.gettempdir()):
            trip("shutil.rmtree", path)
        return _real_rmtree(path, *a, **k)

    os.remove, shutil.rmtree = guarded_remove, guarded_rmtree

    import jarvis                                              # noqa: E402  (after the guards, on purpose)
    from jarvislib import mood as M, llm, turnstate, hearing, mic as micmod, prompt as P, session

    class Everywhere:                                          # same as test_jarvis.py: a fake reaches every module
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
                raise AttributeError(f"semi-live fakes {name}, which no jarvis module has")
            old = getattr(self, name)
            for m in mods:
                if name in vars(m) and vars(m)[name] is old:
                    setattr(m, name, value)

    j = Everywhere(jarvis)

    # where everything is written: the temp folder only
    for attr in ("MEMORY_FILE", "REMIND_FILE", "TOPICS_FILE", "GIST_FILE", "DUCK_FILE", "MICS_FILE"):
        setattr(j, attr, os.path.join(res, "Data", os.path.basename(getattr(j, attr))))
    assert _inside(P.PERSONA, res) and _inside(j.DATA, res), "persona or Data is not the temp copy"

    # what he says and does is recorded, never played or run
    T = {"lines": [], "spoken": [], "actions": [], "logs": [], "first": None, "t0": 0.0, "prompts": []}

    def fake_action(action, target, pending=None):
        row = j.ACTION_TABLE.get(action)
        if row and row.risk == "ask" and pending != (action, target):
            return False
        T["actions"].append([action, str(target)[:80]])
        turnstate.did.append((time.time(), turnstate.DID.get(action, action), True))
        return True

    j.run_action = fake_action
    for k in list(j.ACTIONS):
        j.ACTIONS[k] = (lambda name: lambda *a, **kw: trip(f"ACTIONS[{name}]"))(k)

    def fake_speak(sentences):
        out = []
        for s in sentences:
            if T["first"] is None:
                T["first"] = time.time() - T["t0"]
            out.append(s)
        T["spoken"].append(out)
        return out

    def fake_text_only(sentences, collected):
        fake_speak(sentences)

    def fake_reply_line(text, quiet):
        turnstate.recent["me"] = text
        T["lines"].append(text)
        jarvis.convo_add("J", text)

    real_stream = llm.chat_stream

    def stream(model, messages, temperature=0.5):
        T["prompts"].append(len(messages[0]["content"]))
        return real_stream(model, messages, temperature)

    def opts_with_seed():
        o = {"num_ctx": llm.ctx_tokens(), "seed": args.seed}
        o.update(extra_opts)
        return o

    def fake_set_setting(name, value=""):
        if name == "mood":
            set_setting_file(res, "JarvisPersonality", value)
            import jarvislib.base as B
            B._settings_cache = (0.0, {})
        T["actions"].append(["set_setting", f"{name} {value}"])

    real_turn_mood = M.turn_mood

    def turn_mood(text, base, counted=True):                   # the mood this turn really had (serious topic, timed)
        T["mood"] = real_turn_mood(text, base, counted)
        return T["mood"]

    M.turn_mood = turn_mood
    j.speak_all, j.say_text_only, j.reply_line = fake_speak, fake_text_only, fake_reply_line
    j.filler = lambda key, quiet: None
    j.filler_done = lambda: None
    j.prepare_fillers = lambda: None
    j.chime = lambda: 0.0
    j.muted = lambda: False
    j.speakers = lambda mute=None, volume=None: (False, 40)
    j.mic_volume = lambda mute=None, volume=None: (False, 80)
    j.screen_brightness = lambda percent=None: 60
    j.theme_mode = lambda mode=None: "dark"
    j.gpu = lambda: True
    j.sensors = lambda: "CPU load: 18%\nGPU load: 9%\nGPU temperature: 52 C\nPending: no alarms, reminders or timers"
    j.diagnose = lambda topic, span=None, own_cpu=False: ("", [])
    j.set_setting = fake_set_setting
    j.load_options = opts_with_seed
    j.chat_stream = stream
    j.start_apps = lambda: [("Google Chrome", "Chrome"), ("Visual Studio Code", "Code"), ("Spotify", "Spotify"),
                            ("Notepad", "notepad"), ("Steam", "steam"), ("Discord", "Discord")]
    j.rainmeter_running = lambda: True
    keep_log = jarvis.log
    j.log = lambda msg: T["logs"].append(str(msg))

    # the checks of rule 1: each fake is the one installed
    assert jarvis.run_action is fake_action and jarvis.speak_all is fake_speak and jarvis.reply_line is fake_reply_line
    assert all(getattr(f, "__name__", "") == "<lambda>" for f in j.ACTIONS.values()), "an ACTIONS entry is real"
    assert isinstance(ctypes.windll, _Windll) and subprocess.run.__name__ == "<lambda>", "a guard is missing"

    cases = [json.loads(l) for l in open(args.cases, encoding="utf-8") if l.strip() and not l.startswith("//")]
    if args.only:
        want = set(args.only.split(","))
        cases = [c for c in cases if c["id"] in want or want & set(c.get("tags", []))]
    if args.limit:
        cases = cases[:args.limit]
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    out = open(args.out, "w", encoding="utf-8")
    jarvis.ensure_ollama()
    jarvis.turn(0, typed="Tell me a fun fact about the moon.")    # warm-up: loads the model and the meaning match; not scored
    while jarvis.busy.locked():
        time.sleep(0.05)
    started = time.time()
    for rep in range(args.repeat):
        for n, case in enumerate(cases):
            # a fresh session per case: talk, mood, offers, undo, memory, reminders
            jarvis.history = []
            jarvis.last_turn = 0.0
            session.reset_turn_state()                         # mood, offers, last list, recent, undo, did (jarvislib/session.py)
            for f in (j.MEMORY_FILE, j.REMIND_FILE, j.TOPICS_FILE, j.GIST_FILE):
                if os.path.exists(f):
                    _real_remove(f)
            set_setting_file(res, "JarvisPersonality", case.get("mood", "mirror"))
            for k, v in case.get("settings", {}).items():
                set_setting_file(res, k, v)
            import jarvislib.base as B
            B._settings_cache = (0.0, {})
            turns_out = []
            for t in case["turns"]:
                for k in ("lines", "spoken", "actions", "logs", "prompts"):
                    T[k] = []
                T["first"], T["t0"], T["mood"] = None, time.time(), None
                trips_before = len(TRIPS)
                hearing.heard_score[0] = -1.5 if t.get("unsure") else 0.0
                micmod.onset[0] = 0.0
                err = ""
                try:
                    if t.get("ear"):                           # said in the open ear after his last reply
                        jarvis.exchange(0, 1, False, t.get("ear_mode", "ear"), {}, typed=t["say"])
                    else:
                        jarvis.turn(0, typed=t["say"])
                except Exception as e:                         # exchange() catches its own; this is the harness
                    err = repr(e)
                while jarvis.busy.locked():
                    time.sleep(0.05)
                route = next((l for l in reversed(T["logs"]) if l.startswith("route: ")), "")
                fails = [l for l in T["logs"] if l.startswith("turn failed")]
                turns_out.append({
                    "say": t["say"], "expect": t.get("expect", {}), "lines": T["lines"],
                    "spoken": T["spoken"], "route": route, "actions": T["actions"],
                    "trips": TRIPS[trips_before:], "error": err or (fails[0] if fails else ""),
                    "first_s": round(T["first"], 2) if T["first"] is not None else None,
                    "total_s": round(time.time() - T["t0"], 2), "prompt_chars": T["prompts"],
                    "mood": T["mood"] or case.get("mood", "mirror")})
            row = {"id": case["id"], "tags": case.get("tags", []), "holdout": case.get("holdout", False),
                   "model": args.model, "rep": rep, "turns": turns_out}
            out.write(json.dumps(row, ensure_ascii=False) + "\n")
            out.flush()
            print(f"[{rep}:{n + 1}/{len(cases)}] {case['id']}: " + " | ".join(
                (" ".join(" ".join(s) for s in t["spoken"]) or "(silent)")[:90] for t in turns_out), flush=True)
    out.close()
    print(f"done: {len(cases) * args.repeat} cases in {time.time() - started:.0f}s, tripwires: {len(TRIPS)}")
    keep_log("semi-live run finished")
    shutil.rmtree = _real_rmtree
    _real_rmtree(res, ignore_errors=True)
    return 1 if TRIPS else 0


if __name__ == "__main__":
    sys.exit(main())
