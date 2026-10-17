"""reminders: moved verbatim from jarvis.py (refactor). See JARVIS-Repair-Plan.txt, REFACTOR."""
import os
import re
from datetime import datetime
from datetime import timedelta
from .base import DATA, log, problem, write_atomic
from .calc import WEEKDAYS, _num, _remind_bad, clock, unit


# ------------------------------------------------------------------ timers and reminders
# "remind me to cook in 20 minutes", "set a timer for 10 minutes", "what reminders do I have", "cancel the timer".
# All of it is read by the code below, never by the model. They are kept in Data\jarvis_reminders.txt (so they
# survive a restart) and ring only while JARVIS runs: a ding and the line, repeated until a stop word or a click.
# A repeating reminder keeps its rule in the kind field (daily | weekdays | mon ... sun), so the file format is the same.
REMIND_FILE = os.path.join(DATA, "jarvis_reminders.txt")      # due|created|kind|label  (kind: reminder | timer | a rule)
STOP_WORDS = re.compile(r"\b(stop|shush|shh+|shut ?up|quiet|enough|okay|ok|thanks|thank you|dismiss)\b", re.I)
RINGS = 10                                                    # each is a ding, the line, and up to 6 s of listening
SNOOZE = 300                                                  # seconds, when "snooze" is said with no length
ALARM_CAP = 300                                               # an alarm rings this long unanswered, then it is missed
ALARM_SAY = 30                                                # an alarm says its line again after this many seconds
NAME_ONLY = re.compile(r"\W*(?:(?:hey|hi|ok|okay)\W+)?jarvis\W*", re.I)   # said in a gap, it stops an alarm
DAYS = "mon tue wed thu fri sat sun".split()


def duration(s):
    """'10 minutes', 'an hour and a half', 'two minutes and 30 seconds' -> seconds, or None if it is not a duration."""
    s = re.sub(r"\b(?:an?|one) (hour|minute) and a half\b", lambda m: "90 " + ("minutes" if m.group(1) == "hour" else "seconds"),
               s.strip()).replace("half an hour", "30 minutes")
    s = re.sub(r"((?:sec|min|hour|hr)[a-z]*),? (?!and )", r"\1 and ", s)      # "1 hour 30 minutes" has no "and"
    total = 0
    for piece in s.split(" and "):
        m = re.fullmatch(r"(.+?)[ -]?(sec|min|hour|hr)[a-z]*", piece.strip())
        n = _num(m.group(1)) if m else None
        if n is None:
            return None
        total += n * {"sec": 1, "min": 60}.get(m.group(2), 3600)
    return total


def when(s, now):
    """'in 20 minutes', 'at 6:30 pm', 'at 18:30', 'at 7', 'at seven thirty in the morning', 'at 1900 hours',
    'at noon', 'at 9 tomorrow' -> the time it is due, or None. A clock time is its next occurrence; with no am / pm,
    'at 7' is whichever 7 o'clock comes first. 'hours', 'hundred' and a leading 0 mean the 24-hour clock."""
    s = s.strip().lower().rstrip(".")
    if s.startswith("in "):
        d = duration(s[3:])
        return None if d is None else now + d
    nxt = re.search(rf"\bnext ({'|'.join(WEEKDAYS)})\b", s)     # "next Friday" said on a Friday is a week away
    lead = re.fullmatch(rf"(?:on |next |this )*(tomorrow|today|{'|'.join(WEEKDAYS)}),?(?: at)? (.+)", s)
    if lead:                                                   # "tomorrow at 9", "on Friday at 9" -> "at 9 friday"
        s = f"at {lead.group(2)} {lead.group(1)}"
    if not s.startswith("at "):
        return None
    s = f" {s[3:]} "
    days = 1 if " tomorrow " in s else 0
    s = re.sub(r",? (?:tomorrow|today)(?: at)? ", " ", s)
    wd = re.search(rf",? (?:on )?(?:next |this |coming )?({'|'.join(WEEKDAYS)})(?: at)? ", s)
    if wd:                                                     # "Monday at 7": that day, at most 7 days ahead
        days = (WEEKDAYS.index(wd.group(1)) - datetime.fromtimestamp(now).weekday()) % 7
        s = s[:wd.start()] + " " + s[wd.end():]
    if nxt and days == 0:
        days = 7
    # "half past six", "quarter to 8", "ten past 7" -> 6:30, 7:45, 7:10
    q = re.match(r" (half|quarter|[a-z0-9 ]+?)(?: minutes?)? (past|after|to|till) ([a-z0-9]+) ", s)
    if q:
        mins, hr = {"half": 30, "quarter": 15}.get(q.group(1), _num(q.group(1))), _num(q.group(3))
        if mins is not None and hr is not None and 0 < mins <= 30 and mins == int(mins) and hr == int(hr) and 0 <= hr <= 23:
            back = q.group(2) in ("to", "till")
            hr = (int(hr) - 1 - back) % 12 + 1 if 1 <= hr <= 12 else (int(hr) - back) % 24     # "quarter to 1" is 12:45
            s = f" {hr}:{(60 - int(mins)) % 60 if back else int(mins):02d} " + s[q.end():]
    s = re.sub(r" o'?clock ", " ", s)
    s = re.sub(r" (?:in the |this )?morning ", " am ", s)
    s = re.sub(r" (?:(?:in the |this )?(?:afternoon|evening)|(?:at )?night|tonight) ", " pm ", s)
    s = re.sub(r" (?:12 )?noon ", " 12 pm ", s)
    s = re.sub(r" (?:12 )?midnight ", " 12 am ", s)
    m = re.fullmatch(r"(.+?) ?(?:([ap])\.? ?m\.?)?", s.strip())
    if not m:
        return None
    s, half = m.group(1), m.group(2)
    d = re.fullmatch(r"(\d{1,2})(?:[: .]?(\d{2}))?( hundred)?( hours)?", s)
    if d:
        if d.group(4) and not (d.group(2) or d.group(3)):
            return None                                        # "at 2 hours" is a wait, not a time
        hour, minute = int(d.group(1)), int(d.group(2) or 0)
        strict = bool(d.group(3) or d.group(4) or (len(d.group(1)) == 2 and d.group(1)[0] == "0"))
    else:
        ws = s.split()
        strict = bool({"hours", "hundred"} & set(ws))
        ws = [w for w in ws if w not in ("hours", "hundred")]
        if not ws or {"a", "an"} & set(ws):
            return None
        if strict and "hundred" in s:
            hour, minute = _num(" ".join(ws)), 0               # "nineteen hundred"
        else:
            hour = _num(ws[0])
            minute = _num(" ".join(ws[1:])[3:] if ws[1:2] == ["oh"] else " ".join(ws[1:])) if ws[1:] else 0
        if hour is None or minute is None or hour != int(hour) or minute != int(minute):
            return None
        hour, minute = int(hour), int(minute)
    if minute > 59 or hour > 23 or (half and not 1 <= hour <= 12) or (half and strict):
        return None
    hours = [hour % 12 + (12 if half == "p" else 0)] if half else [hour] if strict or not 1 <= hour <= 12 else [hour, (hour + 12) % 24]
    day = datetime.fromtimestamp(now).replace(minute=minute, second=0, microsecond=0)
    if days or wd:                                             # "tomorrow", "Friday": that day's first match, no rolling on
        day += timedelta(days=days)
        ts = [day.replace(hour=h).timestamp() for h in hours]
        # today's own weekday with its time gone: the same day next week
        return min([t for t in ts if t > now] or [(day + timedelta(days=7)).replace(hour=h).timestamp() for h in hours])
    # gone today: the same clock time tomorrow (a calendar day, so a daylight-saving change cannot shift it an hour)
    return min((d if d.timestamp() > now else d + timedelta(days=1)).timestamp() for d in (day.replace(hour=h) for h in hours))


def span(sec, s="s"):
    """600 -> '10 minutes'; with s='' it is '10 minute' (as in "your 10 minute timer")."""
    sec = int(round(sec))
    parts = ((sec // 3600, "hour"), (sec % 3600 // 60, "minute"), (sec % 60, "second"))
    return " ".join(f"{n} {unit}{s if n != 1 else ''}" for n, unit in parts if n) or "0 seconds"


def snooze_for(heard):
    """What was said while it rang -> None (not a snooze), the seconds to wait, or 0 for a length he cannot use
    (under a minute, over 2 hours, or not understood: it keeps ringing)."""
    s = re.sub(r"[^a-z0-9. ]+|\.(?!\d)", " ", heard.lower())
    if not re.search(r"\b(?:snooze|later|not now|again in)\b|\bmore (?:sec|min|hour)|\b(?:sec|min|hour)\w* more\b", s):
        return None
    rest = " ".join(w for w in s.split() if w not in ("snooze", "later", "not", "now", "more", "for", "in", "again", "it", "ok",
                                                      "okay", "another", "please", "jarvis"))
    if not rest:
        return SNOOZE
    d = duration(rest)
    if d is None:
        n = _num(rest)                                         # a bare number ("again in ten", "snooze for 10") = minutes
        d = n * 60 if n is not None else None
    return d if d and 60 <= d <= 7200 else 0


def next_due(due, kind, now):
    """The next time a repeating reminder rings after `now`: the same clock time, on a day its rule allows. Stepped on
    the wall clock, so "9" stays 9 across a daylight-saving change."""
    d = datetime.fromtimestamp(due)
    while d.timestamp() <= now or not (kind == "daily" or (d.weekday() < 5 if kind == "weekdays" else DAYS[d.weekday()] == kind)):
        d += timedelta(days=1)
    return d.timestamp()


def repeats(kind, due):
    """'every day ' / 'every weekday ' / 'every Monday ' for a repeating kind, '' for a single reminder or a timer."""
    return {"reminder": "", "timer": "", "daily": "every day ", "weekdays": "every weekday "}.get(
        kind, datetime.fromtimestamp(due).strftime("every %A "))


def split_time(rest, now):
    """'to cook in 20 minutes' or 'in 20 minutes to cook' -> (due, label, the time as said). No time in it: due is None."""
    for m in re.finditer(r"\b(?:in|at) ", rest):               # the time comes last
        label, said = rest[:m.start()], rest[m.start():]
        day = re.search(rf"(?:^|\s)(?:on |next |this )*(tomorrow|today|{'|'.join(WEEKDAYS)}),?\s*$", label) if said[:3] == "at " else None
        if day:                                                # "to call mom tomorrow at 9": the day is part of the time
            label, said = label[:day.start()], f"{said} {day.group(1)}"
        due = when(said, now)
        if due is not None:
            return due, label.strip(), said
    for m in re.finditer(r" (?=(?:to|about|that|for) )", rest):   # the time comes first
        due = when(rest[:m.start()], now)
        if due is not None:
            return due, rest[m.end():].strip(), rest[:m.start()]
    return None, rest.strip(), ""


def reminder_cmd(t, cmd, now):
    """A timer or reminder command -> ("list", kind) | ("cancel", kind, words) | ("set", kind, due, label, time as said);
    anything else -> None. due is None when no time was heard (he then asks)."""
    # alarms are saved as reminders labelled "alarm": kind "alarm" would read as a weekly rule (repeats, next_due)
    # "can you tell me if i have any alarms..." is "do i have any alarms...": by rule, never the model
    t = re.sub(r"^(?:(?:can|could|would|will) you (?:please )?)?(?:tell me|check|see|let me know|find out) (?:if|whether) (?=i have )",
               "do ", t)
    if re.match(r"(?:do i have|have i (?:got|set)|(?:what|which)(?: are)?|what time(?:'s| is)|(?:list|show)(?: me)?|when(?:'s| is)|"
                r"how long (?:until|till|before)|is|are there|is there|any) (?:an? |any |all |my |the |next )*alarms?\b", t):
        return ("list", "alarm")
    # "move my alarm to 8", "change the 7 am alarm to 8", "make the timer 10 minutes", "add 5 minutes to the timer":
    # (words that say which one, the new time; or for "add", None and the seconds added). No time read: not this
    m = re.match(r"(?:change|move|push|reschedule|switch|shift|update) (?:(?:the|my|that) )+(?:(.+?) )?(alarm|reminder) "
                 r"(?:to|for|until|till) (.+)$", cmd)
    if m:
        due = next((d for d in (when(s, now) for s in (m.group(3), "at " + m.group(3))) if d is not None), None)
        return None if due is None else ("move", m.group(2), m.group(1) or "", due, 0)
    m = (re.match(r"(?:make|change|reset|update) (?:(?:the|my|that) )+(?:(.+?) )?timer (?:to |for |into )?(.+)$", cmd)
         or re.match(r"(add) (.+?) (?:to|onto|on to) (?:(?:the|my|that) )+(?:(.+?) )?timer$", cmd))
    if m:
        add = m.group(1) == "add"
        secs = duration(m.group(2))
        return None if secs is None else ("move", "timer", (m.group(3) if add else m.group(1)) or "",
                                          None if add else now + secs, secs if add else 0)
    # "cancel the alarm", "remove my 7 am alarm", "cancel the alarm for 7": the words left say which one (a clock time)
    m = re.match(r"(?:cancel|delete|remove|clear|stop|turn off|forget) (?:(?:all|every|both|the|my|that|of) )*(?:(.+?) )?alarms?"
                 r"(?: (?:for|at) (.+?))?(?: (?:that )?i (?:set|made))?$", cmd)
    # "cancel all alarms", "cancel both", "turn off my alarms": the whole schedule. A plural with other words is by those
    every = "all " if re.search(r"\b(?:all|every|both)\b", cmd) else ""
    plural = "all" if re.search(r"\b(?:alarm|reminder|timer)s\b", cmd) else ""
    if m:
        return ("cancel", "alarm", f"{every}{m.group(1) or ''} {m.group(2) or ''}".strip() or plural)
    m = re.match(r"((?:set|create|make|add)(?: me| up)? (?:an? |my |the |another |some )?alarms?|i (?:need|want) (?:an? )?alarm|"
                 r"alarm|wake me(?: up)?)(?: for| at)?(?: (.+))?$", cmd)
    if m:
        rest = re.sub(r" from now$", "", m.group(2) or "")
        for said in (rest, "at " + rest, "in " + rest):       # "in one minute", "7 am", "one minute"; "at" before "in"
            due = when(said, now) if rest else None
            if due is not None:
                return ("set", "alarm", due, "alarm", said)
        parts = re.split(r",? and |, ", rest)                  # "7 and 8 am": the am / pm said last is for each
        half = re.search(r" ?(?:[ap]\.? ?m\.?|in the (?:morning|afternoon|evening)|tonight|at night)$", parts[-1])
        if len(parts) > 1:
            dues = [when("at " + (p if half is None or re.search(half.re, p) else p + half.group()), now) for p in parts]
            if None not in dues:
                return ("set", "alarm", dues, "alarm", "at " + rest)
        if not m.group(1).startswith(("alarm", "wake")) and not rest:
            return ("set", "alarm", None, "alarm", "")        # he asks when
    m = re.match(r"(?:(?:what|which) (?:are )?(?:my |the )?|(?:list|show|read)(?: me| out)? (?:all )?(?:my |the )?|"
                 r"do i have (?:any )?|how (?:much time|long) (?:is |do i have )?left on (?:my |the )?(?:\S+ )?)(reminder|timer)s?"
                 r"(?: (?:do i have|have i (?:got|set)|are (?:set|there|left|pending|running)).*)?$", t)
    if m:
        return ("list", m.group(1))
    if re.fullmatch(r"how (?:much time|long) is left", t):
        return ("list", "timer")
    m = re.match(r"(?:cancel|delete|remove|clear|stop|forget) (?:(?:all|every|both|of|the|my|that) )*(?:(.+) )?(reminder|timer)s?"
                 r"(?: (?:to|about|for) (.+))?$", cmd)
    if m:
        return ("cancel", m.group(2), f"{every}{m.group(1) or ''} {m.group(3) or ''}".strip() or plural)
    m = re.match(r"(?:remind me|(?:set|add) (?:a |another )?reminder)(?: (.+))?$", cmd)
    if m:
        if re.match(r"(what|who|how|why|where|when|which|whether|if) ", m.group(1) or ""):
            return None                                        # "remind me what the capital is": a question for the model
        rest, kind = m.group(1) or "", "reminder"
        rep = re.search(r"\bevery ?(day|week ?day|(?:mon|tues|wednes|thurs|fri|satur|sun)day)s?\b ?", rest)
        if rep:                                                # "every day at 9", "every weekday", "every Monday"
            kind = "daily" if rep.group(1) == "day" else "weekdays" if rep.group(1).startswith("week") else rep.group(1)[:3]
            rest = (rest[:rep.start()] + rest[rep.end():]).strip()
        due, label, said = split_time(rest, now)
        if rep and due is not None:
            due = next_due(due, kind, now)
        if label and not re.match(r"(to|about|that) ", label):
            label = "about " + re.sub(r"^(for|of) ", "", label)
        return ("set", kind, due, re.sub(r"\bmy\b", "your", label), said)
    m = re.match(r"(set |start |create |put on |give me )?(?:a |an |another |the )?(?:(.+?)[ -])?timer(?: (?:for|of) (.+))?$", cmd)
    if not m:
        return None
    verb, before, after = m.groups()
    if before and " and " in before:                           # "set an alarm for 7 and set a timer": two commands
        return None
    if after and " and " in after and duration(after) is None:     # "5 minutes and mute": the router splits it
        return None
    secs, label = (duration(before) if before else None), ""
    if before and secs is None:
        if not verb:                                           # "open timer", "what is a timer": not a command for this
            return None
        label = before                                         # "set a pasta timer for 10 minutes"
    for piece in (after or "").split(" for "):           # "the pasta for 10 minutes" or "10 minutes for the pasta"
        d = duration(piece) if secs is None else None
        if d is None:
            label = f"{label} {piece}".strip()
        else:
            secs = d
    return ("set", "timer", None if secs is None else now + secs, re.sub(r"\bmy\b", "your", label), "in")


def load_reminders():
    """[(due, created, kind, label)], soonest first. A file that cannot be read raises OSError / ValueError: an error
    is not "no reminders", and the caller must then leave the file alone."""
    if not os.path.exists(REMIND_FILE):
        return []
    out = []
    with open(REMIND_FILE, "r", encoding="utf-8") as f:
        for line in f.read().splitlines():
            if line.strip():
                due, created, kind, label = line.split("|", 3)
                out.append((float(due), float(created), kind, label))
    return sorted(out)


def save_reminders(items):
    # one reminder per line: a line break in a label would split it and stop every reminder on the next load
    write_atomic(REMIND_FILE, "".join(f"{due:.0f}|{created:.0f}|{kind}|{' '.join(label.split())}\n"
                                      for due, created, kind, label in items))


def describe(r, now):
    due, created, kind, label = r
    if kind == "timer":
        return f"{span(due - now)} left on the timer" + (f" for {label}" if label else "")
    if repeats(kind, due):
        return f"{label or 'a reminder'}, {repeats(kind, due)}at {clock(due, due)}"
    return f"{label or 'a reminder'} at {clock(due, now)}"


def ring_line(r, now):
    """What he says when it is due: your own words back ("Time to cook."), not something the model wrote."""
    due, created, kind, label = r
    if kind == "timer":
        line = f"Your timer for {label} is done." if label else f"Your {span(due - created, '')} timer is done."
    elif label == "alarm":
        line = "This is your alarm."
    elif label.startswith("to "):
        line = f"Time {label}."
    else:
        line = f"Reminder: {label[5:]}." if label.startswith("that ") else f"Reminder {label}." if label else "This is your reminder."
    if now - due > 120:                                        # the PC slept, or JARVIS was not running
        return f"Missed {'timer' if kind == 'timer' else 'alarm' if label == 'alarm' else 'reminder'} from {clock(due, now)}: {line[0].lower()}{line[1:]}"
    return line


def find_items(pool, said, kind, now):
    """The items of `pool` that `said` points at, and the words that pointed: by clock time, else by words, else (no
    words) the asked kind first. Timers go by words only."""
    # shortcut: a word matches on its first four letters ("cooking" finds "to cook"); fine for a list of 20
    words = [w for w in said.split() if w not in ("the", "my", "a", "an", "one", "to", "about", "for", "at", "all")]
    found = [r for r in pool if all(w[:4] in f"{r[3]} {span(r[0] - r[1], '')}" for w in words)]
    if kind != "timer" and not said.startswith("all"):
        own = [r for r in pool if (r[2:] == ("reminder", "alarm")) == (kind == "alarm")]
        at = when("at " + " ".join(words), now) if words else None
        if at:                                                 # by clock time; "7" with no am / pm is either 7
            hhmm = lambda ts: datetime.fromtimestamp(ts).strftime("%H:%M")
            half = re.search(r"\b(?:[ap]\.? ?m\b|morning|afternoon|evening|tonight|night|noon|midnight|hours|hundred)", said)
            times = {hhmm(at)} | (set() if half else {hhmm(at + 43200)})
            found = [r for r in pool if hhmm(r[0]) in times]
        elif not words:                                        # "cancel the reminder": its own kind first, else the other
            found = own or pool
        elif not found and len(own) == 1:                      # "cancel the morning alarm" with one alarm: that one
            found = own
    return found, words


rang = []                                                     # [when the ringing stopped, what rang]: for a later "snooze"


def snoozed(due, again):
    """What rang, back in the schedule once at `again` (a repeating one keeps its own series)."""
    return [(again, r[1] + again - r[0], "timer" if r[2] == "timer" else "reminder", r[3]) for r in due]


def due_reminders(now):
    """True when something is due. An unreadable file is reported once, and nothing rings until it can be read."""
    try:
        items = load_reminders()
    except (OSError, ValueError) as e:
        if not _remind_bad[0]:
            _remind_bad[0] = True
            log(f"reminders: the file cannot be read ({type(e).__name__})")
            problem("Can't read Data\\jarvis_reminders.txt - reminders are paused until it is fixed or deleted", popup=False)
        return False
    _remind_bad[0] = False
    return bool(items) and items[0][0] <= now
