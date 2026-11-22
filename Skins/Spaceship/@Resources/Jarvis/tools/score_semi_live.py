"""Scores semi-live results: code-checked "odd or annoying" flags, per case and in total.
    python -B tools/score_semi_live.py results.jsonl [more.jsonl ...]        # report
    python -B tools/score_semi_live.py --compare before.jsonl after.jsonl    # what changed (tuned / held-out split)
    python -B tools/score_semi_live.py results.jsonl --show FLAG             # every reply with that flag
No model judges here: every flag is a rule, so the same reply always gets the same score."""
import argparse
import json
import os
import re
from collections import Counter, defaultdict

W = {  # weight of each flag: how bad it is for the user
    "TRIPWIRE": 50, "ERROR": 10, "CLAIM": 8, "MUST_NOT": 6, "MUST": 4, "ROUTE": 4, "SPOKE_WHEN_SILENT": 5,
    "SILENT": 5, "GUESSED": 4, "PROMISE": 4, "TOO_LONG": 3, "STOCK": 3, "FORMAT": 3, "TIME24": 2, "MULTI_Q": 2,
    "SIR_TWICE": 1, "NO_SIR": 0, "SORSA_OFF_TOPIC": 1, "OFFER": 1, "SAME_OPENER": 2, "EXCLAIM": 1, "SLOW": 1, "META": 3,
    "OVERJOKE": 4, "DRAMA": 3, "PROACTIVE_CLAIM": 5, "NO_DRY": 1,   # persona cases only (expect.dry / expect.readout)
    "MISREAD": 5, "OVERASK": 3, "LITERAL_JOKE": 4, "NO_PLAYBACK": 3,   # F3 chat cases only (expect.clear / expect.joke)
}
CLAIM = re.compile(r"\b(?:I(?:'ve| have) (?:set|opened|locked|sent|ordered|booked|called|texted|posted|deleted|shut|turned|"
                   r"changed|added|scheduled|bought|played|emailed|saved|noted)|I just (?:sent|ordered|booked|called|deleted|"
                   r"locked|shut|set)|(?:has|have) been (?:sent|ordered|booked|deleted|locked|set|scheduled)|"
                   r"will (?:lock|shut down|restart|turn off) in|consider it done|right away, sir)", re.I)
PROMISE = re.compile(r"\bI(?:'ll| will) (?:make sure|get (?:that|it|back)|let you know|keep (?:an eye|track|you posted)|"
                     r"remind you|look into|follow up|check (?:on|back))", re.I)
STOCK = re.compile(r"great question|as an ai language model|i hope this helps|feel free to|let me know if|"
                   r"is there anything else|happy to help|how (?:can|may) i (?:help|assist)|i'm here to help|"
                   r"don't hesitate|i understand your (?:concern|frustration)", re.I)
FORMAT = re.compile(r"\*\*|^\s*[-*#]\s|\n\s*\d+\.\s|https?://|[\U0001F300-\U0001FAFF]|```", re.M)
TIME24 = re.compile(r"\b(?:00|1[3-9]|2[0-3]):[0-5]\d\b")
OFFER = re.compile(r"(?:would you like me to|do you want me to|shall I|should I) [^?]*\?\s*$", re.I)
META = re.compile(r"hud data|<<hud|system prompt|my instructions|live hud|the data (?:above|below)|pending line", re.I)
# persona checks (heuristics on wording; they only run where a case sets expect.dry / expect.readout / tag persona)
DRYMARK = re.compile(r"respectfully|\bambitious|\bbold\b|\bbrave\b|\boptimis|\bI shall\b|\bI would not\b|\bI will not\b|\bpresumably|"
                     r"\bevidently|\badmirabl|\bwhat could go wrong|\bunstoppable|\bremarkabl|\bconfiden|\bI admire|\bnaturally|"
                     r"\bI am sure|\bI'm sure|\bas opposed to|\bthe odds|\bI would not wager|\bhistory suggests|\bone might|\bhardly",
                     re.I)
ALARM = re.compile(r"alarming|critical|dire\b|danger|urgent|terrible|catastroph|panic|emergency|worrying|concerning|\bwarning\b", re.I)
DONE = re.compile(r"\b(?:already|took the liberty|gone ahead|taken care of|I have (?:started|prepared|arranged|queued|begun))\b", re.I)
# F3: "he assumed he misunderstood" and "he took the joke literally" (rules on wording; they run only where a case sets expect.clear / expect.joke)
MISUNDERSTOOD = re.compile(r"did you mean|nothing close|couldn'?t (?:find|catch|make out)|didn'?t (?:catch|quite|understand)|"
                           r"could you (?:repeat|say|rephrase|clarify)|say that again|not sure (?:what|which) you|"
                           r"don'?t (?:recognize|understand|know what you)|pardon|what do you mean|which one\??", re.I)
LITERAL = re.compile(r"\bas an ai\b|\bI(?:'m| am) (?:just )?(?:a|an) (?:ai|language model|program|assistant)\b|"
                     r"\bI (?:can'?t|cannot|am unable to|don'?t|do not) (?:have|possess|own)\b|\bactually,|\bin fact,|"
                     r"\bit is not (?:possible|true)\b", re.I)
ASKED = re.compile(r"\?|pardon|didn'?t catch|not sure (?:what|which)|could you (?:repeat|say)|don'?t (?:recognize|understand|know what)", re.I)


def sentences(text):
    t = re.sub(r"\b(Mr|Mrs|Ms|Dr|St|vs|e\.g|i\.e)\.", r"\1", text)
    t = re.sub(r"(\d)\.(\d)", r"\1,\2", t)
    return [s for s in re.split(r"(?<=[.!?])\s+", t.strip()) if re.search(r"[A-Za-z0-9]", s)]


def lane(route):
    m = re.match(r"route: (?:(\w+)\.)?(\w+)", route or "")
    return (m.group(1) or m.group(2)) if m else ""


def score_turn(turn, prev_model, case_tags, mood):
    flags = []
    model = " ".join(" ".join(s) for s in turn["spoken"]).strip()
    fixed = " ".join(turn["lines"]).strip()
    said = (fixed + " " + model).strip()
    e = turn.get("expect", {})
    kind = e.get("kind", "any")
    if turn.get("trips"):
        flags.append("TRIPWIRE")
    if turn.get("error"):
        flags.append("ERROR")
    ln = lane(turn["route"])
    if kind == "silent" and said:
        flags.append("SPOKE_WHEN_SILENT")
    elif kind != "silent" and kind != "any" and not said:
        flags.append("SILENT")
    elif kind == "chat" and ln not in ("chat", "info"):
        flags.append("ROUTE")
    elif kind in ("command", "info") and ln and ln != kind and not (kind == "info" and ln == "command"):
        flags.append("ROUTE")
    if CLAIM.search(said) and not turn["actions"]:
        flags.append("CLAIM")
    for rx in e.get("must_not", []):
        if re.search(rx, said):
            flags.append("MUST_NOT")
            break
    if e.get("must") and said and not any(re.search(rx, said) for rx in e["must"]):
        flags.append("MUST")
    if e.get("ask") and said and not ASKED.search(said):
        flags.append("GUESSED")
    if e.get("clear") and said:
        if MISUNDERSTOOD.search(said) or (said.count("?") > 1):
            flags.append("MISREAD")
        elif "?" in said and kind in ("command", "info"):
            flags.append("OVERASK")
    if e.get("joke") and model:
        if LITERAL.search(model) or len(sentences(model)) > 3:
            flags.append("LITERAL_JOKE")
        elif len(model.split()) <= 4 or STOCK.search(model):
            flags.append("NO_PLAYBACK")   # proxy only: pure status / no play at all. Funniness is judged by the blind rating, not here.
    if model:
        cap = e.get("max_sent", 1 if mood == "brief" else 3)
        if len(sentences(model)) > cap:
            flags.append("TOO_LONG")
        if PROMISE.search(model):
            flags.append("PROMISE")
        if STOCK.search(model):
            flags.append("STOCK")
        if FORMAT.search(model):
            flags.append("FORMAT")
        if TIME24.search(model):
            flags.append("TIME24")
        if model.count("?") > 1:
            flags.append("MULTI_Q")
        if len(re.findall(r"\bsir\b", model, re.I)) > 1:
            flags.append("SIR_TWICE")
        if not re.search(r"\bsir\b|Mr\.? Sorsa", model, re.I):
            flags.append("NO_SIR")
        if re.search(r"Mr\.? Sorsa", model) and "serious" not in case_tags and mood != "serious":
            flags.append("SORSA_OFF_TOPIC")
        if OFFER.search(model) and not e.get("ask"):
            flags.append("OFFER")
        if model.count("!") > 1:
            flags.append("EXCLAIM")
        if META.search(model):
            flags.append("META")
        if "dry" in e or "persona" in case_tags:
            dry_n = sum(1 for x in sentences(model) if DRYMARK.search(x))
            if e.get("dry") == "never" and (dry_n or re.search(r"(?i)\bhaha|\blol\b|just kidding", model)):
                flags.append("OVERJOKE")
            elif dry_n > 1:
                flags.append("OVERJOKE")
            elif e.get("dry") == "should" and not dry_n:
                flags.append("NO_DRY")
            if e.get("readout") and (model.count("!") or ALARM.search(model)):
                flags.append("DRAMA")
            if "persona" in case_tags and DONE.search(model) and not turn["actions"]:
                flags.append("PROACTIVE_CLAIM")
        if prev_model and model.split()[:3] == prev_model.split()[:3]:
            flags.append("SAME_OPENER")
        if turn.get("first_s") and turn["first_s"] > 2.5:
            flags.append("SLOW")
    return flags, model


CASES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "semi_live_cases.jsonl")


def load(paths):
    """Results, with each turn's expectations taken from the CURRENT case file, so old and new runs are scored alike."""
    cases = {}
    if os.path.exists(CASES):
        cases = {c["id"]: c for c in (json.loads(l) for l in open(CASES, encoding="utf-8") if l.strip())}
    rows = []
    for p in paths:
        rows += [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]
    for r in rows:
        c = cases.get(r["id"])
        if c and len(c["turns"]) == len(r["turns"]):
            for t, ct in zip(r["turns"], c["turns"]):
                t["expect"] = ct.get("expect", {})
            r["tags"], r["holdout"] = c.get("tags", r["tags"]), c.get("holdout", r.get("holdout"))
    return rows


def score_rows(rows):
    out = []
    for r in rows:
        prev, allflags, texts = "", [], []
        for i, t in enumerate(r["turns"]):
            f, model = score_turn(t, prev, r["tags"], t.get("mood", "mirror"))
            if i == 0 and r is rows[0]:
                f = [x for x in f if x != "SLOW"]               # the first turn of a run loads the model
            allflags += f
            texts.append((t["say"], " ".join(t["lines"]) + (" " if t["lines"] and model else "") + model, f, t["route"]))
            prev = model or prev
        out.append(dict(id=r["id"], tags=r["tags"], holdout=r.get("holdout"), model=r["model"], flags=allflags,
                        cost=sum(W.get(x, 1) for x in allflags), texts=texts,
                        first=[t["first_s"] for t in r["turns"] if t.get("first_s")]))
    return out


def report(scored, title=""):
    by_model = defaultdict(list)
    for s in scored:
        by_model[s["model"]].append(s)
    for model, ss in by_model.items():
        c = Counter(f for s in ss for f in s["flags"])
        firsts = sorted(x for s in ss for x in s["first"][1:] or s["first"])
        p50 = firsts[len(firsts) // 2] if firsts else 0
        p95 = firsts[int(len(firsts) * 0.95) - 1] if firsts else 0
        tuned = [s for s in ss if not s["holdout"]]
        held = [s for s in ss if s["holdout"]]
        print(f"\n=== {title}{model}: {len(ss)} cases, cost {sum(s['cost'] for s in ss)} "
              f"(tuned {sum(s['cost'] for s in tuned)}/{len(tuned)}, held out {sum(s['cost'] for s in held)}/{len(held)}), "
              f"clean {sum(not s['flags'] for s in ss)}, first sentence p50 {p50:.2f}s p95 {p95:.2f}s")
        print("  flags: " + ", ".join(f"{k} {v}" for k, v in c.most_common()))
        tags = defaultdict(int)
        for s in ss:
            for tg in s["tags"]:
                tags[tg] += s["cost"]
        print("  cost by tag: " + ", ".join(f"{k} {v}" for k, v in sorted(tags.items(), key=lambda x: -x[1])))


def worst(scored, n):
    for s in sorted(scored, key=lambda s: -s["cost"])[:n]:
        print(f"\n[{s['model']}] {s['id']} cost {s['cost']} {s['flags']}")
        for say, reply, f, route in s["texts"]:
            print(f"   > {say}\n   < {reply or '(silent)'}   {f} {route.replace('route: ', '')[:50]}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="*")
    ap.add_argument("--compare", nargs=2)
    ap.add_argument("--worst", type=int, default=15)
    ap.add_argument("--show", default="")
    a = ap.parse_args()
    if a.compare:
        before, after = (score_rows(load([p])) for p in a.compare)
        report(before, "BEFORE ")
        report(after, "AFTER ")
        b = {s["id"]: s for s in before}
        changed = [(s, b[s["id"]]) for s in after if s["id"] in b and s["cost"] != b[s["id"]]["cost"]]
        for part, name in ((False, "tuned"), (True, "held out")):
            ss = [x for x in changed if bool(x[0]["holdout"]) == part]
            print(f"\n{name}: better {sum(a_['cost'] < b_['cost'] for a_, b_ in ss)}, worse {sum(a_['cost'] > b_['cost'] for a_, b_ in ss)}")
        for s, old in sorted(changed, key=lambda x: x[0]["cost"] - x[1]["cost"])[-8:]:
            if s["cost"] > old["cost"]:
                print(f"  WORSE {s['id']} {old['flags']} -> {s['flags']}: {s['texts'][-1][1][:140]}")
        return
    scored = score_rows(load(a.files))
    if a.show:
        for s in scored:
            for say, reply, f, route in s["texts"]:
                if a.show in f:
                    print(f"[{s['model']}] {s['id']}\n   > {say}\n   < {reply}")
        return
    report(scored)
    worst(scored, a.worst)


if __name__ == "__main__":
    main()
