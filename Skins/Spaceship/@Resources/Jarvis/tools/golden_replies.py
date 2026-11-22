"""Golden reply table (refactor plan phase 0.3): the reply chain of jarvis.py exchange() replayed over recorded text,
so a refactor of the chunker and the filters can be checked byte for byte. No model, no audio (see golden_common.py).

    TZ=ABC+12 python -B tools/golden_replies.py --build-corpus  # 600 sampled replies from semi-live-results + trigger lines
                                                                 #   -> tests/golden/reply_corpus.jsonl (committed)
    TZ=ABC+12 python -B tools/golden_replies.py                 # write tests/golden/replies.jsonl
    TZ=ABC+12 python -B tools/golden_replies.py --check         # compare; exit 1 on any diff

The chain is the one in exchange() (jarvis.py, "said = mood.polish(...)"):
    polish(grounded(no_hope(no_claims(sentences_from(stream, collected), collected)), collected, known), collected, cap, serious)
Each text is fed as a lazy token stream (" word" pieces, like Ollama), under 4 configs: JarvisVoiceSmooth 1/0 x
(cap 3, not serious) / (no cap, serious). Recorded: the pieces yielded, "".join(collected), clean_reply(), log lines.
The recorded texts are already filtered once; they are a regression corpus, not model output. TRIGGERS adds lines that
make each filter act."""
import argparse
import glob
import json
import os
import random
import re
import sys

import golden_common as G

CORPUS = os.path.join(G.GOLDEN_DIR, "reply_corpus.jsonl")
OUT = os.path.join(G.GOLDEN_DIR, "replies.jsonl")
RESULTS = os.path.join(G.HERE, "semi-live-results")
KNOWN = ("CPU load: 18%\nGPU load: 9%\nGPU temperature: 52 C\nPending: no alarms, reminders or timers\n"
         "Unread Gmail: 4\nUpcoming calendar events: Physics quiz at 6:00 PM\n"   # the data-line formats mood.miscounted() reads
         "Open to-dos: Finish the physics lab report; Email Professor Lim\nOpen apps: Chrome, Code, Spotify")
SAMPLE = 600                                                   # recorded replies kept (seeded sample of the unique ones)
CONFIGS = [("1", 3, False), ("1", None, True), ("0", 3, False), ("0", None, True)]
TRIGGERS = [                                                   # one or more per filter; text only, nothing runs
    "Done, sir. I've locked the computer.",
    "The computer will lock in 30 seconds, sir.",
    "Spotify is now open, sir.",
    "I'll send an email to your professor, sir.",
    "I can inform your professor about the delay.",
    "I hope this helps! Let me know if you need anything else.",
    "How may I assist you, sir?",
    "I'd be happy to help, but I need more details. However,",
    "Certainly, sir. The answer is four, sir. Anything else, sir?",
    "Good evening, Mr. Sorsa. Mr. Sorsa, the time is late.",
    "One. Two. Three. Four. Five. Six. Seven. Eight. Nine. Ten.",
    "Pardon, sir? Could you repeat that? I didn't catch it.",
    "Your WiFi signal is at 85%, sir.",
    "Your GPU temperature is 52 degrees, sir.",
    "Your CPU is running at 85% capacity.",
    "You have no unread emails, sir.",
    "You have 2 unread emails, sir.",
    "You have no events today, sir.",
    "You have no tasks left, sir.",
    "No apps are open right now.",
    "You have 4 unread emails, sir.",
    "Would you like me to set a reminder for that, sir?",
    "Dr. Smith said the meeting is at 3 p.m. today, sir... which is, of course, unfortunate.",
    "The answer is 3.14, roughly. Mr. Sorsa, that is pi.",
    "Well — it depends; the first option is cheaper, but the second one, honestly, lasts much longer and is better built.",
    "Yes.",
    "Very good, sir.",
    "I can't do that from here, sir.",
]


def build_corpus():
    texts = []
    for path in sorted(glob.glob(os.path.join(RESULTS, "*.jsonl"))):
        for line in open(path, encoding="utf-8"):
            if not line.strip():
                continue
            for t in json.loads(line).get("turns", []):
                said = " ".join(" ".join(s) for s in t.get("spoken", [])).strip()
                if said:
                    texts.append(said)
    seen = sorted(set(texts) - set(TRIGGERS))
    pick = sorted(random.Random(7).sample(seen, min(SAMPLE, len(seen))))   # a fixed sample keeps the golden file small
    rows = TRIGGERS + pick
    with open(CORPUS, "w", encoding="utf-8", newline="\n") as f:
        f.write("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))
    print(f"corpus: {len(TRIGGERS)} trigger lines + {len(pick)} of {len(seen)} recorded replies "
          f"from {len(glob.glob(os.path.join(RESULTS, '*.jsonl')))} result files -> {os.path.relpath(CORPUS, G.JARVIS_DIR)}")


def tokens(text):
    for piece in re.findall(r"\s*\S+", text):                  # lazy, like a model stream
        yield piece


def run():
    texts = [json.loads(l) for l in open(CORPUS, encoding="utf-8") if l.strip()]
    rows = []
    with G.Box() as b:
        J = b.jarvis
        from jarvislib import mood as M
        for smooth, cap, serious in CONFIGS:
            b.set_setting("JarvisVoiceSmooth", smooth)
            for text in texts:
                b.reset()
                collected = []
                try:
                    said = M.polish(M.grounded(M.no_hope(J.no_claims(J.sentences_from(tokens(text), collected), collected)),
                                               collected, KNOWN), collected, cap, serious)
                    pieces = list(said)
                    row = {"text": text, "cfg": [smooth, cap, serious], "pieces": pieces,
                           "collected": "".join(collected), "clean": M.clean_reply("".join(collected).strip())}
                except Exception as e:
                    row = {"text": text, "cfg": [smooth, cap, serious], "raises": type(e).__name__ + ": " + str(e)[:120]}
                row["logs"] = list(b.logs)
                rows.append(json.dumps(row, ensure_ascii=False))
        trips = list(G.SL.TRIPS)
    return rows, trips


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--build-corpus", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    sys.argv[1:] = []
    if a.build_corpus:
        build_corpus()
        return 0
    rows, trips = run()
    print(f"replays: {len(rows)}, tripwires: {len(trips)}")
    return G.diff_lines(OUT, rows, a.check) or (1 if trips else 0)


if __name__ == "__main__":
    sys.exit(main())
