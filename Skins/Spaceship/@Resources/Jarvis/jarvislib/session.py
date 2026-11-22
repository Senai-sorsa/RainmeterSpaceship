"""session (refactor phase 5): the conversation state that lives in module-level containers, with ONE reset.

Before this, tools/semi_live.py and tools/golden_common.py each copied the same six clear() lines, so a new container
would have been added in one place and forgotten in the other. reset_turn_state() clears: the mood and its timed override
(mood), the offer / last-list / recent / undo / did memories (turnstate) and Whisper's unsure score (hearing).
It does NOT touch jarvis.py's own `history`, `last_turn`, `cancel`, `busy`, `turn_id` (they stay with the turn driver) and
never deletes files. The product does not call it: a live conversation is never reset, only a test run is."""
from . import mood, turnstate


def reset_turn_state():
    from . import hearing                                      # heavy import: only when a reset is asked for
    mood.reset()
    mood.state["temp"] = None
    for d in (turnstate.offer, turnstate.last):
        d.clear()
    turnstate.recent.update(you="", me="")
    turnstate.undo.clear()
    turnstate.did.clear()
    hearing.heard_score[0] = 0.0
