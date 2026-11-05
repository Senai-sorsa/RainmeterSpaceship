"""player: smooth speech playback (JarvisVoiceSmooth=1). One persistent output stream instead of one per chunk, WASAPI
(shared, low latency, automatic sample-rate conversion) with an automatic fallback to the old default path, every clip
trimmed of its built-in 0.3 s of near-silence and faded at both ends, and the pause between chunks chosen by the kind of
boundary instead of whatever each clip happens to end with. See tasks/jarvis-voice-plan-2026-11-03.md (V1-V5, V10).
With JarvisVoiceSmooth=0 (default is 1) none of this runs: speech.play_samples keeps its old stream-per-chunk code."""
import re
import threading
import time
from ..base import S, cancel, log, setting
from ..stopwords import far_add

# pause before a chunk, by what the PREVIOUS chunk ended with (ms; the setting overrides the code default)
PAUSES = {"cont": ("JarvisPauseCont", 25), "clause": ("JarvisPauseClause", 150), "sentence": ("JarvisPauseSentence", 300),
          "hesitate": ("JarvisPauseHesitate", 350)}
CLAUSE_END = re.compile(r"[,;:—–-][\"')]*$")
SENTENCE_END = re.compile(r"[.!?][\"')]*$")


SMOOTH_DEFAULT = "1"          # on unless JarvisVoiceSmooth=0 (the old stream-per-chunk path stays as the fallback)


def smooth_on():
    return str(setting("JarvisVoiceSmooth", SMOOTH_DEFAULT)).strip() == "1"


def _num(name, default, lo, hi):
    try:
        return max(lo, min(hi, float(setting(name, str(default)))))
    except (TypeError, ValueError):
        return default


def stream_latency():
    """The WASAPI buffer in seconds (JarvisPlayerLatency, default 0.1; 0 = PortAudio's "low", about 25 ms on this machine). A bigger
    buffer rides out short stalls of the writing thread, which is what random slight glitches in the speech were by ear (live test F1)."""
    sec = _num("JarvisPlayerLatency", 0.1, 0.0, 0.5)
    return sec if sec > 0 else "low"


def pause_ms(kind):
    name, default = PAUSES.get(kind, PAUSES["cont"])
    return int(_num(name, default, 0, 1500))


def boundary(prev_text):
    """What the previous chunk ended with: a "sentence" end, a "clause" end (comma, colon, dash), or "cont" (cut mid-clause)."""
    t = (prev_text or "").rstrip()
    return "sentence" if SENTENCE_END.search(t) else "clause" if CLAUSE_END.search(t) else "cont"


def trim(a, rate):
    """Cut the near-silence (below JarvisTrimDb, default -45 dB) off both ends, keeping ~20 ms. An all-quiet clip is left alone."""
    import numpy as np
    thr = 10 ** (_num("JarvisTrimDb", -45, -80, -20) / 20)
    x = np.abs(a) if a.ndim == 1 else np.abs(a).max(axis=1)
    idx = np.nonzero(x > thr)[0]
    if idx.size == 0:
        return a
    keep = int(rate * 0.02)
    return a[max(0, int(idx[0]) - keep): min(len(a), int(idx[-1]) + 1 + keep)]


def fade(a, rate, ms=None):
    """A copy with a raised-cosine fade in and out (JarvisFadeMs, default 10), so a cut never clicks. Same length."""
    import numpy as np
    n = int(rate * (ms if ms is not None else _num("JarvisFadeMs", 10, 0, 50)) / 1000)
    n = min(n, len(a) // 2)
    out = np.array(a, dtype=np.float32, copy=True)
    if n > 0:
        ramp = (0.5 - 0.5 * np.cos(np.linspace(0.0, np.pi, n, dtype=np.float32)))
        if out.ndim > 1:
            ramp = ramp[:, None]
        out[:n] *= ramp
        out[len(out) - n:] *= ramp[::-1]
    return out


def prepare(a, rate):
    """trim + fade: what a clip becomes before it is written to the stream."""
    return fade(trim(a, rate), rate)


class Player:
    """One output stream kept open across chunks (and fillers), closed after JarvisIdleClose seconds (default 1.5) without
    a write. Safe to call from several threads: one chunk plays at a time."""

    def __init__(self):
        self.lock = threading.RLock()
        self.out = None
        self.fmt = None
        self.api = ""
        self.last = 0.0
        self.timer = None

    # -- opening
    def _wasapi_device(self, sd):
        for api in sd.query_hostapis():
            if "wasapi" in str(api.get("name", "")).lower():
                dev = api.get("default_output_device", -1)
                return dev if isinstance(dev, int) and dev >= 0 else None
        return None

    def _open(self, rate, ch):
        import sounddevice as sd
        out, api = None, ""
        if str(setting("JarvisWasapi", "1")).strip() != "0":
            try:
                dev = self._wasapi_device(sd)
                if dev is not None:
                    out = sd.OutputStream(samplerate=rate, channels=ch, dtype="float32", device=dev, latency=stream_latency(),
                                          extra_settings=sd.WasapiSettings(auto_convert=True))
                    out.start()
                    api = "wasapi"
            except Exception as e:
                log(f"player: WASAPI not available ({type(e).__name__}: {str(e)[:80]}) - using the default audio path")
                out = None
        if out is None:
            out = sd.OutputStream(samplerate=rate, channels=ch, dtype="float32")
            out.start()
            api = "default"
        self.out, self.fmt, self.api = out, (rate, ch), api
        log(f"player: stream open ({api}, {rate} Hz)")

    def _ready(self, rate, ch):
        if self.out is not None and self.fmt != (rate, ch):
            self.close()
        if self.out is None:
            self._open(rate, ch)

    def warm(self, rate=24000):
        """Open the stream now (before the first clip is ready), so the first word doesn't wait for the device."""
        try:
            with self.lock:
                if self.out is None:
                    self._ready(rate, 1)
                    self.last = time.time()
                    self._arm()
        except Exception as e:
            self._drop()
            log(f"player: warm-up failed ({type(e).__name__}: {str(e)[:80]})")

    # -- closing
    def _arm(self):
        if self.timer is not None:
            self.timer.cancel()
        self.timer = threading.Timer(_num("JarvisIdleClose", 1.5, 0.3, 30) + 0.05, self._idle)
        self.timer.daemon = True
        self.timer.start()

    def _idle(self):
        if not self.lock.acquire(blocking=False):
            return self._arm()                                 # a chunk is playing: look again later
        try:
            if self.out is not None and time.time() - self.last >= _num("JarvisIdleClose", 1.5, 0.3, 30):
                self.close()
            elif self.out is not None:
                self._arm()
        finally:
            self.lock.release()

    def _drop(self):
        out, self.out, self.fmt = self.out, None, None
        if out is not None:
            try:
                out.abort()
                out.close()
            except Exception:
                pass

    def close(self):
        with self.lock:
            out, self.out, self.fmt = self.out, None, None
            if self.timer is not None:
                self.timer.cancel()
                self.timer = None
            if out is not None:
                try:
                    out.stop()
                    out.close()
                except Exception:
                    pass

    # -- playing
    def play(self, a, rate, progress=None, lead_ms=0, gain=1.0):
        """Write `lead_ms` of silence, then the clip (trimmed, faded) in 40 ms blocks, to the open stream. The same hooks as the
        old path: stop/barge-in (cancel) aborts within one block, the orb level, the echo reference, the pop-up progress."""
        import numpy as np
        a = prepare(np.asarray(a, dtype=np.float32), rate)
        ch = 1 if a.ndim == 1 else a.shape[1]
        block = max(1, int(rate * 0.04))
        with self.lock:
            try:
                if cancel.is_set():
                    return
                self._ready(rate, ch)
                shape = (block,) if ch == 1 else (block, ch)
                for left in range(int(rate * lead_ms / 1000), 0, -block):      # the chosen pause, in the same stream
                    if cancel.is_set():
                        self._drop()
                        return
                    self.out.write(np.zeros(shape, dtype=np.float32) if left >= block else np.zeros((left,) + shape[1:], np.float32))
                under = 0                                      # diagnostic only: device under-runs (write() returns True)
                for i in range(0, len(a), block):
                    if cancel.is_set():
                        self._drop()                           # abort: silent now, not after the buffer; the next clip re-opens
                        return
                    chunk = np.ascontiguousarray(a[i:i + block], dtype=np.float32)
                    out = chunk * gain if gain < 1.0 else chunk
                    if self.out.write(out) is True:
                        under += 1
                    far_add(out, rate)                         # the echo reference is what really played
                    S.set(level=min(1.0, float(np.sqrt(np.mean(chunk * chunk)) + 1e-9) / 0.18), force=False)
                    if progress:
                        progress(min(1.0, (i + block) / len(a)))
                log(f"player: clip {len(a) / rate:.1f} s, peak {float(np.max(np.abs(a))) if len(a) else 0.0:.2f}, device under-runs {under}")
                self.last = time.time()
                self._arm()
            except Exception:
                self._drop()                                   # a broken stream is never reused
                raise
            finally:
                S.set(level=0.0)


player = Player()
