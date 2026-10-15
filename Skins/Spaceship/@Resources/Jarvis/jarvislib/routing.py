"""routing: moved verbatim from jarvis.py (refactor). See JARVIS-Repair-Plan.txt, REFACTOR."""
import os
import re
import time
from dataclasses import dataclass
from datetime import datetime
from .actions import MEDIA_KEYS, act_close, act_lock, act_mic_level, act_open, act_sleep, act_volume, best_app, press_key, run_ok, running_window, start_apps
from .audio import mic_volume, speakers_mute
from .base import log, setting, todo_note
from .calc import _num, fact_answer
from .confirm import DANGER, NAMES
from .llm import chat_json
from .memory import ACTIVE_TTL, MEMORY_BAD, fact_save, facts_about, load_gist, load_memory, load_topics, save_gist, save_memory, save_topics, talk_forget, talk_list
from .reminders import reminder_cmd, snooze_for
from .todo import act_todo
from .turnstate import last, undo


# ------------------------------------------------------------------ AI fallback for a command the patterns missed
# The model only names the intent and copies your words. Code checks every word was said and the intent's own word is
# in what you said, builds one fixed sentence, and route() must read it as that command; then the usual code runs it.
# Lock, sleep, restart, shutdown, open, close, memory and to-do are not on its list: those stay pattern-only.
AI_CUES = {"alarm_set": r"alarm|wake|woken|get me up", "reminder_set": r"remind|ping me|heads.?up", "timer_set": r"timer",
           "schedule_list": r"alarm|remind|timer|schedul", "schedule_cancel": r"alarm|remind|timer|schedul",
           "volume_set": r"volume|sound|audio|speaker|music", "volume_step": r"volume|sound|audio|speaker|music|louder|quieter|quiet|soft|softer|loud|crank|turn (?:it|that|this) (?:up|down)",
           "volume_level": r"volume|sound|loud|muted", "mute": r"mute|silen", "unmute": r"unmute|sound|audio|speaker",
           "media": r"pause|resume|skip|next (?:song|track)|previous|song|track|music"}
AI_DOWN = re.compile(r"\b(?:down|lower|quieter|softer|less|decrease|reduce)\b|\b(?:too loud|be quiet)\b")   # which way a step goes
AI_UP = re.compile(r"\b(?:up|louder|raise|more|increase|boost|crank)\b|\btoo (?:quiet|soft)\b|\bcan'?t hear\b|\bbarely hear\b")
AI_WORDS = re.compile(r"\b(?:" + "|".join(AI_CUES.values()) + ")")
AI_NOT = re.compile(r"(?:how|why|what|when|who|where|which|whose|should|shall|is|are|was|were|do|does|did|has|had)\b|"
                    r".*\b(?:yesterday|earlier|ago|last (?:night|week)|explain|tell me about)\b")
AI_SCHEMA = {"type": "object", "properties": {"commands": {"type": "array", "items": {"type": "object", "properties": {
    "intent": {"type": "string", "enum": list(AI_CUES) + ["chat"]}, "when": {"type": "string"}, "label": {"type": "string"},
    "number": {"type": "integer"}}, "required": ["intent"]}}}, "required": ["commands"]}
AI_PROMPT = """You sort what the user said to a voice assistant into commands. Output JSON only.
RULE 1: a question is "chat". Anything asking how, why or should, any opinion, anything about the past, and talk ABOUT
alarms, timers or volume is "chat". Only an order to do something now is a command. Anything not listed below is "chat".
RULE 2: "when" is copied word for word from the user, including "in"/"at"/"for", and nothing added: never add am, pm,
today or tomorrow that the user did not say. "number" is only for volume.
Intents, with examples ->  output:
alarm_set: "wake me at 7" -> when "at 7";  "alarm for 6:30 am" -> when "for 6:30 am"
reminder_set: "remind me to cook in 20 minutes" -> label "to cook", when "in 20 minutes"
timer_set: "ten minute timer for pasta" -> when "ten minute", label "pasta"
schedule_list: "what reminders do I have", "list my timers", "any alarms?"
schedule_cancel: "cancel the 7 am alarm" -> when "7 am";  "cancel the cooking reminder" -> label "cooking";
  "stop the timer", "cancel all reminders"
volume_set: "volume to 30" -> number 30   volume_step: "louder", "turn it down"
volume_level: "what's the volume"   mute: "mute"   unmute: "unmute the sound"
media: "pause", "skip", "next song", "previous track" -> label playpause | next | prev
Several orders in one sentence -> several commands in order: "alarms for 7 and 8 am" -> when "7", when "8 am".
Now: {now}."""


def ask_ai(text, routed):
    """Only a near-miss, or a chat line with a command word that is not a question or about the past, goes to the AI."""
    t = re.sub(r"^(?:(?:and|then|so|now|okay|ok|alright|um|uh|yo|hey|hi)[,.]? +)+", "", strip_name(text).strip().lower())
    if (setting("JarvisAIRouter", "1") != "1" or AI_NOT.match(t)
            or t.endswith("?") and not re.match(r"(?:can|could|would|will) you\b", t)):
        return False
    return routed[3] == NEAR_MISS or routed[0] == "chat" and bool(AI_WORDS.search(t))


def _words(s):
    return re.findall(r"[a-z0-9:']+", re.sub(r"\b([ap])\.? ?m\b\.?", r"\1m", s.lower()))


def interpret(model, text):
    """What the AI made of a missed command, as a checked route; None when there is none or it can't be trusted."""
    t0, low = time.time(), text.lower()
    heard = set(_words(text))
    nums = {_num(w) for w in heard} - {None}
    said = lambda s: all(w in heard or w in ("at", "in", "for", "to", "the", "and") or _num(w) in nums for w in _words(s))
    try:
        prompt = AI_PROMPT.replace("{now}", datetime.now().strftime("%A %d %B %Y, %I:%M %p"))
        cmds = [c for c in chat_json(model, AI_SCHEMA, prompt, text, 160, 8)["commands"] if c.get("intent") != "chat"]
        sets = [c for c in cmds if c.get("intent") == "alarm_set"]
        if len(sets) > 1 and len(sets) == len(cmds) and not any(str(c.get("when", "")).startswith("in ") for c in sets):
            # "alarms for 7 and 8 am": one sentence, so route() gives the am / pm said last to each
            cmds = [{"intent": "alarm_set", "when": "for " + " and ".join(re.sub(r"^(?:at|for) ", "", c.get("when", "")) for c in sets)}]
        routes = []
        for c in cmds:
            intent, at, label = c["intent"], str(c.get("when") or "").strip(), str(c.get("label") or "").strip()
            label = " ".join(re.sub(r"\b(?:alarms?|reminders?|timers?)\b", " ", label).split())
            if not re.search(rf"\b(?:{AI_CUES[intent]})", low) or not said(at) or intent != "media" and not said(label):
                raise ValueError("not what was said")
            bare = re.sub(r"^(?:at|in|for|on) ", "", at)
            noun = "timer" if "timer" in low else "reminder" if "remind" in low else "alarm"
            spec = " ".join(x for x in (bare, label) if x)
            n = c.get("number")
            if intent == "volume_set" and not (isinstance(n, int) and 0 <= n <= 100 and n in nums):
                raise ValueError("volume not said")
            down, step_by = False, ""
            if intent == "volume_step":
                down, up = bool(AI_DOWN.search(low)), bool(AI_UP.search(low))
                if down == up:                                 # neither way, or both ("be quiet, turn up"): do not guess
                    raise ValueError("not what was said")
                step_by = f" by {n}" if isinstance(n, int) and 1 <= n <= 100 and n in nums else ""
            sentence = {
                "alarm_set": f"set an alarm {at}".strip(),
                "reminder_set": f"remind me {label if re.match(r'(?:to|about|that) ', label) or not label else 'to ' + label} {at}".strip(),
                "timer_set": f"set a timer for {bare}" + (f" for {label}" if label else "") if bare else "set a timer",
                "schedule_list": "list my timers" if noun == "timer" else "what alarms do I have",
                "schedule_cancel": (f"cancel all {noun}s" if re.search(r"\b(?:all|every)\b", low) and not spec
                                    else f"cancel the {noun} for {spec}" if spec else f"cancel the {noun}"),
                "volume_set": f"set the volume to {n}",
                "volume_step": f"turn it {'down' if down else 'up'}{step_by}",
                "volume_level": "what's the volume", "mute": "mute", "unmute": "unmute",
                "media": {"playpause": "pause", "next": "next track", "prev": "previous track"}.get(label, ""),
            }[intent]
            r = route(sentence)
            want = {"alarm_set": "set", "reminder_set": "set", "timer_set": "set", "schedule_list": "list",
                    "schedule_cancel": "cancel"}.get(intent)
            ok = (r[:2] == ("remind", want) and (intent != "alarm_set" or r[2][0] == "alarm")
                  and (intent != "timer_set" or r[2][0] == "timer") and (intent != "reminder_set" or r[2][0] not in ("alarm", "timer"))
                  if want else r == ("level", None, None, None) if intent == "volume_level"
                  else r[0] == "act" and r[1] == {"mute": "mute", "unmute": "unmute", "media": "media"}.get(intent, "volume") and r[3] is None)
            if not ok:
                raise ValueError("no preset")
            routes.append(r)
        # several commands only when each is complete: a set with no time would stop to ask
        if len(routes) > 1 and any(r[1] == "set" and r[2][1] is None for r in routes):
            raise ValueError("incomplete")
    except Exception as e:
        why = str(e) if str(e) in ("not what was said", "volume not said", "no preset", "incomplete") else type(e).__name__
        log(f"interpreter: fallback ({why})")                  # our own reasons only, never the model's or your words
        return None
    log(f"interpreter: {len(routes)} commands, {time.time() - t0:.1f}s" if routes else "interpreter: no command")
    return None if not routes else routes[0] if len(routes) == 1 else ("multi", None, routes, None)


def forget_talk(gone):
    """`gone` holds filed talks (lists) and gist facts (strings): drop both."""
    save_topics([t for t in load_topics() if t["talk"] not in gone])
    rows, month = load_gist()
    if any(f in gone for _, f in rows):
        save_gist([(d, f) for d, f in rows if f not in gone], month)


@dataclass(frozen=True)
class Action:
    """One row of the action table (7-0). Only these can ever run; risk is decided here, never by the model."""
    run: object                    # run(target): does it, raises on failure
    risk: str                      # "read" | "change" | "ask": an "ask" row runs only with the confirmed pending action
    desc: str                      # the reply after it is done_line(action, target): read back from Windows


ACTION_TABLE = {
    "lock": Action(act_lock, "ask", "lock the PC"),
    "sleep": Action(act_sleep, "ask", "put the PC to sleep"),
    "restart": Action(lambda _: run_ok(["shutdown", "/r", "/t", "10"]), "ask", "restart the PC"),
    "shutdown": Action(lambda _: run_ok(["shutdown", "/s", "/t", "10"]), "ask", "shut the PC down"),
    "close": Action(act_close, "ask", "close an app"),
    "open": Action(act_open, "change", "open an app"),
    "mute": Action(lambda _: speakers_mute(True), "change", "mute the sound"),
    "unmute": Action(lambda _: speakers_mute(False), "change", "unmute the sound"),
    "volume": Action(act_volume, "change", "set or step the volume"),
    "media": Action(lambda key: press_key(MEDIA_KEYS[key]), "change", "press a media key"),
    "mic_mute": Action(lambda _: mic_volume(mute=True), "ask", "mute the microphone"),
    "mic_unmute": Action(lambda _: mic_volume(mute=False), "change", "unmute the microphone"),
    "mic_level": Action(act_mic_level, "change", "set or step the microphone level"),
    "todo": Action(lambda item: act_todo(item), "ask", "add a to-do"),
    "forget_all": Action(lambda _: save_memory([]), "ask", "forget every saved fact"),
    "forget_talk": Action(forget_talk, "ask", "forget earlier talks"),                         # M2b, after the read-back
    "forget_facts": Action(lambda gone: save_memory([f for f in load_memory() if f not in gone]), "ask",
                           "forget some saved facts"),                                         # M4a, after the read-back
    "replace_fact": Action(lambda pair: save_memory([pair[1] if f == pair[0] else f for f in load_memory()]), "ask",
                           "replace a saved fact"),
}
ACTIONS = {name: a.run for name, a in ACTION_TABLE.items()}    # the callers' and tests' name for the handlers

NEAR_MISS = "I heard a command but couldn't work it out. Try: set a timer for one minute."
CLAIM_LINE = "I didn't catch that as a command, so nothing changed. Say it again, like: set an alarm for 7 AM."
# a chat answer that says something was done: nothing runs on the chat path, so it cannot be true
# S2-8: any "I did it" / "it is now on" about a setting, the PC or an app; "I'll dim it" promises the same lie
CLAIM = re.compile(r"\b(?:alarm|timer|reminder|volume)s? (?:is |has been |was )?(?:set|added|changed|now|snoozed)\b|"
                   r"\bi(?:['’]ve| have| just)? (?:just )?(?:set|turned|changed|opened|closed|muted|unmuted|"
                   r"added|created|scheduled|adjusted|connected|disconnected|cancelled|canceled|snoozed|moved|dimmed|"
                   r"brightened|lowered|raised|increased|decreased|reduced|enabled|disabled|switched|activated|"
                   r"deactivated|toggled|paired|restarted|rebooted|locked|launched|shut|powered)\b|"
                   r"\bi(?:['’]ll| will) (?:now )?(?:set|turn|change|open|close|mute|unmute|dim|brighten|lower|raise|"
                   r"enable|disable|switch|connect|disconnect|restart|reboot|lock|shut|put)\b|"
                   r"\b(?:brightness|bluetooth|wi-?fi|night light|dark mode|light mode|screen|display|wallpaper|headphones|"
                   r"microphone|mic|computer|pc|laptop)(?: is| has been| was)? (?:now (?:at )?\d|(?:now )?(?:on|off|enabled|"
                   r"disabled|dimmed|brighter|darker|connected|disconnected|set to|lowered|raised|increased|decreased|"
                   r"reduced|changed|adjusted|turned (?:on|off|up|down)|locked|restarting|shutting down|going to sleep)\b)|"
                   r"^(?:done|all set)\b", re.I)
CANT = "I can't do that yet."
# S2-8 capability table, the part not built yet: a request for one is said by code before the model (it would answer
# "done"). What IS built: ACTIONS, the reminder / volume / media lanes. Phase 7-0 folds both into one action table.
UNBUILT_CAPS = {
    "brightness": r"brightness|brighter|dimmer|dim|darker",
    "bluetooth": r"bluetooth|headphones|earbuds|airpods",
    "wifi": r"wi-?fi|airplane mode|flight mode|hotspot",
    "display": r"night ?light|dark mode|light mode|wallpaper|(?:desktop )?background|resolution|screen ?saver",
    "microphone": r"microphone|mic",
    "account": r"hibernat\w*|sign (?:me )?out|log (?:me )?(?:off|out)",
    "power plan": r"battery saver|power mode",
    "keyboard light": r"keyboard (?:light|backlight)",
    "notifications": r"do not disturb|focus assist",
}
UNBUILT = re.compile(r"\b(?:" + "|".join(f"(?P<{k.replace(' ', '_')}>{v})" for k, v in UNBUILT_CAPS.items()) + r")\b")
UNBUILT_ASK = re.compile(r"(?:i (?:want|need) (?:you )?to |i'?d like (?:you )?to )?(?:set|turn|change|make|dim|brighten|"
                         r"darken|lower|raise|increase|decrease|reduce|boost|switch|connect|disconnect|pair|unpair|enable|"
                         r"disable|activate|deactivate|toggle|put|hibernate|sign|log|mute|unmute|open|start)\b")


def strip_name(text):
    """'Travis, set the volume' -> 'set the volume'. Only as the first words, after an optional hey / hi / ok; a
    misheard name needs the greeting or a comma after it, so "Service the car" and "Travis Scott is..." stay as said."""
    extra = [n.strip().lower() for n in setting("JarvisNameAliases", "").split(",") if n.strip()]
    names = "|".join(re.escape(n) for n in NAMES + extra)
    m = re.match(rf"\s*(?:(hey|hi|ok|okay)[,.]?\s+)?(?:(jarvis)|({names}))\b(?(1)\s*[,.!?]?|(?(2)\s*[,.!?]?|\s*[,.!?]))\s*",
                 text, re.I)
    if not m or not text[m.end():].strip():
        return text
    if m.group(3):
        log("name: heard as another word")                     # how often, never what was said
    return text[m.end():]


# ------------------------------------------------------------------ autocorrect: a command Whisper got slightly wrong
FILLER = re.compile(r"\b(?:please|could you|can you|would you|um+|uh+|so|like|just|for me|i want you to|go ahead and)\b,?", re.I)
SOUNDALIKE = [(r"\bthe value\b", "the volume"), (r"\btime are\b", "timer"), (r"\ba larm\b", "alarm"), (r"\bwon\b", "one"),
              (r"\bate\b", "eight"), (r"\bfor for\b", "for four"), (r"\bto+ (?=(?:minutes|seconds|hours)\b)", "two ")]
PHRASES = [(r"^(?:make|change) (?:the )?volume (?:to |at )?(\w+(?: \w+)?)$", r"set the volume to \1")]   # what route() misses
CMD_WORDS = ("volume mute unmute timer alarm reminder snooze cancel pause resume skip next previous track song louder "
             "quieter remind minutes seconds hours").split()
KEEP = set("minute second hour alarms timers reminders tracks songs volumes mutes muted music".split())   # already right


def tidy(text):
    """Filler words out, sound-alikes fixed, small-word variants put the way route() reads them."""
    t = " ".join(FILLER.sub(" ", strip_name(text)).split()).strip(" ,.!?")
    for pat, rep in SOUNDALIKE + PHRASES:
        t = re.sub(pat, rep, t, flags=re.I)
    return t


def fix_route(text, routed):
    """A chat line or near-miss of up to 8 words that becomes exactly one command once tidied or with one word swapped
    for a close command word (volyum -> volume) is that command; two different ones -> he asks. Otherwise as heard."""
    if not (routed[0] == "chat" or routed[3] == NEAR_MISS) or len(text.split()) > 8:
        return routed
    import difflib
    base = tidy(text)
    tries = [base] + [re.sub(rf"\b{w}\b", m, base, flags=re.I) for w in {w.lower() for w in re.findall(r"[A-Za-z]{4,}", base)}
                      if w not in CMD_WORDS and w not in KEEP for m in difflib.get_close_matches(w, CMD_WORDS, n=2, cutoff=0.8)]
    found = {}
    for t in tries:
        r = route(t)
        if r[0] in ("act", "remind", "level", "multi") and r[3] != NEAR_MISS:
            found.setdefault((r[0], r[1], re.sub(r"\.\d+", "", repr(r[2]))), (t, r))   # due times differ by microseconds
    if len(found) == 1:
        r = next(iter(found.values()))[1]
        log(f"autocorrect: {r[0]} {r[1]}")                     # what kind, never the words
        return r
    if len(found) > 1:
        a, b = [t for t, _ in found.values()][:2]
        log("autocorrect: two readings - asked")
        return ("say", None, None, f"Did you mean {a} or {b}? Say it once more.")
    return routed


def no_claims(sentences, collected):
    """The chat answer as it is spoken: a sentence that says an action was done is replaced, and the answer ends there."""
    for s in sentences:
        if CLAIM.search(s):
            log("chat answer claimed an action - replaced")
            collected[:] = [CLAIM_LINE]
            yield CLAIM_LINE
            return
        yield s


ORDINALS = ("first", "second", "third", "fourth", "fifth", "sixth", "seventh", "eighth", "ninth", "tenth")
# M1b: "cancel the second one", "open it again". "cancel that" stays undo; "stop it" is left alone (stop is for ringing)
REFER = re.compile(rf"(cancel|delete|remove|turn off|open|reopen|launch|close|quit|exit) (?:the )?(?:({'|'.join(ORDINALS)}|last) "
                   r"(?:one|alarm|reminder|timer|app)|(?:that|this) (?:one|alarm|reminder|timer|app)|it)(?: again)?")


def pick_last(cmd):
    """M1b: a sentence that points at what he just listed or acted on -> the route for that item, as if it had been said
    by name; "Which one?" when nothing fits. None when the sentence does not point back. Code picks, never the model."""
    m = REFER.fullmatch(cmd)
    if not m:
        return None
    app = m.group(1) in ("open", "reopen", "launch", "close", "quit", "exit")
    fresh = time.time() - last.get("when", 0) <= ACTIVE_TTL and (last.get("kind") == "app") == app
    items = last["items"] if fresh else []
    nth = m.group(2)
    i = (-1 if nth == "last" else ORDINALS.index(nth)) if nth else 0 if len(items) == 1 else None   # "it" needs one item
    if i is None or not -len(items) <= i < len(items):
        return ("say", None, None, "Which one?")
    if not app:
        return ("remind", "cancel", (last["kind"], "", items[i]), None)
    name = items[i][0] if isinstance(items[i], tuple) else os.path.splitext(items[i])[0]   # opened (name, id) / closed exe
    if REFER.fullmatch(f"open {name}".lower()):                 # an app called "it" would point back here forever
        return ("say", None, None, "Which one?")
    if m.group(1) in ("open", "reopen", "launch"):
        return route(f"open {name}")
    r = route(f"close {name}")
    return r if r[0] == "act" else route(f"close {name.split()[-1]}")   # "Google Chrome" is open as chrome.exe


def route(text):
    """Map what you said to (kind, action, target, confirmation prompt). kind: chat | notes | apps | act | guard | say |
    remind (action = list / cancel / set / flip, target = its details) | memory (action = save / list / forget) | brief |
    fact (prompt = the answer) | undo | heard | again | level (the volume, read in turn) | multi (target = the routes)."""
    said = strip_name(text)
    named, text = said != text, said
    t = text.strip().lower().rstrip(".!?")
    # "then change the volume", "Okay, set an alarm": a word that joins it to the last sentence is not the command
    t = re.sub(r"^(?:(?:and|then|so|now|okay|ok|alright|um|uh|yo|hey|hi)[,.]? +)+|,? please$", "", t)
    if DANGER.search(t):
        return ("guard", None, None, None)
    # actions only for commands ("lock my computer", "jarvis, could you open chrome"), never for questions about them
    # ("should I restart my computer?", "how do I close a for loop?")
    whole = cmd = re.sub(r"^(hey |ok |okay )?(jarvis[, ]+)?(please |can you |could you |would you |will you )?(please )?", "", t).strip()
    if text.strip().endswith("?") and cmd == t and not named:   # "Jarvis, ...?" was a command before the name moved out
        cmd = ""
    if re.fullmatch(rf"(?:(?:no|oh|oops|wait|actually|never ?mind|{'|'.join(['jarvis'] + NAMES)})[,.!]? +)*"
                    r"(?:undo(?: that| it)?|put it back|cancel that|take that back)", whole):
        return ("undo", None, None, None)
    if re.search(r"\bnever ?mind\b|\bactually,? (?:don'?t|do not|no)\b", whole):   # "set a timer for... never mind"
        return ("say", None, None, "Okay, never mind.")
    # "no, AM" / "I meant the evening" just after a clock time was set: moved 12 hours (remind_reply). "Morning." alone
    # is a greeting, so a part of the day needs the "no" / "I meant" in front
    m = re.fullmatch(r"((?:no,? |i meant |make (?:it|that) )*)(?:in the |the |at )?(a\.? ?m|p\.? ?m|morning|afternoon|evening|night)", whole)
    if m and (m.group(1) or len(m.group(2)) <= 4) and undo and undo[1] in ("reminder", "flip") and time.time() < undo[0]:
        return ("remind", "flip", ("alarm", "am" if m.group(2) == "morning" or m.group(2)[:2] in ("a.", "am", "a ") else "pm"), None)
    # read from Windows each time (turn), never from what the model or the chat remembers
    if re.fullmatch(r"what(?:'s| is) the (?:current )?volume(?: at| set to| now)?|how loud is it|is (?:it|the sound|the volume) muted", whole):
        return ("level", None, None, None)
    if re.fullmatch(r"what did you (?:just )?hear|what did i (?:just )?say", whole):
        return ("heard", None, None, None)
    if re.fullmatch(r"(?:say|repeat) (?:that|it) again|repeat that|come again|what did you (?:just )?say", whole):
        return ("again", None, None, None)
    if re.match(r"snooze\b", cmd):                             # after it stopped ringing (while it rings, alarm() hears it)
        return ("remind", "snooze", ("alarm", snooze_for(cmd)), None)
    picked = pick_last(cmd)
    if picked:
        return picked
    op = reminder_cmd(t, cmd, time.time())
    if op:
        return ("remind", op[0], op[1:], None)
    if re.fullmatch(r"(?:good (?:morning|afternoon|evening)|brief me|(?:give me )?(?:my |the )?daily briefing|"
                    r"what.?s my day look(?:ing)? like)(?:,? jarvis)?", whole):
        return ("brief", None, None, None)
    # M2b, talk filed by topic: forgetting reads them back and waits for yes; the list is said by code, not the model
    m = re.fullmatch(r"(?:forget|delete|erase) (?:what|everything) (?:we|i)(?:'ve| have)? (?:said|talked|spoken|spoke|"
                     r"discussed) about (.+)", whole)
    if m:
        return talk_forget(m.group(1))
    m = re.fullmatch(r"what do you (?:remember|recall) about (.+)|what (?:did|have) we (?:say|said|talk|talked|discuss|"
                     r"discussed) about (.+)", whole)
    if m:
        return ("say", None, None, talk_list(m.group(1) or m.group(2)))
    # remembered facts. "do you remember that film?" and "remember to buy milk" are not for this
    if re.fullmatch(r"what do you remember|what have i (?:told|asked) you to remember|"
                    r"(?:list|show|read)(?: me)? (?:my |your )?memor(?:y|ies)|what.?s in your memory", whole):
        return ("memory", "list", None, None)
    m = (re.match(r"(?:(?:oh|also|and),? )*(?:i (?:want|need) you to )?remember[,:]? (?:that )?(?!to )(?!(?:that|it|this)$)(.+)", cmd)
         or re.match(r"(?:note|(?:don't|do not) forget|keep in mind) that (\S+ .+)", cmd)   # two words: not "note that down"
         or re.fullmatch(r"(?!.*\?)(\S+ .+?)[,.;!] (?:(?:please )?remember (?:that|this|it)|(?:don't|do not) forget (?:that|it)|"
                         r"keep (?:that|this|it) in mind)", cmd))   # "my sister's name is Ana, remember that"
    if m:
        return fact_save(as_said(text, m.group(1)))
    m = re.fullmatch(r"what do you know about (.+)", whole)      # M4a: your own words, by code; nothing saved -> the model
    if m:
        try:
            hits = facts_about(m.group(1))
        except (OSError, ValueError):
            return ("say", None, None, MEMORY_BAD)
        if hits:
            return ("say", None, None, "You told me: " + "; ".join(hits) + ".")
    if re.match(r"forget (?:everything|all)\b", cmd):
        try:
            n = len(load_memory())
        except (OSError, ValueError):
            return ("say", None, None, MEMORY_BAD)
        if not n:
            return ("say", None, None, "You haven't asked me to remember anything.")
        return ("act", "forget_all", None, f"Forget all {n} thing{'s' if n != 1 else ''} I remember? Confirm with yes.")
    m = re.match(r"forget (?:that |about |the )*(.+)", cmd)
    if m and m.group(1) not in ("it", "that", "this", "about it", "about that"):
        try:
            gone = [f for f in load_memory() if holds_words(f, m.group(1))]
        except (OSError, ValueError):
            return ("say", None, None, MEMORY_BAD)
        if len(gone) > 1:                                      # M4a: more than one: read back, wait for yes
            return ("act", "forget_facts", gone, f"Forget {len(gone)} things: {'; '.join(gone)}? Confirm with yes.")
        return ("memory", "forget", m.group(1), None)
    # "add buy milk to my to-do list", "add a task: renew passport". It writes into your note, so he asks first
    m = (re.match(r"(?:add|put) (.+?) (?:to|on|in|onto) (?:my |the )?(?:to-do|to do|todo|task)s?(?: list)?$", cmd)
         or re.match(r"(?:add|new|create|make) (?:a |an )?(?:new )?(?:task|to-do|todo|to do)(?: item)?[:,]? (.+)$", cmd))
    if m:
        if not todo_note():
            return ("say", None, None, "No to-do note is set (Control Center, TO-DO NOTE).")
        item = " ".join(as_said(text, m.group(1)).split())[:200]
        return ("act", "todo", item, f"Add '{item}' to your to-do list? Confirm with yes.")
    m = re.search(r"\b(?:search|check|look (?:through|in)|find|what do)\b.*\b(?:my )?(?:notes?|vault|obsidian)\b(?:.*?\b(?:for|about|on)\b\s+(.+))?", t)
    if m:
        q = m.group(1) or re.sub(r"\b(search|check|look|through|in|find|what|do|my|notes?|vault|obsidian|say)\b", " ", t)
        return ("notes", None, q.strip(), None)
    m = re.search(r"\b(?:is|do i have)\s+(.+?)\s+installed\b|\b(?:what|which|list)\b.*\b(?:apps|applications|programs)\b.*\binstalled\b", t)
    if m:
        return ("apps", None, (m.group(1) or "").strip(), None)
    pc = r"(?:the |my |this )?(?:pc|computer|laptop|system|machine)"
    if re.match(r"lock (the |my )?(pc|computer|screen|laptop)\b", cmd) or re.fullmatch(rf"lock(?: it| up| {pc})?", cmd):
        return ("act", "lock", None, "You want me to lock the PC. Confirm with yes.")
    if (re.match(r"(go to sleep|put (the |my )?(pc|computer|laptop) to sleep|sleep (the |my )?(pc|computer|laptop))\b", cmd)
            or re.fullmatch(rf"(?:go into |enter )?sleep(?: mode)?|(?:put|set|send) (?:it |{pc} )?(?:in|on|to|into) sleep(?: mode)?", cmd)):
        return ("act", "sleep", None, "You want me to put the PC to sleep. Confirm with yes.")
    if re.match(r"(restart|reboot) (the |my )?(pc|computer|laptop|system)\b", cmd) or re.fullmatch(rf"(?:restart|reboot)(?: it| {pc})?", cmd):
        return ("act", "restart", None, "You're asking me to restart the PC. Confirm with yes.")
    if (re.match(r"(shut ?down|power off|turn off) (the |my )?(pc|computer|laptop|system)\b", cmd)
            or re.fullmatch(rf"shut ?down(?: {pc})?|shut (?:it|{pc}) (?:down|off)|power (?:off|down)(?: it| {pc})?|"
                            rf"power (?:it|{pc}) (?:off|down)", cmd)):
        return ("act", "shutdown", None, "You're asking me to shut down the PC. Confirm with yes.")
    mic_word = r"(?:the |my )?(?:mic|microphone)"
    m = re.match(rf"(mute|unmute) {mic_word}$", cmd)
    if m:                                                      # 7a: he cannot hear "unmute" once muted, so mute asks first
        if m.group(1) == "unmute":
            return ("act", "mic_unmute", None, None)
        return ("act", "mic_mute", None, "You want me to mute the microphone. I won't hear you after that; click me to "
                "unmute it. Confirm with yes.")
    m = (re.match(rf"(?:set|turn|change|put) {mic_word}(?: volume| level)?(?: up| down)? (?:to|at) (.+?)(?: ?%| percent)?$", cmd)
         or re.match(rf"{mic_word}(?: volume| level)? (?:to|at) (.+?)(?: ?%| percent)?$", cmd))
    if m and _num(m.group(1)) is not None:
        n = _num(m.group(1))
        return ("act", "mic_level", ("set", int(n)), None) if n <= 100 else ("say", None, None, "I can set it between 0 and 100.")
    m = (re.match(rf"turn (up|down) {mic_word}(?: volume| level)?(?: (?:a )?(?:bit|little|tad)| slightly)?$", cmd)
         or re.match(rf"turn {mic_word}(?: volume| level)? (up|down)(?: (?:a )?(?:bit|little|tad)| slightly)?$", cmd)
         or re.match(rf"(raise|increase|boost|lower|decrease|reduce) {mic_word}(?: volume| level)?(?: (?:a )?(?:bit|little|tad)| slightly)?$", cmd))
    if m:
        return ("act", "mic_level", ("step", 10 if m.group(1) in ("up", "raise", "increase", "boost") else -10), None)
    m = re.match(r"(mute|unmute)( the)?( sound| audio| volume| speakers)?$", cmd)
    if m:
        return ("act", m.group(1), None, None)
    # "set the volume to 30 / thirty / max / half", "set it to 30", "max volume", "turn it all the way up"
    m = (re.match(r"(?:i (?:want|need) |i'?d like )?(?:(?:set|turn|change|put|raise|lower|bring) )?(?:the )?volume(?: up| down)? "
                  r"(?:to |at |on )?(?:the )?(.+?)(?: ?%| percent)?$", cmd)
         or re.match(r"(?:set|turn|change|put) it (?:to|at) (.+?)(?: ?%| percent)?$", cmd)
         or re.match(r"(max|maximum|full|half) volume$|(?:turn |put )?(?:it|the (?:sound|music)) (all the way (?:up|down))$", cmd))
    if m:
        word = m.group(m.lastindex)
        n = {"max": 100, "maximum": 100, "full": 100, "half": 50, "all the way up": 100, "all the way down": 0,
             "a hundred": 100, "one hundred": 100, "hundred": 100}.get(word, _num(word))
        if n is not None and n > 100:
            return ("say", None, None, "I can set it between 0 and 100.")
        if n is not None:
            return ("act", "volume", ("set", int(n)), None)
    soft = r"(?:a (?:bit|little|tad) |slightly )?"               # "a bit" is the same 10 steps as plain "louder"
    m = re.match(rf"{soft}(?:(?:turn |make )?(?:it |(?:the )?(?:volume|sound|music) ){soft}(up|down|louder|quieter)|"
                 rf"turn (up|down) (?:it|the (?:volume|sound|music))|(louder|quieter))(?: (?:a )?(?:bit|little|tad)(?: more)?| slightly|"
                 r" by (.+?)(?: ?%| percent)?)?$", cmd)
    n = m and (_num(m.group(4)) if m.group(4) else 10)        # "turn it up by 20"; a plain step is 10
    if m and n is not None:
        return ("act", "volume", ("step", int(n) if (m.group(1) or m.group(2) or m.group(3)) in ("up", "louder") else -int(n)), None)
    m = re.match(r"(raise|increase|boost|lower|decrease|reduce) (?:the )?(?:volume|sound|music)(?: (?:a )?(?:bit|little|tad)| slightly|"
                 r" by (.+?)(?: ?%| percent)?)?$", cmd)
    n = m and (_num(m.group(2)) if m.group(2) else 10)
    if m and n is not None:
        return ("act", "volume", ("step", int(n) if m.group(1) in ("raise", "increase", "boost") else -int(n)), None)
    thing = r"(?: (?:the |my |this )?(?:music|song|track|video|playback))"
    # shortcut: one play/pause key, so "play" while it plays pauses; Windows has no separate keys worth the code
    if re.match(rf"(?:(?:pause|play|resume|unpause){thing}?|stop{thing})$", cmd):
        return ("act", "media", "playpause", None)
    if re.match(r"(?:(?:play |skip to )?(?:the )?next(?: track| song)?|skip(?: (?:this |the )?(?:track|song))?)$", cmd):
        return ("act", "media", "next", None)
    if re.match(r"(?:(?:play |go back to )?(?:the )?(?:previous|last) (?:track|song)|go back a (?:track|song)|previous)$", cmd):
        return ("act", "media", "prev", None)
    m = re.match(r"(?:close|quit|exit|kill)\s+(?:the\s+)?(.+?)(?:\s+app(?:lication)?)?$", cmd)
    if m and not re.search(r"\b(log|transcript|history|conversation|chat|pop ?up|window)\b", m.group(1)):
        exe = running_window(m.group(1))
        if exe:
            return ("act", "close", exe, f"You want me to close {exe.replace('.exe', '')}. Unsaved work could be lost. Confirm with yes.")
        return ("say", None, None, f"I don't see {m.group(1)} open.")
    m = re.match(r"(?:open|launch|start|run)\s+(?:the\s+|up\s+)?(.+?)(?:\s+app(?:lication)?)?$", cmd)
    if m and not re.search(r"\b(log|transcript|history|conversation|chat|pop ?up)\b", m.group(1)):
        app = best_app(m.group(1))
        if app:
            return ("act", "open", app, None)                       # opening is harmless: no confirmation
        if start_apps() is None:
            return ("say", None, None, "The app list isn't ready yet.")
        # not an app ("run a speed test"): let the model answer
    answer = fact_answer(whole, time.time())
    if answer:
        return ("fact", None, None, answer)
    # "set an alarm for 7 and remind me to cook": two commands, run one after the other only when each is complete and
    # safe on its own (no confirmation); otherwise it is not split
    pieces = [p for p in re.split(r",? and (?:then )?|, then ", whole) if p.strip()]
    parts = [route(p) for p in pieces] if len(pieces) > 1 else []          # each piece is shorter: no endless recursion
    if parts and all(p[0] in ("remind", "level") and p[1] != "flip" and not (p[1] == "set" and p[2][1] is None)
                     or p[0] == "act" and p[3] is None for p in parts):       # a set with no time would ask: not split
        return ("multi", None, parts, None)
    cap = UNBUILT.search(cmd) if UNBUILT_ASK.match(cmd) else None
    if cap or re.fullmatch(r"hibernate(?: it| (?:the |my )?(?:pc|computer|laptop))?|(?:sign|log) (?:me )?(?:out|off)", cmd):
        log(f"capability: {cap.lastgroup.replace('_', ' ') if cap else 'account'} not built yet - said so")
        return ("say", None, None, CANT)
    # a command that no parser above took: said plainly, never handed to the model (it would answer "done")
    if (re.match(r"(?:i (?:want|need) (?:you )?to |i'?d like (?:you )?to )?(?:set|turn|change|open|close|mute|cancel|"
                 r"connect|snooze|switch)\b", cmd)
            and re.search(r"\b(?:volume|alarms?|timers?|reminders?|apps?|application|bluetooth|microphone|mic|brightness|"
                          r"screen|display|colou?r|settings?|wi-?fi|headphones|speakers?|sound)\b", cmd)
            and not re.match(r"(?:how|why|what|when|who|where|which|can you explain|could you explain)\b", t)):
        return ("say", None, None, NEAR_MISS)
    return ("chat", None, None, None)


def as_said(text, part):
    """`part` was found in the lowercased text: give it back with the capitals it was said with."""
    i = text.lower().find(part)
    return text[i:i + len(part)] if i >= 0 else part


def holds_words(fact, said):
    """Every word said is a whole word of the fact ("car" is not in "Oscar")."""
    return set(re.findall(r"[\w']+", said.lower())) <= set(re.findall(r"[\w']+", fact.lower()))
