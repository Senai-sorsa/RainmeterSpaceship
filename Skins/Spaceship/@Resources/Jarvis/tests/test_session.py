"""session.reset_turn_state() (refactor phase 5): every conversation container is cleared, in place (the same objects, so every
module that imported them sees the reset), and nothing outside its list is touched."""
import os
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.argv[1:] = [tempfile.mkdtemp()]                            # temp RES: no real Settings.inc, no real jarvis.log

from jarvislib import hearing, mood, session, turnstate  # noqa: E402

ids = [id(x) for x in (turnstate.offer, turnstate.last, turnstate.recent, turnstate.undo, turnstate.did, mood.state)]
turnstate.offer["fact"] = "x"
turnstate.last["kind"] = "app"
turnstate.recent.update(you="hi", me="hello")
turnstate.undo.append([time.time() + 60, "volume", 30])
turnstate.did_add("lock")
mood.state["temp"] = ("dry", time.time() + 600)
mood.state["left"] = 3
hearing.heard_score[0] = -2.0

session.reset_turn_state()

assert not turnstate.offer and not turnstate.last and not turnstate.undo and not turnstate.did
assert turnstate.recent == {"you": "", "me": ""}, turnstate.recent
assert mood.state["temp"] is None and mood.state["left"] == 0, mood.state
assert hearing.heard_score[0] == 0.0
assert ids == [id(x) for x in (turnstate.offer, turnstate.last, turnstate.recent, turnstate.undo, turnstate.did, mood.state)], \
    "reset must clear in place, not rebind"
print("session reset: all containers cleared in place: OK")
