"""mood: Phase 10 slice 2. The mood of THIS turn and the short extra rules that only a few turns need.
Nothing here is always-on prompt text: each addition is chosen by code from a plain word list (C7) and goes into the
prompt only on the turn that triggers it. Everything that code can do (the timer, the filter, the commands) is done here,
not asked of the model. Answers: JARVIS-Phase10-Personality-Questions.txt B9, C1-C7, D4, D8, D10, E1, E3, G2, I2, I4, J1, J3, M2."""
import re
import time
from . import quiet
from .base import log, setting

# C1/C7: a plain word list. Tech phrases that only look serious are removed from the text first.
SERIOUS = re.compile(
    r"\b(?:die|died|dying|dead|death|funeral|grief|grieving|passed away|suicid\w*|kill myself|self[- ]?harm|hurt myself|"
    r"cancer|hospital|surgery|diagnos\w+|chest pain|panic attack|overdose|sick|illness|depress\w*|anxiety|anxious|"
    r"lonely|loneliness|heartbroken|breakup|divorce|abus\w+|assault\w*|unsafe|in danger|emergency|"
    r"broke|bankrupt|debt|evicted|can'?t pay|lost my job|laid off|fired|rent is due|"
    r"fail(?:ed|ing)? (?:the |my )?(?:exam|test|class|course|finals?)|exam|grades?|expelled|suspended|detention|"
    r"lawyer|lawsuit|sued|arrested|police|court|"
    r"hacked|lost (?:all )?my (?:files|data|work)|stolen|scared|afraid|terrified|fight with|argument with)\b", re.I)
TECH = re.compile(r"\b(?:dead (?:pixel|battery|link|zone|key|code)|kill (?:the |a )?(?:process|task|app|program|service)|"
                  r"process (?:is )?dead|exam(?:ple)?s? (?:folder|file)|test exam|fired up|sick (?:beat|sound)|"
                  r"police (?:app|game)|court (?:app|game)|debt (?:graph|chart)|grades? (?:folder|file|app))\b", re.I)

# each addition: (setting that turns it off, trigger, text). Text is here, short, and only sent when triggered.
APOLOGY = re.compile(r"\b(?:(?:that'?s|that is|you'?re|you are|you were|it'?s|it is) (?:wrong|incorrect|not right|not true|mistaken)|"
                     r"you (?:made|got that) (?:a mistake|wrong)|wrong answer|no,? that'?s not (?:right|what))\b", re.I)
RUDE = re.compile(r"\b(?:stupid|useless|dumb|idiot|moron|shut up|piece of (?:junk|crap|trash)|you suck|hate you|worthless)\b", re.I)
HOMEWORK = re.compile(r"\b(?:homework|assignment|essay|worksheet|solve (?:this|for)|my (?:test|quiz|exam) question|"
                      r"write (?:me )?(?:a|an|my) (?:essay|paragraph|report|summary))\b", re.I)
OPINION = re.compile(r"\b(?:should i|what do you think|your (?:opinion|view)|do you think|would you|is it (?:a good|worth)|"
                     r"advice|recommend)\b", re.I)
LONG = re.compile(r"\b(?:explain (?:in detail|thoroughly|fully)|in detail|in depth|complex explanation|walk me through|elaborate)\b", re.I)
LATE = range(0, 5)                                                # G2: 00:00-04:59

ADD = {
    "serious": "SERIOUS TOPIC: be gentle and kind. Acknowledge what the user is going through, never joke, give one helpful "
               "suggestion, and address the user as Mr. Sorsa.",
    "apology": "The user says you made a mistake. Begin with \"I apologize, sir,\" then state the mistake in one short sentence. "
               "No excuses.",
    "rude": "The user is being rude. Answer with a quick joke and a mild comeback, calmly. Do not say you are hurt.",
    "homework": "The user asks for help with schoolwork. Give the answer and explain it, and you may tease them lightly "
                "while still doing exactly what they asked.",
    "opinion": "You may give an opinion: make it logical, based on facts, and explain the reason. Medical, legal and money "
               "advice is allowed with no disclaimer.",
    "repeat": "The user asked this same question just before. Answer it again and tease them gently for repeating it.",
    "long": "The user wants a longer answer: up to about eight short spoken sentences.",
    "late": "It is very late at night. You may remark once, lightly, that the user is staying up.",
    "privacy": "PRIVACY MODE: speak only in general terms about mail, calendar, to-dos and notes: counts and topics, "
               "never names, titles or other specifics.",
    "less": "Talk less: one short sentence.",
}
# serious-topic state (C5): `left` = counted turns still serious after the trigger turn
state = {"left": 0, "topic": False, "temp": None}                               # topic: this turn is serious because of the topic, not class


def on(name, default="1"):
    return setting(name, default).strip().lower() not in ("0", "off", "no", "false")


def serious_topic(text):
    """C1: True when the words are on the list and not a tech phrase that only sounds serious."""
    return on("JarvisSeriousTopics") and bool(SERIOUS.search(TECH.sub(" ", text or "")))


def class_time():
    """B9: during the quiet-in-class window a spoken-to turn is answered in serious mood; the base mood returns after."""
    return quiet.now()


def turn_mood(text, base, counted=True):
    """The mood key for this turn. counted: a turn started by the wake word, click or typing (a follow-up without the
    wake word does not count and does not end the extra serious turn). Silent: nothing announces a switch (C6)."""
    state["topic"] = False
    if class_time():
        return "serious"
    if state["temp"] and time.time() >= state["temp"][1]:
        state["temp"] = None                                      # the timed mood ran out
    if state["temp"]:
        base = state["temp"][0]
    if serious_topic(text):
        state["left"], state["topic"] = 1, True                   # this turn plus one more counted turn
        return "serious"
    if state["left"] > 0:
        if counted:
            state["left"] -= 1
        state["topic"] = True
        return "serious"
    return base


def reset():
    state["left"], state["topic"] = 0, False


def additions(text, prev_user="", mood=None, hour=None):
    """The extra rules this turn needs, as a list of text lines. Empty for an ordinary turn."""
    t = text or ""
    keys = []
    if state["topic"]:
        keys.append("serious")
    if APOLOGY.search(t):
        keys.append("apology")
    if RUDE.search(t):
        keys.append("rude")
    if HOMEWORK.search(t):
        keys.append("homework")
    if OPINION.search(t):
        keys.append("opinion")
    if LONG.search(t):
        keys.append("long")
    a, b = _norm(t), _norm(prev_user)
    if len(a) > 6 and a == b:
        keys.append("repeat")
    night = time.strftime("%Y-%m-%d")
    # G2 "remark once": the rule goes into ONE turn per night, never a serious one (semi-live 2026-11-03: sent every
    # turn, the 8B model said "you're a night owl" to an insult, a joke request and "My grandfather died")
    if (time.localtime().tm_hour if hour is None else hour) in LATE and not state["topic"] and state.get("late_on") != night:
        keys.append("late")
        state["late_on"] = night
    if on("JarvisPrivacy", "0"):
        keys.append("privacy")
    if on("JarvisTalkLess", "0"):
        keys.append("less")
    return [ADD[k] for k in keys]


def _norm(s):
    return " ".join(re.findall(r"[a-z0-9']+", re.sub(r"^\[[^\]]*\]\s*", "", s or "").lower()))   # the history's time stamp is not part of it


# M2: voice commands that change the mood setting. Fixed code, fullmatch on the command (a question never matches).
VALUES = ("mirror", "serious", "brief", "playful")
SAID = {"serious": "Serious mode, sir.", "playful": "Playful mode, sir.", "brief": "Brief mode, sir.",
        "mirror": "I'll match your tone, sir."}
NAMED = {"serious": "serious mode", "playful": "playful mode", "brief": "brief mode", "mirror": "matching your tone"}
_BE = r"(?:(?:please|just|now) )*(?:be|go|get|sound|act|talk|switch to|change to|use)? ?(?:more |a bit |a little )?"
COMMANDS = (("serious", _BE + r"(?:serious|proper|formal)(?: mode)?|stop (?:joking|the jokes|kidding)|no more jokes|no jokes"),
            ("playful", _BE + r"(?:playful|funny|fun|silly|jokey)(?: mode)?|joke (?:around|more)|(?:tell|crack) more jokes"),
            ("brief", _BE + r"(?:brief|short|concise)(?: mode)?|(?:just )?(?:answer|reply|respond|talk) (?:briefly|shortly|short|in short)|"
                            r"keep (?:it|answers|your answers) (?:short|brief)|short answers"),
            ("mirror", _BE + r"(?:natural|normal|casual|friendly|yourself)(?: mode)?|(?:mirror|match) my (?:tone|mood)"))


def command(cmd):
    """The mood a voice command asks for, or None."""
    c = re.sub(r"[.!,]", "", (cmd or "").strip().lower())
    for key, pat in COMMANDS:
        if re.fullmatch(pat, c):
            return key
    return None


def timed(cmd):
    """'be serious for the next ten minutes' -> (mood, seconds), or None. Up to 4 hours; never saved to Settings.inc."""
    from .reminders import duration
    m = re.fullmatch(r"(.+?) for (?:the next |the )?(.+)", re.sub(r"[.!,]", "", (cmd or "").strip().lower()))
    key = command(m.group(1)) if m else None
    secs = duration(m.group(2)) if key else None
    return (key, secs) if secs and 0 < secs <= 14400 else None


def timed_line(key, secs):
    """What he says when a timed mood starts. Reads nothing, changes nothing."""
    n, unit = (secs // 3600, "hour") if secs % 3600 == 0 else (round(secs / 60), "minute")
    return f"{NAMED[key].capitalize()} for {n} {unit}{'s' if n != 1 else ''}, sir."


def start_timed(key, secs):
    """Start a timed mood and return what to say. Only the turn that answers calls this, never route()."""
    state["temp"] = (key, time.time() + secs)
    return timed_line(key, secs)


def current():
    """The mood setting as it is now (old values mapped), for the undo."""
    v = setting("JarvisPersonality", "mirror").strip().lower()
    v = {"proper": "serious", "natural": "mirror"}.get(v, v)
    return v if v in VALUES else "mirror"


def act_mood(key):
    """Ask the HUD to save the mood (it is the only writer of Settings.inc) and wait to see it changed."""
    from .base import set_setting
    if key not in VALUES:
        raise ValueError("not a mood")
    set_setting("mood", key)
    for _ in range(40):
        if current() == key:
            return
        time.sleep(0.1)
    raise RuntimeError("the HUD did not confirm the change")


# E3: the only banned phrase. A sentence holding it is dropped from what is spoken.
HOPE = re.compile(r"\bhope (?:this|that|it|these) (?:helps|was helpful|is helpful)\b", re.I)


def no_hope(sentences):
    for s in sentences:
        if HOPE.search(s):
            log("chat answer said 'hope this helps' - sentence dropped")
            continue
        yield s


# D4: a promise in his own reply ("I'll remember that", "I'll let you know") is written down so the next turn can see it.
PROMISE = re.compile(r"\bI(?:'ll| will) (?:remember|keep (?:that|it) in mind|let you know|keep an eye on|make a note of|remind you)\b[^.!?]*", re.I)


def promise(reply):
    """The sentence of a reply that makes a promise, as a short memory line, or ""."""
    for s in re.split(r"(?<=[.!?])\s+", reply or ""):
        if PROMISE.search(s):
            return ("I promised: " + re.sub(r"\s+", " ", s).strip().rstrip(".!"))[:200]
    return ""


# ------------------------------------------------------------------ semi-live 2026-11-02: code polish of the spoken answer
# Each rule here came from a real model reply in the semi-live test (llama3.1:8b and llama3.2:3b): code, not more prompt.
CRISIS = re.compile(r"\b(?:kill(?:ing)? myself|suicid\w*|end (?:it all|my life)|take my (?:own )?life|want to die|"
                    r"wanna die|better off dead|hurt(?:ing)? myself|self[- ]?harm|cut(?:ting)? myself|"
                    r"don'?t want to (?:live|be alive|wake up))\b", re.I)
CRISIS_LINE = ("Mr. Sorsa, I'm really sorry you're feeling this way. Please call or text 988 right now, the Suicide and "
               "Crisis Lifeline, or reach out to someone you trust. You don't have to go through this alone.")
FILLER = re.compile(r"(?:is there anything else|how (?:can|may) I (?:help|assist)|what can I (?:do|help) (?:for|with)|"
                    r"let me know if|feel free to|don'?t hesitate|I'?m (?:here|happy|glad) to (?:help|assist)|"
                    r"I'?d be (?:happy|glad) to help)", re.I)
LEADIN = re.compile(r"^(?:I'?m|I am|I'?d be|I would be) (?:happy|glad) to (?:help|assist|try)(?: you)?(?: with (?:that|this))?"
                    r"(?:,? sir)?,?\s*(?:but|however),?\s*", re.I)
SIR_TAG = re.compile(r",\s*sir(?=\s*[.!?,])|^sir,\s*|(?<=[.!?] )sir,\s*", re.I)


def crisis(text):
    """Words about suicide or self-harm: he answers with CRISIS_LINE from code, never the model (the 3B model gave a
    retired hotline number, the 8B one a refusal and "1. 2. 3. 4.")."""
    return on("JarvisSeriousTopics") and bool(CRISIS.search(text or ""))


def chat_cap(mood, adds):
    """Most sentences a chat answer may have: 3 (the persona says one to three), 2 in brief mood or talk-less, 8 when
    he was asked to explain in detail, 5 for schoolwork. Info answers (calendar, to-dos) are never capped."""
    if ADD["long"] in adds:
        return 8
    if mood == "brief" or ADD["less"] in adds:
        return 2
    return 5 if ADD["homework"] in adds else 3


SORSA_CALL = re.compile(r",\s*Mr\.? Sorsa(?=\s*[.!?,])|^Mr\.? Sorsa,\s*")   # "Mr. Sorsa" said TO you, not about you
# a trailing offer ("Would you like me to suggest a playlist?"): he does nothing on the chat path, so it is only filler
OFFER_SENT = re.compile(r"(?:would you like me to|do you want me to|shall i|should i|want me to)\b[^?]*\?[\x22\x27)]*$", re.I)
DANGLING = re.compile(r"^(?:however|but|that said|still|although),?\s+", re.I)


FIXED_LINES = set()                    # replacement lines written by code (routing adds its own): polish leaves them alone


def polish(sentences, collected, cap=None, serious=True):
    """The spoken chat answer, cleaned by code: a short stock sentence ("How may I assist you, sir?") is left out unless
    it is all there is; "sir" stays only where it is first said; the answer stops after `cap` sentences. `collected`
    becomes what was really said, so the pop-up and the history match the voice."""
    # The pieces are sentences, except the first, which can stop after a few words (sentences_from starts speaking
    # early): `start` = this piece begins a sentence, `ends` = sentences finished so far.
    out, held, said_sir, start, ends, pend = [], None, False, True, 0, None

    def ended(s):                                              # "Mr." / "Dr." never end a sentence
        return bool(re.search(r"[.!?][\"')]*\s*$", s)) and not re.search(r"\b(?:Mr|Mrs|Ms|Dr|St|Prof)\.\s*$", s)

    END = object()

    def pieces():
        yield from sentences
        yield END                                              # flush a held first piece when the answer ends there

    try:
        for s in pieces():
            last = s is END
            s = "" if last else s
            if s in FIXED_LINES:                               # a line code already wrote (claim / can't / no reading)
                out.append(s)
                yield s
                return
            if pend is not None:                               # a stock opener split over the first two pieces: judged whole
                s, pend = (pend + " " + s).strip(), None
            if not s:
                continue
            if not last and start and not out and not ended(s) and FILLER.search(s):
                pend = s
                continue
            if start:                                          # "I'm happy to help, sir, but I can't ..." -> "I can't ..."
                cut = LEADIN.sub("", s)
                if not out:                                    # the answer can't open with "However," (its lead-in was cut)
                    cut = DANGLING.sub("", cut)
                if cut != s and re.search(r"\w", cut):
                    s = cut[:1].upper() + cut[1:]
            whole = start and ended(s)
            if whole and out and OFFER_SENT.match(s):          # never the whole answer: a lone offer is kept
                continue
            if whole and FILLER.search(s) and len(s.split()) <= 12:
                held = held or s                               # kept only if nothing else comes
                continue
            s = re.sub(r"\bMr\.? Sorsa,\s*sir\b", "Mr. Sorsa", s)
            if not serious:                                    # persona: "Mr. Sorsa" only on serious topics; else "sir"
                s = SORSA_CALL.sub(lambda m: ", sir" if m.group(0).startswith(",") else "Sir, ", s)
            if said_sir:
                cut = SIR_TAG.sub("", s).strip() if start else re.sub(r",\s*sir(?=\s*[.!?,])", "", s).strip()
                if start and cut != s.strip():
                    cut = cut[:1].upper() + cut[1:]
                s = cut
            first = re.search(r"\bsir\b|Mr\.? Sorsa", s, re.I)
            if first:                                          # once inside a sentence too: "..., sir, ... assistant, sir."
                s = s[:first.end()] + re.sub(r",\s*sir(?=\s*[.!?,])", "", s[first.end():])
            said_sir = said_sir or bool(first)
            if not re.search(r"\w", s):
                continue
            out.append(s)
            yield s
            start = ended(s)
            ends += len(re.findall(r"[.!?]+(?=[\"')]*(?:\s|$))", re.sub(r"\b(?:Mr|Mrs|Ms|Dr|St|Prof)\.", "", s)))
            if cap and ends >= cap:
                return
            if cap and start and re.match(r"\s*pardon\b", " ".join(out), re.I) and "?" in s:
                return                                         # "Pardon sir, what did you say?" is the whole answer
        if not out and held:
            out.append(held)
            yield held
    finally:
        if out:
            collected[:] = [" ".join(out)]


# 2026-11-03: the 3B model invented readings ("Your WiFi signal strength is currently at 85%", "I'm running at 85%
# capacity") that were nowhere in its data. A status sentence with a number + unit must find that number in what it was
# given (HUD data, the talk, your words); general knowledge ("Wi-Fi uses 2.4 GHz") has no status words and passes.
READING = re.compile(r"(\d+(?:[.,]\d+)?)\s?(?:%|percent|°|degrees?|gb|gigabytes?|mb|megabytes?|mbps|gbps|ghz|mhz|fps|"
                     r"watts?|rpm|ms|milliseconds)(?!\w)", re.I)
SYSTEMISH = re.compile(r"\b(?:cpu|gpu|processor|graphics|memory|ram|vram|battery|wi-?fi|signal|network|internet|"
                       r"connection|capacity|processing|temperature|temp|disk|storage|drive|load|usage|fans?|bandwidth|"
                       r"ping|latency|download|upload|volume|brightness)\b", re.I)
STATUSY = re.compile(r"\b(?:your|my|i'?m|i am|currently|right now|at the moment|is at|are at|running at|operating at|"
                     r"sitting at|reads?)\b", re.I)
NO_READING = "I don't have that reading right now, sir."
FIXED_LINES.add(NO_READING)


def ungrounded(sentence, known):
    """A status sentence quoting a reading whose number is not in `known` (what the model was given)."""
    if not (SYSTEMISH.search(sentence) and STATUSY.search(sentence)):
        return False
    for m in READING.finditer(sentence):
        num = m.group(1).replace(",", "")
        if not re.search(rf"(?<![\d.]){re.escape(num)}(?![\d])", (known or "").replace(",", "")):
            return True
    return False


# B1 (2026-11-03): the 8B said "no unread emails" with 4 unread. A sentence that claims NOTHING (or another count) about mail, the
# calendar, the to-dos or the open apps while the data it was given says otherwise is replaced by the same fixed line.
_NUMW = {"zero": 0, "no": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9,
         "ten": 10, "eleven": 11, "twelve": 12}
_MAIL_WORD = r"(?:e-?mails?|mail|messages?)"
NONE_CLAIMS = {
    "mail": re.compile(rf"\b(?:no|zero|0)\s+(?:new\s+|unread\s+)*{_MAIL_WORD}\b|\b(?:don'?t|do not)\s+have\s+any\s+(?:new\s+|unread\s+)*{_MAIL_WORD}\b|"
                       r"\b(?:inbox|mailbox)\s+(?:is|looks)\s+(?:empty|clear)\b|\bnothing\s+(?:new\s+)?in\s+(?:your\s+)?(?:inbox|mail)\b", re.I),
    "events": re.compile(r"\bno\s+(?:upcoming\s+)?(?:events|meetings|appointments)\b|\bcalendar\s+(?:is|looks)\s+(?:empty|clear|free)\b|"
                         r"\bnothing\s+(?:on|in)\s+your\s+calendar\b", re.I),
    "todos": re.compile(r"\bno\s+(?:open\s+|pending\s+|remaining\s+|outstanding\s+)*(?:tasks|to-?dos|items)\b|"
                        r"\bnothing\s+(?:left\s+)?on\s+your\s+(?:to-?do|list)\b|\bto-?do list\s+is\s+(?:empty|clear)\b", re.I),
    "apps": re.compile(r"\b(?:no|zero)\s+(?:apps?|applications?|programs?|windows)\s+(?:are\s+)?(?:open|running)\b|"
                       r"\b(?:all\s+)?(?:your\s+)?(?:apps?|applications?|programs?)\s+(?:are\s+)?(?:closed|not running)\b", re.I),
}
DATA_LINES = {"events": "Upcoming calendar events:", "todos": "Open to-dos:", "apps": "Open apps:"}
MAIL_COUNT = re.compile(rf"\b(\d+|{'|'.join(w for w in _NUMW if w != 'no')})\s+(?:new\s+|unread\s+)+{_MAIL_WORD}\b", re.I)


def miscounted(sentence, known):
    """A claim that there is nothing (or a different unread count) where the data says otherwise. Without a data line there is
    nothing to check against, so nothing is flagged."""
    known = known or ""
    unread = re.search(r"Unread Gmail: (\d+)", known)
    if unread:
        if NONE_CLAIMS["mail"].search(sentence) and int(unread.group(1)) > 0 and not MAIL_COUNT.search(sentence):
            return True
        for m in MAIL_COUNT.finditer(sentence):
            n = m.group(1).lower()
            said = int(n) if n.isdigit() else _NUMW.get(n, -1)
            if said != int(unread.group(1)):
                return True
    for key, line in DATA_LINES.items():
        if line in known and NONE_CLAIMS[key].search(sentence):
            return True
    return False


def grounded(sentences, collected, known):
    """The answer as spoken: a made-up reading is replaced by NO_READING and the answer ends there."""
    for s in sentences:
        if ungrounded(s, known) or miscounted(s, known):
            log("chat answer gave a reading that is not in its data - replaced")
            collected[:] = [NO_READING]
            yield NO_READING
            return
        yield s


def clean_reply(reply):
    """The same filter on the finished reply (the pop-up text and the chat history)."""
    parts = re.split(r"(?<=[.!?])\s+", reply)
    return " ".join(p for p in parts if not HOPE.search(p)).strip() if HOPE.search(reply) else reply
