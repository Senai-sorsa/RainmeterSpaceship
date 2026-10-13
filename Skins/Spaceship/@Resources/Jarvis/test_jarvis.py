"""Self-check for jarvis.py: plain asserts, no test framework.  Run:  py -3 -B test_jarvis.py"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jarvis as j

# no disk, no sound card, no processes: fixed app list, fixed window list, recorded mute calls and commands
real_start_apps = j.start_apps
j.start_apps = lambda: [("Google Chrome", "Chrome"), ("Microsoft Edge", "MSEdge"), ("Notepad", "notepad")]
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
assert "Timers and reminders pending: 1, the next at " in got and "cook" not in got, got   # how many and when, not what
for line in ("CPU temperature: 61 C", "CPU load: 75%", "GPU load: 37%, video memory 2.0 of 8 GB in use",
             "Speaker volume: 100%", "Screen brightness: 70%", "GB free of"):
    assert line in got, (line, got)
assert "GPU temperature" not in got and "Fan 1" not in got and "Microphone" not in got, got
j.subprocess.run, j.read_kv = _hang, lambda name: "T 5\nBRIGHT 70\n"
got = j.sensors()                                                 # nvidia-smi hangs, the HUD's file is old, no CPU sample
assert "CPU temperature: 61 C" in got and not [x for x in ("GPU load", "brightness", "CPU load") if x in got], got
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
j._whisper = None
j.whisper()
assert made == [j.cpu_threads()] and 2 <= made[0] <= max(2, (os.cpu_count() or 8) // 4)
assert len(said) == 1 and said[0][0].startswith("CPU in use") and said[0][1] is False
j.setting = lambda name, default: "gpu" if name == "JarvisWhisperDevice" else default     # a mistyped device
j._whisper = None
j.whisper()
assert "JarvisWhisperDevice=gpu" in said[-1][0], said[-1]

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
j.synth_audio = lambda text: (text, 1)
j.play_samples = lambda a, rate: played.append(a)
many = [str(i) for i in range(20)]

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
j._listen = lambda: "audio"
assert j.listen() == "audio" and not j.mic.locked()
j._listen = lambda: _no_voice("")
assert isinstance(within(2, j.listen), RuntimeError) and not j.mic.locked()

# a whole turn: every way out ends idle with the turn lock free
j.missing_packages, j.ensure_ollama, j.pick_model, j.warm = lambda: [], lambda: True, lambda tier: "m", lambda m: None
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
assert cmd("Cancel all reminders.") == ("cancel", "reminder", "") and cmd("stop the timer") == ("cancel", "timer", "")
assert cmd("cancel the timer for the pasta") == ("cancel", "timer", "the pasta")

# clock times, from 3 PM: the next time the clock shows it; anything unreadable is None, never a guess
at3 = datetime(2026, 10, 13, 15, 0).timestamp()


def hm(text):
    due = j.when(text, at3)
    return due and datetime.fromtimestamp(due).strftime("%d %H:%M")


for text, want in (("at 6:30 pm", "13 18:30"), ("at 18:30", "13 18:30"), ("at 6 30", "13 18:30"), ("at 7", "13 19:00"),
                   ("at 2", "14 02:00"), ("at 9 a.m.", "14 09:00"), ("at 12", "14 00:00"), ("at 12 pm", "14 12:00"),
                   ("at 25", None), ("at 6:75", None), ("at seven", None), ("in a bit", None), ("in 0 minutes", "13 15:00")):
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
assert do("cancel the cooking reminder") == "I don't see a reminder like that."
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


def _listen():
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
assert talk(99, words="Set a timer for 10 minutes.") == 1         # fixed replies get none
j.save_reminders([])
assert "BRIEFING:" not in prompts[-1]
talk(1, words="Good morning.")
assert "BRIEFING:" in prompts[-1] and "at most three" in prompts[-1]
j.setting = lambda name, default="": default

print("test_jarvis: OK")
