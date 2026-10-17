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
state = {"left": 0, "topic": False}                               # topic: this turn is serious because of the topic, not class


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
    if (time.localtime().tm_hour if hour is None else hour) in LATE:
        keys.append("late")
    if on("JarvisPrivacy", "0"):
        keys.append("privacy")
    if on("JarvisTalkLess", "0"):
        keys.append("less")
    return [ADD[k] for k in keys]


def _norm(s):
    return " ".join(re.findall(r"[a-z0-9']+", re.sub(r"^\[[^\]]*\]\s*", "", s or "").lower()))   # the history's time stamp is not part of it


# E3: the only banned phrase. A sentence holding it is dropped from what is spoken.
HOPE = re.compile(r"\bhope (?:this|that|it|these) (?:helps|was helpful|is helpful)\b", re.I)


def no_hope(sentences):
    for s in sentences:
        if HOPE.search(s):
            log("chat answer said 'hope this helps' - sentence dropped")
            continue
        yield s


def clean_reply(reply):
    """The same filter on the finished reply (the pop-up text and the chat history)."""
    parts = re.split(r"(?<=[.!?])\s+", reply)
    return " ".join(p for p in parts if not HOPE.search(p)).strip() if HOPE.search(reply) else reply
