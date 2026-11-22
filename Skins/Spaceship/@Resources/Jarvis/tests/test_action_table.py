"""The action table (refactor phase 7): every row can be trusted by the rest of the code. Only rows here can ever run; risk is
code's decision (never the model's); every action that can happen is also something he can later say he did (turnstate.DID).
Exemptions are written down, not silent. Needs no audio and never calls an action."""
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.argv[1:] = [tempfile.mkdtemp()]                            # temp RES: no real settings, no real log

from jarvislib.routing import ACTION_TABLE, ACTIONS  # noqa: E402
from jarvislib.turnstate import DID  # noqa: E402

# built from the target inside did_add(), so no fixed text is needed
BUILT_FROM_TARGET = {"open", "close"}
# KNOWN GAP (found 2026-11-03, left as is: a refactor does not change what he says): did_add("mood") falls back to the bare word
# "mood" because DID has no sentence for it. Fix = add DID["mood"] = "changed his mood" in turnstate.py, in its own commit.
KNOWN_NO_DID = set()                                       # "mood" had none; turnstate.DID["mood"] fixed it
# things that are in DID but are not table actions: reminders, memory and undo, logged by their own code
NOT_ACTIONS = {"cancel", "fact", "flip", "forget", "move", "reminder", "snooze", "undo"}

assert ACTION_TABLE and set(ACTIONS) == set(ACTION_TABLE), "ACTIONS must be derived from ACTION_TABLE"
for name, a in ACTION_TABLE.items():
    assert callable(a.run), name
    assert a.risk in ("read", "change", "ask"), (name, a.risk)
    assert a.desc and a.desc == a.desc.strip(), (name, "needs a description")
no_did = {n for n in ACTION_TABLE if n not in DID} - BUILT_FROM_TARGET
assert no_did == KNOWN_NO_DID, f"actions without a DID sentence: {sorted(no_did)} (add one, or list the exemption with its reason)"
assert {k for k in DID if k not in ACTION_TABLE} == NOT_ACTIONS, sorted(k for k in DID if k not in ACTION_TABLE)
danger = {"lock", "sleep", "restart", "shutdown", "close", "recycle", "forget_all", "forget_facts", "replace_fact"}
assert all(ACTION_TABLE[n].risk == "ask" for n in danger if n in ACTION_TABLE), "a destructive action must be an 'ask' row"
print(f"action table: {len(ACTION_TABLE)} actions, risks {sorted({a.risk for a in ACTION_TABLE.values()})}, "
      f"{len(KNOWN_NO_DID)} documented gap: OK")
