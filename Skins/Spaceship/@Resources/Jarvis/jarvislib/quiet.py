"""8c quiet during class: while a timed event of the calendar named in JarvisQuietCalendar runs, he is QUIET (replies
and alarms are the HUD pop-up only, no sound, as in STEALTH). Reads calendar.txt (in Data), which the HUD already writes.
Event titles are never logged or spoken."""
import re
import time
from .base import log, read_kv, setting

EVENT = re.compile(r"^E (\d+)\|(\d+)\|(\d)\|([^|]*)\|", re.M)
TALK = re.compile(r"(?:you can (?:talk|speak)(?: now| again| normally)?|(?:talk|speak) normally|end quiet mode|quiet mode off)")
_off = [0]                                                     # end time of the event he was told he can talk in
_seen = [0]                                                    # end time of the event last logged
_cache = [0.0, False]                                          # when it was last read, the answer
typed = [False]                                                # a turn that came from the chat box is running: the answer is text only


def _current():
    """End time of the running timed event of the quiet calendar, or 0."""
    want = setting("JarvisQuietCalendar", "").strip().lower()
    if not want:
        return 0
    now = time.time()
    for m in EVENT.finditer(read_kv("calendar.txt")):
        if m.group(3) == "0" and int(m.group(1)) <= now < int(m.group(2)) and m.group(4).strip().lower() == want:
            return int(m.group(2))
    return 0


def now():
    """True while he is quiet. Also true for the length of a typed turn: what you type in the chat is answered in the chat,
    not out loud. (Not the same as in_class(): a typed turn is NOT class time, so it keeps its mood.)"""
    return True if typed[0] else in_class()


def in_class():
    """True while a QUIET calendar event is running. Read at most every 5 s: muted() asks on every sentence."""
    if time.time() - _cache[0] < 5:
        return _cache[1]
    end = _current()
    _cache[:] = [time.time(), bool(end) and end != _off[0]]
    if end and end != _seen[0]:
        _seen[0] = end
        log("quiet: class until " + time.strftime("%H:%M", time.localtime(end)))
    return _cache[1]


def talk():
    """"You can talk": end QUIET for the running event only. False if there is none."""
    end = _current()
    if end:
        _off[0] = end
        _cache[0] = 0.0
        log("quiet: ended by you for this class")
    return bool(end)
