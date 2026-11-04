"""voice/pacing: which pieces become one clip, and where the text asks for a pause (moved verbatim from speech.py,
refactor phase 3). No audio, no device."""
import queue
import re
import threading
from ..base import cancel


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
