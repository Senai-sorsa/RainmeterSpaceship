"""The fixed-line registry (refactor phase 2): the pass-through set is exactly the three lines polish() always left alone,
no text is registered under two keys, and the registry imports nothing from jarvislib (no sys.argv / RES read)."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.argv[1:] = []

from jarvislib.reply import fixed as F  # noqa: E402

assert not [m for m in sys.modules if m.startswith("jarvislib.") and m not in ("jarvislib.reply", "jarvislib.reply.fixed")], \
    "reply/fixed.py must not import other jarvislib modules"
assert F.FIXED_LINES == {F.CLAIM_LINE, F.CANT_LINE, F.NO_READING}, F.FIXED_LINES
texts = list(F.LINES.values())
assert len(texts) == len(set(texts)), "one text under two keys"
try:
    F.register("claim", "something else")
    raise AssertionError("re-registering a key with other text must fail")
except ValueError:
    pass
assert F.register("claim", F.CLAIM_LINE) == F.CLAIM_LINE           # same text again is fine (idempotent)
import ast  # noqa: E402

src = open(os.path.join(os.path.dirname(HERE), "jarvis.py"), encoding="utf-8").read()
raw = []
for node in ast.walk(ast.parse(src)):                          # fixed("...") / reply_line("...") with a raw literal: use FX.X
    if isinstance(node, ast.Call) and getattr(node.func, "id", "") in ("fixed", "reply_line"):
        todo = list(node.args[:1])                             # the line itself, or a branch of "a if c else b"
        while todo:                                            # (f-string templates and joins are built text: allowed)
            sub = todo.pop()
            if isinstance(sub, ast.IfExp):
                todo += [sub.body, sub.orelse]
            elif isinstance(sub, ast.Constant) and isinstance(sub.value, str) and sub.value.strip():
                raw.append((node.lineno, sub.value))
assert not raw, f"jarvis.py passes raw lines (register them in reply/fixed.py): {raw}"
print(f"fixed lines: {len(F.LINES)} registered, {len(F.FIXED_LINES)} pass-through: OK")
