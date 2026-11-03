"""Every fixed ("canned") line JARVIS says from code, in one registry (refactor phase 2).

register(key, text) returns the text, so modules keep their old names (`CLAIM_LINE = ...` is imported from here and
re-exported by routing.py, mood.py, prompt.py, memory.py, diag.py). FIXED_LINES, the set mood.polish() passes through
untouched, is DERIVED from the entries registered with passthrough=True: never add to it by hand.
No imports from jarvislib on purpose (mood, routing and prompt import this module)."""

LINES = {}                     # key -> text
FIXED_LINES = set()            # derived: texts registered with passthrough=True


def register(key, text, passthrough=False):
    if LINES.get(key, text) != text:
        raise ValueError(f"fixed line {key!r} registered twice with different text")
    LINES[key] = text
    if passthrough:
        FIXED_LINES.add(text)
    return text


# routing.py: the claim / promise filters and the router's own lines
NEAR_MISS = register("near_miss", "Could you say that again?")
CLAIM_LINE = register("claim", "I didn't catch that as a command, so nothing changed. Say it again, like: set an alarm for 7 AM.",
                      passthrough=True)
CANT = register("cant", "I can't do that yet.")
CANT_LINE = register("cant_promise", "I can't do that from here, sir.", passthrough=True)
# mood.py: crisis words, and a made-up reading in a chat answer
CRISIS_LINE = register("crisis", "Mr. Sorsa, I'm really sorry you're feeling this way. Please call or text 988 right now, the Suicide and "
                                 "Crisis Lifeline, or reach out to someone you trust. You don't have to go through this alone.")
NO_READING = register("no_reading", "I don't have that reading right now, sir.", passthrough=True)
# prompt.py: live-internet questions while offline
LIVE_FACT_LINE = register("live_fact", "I can't look that up yet.")
# memory.py / diag.py: a file he cannot read
MEMORY_BAD = register("memory_bad", "I can't read my memory file, so I left it alone.")
TOPICS_BAD = register("topics_bad", "I can't read my topic memory, so I left it alone.")
NO_TALK = register("no_talk", "I don't remember us talking about that.")
COULDNT = register("couldnt", "I couldn't read that.")
# jarvis.py: results of a command, confirmations and small control replies
DONE = register("done", "Done.")
FAILED = register("failed", "That didn't work.")
OKAY = register("okay", "Okay.")
ADDED = register("added", "Added.")
CANCELLED = register("cancelled", "Cancelled.")
HOW_LONG = register("how_long", "How long?")
WHEN = register("when", "When?")
NOTHING_WAITING = register("nothing_waiting", "There's nothing waiting for a yes, sir.")
NOT_QUIET = register("not_quiet", "I'm not in quiet mode.")
CAN_TALK = register("can_talk", "Okay, I can talk.")
CLOSING_LOG = register("closing_log", "Closing the log.")
ALL_SAID = register("all_said", "Here's everything we've said.")
DIAG_OFF = register("diag_off", "Diagnosis is off.")
GPU_OFF = register("gpu_off", "My graphics card is off.")
ASK_REMEMBER = register("ask_remember", "Want me to remember that?")
ASK_CLOSE = register("ask_close", "Want me to close it?")
THEME_MIXED = register("theme_mixed", "It was mixed before, so I can't put that back.")
MIC_DEFAULT = register("mic_default", "Back to the Windows default microphone.")
HEARD_NOTHING = register("heard_nothing", "I haven't heard anything yet.")
SAID_NOTHING = register("said_nothing", "I haven't said anything yet.")
