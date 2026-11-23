"""voice/output: what touches the speakers and the pop-up: play_samples (device, headphone gain, the orb), muted(),
say_text_only (moved verbatim from speech.py, refactor phase 3)."""
import re
import time
from ..audio import speakers_mute
from .. import quiet
from ..base import ENV_FILE, S, cancel, live, log, setting
from ..stopwords import far_add
from .player import player, smooth_on


HEADPHONES = re.compile(r"head ?phones?|head ?set|ear ?buds?|ear ?phones?|airpods|\bbuds\d*\b|in-?ear", re.I)
_out_name = [0.0, ""]                                          # when the output device name was last read, the name
first_sound = [None]                                           # E6: when this turn's first clip began (the turn resets it)


def headphone_gain(device_name, level):
    """T7/J4: his voice in headphones plays at JarvisHeadphoneLevel % (default 60; 100 = as loud as on speakers), since
    it is right at your ear. 1.0 for speakers or an unknown device. Only his voice: the Windows volume is not touched."""
    if not device_name or not HEADPHONES.search(device_name):
        return 1.0
    try:
        return max(10, min(100, int(float(level)))) / 100
    except (TypeError, ValueError):
        return 0.6


def output_name():
    """The default output device's name, read at most every 10 s (a headset plugged in mid-talk counts from then)."""
    if time.time() - _out_name[0] > 10:
        try:
            import sounddevice as sd
            _out_name[1] = str(sd.query_devices(kind="output").get("name", ""))
        except Exception:
            _out_name[1] = ""
        _out_name[0] = time.time()
    return _out_name[1]


def play_samples(a, rate, progress=None, lead_ms=None):
    """Play audio, writing its loudness to the HUD as it goes (that's what moves the hologram). progress(0..1), if
    given, is called after each block (the pop-up types the sentence at speaking pace).
    lead_ms (JarvisVoiceSmooth=1 only, given by his own speech and fillers): the clip goes to the persistent stream, trimmed
    and faded, after that many ms of silence. Everything else (chimes, dings) keeps the old stream-per-call path."""
    if first_sound[0] is None:
        first_sound[0] = time.time() + (lead_ms / 1000 if lead_ms is not None and smooth_on() else 0)   # smooth: after its lead silence
    import numpy as np
    import sounddevice as sd
    ch = 1 if a.ndim == 1 else a.shape[1]
    block = max(1, int(rate * 0.04))
    gain = headphone_gain(output_name(), setting("JarvisHeadphoneLevel", "60"))
    if lead_ms is not None and smooth_on():
        try:
            return player.play(a, rate, progress, lead_ms, gain)
        except Exception as e:                                 # the new path failed: the old one still speaks this clip
            log(f"player failed ({type(e).__name__}: {str(e)[:80]}) - using the old playback for this clip")
    try:
        with sd.OutputStream(samplerate=rate, channels=ch, dtype="float32") as out:
            for i in range(0, len(a), block):
                if cancel.is_set():
                    out.abort()                                # drop what is queued: silent now, not after the buffer
                    break
                chunk = np.ascontiguousarray(a[i:i + block], dtype=np.float32)
                out.write(chunk * gain if gain < 1.0 else chunk)
                far_add(chunk * gain if gain < 1.0 else chunk, rate)   # the echo reference is what really played
                S.set(level=min(1.0, float(np.sqrt(np.mean(chunk * chunk)) + 1e-9) / 0.18), force=False)   # the orb: unscaled
                if progress:
                    progress(min(1.0, (i + block) / len(a)))
    finally:
        S.set(level=0.0)


def muted():
    if quiet.now():                                            # 8c: class: pop-up only
        return True
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
    try:
        for s in sentences:
            if cancel.is_set():
                break
            text = (text + " " + s).strip()
            live(text)
            S.set(level=0.25 + 0.2 * abs(((time.time() - t0) * 2) % 2 - 1), force=False)
    finally:
        live("")
