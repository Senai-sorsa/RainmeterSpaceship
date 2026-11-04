"""voice/fillers: cached status phrases ("Searching your notes.") spoken at once while slower work runs (moved verbatim
from speech.py, refactor phase 3)."""
import threading
from ..base import live, log, setting
from .output import play_samples
from .player import smooth_on
from . import synth as _tts
from .synth import synth_audio, voice_rate


# ------------------------------------------------------------------ skills: fillers, actions, guardrails
# 1. Status fillers - common phrases are spoken into memory at startup, so when a slower route starts (searching
#    your notes, scanning apps) Jarvis says "Searching your notes." instantly while the work runs alongside.
# 2. Actions - a small whitelist. Safe ones (open an app, mute) run at once; ones that change or stop things (close an
#    app, lock, sleep, restart, shut down) are staged and need a spoken "yes" within 15 s - he listens for it himself.
# 3. Guardrails - nothing outside the whitelist is ever executed. Destructive or joke requests ("self-destruct",
#    "delete system32") go to the model in persona with a note that nothing will run, so he plays along drily.
FILLERS = {"notes": "Searching your notes.", "apps": "Scanning installed applications.", "diag": "Checking the system.",
           "confirm_wait": "One moment.", "cancelled": "Cancelled.", "done": "Done."}
_filler_audio = {}
_filler_voice = [None]
_filler_thread = [None]


def prepare_fillers():
    """Speak the status phrases into memory with the current voice (re-done if you switch voices)."""
    voice = setting("JarvisVoice", "") + "|" + setting("JarvisKokoroVoice", "") + "|" + str(voice_rate())
    if _filler_voice[0] == voice and smooth_on() and not _tts._engines:
        try:                                                   # V15: the voice was unloaded while idle: load it now, not at the first word
            synth_audio("Ready.")
        except Exception as e:
            log(f"voice warm-up failed: {e}")
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
            if smooth_on():
                play_samples(a[0], a[1], None, 0)               # through the persistent stream, trimmed, so it joins the reply cleanly
            else:
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
