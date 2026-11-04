"""Static test (refactor phase 1): every setting read in jarvis.py / jarvislib uses a key from jarvislib/config.py with the
same default, and every key in the table is read somewhere. Reads source with ast; runs no JARVIS code."""
import ast
import importlib.util
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
JARVIS = os.path.dirname(HERE)
spec = importlib.util.spec_from_file_location("jarvis_config", os.path.join(JARVIS, "jarvislib", "config.py"))
config = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config)
D = config.DEFAULTS


def sources():
    yield "jarvis.py"
    base = os.path.join(JARVIS, "jarvislib")
    for root, dirs, files in os.walk(base):                    # jarvislib/ and its sub-packages (voice/, reply/)
        dirs[:] = sorted(d for d in dirs if d != "__pycache__")
        for f in sorted(files):
            if f.endswith(".py"):
                yield os.path.relpath(os.path.join(root, f), JARVIS).replace(os.sep, "/")


def name_of(call):
    f = call.func
    return f.attr if isinstance(f, ast.Attribute) else f.id if isinstance(f, ast.Name) else ""


def const(node, consts):
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub) and isinstance(node.operand, ast.Constant):
        return -node.operand.value
    if isinstance(node, ast.Name) and node.id in consts:
        return consts[node.id]
    raise LookupError(ast.dump(node)[:80])


def main():
    problems, seen = [], set()
    for rel in sources():
        tree = ast.parse(open(os.path.join(JARVIS, rel), encoding="utf-8").read())
        consts = {t.id: n.value.value for n in tree.body if isinstance(n, ast.Assign) and isinstance(n.value, ast.Constant)
                  for t in n.targets if isinstance(t, ast.Name)}
        reads = []                                             # (key, default or None = no default to compare, line)
        for n in tree.body:                                    # player.PAUSES = {kind: (key, default)}
            if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "PAUSES" for t in n.targets):
                for v in n.value.values:
                    reads.append((v.elts[0].value, v.elts[1].value, n.lineno))
        for c in ast.walk(tree):
            if not isinstance(c, ast.Call) or not c.args or not isinstance(c.args[0], ast.Constant) \
                    or not isinstance(c.args[0].value, str):
                continue
            key, fn = c.args[0].value, name_of(c)
            try:
                if fn == "setting":
                    reads.append((key, const(c.args[1], consts), c.lineno))
                elif fn == "on":                               # mood.on(name, default="1")
                    reads.append((key, const(c.args[1], consts) if len(c.args) > 1 else "1", c.lineno))
                elif fn == "_num":                             # player._num(name, default, lo, hi)
                    reads.append((key, const(c.args[1], consts), c.lineno))
                elif fn == "get" and isinstance(c.func, ast.Attribute) and isinstance(c.func.value, ast.Call) \
                        and name_of(c.func.value) == "settings" and not key.startswith("HW_"):
                    reads.append((key, None, c.lineno))
            except (LookupError, IndexError) as e:
                problems.append(f"{rel}:{c.lineno} {key}: default not a constant ({e})")
        for key, dflt, line in reads:
            seen.add(key)
            if key not in D:
                problems.append(f"{rel}:{line} reads {key!r}, which is not in jarvislib/config.py DEFAULTS")
            elif dflt is not None and dflt != D[key] and (key, dflt) not in config.RAW_READS:
                problems.append(f"{rel}:{line} {key} default {dflt!r} != table {D[key]!r}")
    for key in sorted(set(D) - seen):
        problems.append(f"config.py: {key} is in the table but never read")
    for p in problems:
        print("FAIL", p)
    print(f"settings schema: {len(D)} keys, {len(seen)} read, problems: {len(problems)}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
