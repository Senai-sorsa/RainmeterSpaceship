"""turnstate: moved verbatim from jarvis.py (refactor). See JARVIS-Repair-Plan.txt, REFACTOR."""
import re
import time
from .calc import clock


# ------------------------------------------------------------------ "undo that", "what did you hear?", "say that again"
UNDO_FOR = 120                                                # seconds
undo = []                                                     # [expires, what, before]: the last change, memory only
recent = {"you": "", "me": ""}                                # the last thing heard and said, memory only, never logged
offer = {}            # M4a-3: a fact he offered to remember {fact, expires}; memory only, never logged
last = {}             # M1b: the list he just read out or the one thing he acted on {kind, items, when}; memory only, never logged


# M4b: the last 20 actions really run (time, what, worked), memory only, never logged. Fed by run_action, can_undo
# (facts and reminders), snoozes and undo; questions about him get it in the prompt (DID_ASK).
did = []
DID = {"lock": "locked the PC", "sleep": "put the PC to sleep", "restart": "started a restart", "shutdown": "started a shutdown",
       "mute": "muted the sound", "unmute": "unmuted the sound", "volume": "changed the volume", "media": "pressed a media key",
       "todo": "added a to-do", "forget_all": "forgot all saved facts", "forget_talk": "forgot earlier talks",
       "forget_facts": "forgot saved facts", "replace_fact": "replaced a saved fact", "fact": "saved a fact",
       "forget": "forgot a saved fact", "cancel": "cancelled a reminder", "move": "moved a reminder", "flip": "moved a reminder to am or pm",
       "snooze": "snoozed a reminder", "undo": "undid the last change", "reminder": "set a reminder"}
DID_ASK = re.compile(r"\b(?:what (?:did|have|were) you (?:just )?(?:do|done|doing|run|change)|what actions|"
                     r"did you (?:\w+ )?(?:set|open|close|save|remember|change|cancel|mute|unmute|lock|add|turn|do|run|"
                     r"snooze|move|forget|undo|put)|have you (?:\w+ )?(?:set|opened|closed|saved|changed|cancelled|muted|"
                     r"done|run|added|locked|snoozed|moved|forgotten))\b", re.I)


def did_add(what, target=None, ok=True):
    line = DID.get(what, str(what).replace("_", " "))
    try:                                                       # an odd target never stops the action itself
        if what == "open":
            line = f"opened {target[0]}"                       # (name, path)
        elif what == "close":
            line = f"closed {target.replace('.exe', '')}"
        elif what == "reminder":                               # target: the reminders set, as the file stores them
            r = target[0]
            line = f"set {'a timer' if r[2] == 'timer' else 'an alarm' if r[3] == 'alarm' else 'a reminder'} for {clock(r[0])}"
    except (TypeError, IndexError, AttributeError, ValueError, OSError, OverflowError):
        pass
    did.append((time.time(), line, ok))
    del did[:-20]
