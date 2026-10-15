"""mic: moved verbatim from jarvis.py (refactor). See JARVIS-Repair-Plan.txt, REFACTOR."""
import os
import re
import time
from .audio import speakers
from .base import DUCK_FILE, MICS_FILE, S, cancel, log, mic, problem, setting


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


def pick_mic(term):
    """The one listed input device whose name holds `term` (the words you said): its full name, "" for the Windows default,
    None if none matches, a list if several do. Reads the same list the Control Center shows."""
    if re.fullmatch(r"(?:the )?(?:windows |system |normal |usual )?default", term.strip().lower()):
        return ""
    try:
        with open(MICS_FILE, encoding="utf-8") as f:
            names = [n.strip() for n in f if n.strip()]
    except OSError:
        return None
    hits = [n for n in names if term.strip().lower() in n.lower()]
    return hits[0] if len(hits) == 1 else hits or None


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
    """Seconds a follow-up waits for you to start talking: JarvisFollowUpWait, default 3, kept to 3-30."""
    try:
        return max(3.0, min(30.0, float(setting("JarvisFollowUpWait", "3"))))
    except ValueError:
        return 3.0


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
    return np.concatenate(frames)
