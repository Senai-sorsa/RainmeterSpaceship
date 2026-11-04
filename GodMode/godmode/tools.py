"""The tools the model may call (read side + the gated apply_patch). Every path goes through PathPolicy.
Results are labelled as untrusted data so file text can't pose as instructions."""
import hashlib
import json
import os
from pathlib import Path

from . import memory, paths
from .gate import Violation

MAX_OUT = 20000
MAX_LIST = 500
GREP_MAX_FILES = 3000
GREP_MAX_BYTES = 200 * 1024 * 1024

SCHEMAS = {
    "fs_list": ("List a folder (names, type, size).", {"path": "absolute folder path"}),
    "fs_stat": ("Size, dates and type of one file or folder.", {"path": "absolute path"}),
    "fs_read": ("Read a text file, with line numbers. Use start_line to page.",
                {"path": "absolute file path", "start_line": "first line, default 1"}),
    "fs_grep": ("Find a literal text in files under a folder (case-insensitive). Returns path:line matches.",
                {"path": "absolute folder or file", "text": "literal text to find"}),
    "sys_memory": ("Current RAM/VRAM and the comfortable budget.", {}),
    "apply_patch": ("Propose a small tweak to an allowed file. It is checked, tested in a copy and shown to the "
                    "user; nothing is changed until they apply it. edits: list of {path, search, replace} where "
                    "path is relative to the repo and search is exact text that appears once.",
                    {"reason": "one line: why", "edits": "list of {path, search, replace}"}),
}
REQUIRED = {"fs_list": ["path"], "fs_stat": ["path"], "fs_read": ["path"], "fs_grep": ["path", "text"],
            "sys_memory": [], "apply_patch": ["reason", "edits"]}


def schemas(names):
    out = []
    for n in sorted(names):
        desc, props = SCHEMAS[n]
        p = {}
        for k, d in props.items():
            t = "integer" if k == "start_line" else "array" if k == "edits" else "string"
            p[k] = {"type": t, "description": d}
            if t == "array":
                p[k]["items"] = {"type": "object", "properties": {x: {"type": "string"} for x in
                                                                  ("path", "search", "replace")},
                                 "required": ["path", "search", "replace"]}
        out.append({"type": "function", "function": {"name": n, "description": desc, "parameters": {
            "type": "object", "properties": p, "required": REQUIRED[n]}}})
    return out


def _data(label, body):
    body = body if len(body) <= MAX_OUT else body[:MAX_OUT] + f"\n[... cut at {MAX_OUT} chars]"
    return f"<<untrusted data: {label}>>\n{body}\n<<end of data>>"


class ToolBox:
    def __init__(self, policy=None, snapshot=memory.snapshot, proposer=None):
        self.policy = policy or paths.PathPolicy()
        self.snapshot = snapshot
        self.proposer = proposer   # callable(patch) -> str, run by the broker; None = unavailable

    def call(self, name, args):
        fn = getattr(self, "t_" + name, None)
        if fn is None:
            raise Violation("tool-not-allowed", name)
        missing = [k for k in REQUIRED[name] if k not in args]
        if missing:
            return f"error: missing argument(s) {missing}"
        if "_malformed" in args:
            return "error: the arguments were not valid JSON"
        return fn(**{k: args[k] for k in args if k in SCHEMAS[name][1]})

    def _allow(self, path):
        v = self.policy.check_read(path)   # PathRejected propagates -> violation
        return paths.canonical(path), v

    def t_fs_list(self, path):
        p, v = self._allow(path)
        if not v.ok:
            return f"not shown: {v.reason}"
        try:
            entries = sorted(os.scandir(p), key=lambda e: e.name.lower())
        except OSError as e:
            return f"error: {e.strerror}"
        lines = []
        for e in entries[:MAX_LIST]:
            full = os.path.join(p, e.name)
            if paths.is_secret(full):
                continue
            try:
                kind = "dir" if e.is_dir(follow_symlinks=False) else "file"
                size = "" if kind == "dir" else f" {e.stat(follow_symlinks=False).st_size}"
            except OSError:
                kind, size = "?", ""
            lines.append(f"{kind} {e.name}{size}")
        more = f"\n... {len(entries) - MAX_LIST} more" if len(entries) > MAX_LIST else ""
        return _data(p, "\n".join(lines) + more)

    def t_fs_stat(self, path):
        p, v = self._allow(path)
        if not v.ok:
            return f"not shown: {v.reason}"
        st = os.stat(p, follow_symlinks=False)
        return json.dumps({"path": p, "size": st.st_size, "modified": int(st.st_mtime), "created": int(st.st_ctime),
                           "dir": os.path.isdir(p)})

    def t_fs_read(self, path, start_line=1):
        p, v = self._allow(path)
        if not v.ok:
            return f"not shown: {v.reason}"
        try:
            start = max(1, int(start_line))
        except (TypeError, ValueError):
            start = 1
        if os.path.isdir(p):
            return "that is a folder; use fs_list"
        size = os.path.getsize(p)
        if size > paths.MAX_READ:
            return f"file is {size} bytes (over the {paths.MAX_READ} cap); use fs_grep instead"
        raw = Path(p).read_bytes()
        if b"\x00" in raw[:8192]:
            return json.dumps({"binary": True, "size": size, "sha256": hashlib.sha256(raw).hexdigest()})
        lines = raw.decode("utf-8", "replace").splitlines()
        chunk = lines[start - 1:start - 1 + 400]
        body = "\n".join(f"{i}: {ln}" for i, ln in enumerate(chunk, start))
        tail = f"\n[lines {start}-{start + len(chunk) - 1} of {len(lines)}]"
        return _data(p, body + tail)

    def t_fs_grep(self, path, text):
        if not isinstance(text, str) or not text or len(text) > 200:
            return "error: text must be 1-200 characters"
        p, v = self._allow(path)
        if not v.ok:
            return f"not searched: {v.reason}"
        needle, hits, files, bytes_ = text.lower(), [], 0, 0
        walk = [(os.path.dirname(p), [], [os.path.basename(p)])] if os.path.isfile(p) else os.walk(p)
        for root, dirs, names in walk:
            dirs[:] = [d for d in dirs if not paths.is_secret(os.path.join(root, d) + "\\x")
                       and not os.path.islink(os.path.join(root, d))]
            for n in names:
                full = os.path.join(root, n)
                if paths.is_secret(full) or os.path.islink(full):
                    continue
                if not self.policy.check_read(full).ok:
                    continue
                files += 1
                try:
                    sz = os.path.getsize(full)
                    if sz > paths.MAX_READ:
                        continue
                    bytes_ += sz
                    data = Path(full).read_bytes()
                except OSError:
                    continue
                if b"\x00" in data[:4096]:
                    continue
                for i, ln in enumerate(data.decode("utf-8", "replace").splitlines(), 1):
                    if needle in ln.lower():
                        hits.append(f"{full}:{i}: {ln.strip()[:200]}")
                        if len(hits) >= 100:
                            return _data("grep " + p, "\n".join(hits) + "\n[stopped at 100 matches]")
                if files >= GREP_MAX_FILES or bytes_ >= GREP_MAX_BYTES:
                    return _data("grep " + p, "\n".join(hits) + "\n[stopped: search size cap]")
        return _data("grep " + p, "\n".join(hits) or "no matches")

    def t_sys_memory(self):
        s = self.snapshot()
        pol = memory.Policy()
        vb = memory.vram_budget(s, pol)
        G = memory.GiB
        return json.dumps({"ram_total_gib": round(s.total_ram / G, 1), "ram_free_gib": round(s.avail_ram / G, 1),
                           "comfortable_ram_gib": round(memory.ram_budget(s, pol) / G, 1),
                           "vram_free_gib": None if s.vram_total is None else round((s.vram_total - s.vram_used) / G, 1),
                           "comfortable_vram_gib": None if vb is None else round(vb / G, 1)})

    def t_apply_patch(self, reason, edits):
        if self.proposer is None:
            return "apply_patch is not available in this session"
        return self.proposer({"reason": reason, "edits": edits})
