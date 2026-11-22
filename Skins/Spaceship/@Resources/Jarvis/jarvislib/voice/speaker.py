"""voice/speaker: speak_all(): synthesise the next piece while the current one plays, pace the pieces, keep the text
guard and the pop-up in step (moved verbatim from speech.py, refactor phase 3)."""
import queue
import re
import threading
import time
from ..base import JARVIS_WORD, S, cancel, live, log, name_until, problem, setting
from ..say import speakable
from ..stopwords import saying
from .fillers import filler_done
from .output import muted, play_samples
from .pacing import hesitation_parts, merged
from .player import boundary, pause_ms, player, smooth_on
from . import synth as _tts
from .synth import synth_audio


def speak_all(sentences):
    """Synthesize the next sentence while the current one plays. If speech fails, the words go to the pop-up.
    Returns the sentences whose playback began (8-A2: what the history keeps when he is talked over)."""
    q = queue.Queue(maxsize=3)
    failed, broke, timed, gone, t0 = [], [], [], threading.Event(), time.time()
    smooth = smooth_on()
    if smooth:
        sentences = merged(sentences, gone)
    windows_only = [False]                                     # smooth mode, V14: once the neural voice failed, the reply stays in one voice

    def put(item):
        while not gone.is_set():                               # the reader left (cancelled): stop, don't wait on a full queue
            try:
                return q.put(item, timeout=0.5)
            except queue.Full:
                pass

    def make(text):
        if windows_only[0]:
            return synth_audio(text, force_windows=True)
        audio = synth_audio(text)
        if smooth and audio is not None and _tts.last_source[0] == "windows":
            windows_only[0] = True
        return audio

    def producer():
        try:
            for s in sentences:
                if cancel.is_set() or gone.is_set():
                    break
                clean = re.sub(r"[*_#`>\[\]]", "", s).strip()
                if not clean:
                    continue
                t1 = time.time()
                for shown, say, pause in (hesitation_parts(clean) if smooth else [(clean, clean, None)]):
                    try:
                        audio = make(speakable(say))
                    except Exception as e:
                        log(f"speech failed: {e}")
                        audio = None
                    if not timed:
                        timed.append(1)
                        log(f"timing: reply start -> first sentence {t1 - t0:.2f}s, its voice {time.time() - t1:.2f}s")
                    if audio is None:
                        failed.append(shown)
                    put((audio, shown, pause))
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
    smooth = smooth_on()
    if smooth:
        threading.Thread(target=player.warm, daemon=True).start()   # V5: the device is open before the first word is ready
    first, spoken, shown, last = True, "", False, ""
    seams, under, t_end, prev_text, prev_pause = [], 0, None, "", None
    while True:
        try:
            item = q.get(timeout=0.5)
        except queue.Empty:
            if cancel.is_set():                                # cancelled while a sentence was still being made
                break
            continue
        if item is None or cancel.is_set():                    # stopped: the rest is never said
            break
        audio, said = item[0], item[1]
        pause_kind = item[2] if len(item) > 2 else None        # smooth mode: a pause the text asked for AFTER this clip
        saying[0], last = (last + " " + said).strip(), said    # the text guard: the previous piece and this one
        spoken = (spoken + " " + said).strip()
        if audio is not None and JARVIS_WORD.search(said):     # his own "Jarvis" must not wake the barge-in
            name_until[0] = time.time() + len(audio[0]) / audio[1] + 1.0
        if first:
            S.set(state="speaking")
            log(f"timing: reply start -> first audio {time.time() - t0:.2f}s")
        # muted mid-reply, or the voice failed: show the words instead
        as_text = (muted() and setting("JarvisMutedPopup", "1") == "1") or audio is None
        if as_text:
            if not shown:
                S.set(pop="open")
                shown = True
            live(spoken)
        if audio is None:
            first = False
            cancel.wait(min(3.0, 0.06 * len(said)))           # reading time instead of speaking time
            continue
        before, words, typed, frac = spoken[:len(spoken) - len(said)].strip(), said.split(), [0], [None]

        def type_on(f):                                        # L8: the pop-up's live line grows with his voice
            frac[0] = f
            n = min(len(words), int(f * len(words)) + 1)
            if n != typed[0]:
                typed[0] = n
                live((before + " " + " ".join(words[:n])).strip())
        # smooth mode: the pause before this clip is chosen by how the previous one ended; time already spent waiting for the
        # synth counts toward it (a wait much longer than the pause is an under-run, logged)
        lead = None
        if smooth and not as_text:
            want = 0 if first else pause_ms(prev_pause or boundary(prev_text))
            waited = 0 if t_end is None else int((time.time() - t_end) * 1000)
            lead = max(0, want - waited)
            if not first:
                seams.append(max(want, waited))
                under += 1 if waited > want + 80 else 0
        first = False
        try:
            if not cancel.is_set():
                if lead is None:
                    play_samples(audio[0], audio[1], None if as_text else type_on)
                else:
                    play_samples(audio[0], audio[1], type_on, lead)
                t_end, prev_text, prev_pause = time.time(), said, pause_kind
                if cancel.is_set() and (lead is not None or frac[0] is not None):
                    # B11: talked over: only the words that really got out count as said (none if it never started)
                    f = frac[0] or 0.0
                    n = len(words) if f >= 1.0 else int(f * len(words))
                    spoken = (before + " " + " ".join(words[:n])).strip()
        except Exception as e:
            log(f"playback failed: {e}")
            if not shown:
                S.set(pop="open")
                shown = True
            live(spoken)
    if smooth and (seams or under):
        log(f"voice gaps: {len(seams) + 1} chunks, seams {seams} ms, {under} under-runs")
    return spoken
