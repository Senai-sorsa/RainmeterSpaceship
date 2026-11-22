"""helpdocs: known CSpace problems and fixes (help_cspace.txt), found by meaning with the same model that picks the HUD blocks."""
import os
import re
from .base import RES, log
from .meaning import _embed, closeness
from .memory import keywords

HELP_FILE = os.path.join(RES, "Jarvis", "help_cspace.txt")
HELP_FLOOR = 0.35         # as MEANING_TALK: a passage rides along only when it is plausibly the answer
_cache = {"mtime": None, "items": []}


def help_items():
    """[(topic, full text)] from the file; [] when it is missing. Re-read only when the file changed."""
    try:
        mt = os.path.getmtime(HELP_FILE)
        if mt != _cache["mtime"]:
            with open(HELP_FILE, "r", encoding="utf-8", errors="ignore") as f:
                paras = [p.strip() for p in re.split(r"\n\s*\n", f.read()) if ":" in p]
            _cache["items"] = [(p.split(":", 1)[0], " ".join(p.split())) for p in paras]
            _cache["mtime"] = mt
    except OSError:
        _cache["items"] = []
    return _cache["items"]


def help_hits(question, limit=2):
    """The passages closest in meaning to the question (shared content words when the model is off), best first."""
    scored = []
    for topic, text in help_items():
        if _embed[0] is not None:
            s = closeness(question, [topic])
        else:
            s = 0.4 if len(keywords(question) & keywords(topic)) >= 2 else 0.0
        if s >= HELP_FLOOR:
            scored.append((s, text))
    if not scored:
        log("help: nothing close") if help_items() else None
    return [t for _, t in sorted(scored, reverse=True)[:limit]]
