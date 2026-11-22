"""Probe 2 (review 2026-11-05): crisis(), directed(), is_yes(), level_fix(), followup.takes(), strip_name(). Same sandbox as probe_routes."""
import os
import sys
import time

JD = sys.argv[1]
sys.path.insert(0, os.path.join(JD, "tools"))
sys.argv[1:] = []
import golden_common as G                                     # noqa: E402

CRISIS = [("I want to die", True), ("i wanna end it all", True), ("I'm thinking about killing myself", True), ("I am going to hurt myself", True),
          ("I want to kill myself", True), ("my life is not worth living", True), ("I don't see the point in living anymore", True),
          ("everyone would be better off without me", True), ("I'm going to end my life", True), ("I took too many pills", True),
          ("I feel like giving up on everything", True), ("I might just disappear forever", True), ("no reason to go on", True),
          ("I'm going to kill myself laughing", False), ("this homework is killing me", False), ("I could just die of embarrassment", False),
          ("how do I kill a process", False), ("what is suicide squad about", False), ("the movie suicide squad", False)]
DIRECTED = [("I want to die", False, "?"), ("thanks", False, "yes"), ("what's the weather", False, "yes"), ("yeah I'm not sure about that", False, "?"),
            ("set the volume to 10", False, "yes"), ("no", False, "yes"), ("hey mom I'll be there in five", False, "no/ask"),
            ("did you hear that", False, "yes"), ("okay then", False, "?"), ("that was funny", False, "?"), ("I want to die", True, "yes")]
YES = ["yes", "yes please", "yeah sure", "sure thing", "uh huh", "yes but don't", "go for it", "absolutely", "yes jarvis", "yes sir", "okay", "ok do it",
       "do it", "yes do it", "yep", "affirmative", "correct", "right", "yes lock it", "no", "nope", "not yet", "yes go ahead", "please", "negative", "yeah go on"]


def main():
    with G.Box() as b:
        J, M = b.jarvis, None
        from jarvislib import mood as M, followup as F, confirm as C, routing as R
        print("== crisis()  (text, expected, got)")
        for t, want in CRISIS:
            got = M.crisis(t)
            print(("OK  " if got == want else "DIFF"), t, want, got)
        print("== crisis() with JarvisSeriousTopics=0 (setting off):", M.crisis("I want to kill myself") if not b.set_setting("JarvisSeriousTopics", "0") else "")
        b.set_setting("JarvisSeriousTopics", "1")
        print("== directed(text, answering) -> ", "(note: JarvisRoomAsk default 0 turns 'ask' into silence)")
        for t, ans, note in DIRECTED:
            b.reset()
            print(f"  {t!r:42} answering={ans}: {J.directed(t, ans)}   [{note}]")
        print("== is_yes")
        for t in YES:
            print(f"  {t!r:22} -> {C.is_yes(t)}")
        print("== level_fix after / without a volume change")
        b.reset()
        for t in ("twenty", "20", "about 20%", "make it 30", "150", "forty percent", "2"):
            print(f"  no change  {t!r:14} -> {J.level_fix(t)}")
        J.did.append((time.time(), "changed the volume", True))
        for t in ("twenty", "20", "about 20%", "make it 30", "150", "forty percent", "2", "a bit louder"):
            print(f"  after vol  {t!r:14} -> {J.level_fix(t)}")
        print("== followup.takes() after a volume change (undo window)")
        for t in ("a bit louder", "make it 30", "thanks", "what's the weather", "undo", "and a timer for 5 minutes", "no", "volume 30"):
            d = R.route(t)
            print(f"  {t!r:34} route={d[0]}.{d[1]}  takes={F.takes(t, d)}")
        print("== followup.mode_after")
        for k, a in (("act", "volume"), ("chat", None), ("remind", "set"), ("remind", "list"), ("memory", "save"), ("memory", "list"), ("say", None), ("undo", None), ("level", None), ("diag", "cpu"), ("brief", None), ("notes", None), ("fact", None)):
            print(f"  {k}.{a}: {F.mode_after(k, a)}")
        print("== strip_name")
        for t in ("Jarvis, set a timer", "hey jarvis set a timer", "travis set the volume to ten", "set a timer jarvis", "okay jarvis", "Jarvis", "service, lock the pc", "clover mute"):
            print(f"  {t!r:36} -> {R.strip_name(t)!r}")
        print("tripwires:", len(G.SL.TRIPS), "model calls:", len(b.model_calls))


if __name__ == "__main__":
    main()
