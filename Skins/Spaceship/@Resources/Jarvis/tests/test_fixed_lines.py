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
print(f"fixed lines: {len(F.LINES)} registered, {len(F.FIXED_LINES)} pass-through: OK")
