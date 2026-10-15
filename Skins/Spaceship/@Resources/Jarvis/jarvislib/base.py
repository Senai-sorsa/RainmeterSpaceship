"""base: moved verbatim from jarvis.py (refactor). See JARVIS-Repair-Plan.txt, REFACTOR."""
import ctypes
import msvcrt
import os
import re
import sys
import threading
import time
from datetime import datetime


# without argv: @Resources is two folders above jarvislib (this was ".." while it lived in jarvis.py)
RES = (sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")).strip().strip('"')
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
        write_atomic(CONVO_FILE, "\n".join(lines) + "\n")
    except OSError:
        pass


def live(text):
    try:
        write_atomic(LIVE_FILE, f"J|{int(time.time())}|{re.sub(chr(10), ' ', text)}\n" if text else "")
    except OSError:
        pass


def write_atomic(path, text):
    """Write a whole file so a reader never sees half of it: a .tmp beside it, then one rename."""
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(text)
    os.replace(tmp, path)
