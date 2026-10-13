"""Self-check for jarvis.py: plain asserts, no test framework.  Run:  py -3 -B test_jarvis.py"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jarvis as j

# no disk, no sound card, no processes: fixed app list, fixed window list, recorded mute calls and commands
j.start_apps = lambda: [("Google Chrome", "Chrome"), ("Microsoft Edge", "MSEdge"), ("Notepad", "notepad")]
j.read_kv = lambda name: "W chrome.exe\nW explorer.exe\nW Code.exe\n"
muted_to, ran = [], []
j.speakers_mute = muted_to.append


class _Done:
    returncode = 0


def _run(args, **kw):
    assert kw.get("timeout"), "every command needs a timeout"
    ran.append(args)
    return _Done()


j.subprocess.run = _run
real_sleep = j.time.sleep
j.time.sleep = lambda s: None

# routing: commands act, questions and dangerous phrases never do
assert j.route("lock my computer")[:2] == ("act", "lock")
assert j.route("lock my computer")[3], "lock must ask for confirmation"
assert j.route("should I restart my computer?")[0] == "chat"
assert j.route("jarvis, self destruct")[0] == "guard"
assert j.route("open chrome")[:2] == ("act", "open")
assert j.route("close chrome")[:3] == ("act", "close", "chrome.exe")

# confirmation: the whole reply must be a plain yes, and in time
due = {"action": "shutdown", "target": None, "expires": 100}
assert j.confirmed(due, "yes", 99) and j.confirmed(due, " Go ahead. ", 99) and j.confirmed(due, "Yes, please!", 99)
for no in ("no", "", None, "yes, but don't do it", "yes no", "okay wait", "sure, restart instead", "yesterday"):
    assert not j.confirmed(due, no, 99), no
assert not j.confirmed(due, "yes", 100) and not j.confirmed(due, "yes", 500), "expired"

assert j.best_app("chrome") == ("Google Chrome", "Chrome")
assert j.best_app("") is None
assert j.running_window("chrome") == "chrome.exe"
assert j.running_window("") is None

# short or partial names must not pick an app or a window by accident
assert j.best_app("e") is None and j.best_app("ch") is None and j.best_app("rome") is None
assert j.best_app("edge") == ("Microsoft Edge", "MSEdge") and j.best_app("note") == ("Notepad", "notepad")
assert j.route("open e")[0] == "chat"
assert j.running_window("e") is None and j.running_window("ex") is None and j.running_window("exe") is None
assert j.running_window("code") == "Code.exe" and j.running_window("explorer") == "explorer.exe"
assert j.running_window("plorer") == "explorer.exe" and j.running_window("chr") == "chrome.exe"

# mute / unmute set the state they name, never a toggle
assert j.route("mute")[:2] == ("act", "mute") and j.route("unmute the sound")[:2] == ("act", "unmute")
j.ACTIONS["mute"](None), j.ACTIONS["unmute"](None)
assert muted_to == [True, False], muted_to

# actions report what really happened: every failure is "not done" plus one problem line
j.log = lambda *a: None
failed = []
j.problem = lambda msg, popup=True: failed.append(msg)
assert j.run_action("shutdown", None) and ran[-1] == ["shutdown", "/s", "/t", "10"] and not failed
assert not j.run_action("format disk", None), "only listed actions can run"
_Done.returncode = 1190                                           # non-zero exit code
assert not j.run_action("restart", None)
_Done.returncode = 0


def _hang(args, **kw):
    raise j.subprocess.TimeoutExpired(args, kw["timeout"])


j.subprocess.run = _hang                                          # the command never comes back
assert not j.run_action("shutdown", None)
j.subprocess.run = _run


def _api_down(on):
    raise OSError("no audio endpoint")


j.speakers_mute = _api_down                                       # the Windows call fails
assert not j.run_action("mute", None)
ran.clear()
assert not j.run_action("close", "notepad.exe") and not ran, "missing target: nothing is sent"
assert not j.run_action("close", "chrome.exe") and ran == [["taskkill", "/IM", "chrome.exe"]], "asked, but it stayed open"
j.read_kv = lambda name: "W chrome.exe\n" if not ran else "W explorer.exe\n"
ran.clear()
assert j.run_action("close", "chrome.exe"), "closed once the window is gone"
assert len(failed) == 6, failed
j.read_kv = lambda name: "W chrome.exe\nW explorer.exe\nW Code.exe\n"
j.time.sleep = real_sleep

# the model stream: normal replies come through, and a cancel ends it even while the request is still blocked
import threading
import time


class _Resp(list):
    __enter__ = lambda self: self
    __exit__ = lambda self, *a: False


j.urllib.request.urlopen = lambda *a, **k: _Resp([b'{"message":{"content":"hi"}}\n', b'\n', b'{"done":true}\n'])
assert list(j.chat_stream("m", [])) == ["hi"]
j.urllib.request.urlopen = lambda *a, **k: time.sleep(3)          # a model that is still loading
threading.Timer(0.3, j.cancel.set).start()
t0 = time.time()
assert list(j.chat_stream("m", [])) == [] and time.time() - t0 < 1.5, time.time() - t0
j.cancel.clear()

# idle unload: only after the idle time, never during a turn, never when switched off
j.log = lambda *a: None
minutes = ["10"]
j.setting = lambda key, default="": minutes[0] if key == "JarvisIdleUnload" else default
j._whisper, j._engines["v"] = object(), object()
assert not j.unload_idle(599, 0) and j._whisper is not None
minutes[0] = "0"
assert not j.unload_idle(9999, 0)
minutes[0] = "10"
with j.busy:
    assert not j.unload_idle(9999, 0)
assert j.unload_idle(601, 0) and j._whisper is None and not j._engines
assert not j.unload_idle(9999, 0)                                 # nothing left to unload

# note index: while a reindex runs, a second one is skipped and the search lock stays free
j.vault_dir = lambda: "R"
j._chroma.update(col="COL", root="R", last=0.0, failed=False)
with j._reindexing:
    assert j.chroma_index(force=True) == "COL" and not j._chroma_lock.locked()
assert not j._reindexing.locked()

# GPU asked for but absent: speech recognition lands on a capped CPU model and says so without a pop-up
import types
made, said = [], []
class FakeWhisper:
    def __init__(self, size, device, compute_type, cpu_threads=0):
        if device == "cuda":
            raise RuntimeError("no CUDA device")
        made.append(cpu_threads)
sys.modules["faster_whisper"] = types.SimpleNamespace(WhisperModel=FakeWhisper)
j.setting = lambda name, default: "cuda" if name == "JarvisWhisperDevice" else default
j.problem = lambda msg, popup=True: said.append((msg, popup))
j._whisper = None
j.whisper()
assert made == [j.cpu_threads()] and 2 <= made[0] <= max(2, (os.cpu_count() or 8) // 4)
assert len(said) == 1 and said[0][0].startswith("CPU in use") and said[0][1] is False

print("test_jarvis: OK")
