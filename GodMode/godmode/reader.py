"""Sandboxed file reader (handoff gap: "worker and broker in one process").

The read tools run in a persistent LOW-INTEGRITY child; the broker (the CLI / later CSpace) keeps the gate,
audit, apply_patch and model calls. So a bug in the read path cannot write anything (OS-enforced), and with
`godmode protect-secrets --apply` the OS also refuses it secret folders. Protocol: one JSON object per line.
  broker -> reader: {"id": n, "tool": name, "args": {...}}
  reader -> broker: {"id": n, "out": text} | {"id": n, "violation": [kind, detail]} | {"id": n, "error": text}"""
import json
import sys
from pathlib import Path

from . import paths
from .gate import Violation

READER_TOOLS = frozenset({"fs_list", "fs_stat", "fs_read", "fs_grep"})
PKG_ROOT = Path(__file__).resolve().parents[1]
MAX_LINE = 8 << 20


def serve(inp, out, toolbox=None):
    """Reader main loop over binary streams. Never raises on bad input."""
    if toolbox is None:
        from .tools import ToolBox
        toolbox = ToolBox(proposer=None, snapshot=None)
    for raw in iter(lambda: inp.readline(MAX_LINE), b""):
        rid = None
        try:
            req = json.loads(raw)
            rid = req.get("id")
            tool, args = req.get("tool"), req.get("args")
            if tool not in READER_TOOLS or not isinstance(args, dict):
                raise Violation("tool-not-allowed", f"reader does not run {tool!r}")
            resp = {"id": rid, "out": str(toolbox.call(tool, args))}
        except Violation as v:
            resp = {"id": rid, "violation": [v.kind, v.detail]}
        except paths.PathRejected as e:
            resp = {"id": rid, "violation": ["bad-path", str(e)]}
        except (ValueError, OSError, TypeError) as e:
            resp = {"id": rid, "error": f"{type(e).__name__}: {e}"[:500]}
        out.write((json.dumps(resp, ensure_ascii=False) + "\n").encode("utf-8"))
        out.flush()


def main():
    serve(sys.stdin.buffer, sys.stdout.buffer)


BOOT = f"import sys; sys.path.insert(0, {str(PKG_ROOT)!r}); from godmode.reader import main; main()"


class RemoteTools:
    """Broker-side ToolBox: read tools go to the low-IL reader; sys_memory and apply_patch stay in the broker."""

    def __init__(self, proc, local):
        self.proc, self.local, self._n = proc, local, 0

    @classmethod
    def start(cls, local, spawn=None):
        from . import sandbox_win as sb
        spawn = spawn or sb.spawn
        cwd = sb.low_il_dir() / "reader"
        cwd.mkdir(parents=True, exist_ok=True)
        proc = spawn([sys.executable, "-I", "-B", "-c", BOOT], cwd=str(cwd),
                     env={"TEMP": str(cwd), "TMP": str(cwd)},
                     limits=sb.Limits(max_processes=2, private_commit=1 << 30, cpu_pct=50,
                                      working_set_cap=512 << 20), sandbox="lowil", pipes=True)
        return cls(proc, local)

    def call(self, name, args):
        if name not in READER_TOOLS:
            return self.local.call(name, args)
        if "path" in args:
            paths.canonical(args["path"])   # trip early in the broker too (PathRejected -> violation)
        self._n += 1
        self.proc.stdin.write((json.dumps({"id": self._n, "tool": name, "args": args}) + "\n").encode("utf-8"))
        self.proc.stdin.flush()
        line = self.proc.stdout.readline(MAX_LINE)
        if not line:
            return "error: the reader process stopped"
        resp = json.loads(line)
        if resp.get("id") != self._n:
            return "error: reader out of sync"
        if "violation" in resp:
            raise Violation(*resp["violation"])
        return resp.get("out", "error: " + str(resp.get("error")))

    def close(self):
        self.proc.kill()
        self.proc.close()
