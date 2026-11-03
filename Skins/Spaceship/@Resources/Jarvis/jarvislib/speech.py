"""speech: moved verbatim from jarvis.py (refactor). See JARVIS-Repair-Plan.txt, REFACTOR."""
import queue
import re
import threading
import time
from .audio import speakers_mute
from . import quiet
from .base import ENV_FILE, JARVIS_WORD, S, cancel, live, log, name_until, problem, setting
from .player import boundary, pause_ms, player, smooth_on
from .say import speakable
from .stopwords import far_add, saying
from . import tts as _tts
from .tts import synth_audio, voice_rate


HEADPHONES = re.compile(r"head ?phones?|head ?set|ear ?buds?|ear ?phones?|airpods|\bbuds\d*\b|in-?ear", re.I)
_out_name = [0.0, ""]                                          # when the output device name was last read, the name


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


MERGE_UNDER, MERGE_MAX = 6, 25          # smooth mode: a piece under 6 words joins the pieces already waiting, up to 25 words
HESITATE = re.compile(r"\s*(?:\.{3}|…)\s*")


def merged(sentences, gone):
    """Smooth mode, V8: the pieces of the reply, where a short piece (under 6 words) is joined to the pieces that are ALREADY
    waiting (never delaying for them), so "Yes." + "You have two." is one clip. The first piece is never held. A model-stream
    error is raised after the pieces before it, as the plain loop would."""
    pq, ahead = queue.Queue(), []

    def pull():
        try:
            for s in sentences:
                pq.put(("s", s))
        except Exception as e:
            pq.put(("e", e))
        pq.put(("end", None))
    threading.Thread(target=pull, daemon=True).start()

    def pop(block):
        if ahead:
            return ahead.pop(0)
        while True:
            try:
                return pq.get(timeout=0.5 if block else 0.02)       # 20 ms of grace for a piece that is just arriving
            except queue.Empty:
                if not block or gone.is_set() or cancel.is_set():
                    return None
    first = True
    while True:
        item = pop(True)
        if item is None or item[0] == "end":
            return
        if item[0] == "e":
            raise item[1]
        text = item[1]
        while not first and len(text.split()) < MERGE_UNDER:
            nxt = pop(False)
            if nxt is None:
                break
            if nxt[0] != "s" or len((text + " " + nxt[1]).split()) > MERGE_MAX:
                ahead.insert(0, nxt)
                break
            text = text + " " + nxt[1]
        first = False
        yield text


def plan_chunks(pieces):
    """The same merge on a finished list (tools/voice_gaps.py): every piece after the first, if short, takes the next ones."""
    ps, out, i = list(pieces), [], 0
    while i < len(ps):
        text, i = ps[i], i + 1
        while out and i < len(ps) and len(text.split()) < MERGE_UNDER and len((text + " " + ps[i]).split()) <= MERGE_MAX:
            text, i = text + " " + ps[i], i + 1
        out.append(text)
    return out


def hesitation_parts(clean):
    """V11: "Well... I suppose so." -> [("Well...", "Well", "hesitate"), ("I suppose so.", "I suppose so.", None)]: a real pause
    instead of a comma. Each part is (words shown, words synthesised, pause kind AFTER it or None). No ellipsis: one part."""
    parts = HESITATE.split(clean)
    if len(parts) < 2 or any(not p.strip() for p in parts):
        return [(clean, clean, None)]
    last = len(parts) - 1
    return [(p + ("..." if k < last else ""), p, "hesitate" if k < last else None) for k, p in enumerate(parts)]


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


def first_words():
    """JarvisFirstWords: how many words of the reply to wait for before he starts talking (default 5)."""
    try:
        return max(0, min(12, int(float(setting("JarvisFirstWords", "5")))))
    except ValueError:
        return 5


# ------------------------------------------------------------------ smooth chunking (JarvisVoiceSmooth=1, V6/V7/V9)
_ABBR = r"(?<!\bMr)(?<!\bMrs)(?<!\bMs)(?<!\bDr)(?<!\bProf)(?<!\bSt)(?<!\bvs)(?<!\betc)(?<!\be\.g)(?<!\bi\.e)"
_SENT = re.compile(r"(.+?" + _ABBR + r"[.!?])(\s+|$)", re.I)
_CLAUSE = re.compile(r"[,;:—–](?=\s)|(?<=\s)-(?=\s)")     # a comma, colon, dash... followed by a space: never "1,000" or "1:48"
START_BEFORE, START_AFTER, START_CAP, LONG_WORDS = 4, 3, 9, 25
_WEAK = frozenset("a an the and or but nor so to of in on at for with from by as than that which who is are was were be your my its "
                  "this these those his her their our i you we it point one two three four five six seven eight nine ten eleven twelve "
                  "twenty thirty forty fifty sixty seventy eighty ninety hundred thousand million".split())   # a chunk should not end on one of these (or a number)


def _done(t):
    """Words in t that are complete (followed by a space): the last word may still be arriving."""
    return len(re.findall(r"\S+\s", t))


def _sentence(buf):
    m = _SENT.match(buf)
    return None if (m and m.end() == len(buf) and not buf.endswith((" ", "\n"))) else m


def first_cut(buf, cap):
    """Smooth mode, V6: where the FIRST chunk of the reply ends, or None to keep waiting. The first sentence end; or the first
    comma/colon/dash after at least 4 words that still leaves at least 3 words of its sentence (so no orphan "sir." is left);
    or, with no such place within `cap` words, that word count. Returns the index just after the chunk."""
    sm = _sentence(buf)
    stop = sm.end(1) if sm else None
    for c in _CLAUSE.finditer(buf):
        if stop is not None and c.end() > stop:
            break
        if (len(buf[:c.end()].split()) >= START_BEFORE and _done(buf[c.end():stop]) >= START_AFTER
                and not re.match(r"\s*(?:sir|mr|mrs|ms|dr)\b", buf[c.end():], re.I)):    # never "..., | sir"
            return c.end()
    if stop is not None:
        return sm.end()
    done = list(re.finditer(r"\S+\s+", buf))
    for k in range(cap, cap + 4):                              # no clause in `cap` words: cut there, but not on "and", "the"...
        if len(done) < k:
            return None
        w = done[k - 1].group().strip(" ,.;:").lower()
        if k == cap + 3 or (w not in _WEAK and not re.fullmatch(r"[\d.,:%$]+", w)):
            return done[k - 1].end()
    return None


def split_long(t, limit=LONG_WORDS):
    """V9: a sentence over 25 words is cut at the comma nearest its middle (both halves 5+ words), never at a random word."""
    w = len(t.split())
    if w <= limit:
        return [t]
    best = None
    for m in re.finditer(r"[,;:](?=\s)", t):
        before = len(t[:m.end()].split())
        if before >= 5 and w - before >= 5 and (best is None or abs(before - w / 2) < abs(best[0] - w / 2)):
            best = (before, m.end())
    return [t] if best is None else split_long(t[:best[1]].strip(), limit) + split_long(t[best[1]:].strip(), limit)


def smooth_sentences_from(stream, collected):
    buf, first, n = "", True, first_words()
    cap = max(n, START_CAP) if n else 0                        # JarvisFirstWords=0: no early start, whole sentences only
    for piece in stream:
        buf += piece
        collected.append(piece)
        while True:
            if first and cap:
                end = first_cut(buf, cap)
                if end is None:
                    break
                out, buf, first = buf[:end].strip(), buf[end:], False
                if out:
                    yield out
                continue
            m = _sentence(buf)
            if not m:
                break
            first, buf = False, buf[m.end():]
            yield from split_long(m.group(1).strip())
    if buf.strip():
        yield from split_long(buf.strip())


def sentences_from(stream, collected):
    """Chunks of the streaming reply to speak. The FIRST chunk is released as soon as its Nth word is complete (or at
    the end of a shorter sentence), so he starts talking while the model is still writing; after that, whole sentences.
    JarvisVoiceSmooth=1: smooth_sentences_from instead (the first chunk ends at a clause, never leaves an orphan)."""
    if smooth_on():
        yield from smooth_sentences_from(stream, collected)
        return
    buf, first, n = "", True, first_words()
    for piece in stream:
        buf += piece
        collected.append(piece)
        while True:
            m = re.search(r"(.+?(?<!\bMr)(?<!\bMrs)(?<!\bMs)(?<!\bDr)(?<!\bProf)(?<!\bSt)(?<!\bvs)(?<!\betc)(?<!\be\.g)(?<!\bi\.e)[.!?])(\s+|$)", buf, re.I)
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
