"""Golden route table (refactor plan phase 0.2): what the CURRENT code makes of each phrase, so a refactor of the rule
ladder can be checked byte for byte. No model, no OS action (see golden_common.py).

    TZ=ABC+12 python -B tools/golden_routes.py --build-corpus   # (re)collect the phrases -> tests/golden/route_corpus.txt
    TZ=ABC+12 python -B tools/golden_routes.py                  # write tests/golden/routes.jsonl from the corpus
    TZ=ABC+12 python -B tools/golden_routes.py --check          # compare with it; exit 1 on any diff

Per phrase: route(), fix_route(route()), ask_ai(), understand() (AI reread faked to "no reading"), directed() with
answering False/True, level_fix(), percent_follow() after "what's 15 percent of 80", crisis(), no_ability(),
LIVE_FACT match, and the log lines those calls wrote. Session state is reset before every phrase."""
import argparse
import ast
import json
import os
import random
import re
import sys

import golden_common as G

CORPUS = os.path.join(G.GOLDEN_DIR, "route_corpus.txt")
OUT = os.path.join(G.GOLDEN_DIR, "routes.jsonl")
CALLS = {"route", "fix_route", "understand", "directed", "level_fix", "no_ability", "crisis", "turn", "exchange", "ask_ai",
         "percent_follow", "tidy", "pick_last", "diag_route", "strip_name", "for_me", "room_talk", "no_data", "serious"}
PREFIX = ["um ", "uh ", "jarvis ", "hey jarvis, ", "okay ", "so ", "and ", "jarvis, could you ", "can you "]
SUFFIX = [" please", " jarvis", " now", ".", "?"]
SOUND = [(r"\bto\b", "two"), (r"\bfor\b", "four"), (r"\btimer\b", "time her"), (r"\bvolume\b", "volyum"),
         (r"\balarm\b", "a larm"), (r"\bremind\b", "remine"), (r"\bminutes\b", "minits"), (r"\bthe\b", "da")]


def bank_phrases():
    out = []
    for name in ("semi_live_cases.jsonl", "semi_live_fresh.jsonl", "semi_live_persona.jsonl"):
        for line in open(os.path.join(G.HERE, name), encoding="utf-8"):
            if line.strip() and not line.startswith("//"):
                out += [t["say"] for t in json.loads(line)["turns"]]
    return out


def test_phrases():
    tree = ast.parse(open(os.path.join(G.JARVIS_DIR, "test_jarvis.py"), encoding="utf-8").read())
    out = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        f = node.func
        name = f.attr if isinstance(f, ast.Attribute) else f.id if isinstance(f, ast.Name) else ""
        if name in CALLS and node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
            out.append(node.args[0].value)
        for kw in node.keywords:
            if kw.arg == "typed" and isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                out.append(kw.value.value)
    return out


def cue_phrases():
    src = open(os.path.join(G.JARVIS_DIR, "jarvislib", "routing.py"), encoding="utf-8").read()
    prompt = re.search(r'AI_PROMPT = """(.*?)"""', src, re.S).group(1)
    return [q for q in re.findall(r'"([^"]+)"', prompt) if " " in q]


def variants(base, n=300, seed=7):
    rnd = random.Random(seed)
    out = []
    while len(out) < n:
        s = rnd.choice(base)
        op = rnd.randrange(5)
        if op == 0:
            v = rnd.choice(PREFIX) + s[:1].lower() + s[1:]
        elif op == 1:
            v = s.rstrip(".!?") + rnd.choice(SUFFIX)
        elif op == 2:
            v = " ".join(re.sub(r"[^a-z0-9' ]", " ", s.lower()).split())
        elif op == 3:
            w = s.split()
            if len(w) < 3:
                continue
            del w[rnd.randrange(len(w))]
            v = " ".join(w)
        else:
            hits = [(p, r) for p, r in SOUND if re.search(p, s, re.I)]
            if not hits:
                continue
            p, r = rnd.choice(hits)
            v = re.sub(p, r, s, count=1, flags=re.I)
        if v.strip() and v not in base:
            out.append(v)
    return out


def build_corpus():
    base = list(dict.fromkeys(p for p in bank_phrases() + test_phrases() + cue_phrases() if p.strip() and "\n" not in p))
    allp = list(dict.fromkeys(base + variants(base)))
    with open(CORPUS, "w", encoding="utf-8", newline="\n") as f:
        f.write("".join(p + "\n" for p in allp))
    print(f"corpus: {len(base)} phrases + {len(allp) - len(base)} variants -> {os.path.relpath(CORPUS, G.JARVIS_DIR)}")


def run():
    phrases = [l.rstrip("\n") for l in open(CORPUS, encoding="utf-8") if l.strip()]
    rows = []
    with G.Box() as b:
        J = b.jarvis
        from jarvislib import routing as R, mood as M, prompt as P
        for say in phrases:
            b.reset()
            row = {"say": say}

            def safe(key, fn):
                try:
                    row[key] = G.norm(fn())
                except Exception as e:                         # recorded, so a change in what raises shows up too
                    row[key] = "RAISES " + type(e).__name__ + ": " + str(e)[:120]

            safe("route", lambda: R.route(say))
            safe("fix", lambda: R.fix_route(say, R.route(say)))
            safe("ask_ai", lambda: R.ask_ai(say, R.route(say)))
            b.reset()
            safe("understand", lambda: J.understand(say, "none", True, ""))
            b.reset()
            safe("directed", lambda: (J.directed(say, False), J.directed(say, True)))
            safe("level_fix", lambda: J.level_fix(R.strip_name(say)))
            safe("percent_follow", lambda: J.percent_follow(say, "what's 15 percent of 80"))
            safe("crisis", lambda: M.crisis(say))
            safe("no_ability", lambda: P.no_ability(say))
            safe("live_fact", lambda: bool(P.LIVE_FACT.search(say + " ")))
            row["logs"] = list(b.logs)
            rows.append(json.dumps(row, ensure_ascii=False))
        model, trips = list(b.model_calls), list(G.SL.TRIPS)
    return rows, model, trips


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--build-corpus", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    sys.argv[1:] = []                                          # jarvislib reads RES from sys.argv[1]: set by the Box
    if a.build_corpus:
        build_corpus()
        return 0
    rows, model, trips = run()
    print(f"phrases: {len(rows)}, AI rereads asked (faked): {model.count('interpret')}, "
          f"other model calls: {len([m for m in model if m != 'interpret'])}, tripwires: {len(trips)}")
    for t in trips[:10]:
        print("  TRIP", t)
    return G.diff_lines(OUT, rows, a.check) or (1 if trips else 0)


if __name__ == "__main__":
    sys.exit(main())
