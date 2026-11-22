"""The routing rules and their order (refactor phase 4). The order of RULES IS the behaviour: an earlier area wins over a later one.
This test prints it, pins it (change it on purpose, together with tests/golden/routes.jsonl), and checks that the area
functions sit in routing.py in that same order and all take the same five values. Static: nothing of JARVIS runs."""
import ast
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(os.path.dirname(HERE), "jarvislib", "routing.py")

EXPECTED = ["undo", "other_device", "mood", "followups", "memory", "lookup", "system", "bluetooth", "settings", "display",
            "mic_level", "sound", "media", "apps", "misc"]

src = open(SRC, encoding="utf-8").read()
tree = ast.parse(src)
table = next(n for n in tree.body if isinstance(n, ast.Assign) and any(getattr(t, "id", "") == "RULES" for t in n.targets))
pairs = [(e.elts[0].value, e.elts[1].id) for e in table.value.elts]
names = [p[0] for p in pairs]
print("rule order:", " > ".join(names))
assert names == EXPECTED, names
assert all(fn == f"_rules_{n}" for n, fn in pairs), pairs
defs = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}
lines = [defs[fn].lineno for _, fn in pairs]
assert lines == sorted(lines) and len(set(lines)) == len(lines), f"area functions are not in RULES order: {lines}"
for _, fn in pairs:
    assert [a.arg for a in defs[fn].args.args] == ["text", "named", "t", "whole", "cmd"], fn
    assert ast.get_docstring(defs[fn]), f"{fn} needs a docstring saying what it covers"
rest = defs["_route_rest"]
assert rest.end_lineno - rest.lineno < 15, "_route_rest is the driver only: rules belong in an area function"
assert not re.search(r"\bRULES\b.*\+", src.split("RULES = (")[1].split("\n")[0]), "RULES must be one literal tuple"
print(f"routing rules: {len(names)} areas in order, driver {rest.end_lineno - rest.lineno + 1} lines: OK")
