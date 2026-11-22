"""reply/pardon.py: when the words were clear, an answer that opens with "Pardon sir, what did you say?" is replaced by a second
answer (asked with a firm hint); unclear words and ordinary answers are left alone; the pieces stay lazy. Fakes only: no model,
no audio, no system calls. Runs in the golden sandbox (temp RES, so the real log is never written)."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
JARVIS = os.path.dirname(HERE)
os.environ.setdefault("TZ", "ABC+12")
sys.path.insert(0, os.path.join(JARVIS, "tools"))
sys.argv[1:] = []
import golden_common as G  # noqa: E402


def main():
    with G.Box():
        from jarvislib.reply import pardon as P
        calls = []

        def maker(first, second):
            def make(messages):
                calls.append([m["content"] for m in messages])
                return iter(first if len(calls) == 1 else second)
            return make

        msgs = [{"role": "system", "content": "SYS"}, {"role": "user", "content": "you are annoying"}]
        asks = ["Pardon sir, what did you say?", "Pardon, sir, what did you say?", "I didn't catch that, sir.",
                "Could you repeat that, sir?", "Sorry sir, what did you say?", "Pardon me, sir. Could you say that again?"]
        fine = ["Pardon me, sir, but I don't have that reading.", "That's a fair point, sir.", "Sorry to hear that, sir.",
                "I have been functioning well, sir.", "Sir, you asked what time it was."]
        for t in asks:
            assert P.asks_again(t), t
        for t in fine:
            assert not P.asks_again(t), t

        # clear words + a "Pardon" opening: asked again with the hint, the second answer is the one used, the first is closed
        calls.clear()
        closed = []

        class First:
            def __init__(self):
                self.it = iter(["Par", "don sir, ", "what did ", "you say?"])

            def __iter__(self):
                return self

            def __next__(self):
                return next(self.it)

            def close(self):
                closed.append(1)
        first = First()
        out = "".join(P.no_pardon(lambda m: first if len(calls.append([x["content"] for x in m]) or calls) == 1 else iter(["Indeed, ", "sir."]),
                                  msgs, True))
        assert out == "Indeed, sir." and len(calls) == 2 and closed == [1], (out, calls, closed)
        assert P.NUDGE in calls[1][0] and calls[1][0].startswith("SYS") and calls[0] == ["SYS", "you are annoying"], calls
        assert msgs[0]["content"] == "SYS", "the caller's messages are never changed"

        # token by token, as Ollama sends it: the ask is only recognised at the end of the sentence, so the look-ahead must reach it
        calls.clear()
        toks = ["Pard", "on", " sir", ",", " what", " did", " you", " say", "?"]
        out = "".join(P.no_pardon(maker(toks, ["Fair", " enough", ", sir."]), msgs, True))
        assert out == "Fair enough, sir." and len(calls) == 2, (out, calls)
        # an ordinary first answer: one call, the pieces unchanged
        calls.clear()
        out = "".join(P.no_pardon(maker(["That is a fair ", "point, sir. ", "Noted."], []), msgs, True))
        assert out == "That is a fair point, sir. Noted." and len(calls) == 1, (out, calls)
        # words that were NOT clear (Whisper unsure): the "Pardon" stands, one call
        calls.clear()
        out = "".join(P.no_pardon(maker(["Pardon sir, what did you say?"], ["never used"]), msgs, False))
        assert out == "Pardon sir, what did you say?" and len(calls) == 1, (out, calls)
        # the second answer also asks: it is used as it is (no third call)
        calls.clear()
        out = "".join(P.no_pardon(maker(["Pardon sir, what did you say?"], ["Pardon, sir?"]), msgs, True))
        assert out == "Pardon, sir?" and len(calls) == 2, (out, calls)
        # lazy: the first pieces of an ordinary answer come out before the stream is used up
        seen = []

        def lazy():
            for p in ["Good ", "evening, sir. ", "All is well. ", "Truly."]:
                seen.append(p)
                yield p
        g = P.no_pardon(lambda m: lazy(), msgs, True)
        assert next(g) == "Good " and len(seen) < 4, seen
    print("pardon: asks recognised, retry once with the hint, unclear words and ordinary answers untouched, lazy: OK")


if __name__ == "__main__":
    main()
