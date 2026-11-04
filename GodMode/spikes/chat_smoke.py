"""Smoke test of the full `godmode chat` stack with the installed llama3.2:3b standing in for the GOD models:
private Ollama (low IL, capped) + RunGuard + low-IL reader + gate + audit + Session, read mode.
Asks it to read one scratch file. A small model may answer imperfectly; the check is that the stack works:
a tool call goes through the reader, the answer comes back, the audit chain verifies.
Run: py -3 -I GodMode/spikes/chat_smoke.py"""
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from godmode import audit, memory  # noqa: E402
from godmode import sandbox_win as sb  # noqa: E402
from godmode.agent import Session  # noqa: E402
from godmode.gate import ModeGate  # noqa: E402
from godmode.guard import RunGuard  # noqa: E402
from godmode.reader import RemoteTools  # noqa: E402
from godmode.servers import PrivateOllama  # noqa: E402
from godmode.tools import ToolBox  # noqa: E402


def main():
    d = Path(tempfile.mkdtemp(prefix="godchat-"))
    f = d / "mission.txt"
    f.write_text("The launch code word is BLUEBIRD.\n", encoding="utf-8")
    log = audit.AuditLog(d / "audit.jsonl")
    checks = []
    with PrivateOllama(working_set_cap=4 << 30) as srv:
        guard = RunGuard(srv.proc, memory.Watchdog(), memory.snapshot).start()
        tools = RemoteTools.start(ToolBox(proposer=None))
        try:
            s = Session(client=srv.client("llama3.2:3b", options={"num_ctx": 4096, "temperature": 0}),
                        gate=ModeGate("read", "advanced"), toolbox=tools, audit=log, jobs_dir=d / "jobs")
            r = s.ask(f"Use the fs_read tool to read {f} and tell me the code word.")
            used = [m for m in s.messages if m["role"] == "tool"]
            print("status:", r["status"], "| tool results:", len(used), "| answer:", r["content"][:200])
            checks.append(("session finished", r["status"] == "done"))
            checks.append(("a tool call went through the low-IL reader", any("BLUEBIRD" in m["content"] for m in used)))
            checks.append(("audit chain verifies", log.verify()[0]))
            checks.append(("guard did not have to act (enough RAM)", guard.state == "running"))
        finally:
            tools.close()
            guard.close()
    shutil.rmtree(d, ignore_errors=True)
    for name, ok in checks:
        print(("PASS " if ok else "FAIL ") + name)
    return 0 if all(ok for _, ok in checks) else 1


if __name__ == "__main__":
    sys.exit(main())
