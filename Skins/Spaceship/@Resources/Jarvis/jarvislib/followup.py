"""followup: what his ear does after he has spoken (Phase 10B T2, T3). One place for the rule, so jarvis.py only asks.

  "ear"   after a chat or info answer, a fixed reply, a question: the open ear of S2-10 (direct window, then his name).
  "undo"  after a direct command (act, reminder, alarm, timer, a saved or forgotten fact): a short window in which only
          "undo" counts. Everything else is dropped without a word.
  "stop"  right after a stop word or the End key: one second, and what you say counts as a follow-up.
Typed turns, muted turns and JarvisFollowUp=0 never listen again (the caller checks those)."""
import time
from .base import log, setting, stopped
from .mic import follow_name_wait, follow_wait, listen
from .turnstate import offer, recent

UNDO_WAIT = 2.0                                                # seconds the ear stays open for "undo" after a command
STOP_WAIT = 1.0                                                # seconds it stays open after a stop
STOPS = ("stop word", "stop key")                              # a click or a barge-in is not "stop": the click starts a new turn
REMIND_CHANGES = ("set", "cancel", "move", "flip", "snooze")   # reminder actions that change something; "list" is a question
MEMORY_CHANGES = ("save", "forget")                            # memory actions that change something; a recall is an answer


def is_command(kind, action=None):
    """A direct command: it changes something, so the answer is "Done" and the only follow-up worth having is an undo."""
    if kind in ("act", "multi", "undo"):
        return True
    if kind == "remind":
        return action in REMIND_CHANGES
    return kind == "memory" and action in MEMORY_CHANGES


def mode_after(kind, action=None):
    """What stays open after a reply of this kind."""
    return "undo" if is_command(kind, action) else "ear"


def after_stop():
    """T3: "stop" while he spoke -> "stop" (listen one second), else None. A click or QUIT ends the turn as before."""
    why, when = stopped
    return "stop" if why in STOPS and time.time() - when < 3 else None


def ear_wait():
    """S2-10: the open-ear window after a reply: JarvisFollowUpWait (3 s); 8 s when he asked or offered something."""
    asked = (recent["me"] or "").rstrip().endswith("?") or time.time() < offer.get("expires", 0)
    return max(follow_wait(), 8.0) if asked else follow_wait()


def listen_for(mode, follow, woke):
    """Open the microphone for the window `mode` names. Returns (audio, wait): wait is the direct window in seconds."""
    if mode == "undo":
        return listen(patience=UNDO_WAIT), UNDO_WAIT
    if mode == "stop":
        return listen(patience=STOP_WAIT), STOP_WAIT
    wait = ear_wait()
    if follow:                                                 # 8a: the direct window, then only with his name, up to JarvisFollowNameWindow
        return listen(patience=max(wait, follow_name_wait()), dim_after=wait), wait
    return (listen(patience=10) if woke else listen()), wait   # a wake: 10 s for the first word


def only_undo(route_kind):
    """In the undo window only an undo counts; `route_kind` is route(...)[0] of what was heard."""
    ok = route_kind == "undo"
    if not ok:
        log("ear: not an undo - dropped")
    return ok
