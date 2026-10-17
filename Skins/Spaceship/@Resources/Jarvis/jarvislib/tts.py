"""tts: moved verbatim from jarvis.py (refactor). See JARVIS-Repair-Plan.txt, REFACTOR."""
import os
import re
import subprocess
import tempfile
import time
import wave
from .base import NO_WINDOW, RES, cancel, log, problem, setting
from .gpu import cpu_threads, gpu
from .hearing import _cuda_dlls


# ------------------------------------------------------------------ text to speech
# Engines, chosen by JarvisVoice: a kokoro-*.onnx file -> Kokoro-82M (natural, runs on the CPU), any other .onnx ->
# Piper, blank -> the built-in Windows voice. If an engine fails, that sentence falls back to the Windows voice, and
# if even that fails the words go to the pop-up - he never just goes silent.
_engines = {}               # loaded voices, by path
_voice_dev = [None]         # "cuda" or "cpu": where the Kokoro voice runs
_voice_gpu_off = [0.0]      # after a GPU failure of the voice: the CPU until then
_broken = {}                # voice file -> when it may be tried again (a missing or unsupported file: never)
_kokoro_last = [None]       # the Kokoro voice last used (logged whenever it changes)


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


def _mix(eng):
    """The voice name "default": half bm_lewis, half am_michael as one style vector (kokoro-onnx 0.6 takes an array as the
    voice). None when either voice is missing."""
    try:
        return (0.5 * eng.get_voice_style("bm_lewis") + 0.5 * eng.get_voice_style("am_michael")).astype("float32")
    except Exception as e:
        log(f"kokoro 'default' voice needs bm_lewis and am_michael ({type(e).__name__}) - using bm_lewis")
        return None


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
    mix = _mix(eng) if name == "default" else None
    if name == "default" and mix is None:
        name = "bm_lewis"
    try:
        known = list(eng.get_voices())
    except Exception:
        known = []
    if mix is None and known and name not in known:
        log(f"kokoro voice '{name}' doesn't exist - using bm_lewis (available: {', '.join(known)})")
        name = "bm_lewis" if "bm_lewis" in known else known[0]
    if _kokoro_last[0] != name:
        _kokoro_last[0] = name
        log(f"kokoro speaking with voice {name}")
    speed = max(0.6, min(1.6, 1.0 + (voice_rate() - 1) * 0.08))
    lang = "en-gb" if name[:1] == "b" or name == "default" else "en-us"
    try:
        samples, rate = eng.create(text, voice=name if mix is None else mix, speed=speed, lang=lang)
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
    # Escape path for PowerShell: inside '...' a quote is doubled (a profile like O'Brien)
    safe_path = path.replace("\\", "/").replace("'", "''")
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
