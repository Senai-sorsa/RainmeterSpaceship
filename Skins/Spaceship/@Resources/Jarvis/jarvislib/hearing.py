"""hearing: moved verbatim from jarvis.py (refactor). See JARVIS-Repair-Plan.txt, REFACTOR."""
import os
import re
import sys
import threading
import time
from .base import S, busy, log, problem, setting
from .gpu import cpu_in_use, cpu_threads, gpu


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
