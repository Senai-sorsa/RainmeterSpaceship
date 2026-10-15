"""
JARVIS - voice assistant service for the Spaceship HUD.

Click the hologram -> chime -> it listens (stops when you stop talking) -> Whisper turns your speech into text
-> your local Ollama model answers, knowing what the HUD knows (time, calendar, Gmail, to-dos, open apps,
battery, memory, network) -> it speaks the answer sentence by sentence while the hologram moves with its voice.

Talks to the HUD through two small files in @Resources\\Data (no network port, so nothing else can trigger it):
  jarvis.txt      written here:   T <unix> | STATE idle|listening|thinking|speaking | LEVEL <0-1> | SAY | ERR |
                                  POP <n> open|close  (ask the HUD to open / close the conversation pop-up)
  jarvis_cmd.txt  written by HUD: WAKE <unix> <tier>  |  CANCEL <unix>  |  FORGET <unix>  |  TRAINWAKE <unix>  |  QUIT <unix>
  jarvis_env.txt  written by HUD: MUTED 0|1  - with the speakers muted Jarvis answers in the pop-up, not out loud
  jarvis_log.txt / jarvis_live.txt  the conversation (and the reply in progress) for the pop-up

Started by the HUD (pyw.exe jarvis.py "<@Resources>"); one copy at a time; exits by itself when Rainmeter closes.
Needs:  Python 3.10+,  pip install faster-whisper sounddevice numpy,  Ollama with a model pulled.
Voices: Kokoro-82M (pip install kokoro-onnx + kokoro-v1.0.onnx and voices-v1.0.bin in the same folder - the old
kokoro-v0_19.onnx is NOT supported; default voice bm_lewis), a Piper
voice (.onnx), or the built-in Windows voice as the always-available fallback.
Settings (Settings.inc, all adjustable in Control Center > JARVIS): JarvisModel, JarvisModelFast (used while the HUD
is on its LITE / LOW tiers, i.e. the GPU is busy), JarvisWhisper, JarvisWhisperDevice, JarvisVoice, JarvisVoiceRate,
JarvisKokoroVoice, JarvisChime, JarvisMutedPopup, JarvisKeepAlive, JarvisContext (model memory in tokens),
JarvisSilence (seconds of silence before he answers, default 1), JarvisFirstWords (he starts speaking after this many
words, default 5; 0 = wait for a whole sentence), ObsidianTodo (open to-dos), JarvisProfile ("about me" note),
JarvisVault (Obsidian vault folder for "search my notes" - default: the to-do note's folder).
JarvisSmartSearch (1 = ChromaDB meaning-based note search, falls back to keywords), JarvisWakeWord (default 1 = say "Hey Jarvis" instead of clicking; 0 = off), JarvisWakeSensitivity (0.2-0.9, lower = more sensitive), JarvisIdleUnload (minutes without a turn before the speech models are freed, default 10; 0 = keep them loaded).
JarvisMic (part of the microphone's name; empty = the Windows default), JarvisDuck (default 1 = other sound goes down
while he listens; 0 = off), JarvisDuckLevel (how far down, % of the volume it was, 10-80, default 30).
JarvisBargeIn (off | wake = "Hey Jarvis" stops him mid-sentence, the default | voice = any speech stops him, headphones
only), JarvisStopKey (end = the End key stops him while he is busy, the default; off).
Skills: instant status phrases while searching, a whitelist of actions (risky ones need a spoken "yes"), and
guardrails - nothing outside the whitelist is ever executed.
Every problem is logged to Data\\jarvis.log, shown on the hologram (ERR) and added to the conversation pop-up.
"""
import ctypes
import gc
import json
import math
import msvcrt
import os
import queue
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
import wave
from collections import Counter, namedtuple
from datetime import datetime, timedelta

RES = (sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")).strip().strip('"')
RES = os.path.abspath(RES)
DATA = os.path.join(RES, "Data")
STATE_FILE = os.path.join(DATA, "jarvis.txt")
CMD_FILE = os.path.join(DATA, "jarvis_cmd.txt")
ENV_FILE = os.path.join(DATA, "jarvis_env.txt")      # written by the HUD: MUTED 0|1
CONVO_FILE = os.path.join(DATA, "jarvis_log.txt")    # the conversation the log pop-up shows (U|unix|text, J|unix|text)
LIVE_FILE = os.path.join(DATA, "jarvis_live.txt")    # the reply being written right now
LOG_FILE = os.path.join(DATA, "jarvis.log")
MODELS_FILE = os.path.join(DATA, "jarvis_models.txt")   # installed Ollama models, for the Control Center
MICS_FILE = os.path.join(DATA, "jarvis_mics.txt")       # input devices, for the Control Center
DUCK_FILE = os.path.join(DATA, "jarvis_duck.txt")       # "old lowered" volume while he listens with other sound down
OLLAMA = "http://127.0.0.1:11434"
NO_WINDOW = 0x08000000

os.makedirs(DATA, exist_ok=True)
for _name in ("stdout", "stderr"):                              # pyw.exe has no console, and libraries that print crash on None
    if getattr(sys, _name) is None:
        setattr(sys, _name, open(os.devnull, "w"))


# ------------------------------------------------------------------ logging + settings
def log(msg):
    try:
        if os.path.exists(LOG_FILE) and os.path.getsize(LOG_FILE) > 512_000:
            os.replace(LOG_FILE, LOG_FILE + ".old")
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(datetime.now().strftime("%Y-%m-%d %H:%M:%S  ") + str(msg) + "\n")
    except OSError:
        pass


_settings_cache = (0.0, {})


def settings():
    """Settings.inc as a dict (re-read at most once a second; copes with UTF-8, ANSI or UTF-16 files)."""
    global _settings_cache
    if time.time() - _settings_cache[0] < 1.0:
        return _settings_cache[1]
    out = {}
    try:
        with open(os.path.join(RES, "Settings.inc"), "rb") as f:
            raw = f.read()
        text = raw.decode("utf-16") if raw[:2] in (b"\xff\xfe", b"\xfe\xff") else raw.decode("utf-8", errors="ignore")
        for line in text.splitlines():
            m = re.match(r"\s*([A-Za-z0-9_]+)\s*=\s*(.*?)\s*$", line)
            if m:
                out[m.group(1)] = m.group(2)
    except (OSError, UnicodeDecodeError) as e:
        log(f"settings read error: {e}")
    _settings_cache = (time.time(), out)
    return out


def setting(name, default):
    v = settings().get(name, "")
    return v if v != "" else default


# ------------------------------------------------------------------ HUD state file
class State:
    def __init__(self):
        self.state, self.level, self.say, self.err = "idle", 0.0, "", ""
        self.pop_n, self.pop = 0, "none"
        self.lock = threading.Lock()
        self.last_write = 0.0

    def set(self, state=None, level=None, say=None, err=None, force=True, pop=None):
        with self.lock:
            if state in ("speaking", "thinking", "listening") and cancel.is_set():
                state = None                                    # stopped: a late write from a dying turn never shows
            if state is not None:
                self.state = state
            if level is not None:
                self.level = max(0.0, min(1.0, level))
            if say is not None:
                self.say = re.sub(r"\s+", " ", say)[:160]
            if err is not None:
                self.err = err[:120]
            if pop is not None:
                self.pop_n, self.pop = self.pop_n + 1, pop
            now = time.time()
            if not force and now - self.last_write < 0.05:      # level updates: at most 20 per second
                return
            self.last_write = now
            body = (f"T {int(now)}\nSTATE {self.state}\nLEVEL {self.level:.3f}\nSAY {self.say}\nERR {self.err}\n"
                    f"POP {self.pop_n} {self.pop}\n")
            tmp = STATE_FILE + ".tmp"
            try:
                with open(tmp, "w", encoding="utf-8") as f:
                    f.write(body)
                for _ in range(3):                              # the skin may be reading the file at that instant
                    try:
                        os.replace(tmp, STATE_FILE)
                        break
                    except OSError:
                        time.sleep(0.01)
            except OSError:
                pass


S = State()
cancel = threading.Event()
busy = threading.Lock()
mic = threading.Lock()                  # whoever has the microphone open holds this: the wake word or a turn, never both
JARVIS_WORD = re.compile(r"\bjarvis\b", re.I)
name_until = [0.0]                      # until then he is saying "Jarvis" himself: the wake word ignores it


def stop_now(why):
    """Stop him at once (a click, the stop key, talking over him): sound, Windows voice and turn end, the HUD is idle."""
    cancel.set()
    S.set(state="idle", level=0.0)
    log(f"stop: {why}")


# ------------------------------------------------------------------ what's installed
def missing_packages():
    """The pip packages Jarvis needs that aren't importable (checked without loading the heavy models)."""
    import importlib.util
    need = {"faster_whisper": "faster-whisper", "sounddevice": "sounddevice", "numpy": "numpy"}
    return [pip for mod, pip in need.items() if importlib.util.find_spec(mod) is None]


def problem(msg, popup=True):
    """Log a problem, show it on the hologram, and add it to the conversation pop-up."""
    log("problem: " + msg)
    S.set(err=msg)
    if popup:
        convo_add("S", msg)
        S.set(pop="open")                                     # you just clicked: show why it didn't work


# ------------------------------------------------------------------ one copy only / quit with Rainmeter
_lock_handle = None

def single_instance():
    global _lock_handle
    _lock_handle = open(os.path.join(DATA, "jarvis.lock"), "w")
    try:
        msvcrt.locking(_lock_handle.fileno(), msvcrt.LK_NBLCK, 1)
        return True
    except OSError:
        return False


def rainmeter_running():
    return ctypes.windll.user32.FindWindowW("DummyRainWClass", None) != 0


# ------------------------------------------------------------------ HUD context for the model
class MEMORYSTATUSEX(ctypes.Structure):
    _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]


class SYSTEM_POWER_STATUS(ctypes.Structure):
    _fields_ = [("ACLineStatus", ctypes.c_byte), ("BatteryFlag", ctypes.c_byte), ("BatteryLifePercent", ctypes.c_byte),
                ("SystemStatusFlag", ctypes.c_byte), ("BatteryLifeTime", ctypes.c_ulong), ("BatteryFullLifeTime", ctypes.c_ulong)]


def read_kv(name):
    try:
        with open(os.path.join(DATA, name), "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except OSError:
        return ""


def todo_note():
    """The to-do note (ObsidianTodo) if it is set and exists, else ""."""
    path = settings().get("ObsidianTodo", "").strip().strip('"')
    return path if path and os.path.exists(path) else ""


# Matching by meaning (the user, 2026-10-14): a shared word OR a close meaning counts, in 6a, M1, M2 and M4a. The model
# is ChromaDB's local all-MiniLM-L6-v2; until it is loaded, or without ChromaDB, matching is by words only.
# Measured 2026-10-14: related pairs 0.39-0.53, unrelated 0.02-0.18; about 30 ms a sentence on the CPU.
MEANING_TALK = 0.35        # talk and facts (M1, M2, M4a)
MEANING_BLOCK = 0.6        # 6a, a lot stricter (the user): only close to one of the block's example questions
_embed = [None]            # the model, set by load_meaning() on a thread at startup
_vecs = {}                 # text -> unit vector, so each line is embedded once
STAMP = re.compile(r"^\[[^\]]*\] ")   # the time stamp fixed() puts on a history line


def load_meaning():
    try:
        from chromadb.utils.embedding_functions import ONNXMiniLM_L6_V2
        # CPU only: the default tries TensorRT / CUDA, fails and retries on every call (330 ms a sentence, not 30)
        ef = ONNXMiniLM_L6_V2(preferred_providers=["CPUExecutionProvider"])
        ef(["warm up"])
        _embed[0] = ef
        for examples in BLOCK_EXAMPLES.values():               # ready before the first question
            for e in examples:
                vec(e)
        try:
            for t in load_topics():                            # M2: each filed topic once, so recall doesn't wait
                vec(topic_text(t))
        except (OSError, ValueError):
            pass
        try:
            for f in load_memory():                            # M4a: each saved fact once, for the same reason
                vec(f)
            for _, g in load_gist()[0]:                        # M3: and each gist line
                vec(g)
        except (OSError, ValueError):
            pass
        log("meaning match: ready")
    except Exception as e:
        _embed[0] = None
        log(f"meaning match off, words only: {e!r}")


def vec(text):
    v = _vecs.get(text)
    if v is None:
        if len(_vecs) > 1000:                                 # warm-up alone is ~300 + gist lines; ~12 KB each
            _vecs.clear()
        raw = [float(x) for x in _embed[0]([text])[0]]
        n = sum(x * x for x in raw) ** 0.5 or 1.0
        v = _vecs[text] = [x / n for x in raw]
    return v


def closeness(text, others):
    """How close text is in meaning to the nearest of `others` (cosine); 0.0 while the model is off."""
    if _embed[0] is None or not others:
        return 0.0
    try:
        q = vec(STAMP.sub("", text))
        return max(sum(a * b for a, b in zip(q, vec(STAMP.sub("", o)))) for o in others)
    except Exception as e:
        log(f"meaning match failed, words only: {e!r}")
        return 0.0


def meaning(text, others, floor):
    """Whether text means about the same as any of `others` (cosine >= floor). False while the model is off."""
    return closeness(text, others) >= floor


# 6a, by meaning: a block also goes in when the question is very close to one of these
BLOCK_EXAMPLES = {
    "calendar": ("What's on my calendar this week?", "Do I have any classes or exams coming up?", "Am I free on Friday?",
                 "When is my next appointment?"),
    "mail": ("Do I have any new emails?", "Did anyone message me?", "How many unread emails are in my inbox?"),
    "todo": ("What's on my to-do list?", "What tasks do I still have to do?", "What do I need to get done?"),
    "pc": ("How hot is my computer running?", "Why is my laptop so slow?", "How much battery is left?",
           "Is my graphics card busy?"),
    "net": ("Is my internet working?", "How fast is my connection?", "Am I connected to the wifi?"),
    "apps": ("What apps are open right now?", "Which programs are running?"),
    "pending": ("What alarms do I have set?", "Did you set my reminder?", "How long is left on the timer?",
                "When will you wake me up?"),
}
# 6a: a block of HUD data goes into the prompt only when the question is about it. The time always; a briefing all.
BLOCKS = {"calendar": r"schedule|today|tomorrow|tonight|week|class|quiz|exam|test|meeting|free|busy|when is|what'?s on|"
                      r"calendar|event|appointment|plans?\b|monday|tuesday|wednesday|thursday|friday|saturday|sunday|"
                      r"weekend|month|morning|afternoon|evening|later\b|due\b|deadline|anything (?:on|for|happening)",
          "mail": r"e?-?mail|inbox|unread|messages?\b|gmail",
          "todo": r"to-?\s?dos?\b|tasks?\b|my list",
          "pc": r"cpu|gpu|graphics|temp|hot|ram\b|memory|fans?\b|power|battery|slow|lag|fps|load|usage|disk|storage|"
                r"volume|bright|mic|alarm|timer|reminder|pending|pc\b|computer|laptop|system",
          "net": r"wi-?fi|network|internet|connection|online|ping|download|upload|speed",
          "apps": r"open\b|running|windows?\b|apps?\b|programs?\b",
          # the Pending line (in sensors()): sent on its own for anything about time or setting things, so "wake me
          # at 7" or "did you set it" can be checked against the real schedule; left out of unrelated chat
          "pending": r"alarms?\b|timers?\b|remind|wake|snooze|cancel|pending|schedul|set\b|did you|o'?clock|"
                     r"\d+ ?(?:am|pm|a\.m|p\.m)\b|minutes?\b|hours?\b|morning|tonight|later\b"}
# "tell me a joke" is not about you: "me" right after tell/give/show/help/let does not count
ABOUT_ME = re.compile(r"\b(?:my|(?<!tell )(?<!give )(?<!show )(?<!help )(?<!let )me|i|i'm|i've|mine|myself)\b", re.I)


def wants(text, kind=None):
    """The HUD blocks a question needs. None = all of them (a briefing, or a caller that did not say)."""
    if text is None or kind == "brief":
        return set(BLOCKS)
    asked = info_blocks(text)                                  # slice C: the blocks an info question was sent for
    return {b for b, pat in BLOCKS.items()
            if re.search(rf"\b(?:{pat})", text, re.I) or b in asked or meaning(text, BLOCK_EXAMPLES[b], MEANING_BLOCK)}


def context(text=None, kind=None):
    want = wants(text, kind)
    lines = [f"Now:{datetime.now().strftime('%A %d %B %Y, %H:%M (%I:%M %p)')}"]
    if "pc" in want:
        try:
            m = MEMORYSTATUSEX(); m.dwLength = ctypes.sizeof(m)
            if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m)):   # 0 = the call failed: no line, not "0 %"
                lines.append(f"Memory in use: {m.dwMemoryLoad}% of {m.ullTotalPhys / 2**30:.0f} GB")
            p = SYSTEM_POWER_STATUS()
            ctypes.windll.kernel32.GetSystemPowerStatus(ctypes.byref(p))
            if p.BatteryLifePercent != -1 and (p.BatteryLifePercent & 0xFF) <= 100:
                lines.append(f"Battery: {p.BatteryLifePercent & 0xFF}% ({'plugged in' if p.ACLineStatus == 1 else 'on battery'})")
        except Exception:
            pass
    mail = "mail" in want and re.search(r"^UNREAD (\d+)", read_kv("mail.txt"), re.M)
    if mail:
        lines.append(f"Unread Gmail: {mail.group(1)}")
    events = []
    for m in re.finditer(r"^E (\d+)\|(\d+)\|(\d)\|([^|]*)\|(.*)$", read_kv("calendar.txt") if "calendar" in want else "", re.M):
        start = datetime.fromtimestamp(int(m.group(1)))
        if int(m.group(2)) >= time.time():
            when = start.strftime("%a %d %b") + ("" if m.group(3) == "1" else start.strftime(" %H:%M"))
            events.append(f"{when} - {m.group(5)}" + (f" ({m.group(4)})" if m.group(4) else ""))
    if events:
        lines.append("Upcoming calendar events: " + "; ".join(events[:6]))
    apps = re.findall(r"^W (.+)$", read_kv("windows.txt"), re.M) if "apps" in want else []
    if apps:
        lines.append("Open apps: " + ", ".join(a.replace(".exe", "") for a in apps[:20]))
    if "net" in want:
        net = read_kv("net.txt")
        d, u = re.search(r"^DOWN (\d+)", net, re.M), re.search(r"^UP (\d+)", net, re.M)
        if d and u:
            lines.append(f"Network right now: {int(d.group(1)) * 8 / 1e6:.1f} Mbps down, {int(u.group(1)) * 8 / 1e6:.1f} Mbps up")
        st = settings()
        if st.get("LinkDownMbps"):
            lines.append(f"Internet speed (last test {st.get('LastSpeedTest', '?')}): {st.get('LinkDownMbps')} down / {st.get('LinkUpMbps', '?')} up Mbps")
    todo = todo_note() if "todo" in want else ""
    if todo:
        try:
            with open(todo, "r", encoding="utf-8", errors="ignore") as f:
                items = [re.sub(r"^\s*[-*]\s*\[ \]\s*", "", l).strip() for l in f if re.match(r"^\s*[-*]\s*\[ \]", l)]
            if items:
                lines.append("Open to-dos: " + "; ".join(items[:12]))
        except OSError:
            pass
    return "\n".join(lines)


# the HWiNFO sensors the HUD shows: Settings.inc key (the sensor's number, -1 = not mapped), spoken name, unit
HW_LINES = (("HW_CpuTemp", "CPU temperature", "C"), ("HW_GpuTemp", "GPU temperature", "C"), ("HW_CpuPower", "CPU power", "W"),
            ("HW_GpuPower", "GPU power", "W"), ("HW_Fan1", "Fan 1", "RPM"), ("HW_Fan2", "Fan 2", "RPM"),
            ("HW_SsdTemp", "SSD temperature", "C"))


def hw_value(index):
    """One HWiNFO reading, from the same registry values HWiNFO.inc shows on the HUD. Not there = OSError."""
    import winreg
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"SOFTWARE\HWiNFO64\VSB") as key:
        return float(winreg.QueryValueEx(key, f"ValueRaw{index}")[0])


def cpu_times():
    idle, kernel, user = ctypes.c_ulonglong(), ctypes.c_ulonglong(), ctypes.c_ulonglong()
    if not ctypes.windll.kernel32.GetSystemTimes(ctypes.byref(idle), ctypes.byref(kernel), ctypes.byref(user)):
        raise OSError("GetSystemTimes failed")
    return idle.value, kernel.value + user.value              # kernel time includes the idle time


def sensors():
    """Readings the HUD shows that context() leaves out. Takes about 0.2 s (two CPU samples), so a turn reads it on a
    thread while you speak. Each source stands alone: one that is missing or fails costs its own line only."""
    lines, st = [], settings()

    def part(fn):
        try:
            lines.extend(fn())
        except Exception:
            pass

    def hw(key, name, unit):
        n = int(float(st.get(key, "-1")))
        return [f"{name}: {hw_value(n):.0f} {unit}"] if n >= 0 else []

    def cpu():
        idle0, all0 = cpu_times()
        time.sleep(0.2)
        idle1, all1 = cpu_times()
        return [f"CPU load: {100 * (1 - (idle1 - idle0) / (all1 - all0)):.0f}%"]

    def card():
        if not gpu():                                         # asking a sleeping card for numbers would wake it
            return []
        r = subprocess.run(["nvidia-smi", "--query-gpu=utilization.gpu,memory.used,memory.total",
                            "--format=csv,noheader,nounits"], creationflags=NO_WINDOW, capture_output=True, text=True, timeout=2)
        if r.returncode:
            return []
        load, used, total = (float(x) for x in r.stdout.splitlines()[0].split(","))
        return [f"GPU load: {load:.0f}%, video memory {used / 1024:.1f} of {total / 1024:.0f} GB in use"]

    def sound():
        is_muted, percent = speakers()
        return [f"Speaker volume: {percent}%" + (" (muted)" if is_muted else "")]

    def panel():
        kv = dict(re.findall(r"^(T|BRIGHT|MIC|MICMUTE) (-?\d+)", read_kv("sys.txt"), re.M))
        if time.time() - int(kv.get("T", 0)) > 30:            # the HUD is off: old numbers are not current numbers
            return []
        out = [f"Screen brightness: {kv['BRIGHT']}%"] if int(kv.get("BRIGHT", -1)) >= 0 else []
        if int(kv.get("MIC", -1)) >= 0:
            out.append(f"Microphone level: {kv['MIC']}%" + (" (muted)" if kv.get("MICMUTE") == "1" else ""))
        return out

    def disk():
        drive = os.environ.get("SystemDrive", "C:")
        use = shutil.disk_usage(drive + "\\")
        return [f"Disk {drive} {use.free / 2**30:.0f} GB free of {use.total / 2**30:.0f} GB"]

    def pending():                                            # what kind and when, never the label: the text stays in its file
        items, now = load_reminders(), time.time()
        each = [f"timer with {span(r[0] - now)} left" if r[2] == "timer" else
                f"{'alarm' if r[3] == 'alarm' else 'reminder'} at {clock(r[0], now)}" for r in items[:5]]
        return [f"Pending: {'; '.join(each) or 'no alarms, reminders or timers'}" + (f"; and {len(items) - 5} more" if len(items) > 5 else "")]
    for line in HW_LINES:
        part(lambda: hw(*line))
    for fn in (cpu, card, sound, panel, disk, pending):
        part(fn)
    return "\n".join(lines)


SYSTEM = ("You are JARVIS, the AI built into the user's spaceship-style desktop HUD. You talk out loud, so answer in "
          "one to three short spoken sentences: no lists, markdown, emoji or code unless asked. {mood} "
          "Use the live HUD data below when it's relevant; if something isn't in it, say you don't "
          "have that rather than guessing. Alarms, timers, reminders, volume and apps are handled by the system, not by "
          "you; the Pending line below is the true schedule. Never say you set or changed something. "
          "Answer only what was asked. Do not mention the data below unless the question is about it.\n")
MOODS = {"proper": "Be calm, precise and a little dry.",       # JarvisPersonality: how the model words its answers
         "playful": "Be funny and quick. When the user jokes or banters, dark humor included, answer in the same spirit. "
                    "When they ask a real question, answer it helpfully first, then joke if it fits. "
                    "You are on their side: back them up. Never joke about a failed action.",
         "brief": "Answer in one short sentence. No small talk."}
# "good morning" / "brief me": the model words it, from data the prompt already holds
# shortcut: if he invents or skips items in practice, build the sentences in code instead
BRIEFING = ("BRIEFING: greet the user, then say in this order, from LIVE HUD DATA only: the time, today's calendar "
            "events, unread mail count, open to-dos (at most three, then the count), pending reminders. Skip a part "
            "that has no data. Five sentences at most.")


def ctx_tokens():
    """The model's context window (JarvisContext, default 2048 - less memory and a faster first word)."""
    try:
        return max(1024, min(32768, int(float(setting("JarvisContext", "2048")))))
    except ValueError:
        return 2048


def about_me():
    """The user's "about me" note (JarvisProfile): a couple of paragraphs that personalise the answers.
    Front matter and comments are stripped; capped at ~4000 characters so it never crowds out the conversation."""
    path = setting("JarvisProfile", "").strip().strip('"')
    if not path or not os.path.exists(path):
        return ""
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()
    except OSError:
        return ""
    text = re.sub(r"^---\n.*?\n---\n", "", text, flags=re.S)            # YAML front matter
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)                    # comments (the template's hints)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    cap = 2000 if ctx_tokens() <= 2048 else 4000       # a small context leaves less room for the note
    if len(text) > cap:
        text = text[:cap].rsplit(" ", 1)[0] + " ..."
    return text


def system_prompt(text=None, kind=None):
    """text / kind: the question, so only the HUD blocks and the profile it needs go in. None = everything."""
    me = about_me() if text is None or kind == "brief" or ABOUT_ME.search(text) else ""
    if me and text is not None and kind != "brief" and len(me) > 500:                # a question about you: the note's start, not all of it
        me = me[:500].rsplit(" ", 1)[0] + " ..."
    out = SYSTEM.replace("{mood}", MOODS.get(setting("JarvisPersonality", "playful").strip().lower(), MOODS["playful"]))
    if me:
        out += ("\nABOUT THE USER (from their own note - use it to personalise answers; don't recite it unless "
                "asked):\n" + me + "\n")
    try:
        facts = load_memory()
    except (OSError, ValueError):
        facts = []                                             # unreadable: he says so when asked, the prompt goes on
    if text is not None and kind != "brief":                   # M4a: only the facts the question is about, best 5
        words = keywords(text)
        facts = sorted((f for f in facts if related(text, [f])), key=lambda f: -len(words & keywords(f)))[:5]
    if facts:
        out += "\nFACTS THE USER TOLD YOU (use them exactly):\n" + "\n".join("- " + f for f in facts)[:2000] + "\n"
    if text is not None and DID_ASK.search(text):              # M4b: only for questions about what he did
        out += ("\nWHAT YOU ACTUALLY DID THIS SESSION (only these ran; never claim anything else):\n"
                + ("\n".join(f"- {clock(t)}: {what}" + ("" if ok else " (it failed)") for t, what, ok in did)
                   or "You ran nothing in this session.") + "\n")
    return out + "\nLIVE HUD DATA:\n" + context(text, kind)


# ------------------------------------------------------------------ Ollama
def http_json(path, payload=None, timeout=5):
    req = urllib.request.Request(OLLAMA + path, data=json.dumps(payload).encode() if payload is not None else None,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode() or "{}")


def ensure_ollama():
    """Ensure Ollama is running, starting it if needed."""
    try:
        http_json("/api/tags", timeout=2)
        return True
    except Exception:
        pass
    try:
        # with both cards visible Ollama picks the Radeon (more shared memory): hide it, so it is the NVIDIA card or nothing
        env = dict(os.environ, ROCR_VISIBLE_DEVICES="-1", HIP_VISIBLE_DEVICES="-1")
        subprocess.Popen(["ollama", "serve"], creationflags=NO_WINDOW, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env)
    except OSError:
        return False
    # Wait for Ollama to start (up to 10 seconds)
    for _ in range(20):
        time.sleep(0.5)
        try:
            http_json("/api/tags", timeout=2)
            return True
        except Exception:
            pass
    return False


def installed_models():
    try:
        names = sorted(m["name"] for m in http_json("/api/tags", timeout=3).get("models", []))
    except Exception:
        return None
    try:
        with open(MODELS_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(names) + "\n")
    except OSError:
        pass
    return names


def pick_model(tier):
    """JarvisModel normally; JarvisModelFast (if set) while the HUD is on LITE / LOW because the GPU is busy."""
    want = setting("JarvisModel", "llama3.1:8b")
    fast = setting("JarvisModelFast", "")
    if tier >= 1 and fast:
        want = fast
    names = installed_models()
    if names is None:
        return want
    other = fast if want != fast else setting("JarvisModel", "llama3.1:8b")
    for n in (want, want + ":latest", other, other + ":latest"):
        if n in names:                                         # only a model you configured: never an embedding model
            if n not in (want, want + ":latest"):
                log(f"model {want} not downloaded - using {n}, the other configured model")
            return n
    log(f"model {want} not downloaded and no other configured model is installed")
    return None


def keep_alive():
    try:
        return f"{max(1, int(float(setting('JarvisKeepAlive', '10'))))}m"
    except ValueError:
        return "10m"


def warm(model):
    def go():
        try:
            http_json("/api/generate", {"model": model, "prompt": "", "keep_alive": keep_alive()}, timeout=120)
        except Exception:
            pass
    threading.Thread(target=go, daemon=True).start()


def ollama_on_cpu(model):
    """Warn when Ollama keeps any part of the chat model in ordinary memory instead of on the graphics card."""
    try:
        for m in http_json("/api/ps", timeout=2).get("models", []):
            if m.get("name") == model and m.get("size_vram", 0) < m.get("size", 0):
                cpu_in_use("the chat model", f"{100 - 100 * m.get('size_vram', 0) // m['size']}% of it is off the GPU")
                return True
    except Exception:
        pass
    return False


_moved = set()                 # chat models reloaded once since they were last seen fully on the card


def chat_to_gpu(model):
    """Ollama keeps part of the chat model off the card: if the card is there, unload and warm it again - once, so a
    card full of a game's data costs one reload, not one per turn."""
    if model in _moved or not gpu():
        return False
    _moved.add(model)

    def go():
        try:
            http_json("/api/generate", {"model": model, "keep_alive": 0}, timeout=30)
        except Exception as e:
            log(f"chat model reload failed ({type(e).__name__})")
            return
        log(f"chat model {model} reloaded to move it onto the GPU")
        warm(model)
    threading.Thread(target=go, daemon=True).start()
    return True


def chat_stream(model, messages, temperature=0.5):
    opts = {"num_ctx": ctx_tokens(), "temperature": temperature, "num_predict": 160}
    if not gpu():
        opts["num_thread"] = cpu_threads()
    body = json.dumps({"model": model, "messages": messages, "stream": True, "keep_alive": keep_alive(),
                       "options": opts}).encode()
    req = urllib.request.Request(OLLAMA + "/api/chat", data=body, headers={"Content-Type": "application/json"})
    # the blocking network read runs in its own thread, so a cancel is seen within 0.2 s even while the model is
    # still thinking; the abandoned read closes its connection as soon as it wakes, which makes Ollama stop too
    lines, gone = queue.Queue(), threading.Event()

    def pump():
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                for raw in r:
                    if gone.is_set():
                        return
                    lines.put(raw)
            lines.put(None)
        except Exception as e:
            lines.put(e)

    threading.Thread(target=pump, daemon=True).start()
    try:
        while True:
            try:
                raw = lines.get(timeout=0.2)
            except queue.Empty:
                if cancel.is_set():
                    return
                continue
            if raw is None or cancel.is_set():
                return
            if isinstance(raw, Exception):
                raise raw
            raw = raw.strip()
            if not raw:
                continue
            obj = json.loads(raw)
            piece = obj.get("message", {}).get("content", "")
            if piece:
                yield piece
            if obj.get("done"):
                return
    finally:
        gone.set()


# ------------------------------------------------------------------ AI fallback for a command the patterns missed
# The model only names the intent and copies your words. Code checks every word was said and the intent's own word is
# in what you said, builds one fixed sentence, and route() must read it as that command; then the usual code runs it.
# Lock, sleep, restart, shutdown, open, close, memory and to-do are not on its list: those stay pattern-only.
AI_CUES = {"alarm_set": r"alarm|wake|woken|get me up", "reminder_set": r"remind|ping me|heads.?up", "timer_set": r"timer",
           "schedule_list": r"alarm|remind|timer|schedul", "schedule_cancel": r"alarm|remind|timer|schedul",
           "volume_set": r"volume|sound|audio|speaker|music", "volume_step": r"volume|sound|audio|speaker|music|louder|quieter|crank",
           "volume_level": r"volume|sound|loud|muted", "mute": r"mute|silen", "unmute": r"unmute|sound|audio|speaker",
           "media": r"pause|resume|skip|next (?:song|track)|previous|song|track|music"}
AI_WORDS = re.compile(r"\b(?:" + "|".join(AI_CUES.values()) + ")")
AI_NOT = re.compile(r"(?:how|why|what|when|who|where|which|whose|should|shall|is|are|was|were|do|does|did|has|had)\b|"
                    r".*\b(?:yesterday|earlier|ago|last (?:night|week)|explain|tell me about)\b")
AI_SCHEMA = {"type": "object", "properties": {"commands": {"type": "array", "items": {"type": "object", "properties": {
    "intent": {"type": "string", "enum": list(AI_CUES) + ["chat"]}, "when": {"type": "string"}, "label": {"type": "string"},
    "number": {"type": "integer"}}, "required": ["intent"]}}}, "required": ["commands"]}
AI_PROMPT = """You sort what the user said to a voice assistant into commands. Output JSON only.
RULE 1: a question is "chat". Anything asking how, why or should, any opinion, anything about the past, and talk ABOUT
alarms, timers or volume is "chat". Only an order to do something now is a command. Anything not listed below is "chat".
RULE 2: "when" is copied word for word from the user, including "in"/"at"/"for", and nothing added: never add am, pm,
today or tomorrow that the user did not say. "number" is only for volume.
Intents, with examples ->  output:
alarm_set: "wake me at 7" -> when "at 7";  "alarm for 6:30 am" -> when "for 6:30 am"
reminder_set: "remind me to cook in 20 minutes" -> label "to cook", when "in 20 minutes"
timer_set: "ten minute timer for pasta" -> when "ten minute", label "pasta"
schedule_list: "what reminders do I have", "list my timers", "any alarms?"
schedule_cancel: "cancel the 7 am alarm" -> when "7 am";  "cancel the cooking reminder" -> label "cooking";
  "stop the timer", "cancel all reminders"
volume_set: "volume to 30" -> number 30   volume_step: "louder", "turn it down"
volume_level: "what's the volume"   mute: "mute"   unmute: "unmute the sound"
media: "pause", "skip", "next song", "previous track" -> label playpause | next | prev
Several orders in one sentence -> several commands in order: "alarms for 7 and 8 am" -> when "7", when "8 am".
Now: {now}."""


def ask_ai(text, routed):
    """Only a near-miss, or a chat line with a command word that is not a question or about the past, goes to the AI."""
    t = re.sub(r"^(?:(?:and|then|so|now|okay|ok|alright|um|uh|yo|hey|hi)[,.]? +)+", "", strip_name(text).strip().lower())
    if (setting("JarvisAIRouter", "1") != "1" or AI_NOT.match(t)
            or t.endswith("?") and not re.match(r"(?:can|could|would|will) you\b", t)):
        return False
    return routed[3] == NEAR_MISS or routed[0] == "chat" and bool(AI_WORDS.search(t))


def _words(s):
    return re.findall(r"[a-z0-9:']+", re.sub(r"\b([ap])\.? ?m\b\.?", r"\1m", s.lower()))


def interpret(model, text):
    """What the AI made of a missed command, as a checked route; None when there is none or it can't be trusted."""
    t0, low = time.time(), text.lower()
    heard = set(_words(text))
    nums = {_num(w) for w in heard} - {None}
    said = lambda s: all(w in heard or w in ("at", "in", "for", "to", "the", "and") or _num(w) in nums for w in _words(s))
    opts = {"num_ctx": ctx_tokens(), "temperature": 0, "num_predict": 160}   # chat's num_ctx: no model reload
    if not gpu():
        opts["num_thread"] = cpu_threads()
    try:
        out = http_json("/api/chat", {"model": model, "stream": False, "format": AI_SCHEMA, "keep_alive": keep_alive(),
                                      "options": opts, "messages": [
                                          {"role": "system", "content": AI_PROMPT.replace("{now}", datetime.now().strftime("%A %d %B %Y, %I:%M %p"))},
                                          {"role": "user", "content": text}]}, timeout=8)
        cmds = [c for c in json.loads(out["message"]["content"])["commands"] if c.get("intent") != "chat"]
        sets = [c for c in cmds if c.get("intent") == "alarm_set"]
        if len(sets) > 1 and len(sets) == len(cmds) and not any(str(c.get("when", "")).startswith("in ") for c in sets):
            # "alarms for 7 and 8 am": one sentence, so route() gives the am / pm said last to each
            cmds = [{"intent": "alarm_set", "when": "for " + " and ".join(re.sub(r"^(?:at|for) ", "", c.get("when", "")) for c in sets)}]
        routes = []
        for c in cmds:
            intent, at, label = c["intent"], str(c.get("when") or "").strip(), str(c.get("label") or "").strip()
            label = " ".join(re.sub(r"\b(?:alarms?|reminders?|timers?)\b", " ", label).split())
            if not re.search(rf"\b(?:{AI_CUES[intent]})", low) or not said(at) or intent != "media" and not said(label):
                raise ValueError("not what was said")
            bare = re.sub(r"^(?:at|in|for|on) ", "", at)
            noun = "timer" if "timer" in low else "reminder" if "remind" in low else "alarm"
            spec = " ".join(x for x in (bare, label) if x)
            n = c.get("number")
            if intent == "volume_set" and not (isinstance(n, int) and 0 <= n <= 100 and n in nums):
                raise ValueError("volume not said")
            sentence = {
                "alarm_set": f"set an alarm {at}".strip(),
                "reminder_set": f"remind me {label if re.match(r'(?:to|about|that) ', label) or not label else 'to ' + label} {at}".strip(),
                "timer_set": f"set a timer for {bare}" + (f" for {label}" if label else "") if bare else "set a timer",
                "schedule_list": "list my timers" if noun == "timer" else "what alarms do I have",
                "schedule_cancel": (f"cancel all {noun}s" if re.search(r"\b(?:all|every)\b", low) and not spec
                                    else f"cancel the {noun} for {spec}" if spec else f"cancel the {noun}"),
                "volume_set": f"set the volume to {n}",
                "volume_step": "turn it down" if re.search(r"\b(?:down|lower|quieter|decrease|reduce|softer)\b", low) else "turn it up",
                "volume_level": "what's the volume", "mute": "mute", "unmute": "unmute",
                "media": {"playpause": "pause", "next": "next track", "prev": "previous track"}.get(label, ""),
            }[intent]
            r = route(sentence)
            want = {"alarm_set": "set", "reminder_set": "set", "timer_set": "set", "schedule_list": "list",
                    "schedule_cancel": "cancel"}.get(intent)
            ok = (r[:2] == ("remind", want) and (intent != "alarm_set" or r[2][0] == "alarm")
                  and (intent != "timer_set" or r[2][0] == "timer") and (intent != "reminder_set" or r[2][0] not in ("alarm", "timer"))
                  if want else r == ("level", None, None, None) if intent == "volume_level"
                  else r[0] == "act" and r[1] == {"mute": "mute", "unmute": "unmute", "media": "media"}.get(intent, "volume") and r[3] is None)
            if not ok:
                raise ValueError("no preset")
            routes.append(r)
        # several commands only when each is complete: a set with no time would stop to ask
        if len(routes) > 1 and any(r[1] == "set" and r[2][1] is None for r in routes):
            raise ValueError("incomplete")
    except Exception as e:
        log(f"interpreter: fallback ({type(e).__name__})")
        return None
    log(f"interpreter: {len(routes)} commands, {time.time() - t0:.1f}s" if routes else "interpreter: no command")
    return None if not routes else routes[0] if len(routes) == 1 else ("multi", None, routes, None)


# ------------------------------------------------------------------ GPU or capped CPU
def gpu():
    """True while an NVIDIA card is attached (a hybrid laptop powers it off on battery)."""
    try:
        import ctranslate2
        return ctranslate2.get_cuda_device_count() > 0
    except Exception:
        return False


def cpu_threads():
    """Threads a model may use when it has to run on the CPU: a quarter of the cores, so a turn can't take the PC."""
    return max(2, (os.cpu_count() or 8) // 4)


def cpu_in_use(what, why):
    """Say so in the log and on the hologram, without opening the pop-up."""
    problem(f"CPU in use - {what} is not on the GPU ({str(why)[:60]})", popup=False)


# ------------------------------------------------------------------ speech to text
_whisper = None
_whisper_dev = [None]          # "cuda" or "cpu": where _whisper runs
_whisper_lock = threading.Lock()
_gpu_try = [0.0, False]        # when the card was last tried, and whether that failure is already logged


def _cuda_dlls():
    """The pip nvidia-* wheels keep cuBLAS / cuDNN / the CUDA runtime in their own bin folders, which Windows does not search."""
    import glob
    for d in [d for p in sys.path for d in glob.glob(os.path.join(p, "nvidia", "*", "bin"))]:
        if d not in os.environ["PATH"]:
            os.add_dll_directory(d)
            os.environ["PATH"] = d + os.pathsep + os.environ["PATH"]


def _load_whisper(device):
    from faster_whisper import WhisperModel
    size = setting("JarvisWhisper", "small.en")
    if device == "cpu":
        return WhisperModel(size, device="cpu", compute_type="int8", cpu_threads=cpu_threads())
    _cuda_dlls()
    return WhisperModel(size, device="cuda", compute_type="float16")


def whisper():
    global _whisper
    with _whisper_lock:                                        # the preload and a turn never load it twice
        if _whisper is None:
            dev = setting("JarvisWhisperDevice", "auto").lower()
            why = f"JarvisWhisperDevice={dev}"
            if dev in ("auto", "cuda"):
                try:
                    _whisper, _whisper_dev[0] = _load_whisper("cuda"), "cuda"
                    log(f"whisper {setting('JarvisWhisper', 'small.en')} on GPU")
                    return _whisper
                except Exception as e:
                    why = e
            _whisper, _whisper_dev[0], _gpu_try[0] = _load_whisper("cpu"), "cpu", time.time()
            if dev in ("auto", "cuda") and not gpu():
                problem("RTX is off - switch the laptop to hybrid graphics", popup=False)
            else:
                cpu_in_use("speech recognition", why)
        return _whisper


def gpu_watch(now):
    """Whisper fell back to the CPU: between turns, at most once a minute, move it to the card once it is back.
    gpu() is asked last, since it starts CUDA."""
    if (_whisper is None or _whisper_dev[0] != "cpu" or busy.locked() or now - _gpu_try[0] < 60
            or setting("JarvisWhisperDevice", "auto").lower() not in ("auto", "cuda") or not gpu()):
        return False
    _gpu_try[0] = now
    threading.Thread(target=_whisper_to_gpu, daemon=True).start()
    return True


def _whisper_to_gpu():
    global _whisper
    t0 = time.time()
    try:
        m = _load_whisper("cuda")                              # outside the lock: a turn meanwhile keeps the CPU model
    except Exception as e:
        if not _gpu_try[1]:
            _gpu_try[1] = True
            log(f"whisper: the GPU is still unavailable ({type(e).__name__})")
        return
    with _whisper_lock:
        if _whisper is None or _whisper_dev[0] != "cpu":       # unloaded or moved meanwhile
            return
        _whisper, _whisper_dev[0], _gpu_try[1] = m, "cuda", False
    log(f"whisper moved to GPU ({time.time() - t0:.1f} s)")
    if S.err.startswith(("RTX is off", "CPU in use - speech recognition")):
        S.set(err="")                                          # only our own warning; other problems stay up


# what Whisper writes on noise or near-silence: treated as silence
PHANTOM = re.compile(r"[\W_]*(?:(?:thanks|thank you)(?: so much)? for watching|subtitles? by\b.*|you)?[\W_]*", re.I)


def real_words(text):
    if text and PHANTOM.fullmatch(text):
        log("transcript: dropped (phantom)")
        return ""
    return text


heard_score = [0.0]            # the lowest segment avg_logprob of the last transcript: below -1.0 Whisper was unsure
HINT = "Hey Jarvis, set a timer for ten minutes. Jarvis, turn the volume down."   # words he should expect


def _decode(model, audio):
    """Whisper told what to expect. VAD trims the silence; when it leaves nothing (it can cut a short "yes") the audio
    is decoded once more without it, and without the hint, which Whisper can say back on near-silence."""
    opts = dict(beam_size=5 if _whisper_dev[0] == "cuda" else 3, language="en", condition_on_previous_text=False)
    segs = list(model.transcribe(audio, vad_filter=True, hotwords="Jarvis", initial_prompt=HINT, **opts)[0])
    if not segs:
        segs = list(model.transcribe(audio, vad_filter=False, **opts)[0])
    segs = no_loops(segs)
    heard_score[0] = min((getattr(s, "avg_logprob", 0.0) for s in segs), default=0.0)
    return real_words(no_repeats(" ".join(s.text for s in segs).strip()))


def no_loops(segs):
    """FR5 N2: drop the segments Whisper itself rates as a loop or as silence (its own limits: compression ratio
    above 2.4; no-speech above 0.6 while unsure, avg log-prob below -1). Only counts go to the log."""
    keep = [s for s in segs if getattr(s, "compression_ratio", 0.0) <= 2.4
            and not (getattr(s, "no_speech_prob", 0.0) > 0.6 and getattr(s, "avg_logprob", 0.0) < -1.0)]
    if len(keep) < len(segs):
        log(f"transcript: dropped (loop) {len(segs) - len(keep)} of {len(segs)} parts")
    return keep


def no_repeats(text):
    """"Okay. Okay. Okay." -> "Okay.": a sentence said 3+ times in a row is kept once (Whisper's repetition loop)."""
    parts = re.split(r"(?<=[.!?])\s+", text)
    same = [re.sub(r"[^\w']+", "", p.lower()) for p in parts]  # "Okay." and "okay" are the same sentence
    res, i = [], 0
    while i < len(parts):
        k = i
        while k + 1 < len(parts) and same[k + 1] == same[i]:
            k += 1
        res += parts[i:k + 1] if k - i < 2 else [parts[i]]
        i = k + 1
    return " ".join(res)


def transcribe(audio):
    if audio is None:
        return ""
    try:
        return _decode(whisper(), audio)
    except Exception as e:
        if "cuda" in str(e).lower() or "cublas" in str(e).lower() or "cudnn" in str(e).lower():
            global _whisper
            cpu_in_use("speech recognition", e)
            try:
                with _whisper_lock:                            # gpu_watch() moves it back to the card later
                    m = _whisper = _load_whisper("cpu")
                    _whisper_dev[0], _gpu_try[0] = "cpu", time.time()
                return _decode(m, audio)
            except Exception as cpu_e:
                log(f"whisper CPU fallback also failed: {cpu_e}")
                raise cpu_e
        raise


def listen(wait=3, patience=6):
    """Record until you stop talking: waits up to `patience` s for speech, then stops after JarvisSilence seconds of
    quiet (default 1 s; raise it if he cuts you off mid-sentence), max 25 s."""
    if not mic.acquire(timeout=wait):                          # the wake word lets go within a second of a turn starting
        raise RuntimeError("The microphone is busy - try again")
    try:
        duck()
        return _listen(patience)
    finally:
        mic.release()
        unduck()                                               # before anything is said or run: a volume command keeps its value


_mic_missing = [""]


def mic_device():
    """JarvisMic (Control Center > JARVIS > MICROPHONE): part of an input device's name; empty = the Windows default.
    MME first: it converts to 16 kHz itself, WASAPI may refuse that rate."""
    want = setting("JarvisMic", "").strip().lower()
    if not want:
        return None
    import sounddevice as sd
    apis = sd.query_hostapis()
    found = [(apis[d["hostapi"]]["name"] != "MME", i) for i, d in enumerate(sd.query_devices())
             if d["max_input_channels"] > 0 and want in d["name"].lower()]
    if found:
        return min(found)[1]
    if _mic_missing[0] != want:                                # once, not on every listen
        _mic_missing[0] = want
        log(f"microphone '{want}' not found - using the Windows default")
    return None


def list_mics():
    """The input devices (MME names, the ones mic_device() opens first) for the Control Center's MICROPHONE row."""
    try:
        import sounddevice as sd
        apis = sd.query_hostapis()
        names = sorted({d["name"] for d in sd.query_devices() if d["max_input_channels"] > 0
                        and apis[d["hostapi"]]["name"] == "MME" and not d["name"].startswith("Microsoft Sound Mapper")})
        with open(MICS_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(names) + "\n")
    except Exception as e:
        log(f"microphone list failed ({type(e).__name__})")


# shortcut: lowers the whole Windows volume, not single apps; per-app (Core Audio sessions) is ~60 more lines, if it annoys
def duck():
    """While he listens, other sound goes down to JarvisDuckLevel % (default 30) of what it was; JarvisDuck=0 = off.
    What to put back is written to a file first, so a crash meanwhile is put right at the next start."""
    if setting("JarvisDuck", "1") != "1" or os.path.exists(DUCK_FILE):   # a file left over: its value is the real one
        return
    try:
        level = max(10, min(80, int(float(setting("JarvisDuckLevel", "30")))))
        is_muted, old = speakers()
        low = old * level // 100
        if is_muted or old <= low:
            return
        with open(DUCK_FILE, "w", encoding="utf-8") as f:
            f.write(f"{old} {low}")
        speakers(volume=low / 100)
    except (OSError, ValueError) as e:
        log(f"duck failed ({type(e).__name__})")


def unduck():
    """Put the volume back, unless it was changed meanwhile (yours stays)."""
    try:
        with open(DUCK_FILE, encoding="utf-8") as f:
            old, low = map(int, f.read().split())
    except FileNotFoundError:
        return
    except (OSError, ValueError):
        old = low = None                                       # unreadable: just remove it
    try:
        if old is not None and speakers()[1] == low:
            speakers(volume=old / 100)
        os.remove(DUCK_FILE)
    except OSError as e:
        log(f"unduck failed ({type(e).__name__})")


def follow_wait():
    """Seconds a follow-up waits for you to start talking: JarvisFollowUpWait, default 10, kept to 3-30."""
    try:
        return max(3.0, min(30.0, float(setting("JarvisFollowUpWait", "10"))))
    except ValueError:
        return 10.0


def _listen(patience=6):
    import numpy as np
    import sounddevice as sd
    rate, block = 16000, 480                     # 30 ms blocks
    frames, started, silent, waited = [], False, 0, 0
    floor = None
    try:
        quiet_blocks = int(max(0.5, min(6.0, float(setting("JarvisSilence", "1.0")))) / 0.03)
    except ValueError:
        quiet_blocks = 33
    stream = None
    try:
        stream = sd.InputStream(samplerate=rate, channels=1, dtype="float32", blocksize=block, device=mic_device())
    except Exception as e:
        raise RuntimeError("No microphone available (" + str(e).split("\n")[0][:60] + ") - check Windows Settings > Privacy > Microphone")
    
    try:
        with stream as stream_ctx:
            t0 = time.time()
            while not cancel.is_set():
                data, _ = stream_ctx.read(block)
                x = data[:, 0]
                rms = float(np.sqrt(np.mean(x * x)) + 1e-9)
                if floor is None:
                    floor = rms
                if not started:
                    floor = 0.95 * floor + 0.05 * rms    # follow the room's background noise
                thresh = max(floor * 3.0, 0.012)
                S.set(level=min(1.0, rms / 0.12), force=False)
                if rms > thresh:
                    started, silent = True, 0
                elif started:
                    silent += 1
                if started:
                    frames.append(x.copy())
                else:
                    waited += 1
                    frames = (frames + [x.copy()])[-10:]     # keep 0.3 s before speech starts
                if started and silent > quiet_blocks:
                    break
                if not started and waited > patience / 0.03:
                    return None
                if time.time() - t0 > 25:
                    break
    except Exception as e:
        problem("The microphone stopped (" + str(e).split("\n")[0][:60] + ")", popup=False)
        return None
    finally:
        if stream is not None:
            try:
                stream.close()
            except Exception:
                pass
    
    if cancel.is_set() or not started:
        return None
    import numpy as np
    return np.concatenate(frames)


# ------------------------------------------------------------------ text to speech
# Engines, chosen by JarvisVoice: a kokoro-*.onnx file -> Kokoro-82M (natural, runs on the CPU), any other .onnx ->
# Piper, blank -> the built-in Windows voice. If an engine fails, that sentence falls back to the Windows voice, and
# if even that fails the words go to the pop-up - he never just goes silent.
_engines = {}               # loaded voices, by path
_voice_dev = [None]         # "cuda" or "cpu": where the Kokoro voice runs
_voice_gpu_off = [0.0]      # after a GPU failure of the voice: the CPU until then
_broken = {}                # voice file -> when it may be tried again (a missing or unsupported file: never)
_kokoro_last = [None]       # the Kokoro voice last used (logged whenever it changes)
KOKORO_VOICES = ("bm_lewis", "bm_george", "bm_fable", "bm_daniel", "bf_emma", "am_michael", "am_adam", "af_heart")


def voice_rate():
    try:
        return max(-5, min(5, int(float(setting("JarvisVoiceRate", "1")))))
    except ValueError:
        return 1


def _wav_to_array(path):
    import numpy as np
    with wave.open(path, "rb") as wf:
        rate, ch, width = wf.getframerate(), wf.getnchannels(), wf.getsampwidth()
        raw = wf.readframes(wf.getnframes())
    if width != 2 or not raw:
        return None
    a = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    return (a.reshape(-1, ch) if ch > 1 else a), rate


def _kokoro(voice_path, text):
    import glob
    import numpy as np
    eng = _engines.get(voice_path)
    if eng is None:
        bins = sorted(glob.glob(os.path.join(os.path.dirname(voice_path), "voices*.bin")))
        if not bins:
            raise RuntimeError("voices-v1.0.bin is missing next to the Kokoro model - run SETUP")
        from kokoro_onnx import Kokoro
        import onnxruntime as rt
        # the full model on the RTX, through onnxruntime-gpu 1.23 (CUDA 12, the same libraries as Whisper):
        # measured 0.3 s a sentence vs 1.0 s on the CPU. The int8 model is 3x SLOWER on CUDA, so only the full one.
        full, sess = os.path.join(os.path.dirname(voice_path), "kokoro-v1.0.onnx"), None
        if (os.path.exists(full) and time.time() >= _voice_gpu_off[0] and gpu()
                and "CUDAExecutionProvider" in rt.get_available_providers()):
            _cuda_dlls()
            opts = rt.SessionOptions()
            opts.log_severity_level = 3                            # its per-run performance hints are noise
            # HEURISTIC: measured 0.9 s to load and 0.24 s a sentence vs 4.1 s and 0.37 s with the default search
            s = rt.InferenceSession(full, opts, providers=[("CUDAExecutionProvider", {"cudnn_conv_algo_search": "HEURISTIC"}),
                                                           "CPUExecutionProvider"])
            if s.get_providers()[0] == "CUDAExecutionProvider":
                sess, used = s, full
        _voice_dev[0] = "cuda" if sess else "cpu"
        if sess is None:
            # our own session, to cap its threads: measured 25% of the machine instead of 50%, 0.6 s slower per sentence
            opts = rt.SessionOptions()
            opts.intra_op_num_threads = cpu_threads()
            sess, used = rt.InferenceSession(voice_path, opts, providers=["CPUExecutionProvider"]), voice_path
        eng = _engines[voice_path] = Kokoro.from_session(sess, bins[-1])
        log(f"kokoro loaded ({os.path.basename(used)}, {os.path.basename(bins[-1])}), "
            + ("on the GPU" if _voice_dev[0] == "cuda" else f"{cpu_threads()} threads on the CPU"))
    name = (setting("JarvisKokoroVoice", "bm_lewis").strip().strip('"').split() or ["bm_lewis"])[0]
    try:
        known = list(eng.get_voices())
    except Exception:
        known = []
    if known and name not in known:
        log(f"kokoro voice '{name}' doesn't exist - using bm_lewis (available: {', '.join(known)})")
        name = "bm_lewis" if "bm_lewis" in known else known[0]
    if _kokoro_last[0] != name:
        _kokoro_last[0] = name
        log(f"kokoro speaking with voice {name}")
    speed = max(0.6, min(1.6, 1.0 + (voice_rate() - 1) * 0.08))
    lang = "en-gb" if name[:1] == "b" else "en-us"
    try:
        samples, rate = eng.create(text, voice=name, speed=speed, lang=lang)
    except Exception:
        if _voice_dev[0] == "cuda":
            # shortcut: the CPU until the next idle unload (or 10 minutes), the GPU watch moves only Whisper back
            _voice_gpu_off[0] = time.time() + 600              # synth_audio's retry builds the CPU voice
        raise
    return np.asarray(samples, dtype=np.float32).reshape(-1), int(rate)


def _piper(voice_path, text):
    eng = _engines.get(voice_path)
    if eng is None:
        from piper import PiperVoice
        eng = _engines[voice_path] = PiperVoice.load(voice_path)
    fd, path = tempfile.mkstemp(suffix=".wav", prefix="jarvis_")
    os.close(fd)
    try:
        length = 1.0 - voice_rate() * 0.06
        with wave.open(path, "wb") as wf:
            if hasattr(eng, "synthesize_wav"):
                try:
                    from piper import SynthesisConfig
                    eng.synthesize_wav(text, wf, syn_config=SynthesisConfig(length_scale=length))
                except ImportError:
                    eng.synthesize_wav(text, wf)
            else:
                eng.synthesize(text, wf, length_scale=length)
        return _wav_to_array(path)
    finally:
        try:
            os.remove(path)
        except OSError:
            pass


def _windows(text):
    fd, path = tempfile.mkstemp(suffix=".wav", prefix="jarvis_")
    os.close(fd)
    # Escape path for PowerShell
    safe_path = path.replace("\\", "/")
    ps = ("Add-Type -AssemblyName System.Speech; $s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
          "$v = $s.GetInstalledVoices() | Where-Object { $_.VoiceInfo.Culture.Name -eq 'en-GB' } | Select-Object -First 1; "
          f"if ($v) {{ $s.SelectVoice($v.VoiceInfo.Name) }}; $s.Rate = {voice_rate()}; "
          f"$s.SetOutputToWaveFile('{safe_path}'); $s.Speak([Console]::In.ReadToEnd()); $s.Dispose()")
    try:
        p = subprocess.Popen(["powershell", "-NoProfile", "-NonInteractive", "-Command", ps], stdin=subprocess.PIPE,
                             creationflags=NO_WINDOW, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        data, end = text.encode("utf-8"), time.time() + 60
        while True:                                            # a stop kills it at once, not after the whole sentence
            try:
                p.communicate(data, timeout=0.1)
                break
            except subprocess.TimeoutExpired:
                data = None                                    # sent once; later calls only wait
                if cancel.is_set() or time.time() > end:
                    p.kill()
                    p.wait()
                    if cancel.is_set():
                        return None
                    raise
        if os.path.exists(path) and os.path.getsize(path) > 100:
            return _wav_to_array(path)
        return None
    except (OSError, subprocess.TimeoutExpired) as e:
        log(f"windows voice failed: {e}")
        return None
    finally:
        try:
            if os.path.exists(path):
                os.remove(path)
        except OSError:
            pass


_resolved = set()


def resolve_voice(voice):
    """If JarvisVoice points at a missing file or an old Kokoro v0.19 model, use a kokoro-v1*.onnx found in the
    same folder (or in @Resources\\Jarvis\\kokoro) instead, so downloading the v1.0 files is all that's needed."""
    import glob
    base = os.path.basename(voice).lower()
    if "kokoro" not in base or (os.path.exists(voice) and not re.search(r"v0[._]", base)):
        return voice
    for folder in (os.path.dirname(voice), os.path.join(RES, "Jarvis", "kokoro")):
        found = sorted(glob.glob(os.path.join(folder, "kokoro-v1*.onnx")))
        if found:
            if voice not in _resolved:
                _resolved.add(voice)
                log(f"voice {os.path.basename(voice)} replaced by {found[-1]}")
            return found[-1]
    return voice


def synth_audio(text):
    """Text -> (samples float32, sample_rate), or None if no voice could speak it."""
    voice = setting("JarvisVoice", "").strip().strip('"')
    if voice:
        voice = resolve_voice(os.path.join(RES, voice))        # a relative path is relative to @Resources
    if voice and time.time() >= _broken.get(voice, 0):
        if not os.path.exists(voice):
            log(f"voice file not found: {voice} - using the Windows voice")
            problem("Voice file not found - using the Windows voice (check JarvisVoice)", popup=False)
            _broken[voice] = float("inf")
        elif re.search(r"kokoro.*v0[._]", os.path.basename(voice).lower()):
            msg = ("Kokoro v0.19 isn't supported - put kokoro-v1.0.onnx and voices-v1.0.bin in "
                   + os.path.dirname(voice))
            log(msg)
            problem(msg, popup=False)
            _broken[voice] = float("inf")
        else:
            for again in (True, False):                        # one failure is retried at once, with a fresh engine
                try:
                    out = (_kokoro if "kokoro" in os.path.basename(voice).lower() else _piper)(voice, text)
                    if out is not None:
                        return out
                    break
                except Exception as e:
                    _engines.pop(voice, None)
                    if not again:
                        problem(f"Voice failed twice ({type(e).__name__}) - the Windows voice for a minute", popup=False)
                        _broken[voice] = time.time() + 60
    return _windows(text)


def play_samples(a, rate):
    """Play audio, writing its loudness to the HUD as it goes (that's what moves the hologram)."""
    import numpy as np
    import sounddevice as sd
    ch = 1 if a.ndim == 1 else a.shape[1]
    block = max(1, int(rate * 0.04))
    try:
        with sd.OutputStream(samplerate=rate, channels=ch, dtype="float32") as out:
            for i in range(0, len(a), block):
                if cancel.is_set():
                    out.abort()                                # drop what is queued: silent now, not after the buffer
                    break
                chunk = np.ascontiguousarray(a[i:i + block], dtype=np.float32)
                out.write(chunk)
                S.set(level=min(1.0, float(np.sqrt(np.mean(chunk * chunk)) + 1e-9) / 0.18), force=False)
    finally:
        S.set(level=0.0)


def speak_all(sentences):
    """Synthesize the next sentence while the current one plays. If speech fails, the words go to the pop-up."""
    q = queue.Queue(maxsize=3)
    failed, broke, timed, gone, t0 = [], [], [], threading.Event(), time.time()

    def put(item):
        while not gone.is_set():                               # the reader left (cancelled): stop, don't wait on a full queue
            try:
                return q.put(item, timeout=0.5)
            except queue.Full:
                pass

    def producer():
        try:
            for s in sentences:
                if cancel.is_set() or gone.is_set():
                    break
                clean = re.sub(r"[*_#`>\[\]]", "", s).strip()
                if not clean:
                    continue
                t1 = time.time()
                try:
                    audio = synth_audio(clean)
                except Exception as e:
                    log(f"speech failed: {e}")
                    audio = None
                if not timed:
                    timed.append(1)
                    log(f"timing: reply start -> first sentence {t1 - t0:.2f}s, its voice {time.time() - t1:.2f}s")
                if audio is None:
                    failed.append(clean)
                put((audio, clean))
        except Exception as e:                                 # the model stream broke: hand it to the turn
            broke.append(e)
        finally:
            put(None)                                          # always: the reader is waiting for this

    threading.Thread(target=producer, daemon=True).start()
    try:
        _speak_queue(q, t0)
    finally:
        gone.set()
    live("")
    if broke:
        raise broke[0]
    if failed:
        problem("Couldn't speak (voice failed) - the reply is in the log", popup=False)


def _speak_queue(q, t0):
    filler_done()                                              # never talk over a status phrase
    first, spoken, shown = True, "", False
    while True:
        try:
            item = q.get(timeout=0.5)
        except queue.Empty:
            if cancel.is_set():                                # cancelled while a sentence was still being made
                break
            continue
        if item is None or cancel.is_set():                    # stopped: the rest is never said
            break
        audio, said = item
        spoken = (spoken + " " + said).strip()
        if audio is not None and JARVIS_WORD.search(said):     # his own "Jarvis" must not wake the barge-in
            name_until[0] = time.time() + len(audio[0]) / audio[1] + 1.0
        if first:
            S.set(state="speaking")
            log(f"timing: reply start -> first audio {time.time() - t0:.2f}s")
            first = False
        # muted mid-reply, or the voice failed: show the words instead
        if (muted() and setting("JarvisMutedPopup", "1") == "1") or audio is None:
            if not shown:
                S.set(pop="open")
                shown = True
            live(spoken)
        if audio is None:
            cancel.wait(min(3.0, 0.06 * len(said)))           # reading time instead of speaking time
            continue
        try:
            if not cancel.is_set():
                play_samples(audio[0], audio[1])
        except Exception as e:
            log(f"playback failed: {e}")
            if not shown:
                S.set(pop="open")
                shown = True
            live(spoken)


def first_words():
    """JarvisFirstWords: how many words of the reply to wait for before he starts talking (default 5)."""
    try:
        return max(0, min(12, int(float(setting("JarvisFirstWords", "5")))))
    except ValueError:
        return 5


def sentences_from(stream, collected):
    """Chunks of the streaming reply to speak. The FIRST chunk is released as soon as its Nth word is complete (or at
    the end of a shorter sentence), so he starts talking while the model is still writing; after that, whole sentences."""
    buf, first, n = "", True, first_words()
    for piece in stream:
        buf += piece
        collected.append(piece)
        while True:
            m = re.search(r"(.+?[.!?])(\s+|$)", buf)
            if m and m.end() == len(buf) and not buf.endswith((" ", "\n")):
                m = None
            m2 = re.match(r"\s*(?:\S+\s+){%d}" % n, buf) if (first and n) else None
            if m and (m2 is None or m.end() <= m2.end()):
                out, buf = m.group(1), buf[m.end():]
            elif m2:
                out, buf = m2.group(0).strip(), buf[m2.end():]
            else:
                break
            first = False
            if out.strip():
                yield out
    if buf.strip():
        yield buf


# ------------------------------------------------------------------ conversation log (for the pop-up)
def convo_add(who, text):
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return
    try:
        lines = []
        if os.path.exists(CONVO_FILE):
            with open(CONVO_FILE, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.read().splitlines()[-299:]
        lines.append(f"{who}|{int(time.time())}|{text}")
        tmp = CONVO_FILE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        os.replace(tmp, CONVO_FILE)
    except OSError:
        pass


def live(text):
    try:
        tmp = LIVE_FILE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(f"J|{int(time.time())}|{re.sub(chr(10), ' ', text)}\n" if text else "")
        os.replace(tmp, LIVE_FILE)
    except OSError:
        pass


def muted():
    try:
        return speakers_mute()                                 # the file below can be seconds old, or left by a HUD that is off
    except Exception:
        pass
    try:
        with open(ENV_FILE, "r", encoding="utf-8") as f:
            return "MUTED 1" in f.read()
    except OSError:
        return False


SHOW_LOG = re.compile(r"\b(show|open|display|pull up|bring up|let me see)\b.*\b(log|transcript|history|conversation|chat|"
                      r"what (you've|you have|you) said|everything you said|what you said)\b", re.I)
HIDE_LOG = re.compile(r"\b(close|hide|dismiss|get rid of)\b.*\b(log|transcript|history|conversation|chat|pop ?up|window)\b", re.I)


def say_text_only(sentences, collected):
    """Speakers muted: stream the reply into the pop-up instead of speaking it."""
    S.set(state="speaking", pop="open")
    text, t0 = "", time.time()
    for s in sentences:
        if cancel.is_set():
            break
        text = (text + " " + s).strip()
        live(text)
        S.set(level=0.25 + 0.2 * abs(((time.time() - t0) * 2) % 2 - 1), force=False)
    live("")


# ------------------------------------------------------------------ skills: fillers, actions, guardrails
# 1. Status fillers - common phrases are spoken into memory at startup, so when a slower route starts (searching
#    your notes, scanning apps) Jarvis says "Searching your notes." instantly while the work runs alongside.
# 2. Actions - a small whitelist. Safe ones (open an app, mute) run at once; ones that change or stop things (close an
#    app, lock, sleep, restart, shut down) are staged and need a spoken "yes" within 15 s - he listens for it himself.
# 3. Guardrails - nothing outside the whitelist is ever executed. Destructive or joke requests ("self-destruct",
#    "delete system32") go to the model in persona with a note that nothing will run, so he plays along drily.
FILLERS = {"notes": "Searching your notes.", "apps": "Scanning installed applications.",
           "confirm_wait": "One moment.", "cancelled": "Cancelled.", "done": "Done."}
_filler_audio = {}
_filler_voice = [None]
_filler_thread = [None]


def prepare_fillers():
    """Speak the status phrases into memory with the current voice (re-done if you switch voices)."""
    voice = setting("JarvisVoice", "") + "|" + setting("JarvisKokoroVoice", "") + "|" + str(voice_rate())
    if _filler_voice[0] == voice:
        return
    for key, text in FILLERS.items():
        try:
            a = synth_audio(text)
            if a is not None:
                _filler_audio[key] = a
        except Exception as e:
            log(f"filler '{key}' failed: {e}")
    _filler_voice[0] = voice


def filler(key, quiet):
    """Start a cached status phrase at once, in the background (returns immediately). Muted: shown instead."""
    if quiet:
        live(FILLERS[key])
        return
    a = _filler_audio.get(key)
    if a is None:
        return

    def go():
        try:
            play_samples(a[0], a[1])
        except Exception as e:
            log(f"filler playback failed: {e}")
    t = threading.Thread(target=go, daemon=True)
    _filler_thread[0] = t
    t.start()


def filler_done():
    """Wait for a filler that's still playing, so the answer never talks over it."""
    t = _filler_thread[0]
    if t is not None:
        t.join(timeout=5)
        _filler_thread[0] = None


def vault_dir():
    v = setting("JarvisVault", "").strip().strip('"')
    if v and os.path.isdir(v):
        return v
    todo = setting("ObsidianTodo", "").strip().strip('"')
    d = os.path.dirname(todo) if todo and os.path.exists(todo) else ""
    for _ in range(4):                                         # the to-do note's folder, or up to three folders above it
        if d and os.path.isdir(os.path.join(d, ".obsidian")):  # only a real vault: a to-do note in Downloads is not one
            return d
        d = os.path.dirname(d)
    return ""


def search_notes(query, limit=3):
    """Plain keyword search through the .md notes in your vault (no index or database needed). Best matches first."""
    root = vault_dir()
    words = [w for w in re.findall(r"[a-z0-9]{3,}", query.lower()) if w not in STOP]
    if not root or not words:
        return root, []
    hits, t0 = [], time.time()
    for dirpath, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if not d.startswith(".")]          # skip .obsidian, .trash
        for fn in files:
            if not fn.lower().endswith(".md"):
                continue
            path = os.path.join(dirpath, fn)
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    text = f.read(200_000)
            except OSError:
                continue
            low = text.lower()
            score = sum(low.count(w) for w in words) + 3 * sum(w in fn.lower() for w in words)
            if score:
                i = min((low.find(w) for w in words if w in low), default=0)
                snippet = re.sub(r"\s+", " ", text[max(0, i - 150):i + 350]).strip()
                hits.append((score, os.path.splitext(fn)[0], snippet))
        if time.time() - t0 > 4:                                      # huge vaults: stop after 4 s
            break
    hits.sort(key=lambda h: -h[0])
    return root, hits[:limit]


STOP = set("the and for with that this what when where which about from have your you are was were can could would "
           "should notes note vault search find look show tell my me any anything something".split())


def start_apps():
    """The installed apps the HUD scanned, or None while that list is missing (not the same as no apps)."""
    out = []
    try:
        with open(os.path.join(DATA, "StartApps.txt"), "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                if "|" in line:
                    name, appid = line.rstrip("\n").split("|", 1)
                    out.append((name.strip(), appid.strip()))
    except OSError:
        return None
    return out


def best_app(name):
    """The installed app whose name best matches what you said."""
    want = re.sub(r"[^a-z0-9 ]", "", name.lower()).strip()
    if not want:
        return None
    best, score = None, 0
    for disp, appid in start_apps() or []:
        d = disp.lower()
        if any(x in d for x in ("uninstall", "help", "readme", "documentation")):
            continue
        # a prefix needs 3+ letters and anything looser a whole word, so "open e" matches nothing
        sc = 3 if d == want else (2 if len(want) >= 3 and d.startswith(want) else
                                  (1 if re.search(r"\b" + re.escape(want) + r"\b", d) else 0))
        if sc > score or (sc == score and sc and best and len(disp) < len(best[0])):
            best, score = (disp, appid), sc
    return best if score else None


def running_window(name):
    """An open app (from the HUD's window list) whose exe matches what you said, e.g. 'chrome' -> chrome.exe."""
    want = re.sub(r"[^a-z0-9]", "", name.lower())
    stems = [(exe, re.sub(r"[^a-z0-9]", "", os.path.splitext(exe)[0].lower())) for exe in open_windows()]
    # exact name first, then a 3+ letter prefix, then a 4+ letter fragment: "close e" must not pick explorer
    for ok in (lambda s: s == want, lambda s: len(want) >= 3 and s.startswith(want), lambda s: len(want) >= 4 and want in s):
        for exe, stem in stems:
            if want and ok(stem):
                return exe
    return None


def _com(obj, slot, *args):
    """Call method number `slot` of a COM object; a failed HRESULT raises OSError."""
    fn = ctypes.WINFUNCTYPE(ctypes.HRESULT, ctypes.c_void_p, *(type(a) for a in args))
    return fn(ctypes.cast(obj, ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p)))[0][slot])(obj, *args)


def speakers(mute=None, volume=None):
    """The default speakers (Core Audio, IAudioEndpointVolume): set mute (True / False) and / or volume (0.0-1.0) when
    given, then return (muted, percent) as Windows reports them. A value Windows did not take raises OSError."""
    ole, P = ctypes.oledll.ole32, ctypes.c_void_p

    def guid(text):
        g = ctypes.create_string_buffer(16)
        ole.CLSIDFromString(ctypes.c_wchar_p(text), g)
        return ctypes.cast(g, P)
    ctypes.windll.ole32.CoInitialize(None)                    # once per thread; a repeat is harmless
    devices, device, vol, state, level = P(), P(), P(), ctypes.c_int(), ctypes.c_float(1)
    ole.CoCreateInstance(guid("{BCDE0395-E52F-467C-8E3D-C4579291692E}"), None, 23,
                         guid("{A95664D2-9614-4F35-A746-DE8DB63617E6}"), ctypes.byref(devices))
    try:
        _com(devices, 4, ctypes.c_int(0), ctypes.c_int(1), ctypes.pointer(device))       # GetDefaultAudioEndpoint
        _com(device, 3, guid("{5CDF2C82-841E-4546-9722-0CF74078229A}"), ctypes.c_uint(23), P(None), ctypes.pointer(vol))
        if volume is not None:
            _com(vol, 7, ctypes.c_float(volume), P(None))                                # SetMasterVolumeLevelScalar
        if mute is not None:
            _com(vol, 14, ctypes.c_int(bool(mute)), P(None))                             # SetMute
        _com(vol, 15, ctypes.pointer(state))                                             # GetMute
        _com(vol, 9, ctypes.pointer(level))                                              # GetMasterVolumeLevelScalar
    finally:
        for obj in (vol, device, devices):
            if obj:
                _com(obj, 2)                                                             # Release
    if mute is not None and bool(state.value) != bool(mute):
        raise OSError("Windows did not change the mute state")
    if volume is not None and abs(level.value - volume) > 0.01:
        raise OSError("Windows did not change the volume")
    return bool(state.value), round(level.value * 100)


def speakers_mute(on=None):
    """Set the mute state and return it. on=None only reads it, and counts a volume of 0 % as muted (nothing would
    be heard either way)."""
    is_muted, percent = speakers(mute=on)
    return is_muted or (on is None and percent <= 0)


def act_volume(change):
    how, n = change                                           # ("set", 30) or ("step", -10)
    if how == "step":
        n += speakers()[1]
    speakers(volume=max(0, min(100, n)) / 100)


MEDIA_KEYS = {"playpause": 0xB3, "next": 0xB0, "prev": 0xB1}


def press_key(vk):
    """Press and release one key. Windows gives no result back, so nobody can tell whether a player took it."""
    for flags in (0, 2):                                      # down, up
        ctypes.windll.user32.keybd_event(vk, 0, flags, 0)


def done_line(action, target):
    """What to say after an action that worked: the value Windows reports, never the one asked for."""
    if action == "open":
        return f"Opening {target[0]}."
    if action == "volume":
        return f"Volume at {speakers()[1]} percent."
    return "Sent." if action == "media" else "Done."


def run_ok(args):
    """Run one fixed command: anything but exit code 0 within 10 s is a failure (TimeoutExpired / OSError)."""
    code = subprocess.run(args, creationflags=NO_WINDOW, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                          timeout=10).returncode
    if code:
        raise OSError(f"{args[0]} ended with code {code}")


def open_windows():
    return re.findall(r"^W (.+)$", read_kv("windows.txt"), re.M)


# action handlers: (description for the confirmation, function). Only these can ever run.
def act_open(app):
    os.startfile("shell:AppsFolder\\" + app[1]) if not os.path.isabs(app[1]) else os.startfile(app[1])


def act_close(exe):
    if exe not in open_windows():                             # it went away while you were being asked
        raise OSError("it is not open any more")
    # taskkill only asks the windows to close, and its exit code is non-zero for any helper process without a
    # window (a browser has many), so the result is read from the HUD's window list instead (rewritten every 1.5 s)
    subprocess.run(["taskkill", "/IM", exe], creationflags=NO_WINDOW, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                   timeout=10)
    for _ in range(10):
        time.sleep(0.5)
        if exe not in open_windows():
            return
    raise OSError("it is still open (it may be asking to save)")


def act_lock(_):
    if not ctypes.windll.user32.LockWorkStation():
        raise OSError("Windows refused to lock")


def act_sleep(_):
    # asked directly so the answer comes back (rundll32 always exits 0); it returns once the PC wakes again
    if not ctypes.windll.powrprof.SetSuspendState(0, 1, 0):
        raise OSError("Windows refused to sleep")


ACTIONS = {
    "lock": act_lock,
    "sleep": act_sleep,
    "restart": lambda _: run_ok(["shutdown", "/r", "/t", "10"]),
    "shutdown": lambda _: run_ok(["shutdown", "/s", "/t", "10"]),
    "close": act_close,
    "open": act_open,
    "mute": lambda _: speakers_mute(True),
    "unmute": lambda _: speakers_mute(False),
    "volume": act_volume,
    "media": lambda key: press_key(MEDIA_KEYS[key]),
    "todo": lambda item: act_todo(item),
    "forget_all": lambda _: save_memory([]),
    "forget_talk": lambda gone: save_topics([t for t in load_topics() if t["talk"] not in gone]),   # M2b, after the read-back
    "forget_facts": lambda gone: save_memory([f for f in load_memory() if f not in gone]),           # M4a, after the read-back
    "replace_fact": lambda pair: save_memory([pair[1] if f == pair[0] else f for f in load_memory()]),
}

# the whole reply has to be one of these: "yes, but don't" is not a yes
YES = {"yes", "yeah", "yep", "yup", "sure", "confirm", "confirmed", "do it", "go ahead", "proceed", "affirmative", "ok",
       "okay", "please do", "yes please", "yes do it", "yes go ahead", "yes confirm", "yes i confirm", "i confirm"}


def confirmed(pending, answer, now):
    """True only for a plain yes to this pending action before it expires."""
    said = " ".join(re.sub(r"[^a-z]+", " ", (answer or "").lower()).split())
    return said in YES and now < pending["expires"]
DANGER = re.compile(r"self[- ]?destruct|system ?32|format (my|the|c)|wipe (my|the)|delete (all|every|my files|windows)|rm -rf|"
                    r"disable (the )?(antivirus|defender|firewall)|hack|brick|destroy|nuke|blow up|kill (all|every)", re.I)
NAMES = "travis jervis javis jarvus service droves drovis".split()   # how Whisper writes "Jarvis" (JarvisNameAliases adds more)
NEAR_MISS = "I heard a command but couldn't work it out. Try: set a timer for one minute."
CLAIM_LINE = "I didn't catch that as a command, so nothing changed. Say it again, like: set an alarm for 7 AM."
# a chat answer that says something was done: nothing runs on the chat path, so it cannot be true
CLAIM = re.compile(r"\b(?:alarm|timer|reminder|volume)s? (?:is |has been |was )?(?:set|added|changed|now|snoozed)\b|"
                   r"\bi(?:['’]ve| have) (?:set|turned|changed|opened|closed|muted|unmuted|added|created|scheduled|"
                   r"adjusted|connected|cancelled|canceled|snoozed|moved)\b", re.I)


def strip_name(text):
    """'Travis, set the volume' -> 'set the volume'. Only as the first words, after an optional hey / hi / ok; a
    misheard name needs the greeting or a comma after it, so "Service the car" and "Travis Scott is..." stay as said."""
    extra = [n.strip().lower() for n in setting("JarvisNameAliases", "").split(",") if n.strip()]
    names = "|".join(re.escape(n) for n in NAMES + extra)
    m = re.match(rf"\s*(?:(hey|hi|ok|okay)[,.]?\s+)?(?:(jarvis)|({names}))\b(?(1)\s*[,.!?]?|(?(2)\s*[,.!?]?|\s*[,.!?]))\s*",
                 text, re.I)
    if not m or not text[m.end():].strip():
        return text
    if m.group(3):
        log("name: heard as another word")                     # how often, never what was said
    return text[m.end():]


# ------------------------------------------------------------------ autocorrect: a command Whisper got slightly wrong
FILLER = re.compile(r"\b(?:please|could you|can you|would you|um+|uh+|so|like|just|for me|i want you to|go ahead and)\b,?", re.I)
SOUNDALIKE = [(r"\bthe value\b", "the volume"), (r"\btime are\b", "timer"), (r"\ba larm\b", "alarm"), (r"\bwon\b", "one"),
              (r"\bate\b", "eight"), (r"\bfor for\b", "for four"), (r"\bto+ (?=(?:minutes|seconds|hours)\b)", "two ")]
PHRASES = [(r"^(?:make|change) (?:the )?volume (?:to |at )?(\w+(?: \w+)?)$", r"set the volume to \1")]   # what route() misses
CMD_WORDS = ("volume mute unmute timer alarm reminder snooze cancel pause resume skip next previous track song louder "
             "quieter remind minutes seconds hours").split()
KEEP = set("minute second hour alarms timers reminders tracks songs volumes mutes muted music".split())   # already right


def tidy(text):
    """Filler words out, sound-alikes fixed, small-word variants put the way route() reads them."""
    t = " ".join(FILLER.sub(" ", strip_name(text)).split()).strip(" ,.!?")
    for pat, rep in SOUNDALIKE + PHRASES:
        t = re.sub(pat, rep, t, flags=re.I)
    return t


def fix_route(text, routed):
    """A chat line or near-miss of up to 8 words that becomes exactly one command once tidied or with one word swapped
    for a close command word (volyum -> volume) is that command; two different ones -> he asks. Otherwise as heard."""
    if not (routed[0] == "chat" or routed[3] == NEAR_MISS) or len(text.split()) > 8:
        return routed
    import difflib
    base = tidy(text)
    tries = [base] + [re.sub(rf"\b{w}\b", m, base, flags=re.I) for w in {w.lower() for w in re.findall(r"[A-Za-z]{4,}", base)}
                      if w not in CMD_WORDS and w not in KEEP for m in difflib.get_close_matches(w, CMD_WORDS, n=2, cutoff=0.8)]
    found = {}
    for t in tries:
        r = route(t)
        if r[0] in ("act", "remind", "level", "multi") and r[3] != NEAR_MISS:
            found.setdefault((r[0], r[1], re.sub(r"\.\d+", "", repr(r[2]))), (t, r))   # due times differ by microseconds
    if len(found) == 1:
        r = next(iter(found.values()))[1]
        log(f"autocorrect: {r[0]} {r[1]}")                     # what kind, never the words
        return r
    if len(found) > 1:
        a, b = [t for t, _ in found.values()][:2]
        log("autocorrect: two readings - asked")
        return ("say", None, None, f"Did you mean {a} or {b}? Say it once more.")
    return routed


def no_claims(sentences, collected):
    """The chat answer as it is spoken: a sentence that says an action was done is replaced, and the answer ends there."""
    for s in sentences:
        if CLAIM.search(s):
            log("chat answer claimed an action - replaced")
            collected[:] = [CLAIM_LINE]
            yield CLAIM_LINE
            return
        yield s


ORDINALS = ("first", "second", "third", "fourth", "fifth", "sixth", "seventh", "eighth", "ninth", "tenth")
# M1b: "cancel the second one", "open it again". "cancel that" stays undo; "stop it" is left alone (stop is for ringing)
REFER = re.compile(rf"(cancel|delete|remove|turn off|open|reopen|launch|close|quit|exit) (?:the )?(?:({'|'.join(ORDINALS)}|last) "
                   r"(?:one|alarm|reminder|timer|app)|(?:that|this) (?:one|alarm|reminder|timer|app)|it)(?: again)?")


def pick_last(cmd):
    """M1b: a sentence that points at what he just listed or acted on -> the route for that item, as if it had been said
    by name; "Which one?" when nothing fits. None when the sentence does not point back. Code picks, never the model."""
    m = REFER.fullmatch(cmd)
    if not m:
        return None
    app = m.group(1) in ("open", "reopen", "launch", "close", "quit", "exit")
    fresh = time.time() - last.get("when", 0) <= ACTIVE_TTL and (last.get("kind") == "app") == app
    items = last["items"] if fresh else []
    nth = m.group(2)
    i = (-1 if nth == "last" else ORDINALS.index(nth)) if nth else 0 if len(items) == 1 else None   # "it" needs one item
    if i is None or not -len(items) <= i < len(items):
        return ("say", None, None, "Which one?")
    if not app:
        return ("remind", "cancel", (last["kind"], "", items[i]), None)
    name = items[i][0] if isinstance(items[i], tuple) else os.path.splitext(items[i])[0]   # opened (name, id) / closed exe
    if REFER.fullmatch(f"open {name}".lower()):                 # an app called "it" would point back here forever
        return ("say", None, None, "Which one?")
    if m.group(1) in ("open", "reopen", "launch"):
        return route(f"open {name}")
    r = route(f"close {name}")
    return r if r[0] == "act" else route(f"close {name.split()[-1]}")   # "Google Chrome" is open as chrome.exe


def route(text):
    """Map what you said to (kind, action, target, confirmation prompt). kind: chat | notes | apps | act | guard | say |
    remind (action = list / cancel / set / flip, target = its details) | memory (action = save / list / forget) | brief |
    fact (prompt = the answer) | undo | heard | again | level (the volume, read in turn) | multi (target = the routes)."""
    said = strip_name(text)
    named, text = said != text, said
    t = text.strip().lower().rstrip(".!?")
    # "then change the volume", "Okay, set an alarm": a word that joins it to the last sentence is not the command
    t = re.sub(r"^(?:(?:and|then|so|now|okay|ok|alright|um|uh|yo|hey|hi)[,.]? +)+|,? please$", "", t)
    if DANGER.search(t):
        return ("guard", None, None, None)
    # actions only for commands ("lock my computer", "jarvis, could you open chrome"), never for questions about them
    # ("should I restart my computer?", "how do I close a for loop?")
    whole = cmd = re.sub(r"^(hey |ok |okay )?(jarvis[, ]+)?(please |can you |could you |would you |will you )?(please )?", "", t).strip()
    if text.strip().endswith("?") and cmd == t and not named:   # "Jarvis, ...?" was a command before the name moved out
        cmd = ""
    if re.fullmatch(r"undo(?: that| it)?|put it back|cancel that|take that back", whole):
        return ("undo", None, None, None)
    if re.search(r"\bnever ?mind\b|\bactually,? (?:don'?t|do not|no)\b", whole):   # "set a timer for... never mind"
        return ("say", None, None, "Okay, never mind.")
    # "no, AM" / "I meant the evening" just after a clock time was set: moved 12 hours (remind_reply). "Morning." alone
    # is a greeting, so a part of the day needs the "no" / "I meant" in front
    m = re.fullmatch(r"((?:no,? |i meant |make (?:it|that) )*)(?:in the |the |at )?(a\.? ?m|p\.? ?m|morning|afternoon|evening|night)", whole)
    if m and (m.group(1) or len(m.group(2)) <= 4) and undo and undo[1] == "reminder" and time.time() < undo[0]:
        return ("remind", "flip", ("alarm", "am" if m.group(2) == "morning" or m.group(2)[:2] in ("a.", "am", "a ") else "pm"), None)
    # read from Windows each time (turn), never from what the model or the chat remembers
    if re.fullmatch(r"what(?:'s| is) the (?:current )?volume(?: at| set to| now)?|how loud is it|is (?:it|the sound|the volume) muted", whole):
        return ("level", None, None, None)
    if re.fullmatch(r"what did you (?:just )?hear|what did i (?:just )?say", whole):
        return ("heard", None, None, None)
    if re.fullmatch(r"(?:say|repeat) (?:that|it) again|repeat that|come again|what did you (?:just )?say", whole):
        return ("again", None, None, None)
    if re.match(r"snooze\b", cmd):                             # after it stopped ringing (while it rings, alarm() hears it)
        return ("remind", "snooze", ("alarm", snooze_for(cmd)), None)
    picked = pick_last(cmd)
    if picked:
        return picked
    op = reminder_cmd(t, cmd, time.time())
    if op:
        return ("remind", op[0], op[1:], None)
    if re.fullmatch(r"(?:good (?:morning|afternoon|evening)|brief me|(?:give me )?(?:my |the )?daily briefing|"
                    r"what.?s my day look(?:ing)? like)(?:,? jarvis)?", whole):
        return ("brief", None, None, None)
    # M2b, talk filed by topic: forgetting reads them back and waits for yes; the list is said by code, not the model
    m = re.fullmatch(r"(?:forget|delete|erase) (?:what|everything) (?:we|i)(?:'ve| have)? (?:said|talked|spoken|spoke|"
                     r"discussed) about (.+)", whole)
    if m:
        return talk_forget(m.group(1))
    m = re.fullmatch(r"what do you (?:remember|recall) about (.+)|what (?:did|have) we (?:say|said|talk|talked|discuss|"
                     r"discussed) about (.+)", whole)
    if m:
        return ("say", None, None, talk_list(m.group(1) or m.group(2)))
    # remembered facts. "do you remember that film?" and "remember to buy milk" are not for this
    if re.fullmatch(r"what do you remember|what have i (?:told|asked) you to remember|"
                    r"(?:list|show|read)(?: me)? (?:my |your )?memor(?:y|ies)|what.?s in your memory", whole):
        return ("memory", "list", None, None)
    m = (re.match(r"(?:(?:oh|also|and),? )*(?:i (?:want|need) you to )?remember[,:]? (?:that )?(?!to )(?!(?:that|it|this)$)(.+)", cmd)
         or re.match(r"(?:note|(?:don't|do not) forget|keep in mind) that (\S+ .+)", cmd)   # two words: not "note that down"
         or re.fullmatch(r"(?!.*\?)(\S+ .+?)[,.;!] (?:(?:please )?remember (?:that|this|it)|(?:don't|do not) forget (?:that|it)|"
                         r"keep (?:that|this|it) in mind)", cmd))   # "my sister's name is Ana, remember that"
    if m:
        return fact_save(as_said(text, m.group(1)))
    m = re.fullmatch(r"what do you know about (.+)", whole)      # M4a: your own words, by code; nothing saved -> the model
    if m:
        try:
            hits = facts_about(m.group(1))
        except (OSError, ValueError):
            return ("say", None, None, MEMORY_BAD)
        if hits:
            return ("say", None, None, "You told me: " + "; ".join(hits) + ".")
    if re.match(r"forget (?:everything|all)\b", cmd):
        try:
            n = len(load_memory())
        except (OSError, ValueError):
            return ("say", None, None, MEMORY_BAD)
        if not n:
            return ("say", None, None, "You haven't asked me to remember anything.")
        return ("act", "forget_all", None, f"Forget all {n} thing{'s' if n != 1 else ''} I remember? Confirm with yes.")
    m = re.match(r"forget (?:that |about |the )*(.+)", cmd)
    if m and m.group(1) not in ("it", "that", "this", "about it", "about that"):
        try:
            gone = [f for f in load_memory() if holds_words(f, m.group(1))]
        except (OSError, ValueError):
            return ("say", None, None, MEMORY_BAD)
        if len(gone) > 1:                                      # M4a: more than one: read back, wait for yes
            return ("act", "forget_facts", gone, f"Forget {len(gone)} things: {'; '.join(gone)}? Confirm with yes.")
        return ("memory", "forget", m.group(1), None)
    # "add buy milk to my to-do list", "add a task: renew passport". It writes into your note, so he asks first
    m = (re.match(r"(?:add|put) (.+?) (?:to|on|in|onto) (?:my |the )?(?:to-do|to do|todo|task)s?(?: list)?$", cmd)
         or re.match(r"(?:add|new|create|make) (?:a |an )?(?:new )?(?:task|to-do|todo|to do)(?: item)?[:,]? (.+)$", cmd))
    if m:
        if not todo_note():
            return ("say", None, None, "No to-do note is set (Control Center, TO-DO NOTE).")
        item = " ".join(as_said(text, m.group(1)).split())[:200]
        return ("act", "todo", item, f"Add '{item}' to your to-do list? Confirm with yes.")
    m = re.search(r"\b(?:search|check|look (?:through|in)|find|what do)\b.*\b(?:my )?(?:notes?|vault|obsidian)\b(?:.*?\b(?:for|about|on)\b\s+(.+))?", t)
    if m:
        q = m.group(1) or re.sub(r"\b(search|check|look|through|in|find|what|do|my|notes?|vault|obsidian|say)\b", " ", t)
        return ("notes", None, q.strip(), None)
    m = re.search(r"\b(?:is|do i have)\s+(.+?)\s+installed\b|\b(?:what|which|list)\b.*\b(?:apps|applications|programs)\b.*\binstalled\b", t)
    if m:
        return ("apps", None, (m.group(1) or "").strip(), None)
    if re.match(r"lock (the |my )?(pc|computer|screen|laptop)\b", cmd):
        return ("act", "lock", None, "You want me to lock the PC. Confirm with yes.")
    if re.match(r"(go to sleep|put (the |my )?(pc|computer|laptop) to sleep|sleep (the |my )?(pc|computer|laptop))\b", cmd):
        return ("act", "sleep", None, "You want me to put the PC to sleep. Confirm with yes.")
    if re.match(r"(restart|reboot) (the |my )?(pc|computer|laptop|system)\b", cmd):
        return ("act", "restart", None, "You're asking me to restart the PC. Confirm with yes.")
    if re.match(r"(shut ?down|power off|turn off) (the |my )?(pc|computer|laptop|system)\b", cmd):
        return ("act", "shutdown", None, "You're asking me to shut down the PC. Confirm with yes.")
    m = re.match(r"(mute|unmute)( the)?( sound| audio| volume| speakers)?$", cmd)
    if m:
        return ("act", m.group(1), None, None)
    # "set the volume to 30 / thirty / max / half", "set it to 30", "max volume", "turn it all the way up"
    m = (re.match(r"(?:i (?:want|need) |i'?d like )?(?:(?:set|turn|change|put|raise|lower|bring) )?(?:the )?volume(?: up| down)? "
                  r"(?:to |at |on )?(?:the )?(.+?)(?: ?%| percent)?$", cmd)
         or re.match(r"(?:set|turn|change|put) it (?:to|at) (.+?)(?: ?%| percent)?$", cmd)
         or re.match(r"(max|maximum|full|half) volume$|(?:turn |put )?(?:it|the (?:sound|music)) (all the way (?:up|down))$", cmd))
    if m:
        word = m.group(m.lastindex)
        n = {"max": 100, "maximum": 100, "full": 100, "half": 50, "all the way up": 100, "all the way down": 0,
             "a hundred": 100, "one hundred": 100, "hundred": 100}.get(word, _num(word))
        if n is not None and n > 100:
            return ("say", None, None, "I can set it between 0 and 100.")
        if n is not None:
            return ("act", "volume", ("set", int(n)), None)
    soft = r"(?:a (?:bit|little|tad) |slightly )?"               # "a bit" is the same 10 steps as plain "louder"
    m = re.match(rf"{soft}(?:(?:turn |make )?(?:it |(?:the )?(?:volume|sound|music) ){soft}(up|down|louder|quieter)|"
                 rf"turn (up|down) (?:it|the (?:volume|sound|music))|(louder|quieter))(?: (?:a )?(?:bit|little|tad)(?: more)?| slightly|"
                 r" by (.+?)(?: ?%| percent)?)?$", cmd)
    n = m and (_num(m.group(4)) if m.group(4) else 10)        # "turn it up by 20"; a plain step is 10
    if m and n is not None:
        return ("act", "volume", ("step", int(n) if (m.group(1) or m.group(2) or m.group(3)) in ("up", "louder") else -int(n)), None)
    m = re.match(r"(raise|increase|boost|lower|decrease|reduce) (?:the )?(?:volume|sound|music)(?: (?:a )?(?:bit|little|tad)| slightly|"
                 r" by (.+?)(?: ?%| percent)?)?$", cmd)
    n = m and (_num(m.group(2)) if m.group(2) else 10)
    if m and n is not None:
        return ("act", "volume", ("step", int(n) if m.group(1) in ("raise", "increase", "boost") else -int(n)), None)
    thing = r"(?: (?:the |my |this )?(?:music|song|track|video|playback))"
    # shortcut: one play/pause key, so "play" while it plays pauses; Windows has no separate keys worth the code
    if re.match(rf"(?:(?:pause|play|resume|unpause){thing}?|stop{thing})$", cmd):
        return ("act", "media", "playpause", None)
    if re.match(r"(?:(?:play |skip to )?(?:the )?next(?: track| song)?|skip(?: (?:this |the )?(?:track|song))?)$", cmd):
        return ("act", "media", "next", None)
    if re.match(r"(?:(?:play |go back to )?(?:the )?(?:previous|last) (?:track|song)|go back a (?:track|song)|previous)$", cmd):
        return ("act", "media", "prev", None)
    m = re.match(r"(?:close|quit|exit|kill)\s+(?:the\s+)?(.+?)(?:\s+app(?:lication)?)?$", cmd)
    if m and not re.search(r"\b(log|transcript|history|conversation|chat|pop ?up|window)\b", m.group(1)):
        exe = running_window(m.group(1))
        if exe:
            return ("act", "close", exe, f"You want me to close {exe.replace('.exe', '')}. Unsaved work could be lost. Confirm with yes.")
        return ("say", None, None, f"I don't see {m.group(1)} open.")
    m = re.match(r"(?:open|launch|start|run)\s+(?:the\s+|up\s+)?(.+?)(?:\s+app(?:lication)?)?$", cmd)
    if m and not re.search(r"\b(log|transcript|history|conversation|chat|pop ?up)\b", m.group(1)):
        app = best_app(m.group(1))
        if app:
            return ("act", "open", app, None)                       # opening is harmless: no confirmation
        if start_apps() is None:
            return ("say", None, None, "The app list isn't ready yet.")
        # not an app ("run a speed test"): let the model answer
    answer = fact_answer(whole, time.time())
    if answer:
        return ("fact", None, None, answer)
    # "set an alarm for 7 and remind me to cook": two commands, run one after the other only when each is complete and
    # safe on its own (no confirmation); otherwise it is not split
    pieces = [p for p in re.split(r",? and (?:then )?|, then ", whole) if p.strip()]
    parts = [route(p) for p in pieces] if len(pieces) > 1 else []          # each piece is shorter: no endless recursion
    if parts and all(p[0] in ("remind", "level") and p[1] != "flip" and not (p[1] == "set" and p[2][1] is None)
                     or p[0] == "act" and p[3] is None for p in parts):       # a set with no time would ask: not split
        return ("multi", None, parts, None)
    # a command that no parser above took: said plainly, never handed to the model (it would answer "done")
    if (re.match(r"(?:i (?:want|need) (?:you )?to |i'?d like (?:you )?to )?(?:set|turn|change|open|close|mute|cancel|"
                 r"connect|snooze|switch)\b", cmd)
            and re.search(r"\b(?:volume|alarms?|timers?|reminders?|apps?|application|bluetooth|microphone|mic|brightness|"
                          r"screen|display|colou?r|settings?|wi-?fi|headphones|speakers?|sound)\b", cmd)
            and not re.match(r"(?:how|why|what|when|who|where|which|can you explain|could you explain)\b", t)):
        return ("say", None, None, NEAR_MISS)
    return ("chat", None, None, None)


ACTIONS_LOGGED = ("close", "open", "volume", "media")           # targets that are app names or levels, never your words


def run_action(action, target):
    try:
        before = speakers() if action in ("volume", "mute", "unmute") else None
        ACTIONS[action](target)
        log(f"action: {action} {target if target and action in ACTIONS_LOGGED else ''}")   # your words stay out of the log
        did_add(action, target)
        can_undo(action, before)                               # anything else (lock, close, a key...) cannot be put back
        if action in ("open", "close"):                        # M1b: "close it", "open it again"
            last.update(kind="app", items=[target], when=time.time())
        return True
    except Exception as e:
        did_add(action, target, False)
        log(f"action {action} failed: {e!r}")
        problem(f"Couldn't {action}: {str(e)[:80]}")
        return False


def reply_line(text, quiet):
    """Speak (or show) a short fixed reply and log it."""
    recent["me"] = text
    convo_add("J", text)
    filler_done()
    if quiet:
        S.set(pop="open")
        live(text)
        time.sleep(min(3.0, 0.06 * len(text)))
        live("")
    else:
        speak_all([text])


def hear(**opts):
    """Listen once more inside a turn and return the words ("" for silence or a click). `opts` go to listen()."""
    audio = listen(**opts) if not cancel.is_set() else None
    return strip_name(transcribe(audio)) if audio is not None else ""   # the "Jarvis" hotword can put the name before a "yes"


def as_said(text, part):
    """`part` was found in the lowercased text: give it back with the capitals it was said with."""
    i = text.lower().find(part)
    return text[i:i + len(part)] if i >= 0 else part


# ------------------------------------------------------------------ answers by code: the clock, dates, sums, conversions
# Exact and instant, where the model is slow and gets sums wrong. Words are parsed here; nothing said is run as code.
MONTHS = "january february march april may june july august september october november december".split()
WEEKDAYS = "monday tuesday wednesday thursday friday saturday sunday".split()
# dimension, factor to the dimension's base unit (temperature: which scale), what he says, the names it is heard as
UNIT_ROWS = """length .001 millimetres mm millimetre|length .01 centimetres cm centimetre|length 1 metres m metre
length 1000 kilometres km kms kilometre|length .0254 inches inch|length .3048 feet ft foot|length .9144 yards yd yard
length 1609.344 miles mi mile|weight .001 milligrams mg milligram|weight 1 grams g gram|weight 1000 kilograms kg kgs kilogram kilo
weight 28.349523125 ounces oz ounce|weight 453.59237 pounds lb lbs pound|weight 6350.29318 stone stone
weight 1000000 tonnes tonne ton|volume .001 millilitres ml millilitre|volume 1 litres l litre
volume .00492892159375 teaspoons tsp teaspoon|volume .01478676478125 tablespoons tbsp tablespoon
volume .0295735295625 fluid_ounces fl_oz fluid_ounce|volume .2365882365 cups cup|volume .473176473 pints pint
volume .946352946 quarts quart|volume 3.785411784 gallons gallon
speed .2777777777777778 kilometres_per_hour kph km/h kmh kilometre_per_hour|speed .44704 miles_per_hour mph mile_per_hour
speed 1 metres_per_second m/s metre_per_second|speed .5144444444444445 knots knot
area 1 square_metres square_metre|area 1000000 square_kilometres square_kilometre|area .09290304 square_feet square_foot
area 2589988.110336 square_miles square_mile|area 4046.8564224 acres acre|area 10000 hectares hectare
time 1 seconds s sec secs second|time 60 minutes min mins minute|time 3600 hours hr hrs hour|time 86400 days day
time 604800 weeks week|data .125 bits bit|data 1 bytes byte|data 1000 kilobytes kb kilobyte|data 1e6 megabytes mb megabyte
data 1e9 gigabytes gb gigabyte|data 1e12 terabytes tb terabyte
temp 0 degrees_Celsius c celsius centigrade|temp 1 degrees_Fahrenheit f fahrenheit|temp 2 kelvin k kelvin"""
UNITS = {}
for _row in UNIT_ROWS.replace("\n", "|").split("|"):
    _dim, _factor, _say, *_names = _row.split()
    for _name in [_say.lower()] + _names:
        UNITS[_name.replace("_", " ")] = (_dim, float(_factor), _say.replace("_", " "))


def for_ear(x):
    """108.0 -> '108', 34.2857 -> 'about 34.3', 0.123456 -> 'about 0.123'."""
    r = float(f"{x:.3g}") if abs(x) < 1 else round(x, 2 if abs(x) < 10 else 1)
    s = f"{r:f}".rstrip("0").rstrip(".")
    return s if abs(r - x) < 1e-9 else "about " + s


def on_day(s, today):
    """'friday', 'the 3rd', 'december 25th', 'the 25th of december' -> the next such date from today, or None."""
    s = re.sub(r"^(?:next |this |the )", "", s)
    if s in WEEKDAYS:
        return today + timedelta((WEEKDAYS.index(s) - today.weekday() - 1) % 7 + 1)
    months = "|".join(MONTHS)
    m = re.fullmatch(rf"(?:({months}) (?:the )?)?(\d{{1,2}})(?:st|nd|rd|th)?(?: of ({months}))?", s)
    if not m or (m.group(1) and m.group(3)):
        return None
    month = MONTHS.index(m.group(1) or m.group(3)) + 1 if m.group(1) or m.group(3) else None
    try:
        d = today.replace(month=month or today.month, day=int(m.group(2)))
        if d < today:
            d = d.replace(year=d.year + 1) if month else (d.replace(day=1) + timedelta(32)).replace(day=d.day)
        return d
    except ValueError:                                         # February 30th, or the 31st of a short month
        return None


def calc(q):
    """'12 times 9', 'fifteen percent of 240', 'square root of 81' -> the line to say, or None."""
    # shortcut: one operation per sum ("2 plus 3 times 4" goes to the model); chains would need precedence rules
    q = re.sub(r"(?<=\d),(?=\d{3}\b)", "", q).replace("%", " percent")
    q = re.sub(r"(?<=\d) ?([-+*/×^]) ?(?=\d)", r" \1 ", q)
    m = re.fullmatch(r"(?:the )?square root of (.+)", q)
    if m:
        a, op, b = _num(m.group(1)), "root", 0
    else:
        m = re.fullmatch(r"(.+?) (?:(squared|cubed)|(plus|minus|times|x|multiplied by|divided by|over|to the power of|"
                         r"percent of|[-+*/×^]) (.+))", q)
        if not m:
            return None
        a, op = _num(m.group(1)), m.group(2) or m.group(3)
        b = {"squared": 2, "cubed": 3}[op] if m.group(2) else _num(m.group(4))
    if a is None or b is None:
        return None
    if max(a, b) > 1e12:
        return "That number is too big to say."
    op = {"plus": "+", "minus": "-", "times": "*", "x": "*", "×": "*", "multiplied by": "*", "divided by": "/",
          "over": "/", "squared": "^", "cubed": "^", "to the power of": "^", "percent of": "%"}.get(op, op)
    if op == "/" and not b:
        return "You can't divide by zero."
    if op == "^" and a > 1 and b * math.log10(a) > 15:        # refused before it is worked out, never after
        return "That number is too big to say."
    x = {"root": lambda: math.sqrt(a), "+": lambda: a + b, "-": lambda: a - b, "*": lambda: a * b, "/": lambda: a / b,
         "^": lambda: a ** b, "%": lambda: a * b / 100}[op]()
    return "That number is too big to say." if abs(x) > 1e15 else for_ear(x).capitalize() + "."


def unit(s):
    s = re.sub(r"^degrees? ", "", s).replace("meter", "metre").replace("liter", "litre").replace("s per ", " per ")
    return UNITS.get(s) or (UNITS.get(s[:-1]) if s.endswith("s") else None)


def amount(s):
    """'26 miles', 'twenty six miles', '5 feet 10' -> (number, unit row), or None."""
    s = re.sub(r"(?<=\d)(?=[a-z])", " ", s)
    m = re.fullmatch(r"(.+?) (?:feet|foot|ft) (?:and )?(.+?)(?: inch(?:es)?)?", s)
    if m and _num(m.group(1)) is not None and _num(m.group(2)) is not None:
        return _num(m.group(1)) * 12 + _num(m.group(2)), UNITS["inch"]
    w = s.split()
    for i in range(1, len(w)):
        n, u = _num(" ".join(w[:i])), unit(" ".join(w[i:]))
        if n is not None and u:
            return n, u
    return None


def convert(q):
    """'how many km in 26 miles', '100 fahrenheit in celsius' -> the line to say, or None."""
    m = re.fullmatch(r"how many (.+?) (?:are )?(?:there )?(?:in|is|are) (.+)", q)
    if m:
        dst, src = m.groups()
    else:
        m = re.fullmatch(r"(?:convert )?(.+) (?:in|to|into|as) (.+)", q)
        if not m:
            return None
        src, dst = m.groups()
    have, want = amount(src), unit(dst)
    if not have or not want or have[1][0] != want[0] or have[0] > 1e12:
        return None
    (n, (dim, f, _)), (_, g, say) = have, want
    if dim == "temp":
        c = [n, (n - 32) * 5 / 9, n - 273.15][int(f)]
        x = [c, c * 9 / 5 + 32, c + 273.15][int(g)]
    else:
        x = n * f / g
    return f"{for_ear(x).capitalize()} {say}."


def fact_answer(q, now):
    """A question the code answers exactly -> the line to say, or None (it goes to the model as before)."""
    q = re.sub(r"^(?:tell me |do you know )", "", re.sub(r"\bwhat['’]?s\b", "what is", q))
    today = datetime.fromtimestamp(now).date()
    if re.fullmatch(r"what time is it(?: now)?|what time it is|what is the time(?: now)?|the time", q):
        return f"It's {clock(now, now)}."
    if re.fullmatch(r"what is (?:the|today's) date(?: today)?|what date is it(?: today)?|(?:the|today's) date", q):
        return f"It's {today:%A}, {today:%B} {today.day}."
    if re.fullmatch(r"what day is (?:it|today)(?: today)?|what day of the week is it", q):
        return f"It's {today:%A}."
    m = re.fullmatch(r"what (?:is |will )?(?:the )?(?:date|day)(?: is it| will it be| be)? in (.+?) (days?|weeks?)", q)
    n = m and _num(m.group(1))
    if n is not None and n <= 3650:
        d = today + timedelta(n * (7 if m.group(2).startswith("week") else 1))
        return f"That's {d:%A}, {d:%B} {d.day}" + ("." if d.year == today.year else f", {d.year}.")
    m = re.fullmatch(r"what day is (.+)", q)
    d = m and on_day(m.group(1), today)
    if d:
        return f"{d:%B} {d.day} is a {d:%A}."
    m = re.fullmatch(r"how many days (?:until|till|til|to|before) (.+)", q)
    d = m and on_day(m.group(1), today)
    if d:
        n = (d - today).days
        return "That's today." if not n else f"{n} day{'s' if n != 1 else ''} until {d:%A}, {d:%B} {d.day}."
    q = re.sub(r"^(?:what is |how much is |calculate |work out )", "", q)
    return calc(q) or convert(q)


# ------------------------------------------------------------------ "undo that", "what did you hear?", "say that again"
UNDO_FOR = 120                                                # seconds
undo = []                                                     # [expires, what, before]: the last change, memory only
recent = {"you": "", "me": ""}                                # the last thing heard and said, memory only, never logged
offer = {}            # M4a-3: a fact he offered to remember {fact, expires}; memory only, never logged
last = {}             # M1b: the list he just read out or the one thing he acted on {kind, items, when}; memory only, never logged


# M4b: the last 20 actions really run (time, what, worked), memory only, never logged. Fed by run_action, can_undo
# (facts and reminders), snoozes and undo; questions about him get it in the prompt (DID_ASK).
did = []
DID = {"lock": "locked the PC", "sleep": "put the PC to sleep", "restart": "started a restart", "shutdown": "started a shutdown",
       "mute": "muted the sound", "unmute": "unmuted the sound", "volume": "changed the volume", "media": "pressed a media key",
       "todo": "added a to-do", "forget_all": "forgot all saved facts", "forget_talk": "forgot earlier talks",
       "forget_facts": "forgot saved facts", "replace_fact": "replaced a saved fact", "fact": "saved a fact",
       "forget": "forgot a saved fact", "cancel": "cancelled a reminder", "move": "moved a reminder",
       "snooze": "snoozed a reminder", "undo": "undid the last change", "reminder": "set a reminder"}
DID_ASK = re.compile(r"\b(?:what (?:did|have|were) you (?:just )?(?:do|done|doing|run|change)|what actions|"
                     r"did you (?:\w+ )?(?:set|open|close|save|remember|change|cancel|mute|unmute|lock|add|turn|do|run|"
                     r"snooze|move|forget|undo|put)|have you (?:\w+ )?(?:set|opened|closed|saved|changed|cancelled|muted|"
                     r"done|run|added|locked|snoozed|moved|forgotten))\b", re.I)


def did_add(what, target=None, ok=True):
    line = DID.get(what, str(what).replace("_", " "))
    try:                                                       # an odd target never stops the action itself
        if what == "open":
            line = f"opened {target[0]}"                       # (name, path)
        elif what == "close":
            line = f"closed {target.replace('.exe', '')}"
        elif what == "reminder":                               # target: the reminders set, as the file stores them
            r = target[0]
            line = f"set {'a timer' if r[2] == 'timer' else 'an alarm' if r[3] == 'alarm' else 'a reminder'} for {clock(r[0])}"
    except (TypeError, IndexError, AttributeError, ValueError, OSError, OverflowError):
        pass
    did.append((time.time(), line, ok))
    del did[:-20]


def can_undo(what, before=None):
    """Keep the one change "undo that" reverses; before=None marks a change that cannot be put back."""
    undo[:] = [time.time() + UNDO_FOR, what, before]
    if what in ("fact", "forget", "cancel", "move", "reminder"):   # run_action records its own
        did_add(what, before)


def undo_last():
    """Put the last change back if it is under 2 minutes old, and say what is true now."""
    if not undo or time.time() > undo[0]:
        undo.clear()
        return "There's nothing to undo."
    _, what, before = undo
    undo.clear()
    if before is None:
        return "I can't undo that."
    if what in ("volume", "mute", "unmute"):
        ok = run_action("volume", ("set", before[1])) if what == "volume" else run_action("mute" if before[0] else "unmute", None)
        undo.clear()                                           # an undo is not itself undone
        if not ok:
            return "That didn't work."
        return f"Volume back at {speakers()[1]} percent." if what == "volume" else "Muted." if before[0] else "Unmuted."
    try:
        if what == "forget":                                   # put back what was forgotten, if not already back
            facts = load_memory()
            back = [f for f in before if f not in facts]
            if not back:
                return "It's already back."
            save_memory(facts + back)
            did_add("undo")
            log(f"fact put back by undo ({len(back)})")
            return "Put back: " + "; ".join(back) + "."
        if what == "fact":
            facts = load_memory()
            if before not in facts:
                return "It's already gone."
            save_memory([f for f in facts if f != before])
            did_add("undo")
            log("fact removed by undo")
            return f"Forgotten: {before}."
        items, now = load_reminders(), time.time()
        if what == "cancel":                                   # put back what was cancelled, if it has not rung yet
            back = [r for r in before if r[0] > now and r not in items]
            if not back:
                return "It's too late to put that back." if any(r[0] <= now for r in before) else "It's already back."
            save_reminders(items + back)
            did_add("undo")
            log(f"reminder put back by undo ({len(back)})")
            return "Put back: " + "; ".join(describe(r, now) for r in back) + "."
        if what == "move":                                     # back to its old time, if that has not passed
            old, new = before
            if new not in items:
                return "It's already gone."
            if old[0] <= now:
                return "It's too late to put that back."
            save_reminders([r for r in items if r != new] + [old])
            did_add("undo")
            log("reminder moved back by undo")
            return "Put back: " + describe(old, now) + "."
        gone = [r for r in items if (round(r[0]), round(r[1]), r[2], r[3]) in before]
        if not gone:
            return "It's already gone."
        save_reminders([r for r in items if r not in gone])
        did_add("undo")
        log(f"reminder removed by undo ({len(gone)})")
        noun = "alarm" if gone[0][2:] == ("reminder", "alarm") else "timer" if gone[0][2] == "timer" else "reminder"
        return f"Removed that {noun}." if len(gone) == 1 else f"Removed those {len(gone)} {noun}s."
    except (OSError, ValueError):
        return "I can't read that file, so I left it alone."


# ------------------------------------------------------------------ to-do by voice and remembered facts
def act_todo(item):
    """Add one open task to the to-do note. Appended, never rewritten (safe while Obsidian or a sync tool has the note
    open), and the note is never created. Errors carry no path: they are logged and shown."""
    item, note = " ".join(str(item).split())[:200], todo_note()
    if not item or not note:
        raise RuntimeError("no to-do note is set")
    try:
        with open(note, "rb+") as f:                           # rb+ fails on a missing file instead of making one
            if f.seek(0, 2):
                f.seek(-1, 2)
                last = f.read(1)
                f.seek(0, 2)
                if last != b"\n":
                    f.write(b"\n")
            f.write(f"- [ ] {item}\n".encode("utf-8"))
    except OSError as e:
        raise RuntimeError(f"the to-do note could not be written ({type(e).__name__})") from None


# "remember that my dentist is on Fridays": one fact a line in Data\jarvis_memory.txt, added to every prompt.
# Plain text on this PC and sent only to the local model, but he reads it out when asked: no passwords in it.
MEMORY_FILE = os.path.join(DATA, "jarvis_memory.txt")
MEMORY_BAD = "I can't read my memory file, so I left it alone."


def load_memory():
    """The remembered facts. A file that cannot be read raises OSError / ValueError, like load_reminders()."""
    if not os.path.exists(MEMORY_FILE):
        return []
    with open(MEMORY_FILE, "r", encoding="utf-8") as f:
        return [line.strip() for line in f.read().splitlines() if line.strip()]


def save_memory(facts):
    tmp = MEMORY_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write("".join(fact + "\n" for fact in facts))
    os.replace(tmp, MEMORY_FILE)


def facts_about(x):
    """The saved facts about x: all of them for "me", else the ones related() to it. Unreadable raises."""
    facts = load_memory()
    if re.fullmatch(r"(?:me|myself)\W*", x.strip().lower()):
        return facts
    return [f for f in facts if related(x, [f])]


def fact_save(fact):
    """route() for a save: an older fact about the same thing asks "Replace?" first; anything else saves."""
    fact = " ".join(fact.split())[:200]
    try:
        facts = load_memory()
    except (OSError, ValueError):
        return ("memory", "save", fact, None)                  # memory_reply says it can't read the file
    new = keywords(fact)
    same = [f for f in facts if f != fact and new and len(new & keywords(f)) * 2 >= len(new)]   # half its words or more
    if fact in facts or not same:
        return ("memory", "save", fact, None)
    old = max(same, key=lambda f: len(new & keywords(f)))
    return ("act", "replace_fact", (old, fact), f"You told me '{old}'. Replace it with this? Confirm with yes.")


# M4a-3: a lasting fact about you said in a chat turn; he offers to remember it, and only a yes saves it.
# shortcut: fixed patterns, not the model, so unusual wording is missed; let the model propose if they miss too much
LEARN = re.compile(r"\b(?:my (?:(?:sister|brother|mum|mom|mother|dad|father|wife|husband|partner|girlfriend|boyfriend|son|"
                   r"daughter|best friend|friend|dog|cat|teacher|boss)(?:'s)? (?:name |birthday )?is|(?:name|birthday|school|"
                   r"job|favou?rite \w+) is)|i'?m allergic to|i am allergic to|i work (?:at|as|for|in)|i live in|"
                   r"i(?:'m| am) (?:a )?(?:vegetarian|vegan)|i study|i have an? \w+ (?:called|named)) \w", re.I)
NO_LEARN = re.compile(r"password|passcode|\bpin\b|code|card|account|bank|social security|\d{3,}", re.I)


def learnable(text):
    """The sentence of a chat turn worth offering to remember, or "": never a question, a number or a secret,
    never one already saved, never with JarvisLearn=off."""
    if setting("JarvisLearn", "ask").strip().lower() in ("off", "0"):
        return ""
    for part in re.split(r"(?<=[.!?])\s+", strip_name(text)):
        part = re.sub(r"^(?:(?:and|so|oh|well|also|by the way),? )+", "", part.strip(), flags=re.I).rstrip(".!")
        if LEARN.search(part) and not part.endswith("?") and not SECRET.search(part) and not NO_LEARN.search(part):
            try:
                if part.lower() in (f.lower() for f in load_memory()):
                    return ""
            except (OSError, ValueError):
                return ""
            return part[:200]
    return ""


def holds_words(fact, said):
    """Every word said is a whole word of the fact ("car" is not in "Oscar")."""
    return set(re.findall(r"[\w']+", said.lower())) <= set(re.findall(r"[\w']+", fact.lower()))


def memory_reply(op, text):
    """Carry out a save / list / forget and return what to say. Only counts reach the log, never the facts."""
    try:
        facts = load_memory()
    except (OSError, ValueError):
        return MEMORY_BAD
    if op == "list":
        if not facts:
            return "You haven't asked me to remember anything."
        return f"I remember {len(facts)} thing{'s' if len(facts) != 1 else ''}: {'; '.join(facts)}."
    if op == "forget":                                         # every fact that holds all the words said
        gone = [f for f in facts if holds_words(f, text)]
        if not gone:
            return "I don't have that."
        save_memory([f for f in facts if f not in gone])
        log(f"fact forgotten ({len(gone)})")
        can_undo("forget", gone)
        return "Forgotten: " + "; ".join(gone) + "."
    fact = " ".join(text.split())[:200]
    if fact not in facts:
        if len(facts) >= 50:
            return "You've told me 50 things. Forget one first."
        save_memory(facts + [fact])
        log(f"fact saved ({len(facts) + 1} stored)")
        can_undo("fact", fact)
    return f"Noted: {fact}."


# ------------------------------------------------------------------ timers and reminders
# "remind me to cook in 20 minutes", "set a timer for 10 minutes", "what reminders do I have", "cancel the timer".
# All of it is read by the code below, never by the model. They are kept in Data\jarvis_reminders.txt (so they
# survive a restart) and ring only while JARVIS runs: a ding and the line, repeated until a stop word or a click.
# A repeating reminder keeps its rule in the kind field (daily | weekdays | mon ... sun), so the file format is the same.
REMIND_FILE = os.path.join(DATA, "jarvis_reminders.txt")      # due|created|kind|label  (kind: reminder | timer | a rule)
STOP_WORDS = re.compile(r"\b(stop|shush|shh+|shut ?up|quiet|enough|okay|ok|thanks|thank you|dismiss)\b", re.I)
RINGS = 10                                                    # each is a ding, the line, and up to 6 s of listening
SNOOZE = 300                                                  # seconds, when "snooze" is said with no length
ALARM_CAP = 300                                               # an alarm rings this long unanswered, then it is missed
ALARM_SAY = 30                                                # an alarm says its line again after this many seconds
NAME_ONLY = re.compile(r"\W*(?:(?:hey|hi|ok|okay)\W+)?jarvis\W*", re.I)   # said in a gap, it stops an alarm
DAYS = "mon tue wed thu fri sat sun".split()
ONES = ("zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen "
        "seventeen eighteen nineteen").split()
TENS = {"twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90}
_remind_bad = [False]                                         # the file could not be read: said once, not every second


def _num(s):
    """'12', '1.5', 'twelve', 'twenty five', 'a' -> the number, anything else -> None."""
    s = s.strip().replace("-", " ")
    if s in ("a", "an"):
        return 1
    if re.fullmatch(r"\d+(\.\d+)?", s):
        return float(s)
    if not s or [w for w in s.split() if w not in ONES and w not in TENS]:
        return None
    return sum(ONES.index(w) if w in ONES else TENS[w] for w in s.split())


def duration(s):
    """'10 minutes', 'an hour and a half', 'two minutes and 30 seconds' -> seconds, or None if it is not a duration."""
    s = re.sub(r"\b(?:an?|one) (hour|minute) and a half\b", lambda m: "90 " + ("minutes" if m.group(1) == "hour" else "seconds"),
               s.strip()).replace("half an hour", "30 minutes")
    s = re.sub(r"((?:sec|min|hour|hr)[a-z]*),? (?!and )", r"\1 and ", s)      # "1 hour 30 minutes" has no "and"
    total = 0
    for piece in s.split(" and "):
        m = re.fullmatch(r"(.+?)[ -]?(sec|min|hour|hr)[a-z]*", piece.strip())
        n = _num(m.group(1)) if m else None
        if n is None:
            return None
        total += n * {"sec": 1, "min": 60}.get(m.group(2), 3600)
    return total


def when(s, now):
    """'in 20 minutes', 'at 6:30 pm', 'at 18:30', 'at 7', 'at seven thirty in the morning', 'at 1900 hours',
    'at noon', 'at 9 tomorrow' -> the time it is due, or None. A clock time is its next occurrence; with no am / pm,
    'at 7' is whichever 7 o'clock comes first. 'hours', 'hundred' and a leading 0 mean the 24-hour clock."""
    s = s.strip().lower().rstrip(".")
    if s.startswith("in "):
        d = duration(s[3:])
        return None if d is None else now + d
    lead = re.fullmatch(rf"(?:on |next |this )*(tomorrow|today|{'|'.join(WEEKDAYS)}),?(?: at)? (.+)", s)
    if lead:                                                   # "tomorrow at 9", "on Friday at 9" -> "at 9 friday"
        s = f"at {lead.group(2)} {lead.group(1)}"
    if not s.startswith("at "):
        return None
    s = f" {s[3:]} "
    days = 1 if " tomorrow " in s else 0
    s = re.sub(r",? (?:tomorrow|today)(?: at)? ", " ", s)
    wd = re.search(rf",? (?:on )?(?:next |this |coming )?({'|'.join(WEEKDAYS)})(?: at)? ", s)
    if wd:                                                     # "Monday at 7": that day, at most 7 days ahead
        days = (WEEKDAYS.index(wd.group(1)) - datetime.fromtimestamp(now).weekday()) % 7
        s = s[:wd.start()] + " " + s[wd.end():]
    # "half past six", "quarter to 8", "ten past 7" -> 6:30, 7:45, 7:10
    q = re.match(r" (half|quarter|[a-z0-9 ]+?)(?: minutes?)? (past|after|to|till) ([a-z0-9]+) ", s)
    if q:
        mins, hr = {"half": 30, "quarter": 15}.get(q.group(1), _num(q.group(1))), _num(q.group(3))
        if mins is not None and hr is not None and 0 < mins <= 30 and mins == int(mins) and hr == int(hr) and 0 <= hr <= 23:
            back = q.group(2) in ("to", "till")
            hr = (int(hr) - 1 - back) % 12 + 1 if 1 <= hr <= 12 else (int(hr) - back) % 24     # "quarter to 1" is 12:45
            s = f" {hr}:{(60 - int(mins)) % 60 if back else int(mins):02d} " + s[q.end():]
    s = re.sub(r" o'?clock ", " ", s)
    s = re.sub(r" (?:in the |this )?morning ", " am ", s)
    s = re.sub(r" (?:(?:in the |this )?(?:afternoon|evening)|(?:at )?night|tonight) ", " pm ", s)
    s = re.sub(r" (?:12 )?noon ", " 12 pm ", s)
    s = re.sub(r" (?:12 )?midnight ", " 12 am ", s)
    m = re.fullmatch(r"(.+?) ?(?:([ap])\.? ?m\.?)?", s.strip())
    if not m:
        return None
    s, half = m.group(1), m.group(2)
    d = re.fullmatch(r"(\d{1,2})(?:[: .]?(\d{2}))?( hundred)?( hours)?", s)
    if d:
        if d.group(4) and not (d.group(2) or d.group(3)):
            return None                                        # "at 2 hours" is a wait, not a time
        hour, minute = int(d.group(1)), int(d.group(2) or 0)
        strict = bool(d.group(3) or d.group(4) or (len(d.group(1)) == 2 and d.group(1)[0] == "0"))
    else:
        ws = s.split()
        strict = bool({"hours", "hundred"} & set(ws))
        ws = [w for w in ws if w not in ("hours", "hundred")]
        if not ws or {"a", "an"} & set(ws):
            return None
        if strict and "hundred" in s:
            hour, minute = _num(" ".join(ws)), 0               # "nineteen hundred"
        else:
            hour = _num(ws[0])
            minute = _num(" ".join(ws[1:])[3:] if ws[1:2] == ["oh"] else " ".join(ws[1:])) if ws[1:] else 0
        if hour is None or minute is None or hour != int(hour) or minute != int(minute):
            return None
        hour, minute = int(hour), int(minute)
    if minute > 59 or hour > 23 or (half and not 1 <= hour <= 12) or (half and strict):
        return None
    hours = [hour % 12 + (12 if half == "p" else 0)] if half else [hour] if strict or not 1 <= hour <= 12 else [hour, (hour + 12) % 24]
    day = datetime.fromtimestamp(now).replace(minute=minute, second=0, microsecond=0)
    if days or wd:                                             # "tomorrow", "Friday": that day's first match, no rolling on
        day += timedelta(days=days)
        ts = [day.replace(hour=h).timestamp() for h in hours]
        # today's own weekday with its time gone: the same day next week
        return min([t for t in ts if t > now] or [(day + timedelta(days=7)).replace(hour=h).timestamp() for h in hours])
    return min(t if t > now else t + 86400 for t in (day.replace(hour=h).timestamp() for h in hours))


def span(sec, s="s"):
    """600 -> '10 minutes'; with s='' it is '10 minute' (as in "your 10 minute timer")."""
    sec = int(round(sec))
    parts = ((sec // 3600, "hour"), (sec % 3600 // 60, "minute"), (sec % 60, "second"))
    return " ".join(f"{n} {unit}{s if n != 1 else ''}" for n, unit in parts if n) or "0 seconds"


def clock(ts, now=None):
    d = datetime.fromtimestamp(ts)
    days = (d.date() - datetime.fromtimestamp(now or time.time()).date()).days
    return (f"{d.hour % 12 or 12}:{d.minute:02d} {'AM' if d.hour < 12 else 'PM'}"
            + ("" if days == 0 else " tomorrow" if days == 1 else d.strftime(" on %A")))


def snooze_for(heard):
    """What was said while it rang -> None (not a snooze), the seconds to wait, or 0 for a length he cannot use
    (under a minute, over 2 hours, or not understood: it keeps ringing)."""
    s = re.sub(r"[^a-z0-9. ]+|\.(?!\d)", " ", heard.lower())
    if not re.search(r"\b(snooze|later|not now)\b|\bmore (sec|min|hour)", s):
        return None
    rest = " ".join(w for w in s.split() if w not in ("snooze", "later", "not", "now", "more", "for", "it", "ok", "okay",
                                                      "another", "please", "jarvis"))
    if not rest:
        return SNOOZE
    d = duration(rest)
    return d if d and 60 <= d <= 7200 else 0


def next_due(due, kind, now):
    """The next time a repeating reminder rings after `now`: the same clock time, on a day its rule allows. Stepped on
    the wall clock, so "9" stays 9 across a daylight-saving change."""
    d = datetime.fromtimestamp(due)
    while d.timestamp() <= now or not (kind == "daily" or (d.weekday() < 5 if kind == "weekdays" else DAYS[d.weekday()] == kind)):
        d += timedelta(days=1)
    return d.timestamp()


def repeats(kind, due):
    """'every day ' / 'every weekday ' / 'every Monday ' for a repeating kind, '' for a single reminder or a timer."""
    return {"reminder": "", "timer": "", "daily": "every day ", "weekdays": "every weekday "}.get(
        kind, datetime.fromtimestamp(due).strftime("every %A "))


def split_time(rest, now):
    """'to cook in 20 minutes' or 'in 20 minutes to cook' -> (due, label, the time as said). No time in it: due is None."""
    for m in re.finditer(r"\b(?:in|at) ", rest):               # the time comes last
        label, said = rest[:m.start()], rest[m.start():]
        day = re.search(rf"(?:^|\s)(?:on |next |this )*(tomorrow|today|{'|'.join(WEEKDAYS)}),?\s*$", label) if said[:3] == "at " else None
        if day:                                                # "to call mom tomorrow at 9": the day is part of the time
            label, said = label[:day.start()], f"{said} {day.group(1)}"
        due = when(said, now)
        if due is not None:
            return due, label.strip(), said
    for m in re.finditer(r" (?=(?:to|about|that|for) )", rest):   # the time comes first
        due = when(rest[:m.start()], now)
        if due is not None:
            return due, rest[m.end():].strip(), rest[:m.start()]
    return None, rest.strip(), ""


def reminder_cmd(t, cmd, now):
    """A timer or reminder command -> ("list", kind) | ("cancel", kind, words) | ("set", kind, due, label, time as said);
    anything else -> None. due is None when no time was heard (he then asks)."""
    # alarms are saved as reminders labelled "alarm": kind "alarm" would read as a weekly rule (repeats, next_due)
    if re.match(r"(?:do i have|have i (?:got|set)|(?:what|which)(?: are)?|what time(?:'s| is)|(?:list|show)(?: me)?|when(?:'s| is)|"
                r"how long (?:until|till|before)|is) (?:an? |any |all |my |the |next )*alarms?\b", t):
        return ("list", "alarm")
    # "move my alarm to 8", "change the 7 am alarm to 8", "make the timer 10 minutes", "add 5 minutes to the timer":
    # (words that say which one, the new time; or for "add", None and the seconds added). No time read: not this
    m = re.match(r"(?:change|move|push|reschedule|switch|shift|update) (?:(?:the|my|that) )+(?:(.+?) )?(alarm|reminder) "
                 r"(?:to|for|until|till) (.+)$", cmd)
    if m:
        due = next((d for d in (when(s, now) for s in (m.group(3), "at " + m.group(3))) if d is not None), None)
        return None if due is None else ("move", m.group(2), m.group(1) or "", due, 0)
    m = (re.match(r"(?:make|change|reset|update) (?:(?:the|my|that) )+(?:(.+?) )?timer (?:to |for |into )?(.+)$", cmd)
         or re.match(r"(add) (.+?) (?:to|onto|on to) (?:(?:the|my|that) )+(?:(.+?) )?timer$", cmd))
    if m:
        add = m.group(1) == "add"
        secs = duration(m.group(2))
        return None if secs is None else ("move", "timer", (m.group(3) if add else m.group(1)) or "",
                                          None if add else now + secs, secs if add else 0)
    # "cancel the alarm", "remove my 7 am alarm", "cancel the alarm for 7": the words left say which one (a clock time)
    m = re.match(r"(?:cancel|delete|remove|clear|stop|turn off|forget) (?:(?:all|every|both|the|my|that|of) )*(?:(.+?) )?alarms?"
                 r"(?: (?:for|at) (.+?))?(?: (?:that )?i (?:set|made))?$", cmd)
    # "cancel all alarms", "cancel both", "turn off my alarms": the whole schedule. A plural with other words is by those
    every = "all " if re.search(r"\b(?:all|every|both)\b", cmd) else ""
    plural = "all" if re.search(r"\b(?:alarm|reminder|timer)s\b", cmd) else ""
    if m:
        return ("cancel", "alarm", f"{every}{m.group(1) or ''} {m.group(2) or ''}".strip() or plural)
    m = re.match(r"((?:set|create|make|add)(?: me| up)? (?:an? |my |the |another |some )?alarms?|i (?:need|want) (?:an? )?alarm|"
                 r"alarm|wake me(?: up)?)(?: for| at)?(?: (.+))?$", cmd)
    if m:
        rest = re.sub(r" from now$", "", m.group(2) or "")
        for said in (rest, "at " + rest, "in " + rest):       # "in one minute", "7 am", "one minute"; "at" before "in"
            due = when(said, now) if rest else None
            if due is not None:
                return ("set", "alarm", due, "alarm", said)
        parts = re.split(r",? and |, ", rest)                  # "7 and 8 am": the am / pm said last is for each
        half = re.search(r" ?(?:[ap]\.? ?m\.?|in the (?:morning|afternoon|evening)|tonight|at night)$", parts[-1])
        if len(parts) > 1:
            dues = [when("at " + (p if half is None or re.search(half.re, p) else p + half.group()), now) for p in parts]
            if None not in dues:
                return ("set", "alarm", dues, "alarm", "at " + rest)
        if not m.group(1).startswith(("alarm", "wake")) and not rest:
            return ("set", "alarm", None, "alarm", "")        # he asks when
    m = re.match(r"(?:(?:what|which) (?:are )?(?:my |the )?|(?:list|show|read)(?: me| out)? (?:all )?(?:my |the )?|"
                 r"do i have (?:any )?|how (?:much time|long) (?:is |do i have )?left on (?:my |the )?)(reminder|timer)s?"
                 r"(?: (?:do i have|have i (?:got|set)|are (?:set|there|left|pending|running)).*)?$", t)
    if m:
        return ("list", m.group(1))
    m = re.match(r"(?:cancel|delete|remove|clear|stop|forget) (?:(?:all|every|both|of|the|my|that) )*(?:(.+) )?(reminder|timer)s?"
                 r"(?: (?:to|about|for) (.+))?$", cmd)
    if m:
        return ("cancel", m.group(2), f"{every}{m.group(1) or ''} {m.group(3) or ''}".strip() or plural)
    m = re.match(r"(?:remind me|(?:set|add) (?:a |another )?reminder)(?: (.+))?$", cmd)
    if m:
        if re.match(r"(what|who|how|why|where|when|which|whether|if) ", m.group(1) or ""):
            return None                                        # "remind me what the capital is": a question for the model
        rest, kind = m.group(1) or "", "reminder"
        rep = re.search(r"\bevery ?(day|week ?day|(?:mon|tues|wednes|thurs|fri|satur|sun)day)s?\b ?", rest)
        if rep:                                                # "every day at 9", "every weekday", "every Monday"
            kind = "daily" if rep.group(1) == "day" else "weekdays" if rep.group(1).startswith("week") else rep.group(1)[:3]
            rest = (rest[:rep.start()] + rest[rep.end():]).strip()
        due, label, said = split_time(rest, now)
        if rep and due is not None:
            due = next_due(due, kind, now)
        if label and not re.match(r"(to|about|that) ", label):
            label = "about " + re.sub(r"^(for|of) ", "", label)
        return ("set", kind, due, re.sub(r"\bmy\b", "your", label), said)
    m = re.match(r"(set |start |create |put on |give me )?(?:a |an |another |the )?(?:(.+?)[ -])?timer(?: (?:for|of) (.+))?$", cmd)
    if not m:
        return None
    verb, before, after = m.groups()
    if before and " and " in before:                           # "set an alarm for 7 and set a timer": two commands
        return None
    secs, label = (duration(before) if before else None), ""
    if before and secs is None:
        if not verb:                                           # "open timer", "what is a timer": not a command for this
            return None
        label = before                                         # "set a pasta timer for 10 minutes"
    for piece in (after or "").split(" for "):           # "the pasta for 10 minutes" or "10 minutes for the pasta"
        d = duration(piece) if secs is None else None
        if d is None:
            label = f"{label} {piece}".strip()
        else:
            secs = d
    return ("set", "timer", None if secs is None else now + secs, re.sub(r"\bmy\b", "your", label), "in")


def load_reminders():
    """[(due, created, kind, label)], soonest first. A file that cannot be read raises OSError / ValueError: an error
    is not "no reminders", and the caller must then leave the file alone."""
    if not os.path.exists(REMIND_FILE):
        return []
    out = []
    with open(REMIND_FILE, "r", encoding="utf-8") as f:
        for line in f.read().splitlines():
            if line.strip():
                due, created, kind, label = line.split("|", 3)
                out.append((float(due), float(created), kind, label))
    return sorted(out)


def save_reminders(items):
    tmp = REMIND_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write("".join(f"{due:.0f}|{created:.0f}|{kind}|{label}\n" for due, created, kind, label in items))
    os.replace(tmp, REMIND_FILE)


def describe(r, now):
    due, created, kind, label = r
    if kind == "timer":
        return f"{span(due - now)} left on the timer" + (f" for {label}" if label else "")
    if repeats(kind, due):
        return f"{label or 'a reminder'}, {repeats(kind, due)}at {clock(due, due)}"
    return f"{label or 'a reminder'} at {clock(due, now)}"


def ring_line(r, now):
    """What he says when it is due: your own words back ("Time to cook."), not something the model wrote."""
    due, created, kind, label = r
    if kind == "timer":
        line = f"Your timer for {label} is done." if label else f"Your {span(due - created, '')} timer is done."
    elif label == "alarm":
        line = "This is your alarm."
    elif label.startswith("to "):
        line = f"Time {label}."
    else:
        line = f"Reminder: {label[5:]}." if label.startswith("that ") else f"Reminder {label}." if label else "This is your reminder."
    if now - due > 120:                                        # the PC slept, or JARVIS was not running
        return f"Missed {'timer' if kind == 'timer' else 'alarm' if label == 'alarm' else 'reminder'} from {clock(due, now)}: {line[0].lower()}{line[1:]}"
    return line


def find_items(pool, said, kind, now):
    """The items of `pool` that `said` points at, and the words that pointed: by clock time, else by words, else (no
    words) the asked kind first. Timers go by words only."""
    # shortcut: a word matches on its first four letters ("cooking" finds "to cook"); fine for a list of 20
    words = [w for w in said.split() if w not in ("the", "my", "a", "an", "one", "to", "about", "for", "at", "all")]
    found = [r for r in pool if all(w[:4] in f"{r[3]} {span(r[0] - r[1], '')}" for w in words)]
    if kind != "timer" and not said.startswith("all"):
        own = [r for r in pool if (r[2:] == ("reminder", "alarm")) == (kind == "alarm")]
        at = when("at " + " ".join(words), now) if words else None
        if at:                                                 # by clock time; "7" with no am / pm is either 7
            hhmm = lambda ts: datetime.fromtimestamp(ts).strftime("%H:%M")
            half = re.search(r"\b(?:[ap]\.? ?m\b|morning|afternoon|evening|tonight|night|noon|midnight|hours|hundred)", said)
            times = {hhmm(at)} | (set() if half else {hhmm(at + 43200)})
            found = [r for r in pool if hhmm(r[0]) in times]
        elif not words:                                        # "cancel the reminder": its own kind first, else the other
            found = own or pool
        elif not found and len(own) == 1:                      # "cancel the morning alarm" with one alarm: that one
            found = own
    return found, words


rang = []                                                     # [when the ringing stopped, what rang]: for a later "snooze"


def snoozed(due, again):
    """What rang, back in the schedule once at `again` (a repeating one keeps its own series)."""
    return [(again, r[1] + again - r[0], "timer" if r[2] == "timer" else "reminder", r[3]) for r in due]


def remind_reply(op, args, quiet):
    """Carry out a list / cancel / set and return what to say. Runs inside a turn, so there is one writer at a time."""
    now, kind = time.time(), args[0]
    try:
        items = load_reminders()
    except (OSError, ValueError):
        return "I can't read the reminders file, so I left it alone."
    # alarms and reminders are one schedule (an alarm is a reminder labelled "alarm"); timers are kept apart
    is_alarm = lambda r: r[2] == "reminder" and r[3] == "alarm"
    pool = [r for r in items if (r[2] == "timer") == (kind == "timer")]
    if op == "list":
        if not pool:
            return "You have no timers." if kind == "timer" else "You have no alarms or reminders."
        n = sum(map(is_alarm, pool))
        counts = (" and ".join(f"{k} {w}{'s' if k != 1 else ''}" for k, w in ((n, "alarm"), (len(pool) - n, "reminder")) if k)
                  if kind != "timer" else f"{len(pool)} timer{'s' if len(pool) != 1 else ''}")
        last.update(kind=kind, items=pool, when=now)          # M1b: "cancel the second one" means this order
        return f"You have {counts}: {'; '.join(describe(r, now) for r in pool)}."
    if op == "snooze":                                         # "snooze" said after the ringing stopped
        if not rang or now - rang[0] > 300:
            return "Nothing is ringing right now."
        if not args[1]:
            return "I can snooze it for 1 minute to 2 hours."
        save_reminders(sorted(items + snoozed(rang[1], now + args[1])))
        did_add("snooze")
        rang.clear()
        log(f"reminder snoozed ({args[1]:.0f}s, after it rang)")
        return f"Snoozed for {span(args[1])}."
    if op == "cancel" and len(args) > 2:                     # M1b: the item was picked from the last list, by code
        key = lambda r: (round(r[0]), round(r[1]), r[2], r[3])
        gone, words = [r for r in pool if key(r) == key(args[2])], []
    elif op in ("cancel", "move"):
        gone, words = find_items(pool, args[1], kind, now)
    if op in ("cancel", "move"):
        if len(gone) > 1 and (op == "move" or not words and not args[1].startswith("all")):   # "turn off my alarm" with 2
            name = lambda r: clock(r[0], now) if is_alarm(r) else describe(r, now)
            reply_line(f"You have {len(gone)} {kind}s: {' and '.join(map(name, gone))}. Which one?", quiet)
            S.set(state="listening", level=0.0)
            answer = hear()
            if answer:
                convo_add("U", answer)
            answer = answer.strip().lower().rstrip(".!?")
            if not (op == "cancel" and re.search(r"\b(?:both|all|every|them)\b", answer)):
                pick, said = find_items(gone, answer, kind, now) if answer else ([], [])
                if not said or not pick or (op == "move" and len(pick) > 1):
                    return "Okay, I left them."
                gone = pick
        if not gone:
            others = "; ".join(describe(r, now) for r in items)
            return f"I don't see {'an' if kind == 'alarm' else 'a'} {kind} like that." + (f" You have: {others}." if others else "")
        if op == "move":
            old, (due, plus) = gone[0], args[2:]
            due = old[0] + plus if plus else next_due(due, old[2], now) if repeats(old[2], now) else due
            if not 5 <= due - now <= 7 * 86400:
                return "I can set that from 5 seconds to 7 days ahead."
            new = (round(due), round(old[1] if plus else now), old[2], old[3])   # as the file stores it
            save_reminders([r for r in items if r != old] + [new])
            log(f"reminder moved ({due - old[0]:.0f}s)")
            can_undo("move", (old, new))
            if kind == "timer":
                return f"The timer now has {span(due - now)} left."
            return f"Moved your {clock(old[0], now)} {'alarm' if is_alarm(old) else 'reminder'} to {clock(due, now)}."
        save_reminders([r for r in items if r not in gone])
        log(f"reminder cancelled ({len(gone)})")
        can_undo("cancel", gone)
        return "Cancelled: " + "; ".join(describe(r, now) for r in gone) + "."
    if op == "flip":                                           # "no, AM": what was just set moves to the other half of the day
        old = [r for r in items if undo and undo[1] == "reminder" and now < undo[0] and r[2] != "timer"
               and (round(r[0]), round(r[1]), r[2], r[3]) in undo[2]]
        if not old:
            return "There's no alarm to change."
        # shortcut: 12 hours in seconds, an hour off across a daylight-saving change; use the wall clock if that matters
        new = [(min(t for t in (r[0] - 43200, r[0] + 43200) if t > now)          # the sooner of the two, never past
                if (datetime.fromtimestamp(r[0]).hour < 12) != (args[1] == "am") else r[0],) + r[1:] for r in old]
        save_reminders([r for r in items if r not in old] + new)
        log(f"reminder moved 12 hours ({len(new)})")
        can_undo("reminder", [(round(r[0]), round(r[1]), r[2], r[3]) for r in new])
        return ("Changed to " if new != old else "It's already set for ") + " and ".join(clock(r[0], now) for r in new) + "."
    _, due, label, said = args
    alarm_set, kind = kind == "alarm", "reminder" if kind == "alarm" else kind
    if repeats(kind, now) and (due is None or said.startswith("in ")):
        return "A repeating reminder needs a clock time, like every day at 9."
    if due is None:                                            # no time heard: ask once and listen, like a confirmation
        reply_line("How long?" if kind == "timer" else "When?", quiet)
        S.set(state="listening", level=0.0)
        answer = hear()
        if answer:
            convo_add("U", answer)
        now, answer = time.time(), answer.strip().lower().rstrip(".!?")
        if re.fullmatch(r"no|nope|never ?mind|cancel(?: that| it)?|forget (?:it|that)|nothing|stop|don'?t", answer):
            return f"Okay, no {args[0]}."
        for said in (answer, "at " + answer, "in " + answer):     # "at" first: "1900 hours" is a time, not a wait
            due = when(said, now)
            if due is not None:
                break
        else:
            return "I didn't catch the time."
    dues = sorted(due) if isinstance(due, list) else [due]     # "alarms for 7 and 8": a list
    if not all(5 <= d - now <= 7 * 86400 for d in dues):
        return "I can set that from 5 seconds to 7 days ahead."
    if len(items) + len(dues) > 20:
        return "You already have 20 pending. Cancel one first."
    label = re.sub(r"[\s|]+", " ", label)
    if kind != "timer":                                        # the same alarm or reminder twice would ring twice
        same = [d for d in dues if any(r[2:] == (kind, label) and abs(r[0] - d) < 60 for r in items)]
        dues = [d for d in dues if d not in same]
        if not dues:
            return f"You already have {'an alarm' if alarm_set else 'that reminder'} for {clock(same[0], now)}."
    save_reminders(items + [(d, now, kind, label) for d in dues])
    log(f"reminder set ({'alarm' if alarm_set else kind}, {dues[0] - now:.0f}s ahead, {len(dues)})")
    can_undo("reminder", [(round(d), round(now), kind, label) for d in dues])   # as the file stores it
    last.update(kind="timer" if kind == "timer" else "alarm" if alarm_set else "reminder",
                items=[(d, now, kind, label) for d in dues], when=now)        # M1b: "cancel it"
    if len(dues) > 1:
        return f"Alarms set for {' and '.join(clock(d, now) for d in dues)}."
    due = dues[0]
    if alarm_set:
        return f"Alarm set for {clock(due, now)}" + (f", {span(due - now)} from now." if said.startswith("in ") else ".")
    if kind == "timer":
        return f"Timer set for {span(due - now)}" + (f", for {label}." if label else ".")
    return f"I'll remind you {label} ".replace("  ", " ") + (
        f"in {span(due - now)}." if said.startswith("in ") else f"{repeats(kind, due)}at {clock(due, due if repeats(kind, due) else now)}.")


def due_reminders(now):
    """True when something is due. An unreadable file is reported once, and nothing rings until it can be read."""
    try:
        items = load_reminders()
    except (OSError, ValueError) as e:
        if not _remind_bad[0]:
            _remind_bad[0] = True
            log(f"reminders: the file cannot be read ({type(e).__name__})")
            problem("Can't read Data\\jarvis_reminders.txt - reminders are paused until it is fixed or deleted", popup=False)
        return False
    _remind_bad[0] = False
    return bool(items) and items[0][0] <= now


def ding():
    """Two falling notes, made here so there is no sound file; played like the voice, so the hologram moves with it."""
    import numpy as np
    rate = 24000
    t = np.arange(int(rate * 0.45)) / rate
    return np.concatenate([0.4 * np.sin(2 * np.pi * hz * t) * np.exp(-6 * t) for hz in (1318.5, 1046.5)]).astype(np.float32), rate


def alarm():
    """Ring for everything that is due, as one alarm: ding, say it, listen for a stop word, repeat. It holds the turn
    lock, so it waits for a running turn, the wake word lets go of the microphone, and a click stops it."""
    with busy:
        cancel.clear()
        turn_id[0] = time.time()                               # counts as activity: the voice is not unloaded mid-ring
        try:
            now = time.time()
            items = load_reminders()
            due = [r for r in items if r[0] <= now]
            if not due:
                return
            # gone before it rings: a crash here cannot ring forever. A repeating one goes back in for its next time
            # (once, however many were missed while the PC was off)
            ahead = [(next_due(r[0], r[2], now), now, r[2], r[3]) for r in due if repeats(r[2], now)]
            save_reminders(sorted(items[len(due):] + ahead))
            log(f"reminder fired ({len(due)})")
            log(f"timing: due -> ring {now - due[-1][0]:.1f}s")
            text = " ".join(ring_line(r, now) for r in due)
            convo_add("J", text)
            audio = None if muted() or hud_tier() >= 3 else synth_audio(text)     # made once, replayed each round
            if audio is None:                                  # muted, STEALTH or no voice: shown like a muted reply
                if setting("JarvisMutedPopup", "1") == "1":
                    S.set(pop="open")
                rang[:] = [time.time(), due]
                return
            # an alarm in the batch: ding every ~2 s until answered (cap ALARM_CAP); timers and reminders: RINGS rounds
            alarm_at = next((r[0] for r in due if r[2] != "timer" and r[3] == "alarm"), None)
            start, said, rounds = time.time(), None, 0
            while time.time() - start < ALARM_CAP if alarm_at else rounds < RINGS:
                rounds += 1
                S.set(state="speaking", say=text)
                play_samples(*ding())
                if not cancel.is_set() and (not alarm_at or said is None or time.time() - said >= ALARM_SAY):
                    play_samples(*audio)
                    said = time.time()
                S.set(state="listening", level=0.0)
                # matched and dropped, never kept; an alarm's gap is short, and Whisper runs only if someone speaks
                heard = hear(patience=1.5) if alarm_at else hear()
                nap = snooze_for(heard)                        # before the stop words: "okay, snooze" snoozes
                if nap and not cancel.is_set():                # rings again once; a repeating one keeps its own series
                    again = time.time() + nap
                    save_reminders(sorted(load_reminders() + snoozed(due, again)))
                    did_add("snooze")
                    rang.clear()
                    log(f"reminder snoozed ({nap:.0f}s)")
                    reply_line(f"Snoozed until {clock(again)}." if alarm_at else f"Snoozed for {span(nap)}.", False)
                    return
                if cancel.is_set() or (nap is None and (STOP_WORDS.search(heard) or alarm_at and NAME_ONLY.fullmatch(heard))):
                    convo_add("J", "(stopped)")
                    rang[:] = [time.time(), due]               # "snooze" in the next 5 minutes still works
                    return
            rang[:] = [time.time(), due]
            if alarm_at:                                       # nobody answered it: a line in the pop-up
                log(f"alarm missed (rang {ALARM_CAP // 60} min)")
                convo_add("J", f"Missed alarm from {clock(alarm_at)}.")
                if setting("JarvisMutedPopup", "1") == "1":
                    S.set(pop="open")
        except Exception as e:
            log(f"alarm failed: {type(e).__name__}")
            problem("A reminder could not ring")
        finally:
            S.set(state="idle", level=0.0)


# ------------------------------------------------------------------ smart note search (ChromaDB)
# JarvisSmartSearch=1 (default when chromadb is installed): your vault is split into passages and indexed by meaning
# in a local ChromaDB database (Data\notes_index), so "what did I write about motor torque" finds notes that never use
# those exact words. The index updates itself in the background (only changed notes) every 10 minutes and before a
# search. If ChromaDB isn't installed or fails, the keyword search below is used instead - search always works.
_chroma = {"col": None, "root": None, "seen": {}, "last": 0.0, "failed": False}
_chroma_lock = threading.Lock()
_reindexing = threading.Lock()         # a full pass over the vault is running


def _chunks(text, size=900):
    paras, out, cur = re.split(r"\n\s*\n", text), [], ""
    for p in paras:
        p = p.strip()
        if not p:
            continue
        if len(cur) + len(p) > size and cur:
            out.append(cur)
            cur = ""
        cur = (cur + "\n\n" + p).strip()
        while len(cur) > size * 1.5:
            out.append(cur[:size])
            cur = cur[size:]
    if cur:
        out.append(cur)
    return out


def chroma_index(force=False):
    """Bring the index up to date with the vault (only new / changed / deleted notes). Returns the collection or None."""
    if setting("JarvisSmartSearch", "1") != "1" or _chroma["failed"]:
        return None
    root = vault_dir()
    if not root:
        return None
    try:
        with _chroma_lock:                                     # held only briefly, so a search never waits for a reindex
            if _chroma["col"] is None or _chroma["root"] != root:
                import chromadb
                client = chromadb.PersistentClient(path=os.path.join(DATA, "notes_index"))
                _chroma["col"] = client.get_or_create_collection("notes", metadata={"hnsw:space": "cosine"})
                _chroma["root"], _chroma["seen"] = root, {}
                for m in (_chroma["col"].get(include=["metadatas"]).get("metadatas") or []):
                    if m:
                        _chroma["seen"][m["path"]] = m.get("mtime", 0)
            if not force and time.time() - _chroma["last"] < 600:
                return _chroma["col"]
        if not _reindexing.acquire(blocking=False):            # one reindex at a time; meanwhile search what is there
            return _chroma["col"]
        try:
            col, seen, t0, changed = _chroma["col"], _chroma["seen"], time.time(), 0
            present = set()
            for dirpath, dirs, files in os.walk(root):
                dirs[:] = [d for d in dirs if not d.startswith(".")]
                for fn in files:
                    if not fn.lower().endswith(".md"):
                        continue
                    path = os.path.join(dirpath, fn)
                    present.add(path)
                    try:
                        mt = os.path.getmtime(path)
                    except OSError:
                        continue
                    if seen.get(path) == mt:
                        continue
                    try:
                        with open(path, "r", encoding="utf-8", errors="ignore") as f:
                            parts = _chunks(f.read(300_000))
                    except OSError:
                        continue                               # deleted or locked mid-sync: the next pass gets it
                    with _chroma_lock:                         # per note: a search waits for one note at most
                        col.delete(where={"path": path})
                        if parts:
                            name = os.path.splitext(fn)[0]
                            col.upsert(ids=[f"{path}#{i}" for i in range(len(parts))],
                                       documents=[f"{name}\n{p}" for p in parts],
                                       metadatas=[{"path": path, "name": name, "mtime": mt} for _ in parts])
                    seen[path] = mt
                    changed += 1
            for gone in [p for p in seen if p not in present]:
                with _chroma_lock:
                    col.delete(where={"path": gone})
                del seen[gone]
                changed += 1
            _chroma["last"] = time.time()
            if changed:
                log(f"notes index: {changed} note(s) updated in {time.time() - t0:.1f}s")
            return col
        finally:
            _reindexing.release()
    except ImportError:
        _chroma["failed"] = True
        log("smart search: chromadb not installed - using keyword search")
    except Exception as e:
        _chroma["failed"] = True
        log(f"smart search failed ({e!r}) - using keyword search until restart")
    return None


def smart_search(query, limit=3):
    col = chroma_index()
    if col is None:
        return None
    try:
        with _chroma_lock:
            res = col.query(query_texts=[query], n_results=limit)
        docs, metas, dists = res["documents"][0], res["metadatas"][0], res.get("distances", [[1] * limit])[0]
        return [(1 - d, m["name"], re.sub(r"\s+", " ", doc)[:600]) for doc, m, d in zip(docs, metas, dists) if d < 0.8]
    except Exception as e:
        log(f"smart search query failed: {e!r}")
        return None


def index_loop():
    load_meaning()                                             # here, so chromadb is imported by one thread only
    while True:
        try:
            chroma_index(force=True)
        except Exception as e:
            log(f"index loop: {e!r}")
        time.sleep(600)


# ------------------------------------------------------------------ one conversation turn
history = []          # the active window (M1): the last 2 exchanges, kept while the talk stays on them
last_turn = 0.0
ACTIVE_TTL = 120      # seconds after the last exchange that the window is still sent
TALK_STOP = STOP | set("how who why whom whose its they them their there then than also just really very not don't "
                       "does did has had will well now yes yeah okay please jarvis want need know think get got going "
                       "like one some more much many all our out into over too let".split())
FOLLOW_START = re.compile(r"(?:it|that|this|he|she|they|and|but|so|what about|how about|why|then|also)\b")


def keywords(text):
    """Content words of a line, for matching talk to talk (L1, later L2 / L4): lowercase, no time stamp,
    stop-words out, a trailing "s" cut."""
    words = re.findall(r"[a-z0-9']+", STAMP.sub("", text).lower().replace("’", "'"))
    words = [w.removesuffix("'s").strip("'") for w in words]
    return {w[:-1] if w.endswith("s") and len(w) > 3 else w for w in words if len(w) > 2 and w not in TALK_STOP}


def related(text, lines):
    """Talk matching for L1 / L2 / L4: a shared keyword, or close in meaning (MEANING_TALK)."""
    return bool(keywords(text) & set().union(set(), *map(keywords, lines))) or meaning(text, lines, MEANING_TALK)


# M2 topic memory: talk that leaves the window is filed by topic in Data\jarvis_topics.json, and comes back only
# when a question is about that topic. Plain text on this PC, sent only to the local model; only counts are logged.
TOPICS_FILE = os.path.join(DATA, "jarvis_topics.json")
SECRET = re.compile(r"\d{6,}|\b(?=\w*\d)(?=\w*[a-z])\w{8,}\b", re.I)   # long numbers and password-like words
RECALL_FLOOR = 1.5    # one rare shared word scores 1.0: not enough alone, so "time" or "day" never pulls a topic in


def recall_on():
    return setting("JarvisRecall", "on").strip().lower() not in ("off", "0")


def load_topics():
    """[{"kw": [...], "talk": [[when, you, him], ...], "used": time}]. Unreadable raises OSError / ValueError."""
    if not os.path.exists(TOPICS_FILE):
        return []
    with open(TOPICS_FILE, "r", encoding="utf-8") as f:
        topics = json.load(f)
    if not isinstance(topics, list) or not all(isinstance(t, dict) and {"kw", "talk", "used"} <= t.keys() for t in topics):
        raise ValueError("not a topic list")
    return topics


def save_topics(topics):
    tmp = TOPICS_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(topics, f)
    os.replace(tmp, TOPICS_FILE)


def topic_text(t):
    """What a topic is about, for the meaning match: your side of its talk."""
    return " ".join(you for _, you, _ in t["talk"])


def file_talk(msgs):
    """Files the chat exchanges in msgs into topics: it joins the topic sharing 2 keywords, or 1 found in no other
    topic, else starts a new one. fixed() stamps command replies, so those are left out."""
    pairs = [(u["content"], a["content"]) for u, a in zip(msgs[::2], msgs[1::2]) if not STAMP.match(u["content"])]
    if not pairs or not recall_on():
        return
    try:
        topics = load_topics()
    except (OSError, ValueError):
        log("topic memory unreadable: left alone")
        return
    for you, him in pairs:
        you, him = (SECRET.sub("[number]", s)[:200] for s in (you, him))
        kw = keywords(you + " " + him) - {"number"}
        if not kw:
            continue
        seen = Counter(w for t in topics for w in t["kw"])
        best = max(topics, key=lambda t: len(kw & set(t["kw"])), default=None)
        shared = kw & set(best["kw"]) if best else set()
        if not (len(shared) >= 2 or any(seen[w] == 1 for w in shared)):
            best = {"talk": []}
            topics.append(best)
        best["talk"] = (best["talk"] + [[round(time.time()), you, him]])[-6:]
        best["kw"] = sorted(set().union(*(keywords(y + " " + h) for _, y, h in best["talk"])) - {"number"})
        best["used"] = time.time()
    topics.sort(key=lambda t: t["used"])
    try:
        save_topics(topics[-200:])     # M3 brings it back to 100 each day; past 200 the oldest goes without a gist
        log(f"topic memory: {len(pairs)} exchange(s) filed, {len(topics[-200:])} topics")
    except OSError as e:
        log(f"topic memory not saved ({type(e).__name__})")


def recall(text):
    """The best 2 filed topics for this question, about 600 characters, or "". Score: shared keywords weighted by
    rarity, + RECALL_FLOOR when close in meaning (words OR meaning), at least RECALL_FLOOR; recent use breaks ties."""
    if not recall_on():
        return ""
    try:
        topics = load_topics()
    except (OSError, ValueError):
        return ""
    kw, now = keywords(text), time.time()
    seen = Counter(w for t in topics for w in t["kw"])
    scored = []
    for t in topics:
        s = sum(1 / seen[w] for w in kw & set(t["kw"]))
        if s < RECALL_FLOOR and meaning(text, [topic_text(t)], MEANING_TALK):
            s += RECALL_FLOOR
        if s >= RECALL_FLOOR:
            scored.append((s + 0.2 * max(0.0, 1 - (now - t["used"]) / (7 * 86400)), t))
    best = [t for _, t in sorted(scored, key=lambda p: -p[0])[:2]]
    gist = gist_for(text)                                      # M3: the checked facts of older talks
    if not best:
        return EARLIER + gist if gist else ""
    # newest exchange of each topic first, taking turns, until about 600 characters
    lines = sorted(((i, f"- {datetime.fromtimestamp(when):%a %d %b}: the user said: {you} / you said: {him}")
                    for t in best for i, (when, you, him) in enumerate(reversed(t["talk"]))), key=lambda p: p[0])
    out = ""
    for _, line in lines:
        if out and len(out) + len(line) > 600:
            break
        out += line + "\n"
    for t in best:
        t["used"] = now
    try:
        save_topics(topics)
    except OSError:
        pass                                                   # only "used" is lost
    log(f"topic memory: {len(best)} topic(s) recalled")
    return EARLIER + out + gist


EARLIER = "\nFROM EARLIER TALKS (only if it helps; don't bring it up otherwise):\n"


TOPICS_BAD = "I can't read my topic memory, so I left it alone."
NO_TALK = "I don't remember us talking about that."


def topics_about(x):
    """M2b: the filed topics about X: all of its keywords, or close in meaning. Unreadable raises OSError / ValueError."""
    kw = keywords(x)
    return [t for t in load_topics() if (kw and kw <= set(t["kw"])) or meaning(x, [topic_text(t)], MEANING_TALK)]


def talk_forget(x):
    """The route for "forget what we said about X": read the matching talks back and ask (the usual yes)."""
    try:
        hits = topics_about(x)
    except (OSError, ValueError):
        return ("say", None, None, TOPICS_BAD)
    if not hits:
        return ("say", None, None, NO_TALK)
    said = "; ".join(t["talk"][0][1][:80] for t in hits[:3]) + ("; and more" if len(hits) > 3 else "")
    n = len(hits)
    return ("act", "forget_talk", [t["talk"] for t in hits],
            f"Forget {n} earlier talk{'s' if n != 1 else ''} about that, starting with: {said}? Confirm with yes.")


def talk_list(x):
    """What you said in the talks about X, newest first, about 300 characters, then up to 3 gist lines about X."""
    try:
        hits = topics_about(x)
        kw = keywords(x)
        notes = [f for _, f in load_gist()[0] if (kw and kw <= keywords(f)) or meaning(x, [f], MEANING_TALK)][:3]
    except (OSError, ValueError):
        return TOPICS_BAD
    if not hits:
        return "From before: " + "; ".join(notes) + "." if notes else NO_TALK
    out = ""
    for you in (you for t in hits for _, you, _ in reversed(t["talk"])):
        if out and len(out) + len(you) > 300:
            break
        out += ("; " if out else "") + you.rstrip(".!? ")
    return f"You asked me: {out}." + (" From before: " + "; ".join(notes) + "." if notes else "")


# M3: once a day while idle, old topics become up to 3 tiny facts each in Data\jarvis_gist.txt ("date|fact" lines,
# "#month YYYY-MM" = the last re-compaction). The model writes them; code checks every one against the saved talk.
GIST_FILE = os.path.join(DATA, "jarvis_gist.txt")
GIST_AGE = 7 * 86400
GIST_SCHEMA = {"type": "object", "properties": {"facts": {"type": "array", "items": {"type": "string"}}}, "required": ["facts"]}
GIST_PROMPT = ("Write at most 3 short facts worth keeping from these lines, each under 120 characters, starting "
               "'The user'. Use only words, names and numbers that appear in the lines; add nothing. Output JSON only.")
gist_day = [""]       # the day compaction last finished
gisting = threading.Lock()


def load_gist():
    """([(date, fact)], month of the last re-compaction). Unreadable raises OSError / ValueError."""
    if not os.path.exists(GIST_FILE):
        return [], ""
    with open(GIST_FILE, "r", encoding="utf-8") as f:
        rows = [l.rstrip("\n") for l in f if l.strip()]
    month = next((r[7:] for r in rows if r.startswith("#month ")), "")
    return [tuple(r.split("|", 1)) for r in rows if not r.startswith("#") and "|" in r], month


def save_gist(lines, month):
    tmp = GIST_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write("".join(f"{l}\n" for l in ([f"#month {month}"] if month else []) + [f"{d}|{g}" for d, g in lines]))
    os.replace(tmp, GIST_FILE)


def gist_for(text):
    """Up to 3 gist lines related to the question (words or meaning), most shared words first."""
    try:
        lines = [g for _, g in load_gist()[0]]
    except (OSError, ValueError):
        return ""
    kw = keywords(text)
    hits = sorted((g for g in lines if related(text, [g])), key=lambda g: -len(kw & keywords(g)))[:3]
    return "".join(f"- earlier: {g}\n" for g in hits)


def gist_ok(fact, talk):
    """The code check: under 120 characters, and every number, name and content word is in the talk ("user" aside)."""
    words = keywords(fact) - TALK_STOP - {"user"}                # "likes" -> "like": a stop-word after the cut
    return (0 < len(fact) <= 120 and bool(words) and words <= keywords(talk)
            and set(re.findall(r"\d+", fact)) <= set(re.findall(r"\d+", talk)))


def ask_gist(model, talk):
    """The model's facts for some talk, unchecked; None when the model is down or answers nonsense."""
    opts = {"num_ctx": ctx_tokens(), "temperature": 0, "num_predict": 200}
    if not gpu():
        opts["num_thread"] = cpu_threads()
    try:
        out = http_json("/api/chat", {"model": model, "stream": False, "format": GIST_SCHEMA, "keep_alive": keep_alive(),
                                      "options": opts, "messages": [{"role": "system", "content": GIST_PROMPT},
                                                                    {"role": "user", "content": talk}]}, timeout=60)
        return [" ".join(str(f).replace("|", "/").split()) for f in json.loads(out["message"]["content"])["facts"]][:3]
    except Exception as e:
        log(f"compaction: model not usable ({type(e).__name__})")
        return None


def compact(now, stop=lambda: False):
    """M3a: topics unused GIST_AGE, or the oldest past 100, become checked facts. Nothing passes the check -> the topic
    stays and is tried tomorrow, removed without a gist after 3 such tries. Model down -> all stay, no try counted.
    Returns False when stopped early (a turn started or the HUD left FULL)."""
    try:
        topics = sorted(load_topics(), key=lambda t: t["used"])
        load_gist()
    except (OSError, ValueError):
        log("compaction: memory unreadable, left alone")
        return True
    old = [t for i, t in enumerate(topics) if now - t["used"] > GIST_AGE or i < len(topics) - 100]
    if not old:
        return True
    model, facts, gone, tried, dropped, finished = pick_model(0), [], [], {}, 0, True
    for t in old:
        if stop():
            finished = False
            break
        talk = "\n".join(f"User: {y}\nJARVIS: {h}" for _, y, h in t["talk"])
        got = ask_gist(model, talk) if model else None
        if got is None:                                        # model down: try again tomorrow, nothing counted
            break
        got = [g for g in got if gist_ok(g, talk)]
        if got:
            facts += [f"{datetime.fromtimestamp(now):%Y-%m-%d}|{g}" for g in got]
            gone.append(t["talk"])
        elif t.get("tries", 0) >= 2:
            gone.append(t["talk"])
            dropped += 1
        else:
            tried[json.dumps(t["talk"])] = t.get("tries", 0) + 1
    try:
        if facts:                                              # the gist first: a failed topic save repeats, never loses
            with open(GIST_FILE, "a", encoding="utf-8") as f:
                f.write("".join(l + "\n" for l in facts))
        topics = load_topics()                                 # again: a turn may have filed talk meanwhile
        for t in topics:
            if json.dumps(t["talk"]) in tried:
                t["tries"] = tried[json.dumps(t["talk"])]
        save_topics([t for t in topics if t["talk"] not in gone])
    except (OSError, ValueError) as e:
        log(f"compaction: not saved ({type(e).__name__})")
        return True
    log(f"compaction: {len(gone) - dropped} topic(s) -> {len(facts)} fact(s), {len(tried)} kept for tomorrow, "
        f"{dropped} removed without a gist")
    return finished


def recompact(now, stop=lambda: False):
    """M3b: once a month, only over 200 gist lines: among the oldest 100, lines sharing 2+ keywords are merged into
    fewer under the same check. Your facts (jarvis_memory.txt) are never touched."""
    try:
        lines, month = load_gist()
    except (OSError, ValueError):
        return
    this = f"{datetime.fromtimestamp(now):%Y-%m}"
    if len(lines) <= 200 or month == this:
        return
    model, old, gone, merged = pick_model(0), lines[:100], set(), []
    for i, (d, g) in enumerate(old):
        if len(merged) >= 30 or stop():                        # shortcut: about 10 merges a month; plenty at 200+ lines
            break
        group = [j for j in range(i, len(old)) if j not in gone and len(keywords(g) & keywords(old[j][1]) - {"user"}) >= 2]
        if i in gone or len(group) < 2:
            continue
        text = "\n".join(old[j][1] for j in group)
        got = ask_gist(model, text) if model else None
        if got is None:
            return                                             # model down: next idle day
        got = [x for x in got if gist_ok(x, text)]
        if got and len(got) < len(group):
            gone.update(group)
            merged += [(d, x) for x in got]
    try:
        save_gist(merged + [l for j, l in enumerate(lines) if j not in gone], this)
    except OSError as e:
        log(f"re-compaction: not saved ({type(e).__name__})")
        return
    log(f"re-compaction: {len(gone)} line(s) -> {len(merged)}")


def compact_due(now, since):
    """Once a day, 10 minutes after the last turn, with no turn running and the HUD on FULL (no game)."""
    return (gist_day[0] != f"{datetime.fromtimestamp(now):%Y-%m-%d}" and now - since >= 600
            and not busy.locked() and hud_tier() == 0 and not gisting.locked())


def daily_memory():
    with gisting:
        stop = lambda: busy.locked() or hud_tier() > 0
        if compact(time.time(), stop) and not stop():
            recompact(time.time(), stop)
            gist_day[0] = f"{datetime.now():%Y-%m-%d}"


def file_active():
    """Unlinked, timed out or "new topic": the window is filed (topic memory, M2) and emptied."""
    file_talk(history)
    history.clear()


def active(text):
    """The window to send with this question. It is kept when the question is related to it (related()), starts
    like a follow-up, or is 3 words or fewer; otherwise (or after ACTIVE_TTL) it is filed first."""
    file_talk(history[:-4])                                    # talk that drops off the window is filed too
    del history[:-4]
    plain = " ".join(re.sub(r"[^a-z' ]", " ", text.lower().replace("’", "'")).split())
    if history and (time.time() - last_turn > ACTIVE_TTL or not (
            len(plain.split()) <= 3 or FOLLOW_START.match(plain) or related(text, [m["content"] for m in history]))):
        file_active()
    return list(history)


def fit_context(system, past, user):
    """Drop the oldest exchanges until everything fits the context window (with room left for the answer), so the
    system prompt - the HUD data and your note - is never the part the model loses."""
    budget = ctx_tokens() - 400
    est = lambda msgs: sum(len(m["content"]) for m in msgs) // 3 + 8 * len(msgs)   # ~3 characters per token
    past = list(past)
    while past and est(system + past + [user]) > budget:
        past = past[2:]
    return system + past + [user]


def chime():
    if setting("JarvisChime", "1") != "1":
        return 0.0
    for name in ("chime.wav", "startup.wav"):
        p = os.path.join(RES, "Sounds", name)
        if os.path.exists(p):
            try:
                import winsound
                with wave.open(p, "rb") as wf:
                    dur = wf.getnframes() / float(wf.getframerate())
                winsound.PlaySound(p, winsound.SND_FILENAME | winsound.SND_ASYNC)
                return min(dur, 0.8)
            except Exception:
                return 0.0
    return 0.0


def watchdog(started):
    """A turn that hangs (stuck microphone, frozen model) is cancelled after 3 minutes."""
    while busy.locked() and started == turn_id[0]:
        if time.time() - started > 180:
            log("watchdog: turn took over 3 minutes - cancelling")
            cancel.set()
            return
        time.sleep(2)


turn_id = [0.0]
NO_FOLLOW = re.compile(r"(?:Okay, never mind|Okay, no \w+|Okay, I left (?:them|it)|Cancelled)\.$")   # he was told to drop it: no follow-up
# a whole reply that means "stop" / "we're done", in any turn: he stops without answering (FR6 L1). Also Whisper's
# stock "Thank you." on noise (FR6 L4): a real thanks needs no answer either
_END = (r"(?:(?:ok|okay|alright|great|cool|perfect|no|nah|oh) )?(?:thanks|thank you(?: so much)?|that's all|that's it|"
        r"no thanks|no thank you|nope|no|goodbye|bye|i'm good|i'm fine|nothing|stop(?: it| talking)?|all good|cheers|"
        r"(?:be )?quiet|shut up|shush|hush|never mind|(?:that's )?enough)(?: jarvis)?")
ENDERS = re.compile(rf"{_END}(?: {_END})*")
# courtesy: a whole reply that is only manners gets a short proper answer from code, no model, no follow-up.
# "{name}" becomes ", <JarvisCallMe>" (nothing when that setting is empty)
_OK = r"(?:(?:ok|okay|alright|great|cool|perfect|oh) )?"
COURTESY = ((re.compile(rf"(?:{_OK}(?:thanks|thank you|thank you so much|thank you very much|thanks a lot|cheers|"
                        r"much appreciated)(?: jarvis)? ?)+"), "You're welcome."),
            (re.compile(r"(?:hello|hi|hey|hiya|howdy|greetings)(?: there)?(?: jarvis)?"), "Hello{name}."),
            (re.compile(rf"{_OK}(?:goodbye|bye|bye bye|see you|see you later)(?: jarvis)?"), "Goodbye{name}."),
            (re.compile(rf"{_OK}good ?night(?: jarvis)?"), "Good night{name}."),
            (re.compile(r"(?:oh )?(?:sorry|my bad)(?: jarvis)?"), "No problem."))
ROOM_ASK = "Were you talking to me?"


def room_talk(text):
    """FR5 N3: long talk with no question, no "you" and not his name: likely meant for someone else in the room."""
    words = re.findall(r"[a-z']+", text.lower().replace("’", "'"))
    return len(words) >= 25 and "?" not in text and not {"you", "your", "you're", "jarvis"} & set(words)


NEW_TOPIC = re.compile(r"(?:(?:ok|okay|alright),? )?(?:let'?s )?(?:(?:start|have) )?(?:a )?(?:new |change (?:the )?)(?:topic|subject)(?:[,.!?:;-]+\s*|\s*$)", re.I)


# REDESIGN slice B: what the turn means, decided once. via: rule, context or ai-reread
Decision = namedtuple("Decision", "kind action target prompt via")
LEVEL = re.compile(r"(?:(?:about|around|roughly|maybe|like|make it|to|at|um|uh|so|and)\s+)*(.+?)\s*(%| ?percent)?")
VOLUME_DID = ("changed the volume", "muted the sound", "unmuted the sound")


def level_fix(text):
    """L2: a lone level ("About 20%.") is a half-heard volume command. Right after a volume change it sets it;
    otherwise only "N percent" counts, and he asks first. None: not a lone level."""
    m = LEVEL.fullmatch(" ".join(re.sub(r"[^a-z0-9% ]", " ", text.lower()).split()))
    n = m and _num(m.group(1))
    if n is None or n > 100:
        return None
    if did and did[-1][1] in VOLUME_DID and time.time() - did[-1][0] <= ACTIVE_TTL:
        return Decision("act", "volume", ("set", int(n)), None, "context")
    if m.group(2):
        return Decision("act", "volume", ("set", int(n)), f"Did you mean the volume at {int(n)} percent?", "context")
    return None


def understand(text, model, quiet, room):
    """Rules first, then the last exchange, then the model only on a miss. kind "room": likely not for him."""
    kind, action, target, prompt = fix_route(text, route(text))
    via = "rule"
    if kind == "chat":
        lone = level_fix(strip_name(text))
        if lone:                                               # still asked back below if Whisper was unsure
            kind, action, target, prompt, via = lone
        elif text != room and room_talk(text):
            return Decision("room", None, None, None, "rule")
    if ask_ai(text, (kind, action, target, prompt)):           # a missed command: the AI's reading, checked, or as before
        filler("confirm_wait", quiet)                          # "One moment." while the model reads it; the answer waits for it
        read = interpret(model, text)
        if read:
            kind, action, target, prompt = read
            via = "ai-reread"
    if kind == "act" and prompt is None and heard_score[0] < -1.0:   # Whisper was unsure: never act on a guess
        prompt = f"Did you say: {text}?"
    return Decision(kind, action, target, prompt, via)


# REDESIGN slice C: lanes. command = code runs it; info = an answer from data only; chat = talk.
# shortcut: no task lane yet (nothing routes there), add it with Phase 7 multi-settings / Stage 2
ASKING = re.compile(r"(?:what|when|where|which|who|how|do|does|did|am|is|are|have|has|any|tell me|show me|check|read)\b", re.I)
INFO_PROMPT = ("\nINFO QUESTION: answer only from the LIVE HUD DATA and the results above. If what was asked is not "
               "there, say you can't see it. Never invent events, emails, names or numbers.")


def info_blocks(text):
    """The data blocks a chat line asks about. Measured 2026-10-14 (MiniLM): info questions 0.46-0.84, talk up to
    0.50, so only a question about you ("I / my", no "you") at 0.5, or any question at 0.55, counts."""
    t = strip_name(text).strip().lower().replace("’", "'")
    words = set(re.findall(r"[a-z']+", t))
    if not (t.endswith("?") or ASKING.match(t)) or {"you", "your", "you're", "yourself"} & words:
        return set()
    floor = 0.5 if {"i", "my", "me", "i'm", "i've", "am"} & words else 0.55
    return {b for b, ex in BLOCK_EXAMPLES.items() if closeness(t, ex) >= floor}


def lane_of(kind, blocks):
    if kind in ("notes", "apps", "brief", "fact", "level") or kind == "chat" and blocks:   # fact: the clock, sums
        return "info"
    return "chat" if kind in ("chat", "guard") else "command"


def no_data(text, blocks):
    """L10: a fixed reply when everything asked about is empty, so the model never fills the gap. None: data to use."""
    if not blocks or blocks - {"calendar", "mail", "todo"}:
        return None
    have = context(text)
    lines = []
    if "calendar" in blocks and "Upcoming calendar events:" not in have:
        lines.append("Nothing is coming up on your calendar." if re.search(r"^C [1-9]", read_kv("calendar.txt"), re.M)
                     else "I can't see a calendar - none is connected (Control Center > DATA > CALENDARS).")
    if "mail" in blocks and "Unread Gmail:" not in have:
        lines.append("I can't see your Gmail right now.")
    if "todo" in blocks and "Open to-dos:" not in have:
        lines.append("Your to-do list is empty." if todo_note() else "No to-do note is set (Control Center > DATA).")
    return " ".join(lines) if len(lines) == len(blocks) else None


def command_reply(kind, action, target, prompt, quiet):
    """Carry out a command that needs no confirmation and return what to say; None if it is not one."""
    if kind in ("say", "fact"):
        return prompt
    if kind == "undo":
        return undo_last()
    if kind == "level":
        is_muted, percent = speakers()
        return f"The volume is at {percent} percent" + (", muted." if is_muted else ".")
    if kind == "remind":
        return remind_reply(action, target, quiet)
    if kind == "memory":
        return memory_reply(action, target)
    if kind == "act" and prompt is None:
        return done_line(action, target) if run_action(action, target) else "That didn't work."
    return None


UNDO_SAID = re.compile(r"\b(?:undo|remove)\b", re.I)
UNDO_WAIT = 5                                                 # seconds after a command reply that listen for "undo"


def ask_yes(prompt, quiet):
    """Every confirmation: ask, listen up to 15 s, and True only for a plain yes (the shared YES set)."""
    reply_line(prompt, quiet)
    pending = {"expires": time.time() + 15}                    # counted from the end of the spoken prompt
    S.set(state="listening", level=0.0)
    answer = hear()
    if answer:
        convo_add("U", answer)
    return confirmed(pending, answer, time.time()) and not cancel.is_set()


def turn(tier, follow=0, woke=False):
    """One exchange, then follow-ups without the wake word (JarvisFollowUp) for as long as you keep answering
    (D2, no cap): after a chat or info answer anything goes; after a command only "undo" / "remove" for 5 s.
    A loop, not recursion, so a long talk never grows the stack. `woke`: started by the wake word."""
    mode = None
    while True:
        left = {}                                              # exchange() fills "again"; survives its early returns
        exchange(tier, follow, woke, mode, left)
        mode = left.get("again")
        if not mode or setting("JarvisFollowUp", "1") != "1" or cancel.is_set():
            return
        follow, woke = follow + 1, False


def exchange(tier, follow, woke, mode, left):
    """One turn. mode: None, or what the last one left open ("follow" / "undo"); what this one leaves open goes in
    left["again"] (a dict, not a return value: a `return` inside the try below would drop it)."""
    global history, last_turn
    if not busy.acquire(blocking=False):
        return
    way = {}                                                   # 6j: which path answered; logged once in finally
    cancel.clear()
    turn_id[0] = time.time()
    threading.Thread(target=watchdog, args=(turn_id[0],), daemon=True).start()
    try:
        if tier >= 3:
            return
        t_click = time.time()
        miss = missing_packages()
        if miss:
            problem("Setup needed - missing " + ", ".join(miss) + ". Run Control Center > JARVIS > SETUP")
            return
        if setting("JarvisGPU", "prefer").lower() == "require" and not gpu():   # never a turn on the CPU
            S.set(err="RTX is off - switch the laptop to hybrid graphics (JarvisGPU=require)")
            reply_line("My graphics card is off.", muted())
            return
        S.set(state="listening", level=0.0, err="")
        if not ensure_ollama():
            problem("Ollama isn't running or installed - run Control Center > JARVIS > SETUP")
            return
        model = pick_model(tier)
        if not model:
            want = setting("JarvisModel", "llama3.1:8b")
            problem(f"Model {want} is not downloaded (Control Center > JARVIS > MODEL, or: ollama pull {want})")
            return
        if follow:
            time.sleep(0.3)                                    # let the last of his own voice fade before the microphone opens
        else:
            warm(model)
            threading.Thread(target=prepare_fillers, daemon=True).start()   # cheap if nothing changed
            time.sleep(chime())                                # don't record the chime
        log(f"timing: click -> listening {time.time() - t_click:.2f}s")
        t_listen = time.time()
        hud = []
        reading = threading.Thread(target=lambda: hud.append(sensors()), daemon=True)
        reading.start()                                        # read while you speak, so it costs the reply nothing
        audio = listen(patience=UNDO_WAIT if mode == "undo" else follow_wait()) if follow else listen()
        if audio is None or cancel.is_set():
            return
        t_spoke = way["t"] = time.time()
        log(f"timing: listening -> end of speech {t_spoke - t_listen:.2f}s")
        S.set(state="thinking", level=0.0)
        try:
            text = transcribe(audio)
        except ImportError:
            problem("Speech recognition isn't installed - run Control Center > JARVIS > SETUP")
            return
        log(f"timing: end of speech -> text {time.time() - t_spoke:.2f}s")
        log(f"you: {text}")
        if not text and woke:                                  # FR6 L9: likely a false wake - end quietly
            log("transcript: nothing after the wake word - ended quietly")
            return
        if not text and not follow and not cancel.is_set():   # spoke but nothing came out: ask once (silence on a follow-up just ends)
            quiet = muted()
            reply_line("Sorry, I didn't catch that.", quiet)
            left["again"] = not quiet and "follow"
            return
        if not text or cancel.is_set():
            return
        if mode == "undo" and not UNDO_SAID.search(text):     # the undo window: other room sound gets no answer
            log("follow-up: ended (not an undo)")
            return
        convo_add("U", text)
        quiet = muted()

        def fixed(reply):
            """Say a fixed reply, keep it in the chat history, and listen once more unless he was told to drop it."""
            global history, last_turn
            reply_line(reply, quiet)
            active(text)
            # stamped, so "7:00 AM tomorrow" in the reply still means the right day after midnight
            history += [{"role": "user", "content": f"[{datetime.now():%a %d %b, %I:%M %p}] {text}"},
                        {"role": "assistant", "content": reply}]
            last_turn = time.time()
            # [F]: chat and info listen again; a command only for "undo", and only if it changed something now
            fresh = undo and undo[0] >= way.get("t", 0) + UNDO_FOR
            left["again"] = (not quiet and not cancel.is_set() and not NO_FOLLOW.match(reply)
                     and ("follow" if way.get("lane") != "command" else "undo" if fresh else None))
        S.set(err="")
        if mode == "undo":                                     # "undo that" / "remove it" right after a change: ask first
            way.update(kind="undo", via="rule", lane="command")
            what = did[-1][1] if did else "that"
            fixed(undo_last() if ask_yes(f"Do you want me to undo that - {what}?", quiet) else "Okay, I left it.")
            return
        fact = offer.pop("fact", None) if time.time() < offer.get("expires", 0) else None
        room = offer.pop("room", None) if time.time() < offer.get("expires", 0) else None
        offer.clear()
        plain = " ".join(re.sub(r"[^a-z]+", " ", strip_name(text).lower()).split())
        if room and plain in YES:                              # "Were you talking to me?" "Yes": answer what was said
            text = room
        if fact and (plain in YES or re.fullmatch(r"(?:yes )?(?:please )?(?:remember|save|note) (?:that|it)(?: please)?", plain)):
            way.update(kind="memory", action="save", via="rule", lane="command")
            fixed(memory_reply("save", fact))
            return
        said = " ".join(re.sub(r"[^a-z' ]", " ", strip_name(text).lower().replace("’", "'")).split())
        polite = text != room and next((r for rx, r in COURTESY if rx.fullmatch(said)), None)
        if polite and not (woke and heard_score[0] < -1.0):  # a weak "Thank you." after a wake is Whisper's noise phrase
            way.update(kind="courtesy", via="rule")
            name = setting("JarvisCallMe", "").strip()
            reply_line(polite.replace("{name}", f", {name}" if name else ""), quiet)
            return
        if text != room and (polite or ENDERS.fullmatch(said)):
            way.update(kind="control", via="rule")             # control check before any routing: never reaches the model
            log("control: ended by you")
            return
        m = NEW_TOPIC.match(strip_name(text))
        way.update(kind="new_topic", via="rule")               # replaced below unless it was "new topic" alone
        if m:                                                  # files the window; "new topic, <question>" goes on without it
            file_active()
            last.clear()                                       # M1b: "cancel it" no longer points back
            text = strip_name(text)[m.end():].strip()
            if not text:
                fixed("Okay.")
                history.clear()                                # "new topic" / "Okay." is not talk to keep
                return
        # "show me what you've said" / "close the log": handled here, no model needed
        way["kind"] = "log"
        if HIDE_LOG.search(text):
            S.set(pop="close")
            reply = "Closing the log."
            convo_add("J", reply)
            if not quiet:
                speak_all([reply])
            return
        if SHOW_LOG.search(text):
            S.set(pop="open")
            reply = "Here's everything we've said."
            convo_add("J", reply)
            if not quiet:
                speak_all([reply])
            return
        kind, action, target, prompt, via = understand(text, model, quiet, room)
        way.update(kind=kind, action=action, via=via)
        if kind == "room":                                     # asked once; a "yes" answers it in full
            log("transcript: not for me? asked")
            reply_line(ROOM_ASK, quiet)
            offer.update(room=text, expires=time.time() + 30 + follow_wait())
            left["again"] = not quiet and "follow"
            return
        if kind == "heard":
            fixed(f"I heard: {recent['you']}" if recent["you"] else "I haven't heard anything yet.")
            return
        if kind == "again":
            fixed(recent["me"] or "I haven't said anything yet.")
            return
        if cancel.is_set():                                    # stopped while the model read it: nothing runs
            return
        blocks = info_blocks(text) if kind == "chat" else set()
        lane = way["lane"] = lane_of(kind, blocks)
        empty = no_data(text, blocks)
        if empty:                                              # no data, no model
            fixed(empty)
            return
        # shortcut: reminders and alarms are not read back (he says the time back and "undo" exists), add if needed
        recent["you"] = text
        extra = ""
        if kind == "multi":                                    # "set an alarm for 7 and a timer for 10 minutes": in order
            replies = [command_reply(*part, quiet) for part in target]
            quiet = muted()
            fixed(" ".join(replies))
            return
        if kind != "act" or prompt is None:
            reply = command_reply(kind, action, target, prompt, quiet)
            if reply is not None:
                if action in ("mute", "unmute", "volume"):     # the reply follows the new state: shown if now silent
                    quiet = muted()
                fixed(reply)
                return
        if kind == "act":
            # two-phase: ask, and listen for the answer (15 s) without another click
            if ask_yes(prompt, quiet):
                ok = run_action(action, target)
                fixed(("Added." if action == "todo" else "Done.") if ok else "That didn't work.")
            else:
                log(f"action {action} not confirmed")
                fixed(memory_reply("save", target[1]) + " I kept the old one too." if action == "replace_fact" else "Cancelled.")
            return
        if kind == "notes":
            filler("notes", quiet)
            hits = smart_search(target or text)
            if hits is None:                                   # no ChromaDB: keyword search
                root, hits = search_notes(target or text)
            else:
                root = vault_dir()
            if not root:
                extra = "\nNOTE SEARCH: no vault is set (Control Center > JARVIS > NOTES VAULT)."
            elif hits:
                extra = "\nNOTE SEARCH RESULTS (from the user's vault - answer from these):\n" + "\n".join(
                    f"- {name}: {snip}" for _, name, snip in hits)
            else:
                extra = f"\nNOTE SEARCH: nothing in the vault matched '{target}'."
        elif kind == "apps":
            filler("apps", quiet)
            apps = start_apps()
            names = sorted({n for n, _ in apps or []})
            if apps is None:
                extra = "\nINSTALLED APPS: the app list isn't ready yet (the HUD is still scanning)."
            elif target:
                app = best_app(target)
                extra = f"\nINSTALLED APP CHECK: '{target}' -> " + (f"yes, installed as {app[0]}." if app else "not found in the Start menu.")
            else:
                extra = f"\nINSTALLED APPS ({len(names)}): " + ", ".join(names[:120])
        elif kind == "guard":
            extra = ("\nGUARDRAIL: this request is destructive or a joke. Nothing will be executed - you have no ability to "
                     "run commands. Play along in character with dry wit if it's clearly playful, or decline politely if "
                     "it's serious. Never claim to have actually done it.")
            log("guardrail: request handled in persona only")
        elif kind == "brief":
            extra = "\n" + BRIEFING
        apart = kind in ("brief", "notes")                     # these neither send nor file the window
        past = [] if apart else active(text)
        reading.join(1.5)                                      # a stuck sensor never holds the reply: its lines are left out
        # the question and the one before it pick the blocks, so "and tomorrow?" after a calendar question still has it
        ask = text + (" " + past[-2]["content"] if len(past) >= 2 else "")
        readings = "\n".join(h for h in hud if h).splitlines()
        want = wants(ask, kind)
        if "pc" not in want:                                   # not a PC question: at most the schedule, and only if it's about time
            readings = [r.replace("Pending:", "Pending (don't bring it up unless asked about alarms, reminders or timers):", 1)
                        for r in readings if r.startswith("Pending:") and "pending" in want]
        extra += "" if apart else recall(text)                # M2: an earlier talk, only when the question is about it
        extra += INFO_PROMPT if lane == "info" else ""
        messages = fit_context([{"role": "system", "content": system_prompt(ask, kind) + "".join("\n" + r for r in readings) + extra}],
                               past, {"role": "user", "content": text})
        collected = []
        way["via"] = "model"
        log(f"timing: end of speech -> reply start {time.time() - t_spoke:.2f}s")
        stream = chat_stream(model, messages, 0 if lane == "info" else 0.5)
        if quiet and setting("JarvisMutedPopup", "1") == "1":
            say_text_only(no_claims(sentences_from(stream, collected), collected), collected)
        else:
            speak_all(no_claims(sentences_from(stream, collected), collected))
        reply = "".join(collected).strip()
        S.set(state="idle", level=0.0)                        # done talking: the HUD doesn't wait for the GPU check
        if ollama_on_cpu(model):
            chat_to_gpu(model)
        else:
            _moved.discard(model)
        log(f"timing: end of speech -> reply done {time.time() - t_spoke:.2f}s ({model})")
        if not reply and not cancel.is_set():
            problem(f"{model} gave no answer - try again, or pick another model in Control Center > JARVIS")
            return
        log(f"jarvis: {reply}")
        recent["me"] = reply
        convo_add("J", reply)
        if not apart:
            history += [{"role": "user", "content": text}, {"role": "assistant", "content": reply}]
            last_turn = time.time()
        S.set(say=reply)
        fact = learnable(text) if kind == "chat" and not cancel.is_set() else ""
        if fact:                                               # M4a-3: one offer; the next turn's yes saves it
            reply_line("Want me to remember that?", quiet)
            offer.update(fact=fact, expires=time.time() + 30 + follow_wait())
        left["again"] = not quiet and not cancel.is_set() and "follow"   # fixed replies set it in fixed()
    except urllib.error.URLError as e:
        problem(f"Lost the connection to Ollama ({e.reason}) - is it still running?")
        live("")
    except Exception as e:
        log(f"turn failed: {e!r}")
        problem(str(e).split("\n")[0][:110])
        live("")
    finally:
        if "kind" in way:                                      # only names from the code, never words you said
            act = way.get("action")
            act = f" {act}" if isinstance(act, str) and re.fullmatch(r"[a-z_]+", act) else ""
            tag = f"{way['lane']}." if "lane" in way else ""
            log(f"route: {tag}{way['kind']}{act} via {way['via']}, total {time.time() - way['t']:.2f}s")
        S.set(state="idle", level=0.0)
        busy.release()


# ------------------------------------------------------------------ wake word ("Hey Jarvis")
# JarvisWakeWord=1: a small background thread listens for "Hey Jarvis" with openWakeWord (runs on your PC, about
# 1-3 % of one CPU core; audio is checked in 80 ms pieces and never stored or sent anywhere). When it hears it, it
# starts a turn exactly like a click. It pauses while Jarvis is busy, while the HUD is on STEALTH, and when turned off.
def hud_tier():
    try:
        return int(float(setting("PerfTier", "0")))
    except ValueError:
        return 0


def barge_in():
    """JarvisBargeIn: off | wake ("Hey Jarvis" stops him mid-sentence, the default) | voice (any speech, headphones only)."""
    v = setting("JarvisBargeIn", "wake").strip().lower()
    return v if v in ("off", "wake", "voice") else "wake"


def barge_turn(follow):
    """The turn after he was talked over: waits for the stopped one to let go (up to 5 s), then listens once."""
    end = time.time() + 5
    while busy.locked():
        if time.time() > end:
            log("barge-in: the stopped turn didn't end - not listening")
            return
        time.sleep(0.05)
    turn(hud_tier(), follow, True)


STOP_KEYS = {"end": 0x23}                                     # VK_END


def stop_key_loop():
    """JarvisStopKey (End, or off): while he is busy the key stops him, like a click; when idle it is not taken, so it
    never wakes him and other apps keep it. A hotkey belongs to the thread that made it, so all of it runs here."""
    import ctypes
    from ctypes import wintypes
    user32 = ctypes.windll.user32
    msg, held, refused = wintypes.MSG(), None, None           # held: the key name now registered; refused: the one Windows said no to
    while True:
        try:
            key = setting("JarvisStopKey", "end").strip().lower()
            want = key if busy.locked() and key in STOP_KEYS and key != refused else None
            if held and held != want:
                user32.UnregisterHotKey(None, 1)
                held = None
            if want and not held:
                if user32.RegisterHotKey(None, 1, 0x4000, STOP_KEYS[want]):   # MOD_NOREPEAT
                    held = want
                else:
                    refused = want                             # not retried until the setting changes
                    log(f"stop key: Windows refused {want.upper()} (another app has it)")
                    problem(f"Stop key: {want.upper()} is taken by another app - pick another in Control Center", popup=False)
            if refused and key != refused:
                refused = None
            while user32.PeekMessageW(ctypes.byref(msg), None, 0x0312, 0x0312, 1):   # WM_HOTKEY, PM_REMOVE
                if held:
                    stop_now("stop key")
        except Exception as e:
            log(f"stop key: {e!r}")
            time.sleep(5)
        time.sleep(0.05)


# ------------------------------------------------------------------ wake word training (plan R5-6, step 6a)
# Your own "Hey Jarvis", "Hey" and "Jarvis" become small checks next to the normal score (Fix Round 5 N1).
# The recordings stay in memory and are never written; only the checks are saved, as Data\wake_<style>.pkl.
WAKE_STYLES = (("hey_jarvis", "Hey Jarvis", 'say "Hey Jarvis"'),
               ("hey", "Hey", 'say just "Hey"'),
               ("jarvis", "bare Jarvis", 'say just "Jarvis"'))
WAKE_FLOOR = 0.1                       # the lowest normal score a moment needs to count as an example
WORD_STYLES = ("hey", "jarvis")        # single words: examples are the moments with speech, not a normal score
                                       # (the normal model knows only the whole phrase, a bare "Hey" may never score)


def heard_speech(oww):
    """The speech filter heard speech 0.4-0.56 s ago, the same frames openWakeWord itself checks."""
    vad = list(getattr(getattr(oww, "vad", None), "prediction_buffer", []))[-7:-4]
    return bool(vad) and max(vad) >= 0.5


def speech_feats(clip, oww):
    """The openWakeWord features of every 80 ms moment of `clip` in which the speech filter hears speech."""
    import numpy as np
    out = []
    oww.reset()
    if hasattr(oww, "vad"):
        oww.vad.prediction_buffer.clear()             # reset() keeps it: the last clip's speech would count here
    for i in range(0, len(clip) - 1280, 1280):
        oww.predict(clip[i:i + 1280])
        if heard_speech(oww):
            out.append(oww.preprocessor.get_features(oww.model_inputs["hey_jarvis"]))
    return np.vstack(out) if out else np.empty((0, oww.model_inputs["hey_jarvis"], 96))


# shortcut: a click stops it only between clips (at most 15 s late); a stoppable recorder if that ever matters
def record(sec):
    """`sec` seconds from the microphone as 16 kHz int16, the form openWakeWord reads."""
    import sounddevice as sd
    if not mic.acquire(timeout=3):
        raise RuntimeError("The microphone is busy - try again")
    try:
        a = sd.rec(int(16000 * sec), samplerate=16000, channels=1, dtype="int16", device=mic_device())
        sd.wait()
        return a[:, 0]
    finally:
        mic.release()


def train_wake():
    """Control Center WAKE WORD > TRAIN: each style six times after a ding, then 15 s of normal talk as the
    "not Jarvis" examples. Holds the turn lock, so the wake word lets go of the microphone; a click stops it."""
    import pickle
    import numpy as np
    from openwakeword.model import Model
    from openwakeword.custom_verifier_model import get_reference_clip_features, train_verifier_model
    with busy:
        cancel.clear()
        turn_id[0] = time.time()
        try:
            clips = {}
            for name, _, how in WAKE_STYLES:
                reply_line(f"After each ding, {how}. Six times.", False)
                clips[name] = []
                for _ in range(6):
                    S.set(state="listening", level=0.0)        # not "speaking": the wake word would keep the microphone
                    play_samples(*ding())
                    if cancel.is_set():
                        return
                    clips[name].append(record(3))
            reply_line("Now talk normally for fifteen seconds, about anything, without my name.", False)
            S.set(state="listening", level=0.0)
            neg = record(15)
            if cancel.is_set():
                return
            try:                                               # the speech filter picks the moments of a bare word
                oww = Model(wakeword_models=["hey_jarvis"], inference_framework="onnx", vad_threshold=0.5)
            except Exception as e:
                log(f"train: without the speech filter ({type(e).__name__}) - Hey and bare Jarvis stay off")
                oww = Model(wakeword_models=["hey_jarvis"], inference_framework="onnx")
            pad = np.zeros(16000, dtype=np.int16)              # the model scores 0 for its first frames
            oww.reset()
            negf = get_reference_clip_features(np.concatenate([pad, neg]), oww, "hey_jarvis", threshold=0.0, N=1)
            word = {n: np.vstack([speech_feats(np.concatenate([pad, c]), oww) for c in clips[n]]) for n in WORD_STYLES}
            made = 0
            old = os.path.join(DATA, "wake_hey_pause.pkl")     # the dropped "Hey ... Jarvis" style
            if os.path.exists(old):
                os.remove(old)
            for name, label, _ in WAKE_STYLES:
                path = os.path.join(DATA, f"wake_{name}.pkl")
                peak, pos = 0.0, []
                for c in clips[name]:
                    c = np.concatenate([pad, c])
                    oww.reset()
                    peak = max([peak] + [oww.predict(c[i:i + 1280])["hey_jarvis"] for i in range(0, len(c) - 1280, 1280)])
                    if name not in WORD_STYLES:
                        oww.reset()
                        pos.append(get_reference_clip_features(c, oww, "hey_jarvis", threshold=WAKE_FLOOR, N=3))
                pos = word[name] if name in WORD_STYLES else np.vstack(pos)
                log(f"train: {label} peaks {peak:.2f} ({len(pos)} examples)")
                if len(pos) == 0:                              # never reached the floor / no speech heard: that way stays off
                    if os.path.exists(path):
                        os.remove(path)                        # an older check must not outlive this training
                    continue
                # "Hey" learns that your "Jarvis" is not it, and the other way round
                other = [word[o] for o in WORD_STYLES if o != name and name in WORD_STYLES]
                neg_all = np.vstack([negf] + other)
                check = train_verifier_model(np.vstack([pos, neg_all]), np.array([1] * len(pos) + [0] * len(neg_all)))
                with open(path + ".tmp", "wb") as f:
                    pickle.dump(check, f)
                os.replace(path + ".tmp", path)
                made += 1
            reply_line(f"Done. I learned {made} of the 3 ways." + ("" if made == 3 else " The log says which."), False)
        except Exception as e:
            log(f"wake training failed: {e!r}")
            problem("Wake word training failed")
        finally:
            S.set(state="idle", level=0.0)


def wake_way(score, held, mine, now, hey_until, need, easy, hard, gap):
    """Which way wakes him on this 80 ms moment (or None), and until when a "Hey" waits for "Jarvis".
    score: the normal "Hey Jarvis" score; held: it was >= need on the moment before too; mine: your trained checks'
    scores by style (only while speech is heard). "Hey" alone never wakes him."""
    if score >= need and held:                                 # W0, the backup: 2 moments in a row
        return "W0", 0.0
    if score >= WAKE_FLOOR and mine.get("hey_jarvis", 0.0) >= 0.5:   # HV: a soft "Hey Jarvis" in your voice
        return "HV", 0.0
    if now <= hey_until and mine.get("jarvis", 0.0) >= hard:   # HJ: your "Jarvis" within `gap` s of your "Hey"
        return "HJ", 0.0
    if easy > 0 and mine.get("hey", 0.0) >= easy and now > hey_until:
        hey_until = now + gap
    return None, hey_until


def wake_checks():
    """Your trained checks from Data\\wake_<style>.pkl; a missing or broken one leaves that way off."""
    import pickle
    checks = {}
    for name, _, _ in WAKE_STYLES:
        path = os.path.join(DATA, f"wake_{name}.pkl")
        if os.path.exists(path):
            try:
                with open(path, "rb") as f:
                    checks[name] = pickle.load(f)
            except Exception as e:
                log(f"wake: check {name} not loaded ({type(e).__name__})")
    return checks


def wake_loop():
    import numpy as np
    model, stream, warned = None, None, False
    off, mic_bad, best, minute = None, False, 0.0, time.time()   # why it is off (logged once per change); top score this minute
    heard_talk, no_vad = 0, False                              # 80 ms blocks heard while he speaks; "voice" without a VAD logged
    checks, last_score, hey_until = None, 0.0, 0.0             # your trained checks (loaded with the model); FR5 N1

    def load(**vad):
        import openwakeword
        from openwakeword.model import Model
        try:
            return Model(wakeword_models=["hey_jarvis"], inference_framework="onnx", **vad)
        except ImportError:
            raise
        except Exception:
            openwakeword.utils.download_models(model_names=["hey_jarvis"])   # first run: fetch the model
            return Model(wakeword_models=["hey_jarvis"], inference_framework="onnx", **vad)

    def drop():
        """Close the microphone and hand it back."""
        nonlocal stream
        if stream is not None:
            try:
                stream.close()
            except Exception:
                pass
            stream = None
            mic.release()
    while True:
        try:
            tier = hud_tier()
            why = ("turned off" if setting("JarvisWakeWord", "1") != "1" else "Jarvis off"
                   if setting("JarvisEnabled", "1") != "1" else f"HUD tier {tier}" if tier >= 3 else None)
            if why != off:
                off = why
                log(f"wake off: {why}" if why else "wake on")
            barge = barge_in()
            talking = busy.locked() and getattr(S, "state", "") == "speaking" and barge != "off"
            heard_talk = heard_talk if talking else 0
            if why or (busy.locked() and not talking):         # mic kept only while he speaks: listen() gets it at once
                drop()
                time.sleep(0.05 if barge != "off" and busy.locked() and not why else 0.5)   # catch him starting to speak
                continue
            if model is None:
                try:
                    model = load(vad_threshold=0.5)                # Silero VAD: no wake on music or a TV without speech
                except ImportError:
                    raise
                except Exception as e:
                    log(f"wake word: without the speech filter ({type(e).__name__})")
                    model = load()
                log("wake word ready - say 'Hey Jarvis'")
            if stream is None:
                import sounddevice as sd
                if not mic.acquire(timeout=0.5):               # a turn is recording
                    continue
                try:
                    stream = sd.InputStream(samplerate=16000, channels=1, dtype="int16", blocksize=1280, device=mic_device())
                    stream.start()
                    model.reset()
                    mic_bad = False
                    found = wake_checks() if getattr(model, "vad", None) is not None else {}   # re-read: a training may
                    if checks is None or set(found) != set(checks):                               # have just ended
                        log(f"wake: your checks: {', '.join(found) or 'none (train in Control Center)'}")
                    checks, last_score, hey_until = found, 0.0, 0.0
                except Exception as e:
                    if stream is None:
                        mic.release()
                    drop()
                    if not mic_bad:                            # once per outage, not every 5 s
                        mic_bad = True
                        problem(f"Wake word: no microphone ({str(e).splitlines()[0][:60]})", popup=False)
                    time.sleep(5)
                    continue
            data, _ = stream.read(1280)
            scores = model.predict(np.asarray(data[:, 0], dtype=np.int16))
            try:
                need = max(0.2, min(0.9, float(setting("JarvisWakeSensitivity", "0.5"))))
            except ValueError:
                need = 0.5
            best = max(best, max(scores.values()))
            if time.time() - minute >= 60:                     # a near miss shows what sensitivity would have worked
                if best >= 0.1:
                    log(f"wake: best {best:.2f} this minute")
                best, minute = 0.0, time.time()
            follow = None                                      # set when he is talked over: 0 = "Hey Jarvis", 1 = any voice
            if talking:
                heard_talk += 1
                if barge == "voice" and getattr(model, "vad", None) is None and not no_vad:
                    no_vad = True
                    log("barge-in: no speech filter loaded - only 'Hey Jarvis' stops him")
                vad = list(getattr(getattr(model, "vad", None), "prediction_buffer", []))[-7:]
                if barge == "voice" and heard_talk >= 7 and len(vad) == 7 and min(vad) >= 0.5:   # 0.56 s of speech
                    follow = 1                                 # a follow-up: "stop" ends it, anything else is a command
                need = min(need + 0.2, 0.95)                   # his own voice is in the room too
                if follow is None and time.time() < name_until[0]:   # he is saying "Jarvis" himself
                    continue
            score, held, last_score, way = max(scores.values()), last_score >= need, max(scores.values()), None
            if follow is None and talking and score >= need:   # over his voice: the normal score alone, as before
                follow = 0
            elif follow is None and not talking:
                mine = {}
                if checks and heard_speech(model):             # silence costs nothing
                    feats = model.preprocessor.get_features(model.model_inputs["hey_jarvis"])
                    mine = {n: float(c.predict_proba(feats)[0][-1]) for n, c in checks.items()}
                try:
                    easy, hard = (float(setting("JarvisWakeEasy", "0.5")), float(setting("JarvisWakeHard", "0.35")))
                    gap = float(setting("JarvisWakeGap", "5"))
                except ValueError:
                    easy, hard, gap = 0.5, 0.35, 5.0
                way, hey_until = wake_way(score, held, mine, time.time(), hey_until, need, easy, hard, gap)
                follow = 0 if way else None
            if follow is not None:
                last_score, hey_until = 0.0, 0.0
                log(f"wake word heard ({score:.2f}, {way})" if not talking else f"barge-in ({'voice' if follow else 'wake'})")
                if talking:
                    stop_now("barge-in")
                drop()
                model.reset()
                if talking:
                    threading.Thread(target=barge_turn, args=(follow,), daemon=True).start()
                else:
                    threading.Thread(target=turn, args=(hud_tier(), 0, True), daemon=True).start()
                time.sleep(1.0)                                # let the turn take the microphone
        except ImportError as e:
            if not warned:
                missing_mod = getattr(e, "name", None) or str(e)
                log(f"wake word: missing module - {e}")
                problem(f"Wake word needs {missing_mod} - run: py -m pip install openwakeword", popup=False)
                warned = True
            time.sleep(10)
        except Exception as e:
            drop()
            if model is None and not warned:                   # no model: shown in the Control Center, once
                warned = True
                problem(f"Wake word: the model didn't load ({type(e).__name__})", popup=False)
            else:
                log(f"wake word: {e!r}")
            time.sleep(5)


# ------------------------------------------------------------------ main loop: watch the command file
owner = False


def preload_ollama():
    """Load the chat model into memory at startup (it stays for JarvisKeepAlive minutes)."""
    if ensure_ollama():
        m = pick_model(0)
        if m:
            warm(m)


def preload_whisper():
    """Load the speech-recognition model at startup, so the first thing you say isn't waiting on it."""
    try:
        whisper()
    except Exception as e:
        log(f"whisper preload failed: {e!r}")


def unload_idle(now, since):
    """Free the speech models after JarvisIdleUnload minutes without a turn; they load again on the next one."""
    global _whisper
    try:
        mins = float(setting("JarvisIdleUnload", "10"))
    except ValueError:
        mins = 10.0
    if mins <= 0 or busy.locked() or now - since < mins * 60 or not (_whisper or _engines):
        return False
    _whisper = None
    _engines.clear()
    gc.collect()
    log(f"idle for {mins:g} min - speech models unloaded")
    return True


def main():
    global owner
    if not single_instance():
        return
    owner = True
    started = time.time()
    log(f"started ({RES}), Python {sys.version.split()[0]}")
    unduck()                                                   # a crash while he listened left the volume down
    miss = missing_packages()
    S.set(state="idle", level=0.0, err=("Setup needed - missing " + ", ".join(miss)) if miss else "")
    threading.Thread(target=preload_ollama, daemon=True).start()
    threading.Thread(target=stop_key_loop, daemon=True).start()
    if not miss:
        # one at a time, here: imported at once by the threads below, numpy half-loaded broke the others (wake word, voice)
        for name in ("numpy", "onnxruntime", "faster_whisper", "openwakeword", "sounddevice"):
            try:
                __import__(name)
            except Exception as e:
                log(f"start-up import of {name} failed ({type(e).__name__})")
        list_mics()
        threading.Thread(target=preload_whisper, daemon=True).start()
        threading.Thread(target=prepare_fillers, daemon=True).start()
        threading.Thread(target=wake_loop, daemon=True).start()
        threading.Thread(target=index_loop, daemon=True).start()
    last_mtime = os.path.getmtime(CMD_FILE) if os.path.exists(CMD_FILE) else 0
    beat, missing, checked, ringing = 0.0, 0, 0.0, None
    while True:
        try:
            time.sleep(0.1)
            now = time.time()
            if now - beat >= 2:
                beat = now
                S.set()                                        # heartbeat
                unload_idle(now, max(turn_id[0], started))
                if compact_due(now, max(turn_id[0], started)):  # M3: old talk into checked facts, once a day
                    threading.Thread(target=daily_memory, daemon=True).start()
                gpu_watch(now)
                missing = 0 if rainmeter_running() else missing + 1
                if missing >= 15:                              # Rainmeter gone for 30 s: quit
                    log("Rainmeter closed - exiting")
                    return
            if now - checked >= 1 and not (ringing and ringing.is_alive()):   # one alarm at a time
                checked = now
                if due_reminders(now):
                    ringing = threading.Thread(target=alarm, daemon=True)
                    ringing.start()
            try:
                mt = os.path.getmtime(CMD_FILE)
            except OSError:
                continue
            if mt == last_mtime:
                continue
            last_mtime = mt
            with open(CMD_FILE, "r", encoding="utf-8", errors="ignore") as f:
                parts = f.read().split()
            if len(parts) < 2 or abs(now - float(parts[1])) > 30:
                continue
            if parts[0] == "WAKE":
                tier = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 0
                threading.Thread(target=turn, args=(tier,), daemon=True).start()
            elif parts[0] == "CANCEL":
                stop_now("click")
            elif parts[0] == "REINDEX":
                _chroma.update(seen={}, last=0.0, failed=False)
                threading.Thread(target=chroma_index, kwargs={"force": True}, daemon=True).start()
                log("notes index: rebuilding")
            elif parts[0] == "FORGET":
                history.clear()
                log("conversation memory cleared")
            elif parts[0] == "TRAINWAKE":
                threading.Thread(target=train_wake, daemon=True).start()
            elif parts[0] == "QUIT":
                log("stopped from the Control Center")
                cancel.set()
                return
        except Exception as e:                                 # one bad read never kills the service
            log(f"main loop: {e!r}")
            time.sleep(1)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log(f"crashed: {e!r}")
        raise
    finally:
        if owner:                                              # tell the HUD we're gone (shows OFFLINE)
            try:
                with open(STATE_FILE, "w", encoding="utf-8") as f:
                    f.write("T 0\nSTATE idle\n")
            except OSError:
                pass
