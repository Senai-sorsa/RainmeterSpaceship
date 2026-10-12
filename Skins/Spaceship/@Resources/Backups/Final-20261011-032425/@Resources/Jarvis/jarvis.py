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
Optional: pip install kokoro-onnx + a voice (.onnx) for a natural voice; otherwise the Windows voice is used.
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
    need = {"faster_whisper": "faster-whisper", "sounddevice": "sounddevice", "numpy": "numpy", "kokoro_onnx": "kokoro-onnx"}
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
    if len(text) > 4000:
        text = text[:4000].rsplit(" ", 1)[0] + " ..."
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
                       "options": {"num_ctx": 2048, "temperature": 0.5}}).encode()
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
    """Record until you stop talking: waits up to 6 s for speech, stops after 0.9 s of silence, max 15 s."""
    import numpy as np
    import sounddevice as sd
    rate, block = 16000, 480                     # 30 ms blocks
    frames, started, silent, waited = [], False, 0, 0
    floor = None
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
            if started and silent > 30:
                break
            if not started and waited > 200:
                return None
            if time.time() - t0 > 15:
                break
    if cancel.is_set() or not started:
        return None
    return np.concatenate(frames)


# ------------------------------------------------------------------ text to speech
_kokoro = None


def voice_rate():
    try:
        return max(-5, min(5, int(float(setting("JarvisVoiceRate", "1")))))
    except ValueError:
        return 1


def synth_kokoro(text):
    """Text -> (samples, sample_rate). Kokoro voice if JarvisVoice points at a .onnx, else None."""
    global _kokoro
    voice = setting("JarvisVoice", "").strip().strip('"')
    if voice and os.path.exists(voice):
        try:
            if _kokoro is None:
                from kokoro_onnx import Kokoro
                voice_bin = os.path.join(os.path.dirname(voice), "voices.bin")
                if not os.path.exists(voice_bin):
                    return None, None
                _kokoro = Kokoro(voice, voice_bin)
            
            speed = 1.0 + (voice_rate() - 1) * 0.1
            samples, sample_rate = _kokoro.create(text, voice="bm_george", speed=speed, lang="en-gb")
            return samples, sample_rate
        except Exception as e:
            log(f"kokoro failed ({e}) - using the Windows voice")
    return None, None


def play_windows_voice(text, shown):
    import numpy as np
    import sounddevice as sd
    fd, path = tempfile.mkstemp(suffix=".wav", prefix="jarvis_win_")
    os.close(fd)
    
    ps = ("Add-Type -AssemblyName System.Speech; $s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
          "$v = $s.GetInstalledVoices() | Where-Object { $_.VoiceInfo.Culture.Name -eq 'en-GB' } | Select-Object -First 1; "
          f"if ($v) {{ $s.SelectVoice($v.VoiceInfo.Name) }}; $s.Rate = {voice_rate()}; "
          f"$s.SetOutputToWaveFile('{path}'); $s.Speak([Console]::In.ReadToEnd()); $s.Dispose()")
    try:
        subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", ps], input=text.encode("utf-8"),
                       creationflags=NO_WINDOW, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=60)
        if os.path.exists(path) and os.path.getsize(path) > 100:
            with wave.open(path, "rb") as wf:
                rate, ch, width = wf.getframerate(), wf.getnchannels(), wf.getsampwidth()
                raw = wf.readframes(wf.getnframes())
            if width == 2:
                a = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
                if ch > 1:
                    a = a.reshape(-1, ch)
                block = int(rate * 0.04)
                with sd.OutputStream(samplerate=rate, channels=ch, dtype="float32") as out:
                    for i in range(0, len(a), block):
                        if cancel.is_set():
                            break
                        chunk = a[i:i + block]
                        out.write(np.ascontiguousarray(chunk, dtype=np.float32))
                        S.set(level=min(1.0, float(np.sqrt(np.mean(chunk * chunk))) / 0.18), force=False)
    except Exception as e:
        log(f"windows voice failed: {e}")
        if not shown:
            S.set(pop="open")
            shown = True
        live(text)
    finally:
        S.set(level=0.0)
        try:
            os.remove(path)
        except OSError:
            pass


def speak_all(sentences):
    """Synthesize the next sentence while the current one plays. If speech fails, the words go to the pop-up."""
    import numpy as np
    import sounddevice as sd
    q = queue.Queue(maxsize=3)
    failed = []

    def producer():
        for s in sentences:
            if cancel.is_set():
                break
            clean = re.sub(r"[*_#`>\[\]]", "", s).strip()
            if not clean:
                continue
            
            samples, sr = synth_kokoro(clean)
            if samples is not None:
                q.put(("kokoro", samples, sr, clean))
            else:
                q.put(("windows", None, None, clean))
        q.put(None)

    threading.Thread(target=producer, daemon=True).start()
    first, spoken, shown = True, "", False
    while True:
        item = q.get()
        if item is None:
            break
        vtype, samples, sr, said = item
        spoken = (spoken + " " + said).strip()
        
        if first:
            S.set(state="speaking")
            first = False
            
        if (muted() and setting("JarvisMutedPopup", "1") == "1"):
            if not shown:
                S.set(pop="open")
                shown = True
            live(spoken)
            time.sleep(min(3.0, 0.06 * len(said)))
            continue
            
        if vtype == "kokoro":
            try:
                if not cancel.is_set():
                    block = int(sr * 0.04)
                    with sd.OutputStream(samplerate=sr, channels=1, dtype="float32") as out:
                        for i in range(0, len(samples), block):
                            if cancel.is_set():
                                break
                            chunk = samples[i:i + block]
                            out.write(np.ascontiguousarray(chunk, dtype=np.float32))
                            rms = float(np.sqrt(np.mean(chunk * chunk)) + 1e-9)
                            S.set(level=min(1.0, rms / 0.18), force=False)
            except Exception as e:
                log(f"kokoro playback failed: {e}")
                if not shown:
                    S.set(pop="open")
                    shown = True
                live(spoken)
            finally:
                S.set(level=0.0)
        else:
            play_windows_voice(said, shown)

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
    text, t0 = time.time(), time.time()
    for s in sentences:
        if cancel.is_set():
            break
        text = (text + " " + s).strip()
        live(text)
        S.set(level=0.25 + 0.2 * abs(((time.time() - t0) * 2) % 2 - 1), force=False)
    live("")


# ------------------------------------------------------------------ one conversation turn
history = []          # recent turns, forgotten after 10 minutes
last_turn = 0.0


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
        if time.time() - last_turn > 600:
            history = []
        messages = [{"role": "system", "content": system_prompt()}] + history[-8:] + [{"role": "user", "content": text}]
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