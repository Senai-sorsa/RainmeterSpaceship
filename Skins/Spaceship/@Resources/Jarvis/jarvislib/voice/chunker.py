"""voice/chunker: how a streaming reply is cut into pieces to speak (moved verbatim from speech.py, refactor phase 3).
Pure text work: no audio, no device. Depends on player.smooth_on() only to pick the chunker."""
import re
from ..base import setting
from .player import smooth_on


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
