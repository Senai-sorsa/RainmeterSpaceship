"""reply/policy.py (refactor phase 2): reply_chain() gives exactly what the old inline chain gave, and stays lazy: the first
spoken piece comes out before the model stream has finished (the voice timing depends on it). Runs inside the golden
sandbox (tools/golden_common.py: guards, temp RES, frozen clock, no model). Needs TZ=ABC+12 like the other tests."""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
JARVIS = os.path.dirname(HERE)
os.environ.setdefault("TZ", "ABC+12")
sys.path.insert(0, os.path.join(JARVIS, "tools"))
sys.argv[1:] = []
import golden_common as G  # noqa: E402

KNOWN = "CPU load: 18%\nUnread Gmail: 4\nOpen apps: Chrome"


class Blocked(Exception):
    pass


def tokens(text):
    return iter(re.findall(r"\s*\S+", text))


def main():
    texts = [json.loads(l) for l in open(os.path.join(G.GOLDEN_DIR, "reply_corpus.jsonl"), encoding="utf-8") if l.strip()][:150]
    n = 0
    with G.Box() as b:
        J = b.jarvis
        from jarvislib import mood as M
        from jarvislib.reply import policy as P
        assert J.reply_chain is P.reply_chain, "exchange() must use the one chain"
        assert P.ORDER == ("sentences_from", "no_claims", "no_hope", "grounded", "polish")
        for smooth in ("1", "0"):
            b.set_setting("JarvisVoiceSmooth", smooth)
            for cap, serious in ((3, False), (None, True)):
                for text in texts:
                    c1, c2 = [], []
                    old = list(M.polish(M.grounded(M.no_hope(J.no_claims(J.sentences_from(tokens(text), c1), c1)), c1, KNOWN),
                                        c1, cap, serious))
                    new = list(P.reply_chain(tokens(text), c2, KNOWN, cap, serious))
                    assert (old, c1) == (new, c2), (smooth, cap, serious, text, old, new)
                    n += 1
            # laziness: the stream gives one full sentence plus the start of the next, then blocks (raises if read again)
            def blocking():
                yield from tokens("Your physics quiz is at six this evening, sir. Then the")
                raise Blocked("the chain read past the first sentence before releasing it")
            first = next(P.reply_chain(blocking(), [], KNOWN, 3, False))
            assert first.strip() and "Then" not in first, (smooth, first)
    print(f"reply policy: {n} replays equal to the old chain, first piece released before the stream ended (smooth 1 and 0): OK")


if __name__ == "__main__":
    main()
