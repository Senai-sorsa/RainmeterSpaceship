"""Self-tweak gate (plan section 4). Code decides; the model only proposes.

A patch = {"reason": str, "edits": [{"path": rel, "search": exact text, "replace": new text}, ...]}.
Checks, in order: surfaces (protected path = Violation), size caps, exact unique matches,
banned-content scan, Python structure lock (same defs, signatures, imports, table keys)."""
import ast
import difflib
import fnmatch
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from .gate import Violation

HERE = Path(__file__).resolve().parent

# Calls / attribute roots that a tweak may not ADD (counted on the AST, so words inside strings are fine).
BANNED_NAMES = {"subprocess", "ctypes", "winreg", "socket", "urllib", "requests", "http", "shutil", "pickle",
                "marshal", "importlib", "__import__", "eval", "exec", "compile", "globals", "locals", "vars",
                "getattr", "setattr", "delattr", "open", "os", "sys", "builtins", "threading", "multiprocessing",
                "asyncio", "signal", "tempfile", "pathlib", "Path", "io", "zipfile", "tarfile", "webbrowser",
                "input", "breakpoint", "exit", "quit"}
BANNED_TEXT = re.compile(r"god\s*mode|godmode|tripwire|audit|surfaces\.json|testgate|sandbox", re.I)


@dataclass
class Surfaces:
    editable: list
    protected: list
    limits: dict

    @classmethod
    def load(cls, path=None):
        d = json.loads(Path(path or HERE / "surfaces.json").read_text(encoding="utf-8"))
        return cls(d["editable"], d["protected"], d["limits"])


@dataclass
class Result:
    ok: bool
    problems: list = field(default_factory=list)
    files: dict = field(default_factory=dict)      # rel path -> new full text
    diff: str = ""
    changed_lines: int = 0


def clean_rel(path):
    """Relative, forward-slash path or Violation. No '..', drives, ADS, backslash tricks, absolute paths."""
    if not isinstance(path, str) or not path or len(path) > 400 or "\x00" in path:
        raise Violation("bad-path", repr(path))
    p = path.replace("\\", "/")
    if p.startswith("/") or ":" in p or re.match(r"^[A-Za-z]:", p):
        raise Violation("bad-path", f"{path!r} must be relative to the repo")
    parts = p.split("/")
    if any(s in ("", ".", "..") or s != s.rstrip(" .") for s in parts):
        raise Violation("bad-path", f"{path!r} has empty, '.', '..' or trailing-dot parts")
    return p


def _match(rel, pattern):
    r, pat = rel.lower(), pattern.lower()
    if fnmatch.fnmatchcase(r, pat):
        return True
    if pat.startswith("**/") and fnmatch.fnmatchcase(r, pat[3:]):
        return True
    if pat.endswith("/**") and (r == pat[:-3] or r.startswith(pat[:-3] + "/")):
        return True
    return False


def is_protected(rel, surfaces):
    return any(_match(rel, p) for p in surfaces.protected)


def is_editable(rel, surfaces):
    return any(_match(rel, p) for p in surfaces.editable) and not is_protected(rel, surfaces)


# ---------------- structure lock ----------------

def _sig(fn):
    decos = [ast.unparse(d) for d in fn.decorator_list]
    return f"{'async ' if isinstance(fn, ast.AsyncFunctionDef) else ''}def {fn.name}({ast.unparse(fn.args)})" \
           f"{' -> ' + ast.unparse(fn.returns) if fn.returns else ''} @{decos}"


def structure(src):
    """What a tweak must not change: defs + signatures, classes + bases + methods, all imports,
    top-level names, and the keys of top-level dict/set/list tables."""
    tree = ast.parse(src)
    out = {"defs": [], "imports": [], "names": [], "tables": {}}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            out["defs"].append(_sig(node))
        elif isinstance(node, ast.ClassDef):
            meths = [_sig(n) for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
            out["defs"].append(f"class {node.name}({', '.join(ast.unparse(b) for b in node.bases)}) {meths}")
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for t in targets:
                for n in ast.walk(t):
                    if isinstance(n, ast.Name):
                        out["names"].append(n.id)
                        if isinstance(node.value, ast.Dict):
                            out["tables"][n.id] = sorted(ast.unparse(k) for k in node.value.keys if k is not None)
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            out["imports"].append(ast.unparse(node))
    out["defs"].sort()
    out["imports"].sort()
    out["names"] = sorted(set(out["names"]))
    return out


def banned_counts(src):
    counts = {}
    for node in ast.walk(ast.parse(src)):
        name = None
        if isinstance(node, ast.Name):
            name = node.id
        elif isinstance(node, ast.Attribute):
            root = node
            while isinstance(root, ast.Attribute):
                root = root.value
            if isinstance(root, ast.Name):
                name = root.id
        if name in BANNED_NAMES:
            counts[name] = counts.get(name, 0) + 1
    return counts


def _python_problems(rel, old, new):
    try:
        so, sn = structure(old), structure(new)
    except SyntaxError as e:
        return [f"{rel}: the change does not parse ({e.msg}, line {e.lineno})"]
    probs = []
    for key, label in (("defs", "functions/classes or their signatures"), ("imports", "imports"),
                       ("names", "top-level names"), ("tables", "table keys")):
        if so[key] != sn[key]:
            probs.append(f"{rel}: changes {label}; only bodies and values may change (main structure is locked)")
    bo, bn = banned_counts(old), banned_counts(new)
    added = sorted(k for k, v in bn.items() if v > bo.get(k, 0))
    if added:
        probs.append(f"{rel}: adds uses of {', '.join(added)} (not allowed in a tweak)")
    return probs


# ---------------- the gate ----------------

def check(patch, read_text, surfaces=None):
    """read_text(rel) -> current file text (from the disposable copy). Raises Violation for protected or
    malformed paths. Returns Result with problems (fixable by the model) or the new file texts."""
    s = surfaces or Surfaces.load()
    lim = s.limits
    if not isinstance(patch, dict) or not isinstance(patch.get("edits"), list) or not patch["edits"]:
        return Result(False, ["patch needs a non-empty 'edits' list"])
    reason = patch.get("reason")
    if not isinstance(reason, str) or not reason.strip() or len(reason) > 300:
        return Result(False, ["patch needs a short 'reason' (one line)"])
    by_file, total_chars = {}, 0
    for e in patch["edits"]:
        if not isinstance(e, dict) or not all(isinstance(e.get(k), str) for k in ("path", "search", "replace")):
            return Result(False, ["each edit needs string 'path', 'search' and 'replace'"])
        rel = clean_rel(e["path"])
        if is_protected(rel, s):
            raise Violation("protected-path", f"tried to edit {rel}")
        if not is_editable(rel, s):
            return Result(False, [f"{rel} is not on the editable list"])
        if not e["search"]:
            return Result(False, [f"{rel}: 'search' must not be empty"])
        total_chars += len(e["search"]) + len(e["replace"])
        by_file.setdefault(rel, []).append(e)
    if len(by_file) > lim["max_files"]:
        return Result(False, [f"too many files ({len(by_file)} > {lim['max_files']})"])
    if total_chars > lim["max_chars"]:
        return Result(False, [f"patch too large ({total_chars} > {lim['max_chars']} chars)"])
    res = Result(True)
    diffs = []
    for rel, edits in by_file.items():
        old = read_text(rel)
        new = old
        for e in edits:
            n = new.count(e["search"])
            if n != 1:
                res.problems.append(f"{rel}: 'search' text found {n} times (must be exactly once)")
                continue
            new = new.replace(e["search"], e["replace"], 1)
            if BANNED_TEXT.search(e["replace"]) and not BANNED_TEXT.search(e["search"]):
                res.problems.append(f"{rel}: the new text mentions GOD mode internals")
        if new == old:
            res.problems.append(f"{rel}: no change")
            continue
        if rel.endswith(".py"):
            res.problems += _python_problems(rel, old, new)
        d = list(difflib.unified_diff(old.splitlines(), new.splitlines(), f"a/{rel}", f"b/{rel}", lineterm=""))
        res.changed_lines += sum(1 for ln in d if ln[:1] in "+-" and not ln.startswith(("+++", "---")))
        diffs.append("\n".join(d))
        res.files[rel] = new
    if res.changed_lines > lim["max_changed_lines"]:
        res.problems.append(f"too many changed lines ({res.changed_lines} > {lim['max_changed_lines']})")
    res.diff = "\n".join(diffs) + ("\n" if diffs else "")
    res.ok = not res.problems
    return res
