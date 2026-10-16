"""speech: moved verbatim from jarvis.py (refactor). See JARVIS-Repair-Plan.txt, REFACTOR."""
import queue
import re
import threading
import time
from .audio import speakers_mute
from .base import ENV_FILE, JARVIS_WORD, S, cancel, live, log, name_until, problem, setting
from .stopwords import far_add, saying
from .tts import synth_audio, voice_rate


def play_samples(a, rate, progress=None):
    """Play audio, writing its loudness to the HUD as it goes (that's what moves the hologram). progress(0..1), if
    given, is called after each block (the pop-up types the sentence at speaking pace)."""
    import numpy as np
    import sounddevice as sd
    ch = 1 if a.ndim == 1 else a.shape[1]
    block = max(1, int(rate * 0.04))
    try:
        with sd.OutputStream(samplerate=rate, channels=ch, dtype="float32") as out:
            for i in range(0, len(a), block):
                if cancel.is_set():
                    out.abort()                                # drop what is queued: silent now, not after the buffer
                    break
                chunk = np.ascontiguousarray(a[i:i + block], dtype=np.float32)
                out.write(chunk)
                far_add(chunk, rate)
                S.set(level=min(1.0, float(np.sqrt(np.mean(chunk * chunk)) + 1e-9) / 0.18), force=False)
                if progress:
                    progress(min(1.0, (i + block) / len(a)))
    finally:
        S.set(level=0.0)


def speak_all(sentences):
    """Synthesize the next sentence while the current one plays. If speech fails, the words go to the pop-up.
    Returns the sentences whose playback began (8-A2: what the history keeps when he is talked over)."""
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
        spoken = _speak_queue(q, t0)
    finally:
        gone.set()
    live("")
    if broke:
        raise broke[0]
    if failed:
        problem("Couldn't speak (voice failed) - the reply is in the log", popup=False)
    return spoken


def _speak_queue(q, t0):
    filler_done()                                              # never talk over a status phrase
    first, spoken, shown, last = True, "", False, ""
    while True:
        try:
            item = q.get(timeout=0.5)
        except queue.Empty:
            if cancel.is_set():                                # cancelled while a sentence was still being made
                break
            continue
        if item is None or cancel.is_set():                    # stopped: the rest is never said
            break
        audio, said = item
        saying[0], last = (last + " " + said).strip(), said    # the text guard: the previous piece and this one
        spoken = (spoken + " " + said).strip()
        if audio is not None and JARVIS_WORD.search(said):     # his own "Jarvis" must not wake the barge-in
            name_until[0] = time.time() + len(audio[0]) / audio[1] + 1.0
        if first:
            S.set(state="speaking")
            log(f"timing: reply start -> first audio {time.time() - t0:.2f}s")
            first = False
        # muted mid-reply, or the voice failed: show the words instead
        as_text = (muted() and setting("JarvisMutedPopup", "1") == "1") or audio is None
        if as_text:
            if not shown:
                S.set(pop="open")
                shown = True
            live(spoken)
        if audio is None:
            cancel.wait(min(3.0, 0.06 * len(said)))           # reading time instead of speaking time
            continue
        before, words, typed = spoken[:len(spoken) - len(said)].strip(), said.split(), [0]

        def type_on(frac):                                     # L8: the pop-up's live line grows with his voice
            n = min(len(words), int(frac * len(words)) + 1)
            if n != typed[0]:
                typed[0] = n
                live((before + " " + " ".join(words[:n])).strip())
        try:
            if not cancel.is_set():
                play_samples(audio[0], audio[1], None if as_text else type_on)
        except Exception as e:
            log(f"playback failed: {e}")
            if not shown:
                S.set(pop="open")
                shown = True
            live(spoken)
    return spoken


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
