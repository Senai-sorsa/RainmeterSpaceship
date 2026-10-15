"""meaning: moved verbatim from jarvis.py (refactor). See JARVIS-Repair-Plan.txt, REFACTOR."""
import re
from .base import log


# Matching by meaning (the user, 2026-10-14): a shared word OR a close meaning counts, in 6a, M1, M2 and M4a. The model
# is ChromaDB's local all-MiniLM-L6-v2; until it is loaded, or without ChromaDB, matching is by words only.
# Measured 2026-10-14: related pairs 0.39-0.53, unrelated 0.02-0.18; about 30 ms a sentence on the CPU.
MEANING_TALK = 0.35        # talk and facts (M1, M2, M4a)
MEANING_BLOCK = 0.6        # 6a, a lot stricter (the user): only close to one of the block's example questions
_embed = [None]            # the model, set by load_meaning() on a thread at startup
_vecs = {}                 # text -> unit vector, so each line is embedded once
STAMP = re.compile(r"^\[[^\]]*\] ")   # the time stamp fixed() puts on a history line


def vec(text):
    v = _vecs.get(text)
    if v is None:
        if len(_vecs) > 1000:                                 # warm-up alone is ~300 + gist lines; ~12 KB each
            _vecs.clear()
        raw = [float(x) for x in _embed[0]([text])[0]]
        n = sum(x * x for x in raw) ** 0.5 or 1.0
        v = _vecs[text] = [x / n for x in raw]
    return v


def closeness(text, others):
    """How close text is in meaning to the nearest of `others` (cosine); 0.0 while the model is off."""
    if _embed[0] is None or not others:
        return 0.0
    try:
        q = vec(STAMP.sub("", text))
        return max(sum(a * b for a, b in zip(q, vec(STAMP.sub("", o)))) for o in others)
    except Exception as e:
        log(f"meaning match failed, words only: {e!r}")
        return 0.0


def meaning(text, others, floor):
    """Whether text means about the same as any of `others` (cosine >= floor). False while the model is off."""
    return closeness(text, others) >= floor
