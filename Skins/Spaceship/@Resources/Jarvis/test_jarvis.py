"""Self-check for jarvis.py: plain asserts, no test framework.  Run:  py -3 -B test_jarvis.py"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jarvis as j

# no disk, no sound card, no processes: fixed app list, fixed window list, recorded mute calls and commands
real_start_apps, real_transcribe = j.start_apps, j.transcribe
j.start_apps =lambda: [("Google Chrome", "Chrome"), ("Microsoft Edge", "MSEdge"), ("Notepad", "notepad")]
j.read_kv = lambda name: "W chrome.exe\nW explorer.exe\nW Code.exe\n"
muted_to, ran = [], []
j.REMIND_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "no-such-reminders")
j.MEMORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "no-such-memory")   # never the real one
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

# volume and media: commands act, questions and other sentences do not, and the level stays inside 0-100
vol, keys = [40], []


def _speakers(mute=None, volume=None):
    if volume is not None:
        vol[0] = round(volume * 100)
    return (False, vol[0])


j.speakers, j.press_key = _speakers, keys.append
for heard, want in (("set volume to 30", ("set", 30)), ("volume 5 percent", ("set", 5)), ("turn it up", ("step", 10)),
                    ("Jarvis, can you turn the volume down?", ("step", -10)), ("louder", ("step", 10)),
                    ("turn down the music", ("step", -10))):
    assert j.route(heard)[:3] == ("act", "volume", want), heard
assert j.route("set volume to 130") == ("say", None, None, "I can set it between 0 and 100.")
for heard, want in (("pause", "playpause"), ("resume the music", "playpause"), ("stop the music", "playpause"),
                    ("next track", "next"), ("skip", "next"), ("previous song", "prev"), ("go back a song", "prev")):
    assert j.route(heard)[:3] == ("act", "media", want), heard
for heard in ("should I turn it up?", "how do I pause a download?", "play despacito", "what volume is 30 decibels", "stop"):
    assert j.route(heard)[0] == "chat", heard
j.ACTIONS["volume"](("set", 30))
assert vol == [30] and j.done_line("volume", None) == "Volume at 30 percent."
j.ACTIONS["volume"](("step", -10)), j.ACTIONS["volume"](("step", -50))
assert vol == [0]
j.ACTIONS["volume"](("set", 95)), j.ACTIONS["volume"](("step", 10))
assert vol == [100]
j.ACTIONS["media"]("next")
assert keys == [0xB0] and j.done_line("media", "next") == "Sent."

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
j.speakers = lambda **kw: _api_down(kw)
assert not j.run_action("volume", ("set", 30)) and vol == [100]
j.speakers = _speakers
ran.clear()
assert not j.run_action("close", "notepad.exe") and not ran, "missing target: nothing is sent"
assert not j.run_action("close", "chrome.exe") and ran == [["taskkill", "/IM", "chrome.exe"]], "asked, but it stayed open"
j.read_kv = lambda name: "W chrome.exe\n" if not ran else "W explorer.exe\n"
ran.clear()
assert j.run_action("close", "chrome.exe"), "closed once the window is gone"
assert len(failed) == 7, failed
j.read_kv = lambda name: "W chrome.exe\nW explorer.exe\nW Code.exe\n"
j.time.sleep = real_sleep

# HUD readings: every source that answers gets a line; an unmapped or missing sensor, a stale file or a hanging tool
# costs only its own line
real_settings, real_gpu = j.settings, j.gpu
j.settings = lambda: {"HW_CpuTemp": "3", "HW_GpuTemp": "-1", "HW_Fan1": "9"}


def _hw(n):
    if n == 9:
        raise OSError("no such sensor")
    return 61.4


class _Smi:
    returncode, stdout = 0, "37, 2048, 8192\n"


ticks = iter([(100, 1000), (150, 1200)])
j.hw_value, j.cpu_times, j.gpu = _hw, lambda: next(ticks), lambda: True
j.subprocess.run = lambda args, **kw: _Smi()
j.read_kv = lambda name: f"T {int(j.time.time())}\nBRIGHT 70\nMIC -1\nMICMUTE 0\n"
real_load, j.load_reminders = j.load_reminders, lambda: [(j.time.time() + 600, 0, "reminder", "to cook")]
got = j.sensors()
assert "Pending: reminder at " in got and "cook" not in got, got   # what kind and when, not what it says
for line in ("CPU temperature: 61 C", "CPU load: 75%", "GPU load: 37%, video memory 2.0 of 8 GB in use",
             "Speaker volume: 100%", "Screen brightness: 70%", "GB free of"):
    assert line in got, (line, got)
assert "GPU temperature" not in got and "Fan 1" not in got and "Microphone" not in got, got
j.subprocess.run, j.read_kv = _hang, lambda name: "T 5\nBRIGHT 70\n"
got = j.sensors()                                                 # nvidia-smi hangs, the HUD's file is old, no CPU sample
assert "CPU temperature: 61 C" in got and not [x for x in ("GPU load", "brightness", "CPU load") if x in got], got
j.load_reminders = lambda: [(j.time.time() + 60, 0, "timer", ""), (j.time.time() + 600, 0, "reminder", "alarm")]
assert "Pending: timer with 1 minute left; alarm at " in j.sensors()   # an alarm is named an alarm, never a timer
j.load_reminders = lambda: []
assert "Pending: no alarms, reminders or timers" in j.sensors()     # nothing pending is said, so the model never guesses
j.subprocess.run, j.settings, j.gpu, j.load_reminders = _run, real_settings, real_gpu, real_load
j.read_kv = lambda name: "W chrome.exe\nW explorer.exe\nW Code.exe\n"

# model choice: the wanted model, else the other configured one, never an arbitrary or embedding model
real_setting, conf = j.setting, {"JarvisModel": "big:7b", "JarvisModelFast": "small:3b"}
j.setting = lambda name, default="": conf.get(name, default)
j.installed_models = lambda: ["big:7b", "nomic-embed-text:latest", "small:3b"]
assert j.pick_model(0) == "big:7b" and j.pick_model(1) == "small:3b"
j.installed_models = lambda: ["nomic-embed-text:latest", "small:3b"]
assert j.pick_model(0) == "small:3b", "missing model: the other configured one"
j.installed_models = lambda: ["aaa-embed:latest", "nomic-embed-text:latest"]
assert j.pick_model(0) is None and j.pick_model(1) is None, "embedding models only: no model"
j.installed_models = lambda: []
assert j.pick_model(0) is None
j.installed_models = lambda: None                                 # Ollama not answering: keep the wanted name
assert j.pick_model(0) == "big:7b"

# vault: a folder you set is trusted; the to-do note's folder counts only with .obsidian in it or up to three above
import tempfile
tmp = tempfile.mkdtemp()
for d in (("vault", ".obsidian"), ("vault", "a", "b"), ("loose",)):
    os.makedirs(os.path.join(tmp, *d))
for p in (("vault", "a", "b", "todo.md"), ("loose", "todo.md")):
    open(os.path.join(tmp, *p), "w").close()
conf["ObsidianTodo"] = os.path.join(tmp, "loose", "todo.md")
assert j.vault_dir() == "", "a to-do note outside a vault: no vault"
conf["ObsidianTodo"] = os.path.join(tmp, "vault", "a", "b", "todo.md")
assert j.vault_dir() == os.path.join(tmp, "vault")
conf["JarvisVault"] = os.path.join(tmp, "loose")
assert j.vault_dir() == os.path.join(tmp, "loose")
j.setting = real_setting

# app list: a missing file is "not ready", an empty one is "no apps"
fake_apps, j.start_apps, real_data, j.DATA = j.start_apps, real_start_apps, j.DATA, tmp
assert j.start_apps() is None and j.best_app("chrome") is None
assert j.route("open chrome") == ("say", None, None, "The app list isn't ready yet.")
open(os.path.join(tmp, "StartApps.txt"), "w").close()
assert j.start_apps() == [] and j.route("open chrome")[0] == "chat"
j.start_apps, j.DATA = fake_apps, real_data

# memory: a failed Windows call leaves the line out instead of reporting 0 %
real_settings, j.settings = j.settings, lambda: {}
assert "Memory in use" in j.context()
j.ctypes.windll.kernel32.GlobalMemoryStatusEx = lambda p: 0
assert "Memory in use" not in j.context()
del j.ctypes.windll.kernel32.GlobalMemoryStatusEx
j.settings = real_settings

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


class _Col:
    def delete(self, where):
        dropped.append(where["path"])


# a note that is gone from the vault is taken out of the index
dropped, empty = [], os.path.join(tmp, "loose", "none")
os.makedirs(empty)
j.vault_dir = lambda: empty
j._chroma.update(col=_Col(), root=empty, seen={"old.md": 1.0}, last=0.0, failed=False)
assert j.chroma_index(force=True) is j._chroma["col"] and dropped == ["old.md"] and not j._chroma["seen"]

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
j.gpu = lambda: True                                              # the card is there, the load still failed
j._whisper = None
j.whisper()
assert made == [j.cpu_threads()] and 2 <= made[0] <= max(2, (os.cpu_count() or 8) // 4)
assert len(said) == 1 and said[0][0].startswith("CPU in use") and said[0][1] is False
j.setting = lambda name, default: "gpu" if name == "JarvisWhisperDevice" else default     # a mistyped device
j._whisper = None
j.whisper()
assert "JarvisWhisperDevice=gpu" in said[-1][0], said[-1]

# Phase 2: off the card only until it is back
card, made = [False], []
class CardWhisper:
    def __init__(self, size, device, compute_type, cpu_threads=0):
        if device == "cuda" and not card[0]:
            raise RuntimeError("no CUDA device")
        real_sleep(0.05)                                          # slow enough that two loads at once would overlap
        self.device = device
        made.append(device)
    def transcribe(self, audio, **k):
        if self.device == "cuda" and not card[0]:
            raise RuntimeError("CUDA error: device lost")
        return [types.SimpleNamespace(text="hello")], None
def until(check):
    for _ in range(200):
        if check():
            return True
        real_sleep(0.02)
    return False
sys.modules["faster_whisper"] = types.SimpleNamespace(WhisperModel=CardWhisper)
j.setting = lambda name, default: default
j.gpu = lambda: card[0]
j._whisper = None
j.whisper()                                                       # the card is off: the plain reason, no pop-up
assert made == ["cpu"] and j._whisper_dev[0] == "cpu"
assert said[-1] == ("RTX is off - switch the laptop to hybrid graphics", False), said[-1]
card[0], t = True, j._gpu_try[0]                                  # the card comes back
with j.busy:
    assert not j.gpu_watch(t + 61)                                # never during a turn
assert not j.gpu_watch(t + 30)                                    # at most once a minute
j.S.err = "RTX is off - switch the laptop to hybrid graphics"
assert j.gpu_watch(t + 61) and until(lambda: j._whisper_dev[0] == "cuda") and made == ["cpu", "cuda"]
assert until(lambda: j.S.err == ""), j.S.err                      # back on the card: the warning goes too
assert not j.gpu_watch(t + 200)                                   # already on the card
card[0] = False                                                   # the card drops out mid-turn: that sentence on the CPU
assert real_transcribe("audio") == "hello" and j._whisper_dev[0] == "cpu"
card[0], t = True, j._gpu_try[0]
j.S.err = "No microphone found"
assert not j.gpu_watch(t + 30) and j.gpu_watch(t + 61) and until(lambda: j._whisper_dev[0] == "cuda")
assert j.S.err == "No microphone found"                           # other problems stay
j.S.err = ""
made.clear()                                                      # two threads at once load one model
j._whisper = None
both = [threading.Thread(target=j.whisper) for _ in range(2)]
[x.start() for x in both], [x.join() for x in both]
assert made == ["cuda"], made
# the chat model off the card: reloaded once, not on every turn, and not while the card is away
real_http, real_warm, posts = j.http_json, j.warm, []
j.http_json = lambda path, payload=None, timeout=5: posts.append(payload) or {}
j.warm = lambda m: posts.append("warm " + m)
assert j.chat_to_gpu("m") and not j.chat_to_gpu("m")
assert until(lambda: len(posts) == 2) and posts == [{"model": "m", "keep_alive": 0}, "warm m"], posts
card[0] = False
assert not j.chat_to_gpu("other")
j.http_json, j.warm, j.gpu = real_http, real_warm, real_gpu
j._moved.clear()
j._whisper = None
# the voice on the CPU is the design, not a problem line
vdir = tempfile.mkdtemp()
open(os.path.join(vdir, "voices-v1.0.bin"), "wb").close()
class FakeKokoro:
    def get_voices(self):
        return ["bm_lewis"]
    def create(self, text, voice, speed, lang):
        return [0.0, 0.1], 24000
real_mods, n = {m: sys.modules.get(m) for m in ("kokoro_onnx", "onnxruntime")}, len(said)
sys.modules["kokoro_onnx"] = types.SimpleNamespace(Kokoro=types.SimpleNamespace(from_session=lambda s, b: FakeKokoro()))
sys.modules["onnxruntime"] = types.SimpleNamespace(SessionOptions=types.SimpleNamespace, InferenceSession=lambda *a, **k: None)
assert j._kokoro(os.path.join(vdir, "kokoro-v1.0.int8.onnx"), "hi")[1] == 24000 and len(said) == n
assert j._voice_dev[0] == "cpu"                                   # no full model next to it: the CPU, as before
# Phase 2e: the full model on the RTX when it is there, the int8 one on the CPU otherwise
sessions, avail, broken = [], ["CUDAExecutionProvider", "CPUExecutionProvider"], [False]
class FakeSess:
    def __init__(self, path, opts=None, providers=None):
        self.path, self.prov = os.path.basename(path), [p[0] if isinstance(p, tuple) else p for p in providers or []]
        sessions.append(self)
    def get_providers(self):
        return [p for p in self.prov if p in avail]
class BreakingKokoro(FakeKokoro):
    def create(self, text, voice, speed, lang):
        if broken[0]:
            raise RuntimeError("CUDA error: device lost")
        return FakeKokoro.create(self, text, voice, speed, lang)
sys.modules["kokoro_onnx"] = types.SimpleNamespace(Kokoro=types.SimpleNamespace(from_session=lambda s, b: BreakingKokoro()))
sys.modules["onnxruntime"] = types.SimpleNamespace(SessionOptions=types.SimpleNamespace, InferenceSession=FakeSess,
                                                   get_available_providers=lambda: avail)
open(os.path.join(vdir, "kokoro-v1.0.onnx"), "wb").close()
int8 = os.path.join(vdir, "kokoro-v1.0.int8.onnx")
j._engines.clear()
real_dlls = j._cuda_dlls
j.gpu, j._cuda_dlls = lambda: True, lambda: None
assert j._kokoro(int8, "hi")[1] == 24000 and j._voice_dev[0] == "cuda"
assert (sessions[-1].path, sessions[-1].prov[0]) == ("kokoro-v1.0.onnx", "CUDAExecutionProvider")
broken[0] = True                                                  # the card drops out mid-sentence
try:
    j._kokoro(int8, "hi")
    assert False, "the error must reach synth_audio, which retries with a fresh engine"
except RuntimeError:
    j._engines.pop(int8, None)
broken[0] = False
assert j._kokoro(int8, "hi")[1] == 24000 and j._voice_dev[0] == "cpu"   # the retry runs on the CPU
assert (sessions[-1].path, sessions[-1].prov) == ("kokoro-v1.0.int8.onnx", ["CPUExecutionProvider"])
j._engines.clear(); j._voice_gpu_off[0] = 0.0
j.gpu = lambda: False                                             # card off: the CPU
assert j._kokoro(int8, "hi") and sessions[-1].path == "kokoro-v1.0.int8.onnx" and j._voice_dev[0] == "cpu"
j._engines.clear()
j.gpu = lambda: True; avail.remove("CUDAExecutionProvider")      # the CPU-only onnxruntime: the CPU
assert j._kokoro(int8, "hi") and sessions[-1].path == "kokoro-v1.0.int8.onnx" and j._voice_dev[0] == "cpu"
j.gpu, j._engines, j._cuda_dlls = real_gpu, {}, real_dlls
assert len(said) == n                                             # none of this is a problem line
for m, mod in real_mods.items():
    if mod is None:
        del sys.modules[m]
    else:
        sys.modules[m] = mod
j._engines.clear()

# muted: Windows is asked first, the HUD's file only when that fails
j.ENV_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "no-such-file")
j.speakers_mute = lambda on=None: True
assert j.muted() is True
j.speakers_mute = _api_down
assert j.muted() is False

# ---- the speech path, with fakes for the microphone, the voice, the speakers and the HUD state
states, played, words = [], [], []


class _S:
    def set(self, **kw):
        states.append(kw)


def within(seconds, fn, *args):
    """Run fn on a thread: a hang fails the check instead of freezing it. Returns the result or the exception."""
    out = []

    def run():
        try:
            out.append(fn(*args))
        except Exception as e:
            out.append(e)
    t = threading.Thread(target=run, daemon=True)
    t.start()
    t.join(seconds)
    assert not t.is_alive(), "still waiting"
    return out[0]


j.S, j.muted, j.live, j.filler_done = _S(), lambda: False, words.append, lambda: None
j.setting = lambda name, default="": default
real_synth_audio = j.synth_audio
j.synth_audio = lambda text: (text, 1)
j.play_samples = lambda a, rate: played.append(a)
many =[str(i) for i in range(20)]

# more sentences than the queue holds: all spoken, in order
assert within(5, j.speak_all, many) is None and played == many


def _breaks():
    yield "one"
    raise j.urllib.error.URLError("gone")


# the model stream dies mid-reply: the reader is not stranded and the turn gets the error
played.clear()
assert isinstance(within(5, j.speak_all, _breaks()), j.urllib.error.URLError) and played == ["one"]


def _no_voice(text):
    raise RuntimeError("voice broke")


# the voice fails: the words are shown instead and it still ends
j.synth_audio, n = _no_voice, len(said)
assert within(5, j.speak_all, ["hi"]) is None and "hi" in words and said[n:] == [("Couldn't speak (voice failed) - the reply is in the log", False)]
j.synth_audio = lambda text: (text, 1)

# cancelled mid-utterance: the queued sentences are dropped, and a full queue does not hold the producer
played.clear()
j.play_samples = lambda a, rate: (played.append(a), j.cancel.set())
assert within(5, j.speak_all, many) is None and played == ["0"]
j.cancel.clear()
j.play_samples = lambda a, rate: played.append(a)

# cancelled while a sentence is still being made
j.synth_audio = lambda text: time.sleep(3)
threading.Timer(0.2, j.cancel.set).start()
t0 = time.time()
within(5, j.speak_all, ["slow"])
assert time.time() - t0 < 1.5, time.time() - t0
j.cancel.clear()

# one owner of the microphone: a second taker is refused, and it is always handed back
with j.mic:
    assert isinstance(within(2, j.listen, 0.1), RuntimeError)
j._listen = lambda patience: "audio"
assert j.listen() == "audio" and not j.mic.locked()
j._listen = lambda patience: _no_voice("")
assert isinstance(within(2, j.listen), RuntimeError) and not j.mic.locked()

# a whole turn: every way out ends idle with the turn lock free
j.missing_packages, j.ensure_ollama, j.pick_model, j.warm = lambda: [], lambda: True, lambda tier: "m", lambda m: None
j.http_json = lambda *a, **k: (_ for _ in ()).throw(OSError("no Ollama in tests"))   # the AI fallback falls back
j.prepare_fillers, j.chime, j.watchdog, j.sensors = lambda: None, lambda: 0, lambda started: None, lambda: "Fan 1: 900 RPM"
idle = {"state": "idle", "level": 0.0}
states.clear()
with j.busy:                                                      # a second click while a turn runs does nothing
    j.turn(0)
assert not states
j.listen = lambda: None                                           # nobody spoke
j.turn(0)
assert states[-1] == idle and not j.busy.locked()
j.listen, j.transcribe = lambda: "audio", _no_voice               # speech recognition fails
j.turn(0)
assert said[-1] == ("voice broke", True) and states[-1] == idle and not j.busy.locked()
# JarvisGPU=require with the card off: the fixed line, no listening, no model
real_setting, real_listen, touched = j.setting, j.listen, []
j.setting = lambda name, default="": "require" if name == "JarvisGPU" else default
j.gpu, j.ensure_ollama, j.listen = lambda: False, lambda: touched.append("ollama"), lambda *a, **k: touched.append("mic")
j.turn(0)
assert touched == [] and j.recent["me"] == "My graphics card is off." and states[-1] == idle and not j.busy.locked()
j.setting, j.listen, j.ensure_ollama, j.gpu = real_setting, real_listen, lambda: True, real_gpu

# ---- timers and reminders: read by code (never the model), kept in a file, rung by alarm()
from datetime import datetime


def cmd(text):
    kind, op, args, _ = j.route(text)
    return (op,) + tuple(args) if kind == "remind" else None


def ahead(text):
    """(kind, seconds from now, label) of a "set" command."""
    _, kind, due, label, _ = cmd(text)
    return kind, None if due is None else round(due - time.time()), label


for text, want in (
        ("Remind me to cook in 20 minutes.", ("reminder", 1200, "to cook")),
        ("remind me in 20 minutes to cook food", ("reminder", 1200, "to cook food")),
        ("Hey Jarvis, remind me to call my mum in an hour and a half", ("reminder", 5400, "to call your mum")),
        ("remind me about the meeting in two hours", ("reminder", 7200, "about the meeting")),
        ("remind me in half an hour", ("reminder", 1800, "")),
        ("remind me to look at the oven in twenty five minutes", ("reminder", 1500, "to look at the oven")),
        ("set a reminder for the dentist in 1 hour 30 minutes", ("reminder", 5400, "about the dentist")),
        ("remind me to cook", ("reminder", None, "to cook")),
        ("Set a timer for 10 minutes.", ("timer", 600, "")),
        ("Can you set a timer for 10 minutes?", ("timer", 600, "")),
        ("ten minute timer for the pasta", ("timer", 600, "the pasta")),
        ("set a 5-minute timer", ("timer", 300, "")),
        ("start a timer for the eggs for 90 seconds", ("timer", 90, "the eggs")),
        ("set a pasta timer for two minutes and 30 seconds", ("timer", 150, "pasta")),
        ("set a timer", ("timer", None, ""))):
    assert ahead(text) == want, (text, ahead(text))
for text in ("How do I set a timer in Python?", "what is a timer", "open timer", "What's the best reminder app?",
             "should I set a timer?", "remind", "stop the music", "what timer should I buy",
             "Can you remind me what the capital of France is?", "remind me how this works"):
    assert cmd(text) is None, text
assert ahead("remind me of the dentist in 2 hours") == ("reminder", 7200, "about the dentist")
assert cmd("What reminders do I have?") == ("list", "reminder") and cmd("list my timers") == ("list", "timer")
assert cmd("how much time is left on the timer") == ("list", "timer")
assert cmd("cancel the cooking reminder") == ("cancel", "reminder", "cooking")
assert cmd("Cancel all reminders.") == ("cancel", "reminder", "all") and cmd("stop the timer") == ("cancel", "timer", "")
assert cmd("cancel the timer for the pasta") == ("cancel", "timer", "the pasta")

# clock times, from 3 PM: the next time the clock shows it; anything unreadable is None, never a guess
at3 = datetime(2026, 10, 13, 15, 0).timestamp()


def hm(text):
    due = j.when(text, at3)
    return due and datetime.fromtimestamp(due).strftime("%d %H:%M")


for text, want in (("at 6:30 pm", "13 18:30"), ("at 18:30", "13 18:30"), ("at 6 30", "13 18:30"), ("at 7", "13 19:00"),
                   ("at 2", "14 02:00"), ("at 9 a.m.", "14 09:00"), ("at 12", "14 00:00"), ("at 12 pm", "14 12:00"),
                   ("at 25", None), ("at 6:75", None), ("at seven", "13 19:00"), ("in a bit", None), ("in 0 minutes", "13 15:00")):
    assert hm(text) == want, (text, hm(text))
assert j.clock(at3 + 12600, at3) == "6:30 PM" and j.clock(at3 + 65100, at3) == "9:05 AM tomorrow"
assert j.clock(at3 + 3 * 86400, at3) == "3:00 PM on Friday"
assert (j.span(600), j.span(5400), j.span(600, ""), j.span(90)) == ("10 minutes", "1 hour 30 minutes", "10 minute", "1 minute 30 seconds")
for item, want in (((at3, at3 - 1200, "reminder", "to cook food"), "Time to cook food."),
                   ((at3, at3 - 600, "timer", ""), "Your 10 minute timer is done."),
                   ((at3, at3 - 600, "timer", "the pasta"), "Your timer for the pasta is done."),
                   ((at3, at3 - 600, "reminder", "about the meeting"), "Reminder about the meeting."),
                   ((at3, at3 - 600, "reminder", "that the oven is on"), "Reminder: the oven is on."),
                   ((at3, at3 - 600, "reminder", ""), "This is your reminder.")):
    assert j.ring_line(item, at3 + 1) == want, j.ring_line(item, at3 + 1)
assert j.ring_line((at3, at3 - 60, "reminder", "to cook"), at3 + 600) == "Missed reminder from 3:00 PM: time to cook."

# set, list and cancel against a file in a temp folder; he says back what he set
j.REMIND_FILE = os.path.join(tmp, "reminders.txt")
asked, convo, acted = [], [], []
j.reply_line = lambda text, quiet: asked.append(text)
j.convo_add = lambda who, text: convo.append((who, text))


def do(text):
    kind, op, args, _ = j.route(text)
    assert kind == "remind", text
    return j.remind_reply(op, args, False)


assert j.due_reminders(time.time()) is False                      # no file yet: nothing due, nothing wrong
assert do("list my timers") == "You have no timers."
assert do("remind me to cook in 20 minutes") == "I'll remind you to cook in 20 minutes."
assert do("set a timer for 10 minutes") == "Timer set for 10 minutes."
assert do("ten minute timer for the pasta") == "Timer set for 10 minutes, for the pasta."
assert [r[2:] for r in j.load_reminders()] == [("timer", ""), ("timer", "the pasta"), ("reminder", "to cook")]
assert do("what reminders do I have").startswith("You have 1 reminder: to cook at ")
assert do("list my timers").startswith("You have 2 timers: ") and "for the pasta" in do("list my timers")
assert do("cancel the pasta timer").startswith("Cancelled: ") and len(j.load_reminders()) == 2
assert do("cancel the cooking reminder").startswith("Cancelled: to cook at ")
assert do("cancel the cooking reminder").startswith("I don't see a reminder like that. You have: ")   # the timer left
assert do("cancel all timers").startswith("Cancelled: ") and j.load_reminders() == []
j.listen, j.transcribe = lambda: "audio", lambda a: "Twenty minutes."       # no time said: he asks once and listens
assert do("remind me to stretch") == "I'll remind you to stretch in 20 minutes." and asked[-1] == "When?"
j.listen = lambda: None
assert do("set a timer") == "I didn't catch the time." and asked[-1] == "How long?"
assert do("set a timer for 2 seconds") == do("remind me to rest in 200 hours") == "I can set that from 5 seconds to 7 days ahead."
j.save_reminders([(time.time() + 900 + i, time.time(), "timer", "") for i in range(20)])
assert do("set a timer for 10 minutes") == "You already have 20 pending. Cancel one first."
assert j.due_reminders(time.time()) is False and j.due_reminders(time.time() + 901) is True

# a file that cannot be read is an error, not "no reminders": said once, and nothing is written over it
with open(j.REMIND_FILE, "w", encoding="utf-8") as f:
    f.write("not a reminder\n")
n = len(said)
assert do("set a timer for 10 minutes") == "I can't read the reminders file, so I left it alone."
assert j.due_reminders(time.time()) is False and j.due_reminders(time.time()) is False
assert len(said) == n + 1 and said[-1][1] is False, said[n:]
with open(j.REMIND_FILE, encoding="utf-8") as f:
    assert f.read() == "not a reminder\n"

# the alarm: ding and line until a stop word, a click or the last round; always ends idle with the turn lock free
real_ding = j.ding
j.ding, j.synth_audio = lambda: ("ding", 1), lambda text: (text, 1)


def ring(heard, mute=False, late=1):
    """One reminder that is due and a timer that is not, then the alarm: (dings played, what is left in the file)."""
    now, back = time.time(), iter(heard)
    j.save_reminders([(now - late, now - 1200 - late, "reminder", "to cook"), (now + 900, now, "timer", "")])
    played.clear(), convo.clear(), states.clear()
    j.muted, j.listen, j.transcribe = lambda: mute, lambda: "audio", lambda a: next(back, "")
    assert within(5, j.alarm) is None
    assert states[-1] == idle and not j.busy.locked() and time.time() - j.turn_id[0] < 5   # the idle timer was reset
    return played.count("ding"), [r[2] for r in j.load_reminders()]


assert ring(["", "Stop."]) == (2, ["timer"]) and convo == [("J", "Time to cook."), ("J", "(stopped)")]
assert played == ["ding", "Time to cook.", "ding", "Time to cook."]
for word in ("shush", "Shut up!", "Shutup.", "okay, thanks", "don't stop believing"):
    assert ring([word])[0] == 1, word
assert ring(["what's for dinner"] * 20) == (j.RINGS, ["timer"]) and ("J", "(stopped)") not in convo   # nobody stopped it
assert ring([], mute=True) == (0, ["timer"]) and played == [] and {"pop": "open"} in states       # muted: shown, not rung
assert convo == [("J", "Time to cook.")]
j.hud_tier = lambda: 3                                            # STEALTH is silent too
assert ring([]) == (0, ["timer"]) and {"pop": "open"} in states
j.hud_tier = lambda: 0
assert ring([], late=600)[0] == j.RINGS and convo[0][1].startswith("Missed reminder from ") and convo[0][1].endswith(": time to cook.")
j.play_samples = lambda a, rate: (played.append(a), j.cancel.set())           # a click while it rings
assert ring([]) == (1, ["timer"]) and played == ["ding"] and convo[-1] == ("J", "(stopped)")
j.play_samples = lambda a, rate: played.append(a)
j.synth_audio = _no_voice                                         # it breaks mid-way: one problem line, still idle
assert ring([]) == (0, ["timer"]) and said[-1] == ("A reminder could not ring", True) and convo == [("J", "Time to cook.")]
j.synth_audio = lambda text: (text, 1)
with j.busy:                                                      # a turn is running: the alarm waits for it
    waiting = threading.Thread(target=j.alarm, daemon=True)
    j.save_reminders([(time.time() - 1, time.time() - 9, "timer", "")])
    played.clear()
    waiting.start()
    waiting.join(0.3)
    assert waiting.is_alive() and played == []
waiting.join(5)
assert played.count("ding") == j.RINGS and j.load_reminders() == [] and not j.busy.locked()

# whole turns: a timer is set from speech, and a confirmation is still heard through the same second listen
j.setting = lambda name, default="": "0" if name == "JarvisFollowUp" else default     # one turn each: no follow-up
turns = iter(["Set a timer for 10 minutes.", "Lock my computer.", "Yes."])
j.muted, j.listen, j.transcribe = lambda: False, lambda: "audio", lambda a: next(turns)
real_run_action = j.run_action
j.run_action = lambda action, target: acted.append(action) or True
j.turn(0)
assert asked[-1] == "Timer set for 10 minutes." and states[-1] == idle and not j.busy.locked()
j.turn(0)
assert acted == ["lock"] and asked[-1] == "Done." and states[-1] == idle and not j.busy.locked()
try:                                                              # the ding itself, where numpy is installed
    import numpy
    tone, rate = real_ding()
    assert rate == 24000 and tone.dtype == numpy.float32 and 0.2 < abs(tone).max() <= 0.4 and len(tone) == 21600
except ImportError:
    pass

# ---- snooze: heard in the same gap as "stop" and checked first; one minute unless a length is said
assert j.snooze_for("Snooze.") == j.snooze_for("okay, later") == j.snooze_for("Not now!") == j.SNOOZE == 60
assert j.snooze_for("snooze 5 minutes") == 300 and j.snooze_for("Ten more minutes.") == 600
assert j.snooze_for("snooze for half an hour") == 1800
assert j.snooze_for("snooze 5 hours") == 0 and j.snooze_for("snooze 10 seconds") == 0     # out of range: keeps ringing
assert j.snooze_for("stop") is None and j.snooze_for("") is None and j.snooze_for("no more") is None
t0 = time.time()
assert ring(["Snooze."]) == (1, ["reminder", "timer"]) and asked[-1] == "Snoozed for 1 minute."
assert 55 < j.load_reminders()[0][0] - t0 < 70 and j.load_reminders()[0][3] == "to cook"
assert ring(["", "okay, snooze 5 minutes"]) == (2, ["reminder", "timer"]) and asked[-1] == "Snoozed for 5 minutes."
assert ring(["okay"]) == (1, ["timer"])
assert ring(["snooze 5 hours", "stop"]) == (2, ["timer"])

# ---- repeating reminders: the rule lives in the kind field, and the next time is saved before it rings
mon9 = datetime(2026, 10, 12, 9, 0).timestamp()                   # a Monday
day = lambda ts: datetime.fromtimestamp(ts).strftime("%a %d %H:%M")
assert day(j.next_due(mon9, "daily", mon9)) == "Tue 13 09:00"
assert day(j.next_due(mon9 + 4 * 86400, "weekdays", mon9 + 4 * 86400)) == "Mon 19 09:00"      # Friday -> Monday
assert day(j.next_due(mon9, "mon", mon9)) == "Mon 19 09:00"
assert day(j.next_due(mon9, "daily", mon9 + 3 * 86400 + 60)) == "Fri 16 09:00"               # three missed days: one next time
op, kind, due, label, said_time = cmd("remind me every day at 9 to take vitamins")
assert (op, kind, label) == ("set", "daily", "to take vitamins") and due > time.time()
op, kind, due, label, _ = cmd("Remind me every weekday at 8:30 to check mail.")
assert (kind, label) == ("weekdays", "to check mail") and datetime.fromtimestamp(due).weekday() < 5
op, kind, due, label, _ = cmd("remind me to put the bins out every Monday at 7")
assert (kind, label) == ("mon", "to put the bins out") and datetime.fromtimestamp(due).weekday() == 0
assert ahead("remind me to cook in 20 minutes") == ("reminder", 1200, "to cook")             # a single one is as before
j.save_reminders([])
assert do("remind me every day at 9 am to take vitamins") == "I'll remind you to take vitamins every day at 9:00 AM."
assert do("remind me every day in 20 minutes to stretch") == "A repeating reminder needs a clock time, like every day at 9."
assert do("remind me every day to stretch") == "A repeating reminder needs a clock time, like every day at 9."
assert "to take vitamins, every day at 9:00 AM" in do("what reminders do I have") and do("list my timers") == "You have no timers."
assert do("cancel the vitamins reminder").startswith("Cancelled: ") and j.load_reminders() == []   # the whole series
now = time.time()
j.save_reminders([(now - 1, now - 100, "daily", "to take vitamins")])
back = iter(["stop"])
j.muted, j.listen, j.transcribe = lambda: False, lambda: "audio", lambda a: next(back, "")
convo.clear()
assert within(5, j.alarm) is None and convo[0] == ("J", "Time to take vitamins.")
left = j.load_reminders()
assert len(left) == 1 and left[0][2:] == ("daily", "to take vitamins") and 80000 < left[0][0] - now < 92000
j.save_reminders([(now - 3 * 86400, now - 4 * 86400, "daily", "to take vitamins")])           # the PC was off for three days
back = iter(["snooze"])
convo.clear()
assert within(5, j.alarm) is None and convo[0][1].startswith("Missed reminder from ")
assert sorted(r[2] for r in j.load_reminders()) == ["daily", "reminder"]     # the series goes on; the snooze is a single ring
assert all(r[0] > now for r in j.load_reminders())
j.save_reminders([])

# ---- remembered facts: kept in a file, said back in your own words, forgotten by word; questions never save
j.context = lambda: ""
j.MEMORY_FILE = os.path.join(tmp, "memory.txt")


def mem(text):
    kind, op, target, _ = j.route(text)
    assert kind == "memory", text
    return j.memory_reply(op, target)


assert mem("What do you remember?") == "You haven't asked me to remember anything."
assert mem("Remember that my dentist is on Fridays.") == "Noted: my dentist is on Fridays."
assert mem("Jarvis, remember my bike is in the shed") == "Noted: my bike is in the shed."
assert mem("remember my bike is in the shed") == "Noted: my bike is in the shed." and len(j.load_memory()) == 2   # not twice
assert mem("what have I told you to remember") == "I remember 2 things: my dentist is on Fridays; my bike is in the shed."
for text in ("Do you remember that film?", "do you remember that film", "remember to buy milk", "forget it", "Remember that film?"):
    assert j.route(text)[0] == "chat", text
assert j.route("forget the cooking reminder")[0] == "remind"
assert "THINGS THE USER ASKED YOU TO REMEMBER:\n- my dentist is on Fridays\n- my bike is in the shed" in j.system_prompt()
assert j.route("forget everything") == ("act", "forget_all", None, "Forget all 2 things I remember? Confirm with yes.")
assert mem("forget that my dentist is on Fridays") == "Forgotten: my dentist is on Fridays."
assert mem("forget the dentist") == "I don't have that." and j.load_memory() == ["my bike is in the shed"]
j.ACTIONS["forget_all"](None)
assert j.load_memory() == [] and j.route("forget everything")[:2] == ("say", None)
assert "TO REMEMBER" not in j.system_prompt()
j.save_memory([f"fact {i}" for i in range(50)])
assert mem("remember one more thing") == "You've told me 50 things. Forget one first." and len(j.load_memory()) == 50
j.save_memory([])
assert mem("remember " + "x" * 300) == "Noted: " + "x" * 200 + "."
with open(j.MEMORY_FILE, "wb") as f:                              # unreadable: said, left alone, and the prompt still works
    f.write(b"\xff\xfe\xff")
assert mem("remember the milk is off") == mem("what do you remember") == "I can't read my memory file, so I left it alone."
assert j.route("forget everything")[:2] == ("say", None) and "You are JARVIS" in j.system_prompt()
with open(j.MEMORY_FILE, "rb") as f:
    assert f.read() == b"\xff\xfe\xff"
os.remove(j.MEMORY_FILE)

# ---- to-do by voice: asked first, appended to the note (never rewritten, never created), the text kept out of the log
note = os.path.join(tmp, "todo.md")
j.todo_note = lambda: note if os.path.exists(note) else ""
assert j.route("add buy milk to my to-do list")[0] == "say"       # no note set: said, nothing staged
with open(note, "wb") as f:
    f.write(b"- [ ] old")                                         # no line break at the end
assert j.route("Add buy milk to my to-do list.") == ("act", "todo", "buy milk", "Add 'buy milk' to your to-do list? Confirm with yes.")
for text, item in (("put call the bank on my todo list", "call the bank"), ("Add a task: renew passport.", "renew passport"),
                   ("new to-do buy milk", "buy milk"), ("Jarvis, add feed the cat to my tasks", "feed the cat"),
                   ("could you add water the plants to the to do list", "water the plants"),
                   ("Add call Dr Smith to my to-do list", "call Dr Smith")):
    assert j.route(text)[1:3] == ("todo", item), text
for text in ("How do I add a task in Jira?", "what's on my to-do list", "add 2 and 3", "put the kettle on"):
    assert j.route(text)[0] == "chat", text
turns = iter(["Add buy milk to my to-do list.", "No, wait.", "Add buy milk to my to-do list.", "Yes."])
j.listen, j.transcribe = lambda: "audio", lambda a: next(turns)
acted.clear()
j.turn(0)
assert acted == [] and asked[-1] == "Cancelled." and not j.busy.locked()
j.turn(0)
assert acted == ["todo"] and asked[-1] == "Added." and not j.busy.locked()
with open(note, "rb") as f:
    assert f.read() == b"- [ ] old"                               # run_action is a fake here: the note is untouched
j.setting = lambda name, default="": default
j.ACTIONS["todo"]("buy milk")
j.ACTIONS["todo"]("call\nthe   bank")
with open(note, "rb") as f:
    assert f.read() == b"- [ ] old\n- [ ] buy milk\n- [ ] call the bank\n"
logged, keep = [], j.log
j.log = logged.append
assert real_run_action("todo", "secret item") is True and "secret" not in "".join(logged)
os.remove(note)
n = len(said)
assert real_run_action("todo", "secret item") is False and not os.path.exists(note)     # a missing note is not created
assert "secret" not in "".join(logged) + said[-1][0] and tmp not in "".join(logged) + said[-1][0] and len(said) == n + 1
j.log = keep

# personality: one sentence of the prompt follows JarvisPersonality; an unknown or unset value is the playful one
j.context = lambda: ""
for mood, sentence in (("proper", "a little dry"), ("playful", "same spirit"), ("brief", "one short sentence"), ("nonsense", "same spirit")):
    j.setting = lambda name, default="", mood=mood: mood if name == "JarvisPersonality" else default
    assert sentence in j.system_prompt() and j.system_prompt().count("You are JARVIS") == 1, mood
j.setting = lambda name, default="": default
assert "same spirit" in j.system_prompt() and "a little dry" not in j.system_prompt()

# ---- briefing and follow-up, as whole turns with a fake model
for text in ("Good morning.", "good evening jarvis", "Brief me", "Hey Jarvis, daily briefing.", "What's my day look like?"):
    assert j.route(text)[0] == "brief", text
for text in ("Good morning, can you open Chrome?", "brief me on quantum physics", "is it a good morning?"):
    assert j.route(text)[0] == "chat", text
prompts, heard, speaks = [], [0], [0]
j.chat_stream = lambda model, messages: prompts.append(messages[0]["content"])
j.sentences_from = lambda stream, collected: collected.append("Ha.") or iter(["Ha."])
j.speak_all = j.say_text_only = lambda sentences, *a: list(sentences)
j.ollama_on_cpu = lambda model: None


def _listen(**k):
    heard[0] += 1
    return "audio" if heard[0] <= speaks[0] else None


def talk(times, mute=False, follow="1", words="Tell me a joke."):
    """One turn in which you speak up to `times` times in a row: how often the microphone was opened."""
    heard[0], speaks[0] = 0, times
    j.muted, j.listen, j.transcribe = lambda: mute, _listen, lambda a: words
    j.setting = lambda name, default="": follow if name == "JarvisFollowUp" else default
    j.turn(0)
    assert states[-1] == idle and not j.busy.locked()
    return heard[0]


assert talk(1) == 2                                               # he answers, then listens once more and hears nothing
assert talk(99) == 4                                              # three follow-ups in a row, then the wake word again
assert talk(99, mute=True) == 1 and talk(99, follow="0") == 1     # shown instead of spoken, or switched off: none
assert talk(99, words="Set a timer for 10 minutes.") == 4         # fixed replies get them too (live test 3)
j.save_reminders([])
assert "BRIEFING:" not in prompts[-1]
talk(1, words="Good morning.")
assert "BRIEFING:" in prompts[-1] and "at most three" in prompts[-1]
j.setting = lambda name, default="": default

# ---- the name as Whisper writes it: removed only as the first words, so every command works after it
real_time = j.time.time
j.time.time = lambda: 2e9                                         # reminder times compare exactly
clean = ("set the volume to 30", "open chrome", "lock my computer", "remind me to cook in 20 minutes", "mute",
         "set a timer for 10 minutes", "what reminders do I have", "turn it up", "next track", "close chrome")
names = ("Travis, ", "Jervis, ", "Javis, ", "Jarvus, ", "Service, ", "Droves, ", "Drovis, ", "Hey Travis, ", "Hi Jervis ",
         "Okay Travis, ", "OK, Javis. ", "Travis. ", "hey service ", "Jarvis, ", "Hey Droves, ", "Jarvus! ", "Hi, Drovis, ",
         "ok drovis ", "Travis ,", "Okay Jarvus ")
for i, name in enumerate(names):
    text = clean[i % len(clean)]
    assert j.route(name + text) == j.route(text), name + text
j.time.time = real_time
for text in ("play Travis Scott", "Travis Scott is playing", "Service the car", "Travis.", "service"):
    assert j.strip_name(text) == text, text
assert j.route("play Travis Scott")[0] == "chat"
j.setting = lambda name, default="": "Jarbis, Garvis" if name == "JarvisNameAliases" else default
assert j.strip_name("Jarbis, mute") == "mute" and j.strip_name("hey garvis open chrome") == "open chrome"
j.setting = lambda name, default="": default

# ---- alarms: a reminder labelled "alarm" (older code reads it as a plain reminder), set by length or clock time
assert ahead("set an alarm for in one minute") == ahead("Set an alarm for one minute.") == ("alarm", 60, "alarm")
assert ahead("wake me up in 10 minutes") == ("alarm", 600, "alarm") and ahead("set an alarm") == ("alarm", None, "alarm")
assert datetime.fromtimestamp(cmd("alarm at 7 am")[2]).strftime("%H:%M") == "07:00"
assert datetime.fromtimestamp(cmd("Wake me up at 6:30.")[2]).minute == 30
assert cmd("do I have an alarm set") == cmd("Do I have any alarms?") == cmd("what alarms do I have") == ("list", "alarm")
assert cmd("cancel my alarm") == cmd("turn off the alarm") == ("cancel", "alarm", "")
for text in ("wake me up when september ends", "alarm clocks are loud", "what is an alarm", "I set an alarm yesterday"):
    assert cmd(text) is None, text
j.save_reminders([])
assert do("set an alarm for one minute").startswith("Alarm set for ") and do("Wake me up in 10 minutes.").startswith("Alarm set")
assert [r[2:] for r in j.load_reminders()] == [("reminder", "alarm")] * 2
assert do("do I have an alarm set").startswith("You have 2 alarms: ") and do("what reminders do I have") == do("do I have an alarm set")
first = j.load_reminders()[0]
assert j.ring_line(first, first[0]) == "This is your alarm." and j.ring_line(first, first[0] + 600).startswith("Missed alarm from ")
j.listen, j.transcribe = lambda: "audio", lambda a: "Both."         # two alarms: he asks which (Round 4)
assert do("cancel my alarm").startswith("Cancelled: ") and j.load_reminders() == [] and asked[-1].endswith("Which one?")
assert do("cancel my alarm") == "I don't see an alarm like that."

# ---- more ways to say the volume; the reply is still what Windows reports
for phrase, want in (("set the volume to thirty", ("set", 30)), ("volume 30", ("set", 30)), ("set it to 30", ("set", 30)),
                    ("Travis, set the volume to thirty.", ("set", 30)), ("turn it down a bit", ("step", -10)),
                    ("a little louder", ("step", 10)), ("turn the volume up a little", ("step", 10)),
                    ("slightly quieter", ("step", -10)), ("make it a bit louder", ("step", 10)), ("max volume", ("set", 100)),
                    ("set the volume to max", ("set", 100)), ("half volume", ("set", 50)), ("volume to half", ("set", 50)),
                    ("set the volume to twenty five percent", ("set", 25)), ("turn it all the way up", ("set", 100)),
                    ("set volume to eighty", ("set", 80)), ("set the volume to a hundred", ("set", 100))):
    assert j.route(phrase)[:3] == ("act", "volume", want), (phrase, j.route(phrase))
assert j.route("set the volume to two hundred")[0] != "act" and j.route("set it to five minutes")[0] != "act"

# ---- he never claims an action: a command no parser took gets a fixed line, and the model is not asked
for text in ("Change the screen colour to blue.", "turn on bluetooth", "set the brightness to 50",
             "set the volume to 30 decibels", "Travis, connect my headphones", "please open the settings app"):
    assert j.route(text) == ("say", None, None, j.NEAR_MISS), (text, j.route(text))
for text in ("how do I change the volume on my phone?", "what timer should I buy", "can you explain how to set an alarm",
             "why won't my bluetooth connect", "I set an alarm yesterday", "who can change the brightness", "play Travis Scott"):
    assert j.route(text)[0] == "chat", text
n = len(prompts)
talk(1, words="Change the screen colour to blue.")
assert len(prompts) == n and asked[-1] == j.NEAR_MISS
for s in ("Alarm set for 5 pm.", "I've turned the volume up.", "Volume is now 30 percent.", "I have set a reminder.",
          "Reminder added.", "I’ve opened Chrome.", "Done, I've muted it."):
    got = []
    assert list(j.no_claims(iter(["Sure.", s, "More."]), got)) == ["Sure.", j.CLAIM_LINE] and got == [j.CLAIM_LINE], s
for s in ("You can set an alarm on your phone.", "Set a timer for that.", "The volume knob is on the left."):
    assert list(j.no_claims(iter([s]), [])) == [s], s
keep_sf, keep_sa, spoken = j.sentences_from, j.speak_all, []
j.sentences_from = lambda stream, collected: collected.append("Alarm set for 5 pm.") or iter(["Alarm set for 5 pm."])
j.speak_all = lambda sentences, *a: spoken.extend(sentences)
convo.clear()
talk(1, words="Wake me at sunrise.")                              # no clock time: not an alarm, so the model answers
assert spoken == [j.CLAIM_LINE] and convo[-1] == ("J", j.CLAIM_LINE)
j.sentences_from, j.speak_all = keep_sf, keep_sa
assert "Never say you set or changed something." in j.system_prompt() and "You cannot set alarms" not in j.system_prompt()

# ---- the voice: one failure is retried at once; failing twice uses the Windows voice for 60 s, then tries again
model_file = os.path.join(tmp, "kokoro-v1.0.onnx")
open(model_file, "w").close()
calls, fails = [], [1]


def _kokoro(path, text):
    calls.append(text)
    if fails[0]:
        fails[0] -= 1
        raise RuntimeError("secret detail")
    return ("kokoro", text)


j.synth_audio, j._kokoro, j._windows, j.resolve_voice = real_synth_audio, _kokoro, lambda text: ("windows", text), lambda v: v
j.setting = lambda name, default="": model_file if name == "JarvisVoice" else default
n = len(said)
assert j.synth_audio("hi") == ("kokoro", "hi") and len(calls) == 2 and len(said) == n     # failed once: retried, no problem
assert j.synth_audio("hi") == ("kokoro", "hi") and len(calls) == 3
fails[0] = 2
assert j.synth_audio("hi") == ("windows", "hi") and len(calls) == 5 and len(said) == n + 1 and "secret" not in said[-1][0]
assert j.synth_audio("hi") == ("windows", "hi") and len(calls) == 5                     # not tried again within 60 s
j.time.time = lambda: real_time() + 61
assert j.synth_audio("hi") == ("kokoro", "hi") and len(calls) == 6
j.time.time = real_time
j.synth_audio, j.setting = lambda text: (text, 1), lambda name, default="": default

# ---- answers by code: the clock, dates, sums and conversions never reach the model
j.time.time = lambda: datetime(2026, 10, 14, 15, 5).timestamp()   # a Wednesday afternoon
for text, want in (("What time is it?", "It's 3:05 PM."), ("what's the time", "It's 3:05 PM."),
                   ("Jarvis, can you tell me the time?", "It's 3:05 PM."), ("What's the date?", "It's Wednesday, October 14."),
                   ("what day is it today", "It's Wednesday."), ("what day is the 3rd", "November 3 is a Tuesday."),
                   ("How many days until Friday?", "2 days until Friday, October 16."),
                   ("how many days until December 25th", "72 days until Friday, December 25."),
                   ("what's the date in 2 weeks", "That's Wednesday, October 28."),
                   ("What's 12 times 9?", "108."), ("twelve times nine", "108."), ("What's 15 percent of 240?", "36."),
                   ("what is 15% of 240", "36."), ("240 divided by 7", "About 34.3."), ("square root of 81", "9."),
                   ("what's 2 to the power of 10", "1024."), ("1,000 plus 250", "1250."), ("7 squared", "49."),
                   ("what is 10 minus 12.5", "-2.5."),
                   ("How many km in 26 miles?", "About 41.8 kilometres."),
                   ("how many kilometres is 26 miles", "About 41.8 kilometres."),
                   ("5 feet 10 in centimetres", "177.8 centimetres."),
                   ("100 fahrenheit in celsius", "About 37.8 degrees Celsius."), ("200 grams in ounces", "About 7.05 ounces."),
                   ("2 hours in seconds", "7200 seconds."), ("convert 60 mph to km/h", "About 96.6 kilometres per hour."),
                   ("how many feet in a mile", "5280 feet."), ("1 gigabyte in megabytes", "1000 megabytes.")):
    assert j.route(text) == ("fact", None, None, want), (text, j.route(text))
assert j.route("what's 2 to the power of 9999999")[3] == "That number is too big to say."
assert j.route("what's 5 divided by zero")[3] == "You can't divide by zero."
for text in ("what is the time complexity of quicksort", "what's 2 plus 3 times 4", "what is x times y",
             "how many people live in Paris", "3 km plus 2 miles", "what day is christmas", "26 miles in pounds",
             "what is love", "how many days until my birthday", "what's 12 times the speed of light"):
    assert j.route(text)[0] == "chat", (text, j.route(text))
n = len(prompts)
talk(1, words="What's 12 times 9?")
assert len(prompts) == n and asked[-1] == "108."
j.time.time = real_time

# ---- "undo that": one change, for 2 minutes, put back to what Windows had before
j.run_action, j.speakers, vol[0], ran[:] = real_run_action, _speakers, 45, []
j.undo.clear()                                                     # left by the tests above
assert j.route("undo that") == j.route("Jarvis, undo.") == j.route("put it back") == ("undo", None, None, None)
assert j.undo_last() == "There's nothing to undo."
assert j.run_action("volume", ("set", 30)) and vol == [30]
assert j.undo_last() == "Volume back at 45 percent." and vol == [45]
assert j.undo_last() == "There's nothing to undo." and vol == [45]
assert j.run_action("volume", ("step", 10)) and vol == [55]
j.time.time = lambda: real_time() + 121
assert j.undo_last() == "There's nothing to undo." and vol == [55]
j.time.time = real_time
assert j.run_action("lock", None) and j.undo_last() == "I can't undo that."
j.save_reminders([])
do("set a timer for 10 minutes")
assert j.undo_last() == "Removed that timer." and j.load_reminders() == []
j.save_memory([])
j.memory_reply("save", "my bike is blue")
assert j.undo_last() == "Forgotten: my bike is blue." and j.load_memory() == []
n = len(ran)
talk(2, words="shut down the PC")                                  # asked, the answer is not a yes: cancelled
assert asked[-1] == "Cancelled." and len(ran) == n and j.undo_last() == "There's nothing to undo."

# ---- "what did you hear?" and "say that again": memory only
talk(1, words="Tell me a joke.")
talk(1, words="What did you hear?")
assert asked[-1] == "I heard: Tell me a joke."
talk(1, words="Say that again.")
assert asked[-1] == "Ha."

# ---- live test of phase 1: a word before the command, more ways to ask for an alarm, "never mind", the volume read
# from Windows every time it is asked, and a longer wait for a follow-up
for text in ("then change the volume to 30%.", "And set the volume to 30.", "Okay, set the volume to 30", "so, set volume to 30"):
    assert j.route(text) == ("act", "volume", ("set", 30), None), text
for text in ("Set me an alarm for one minute.", "Set up an alarm for one minute", "Create an alarm for 1 minute.",
             "Set an alarm for one minute from now.", "Then set an alarm for one minute.", "Okay, set an alarm for 1 minute"):
    assert ahead(text) == ("alarm", 60, "alarm"), (text, j.route(text))
for text in ("Set a timer for actually don't set a timer.", "Set a timer for... never mind.", "Never mind.",
             "Set an alarm, never mind", "actually, don't set a timer"):
    assert j.route(text) == ("say", None, None, "Okay, never mind."), text
j.save_reminders([])
for answer, op, want in (("Never mind.", "set a timer", "Okay, no timer."), ("No.", "set an alarm", "Okay, no alarm."),
                         ("Cancel that.", "remind me to cook", "Okay, no reminder."), ("forget it", "set a timer", "Okay, no timer.")):
    j.listen, j.transcribe = lambda: "audio", lambda a: answer
    assert do(op) == want and j.load_reminders() == [], (answer, do(op))
j.speakers, vol[0] = _speakers, 45
for text in ("What's the volume?", "what is the volume at", "How loud is it?", "Is it muted?", "what's the volume set to"):
    assert j.route(text) == ("level", None, None, None), text
assert j.route("what volume is 30 decibels")[0] == "chat"
talk(1, words="What's the volume?")
assert asked[-1] == "The volume is at 45 percent."
vol[0] = 70                                                        # changed by hand in Windows: read again, not remembered
talk(1, words="What's the volume?")
assert asked[-1] == "The volume is at 70 percent."
waits = []
real_listen = _listen
_listen = lambda **k: waits.append(k.get("patience")) or real_listen()
talk(1)
assert waits == [None, 10.0], waits                               # the first listen as before; the follow-up waits 10 s
j.setting = lambda name, default="": "99" if name == "JarvisFollowUpWait" else default
assert j.follow_wait() == 30.0
j.setting = lambda name, default="": default

# ---- live test 2: more ways to ask for the volume and about an alarm; an alarm is never called a timer
for text, want in (("Can you change the volume to 30 please?", ("set", 30)), ("Change the volume to 30 percent please.", ("set", 30)),
                   ("Turn the volume up to 50.", ("set", 50)), ("Turn the volume down to 20%.", ("set", 20)),
                   ("Raise the volume to 60.", ("set", 60)), ("I want the volume at 40.", ("set", 40)),
                   ("Put the volume on 40.", ("set", 40)), ("Set the volume at 30%, please.", ("set", 30)),
                   ("Lower the volume.", ("step", -10)), ("Increase the volume.", ("step", 10)),
                   ("Could you decrease the sound a bit?", ("step", -10)), ("Volume up.", ("step", 10))):
    assert j.route(text) == ("act", "volume", want, None), (text, j.route(text))
for text in ("When is my alarm?", "How long until my alarm?", "Is my alarm set?"):
    assert cmd(text) == ("list", "alarm"), (text, j.route(text))
j.save_reminders([])
do("set an alarm for 7 am"), do("set an alarm for 8 am"), do("set a timer for 10 minutes")
assert do("cancel the alarm for 7").startswith("Cancelled: alarm at 7:00 AM") and len(j.load_reminders()) == 2
assert do("Remove my 8 am alarm.").startswith("Cancelled: alarm at 8:00 AM") and len(j.load_reminders()) == 1
do("set an alarm for 7 am"), do("set an alarm for 8 am")
j.listen, j.transcribe = lambda: "audio", lambda a: "All of them."  # two alarms: he asks which (Round 4)
assert do("Delete the alarm I set.").count("alarm at") == 2 and [r[2] for r in j.load_reminders()] == ["timer"]
do("set an alarm for 7 am")
said_back = do("cancel the reminder")                              # one schedule: no reminder, so the one alarm goes
assert said_back.startswith("Cancelled: alarm at 7:00 AM") and [r[2] for r in j.load_reminders()] == ["timer"], said_back
j.save_reminders([])

# ---- live test 3: clock words and 24-hour times, several alarms at once, "no, AM" just after, a cancel put back,
# a follow-up after commands and after "didn't catch", and code replies kept in the chat history
for text, want in (("at 7 o'clock", "13 19:00"), ("at 7 in the morning", "14 07:00"), ("at 7 tonight", "13 19:00"),
                   ("at seven am", "14 07:00"), ("at seven thirty pm", "13 19:30"), ("at 1900 hours", "13 19:00"),
                   ("at 0700 hours", "14 07:00"), ("at 07:00", "14 07:00"), ("at nineteen hundred hours", "13 19:00"),
                   ("at noon", "14 12:00"), ("at midnight", "14 00:00"), ("at 7 a.m. tomorrow", "14 07:00"),
                   ("at 9 tomorrow", "14 09:00"), ("at tomorrow at 9 pm", "14 21:00"), ("at 6 in the evening", "13 18:00")):
    assert hm(text) == want, (text, hm(text))
for text in ("at 2 hours", "at a picture", "at 7 and 8", "at seven minutes", "at the stars at 9"):
    assert j.when(text, at3) is None, text
assert datetime.fromtimestamp(j.when("at 7", at3 + 6 * 3600)).strftime("%d %H:%M") == "14 07:00"   # from 9 PM: the morning
for text in ("set an alarm for 1900 hours", "Set an alarm for 7 o'clock.", "set an alarm for 7 in the morning",
             "set an alarm for seven am", "set an alarm for 7 tonight", "set an alarm for 7 a.m. tomorrow",
             "yo can you set an alarm for 7", "I need an alarm at 7"):
    assert cmd(text)[:2] == ("set", "alarm") and cmd(text)[2] is not None, (text, j.route(text))
assert cmd("set an alarm for 1900 hours")[2] - time.time() <= 86400                     # never "in 1900 hours"
two = cmd("hey set an alarm for 7 and 8 am")
assert [datetime.fromtimestamp(d).strftime("%H:%M") for d in two[2]] == ["07:00", "08:00"], two
j.save_reminders([])
said_back = do("set alarms for 7 and 8 am")
assert said_back.startswith("Alarms set for 7:00 AM") and "and 8:00 AM" in said_back and len(j.load_reminders()) == 2
assert j.undo_last() == "Removed those 2 alarms." and j.load_reminders() == []
# "no, AM": the alarm just set moves 12 hours; with nothing just set it is not a correction
assert j.route("No, AM.")[1] != "flip"
do("set an alarm for 7 pm")
assert j.route("No, AM.") == j.route("I meant the morning") == ("remind", "flip", ("alarm", "am"), None)
assert j.route("Morning.")[1] != "flip"
assert do("no, in the morning").startswith("Changed to 7:00 AM") and datetime.fromtimestamp(j.load_reminders()[0][0]).hour == 7
assert do("make it pm").startswith("Changed to 7:00 PM") and do("PM").startswith("It's already set for 7:00 PM")
assert len(j.load_reminders()) == 1
# a cancel is put back by "undo that"
j.save_reminders([])
do("set an alarm for 7 am"), do("set a timer for 10 minutes")
assert do("cancel my alarm").startswith("Cancelled: alarm at 7:00 AM") and len(j.load_reminders()) == 1
assert j.undo_last().startswith("Put back: alarm at 7:00 AM") and len(j.load_reminders()) == 2
assert j.undo_last() == "There's nothing to undo."
# two commands in one sentence: done one after the other when each is safe on its own
both = j.route("set an alarm for 7 am and remind me to cook in 10 minutes")
assert both[0] == "multi" and [p[:2] for p in both[2]] == [("remind", "set"), ("remind", "set")], both
assert j.route("cancel my alarm and set one for 8")[3] == j.NEAR_MISS
for text in ("lock my computer and mute", "tell me a joke and set a timer", "set a timer and set an alarm for 7"):
    assert j.route(text)[0] != "multi", text
j.save_reminders([])
talk(1, words="Set an alarm for 7 am and set a timer for 10 minutes.")
assert asked[-1].startswith("Alarm set for 7:00 AM") and "Timer set for 10 minutes." in asked[-1] and len(j.load_reminders()) == 2
# follow-ups: after a command, not after "never mind", and once after words that could not be made out
assert talk(1, words="Set a timer for 10 minutes.") == 2 and talk(99, words="Never mind.") == 1
assert j.history[-1] == {"role": "assistant", "content": "Okay, never mind."} and j.history[-2]["content"].endswith("] Never mind.")
assert j.re.match(r"\[\w{3} \d\d \w{3}, \d\d:\d\d [AP]M\] ", j.history[-2]["content"]), j.history[-2]   # day, date and time
assert talk(1, words="") == 2 and asked[-1] == "Sorry, I didn't catch that."
assert talk(99, words="") == 2                                    # silence after "didn't catch" ends it: no loop
j.save_reminders([])
j.undo.clear()

# ---- one schedule: alarms and reminders are listed and cancelled together; timers stay apart
do("set an alarm for 7 am"), do("remind me to cook in 20 minutes"), do("set a timer for 10 minutes")
listed = do("what reminders do I have")
assert listed.startswith("You have 1 alarm and 1 reminder: ") and "alarm at 7:00 AM" in listed and "to cook" in listed, listed
assert do("what alarms do I have") == listed and do("list my timers").startswith("You have 1 timer: ")
assert do("cancel the cooking alarm").startswith("Cancelled: to cook at ")          # found by its words, whatever the noun
j.undo_last()
assert do("Cancel all reminders.").count(";") == 1 and [r[2] for r in j.load_reminders()] == ["timer"]
assert j.undo_last().startswith("Put back: ") and len(j.load_reminders()) == 3
assert do("cancel the reminder for 7").startswith("Cancelled: alarm at 7:00 AM")      # by clock time, either kind
j.save_reminders([])
assert do("what alarms do I have") == "You have no alarms or reminders."

# ---- the AI fallback: only for a near-miss, or a chat line with a command word that is not a question. The model
# names the intent and copies the words; code checks they were said, builds a fixed sentence, route() must agree
real_http = j.http_json


def ai(cmds, raw=None):
    j.http_json = lambda path, payload=None, timeout=5: {"message": {"content": raw or j.json.dumps({"commands": cmds})}}


ai([{"intent": "alarm_set", "when": "at 7"}, {"intent": "alarm_set", "when": "8 am"}])
two = j.interpret("m", "I'd love alarms at 7 and 8 am")
assert two[:2] == ("remind", "set") and [datetime.fromtimestamp(d).strftime("%H:%M") for d in two[2][1]] == ["07:00", "08:00"], two
ai([{"intent": "alarm_set", "when": "at 7"}, {"intent": "reminder_set", "label": "to cook", "when": "in 10 minutes"}])
both = j.interpret("m", "get me up at 7 and ping me to cook in 10 minutes")
assert both[0] == "multi" and [p[2][0] for p in both[2]] == ["alarm", "reminder"] and both[2][1][2][2] == "to cook", both
ai([{"intent": "volume_step"}])
assert j.interpret("m", "knock the volume down a notch") == ("act", "volume", ("step", -10), None)
ai([{"intent": "media", "label": "next"}])
assert j.interpret("m", "bin this song") == ("act", "media", "next", None)
for text, cmds in (("wake me at 7", [{"intent": "alarm_set", "when": "at 7 am"}]),               # an invented am
                   ("set the brightness to 50", [{"intent": "volume_set", "number": 50}]),      # no volume word said
                   ("bump the sound up", [{"intent": "volume_set", "number": 40}]),             # a number not said
                   ("shut down the pc", [{"intent": "shutdown"}]),                              # not on its list
                   ("alarm clocks are loud", [{"intent": "chat"}]),
                   ("set an alarm and a timer", [{"intent": "alarm_set"}, {"intent": "timer_set"}])):   # each would ask
    ai(cmds)
    assert j.interpret("m", text) is None, text
for raw in ("not json", '{"commands": "x"}', "{}"):
    ai(None, raw)
    assert j.interpret("m", "wake me at 7") is None, raw
j.http_json = real_http
j.OLLAMA = "http://127.0.0.1:9"                                    # nothing listens there: down, never a hang
assert j.interpret("m", "wake me at 7") is None
for text, routed in (("get me up at 7", ("chat", None, None, None)), ("Change the screen colour to blue.", j.route("Change the screen colour to blue."))):
    assert j.ask_ai(text, routed), text
for text in ("should I set an alarm?", "I set an alarm yesterday", "what's a good alarm sound", "Tell me a joke.",
             "can you explain how volume works", "Is the music too loud?", "tell me about alarms"):
    assert not j.ask_ai(text, ("chat", None, None, None)), text
j.setting = lambda name, default="": "0" if name == "JarvisAIRouter" else default
assert not j.ask_ai("get me up at 7", ("chat", None, None, None))                # switched off: exactly as before
j.setting = lambda name, default="": default
# a whole turn: the AI's alarm is set and said back by code; with the AI down the model answers as before
ai([{"intent": "alarm_set", "when": "at seven thirty"}])
real_filler, said_fillers = j.filler, []
j.filler = lambda key, quiet: said_fillers.append(key)
talk(1, words="Get me up at seven thirty.")
assert asked[-1].startswith("Alarm set for 7:30") and len(j.load_reminders()) == 1, asked[-1]
assert said_fillers == ["confirm_wait"], said_fillers                # "One moment." while the AI reads it
talk(1, words="Set an alarm for 9 am.")                               # understood at once: no AI, no filler
assert said_fillers == ["confirm_wait"] and len(j.load_reminders()) == 2
j.filler = real_filler
j.save_reminders([])
j.http_json = lambda *a, **k: (_ for _ in ()).throw(OSError("down"))
n = len(prompts)
talk(1, words="Get me up at seven thirty.")
assert len(prompts) == n + 1 and j.load_reminders() == []
j.save_reminders([])
j.undo.clear()
j.http_json = real_http

# ---- Round 4: spoken clock forms, weekdays, "which one?", duplicates, move, snooze, enders, phantoms, "by N"
for text, want in (("at half past six", "13 18:30"), ("at quarter to 8", "13 19:45"), ("at quarter past 7", "13 19:15"),
                   ("at quarter to 1", "14 00:45"), ("on Monday at 7", "19 07:00"), ("next Friday at 9 am", "16 09:00"),
                   ("at 7 tomorrow morning", "14 07:00"), ("at 6 tomorrow night", "14 18:00"),
                   ("on Tuesday at 2", "20 02:00"),                    # today's weekday, time gone: next week, under 7 days
                   ("on Tuesday at 4", "13 16:00"), ("tomorrow at 9", "14 09:00")):
    assert hm(text) == want, (text, hm(text))
assert j.duration("a minute and a half") == 90 and j.duration("an hour and a half") == 5400
tomorrow9 = lambda due: datetime.fromtimestamp(due).strftime("%H:%M") == "09:00" and 0 < due - time.time() < 2 * 86400
for text, label in (("remind me to call mom tomorrow at 9", "to call mom"), ("remind me tomorrow at 9 to call mom", "to call mom"),
                    ("remind me on Friday at 9 to pay rent", "to pay rent")):
    _, op, (kind, due, got, said), _ = j.route(text)
    assert (op, kind, got) == ("set", "reminder", label) and datetime.fromtimestamp(due).strftime("%H:%M") == "09:00", text
assert tomorrow9(j.route("remind me to call mom tomorrow at 9")[2][1])
assert cmd("what time is my alarm set for") == ("list", "alarm")
assert j.route("turn it up by 20") == ("act", "volume", ("step", 20), None)
assert j.route("turn the volume down by 5")[2] == ("step", -5) and j.route("turn it up by banana")[0] == "chat"

# cancel with two alarms asks which; the answer picks one, both, or none
j.save_reminders([])
j.undo.clear()


def which(text, answer):
    j.listen, j.transcribe = lambda: "audio", lambda a: answer
    return do(text)


do("set an alarm for 7 am"), do("set an alarm for 8 am")
assert which("turn off my alarm", "the 7").startswith("Cancelled: alarm at 7:00 AM") and asked[-1].endswith("Which one?")
assert len(j.load_reminders()) == 1 and j.undo_last().startswith("Put back: alarm at 7:00 AM")
assert which("turn off my alarm", "nothing") == "Okay, I left them." and len(j.load_reminders()) == 2
assert which("turn off my alarm", "both").count(";") == 1 and j.load_reminders() == []
j.undo_last()
assert do("cancel my alarms").count(";") == 1 and j.load_reminders() == []               # plural: all, no question
j.undo_last()
# the same alarm twice is kept once
assert do("set an alarm for 7 am") == "You already have an alarm for 7:00 AM." and len(j.load_reminders()) == 2
# move: asks which with two, moves one, undo puts it back
assert which("move my alarm to 9 am", "the 8").startswith("Moved your 8:00 AM alarm to 9:00 AM")
assert sorted(datetime.fromtimestamp(r[0]).strftime("%H:%M") for r in j.load_reminders()) == ["07:00", "09:00"]
assert j.undo_last().startswith("Put back: alarm at 8:00 AM")
assert sorted(datetime.fromtimestamp(r[0]).strftime("%H:%M") for r in j.load_reminders()) == ["07:00", "08:00"]
assert which("change my alarm to 9", "") == "Okay, I left them." and asked[-1].endswith("Which one?")
j.save_reminders([])
do("set a timer for 10 minutes")
before = j.load_reminders()[0][0]
assert do("add 5 minutes to the timer").startswith("The timer now has 15 minutes") and j.load_reminders()[0][0] == before + 300
assert do("make the timer 2 minutes").startswith("The timer now has 2 minutes")
assert j.undo_last().startswith("Put back: ") and j.load_reminders()[0][0] == before + 300
j.save_reminders([])
j.undo.clear()
# snooze after the ringing stopped: only within 5 minutes of something ringing
j.rang.clear()
assert do("snooze for 10 minutes") == "Nothing is ringing right now." and j.load_reminders() == []
j.rang[:] = [time.time(), [(time.time() - 5, time.time() - 600, "reminder", "to cook")]]
assert do("snooze for 10 minutes") == "Snoozed for 10 minutes." and [r[2:] for r in j.load_reminders()] == [("reminder", "to cook")]
assert abs(j.load_reminders()[0][0] - time.time() - 600) < 5 and j.rang == []     # the file keeps whole seconds
assert do("snooze for 10 minutes") == "Nothing is ringing right now."
assert j.CLAIM.search("I've snoozed your alarm.") and j.CLAIM.search("Your alarm has been snoozed.")
j.save_reminders([])
j.undo.clear()

# enders end a follow-up without a reply; a turn you started still gets one; phantoms are silence
n = len(prompts)
assert talk(99, words="Thanks.") == 2 and len(prompts) == n + 1                  # answered once, then "thanks" ends it
for words in ("Okay, thanks Jarvis!", "That’s all.", "no thank you", "Nope.", "I'm good."):
    assert j.ENDERS.fullmatch(" ".join(j.re.sub(r"[^a-z' ]", " ", words.lower().replace("’", "'")).split())), words
for words in ("no am", "no, set it for 8", "thanks for the help with my essay"):
    assert not j.ENDERS.fullmatch(" ".join(j.re.sub(r"[^a-z' ]", " ", words.lower()).split())), words
real_whisper = j.whisper
for phrase, want in (("Thanks for watching!", ""), (" you", ""), ("Subtitles by the Amara.org community", ""), ("...", ""),
                     ("Thank you.", "Thank you."), ("you said seven", "you said seven"), ("open chrome", "open chrome")):
    j.whisper = lambda: types.SimpleNamespace(transcribe=lambda a, **k: ([types.SimpleNamespace(text=phrase)], None))
    assert real_transcribe("audio") == want, phrase
j.whisper = real_whisper                                          # an empty transcript is already silence in turn()

print("test_jarvis: OK")
