"""pardon: the model sometimes opens with "Pardon sir, what did you say?" for words that were perfectly clear (insults, jokes,
"what did I ask you?"). When the words were clear (typed, or Whisper was confident), that opening is not allowed to stand:
the question is asked once more with a firm hint, and the second answer is used. Real gibberish may still get the "Pardon".
Only the start of the stream is looked at (the first sentence), so the first words out are not delayed."""
import re

from ..base import log

NUDGE = ("\nThe user's last words were heard clearly. Answer them directly and briefly, in character. Do not ask them to repeat "
         "or say what you did not catch. Only if they are truly meaningless gibberish may you say \"Pardon sir, what did you say?\".")
_ASK = re.compile(r"\W*(?:pardon|i beg your pardon|excuse me|sorry)\b[^.!]*(?:\?|what did you say|say that again|repeat)|"
                  r".*\bwhat did you say\b|.*\bdidn'?t (?:catch|hear)\b|.*\bcould you (?:repeat|say that again)\b", re.I | re.S)


def asks_again(opening):
    """True when the start of an answer asks the user to repeat himself."""
    return bool(_ASK.match(opening or ""))


def no_pardon(make_stream, messages, clear):
    """The pieces of make_stream(messages); the model is called right away, as before. If `clear` and the answer opens by asking
    to repeat, the model is asked once more with NUDGE added to the system message (a copy: `messages` is never changed) and
    that answer is used instead."""
    stream = make_stream(messages)
    if not clear or not hasattr(stream, "__iter__"):
        return stream                                          # unchanged: the same object the caller always got
    return _watch(stream, make_stream, messages)


def _watch(stream, make_stream, messages):
    it, head = iter(stream), []
    for piece in it:
        head.append(piece)
        opening = "".join(head)
        if len(opening) >= 40 or re.search(r"[.!?]", opening):
            break
    opening = "".join(head)
    if not asks_again(opening):
        yield from head
        yield from it
        return
    close = getattr(stream, "close", None)
    if close:
        close()                                                # stop the first answer (Ollama stops with the connection)
    log("pardon: the words were clear - answered again")
    again = [dict(m) for m in messages]
    again[0]["content"] = again[0]["content"] + NUDGE
    yield from make_stream(again)
