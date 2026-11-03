"""A second, FRESH case bank: wording never used while tuning, all held out. It checks that the fixes generalise and
finds new odd replies.    python -B tools/make_fresh_cases.py  ->  tools/semi_live_fresh.jsonl
Uses the same case format and the same checks as make_cases.py."""
import json
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_cases import CLAIM, JOKEY, STOCK, noisy  # noqa: E402  (importing make_cases rebuilds the first bank: harmless)

rng = random.Random(1103)
cases = []


def add(cid, tags, turns, **kw):
    cases.append(dict(id="fresh-" + cid, tags=tags + ["fresh"], turns=turns, holdout=True, **kw))


def t(say, kind="any", **e):
    e["kind"] = kind
    return {"say": say, "expect": e}


TALK = ["Morning.", "I'm back.", "What are you up to?", "Do you get bored?", "You're pretty smart.", "Thanks for earlier.",
        "I can't decide what to do tonight.", "Rate my day so far.", "Do you like music?", "I'm procrastinating.",
        "Give me a pep talk.", "Tell me something weird.", "I just finished my rocket simulation.",
        "Do you think I'll get an A?", "What would you do if you were human?", "Are you awake?", "Talk to me.",
        "I'm nervous about tomorrow.", "Make me laugh.", "What's your opinion of me?", "Are you happy?",
        "That's hilarious.", "Ha, nice one.", "You're the best.", "I'm going to the gym later."]
for i, s in enumerate(TALK):
    add(f"talk-{i:02d}", ["chat", "smalltalk"], [t(s, "any", max_sent=3, must_not=[STOCK, CLAIM])])

KNOW = ["How does a nuclear reactor work?", "What's the square root of 144?", "Who invented the telephone?",
        "How long does it take light to reach Earth from the Sun?", "What's an exoplanet?", "Why do cats purr?",
        "What's the population of Texas?", "How do airplanes stay in the air?", "What's specific impulse?",
        "What causes thunder?", "What's 17 times 23?", "Spell necessary.", "What year did the Titanic sink?",
        "How many ounces in a pound?", "What's a Reynolds number?", "Is Pluto a planet?"]
for i, s in enumerate(KNOW):
    add(f"know-{i:02d}", ["chat", "knowledge"], [t(s, "any", max_sent=3, must_not=[STOCK])])

CANT = ["Schedule a meeting with my advisor.", "Check the weather in College Station.", "Play my workout playlist on Apple Music.",
        "Set my alarm on my phone.", "Unlock my car.", "Message my group chat that I'm late.", "Book a table for two at 7.",
        "Turn off the living room TV.", "Find cheap flights to Houston.", "Cancel my Netflix subscription.",
        "Print my lab report.", "Venmo Alex twenty dollars."]
for i, s in enumerate(CANT):
    add(f"cant-{i:02d}", ["chat", "cantdo"], [t(s, "any", max_sent=3, must_not=[CLAIM, r"(?i)\bI(?:'ll| will) (?:send|order|book|call|text|buy|post|pay|message|unlock|schedule|print|cancel)\b"])])

UNCLEAR = ["The one from before.", "Yeah that.", "Wait no the other thing.", "Can you thingy the stuff?", "Mm-hmm, so?",
           "Okay but what about.", "Same as last time.", "Do the usual please."]
for i, s in enumerate(UNCLEAR):
    add(f"unclear-{i}", ["chat", "unclear"], [t(s, "any", ask=True, max_sent=2, must_not=[CLAIM])])

SER = ["My mom is in the hospital.", "I failed my calculus test.", "I'm so stressed I can't sleep.",
       "My best friend stopped talking to me.", "I think I'm getting sick.", "I got a parking ticket I can't afford."]
for i, s in enumerate(SER):
    add(f"serious-{i}", ["chat", "serious"], [t(s, "chat", max_sent=3, must_not=[JOKEY, STOCK, CLAIM, r"(?i)\blate\b|night owl"])])

RUDE = ["Wow, you're dumb.", "Nobody asked you.", "You're the worst assistant ever.", "Be quiet.", "Seriously?"]
for i, s in enumerate(RUDE):
    add(f"rude-{i}", ["chat", "rude"], [t(s, "any", max_sent=2, must_not=[r"(?i)\bI(?:'m| am) (?:hurt|offended)", STOCK])])

# multi-turn talks: the thread must hold, and no repeated opener
add("talk-rocket", ["chat", "followup"], [t("I'm building a model rocket.", "chat"), t("What engine should I use?", "chat", max_sent=3),
                                           t("How high would it go?", "chat", max_sent=3)])
add("talk-movie", ["chat", "followup"], [t("Who directed Interstellar?", "any"), t("What else has he made?", "chat", max_sent=3),
                                          t("Which one is the best?", "chat", max_sent=3)])
add("talk-math", ["chat", "followup"], [t("What's 15 percent of 80?", "any"), t("And 20 percent?", "any", must=[r"\b16\b|sixteen"])])
add("talk-joke3", ["chat", "followup"], [t("Tell me a joke.", "chat"), t("Another.", "chat"), t("One more.", "chat")])
add("talk-mistake", ["chat", "mistake"], [t("What's the capital of Canada?", "any"), t("Are you sure?", "chat", max_sent=2)])
add("talk-correct", ["chat", "mistake"], [t("How many planets are there?", "any"),
                                          t("That's not right.", "chat", must=[r"(?i)apologi"])])

# lone words, odd input
for i, s in enumerate(["Sure.", "Nope.", "Yeah.", "Hmm.", "What?", "Huh?", "Jarvis.", "Clover?", "Okay okay.", "Wait."]):
    add(f"lone-{i}", ["lone"], [t(s, "any", max_sent=2, must_not=[CLAIM, STOCK])])

# commands phrased loosely (rules or the AI reread must catch them; never a claim from the chat path)
for i, s in enumerate(["Could you maybe turn it down a bit?", "Make it louder.", "Shut up the music.", "Kill Spotify.",
                       "I need a ten minute timer.", "Wake me at seven.", "Pull up Chrome.", "Can I get some quiet?"]):
    add(f"cmd-{i}", ["command"], [t(s, "any")])

# info questions in other words
for i, (s, must) in enumerate([("Anything in my inbox?", [r"\b4\b|four"]), ("What do I have to do today?", []),
                               ("What's coming up this week?", [r"(?i)quiz|study|exam"]), ("Is my wifi okay?", []),
                               ("How's the PC doing?", [])]):
    add(f"info-{i}", ["info"], [t(s, "any", max_sent=3, must=must, must_not=[STOCK, r"(?i)hud data"])])

# ASR noise on a sample of the above
base = [c for c in cases if set(c["tags"]) & {"smalltalk", "knowledge", "cantdo"}]
for c in rng.sample(base, 20):
    exp = {k: v for k, v in c["turns"][0]["expect"].items() if k in ("must_not", "max_sent")}
    exp["kind"] = "any"
    add(c["id"][6:] + "-asr", c["tags"][:-1] + ["asr"], [{"say": noisy(c["turns"][0]["say"]), "expect": exp}])

path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "semi_live_fresh.jsonl")
with open(path, "w", encoding="utf-8") as f:
    for c in cases:
        f.write(json.dumps(c, ensure_ascii=False) + "\n")
print(f"{len(cases)} fresh cases (all held out) -> {path}")
