"""
JARVIS - voice assistant service for the Spaceship HUD.

Click the hologram -> chime -> it listens (stops when you stop talking) -> Whisper turns your speech into text
-> your local Ollama model answers, knowing what the HUD knows (time, calendar, Gmail, to-dos, open apps,
battery, memory, network) -> it speaks the answer sentence by sentence while the hologram moves with its voice.

Talks to the HUD through two small files in @Resources\\Data (no network port, so nothing else can trigger it):
  jarvis.txt      written here:   T <unix> | STATE idle|listening|thinking|speaking | LEVEL <0-1> | SAY | ERR |
                                  POP <n> open|close  (ask the HUD to open / close the conversation pop-up)
  jarvis_cmd.txt  written by HUD: WAKE <unix> <tier>  |  CANCEL <unix>  |  FORGET <unix>  |  QUIT <unix>
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
Skills: instant status phrases while searching, a whitelist of actions (risky ones need a spoken "yes"), and
guardrails - nothing outside the whitelist is ever executed.
Every problem is logged to Data\\jarvis.log, shown on the hologram (ERR) and added to the conversation pop-up.
"""
import ctypes
import gc
import json
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
from datetime import datetime

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


def context():
    lines = [f"Now: {datetime.now().strftime('%A %d %B %Y, %H:%M')}"]
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
    mail = re.search(r"^UNREAD (\d+)", read_kv("mail.txt"), re.M)
    if mail:
        lines.append(f"Unread Gmail: {mail.group(1)}")
    events = []
    for m in re.finditer(r"^E (\d+)\|(\d+)\|(\d)\|([^|]*)\|(.*)$", read_kv("calendar.txt"), re.M):
        start = datetime.fromtimestamp(int(m.group(1)))
        if int(m.group(2)) >= time.time():
            when = start.strftime("%a %d %b") + ("" if m.group(3) == "1" else start.strftime(" %H:%M"))
            events.append(f"{when} - {m.group(5)}" + (f" ({m.group(4)})" if m.group(4) else ""))
    if events:
        lines.append("Upcoming calendar events: " + "; ".join(events[:6]))
    apps = re.findall(r"^W (.+)$", read_kv("windows.txt"), re.M)
    if apps:
        lines.append("Open apps: " + ", ".join(a.replace(".exe", "") for a in apps[:20]))
    net = read_kv("net.txt")
    d, u = re.search(r"^DOWN (\d+)", net, re.M), re.search(r"^UP (\d+)", net, re.M)
    if d and u:
        lines.append(f"Network right now: {int(d.group(1)) * 8 / 1e6:.1f} Mbps down, {int(u.group(1)) * 8 / 1e6:.1f} Mbps up")
    st = settings()
    if st.get("LinkDownMbps"):
        lines.append(f"Internet speed (last test {st.get('LastSpeedTest', '?')}): {st.get('LinkDownMbps')} down / {st.get('LinkUpMbps', '?')} up Mbps")
    todo = st.get("ObsidianTodo", "").strip().strip('"')
    if todo and os.path.exists(todo):
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

    def pending():                                            # how many and when, not what: the text stays in its file
        items = load_reminders()
        return [f"Timers and reminders pending: {len(items)}, the next at {clock(items[0][0])}"] if items else []
    for line in HW_LINES:
        part(lambda: hw(*line))
    for fn in (cpu, card, sound, panel, disk, pending):
        part(fn)
    return "\n".join(lines)


SYSTEM = ("You are JARVIS, the AI built into the user's spaceship-style desktop HUD. You talk out loud, so answer in "
          "one to three short spoken sentences: no lists, markdown, emoji or code unless asked. {mood} "
          "Use the live HUD data below when it's relevant; if something isn't in it, say you don't "
          "have that rather than guessing.\n")
MOODS = {"proper": "Be calm, precise and a little dry.",       # JarvisPersonality: how the model words its answers
         "playful": "Be funny and quick. When the user jokes or banters, dark humor included, answer in the same spirit. "
                    "When they ask a real question, answer it helpfully first, then joke if it fits. "
                    "You are on their side: back them up. Never joke about a failed action.",
         "brief": "Answer in one short sentence. No small talk."}


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


def system_prompt():
    me = about_me()
    out = SYSTEM.replace("{mood}", MOODS.get(setting("JarvisPersonality", "playful").strip().lower(), MOODS["playful"]))
    if me:
        out += ("\nABOUT THE USER (from their own note - use it to personalise answers; don't recite it unless "
                "asked):\n" + me + "\n")
    return out + "\nLIVE HUD DATA:\n" + context()


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


def chat_stream(model, messages):
    opts = {"num_ctx": ctx_tokens(), "temperature": 0.5, "num_predict": 160}
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


def whisper():
    global _whisper
    if _whisper is None:
        from faster_whisper import WhisperModel
        size = setting("JarvisWhisper", "base.en")
        dev = setting("JarvisWhisperDevice", "auto").lower()
        why = f"JarvisWhisperDevice={dev}"
        if dev in ("auto", "cuda"):
            try:
                # the pip nvidia-* wheels keep cuBLAS / cuDNN in their own bin folders, which Windows does not search
                import glob
                for d in [d for p in sys.path for d in glob.glob(os.path.join(p, "nvidia", "*", "bin"))]:
                    if d not in os.environ["PATH"]:
                        os.add_dll_directory(d)
                        os.environ["PATH"] = d + os.pathsep + os.environ["PATH"]
                _whisper =WhisperModel(size, device="cuda", compute_type="float16")
                log(f"whisper {size} on GPU")
                return _whisper
            except Exception as e:
                why = e
        _whisper = WhisperModel(size, device="cpu", compute_type="int8", cpu_threads=cpu_threads())
        cpu_in_use("speech recognition", why)
    return _whisper


def transcribe(audio):
    if audio is None:
        return ""
    try:
        segs, _ = whisper().transcribe(audio, beam_size=1, language="en", vad_filter=False)
        return " ".join(s.text for s in segs).strip()
    except Exception as e:
        if "cuda" in str(e).lower() or "cublas" in str(e).lower() or "cudnn" in str(e).lower():
            global _whisper
            cpu_in_use("speech recognition", e)
            try:
                from faster_whisper import WhisperModel
                _whisper = WhisperModel(setting("JarvisWhisper", "base.en"), device="cpu", compute_type="int8",
                                        cpu_threads=cpu_threads())
                segs, _ = _whisper.transcribe(audio, beam_size=1, language="en", vad_filter=False)
                return " ".join(s.text for s in segs).strip()
            except Exception as cpu_e:
                log(f"whisper CPU fallback also failed: {cpu_e}")
                raise cpu_e
        raise


def listen(wait=3):
    """Record until you stop talking: waits up to 6 s for speech, then stops after JarvisSilence seconds of quiet
    (default 1 s; raise it if he cuts you off mid-sentence), max 25 s."""
    if not mic.acquire(timeout=wait):                          # the wake word lets go within a second of a turn starting
        raise RuntimeError("The microphone is busy - try again")
    try:
        return _listen()
    finally:
        mic.release()


def _listen():
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
        stream = sd.InputStream(samplerate=rate, channels=1, dtype="float32", blocksize=block)
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
                if not started and waited > 200:
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
_broken = set()             # voice files that failed to load (not retried until the service restarts)
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
        # our own session, to cap its threads: measured 25% of the machine instead of 50%, 0.6 s slower per sentence
        # shortcut: CPU only, onnxruntime-gpu 1.31 wants CUDA 13 while Whisper (ctranslate2) loads CUDA 12, and both
        # ship a cudnn64_9.dll (not tried together); move the voice to the GPU once the two agree on a CUDA version
        opts = rt.SessionOptions()
        opts.intra_op_num_threads = cpu_threads()
        sess = rt.InferenceSession(voice_path, opts, providers=["CPUExecutionProvider"])
        eng = _engines[voice_path] = Kokoro.from_session(sess, bins[-1])
        log(f"kokoro loaded ({os.path.basename(voice_path)}, {os.path.basename(bins[-1])}), {cpu_threads()} threads")
        cpu_in_use("the voice", "no GPU build of onnxruntime here")
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
    samples, rate = eng.create(text, voice=name, speed=speed, lang=lang)
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
        subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", ps], input=text.encode("utf-8"),
                       creationflags=NO_WINDOW, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=60)
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
    if voice and voice not in _broken:
        if not os.path.exists(voice):
            log(f"voice file not found: {voice} - using the Windows voice")
            problem("Voice file not found - using the Windows voice (check JarvisVoice)", popup=False)
            _broken.add(voice)
        elif re.search(r"kokoro.*v0[._]", os.path.basename(voice).lower()):
            msg = ("Kokoro v0.19 isn't supported - put kokoro-v1.0.onnx and voices-v1.0.bin in "
                   + os.path.dirname(voice))
            log(msg)
            problem(msg, popup=False)
            _broken.add(voice)
        else:
            try:
                if "kokoro" in os.path.basename(voice).lower():
                    out = _kokoro(voice, text)
                else:
                    out = _piper(voice, text)
                if out is not None:
                    return out
            except Exception as e:
                problem(f"Voice failed - using the Windows voice ({str(e)[:60]})", popup=False)   # once: it is not retried
                _broken.add(voice)
                _engines.pop(voice, None)
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
        if item is None:
            break
        audio, said = item
        spoken = (spoken + " " + said).strip()
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


def route(text):
    """Map what you said to (kind, action, target, confirmation prompt). kind: chat | notes | apps | act | guard | say |
    remind (action = list / cancel / set, target = its details)."""
    t = text.strip().lower().rstrip(".!?")
    if DANGER.search(t):
        return ("guard", None, None, None)
    # actions only for commands ("lock my computer", "jarvis, could you open chrome"), never for questions about them
    # ("should I restart my computer?", "how do I close a for loop?")
    cmd = re.sub(r"^(hey |ok |okay )?(jarvis[, ]+)?(please |can you |could you |would you |will you )?(please )?", "", t).strip()
    if text.strip().endswith("?") and cmd == t:
        cmd = ""
    op = reminder_cmd(t, cmd, time.time())
    if op:
        return ("remind", op[0], op[1:], None)
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
    # shortcut: the volume number must be digits (speech recognition writes "30", not "thirty"); add words if it does not
    m = re.match(r"(?:set |turn |change |put )?(?:the )?volume (?:to |at )?(\d{1,3})(?: ?%| percent)?$", cmd)
    if m:
        if int(m.group(1)) > 100:
            return ("say", None, None, "I can set it between 0 and 100.")
        return ("act", "volume", ("set", int(m.group(1))), None)
    m = re.match(r"(?:(?:turn |make )?(?:it |(?:the )?(?:volume|sound|music) )(up|down|louder|quieter)|"
                 r"turn (up|down) (?:it|the (?:volume|sound|music))|(louder|quieter))$", cmd)
    if m:
        return ("act", "volume", ("step", 10 if (m.group(1) or m.group(2) or m.group(3)) in ("up", "louder") else -10), None)
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
    return ("chat", None, None, None)


def run_action(action, target):
    try:
        ACTIONS[action](target)
        log(f"action: {action} {target if target else ''}")
        return True
    except Exception as e:
        log(f"action {action} failed: {e!r}")
        problem(f"Couldn't {action}: {str(e)[:80]}")
        return False


def reply_line(text, quiet):
    """Speak (or show) a short fixed reply and log it."""
    convo_add("J", text)
    filler_done()
    if quiet:
        S.set(pop="open")
        live(text)
        time.sleep(min(3.0, 0.06 * len(text)))
        live("")
    else:
        speak_all([text])


def hear():
    """Listen once more inside a turn and return the words ("" for silence or a click)."""
    audio = listen() if not cancel.is_set() else None
    return transcribe(audio) if audio is not None else ""


# ------------------------------------------------------------------ timers and reminders
# "remind me to cook in 20 minutes", "set a timer for 10 minutes", "what reminders do I have", "cancel the timer".
# All of it is read by the code below, never by the model. They are kept in Data\jarvis_reminders.txt (so they
# survive a restart) and ring only while JARVIS runs: a ding and the line, repeated until a stop word or a click.
REMIND_FILE = os.path.join(DATA, "jarvis_reminders.txt")      # due|created|kind|label  (kind: reminder | timer)
STOP_WORDS = re.compile(r"\b(stop|shush|shh+|shut ?up|quiet|enough|okay|ok|thanks|thank you|dismiss)\b", re.I)
RINGS = 10                                                    # each is a ding, the line, and up to 6 s of listening
ONES = ("zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen "
        "seventeen eighteen nineteen").split()
TENS = {"twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60}
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
    s = re.sub(r"\b(an?|one) hour and a half\b", "90 minutes", s.strip()).replace("half an hour", "30 minutes")
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
    """'in 20 minutes', 'at 6:30 pm', 'at 18:30', 'at 7' -> the time it is due, or None. A clock time is its next
    occurrence; with no am / pm, 'at 7' is whichever 7 o'clock comes first."""
    # shortcut: clock times must be digits ("at 7", not "at seven"), which is how speech recognition writes them
    s = s.strip()
    if s.startswith("in "):
        d = duration(s[3:])
        return None if d is None else now + d
    m = re.fullmatch(r"at (\d{1,2})(?:[: .]?(\d{2}))? ?(a\.?m|p\.?m)?\.?", s)
    if not m:
        return None
    hour, minute, half = int(m.group(1)), int(m.group(2) or 0), (m.group(3) or "").replace(".", "")
    if minute > 59 or hour > 23 or (half and not 1 <= hour <= 12):
        return None
    hours = [hour % 12 + (12 if half == "pm" else 0)] if half else [hour, (hour + 12) % 24] if 1 <= hour <= 12 else [hour]
    day = datetime.fromtimestamp(now).replace(minute=minute, second=0, microsecond=0)
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


def split_time(rest, now):
    """'to cook in 20 minutes' or 'in 20 minutes to cook' -> (due, label, the time as said). No time in it: due is None."""
    for m in re.finditer(r"\b(?:in|at) ", rest):               # the time comes last
        due = when(rest[m.start():], now)
        if due is not None:
            return due, rest[:m.start()].strip(), rest[m.start():]
    for m in re.finditer(r" (?=(?:to|about|that|for) )", rest):   # the time comes first
        due = when(rest[:m.start()], now)
        if due is not None:
            return due, rest[m.end():].strip(), rest[:m.start()]
    return None, rest.strip(), ""


def reminder_cmd(t, cmd, now):
    """A timer or reminder command -> ("list", kind) | ("cancel", kind, words) | ("set", kind, due, label, time as said);
    anything else -> None. due is None when no time was heard (he then asks)."""
    m = re.match(r"(?:(?:what|which) (?:are )?(?:my |the )?|(?:list|show|read)(?: me| out)? (?:all )?(?:my |the )?|"
                 r"do i have (?:any )?|how (?:much time|long) (?:is |do i have )?left on (?:my |the )?)(reminder|timer)s?"
                 r"(?: (?:do i have|have i (?:got|set)|are (?:set|there|left|pending|running)).*)?$", t)
    if m:
        return ("list", m.group(1))
    m = re.match(r"(?:cancel|delete|remove|clear|stop|forget) (?:(?:all|every|of|the|my|that) )*(?:(.+) )?(reminder|timer)s?"
                 r"(?: (?:to|about|for) (.+))?$", cmd)
    if m:
        return ("cancel", m.group(2), f"{m.group(1) or ''} {m.group(3) or ''}".strip())
    m = re.match(r"(?:remind me|(?:set|add) (?:a |another )?reminder)(?: (.+))?$", cmd)
    if m:
        if re.match(r"(what|who|how|why|where|when|which|whether|if) ", m.group(1) or ""):
            return None                                        # "remind me what the capital is": a question for the model
        due, label, said = split_time(m.group(1) or "", now)
        if label and not re.match(r"(to|about|that) ", label):
            label = "about " + re.sub(r"^(for|of) ", "", label)
        return ("set", "reminder", due, re.sub(r"\bmy\b", "your", label), said)
    m = re.match(r"(set |start |create |put on |give me )?(?:a |an |another |the )?(?:(.+?)[ -])?timer(?: (?:for|of) (.+))?$", cmd)
    if not m:
        return None
    verb, before, after = m.groups()
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
    return f"{label or 'a reminder'} at {clock(due, now)}"


def ring_line(r, now):
    """What he says when it is due: your own words back ("Time to cook."), not something the model wrote."""
    due, created, kind, label = r
    if kind == "timer":
        line = f"Your timer for {label} is done." if label else f"Your {span(due - created, '')} timer is done."
    elif label.startswith("to "):
        line = f"Time {label}."
    else:
        line = f"Reminder: {label[5:]}." if label.startswith("that ") else f"Reminder {label}." if label else "This is your reminder."
    if now - due > 120:                                        # the PC slept, or JARVIS was not running
        return f"Missed {kind} from {clock(due, now)}: {line[0].lower()}{line[1:]}"
    return line


def remind_reply(op, args, quiet):
    """Carry out a list / cancel / set and return what to say. Runs inside a turn, so there is one writer at a time."""
    now, kind = time.time(), args[0]
    try:
        items = load_reminders()
    except (OSError, ValueError):
        return "I can't read the reminders file, so I left it alone."
    if op == "list":
        mine = [describe(r, now) for r in items if r[2] == kind]
        return f"You have {len(mine)} {kind}{'s' if len(mine) != 1 else ''}: {'; '.join(mine)}." if mine else f"You have no {kind}s."
    if op == "cancel":
        # shortcut: a word matches on its first four letters ("cooking" finds "to cook"); fine for a list of 20
        words = [w for w in args[1].split() if w not in ("the", "my", "a", "an", "one", "to", "about", "for")]
        gone = [r for r in items if r[2] == kind and all(w[:4] in f"{r[3]} {span(r[0] - r[1], '')}" for w in words)]
        if not gone:
            return f"I don't see a {kind} like that."
        save_reminders([r for r in items if r not in gone])
        log(f"reminder cancelled ({len(gone)})")
        return "Cancelled: " + "; ".join(describe(r, now) for r in gone) + "."
    _, due, label, said = args
    if due is None:                                            # no time heard: ask once and listen, like a confirmation
        reply_line("When?" if kind == "reminder" else "How long?", quiet)
        S.set(state="listening", level=0.0)
        answer = hear()
        if answer:
            convo_add("U", answer)
        now, answer = time.time(), answer.strip().lower().rstrip(".!?")
        for said in (answer, "in " + answer, "at " + answer):
            due = when(said, now)
            if due is not None:
                break
        else:
            return "I didn't catch the time."
    if not 5 <= due - now <= 7 * 86400:
        return "I can set that from 5 seconds to 7 days ahead."
    if len(items) >= 20:
        return "You already have 20 pending. Cancel one first."
    save_reminders(items + [(due, now, kind, re.sub(r"[\s|]+", " ", label))])
    log(f"reminder set ({kind}, {due - now:.0f}s ahead)")
    if kind == "timer":
        return f"Timer set for {span(due - now)}" + (f", for {label}." if label else ".")
    return f"I'll remind you {label} ".replace("  ", " ") + (f"in {span(due - now)}." if said.startswith("in ") else f"at {clock(due, now)}.")


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
            save_reminders(items[len(due):])                   # gone before it rings: a crash here cannot ring forever
            log(f"reminder fired ({len(due)})")
            log(f"timing: due -> ring {now - due[-1][0]:.1f}s")
            text = " ".join(ring_line(r, now) for r in due)
            convo_add("J", text)
            audio = None if muted() or hud_tier() >= 3 else synth_audio(text)     # made once, replayed each round
            if audio is None:                                  # muted, STEALTH or no voice: shown like a muted reply
                if setting("JarvisMutedPopup", "1") == "1":
                    S.set(pop="open")
                return
            for _ in range(RINGS):
                S.set(state="speaking", say=text)
                play_samples(*ding())
                if not cancel.is_set():
                    play_samples(*audio)
                S.set(state="listening", level=0.0)
                if cancel.is_set() or STOP_WORDS.search(hear()):   # what is heard here is matched and dropped, never kept
                    convo_add("J", "(stopped)")
                    return
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
                    with open(path, "r", encoding="utf-8", errors="ignore") as f:
                        parts = _chunks(f.read(300_000))
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
    while True:
        try:
            chroma_index(force=True)
        except Exception as e:
            log(f"index loop: {e!r}")
        time.sleep(600)


# ------------------------------------------------------------------ one conversation turn
history = []          # recent turns, forgotten after 10 minutes
last_turn = 0.0


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


def turn(tier):
    global history, last_turn
    if not busy.acquire(blocking=False):
        return
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
        S.set(state="listening", level=0.0, err="")
        if not ensure_ollama():
            problem("Ollama isn't running or installed - run Control Center > JARVIS > SETUP")
            return
        model = pick_model(tier)
        if not model:
            want = setting("JarvisModel", "llama3.1:8b")
            problem(f"Model {want} is not downloaded (Control Center > JARVIS > MODEL, or: ollama pull {want})")
            return
        warm(model)
        threading.Thread(target=prepare_fillers, daemon=True).start()   # cheap if nothing changed
        time.sleep(chime())                                    # don't record the chime
        log(f"timing: click -> listening {time.time() - t_click:.2f}s")
        t_listen = time.time()
        hud = []
        reading = threading.Thread(target=lambda: hud.append(sensors()), daemon=True)
        reading.start()                                        # read while you speak, so it costs the reply nothing
        audio = listen()
        if audio is None or cancel.is_set():
            return
        t_spoke = time.time()
        log(f"timing: listening -> end of speech {t_spoke - t_listen:.2f}s")
        S.set(state="thinking", level=0.0)
        try:
            text = transcribe(audio)
        except ImportError:
            problem("Speech recognition isn't installed - run Control Center > JARVIS > SETUP")
            return
        log(f"timing: end of speech -> text {time.time() - t_spoke:.2f}s")
        log(f"you: {text}")
        if not text or cancel.is_set():
            return
        convo_add("U", text)
        quiet = muted()
        S.set(err="")
        # "show me what you've said" / "close the log": handled here, no model needed
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
        kind, action, target, prompt = route(text)
        extra = ""
        if kind == "say":
            reply_line(prompt, quiet)
            return
        if kind == "remind":
            reply_line(remind_reply(action, target, quiet), quiet)
            return
        if kind == "act":
            if prompt is None:                                 # harmless: do it now
                ok = run_action(action, target)
                if action in ("mute", "unmute", "volume"):     # the reply follows the new state: shown if now silent
                    quiet = muted()
                reply_line(done_line(action, target) if ok else "That didn't work.", quiet)
                return
            # two-phase: stage it, ask, and listen for the answer (15 s) without another click
            pending = {"action": action, "target": target}
            reply_line(prompt, quiet)
            pending["expires"] = time.time() + 15              # counted from the end of the spoken prompt
            S.set(state="listening", level=0.0)
            answer = hear()
            if answer:
                convo_add("U", answer)
            if confirmed(pending, answer, time.time()) and not cancel.is_set():
                ok = run_action(pending["action"], pending["target"])
                reply_line("Done." if ok else "That didn't work.", quiet)
            else:
                log(f"action {action} not confirmed ({answer!r})")
                reply_line("Cancelled.", quiet)
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
        if time.time() - last_turn > 600:
            history = []
        reading.join(1.5)                                      # a stuck sensor never holds the reply: its lines are left out
        messages = fit_context([{"role": "system", "content": system_prompt() + "".join("\n" + h for h in hud if h) + extra}],
                               history[-8:], {"role": "user", "content": text})
        collected = []
        stream = chat_stream(model, messages)
        if quiet and setting("JarvisMutedPopup", "1") == "1":
            say_text_only(sentences_from(stream, collected), collected)
        else:
            speak_all(sentences_from(stream, collected))
        reply = "".join(collected).strip()
        ollama_on_cpu(model)
        log(f"timing: end of speech -> reply done {time.time() - t_spoke:.2f}s ({model})")
        if not reply and not cancel.is_set():
            problem(f"{model} gave no answer - try again, or pick another model in Control Center > JARVIS")
            return
        log(f"jarvis: {reply}")
        convo_add("J", reply)
        history += [{"role": "user", "content": text}, {"role": "assistant", "content": reply}]
        last_turn = time.time()
        S.set(say=reply)
    except urllib.error.URLError as e:
        problem(f"Lost the connection to Ollama ({e.reason}) - is it still running?")
        live("")
    except Exception as e:
        log(f"turn failed: {e!r}")
        problem(str(e).split("\n")[0][:110])
        live("")
    finally:
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


def wake_loop():
    import numpy as np
    model, stream, warned = None, None, False

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
            want = setting("JarvisWakeWord", "1") == "1" and setting("JarvisEnabled", "1") == "1" and hud_tier() < 3
            if not want or busy.locked():
                drop()
                time.sleep(0.5)
                continue
            if model is None:
                import openwakeword
                from openwakeword.model import Model
                try:
                    model = Model(wakeword_models=["hey_jarvis"], inference_framework="onnx")
                except Exception:
                    openwakeword.utils.download_models(model_names=["hey_jarvis"])   # first run: fetch the model
                    model = Model(wakeword_models=["hey_jarvis"], inference_framework="onnx")
                log("wake word ready - say 'Hey Jarvis'")
            if stream is None:
                import sounddevice as sd
                if not mic.acquire(timeout=0.5):               # a turn is recording
                    continue
                try:
                    stream = sd.InputStream(samplerate=16000, channels=1, dtype="int16", blocksize=1280)
                    stream.start()
                    model.reset()
                except Exception as e:
                    if stream is None:
                        mic.release()
                    drop()
                    log(f"wake word: couldn't open microphone - {e}")
                    time.sleep(5)
                    continue
            data, _ = stream.read(1280)
            scores = model.predict(np.asarray(data[:, 0], dtype=np.int16))
            try:
                need = max(0.2, min(0.9, float(setting("JarvisWakeSensitivity", "0.5"))))
            except ValueError:
                need = 0.5
            if max(scores.values()) >= need:
                log(f"wake word heard ({max(scores.values()):.2f})")
                drop()
                model.reset()
                threading.Thread(target=turn, args=(hud_tier(),), daemon=True).start()
                time.sleep(1.0)                                # let the turn take the microphone
        except ImportError as e:
            if not warned:
                missing_mod = getattr(e, "name", None) or str(e)
                log(f"wake word: missing module - {e}")
                problem(f"Wake word needs {missing_mod} - run: py -m pip install openwakeword", popup=False)
                warned = True
            time.sleep(10)
        except Exception as e:
            log(f"wake word: {e!r}")
            drop()
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
    miss = missing_packages()
    S.set(state="idle", level=0.0, err=("Setup needed - missing " + ", ".join(miss)) if miss else "")
    threading.Thread(target=preload_ollama, daemon=True).start()
    if not miss:
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
                cancel.set()
            elif parts[0] == "REINDEX":
                _chroma.update(seen={}, last=0.0, failed=False)
                threading.Thread(target=chroma_index, kwargs={"force": True}, daemon=True).start()
                log("notes index: rebuilding")
            elif parts[0] == "FORGET":
                history.clear()
                log("conversation memory cleared")
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
