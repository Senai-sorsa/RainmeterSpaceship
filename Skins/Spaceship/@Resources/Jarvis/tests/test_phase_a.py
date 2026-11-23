"""Phase A fixes (2026-11-22), as pure-function checks (no model, no audio, no Windows calls): small talk is not a recap (A3),
a whole-command correction (A4), "format" needs a drive word (A10), "make it 50" follows the timer or volume just changed (A11)."""
import os
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.argv[1:] = [tempfile.mkdtemp()]                            # temp RES: no real Settings.inc, no real jarvis.log

from jarvislib import routing, turnstate  # noqa: E402

# A3: "what did you do" about your weekend is small talk; about the last action it is a recap
for s in ("what did you do last weekend", "what were you doing yesterday", "what did you do for fun", "what have you done this week"):
    assert not turnstate.DID_WHAT.search(s), s
for s in ("what did you just do", "what did you do", "what did you change", "what actions"):
    assert turnstate.DID_WHAT.search(s), s

# A4: a correction that is a whole command replaces the first one; a number still replaces the number
assert routing.route("set volume to 30, no, mute")[:2] == ("act", "mute")
assert routing.route("set the volume to 30, no, 40")[2] == ("set", 40)

# A10: formatting text is not an order to wipe a drive; formatting a drive still is
for s in ("format the paragraph", "format my resume", "how do I format my resume", "format this document"):
    assert routing.route(s)[0] != "guard", s
for s in ("format the c drive", "format c", "format my hard drive", "format my laptop", "format the disk", "format d:"):
    assert routing.route(s)[0] == "guard", s

# A11: "make it 50" with nothing just changed is for the model; after a timer it moves the timer, after a volume change it sets volume
turnstate.undo[:] = []
assert routing.route("make it 50")[0] == "chat"
now = time.time()
turnstate.undo[:] = [now + 60, "reminder", [(now + 300, now, "timer", "")]]
r = routing.route("make it 50")
assert r[:2] == ("remind", "move") and r[2][0] == "timer" and abs(r[2][2] - (time.time() + 50 * 60)) < 5, r
turnstate.undo[:] = [now + 60, "volume", 30]
assert routing.route("make it 50")[:3] == ("act", "volume", ("set", 50))
turnstate.undo[:] = [now - 1, "volume", 30]                    # expired: no context any more
assert routing.route("make it 50")[0] == "chat"
turnstate.undo[:] = []

# E3 "cancel that" family: "scratch that" undoes the last action like "cancel that" (it went to the model before)
for s in ("scratch that", "no, scratch that", "cancel that", "take that back"):
    assert routing.route(s)[0] == "undo", s
assert routing.route("scratch that off my list")[0] != "undo"

# E1: a closing phrase ends the conversation silently; thanks alone and "I'm good" (an answer to "how are you") stay chat
for s in ("that's all", "that's all for now", "we're done", "stop listening", "goodbye", "bye", "no thanks", "nothing else",
          "Okay, thanks, that's all.", "That's all, Jarvis.", "No, I'm good.", "no that's it"):
    assert routing.route(s)[0] == "end", s
for s in ("thanks", "thank you", "i'm good", "is that all you can do", "that's it for the timer", "say goodbye to my mom",
          "we're done with the essay, what next", "that's everything I need to know about rome"):
    assert routing.route(s)[0] != "end", s

print("test_phase_a: OK")
