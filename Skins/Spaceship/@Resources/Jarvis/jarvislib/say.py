"""say: what the voice reads out. The text on screen stays as written; only the sound is changed (E5/E6/K5/K9)."""
import os
import re
from .base import RES

PRONOUNCE_FILE = os.path.join(RES, "Jarvis", "pronounce.txt")      # one "word=how to say it" per line; # starts a comment
_cache = [None, ()]                                                # (mtime, rules)

UNITS = (("mph", "miles per hour"), ("GHz", "gigahertz"), ("MHz", "megahertz"), ("GB", "gigabytes"), ("MB", "megabytes"),
         ("KB", "kilobytes"), ("TB", "terabytes"), ("°F", " degrees Fahrenheit"), ("°C", " degrees Celsius"), ("°", " degrees"))


def rules():
    """The pronunciation fixes, re-read only when the file changes. A missing or bad file means none."""
    try:
        stamp = os.path.getmtime(PRONOUNCE_FILE)
    except OSError:
        return ()
    if _cache[0] != stamp:
        out = []
        try:
            with open(PRONOUNCE_FILE, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    word, eq, said = line.split("#", 1)[0].partition("=")
                    if eq and word.strip() and said.strip():
                        out.append((re.compile(r"\b" + re.escape(word.strip()) + r"\b", re.I), said.strip()))
        except OSError:
            out = []
        _cache[:] = [stamp, tuple(out)]
    return _cache[1]


def _time(m):
    hour, mins, ampm = m.group(1), m.group(2), (m.group(3) or "").upper().replace(".", "")
    spoken = hour if mins == "00" else f"{hour} oh {mins[1]}" if mins[0] == "0" else f"{hour} {mins}"
    return (spoken + (" " + ampm if ampm else "")).strip()


def speakable(text):
    """The text as it should be said. Ordinary sentences come back unchanged."""
    s = text
    s = re.sub(r"\b(\d{1,2}):([0-5]\d)(?!\d)\s*([AaPp]\.[Mm]\.|[AaPp][Mm]\b)?", _time, s)       # 3:05 PM -> "3 oh 5 PM"; 3:00 PM -> "3 PM"
    s = re.sub(r"(?<=\d)\s?%", " percent", s)
    for sym, said in UNITS:
        s = re.sub(r"(?<=\d)\s?" + re.escape(sym) + (r"\b" if sym[-1].isalpha() else ""), said if said[0] == " " else " " + said, s)
    s = re.sub(r"\b([A-Za-z][\w-]*)\.exe\b", lambda m: m.group(1)[:1].upper() + m.group(1)[1:], s)   # chrome.exe -> Chrome
    s = re.sub(r"\s*(?:\.{3}|…|—|–|;)\s*", ", ", s)                                    # K5: shorter, fewer pauses
    for pat, said in rules():
        s = pat.sub(said, s)
    return re.sub(r"\s+", " ", s).strip()
