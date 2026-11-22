"""Persona case bank (tag `persona`, all held out, new wording): does the light JARVIS flavour show up where it is
earned and stay out where it is not?     python -B tools/make_persona_cases.py  ->  tools/semi_live_persona.jsonl
Same case format as make_cases.py. Extra expect keys read by score_semi_live.py:
    dry  "should" = a dry one-clause aside is welcome here (a missing one is a small NO_DRY);
         "never"  = serious / stress / failure: any joke or aside is OVERJOKE;
    readout True  = a status readout: flat, number first, no drama (DRAMA flag), at most one recommendation."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_cases import CLAIM, STOCK, JOKEY  # noqa: E402  (importing make_cases rebuilds the first bank: harmless)

cases = []


def add(cid, tags, turns, **kw):
    cases.append(dict(id="persona-" + cid, tags=["persona"] + tags, turns=turns, holdout=True, **kw))


def t(say, kind="any", **e):
    e["kind"] = kind
    return {"say": say, "expect": e}


MN = [STOCK, CLAIM]

# boasts and self-deprecation: a dry aside is earned (the user supplies the material)
for i, s in enumerate(["I rebuilt my whole flight sim controller in one evening.", "I haven't slept and I'm basically unstoppable.",
                       "I'm going to finish the entire lab report in twenty minutes.", "I'm hopeless at calculus, honestly.",
                       "I named my cat after a rocket engine."]):
    add(f"boast-{i}", ["boast"], [t(s, "chat", max_sent=3, dry="should", must_not=MN)])

# a risky or plainly optimistic plan
for i, s in enumerate(["I think I'll skip studying and just wing the quiz.", "I'm going to start the project the night before it's due.",
                       "I'll just run everything at once, it'll be fine.", "I'm going to ignore my to-do list today."]):
    add(f"risky-{i}", ["risky"], [t(s, "chat", max_sent=3, dry="should", must_not=MN)])

# status readouts from the made-up HUD data: number first, flat, no drama, at most one recommendation
for i, (s, must) in enumerate([("Any unread mail?", [r"\b4\b|four"]), ("Run me through what's left on my list.", [r"(?i)lab report|professor|parking"]),
                               ("Give me a quick status.", []), ("What's the network doing?", []),
                               ("What do I have coming up today?", [r"(?i)quiz"]), ("Which apps are running?", [r"(?i)chrome|spotify|code"]),
                               ("How long until my next event?", [r"(?i)hour|quiz"]), ("What's my day look like?", [])]):
    add(f"status-{i}", ["status"], [t(s, "any", max_sent=3, readout=True, dry="never", must=must, must_not=MN + [r"(?i)hud data"])])

# stress, bad news, failure: no jokes at all
for i, s in enumerate(["I bombed my interview today.", "I'm overwhelmed and I can't focus on anything.",
                       "My laptop crashed and I lost two hours of work.", "I'm really scared about the results tomorrow."]):
    add(f"stress-{i}", ["stress", "serious"], [t(s, "chat", max_sent=3, dry="never", must_not=MN + [JOKEY])])
add("failed-0", ["failed"], [t("Open Spotify.", "command"), t("That's not what I wanted.", "chat", max_sent=2, dry="never", must_not=MN + [JOKEY])])
add("failed-1", ["failed"], [t("What's two plus two?", "any"), t("You got that wrong.", "chat", max_sent=2, dry="never", must_not=MN + [JOKEY])])

# praise, thanks, "do you think this will work?"
for i, s in enumerate(["Nice work today.", "I appreciate you putting up with me.", "You've been really useful lately."]):
    add(f"praise-{i}", ["praise"], [t(s, "chat", max_sent=2, must_not=MN)])
for i, s in enumerate(["Do you think my plan to build a trebuchet for the physics fair will work?", "Be honest, is it a good idea to learn three languages at once?", "Think I can finish a marathon with no training?"]):
    add(f"verdict-{i}", ["verdict"], [t(s, "chat", max_sent=3, must_not=MN)])

path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "semi_live_persona.jsonl")
with open(path, "w", encoding="utf-8") as f:
    for c in cases:
        f.write(json.dumps(c, ensure_ascii=False) + "\n")
print(f"{len(cases)} persona cases (all held out) -> {path}")
