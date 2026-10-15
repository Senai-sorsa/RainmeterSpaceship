"""notes: moved verbatim from jarvis.py (refactor). See JARVIS-Repair-Plan.txt, REFACTOR."""
import os
import re
import time
from .base import setting


def vault_dir():
    v = setting("JarvisVault", "").strip().strip('"')
    if v and os.path.isdir(v):
        return v
    todo = setting("ObsidianTodo", "").strip().strip('"')
    d = os.path.dirname(todo) if todo and os.path.exists(todo) else ""
    for _ in range(4):                                         # the to-do note's folder, or up to three folders above it
        if d and os.path.isdir(os.path.join(d, ".obsidian")):  # only a real vault: a to-do note in Downloads is not one
            return d
        d = os.path.dirname(d)
    return ""


def search_notes(query, limit=3):
    """Plain keyword search through the .md notes in your vault (no index or database needed). Best matches first."""
    root = vault_dir()
    words = [w for w in re.findall(r"[a-z0-9]{3,}", query.lower()) if w not in STOP]
    if not root or not words:
        return root, []
    hits, t0 = [], time.time()
    for dirpath, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if not d.startswith(".")]          # skip .obsidian, .trash
        for fn in files:
            if not fn.lower().endswith(".md"):
                continue
            path = os.path.join(dirpath, fn)
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    text = f.read(200_000)
            except OSError:
                continue
            low = text.lower()
            score = sum(low.count(w) for w in words) + 3 * sum(w in fn.lower() for w in words)
            if score:
                i = min((low.find(w) for w in words if w in low), default=0)
                snippet = re.sub(r"\s+", " ", text[max(0, i - 150):i + 350]).strip()
                hits.append((score, os.path.splitext(fn)[0], snippet))
        if time.time() - t0 > 4:                                      # huge vaults: stop after 4 s
            break
    hits.sort(key=lambda h: -h[0])
    return root, hits[:limit]


STOP = set("the and for with that this what when where which about from have your you are was were can could would "
           "should notes note vault search find look show tell my me any anything something".split())
