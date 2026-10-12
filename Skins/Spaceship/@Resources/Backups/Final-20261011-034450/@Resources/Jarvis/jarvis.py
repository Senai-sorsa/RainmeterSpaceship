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
Voices: Kokoro-82M (pip install kokoro-onnx + kokoro-v1.0*.onnx and voices-v1.0.bin - Setup downloads them), a Piper
voice (.onnx), or the built-in Windows voice as the always-available fallback.
Settings (Settings.inc, all adjustable in Control Center > JARVIS): JarvisModel, JarvisModelFast (used while the HUD
is on its LITE / LOW tiers, i.e. the GPU is busy), JarvisWhisper, JarvisWhisperDevice, JarvisVoice, JarvisVoiceRate,
JarvisKokoroVoice, JarvisChime, JarvisMutedPopup, JarvisKeepAlive, JarvisContext (model memory in tokens),
JarvisSilence (seconds of silence before he answers), ObsidianTodo (open to-dos), JarvisProfile ("about me" note),
JarvisVault (Obsidian vault folder for "search my notes" - default: the to-do note's folder).
JarvisSmartSearch (1 = ChromaDB meaning-based note search, falls back to keywords), JarvisWakeWord (1 = say "Hey Jarvis" instead of clicking), JarvisWakeSensitivity (0.2-0.9, lower = more sensitive).
Skills: instant status phrases while searching, a whitelist of actions (risky ones need a spoken "yes"), and
guardrails - nothing outside the whitelist is ever executed.
Every problem is logged to Data\\jarvis.log, shown on the hologram (ERR) and added to the conversation pop-up.
"""
import ctypes
import json
import msvcrt
import os
import queue
import re
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
    except OSError:
        pass
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
                os.replace(tmp, STATE_FILE)
            except OSError:
                pass


S = State()
cancel = threading.Event()
busy = threading.Lock()


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
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
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


SYSTEM = ("You are JARVIS, the AI built into the user's spaceship-style desktop HUD. You talk out loud, so answer in "
          "one to three short spoken sentences: no lists, markdown, emoji or code unless asked. Be calm, precise and "
          "a little dry. Use the live HUD data below when it's relevant; if something isn't in it, say you don't "
          "have that rather than guessing.\n")


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
    out = SYSTEM
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
    try:
        http_json("/api/tags", timeout=2)
        return True
    except Exception:
        pass
    try:
        subprocess.Popen(["ollama", "serve"], creationflags=NO_WINDOW, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except OSError:
        return False
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
    if not names:
        return None
    for n in (want, want + ":latest"):
        if n in names:
            return n
    log(f"model {want} not downloaded - using {names[0]} (Control Center > JARVIS > MODEL, or: ollama pull {want})")
    return names[0]


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


def chat_stream(model, messages):
    body = json.dumps({"model": model, "messages": messages, "stream": True, "keep_alive": keep_alive(),
                       "options": {"num_ctx": ctx_tokens(), "temperature": 0.5}}).encode()
    req = urllib.request.Request(OLLAMA + "/api/chat", data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        for raw in r:
            if cancel.is_set():
                return
            raw = raw.strip()
            if not raw:
                continue
            obj = json.loads(raw)
            piece = obj.get("message", {}).get("content", "")
            if piece:
                yield piece
            if obj.get("done"):
                return


# ------------------------------------------------------------------ speech to text
_whisper = None


def whisper():
    global _whisper
    if _whisper is None:
        from faster_whisper import WhisperModel
        size = setting("JarvisWhisper", "base.en")
        dev = setting("JarvisWhisperDevice", "auto").lower()
        if dev in ("auto", "cuda"):
            try:
                _whisper = WhisperModel(size, device="cuda", compute_type="float16")
                log(f"whisper {size} on GPU")
                return _whisper
            except Exception as e:
                if dev == "cuda":
                    log(f"whisper GPU failed ({e}) - using CPU")
        _whisper = WhisperModel(size, device="cpu", compute_type="int8")
        log(f"whisper {size} on CPU")
    return _whisper


def transcribe(audio):
    try:
        segs, _ = whisper().transcribe(audio, beam_size=1, language="en", vad_filter=False)
        return " ".join(s.text for s in segs).strip()
    except Exception as e:
        if "cuda" in str(e).lower() or "cublas" in str(e).lower() or "cudnn" in str(e).lower():
            global _whisper
            log(f"whisper GPU error ({e}) - switching to CPU")
            from faster_whisper import WhisperModel
            _whisper = WhisperModel(setting("JarvisWhisper", "base.en"), device="cpu", compute_type="int8")
            segs, _ = _whisper.transcribe(audio, beam_size=1, language="en", vad_filter=False)
            return " ".join(s.text for s in segs).strip()
        raise


def listen():
    """Record until you stop talking: waits up to 6 s for speech, then stops after JarvisSilence seconds of quiet
    (default 3 s - room to pause mid-sentence; lower it for snappier answers), max 25 s."""
    import numpy as np
    import sounddevice as sd
    rate, block = 16000, 480                     # 30 ms blocks
    frames, started, silent, waited = [], False, 0, 0
    floor = None
    try:
        quiet_blocks = int(max(0.5, min(6.0, float(setting("JarvisSilence", "3")))) / 0.03)
    except ValueError:
        quiet_blocks = 100
    try:
        stream_cm = sd.InputStream(samplerate=rate, channels=1, dtype="float32", blocksize=block)
    except Exception as e:
        raise RuntimeError("No microphone available (" + str(e).split("\n")[0][:60] + ") - check Windows Settings > Privacy > Microphone")
    with stream_cm as stream:
        t0 = time.time()
        while not cancel.is_set():
            data, _ = stream.read(block)
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
    if cancel.is_set() or not started:
        return None
    return np.concatenate(frames)


# ------------------------------------------------------------------ text to speech
# Engines, chosen by JarvisVoice: a kokoro-*.onnx file -> Kokoro-82M (natural, runs on the CPU), any other .onnx ->
# Piper, blank -> the built-in Windows voice. If an engine fails, that sentence falls back to the Windows voice, and
# if even that fails the words go to the pop-up - he never just goes silent.
_engines = {}               # loaded voices, by path
_broken = set()             # voice files that failed to load (not retried until the service restarts)
KOKORO_VOICES = ("bm_george", "bm_lewis", "bm_fable", "bm_daniel", "bf_emma", "am_michael", "am_adam", "af_heart")


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
        eng = _engines[voice_path] = Kokoro(voice_path, bins[-1])
        log(f"kokoro loaded ({os.path.basename(voice_path)}, {os.path.basename(bins[-1])})")
    name = setting("JarvisKokoroVoice", "bm_george")
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
    ps = ("Add-Type -AssemblyName System.Speech; $s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
          "$v = $s.GetInstalledVoices() | Where-Object { $_.VoiceInfo.Culture.Name -eq 'en-GB' } | Select-Object -First 1; "
          f"if ($v) {{ $s.SelectVoice($v.VoiceInfo.Name) }}; $s.Rate = {voice_rate()}; "
          f"$s.SetOutputToWaveFile('{path}'); $s.Speak([Console]::In.ReadToEnd()); $s.Dispose()")
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
            os.remove(path)
        except OSError:
            pass


def synth_audio(text):
    """Text -> (samples float32, sample_rate), or None if no voice could speak it."""
    voice = setting("JarvisVoice", "").strip().strip('"')
    if voice and voice not in _broken:
        if not os.path.exists(voice):
            log(f"voice file not found: {voice} - using the Windows voice")
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
                log(f"voice failed ({e}) - using the Windows voice")
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
    failed = []

    def producer():
        for s in sentences:
            if cancel.is_set():
                break
            clean = re.sub(r"[*_#`>\[\]]", "", s).strip()
            if not clean:
                continue
            try:
                audio = synth_audio(clean)
            except Exception as e:
                log(f"speech failed: {e}")
                audio = None
            if audio is None:
                failed.append(clean)
            q.put((audio, clean))
        q.put(None)

    threading.Thread(target=producer, daemon=True).start()
    filler_done()                                              # never talk over a status phrase
    first, spoken, shown = True, "", False
    while True:
        item = q.get()
        if item is None:
            break
        audio, said = item
        spoken = (spoken + " " + said).strip()
        if first:
            S.set(state="speaking")
            first = False
        # muted mid-reply, or the voice failed: show the words instead
        if (muted() and setting("JarvisMutedPopup", "1") == "1") or audio is None:
            if not shown:
                S.set(pop="open")
                shown = True
            live(spoken)
        if audio is None:
            time.sleep(min(3.0, 0.06 * len(said)))            # reading time instead of speaking time
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
    live("")
    if failed:
        problem("Couldn't speak (voice failed) - the reply is in the log", popup=False)


def sentences_from(stream, collected):
    buf = ""
    for piece in stream:
        buf += piece
        collected.append(piece)
        while True:
            m = re.search(r"(.+?[.!?])(\s+|$)", buf)
            if not m or (m.end() == len(buf) and not buf.endswith((" ", "\n"))):
                break
            yield m.group(1)
            buf = buf[m.end():]
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
    return os.path.dirname(todo) if todo and os.path.exists(todo) else ""


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
    out = []
    try:
        with open(os.path.join(DATA, "StartApps.txt"), "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                if "|" in line:
                    name, appid = line.rstrip("\n").split("|", 1)
                    out.append((name.strip(), appid.strip()))
    except OSError:
        pass
    return out


def best_app(name):
    """The installed app whose name best matches what you said."""
    want = re.sub(r"[^a-z0-9 ]", "", name.lower()).strip()
    if not want:
        return None
    best, score = None, 0
    for disp, appid in start_apps():
        d = disp.lower()
        if any(x in d for x in ("uninstall", "help", "readme", "documentation")):
            continue
        sc = 3 if d == want else (2 if d.startswith(want) else (1 if want in d else 0))
        if sc > score or (sc == score and sc and best and len(disp) < len(best[0])):
            best, score = (disp, appid), sc
    return best if score else None


def running_window(name):
    """An open app (from the HUD's window list) whose exe matches what you said, e.g. 'chrome' -> chrome.exe."""
    want = re.sub(r"[^a-z0-9]", "", name.lower())
    for exe in re.findall(r"^W (.+)$", read_kv("windows.txt"), re.M):
        if want and want in re.sub(r"[^a-z0-9]", "", exe.lower()):
            return exe
    return None


def press_key(vk):
    ctypes.windll.user32.keybd_event(vk, 0, 0, 0)
    ctypes.windll.user32.keybd_event(vk, 0, 2, 0)


# action handlers: (description for the confirmation, function). Only these can ever run.
def act_open(app):
    os.startfile("shell:AppsFolder\\" + app[1]) if not os.path.isabs(app[1]) else os.startfile(app[1])


def act_close(exe):
    subprocess.run(["taskkill", "/IM", exe], creationflags=NO_WINDOW, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


ACTIONS = {
    "lock": lambda _: ctypes.windll.user32.LockWorkStation(),
    "sleep": lambda _: subprocess.run(["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"], creationflags=NO_WINDOW),
    "restart": lambda _: subprocess.run(["shutdown", "/r", "/t", "10"], creationflags=NO_WINDOW),
    "shutdown": lambda _: subprocess.run(["shutdown", "/s", "/t", "10"], creationflags=NO_WINDOW),
    "close": act_close,
    "open": act_open,
    "mute": lambda _: press_key(0xAD),           # VK_VOLUME_MUTE toggles
}

YES = re.compile(r"^\W*(yes|yeah|yep|yup|sure|confirm(ed)?|do it|go ahead|proceed|affirmative|ok(ay)?|please do)\b", re.I)
DANGER = re.compile(r"self[- ]?destruct|system ?32|format (my|the|c)|wipe (my|the)|delete (all|every|my files|windows)|rm -rf|"
                    r"disable (the )?(antivirus|defender|firewall)|hack|brick|destroy|nuke|blow up|kill (all|every)", re.I)


def route(text):
    """Map what you said to (kind, action, target, confirmation prompt). kind: chat | notes | apps | act | guard."""
    t = text.strip().lower().rstrip(".!?")
    if DANGER.search(t):
        return ("guard", None, None, None)
    # actions only for commands ("lock my computer", "jarvis, could you open chrome"), never for questions about them
    # ("should I restart my computer?", "how do I close a for loop?")
    cmd = re.sub(r"^(hey |ok |okay )?(jarvis[, ]+)?(please |can you |could you |would you |will you )?(please )?", "", t).strip()
    if text.strip().endswith("?") and cmd == t:
        cmd = ""
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
    if re.match(r"(mute|unmute)( the)?( sound| audio| volume| speakers)?$", cmd):
        return ("act", "mute", None, None)
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


# ------------------------------------------------------------------ smart note search (ChromaDB)
# JarvisSmartSearch=1 (default when chromadb is installed): your vault is split into passages and indexed by meaning
# in a local ChromaDB database (Data\notes_index), so "what did I write about motor torque" finds notes that never use
# those exact words. The index updates itself in the background (only changed notes) every 10 minutes and before a
# search. If ChromaDB isn't installed or fails, the keyword search below is used instead - search always works.
_chroma = {"col": None, "root": None, "seen": {}, "last": 0.0, "failed": False}
_chroma_lock = threading.Lock()


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
    with _chroma_lock:
        try:
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
                    col.delete(where={"path": path})
                    if parts:
                        name = os.path.splitext(fn)[0]
                        col.upsert(ids=[f"{path}#{i}" for i in range(len(parts))],
                                   documents=[f"{name}\n{p}" for p in parts],
                                   metadatas=[{"path": path, "name": name, "mtime": mt} for _ in parts])
                    seen[path] = mt
                    changed += 1
            for gone in [p for p in seen if p not in present]:
                col.delete(where={"path": gone})
                del seen[gone]
                changed += 1
            _chroma["last"] = time.time()
            if changed:
                log(f"notes index: {changed} note(s) updated in {time.time() - t0:.1f}s")
            return col
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
                return min(dur, 2.5)
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
            problem("No Ollama model downloaded - run Control Center > JARVIS > SETUP (or: ollama pull llama3.1:8b)")
            return
        warm(model)
        threading.Thread(target=prepare_fillers, daemon=True).start()   # cheap if nothing changed
        time.sleep(chime())                                    # don't record the chime
        log(f"timing: click -> listening {time.time() - t_click:.2f}s")
        audio = listen()
        if audio is None or cancel.is_set():
            return
        t_spoke = time.time()
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
        if kind == "act":
            if prompt is None:                                 # harmless: do it now
                ok = run_action(action, target)
                reply_line((f"Opening {target[0]}." if action == "open" else "Done.") if ok else "That didn't work.", quiet)
                return
            # two-phase: stage it, ask, and listen for the answer (15 s) without another click
            pending = {"action": action, "target": target, "expires": time.time() + 15}
            reply_line(prompt, quiet)
            S.set(state="listening", level=0.0)
            answer_audio = listen() if not cancel.is_set() else None
            answer = transcribe(answer_audio) if answer_audio is not None else ""
            if answer:
                convo_add("U", answer)
            if answer and YES.search(answer) and time.time() < pending["expires"] and not cancel.is_set():
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
            names = sorted({n for n, _ in start_apps()})
            if target:
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
        messages = fit_context([{"role": "system", "content": system_prompt() + extra}], history[-8:], {"role": "user", "content": text})
        collected = []
        stream = chat_stream(model, messages)
        if quiet and setting("JarvisMutedPopup", "1") == "1":
            say_text_only(sentences_from(stream, collected), collected)
        else:
            speak_all(sentences_from(stream, collected))
        reply = "".join(collected).strip()
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
    while True:
        try:
            want = setting("JarvisWakeWord", "0") == "1" and hud_tier() < 3
            if not want or busy.locked():
                if stream is not None:
                    stream.close()
                    stream = None
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
                stream = sd.InputStream(samplerate=16000, channels=1, dtype="int16", blocksize=1280)
                stream.start()
                model.reset()
            data, _ = stream.read(1280)
            scores = model.predict(np.asarray(data[:, 0], dtype=np.int16))
            try:
                need = max(0.2, min(0.9, float(setting("JarvisWakeSensitivity", "0.5"))))
            except ValueError:
                need = 0.5
            if max(scores.values()) >= need:
                log(f"wake word heard ({max(scores.values()):.2f})")
                stream.close()
                stream = None
                model.reset()
                threading.Thread(target=turn, args=(hud_tier(),), daemon=True).start()
                time.sleep(1.0)                                # let the turn take the microphone
        except ImportError:
            if not warned:
                problem("Wake word needs openwakeword - run Control Center > JARVIS > SETUP", popup=False)
                warned = True
            time.sleep(10)
        except Exception as e:
            log(f"wake word: {e!r}")
            try:
                if stream is not None:
                    stream.close()
            except Exception:
                pass
            stream = None
            time.sleep(5)


# ------------------------------------------------------------------ main loop: watch the command file
owner = False


def main():
    global owner
    if not single_instance():
        return
    owner = True
    log(f"started ({RES}), Python {sys.version.split()[0]}")
    miss = missing_packages()
    S.set(state="idle", level=0.0, err=("Setup needed - missing " + ", ".join(miss)) if miss else "")
    threading.Thread(target=lambda: ensure_ollama() and installed_models(), daemon=True).start()
    if not miss:
        threading.Thread(target=prepare_fillers, daemon=True).start()
        threading.Thread(target=wake_loop, daemon=True).start()
        threading.Thread(target=index_loop, daemon=True).start()
    last_mtime = os.path.getmtime(CMD_FILE) if os.path.exists(CMD_FILE) else 0
    beat, missing = 0.0, 0
    while True:
        try:
            time.sleep(0.1)
            now = time.time()
            if now - beat >= 2:
                beat = now
                S.set()                                        # heartbeat
                missing = 0 if rainmeter_running() else missing + 1
                if missing >= 15:                              # Rainmeter gone for 30 s: quit
                    log("Rainmeter closed - exiting")
                    return
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
