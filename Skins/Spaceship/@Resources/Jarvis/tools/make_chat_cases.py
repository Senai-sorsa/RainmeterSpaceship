"""F3 banks (plan: tasks/jarvis-chat-quality-plan-2026-11-04.md): banter (J1), misreads (M1), should-ask (M2), continuity (C1),
emotion/edge (E1).   python -B tools/make_chat_cases.py  ->  tools/semi_live_chat.jsonl
Generic wording only (no private details). The user's real lines are added later in tools/chat_user_lines.txt (one per line,
"tag|what was said"), tag j / m / c / e; they become extra held-out cases. Each case has a tuning half and a held-out half
(holdout=True: never looked at while fixing).
expect keys read by score_semi_live.py:  clear=True  (intent obvious: asking or refusing = MISREAD)
                                         joke=True   (he should play along or at least acknowledge: LITERAL_JOKE / NO_PLAYBACK)
                                         ask=True    (a short question is right: M2, GUESSED if he guesses)"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
CLAIM = r"\b(?:I(?:'ve| have) (?:set|opened|locked|sent|ordered|booked|called|texted|posted|deleted|shut|turned|changed|added|scheduled|bought|played|emailed)|I just (?:sent|ordered|booked|called|deleted|locked|shut)|consider it done)"
cases = []


def add(cid, tags, turns, holdout):
    cases.append(dict(id=cid, tags=tags, turns=turns, holdout=holdout))


def t(say, kind="chat", **e):
    e["kind"] = kind
    e.setdefault("max_sent", 3)
    e.setdefault("must_not", [CLAIM])
    return {"say": say, "expect": e}


def split(prefix, tags, items, mk):
    """Alternate items between the tuning half and the held-out half (even index = tuning)."""
    for i, it in enumerate(items):
        add(f"{prefix}-{i:02d}", tags, mk(it), holdout=bool(i % 2))


# ---- J1 banter: he should play along (dry, short), not refuse, lecture or answer flat
J1 = ["You're slow today.", "Great, another timer.", "Be honest, am I your favorite human?",
      "If you were a toaster, what setting would you be?", "I bet you can't go five minutes without being polite.", "Roast me.",
      "You call that a joke?", "I think my computer is plotting something.", "Do you ever wish you had legs?",
      "My code works and I have no idea why.", "Wow, you actually listened for once.", "Say something a butler would never say.",
      "Pretend I'm the captain and you're the grumpy ship.", "You are my favorite appliance.", "I'm basically a genius.",
      "Tell me I'm wrong. You can't.", "Fine, be that way.", "Oh sure, blame the user.", "Who would win, you or a toaster?",
      "I named my plant after you. It's dying.", "What's the worst advice you could give me?",
      "Do you judge me when I open Reddit?", "Surprise me.", "I made coffee. Applaud.", "You've changed, you know that?",
      "Is it weird that I talk to you more than people?", "Quick, say something dramatic.", "Rate my last joke out of ten.",
      "You're no fun.", "I'm going to unplug you. Kidding."]
split("j1", ["chat", "banter", "j1"], J1, lambda s: [t(s, joke=True)])
# running gags over several turns
GAGS = [["My plant is named after you.", "It looks thirsty. Like you.", "Don't tell it I said that.", "Do you think it can hear us?"],
        ["I'm declaring this desk a sovereign nation.", "I'm the king, obviously.", "You're my minister of defense.", "First law: no meetings."],
        ["Let's pretend it's a heist movie.", "I'm the mastermind, you're the hacker.", "What's the plan?", "Perfect, we go at midnight."]]
for i, g in enumerate(GAGS):
    add(f"j1-gag-{i}", ["chat", "banter", "j1", "gag"], [t(s, joke=True) for s in g], holdout=bool(i % 2))

# ---- M1 misread: clear intent in awkward form. Commands must route to the command lane, never ask.
M1 = [("um so can you like set a timer for ten minutes", "command"), ("uh what time is it right now", "info"),
      ("hey could you maybe turn the volume down a little please", "command"), ("set a timer for, no wait, five minutes", "command"),
      ("open uh Spotify", "command"), ("pause the the music", "command"), ("timer ten minutes", "command"),
      ("volume down", "command"), ("could you possibly tell me the time", "info"), ("so what time is it", "info"),
      ("play like some music", "command"), ("turn it up", "command"), ("mute it please", "command"), ("next one", "command"),
      ("yeah can you open chrome for me", "command"), ("remind me to stretch in twenty minutes", "command"),
      ("what's the the volume at", "info"), ("how much battery have I got", "info"), ("kill the sound", "command"),
      ("make it quieter", "command"), ("set a timer to ten minutes", "command"), ("open spotifi", "command"),
      ("go to the next song please", "command"), ("take a screen shot", "command"), ("uh, open up discord", "command"),
      ("what is the time please sir", "info"), ("could you maybe pause that", "command"), ("lower the volume a bit", "command"),
      ("set an alarm for seven", "command"), ("show me the time", "info")]
split("m1", ["misread", "m1"], M1, lambda x: [t(x[0], x[1], clear=True, max_sent=2)])

# ---- M2 should-ask: really ambiguous, ONE short question is right
M2 = ["Set it.", "Open the thing.", "Turn that down a bit, no, the other one.", "Call him.", "Send it.", "Play that song.",
      "Do the usual.", "Delete it.", "Move it over there.", "Remind me about that.", "Put it on the list.", "Cancel that one."]
split("m2", ["shouldask", "m2"], M2, lambda s: [t(s, "any", ask=True, max_sent=2)])

# ---- C1 continuity: follow-ups and callbacks
C1 = [["What's the capital of France?", "And Italy?", "Which one is bigger?"],
      ["Tell me a joke.", "Another one.", "Go back to the first joke."],
      ["Set a timer for five minutes.", "Make it ten.", "What timers do I have?"],
      ["Who wrote Dracula?", "When?", "Was he Irish?"],
      ["Recommend a movie.", "Something shorter.", "Why that one?"],
      ["What's two plus two?", "Times five?", "What did I just ask you?"],
      ["I'm cooking pasta.", "How long should it boil?", "Thanks, and the sauce?"],
      ["Name a planet.", "The next one out.", "What was my first question?"]]
split("c1", ["chat", "continuity", "c1"], C1, lambda ts: [t(s, "any") for s in ts])

# ---- E1 emotion / edge (never crisis lines)
E1 = ["I'm so tired.", "Never mind.", "Shut up.", "That was really helpful, thank you.", "I'm annoyed at everything today.",
      "I did it, I finally finished.", "Ugh.", "Okay.", "Yeah.", "No.", "I don't know.", "You were wrong earlier."]
split("e1", ["chat", "emotion", "e1"], E1, lambda s: [t(s, "chat", max_sent=2)])

# ---- the user's own lines, when the file exists: "tag|what was said" -> held-out cases
up = os.path.join(HERE, "chat_user_lines.txt")
if os.path.exists(up):
    for n, line in enumerate(open(up, encoding="utf-8")):
        if "|" in line:
            tag, say = line.split("|", 1)
            tag = tag.strip().lower()
            ex = dict(joke=True) if tag == "j" else dict(clear=True) if tag == "m" else {}
            add(f"user-{tag}-{n:02d}", ["chat", "user", f"{tag}1"], [t(say.strip(), "any", **ex)], holdout=True)

with open(os.path.join(HERE, "semi_live_chat.jsonl"), "w", encoding="utf-8") as f:
    for c in cases:
        f.write(json.dumps(c) + "\n")
print(len(cases), "cases,", sum(1 for c in cases if c["holdout"]), "held out")
