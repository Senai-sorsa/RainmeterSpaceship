"""memory: moved verbatim from jarvis.py (refactor). See JARVIS-Repair-Plan.txt, REFACTOR."""
import json
import os
import re
import threading
import time
from collections import Counter
from datetime import datetime
from .base import DATA, log, setting, write_atomic
from .llm import chat_json, pick_model
from .meaning import MEANING_TALK, STAMP, meaning
from .notes import STOP
from .reminders import when


# "remember that my dentist is on Fridays": one fact a line in Data\jarvis_memory.txt, added to every prompt.
# Plain text on this PC and sent only to the local model, but he reads it out when asked: no passwords in it.
MEMORY_FILE = os.path.join(DATA, "jarvis_memory.txt")
MEMORY_BAD = "I can't read my memory file, so I left it alone."


def load_memory():
    """The remembered facts. A file that cannot be read raises OSError / ValueError, like load_reminders()."""
    if not os.path.exists(MEMORY_FILE):
        return []
    with open(MEMORY_FILE, "r", encoding="utf-8") as f:
        return [line.strip() for line in f.read().splitlines() if line.strip()]


def save_memory(facts):
    write_atomic(MEMORY_FILE, "".join(fact + "\n" for fact in facts))


def facts_about(x):
    """The saved facts about x: all of them for "me", else the ones related() to it. Unreadable raises."""
    facts = load_memory()
    if re.fullmatch(r"(?:me|myself)\W*", x.strip().lower()):
        return facts
    return [f for f in facts if related(x, [f])]


def fact_save(fact):
    """route() for a save: an older fact about the same thing asks "Replace?" first; anything else saves."""
    fact = " ".join(fact.split())[:200]
    try:
        facts = load_memory()
    except (OSError, ValueError):
        return ("memory", "save", fact, None)                  # memory_reply says it can't read the file
    new = keywords(fact)
    same = [f for f in facts if f != fact and new and len(new & keywords(f)) * 2 >= len(new)]   # half its words or more
    if fact in facts or not same:
        return ("memory", "save", fact, None)
    old = max(same, key=lambda f: len(new & keywords(f)))
    return ("act", "replace_fact", (old, fact), f"You told me '{old}'. Replace it with this? Confirm with yes.")


ACTIVE_TTL = 120      # seconds after the last exchange that the window is still sent
TALK_STOP = STOP | set("how who why whom whose its they them their there then than also just really very not don't "
                       "does did has had will well now yes yeah okay please jarvis want need know think get got going "
                       "like one some more much many all our out into over too let".split())
FOLLOW_START = re.compile(r"(?:it|that|this|he|she|they|and|but|so|what about|how about|why|then|also)\b")


def keywords(text):
    """Content words of a line, for matching talk to talk (L1, later L2 / L4): lowercase, no time stamp,
    stop-words out, a trailing "s" cut."""
    words = re.findall(r"[a-z0-9']+", STAMP.sub("", text).lower().replace("’", "'"))
    words = [w.removesuffix("'s").strip("'") for w in words]
    return {w[:-1] if w.endswith("s") and len(w) > 3 else w for w in words if len(w) > 2 and w not in TALK_STOP}


def related(text, lines):
    """Talk matching for L1 / L2 / L4: a shared keyword, or close in meaning (MEANING_TALK)."""
    return bool(keywords(text) & set().union(set(), *map(keywords, lines))) or meaning(text, lines, MEANING_TALK)


# M2 topic memory: talk that leaves the window is filed by topic in Data\jarvis_topics.json, and comes back only
# when a question is about that topic. Plain text on this PC, sent only to the local model; only counts are logged.
TOPICS_FILE = os.path.join(DATA, "jarvis_topics.json")
SECRET = re.compile(r"\d{6,}|\b(?=\w*\d)(?=\w*[a-z])\w{8,}\b", re.I)   # long numbers and password-like words
RECALL_FLOOR = 1.5    # one rare shared word scores 1.0: not enough alone, so "time" or "day" never pulls a topic in


def recall_on():
    return setting("JarvisRecall", "on").strip().lower() not in ("off", "0")


def load_topics():
    """[{"kw": [...], "talk": [[when, you, him], ...], "used": time}]. Unreadable raises OSError / ValueError."""
    if not os.path.exists(TOPICS_FILE):
        return []
    with open(TOPICS_FILE, "r", encoding="utf-8") as f:
        topics = json.load(f)
    if not isinstance(topics, list) or not all(isinstance(t, dict) and {"kw", "talk", "used"} <= t.keys() for t in topics):
        raise ValueError("not a topic list")
    return topics


def save_topics(topics):
    write_atomic(TOPICS_FILE, json.dumps(topics))


def topic_text(t):
    """What a topic is about, for the meaning match: your side of its talk."""
    return " ".join(you for _, you, _ in t["talk"])


def file_talk(msgs):
    """Files the chat exchanges in msgs into topics: it joins the topic sharing 2 keywords, or 1 found in no other
    topic, else starts a new one. fixed() stamps command replies, so those are left out."""
    pairs = [(u["content"], a["content"]) for u, a in zip(msgs[::2], msgs[1::2]) if not STAMP.match(u["content"])]
    if not pairs or not recall_on():
        return
    try:
        topics = load_topics()
    except (OSError, ValueError):
        log("topic memory unreadable: left alone")
        return
    for you, him in pairs:
        you, him = (SECRET.sub("[number]", s)[:200] for s in (you, him))
        kw = keywords(you + " " + him) - {"number"}
        if not kw:
            continue
        seen = Counter(w for t in topics for w in t["kw"])
        best = max(topics, key=lambda t: len(kw & set(t["kw"])), default=None)
        shared = kw & set(best["kw"]) if best else set()
        if not (len(shared) >= 2 or any(seen[w] == 1 for w in shared)):
            best = {"talk": []}
            topics.append(best)
        best["talk"] = (best["talk"] + [[round(time.time()), you, him]])[-6:]
        best["kw"] = sorted(set().union(*(keywords(y + " " + h) for _, y, h in best["talk"])) - {"number"})
        best["used"] = time.time()
    topics.sort(key=lambda t: t["used"])
    try:
        save_topics(topics[-200:])     # M3 brings it back to 100 each day; past 200 the oldest goes without a gist
        log(f"topic memory: {len(pairs)} exchange(s) filed, {len(topics[-200:])} topics")
    except OSError as e:
        log(f"topic memory not saved ({type(e).__name__})")


def recall(text):
    """The best 2 filed topics for this question, about 600 characters, or "". Score: shared keywords weighted by
    rarity, + RECALL_FLOOR when close in meaning (words OR meaning), at least RECALL_FLOOR; recent use breaks ties."""
    if not recall_on():
        return ""
    try:
        topics = load_topics()
    except (OSError, ValueError):
        return ""
    kw, now = keywords(text), time.time()
    seen = Counter(w for t in topics for w in t["kw"])
    scored = []
    for t in topics:
        s = sum(1 / seen[w] for w in kw & set(t["kw"]))
        if s < RECALL_FLOOR and meaning(text, [topic_text(t)], MEANING_TALK):
            s += RECALL_FLOOR
        if s >= RECALL_FLOOR:
            scored.append((s + 0.2 * max(0.0, 1 - (now - t["used"]) / (7 * 86400)), t))
    best = [t for _, t in sorted(scored, key=lambda p: -p[0])[:2]]
    gist = gist_for(text)                                      # M3: the checked facts of older talks
    if not best:
        return EARLIER + gist if gist else ""
    # newest exchange of each topic first, taking turns, until about 600 characters
    lines = sorted(((i, f"- {datetime.fromtimestamp(when):%a %d %b}: the user said: {you} / you said: {him}")
                    for t in best for i, (when, you, him) in enumerate(reversed(t["talk"]))), key=lambda p: p[0])
    out = ""
    for _, line in lines:
        if out and len(out) + len(line) > 600:
            break
        out += line + "\n"
    for t in best:
        t["used"] = now
    try:
        save_topics(topics)
    except OSError:
        pass                                                   # only "used" is lost
    log(f"topic memory: {len(best)} topic(s) recalled")
    return EARLIER + out + gist


EARLIER = "\nFROM EARLIER TALKS (only if it helps; don't bring it up otherwise):\n"


TOPICS_BAD = "I can't read my topic memory, so I left it alone."
NO_TALK = "I don't remember us talking about that."


def topics_about(x):
    """M2b: the filed topics about X: all of its keywords, or close in meaning. Unreadable raises OSError / ValueError."""
    kw = keywords(x)
    return [t for t in load_topics() if (kw and kw <= set(t["kw"])) or meaning(x, [topic_text(t)], MEANING_TALK)]


def gist_about(x):
    """Compacted (date, fact) rows in jarvis_gist.txt about X: the same match talk_list reads out."""
    kw = keywords(x)
    return [(d, f) for d, f in load_gist()[0] if (kw and kw <= keywords(f)) or meaning(x, [f], MEANING_TALK)]


def talk_forget(x):
    """The route for "forget what we said about X": read the matching talks and gist lines back and ask (the usual yes).
    The action's list holds the talks (lists) and the gist facts (strings)."""
    try:
        hits, gists = topics_about(x), gist_about(x)
    except (OSError, ValueError):
        return ("say", None, None, TOPICS_BAD)
    if not hits and not gists:
        return ("say", None, None, NO_TALK)
    shown = [t["talk"][0][1][:80] for t in hits[:3]] + [f[:80] for _, f in gists][:max(0, 3 - len(hits))]
    said = "; ".join(shown) + ("; and more" if len(hits) + len(gists) > 3 else "")
    n = len(hits) + len(gists)
    what = "talk" if not gists else "item"
    return ("act", "forget_talk", [t["talk"] for t in hits] + [f for _, f in gists],
            f"Forget {n} earlier {what}{'s' if n != 1 else ''} about that, starting with: {said}? Confirm with yes.")


def talk_list(x):
    """What you said in the talks about X, newest first, about 300 characters, then up to 3 gist lines about X."""
    try:
        hits = topics_about(x)
        notes = [f for _, f in gist_about(x)][:3]
    except (OSError, ValueError):
        return TOPICS_BAD
    if not hits:
        return "From before: " + "; ".join(notes) + "." if notes else NO_TALK
    out = ""
    for you in (you for t in hits for _, you, _ in reversed(t["talk"])):
        if out and len(out) + len(you) > 300:
            break
        out += ("; " if out else "") + you.rstrip(".!? ")
    return f"You asked me: {out}." + (" From before: " + "; ".join(notes) + "." if notes else "")


# M3: once a day while idle, old topics become up to 3 tiny facts each in Data\jarvis_gist.txt ("date|fact" lines,
# "#month YYYY-MM" = the last re-compaction). The model writes them; code checks every one against the saved talk.
GIST_FILE = os.path.join(DATA, "jarvis_gist.txt")
GIST_AGE = 7 * 86400
GIST_SCHEMA = {"type": "object", "properties": {"facts": {"type": "array", "items": {"type": "string"}}}, "required": ["facts"]}
GIST_PROMPT = ("Write at most 3 short facts worth keeping from these lines, each under 120 characters, starting "
               "'The user'. Use only words, names and numbers that appear in the lines; add nothing. Output JSON only.")
gist_day = [""]       # the day compaction last finished
gisting = threading.Lock()


def load_gist():
    """([(date, fact)], month of the last re-compaction). Unreadable raises OSError / ValueError."""
    if not os.path.exists(GIST_FILE):
        return [], ""
    with open(GIST_FILE, "r", encoding="utf-8") as f:
        rows = [l.rstrip("\n") for l in f if l.strip()]
    month = next((r[7:] for r in rows if r.startswith("#month ")), "")
    return [tuple(r.split("|", 1)) for r in rows if not r.startswith("#") and "|" in r], month


def save_gist(lines, month):
    write_atomic(GIST_FILE, "".join(f"{l}\n" for l in ([f"#month {month}"] if month else []) + [f"{d}|{g}" for d, g in lines]))


def gist_for(text):
    """Up to 3 gist lines related to the question (words or meaning), most shared words first."""
    try:
        lines = [g for _, g in load_gist()[0]]
    except (OSError, ValueError):
        return ""
    kw = keywords(text)
    hits = sorted((g for g in lines if related(text, [g])), key=lambda g: -len(kw & keywords(g)))[:3]
    return "".join(f"- earlier: {g}\n" for g in hits)


def gist_ok(fact, talk):
    """The code check: under 120 characters, and every number, name and content word is in the talk ("user" aside)."""
    words = keywords(fact) - TALK_STOP - {"user"}                # "likes" -> "like": a stop-word after the cut
    return (0 < len(fact) <= 120 and bool(words) and words <= keywords(talk)
            and set(re.findall(r"\d+", fact)) <= set(re.findall(r"\d+", talk)))


def ask_gist(model, talk):
    """The model's facts for some talk, unchecked; None when the model is down or answers nonsense."""
    try:
        return [" ".join(str(f).replace("|", "/").split()) for f in chat_json(model, GIST_SCHEMA, GIST_PROMPT, talk, 200, 60)["facts"]][:3]
    except Exception as e:
        log(f"compaction: model not usable ({type(e).__name__})")
        return None


def compact(now, stop=lambda: False):
    """M3a: topics unused GIST_AGE, or the oldest past 100, become checked facts. Nothing passes the check -> the topic
    stays and is tried tomorrow, removed without a gist after 3 such tries. Model down -> all stay, no try counted.
    Returns False when stopped early (a turn started or the HUD left FULL)."""
    try:
        topics = sorted(load_topics(), key=lambda t: t["used"])
        load_gist()
    except (OSError, ValueError):
        log("compaction: memory unreadable, left alone")
        return True
    old = [t for i, t in enumerate(topics) if now - t["used"] > GIST_AGE or i < len(topics) - 100]
    if not old:
        return True
    model, facts, gone, tried, dropped, finished = pick_model(0), [], [], {}, 0, True
    for t in old:
        if stop():
            finished = False
            break
        talk = "\n".join(f"User: {y}\nJARVIS: {h}" for _, y, h in t["talk"])
        got = ask_gist(model, talk) if model else None
        if got is None:                                        # model down: try again tomorrow, nothing counted
            break
        got = [g for g in got if gist_ok(g, talk)]
        if got:
            facts += [(f"{datetime.fromtimestamp(now):%Y-%m-%d}", g) for g in got]
            gone.append(t["talk"])
        elif t.get("tries", 0) >= 2:
            gone.append(t["talk"])
            dropped += 1
        else:
            tried[json.dumps(t["talk"])] = t.get("tries", 0) + 1
    try:
        if facts:                                              # the gist first: a failed topic save repeats, never loses
            have, month = load_gist()
            save_gist(have + facts, month)
        topics = load_topics()                                 # again: a turn may have filed talk meanwhile
        for t in topics:
            if json.dumps(t["talk"]) in tried:
                t["tries"] = tried[json.dumps(t["talk"])]
        save_topics([t for t in topics if t["talk"] not in gone])
    except (OSError, ValueError) as e:
        log(f"compaction: not saved ({type(e).__name__})")
        return True
    log(f"compaction: {len(gone) - dropped} topic(s) -> {len(facts)} fact(s), {len(tried)} kept for tomorrow, "
        f"{dropped} removed without a gist")
    return finished


def recompact(now, stop=lambda: False):
    """M3b: once a month, only over 200 gist lines: among the oldest 100, lines sharing 2+ keywords are merged into
    fewer under the same check. Your facts (jarvis_memory.txt) are never touched."""
    try:
        lines, month = load_gist()
    except (OSError, ValueError):
        return
    this = f"{datetime.fromtimestamp(now):%Y-%m}"
    if len(lines) <= 200 or month == this:
        return
    model, old, gone, merged = pick_model(0), lines[:100], set(), []
    for i, (d, g) in enumerate(old):
        if len(merged) >= 30 or stop():                        # shortcut: about 10 merges a month; plenty at 200+ lines
            break
        group = [j for j in range(i, len(old)) if j not in gone and len((keywords(g) & keywords(old[j][1])) - {"user"}) >= 2]
        if i in gone or len(group) < 2:
            continue
        text = "\n".join(old[j][1] for j in group)
        got = ask_gist(model, text) if model else None
        if got is None:
            return                                             # model down: next idle day
        got = [x for x in got if gist_ok(x, text)]
        if got and len(got) < len(group):
            gone.update(group)
            merged += [(d, x) for x in got]
    try:
        save_gist(merged + [l for j, l in enumerate(lines) if j not in gone], this)
    except OSError as e:
        log(f"re-compaction: not saved ({type(e).__name__})")
        return
    log(f"re-compaction: {len(gone)} line(s) -> {len(merged)}")
