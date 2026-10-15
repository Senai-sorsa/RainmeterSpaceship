"""todo: moved verbatim from jarvis.py (refactor). See JARVIS-Repair-Plan.txt, REFACTOR."""
from .base import todo_note
from .turnstate import last


# ------------------------------------------------------------------ to-do by voice and remembered facts
def act_todo(item):
    """Add one open task to the to-do note. Appended, never rewritten (safe while Obsidian or a sync tool has the note
    open), and the note is never created. Errors carry no path: they are logged and shown."""
    item, note = " ".join(str(item).split())[:200], todo_note()
    if not item or not note:
        raise RuntimeError("no to-do note is set")
    try:
        with open(note, "rb+") as f:                           # rb+ fails on a missing file instead of making one
            if f.seek(0, 2):
                f.seek(-1, 2)
                last = f.read(1)
                f.seek(0, 2)
                if last != b"\n":
                    f.write(b"\n")
            f.write(f"- [ ] {item}\n".encode("utf-8"))
    except OSError as e:
        raise RuntimeError(f"the to-do note could not be written ({type(e).__name__})") from None
