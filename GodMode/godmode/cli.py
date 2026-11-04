"""godmode command line (run from the repo:  py -3 -I -m godmode <command>  inside GodMode/).

  doctor              read-only health check: RAM/VRAM budgets, placements, Ollama, models, folders
  plan [slot]         comfortable-RAM placement for a slot (default: all)
  gguf PATH | --ollama TAG   header summary: expert bytes, layers, KV/token, chat-template red flags
  audit-verify        check the audit hash chain
  tweak-check FILE    static gate only (surfaces, size, structure, banned content) against the repo
  tweak-run FILE      full gate: copy, baseline tests, patch, tests again (sandboxed) -> proposal bundle
  proposal-show ID    print a proposal's diff, results and the commands to apply it by hand
  chat --slot S --mode M   console session (needs the model installed; read/chat/tweak; ultron = chat only)
  incident-ack        unlock after reading an incident
  sandbox-setup [--venv] [--undo]   AppContainer for tweak tests (--venv grants read on the JARVIS venv: needs OK)
  protect-secrets [--apply|--undo]  dry run by default: label secret folders so sandboxed processes can't read them"""
import argparse
import datetime as dt
import json
import os
import shutil
import sys
import uuid
from pathlib import Path

from . import audit, gate, gguf, hardening, memory, paths, profiles, testgate, tweak
from . import sandbox_win as sb

REPO = Path(__file__).resolve().parents[2]
G = memory.GiB


def venv_python():
    return Path(os.environ.get("LOCALAPPDATA", "")) / "SpaceshipHUD" / "venv" / "Scripts" / "python.exe"


def audit_log():
    return audit.AuditLog(sb.broker_dir() / "audit.jsonl")


def lock_file():
    return sb.broker_dir() / "incident.lock"


def _gib(b):
    return "?" if b is None else f"{b / G:.1f} GiB"


def cmd_doctor(_):
    ok = True
    print(f"GOD mode doctor  (repo {REPO})")
    try:
        s = memory.snapshot()
    except OSError as e:
        print("  memory probe FAILED:", e)
        return 1
    pol = memory.Policy()
    print(f"  RAM  total {_gib(s.total_ram)}, free {_gib(s.avail_ram)}, reserve {_gib(memory.reserve(s, pol))}, "
          f"comfortable {_gib(memory.ram_budget(s, pol))}")
    print(f"  commit {_gib(s.commit_used)} of {_gib(s.commit_limit)}")
    print(f"  VRAM total {_gib(s.vram_total)}, used {_gib(s.vram_used)}, comfortable {_gib(memory.vram_budget(s, pol))}")
    cores = memory.physical_cores()
    print(f"  physical cores {cores}")
    du = shutil.disk_usage("C:\\")
    print(f"  C: free {du.free / 1e9:.0f} GB")
    from .runtime import OllamaClient
    tags = []
    try:
        oc = OllamaClient("x")
        print(f"  Ollama {oc.version()} on 127.0.0.1:11434")
        tags = oc.tags()
    except OSError as e:
        ok = False
        print("  Ollama not reachable:", e)
    for slot, p in profiles.load().items():
        if p.reserved:
            print(f"  [{slot}] {p.display}: reserved slot (no model yet, tools={p.tools})")
            continue
        have = p.model in tags or (p.model + ":latest") in tags
        print(f"  [{slot}] {p.display}: {p.model} via {p.runtime}, installed={have}"
              f"{' (sizes are estimates until G0)' if p.estimate else ''}")
        if p.runtime == "ollama":
            mode, ctx, why = memory.ollama_check(p, s, pol)
            print(f"      Ollama pre-load: {mode.upper()} ctx={ctx}: {why}")
        else:
            pl = memory.plan(p, s, pol, cores)
            print(f"      placement: {pl.mode.upper()} ctx={pl.ctx} n-cpu-moe={pl.n_cpu_moe} threads={pl.threads} "
                  f"coverage={pl.coverage:.0%} ws-cap={_gib(pl.working_set_cap)}: {pl.reason}")
    vp = venv_python()
    print(f"  JARVIS venv python for tests: {'found' if vp.is_file() else 'MISSING'} ({vp})")
    print(f"  broker folder (medium IL): {sb.broker_dir()}")
    print(f"  sandbox folder (low IL):   {sb.low_il_dir()}")
    print(f"  llama-server: {'not downloaded yet (G0, needs approval)' if not shutil.which('llama-server') else shutil.which('llama-server')}")
    a_ok, a_why = audit_log().verify()
    print(f"  audit log: {'OK' if a_ok else 'BROKEN'} ({a_why})")
    print(f"  incident lock: {'LOCKED' if lock_file().exists() else 'none'}")
    return 0 if ok else 1


def cmd_plan(a):
    s, cores = memory.snapshot(), memory.physical_cores()
    for slot, p in profiles.load().items():
        if a.slot and slot != a.slot:
            continue
        pl = memory.plan(p, s, memory.Policy(), cores)
        print(json.dumps({"slot": slot, **pl.__dict__}, indent=1))
    return 0


def cmd_gguf(a):
    path = gguf.ollama_blob(a.ollama) if a.ollama else Path(a.path)
    print(json.dumps({"file": str(path), **gguf.summarize(gguf.read(path))}, indent=1))
    return 0


def cmd_audit_verify(_):
    ok, why = audit_log().verify()
    print(("OK " if ok else "BROKEN ") + why)
    return 0 if ok else 1


def _load_patch(f):
    return json.loads(Path(f).read_text(encoding="utf-8"))


def cmd_tweak_check(a):
    try:
        res = tweak.check(_load_patch(a.file), lambda rel: (REPO / rel).read_text(encoding="utf-8"))
    except gate.Violation as v:
        print("VIOLATION (would trip):", v)
        return 2
    print("OK" if res.ok else "REJECTED")
    for p in res.problems:
        print(" -", p)
    print(res.diff)
    return 0 if res.ok else 1


def proposals_dir():
    return sb.broker_dir() / "proposals"


def propose(patch, log=None):
    """Broker-side: full gate on a fresh copy. Returns a short text for the model. Raises Violation."""
    log = log or audit_log()
    lim = tweak.Surfaces.load().limits
    today = dt.date.today().strftime("%Y%m%d")
    pd = proposals_dir()
    if pd.exists() and sum(1 for d in pd.iterdir() if d.name.startswith(today)) >= lim["max_per_day"]:
        return "rejected: the daily tweak limit is reached"
    pid = f"{today}-{uuid.uuid4().hex[:8]}"
    work = sb.broker_dir() / "work" / pid
    ac = hardening.tests_in_appcontainer()          # (runtime python, site-packages) or None
    tmp = (hardening.ac_folders()["actmp"] if ac else sb.low_il_dir() / "tmp") / pid
    tmp.mkdir(parents=True, exist_ok=True)
    vp = venv_python()
    if not vp.is_file():
        return "rejected: JARVIS venv python not found, tests can't run"
    box = "appcontainer" if ac else "lowil"

    def runner(argv, cwd, env, timeout):
        return sb.run(argv, cwd=cwd, env=env, timeout=timeout, sandbox=box,
                      limits=sb.Limits(cpu_pct=60, private_commit=4 << 30))

    try:
        res, rep = testgate.run_gate(REPO, work, patch, runner, tmp, {"venv_python": str(vp)}, appcontainer=ac)
    except gate.Violation as v:
        log.write("tripwire", kind=v.kind, detail=v.detail, tool="apply_patch", proposal=pid)
        raise
    out = pd / pid
    out.mkdir(parents=True, exist_ok=True)
    (out / "patch.json").write_text(json.dumps(patch, indent=1, ensure_ascii=False), encoding="utf-8")
    (out / "change.diff").write_text(res.diff, encoding="utf-8")
    report = {"ok": rep.ok, "reasons": rep.reasons, "changed_lines": res.changed_lines, "sandbox": box,
              "baseline": [r.__dict__ for r in rep.baseline], "patched": [r.__dict__ for r in rep.patched]}
    (out / "report.json").write_text(json.dumps(report, indent=1, ensure_ascii=False), encoding="utf-8")
    rec = log.write("proposal", id=pid, ok=rep.ok, files=sorted(res.files), reasons=rep.reasons)
    shutil.rmtree(work, ignore_errors=True)   # only our own work copy
    shutil.rmtree(tmp, ignore_errors=True)
    if rep.ok:
        return f"proposal {pid} passed all checks and tests; the user will review it. (audit {rec['h'][:12]})"
    return f"proposal {pid} rejected: " + "; ".join(rep.reasons)


def cmd_tweak_run(a):
    try:
        print(propose(_load_patch(a.file)))
    except gate.Violation as v:
        print("VIOLATION:", v)
        return 2
    return 0


def cmd_proposal_show(a):
    d = proposals_dir() / a.id
    if not d.is_dir() or "/" in a.id or "\\" in a.id:
        print("no such proposal")
        return 1
    rep = json.loads((d / "report.json").read_text(encoding="utf-8"))
    print((d / "change.diff").read_text(encoding="utf-8"))
    print("checks:", "PASSED" if rep["ok"] else "REJECTED", rep["reasons"])
    if rep["ok"]:
        print("\nTo apply by hand (review the diff first):")
        print(f'  git switch -c god/tweak-{a.id}')
        print(f'  git apply --check "{d / "change.diff"}" && git apply "{d / "change.diff"}"')
        print("  then run the JARVIS tests yourself before merging.")
    return 0


def cmd_chat(a):
    """Console session. The model runs in GOD mode's own private Ollama (low IL, capped, frozen under memory
    pressure by RunGuard); read tools run in a low-IL reader process; gate/audit/apply_patch stay here."""
    from .agent import Session, Tripped
    from .guard import RunGuard
    from .incident import EXPLAINER_MODEL, explain
    from .reader import RemoteTools
    from .runtime import OllamaClient
    from .servers import PrivateOllama
    from .tools import ToolBox
    p = profiles.load().get(a.slot)
    if not p or p.reserved or not p.model:
        print("that slot has no model yet")
        return 1
    if p.runtime != "ollama":
        print("this slot uses llama-server split mode; it is set up in G0 (binary not downloaded yet)")
        return 1
    mode = "ultron" if a.slot == "ultron" else a.mode
    g = gate.ModeGate(mode, a.slot)
    s = memory.snapshot()
    fit, ctx, why = memory.ollama_check(p, s)
    if fit == "refuse":
        print("not loading:", why)
        return 1
    if p.model not in OllamaClient("x").tags():
        print(f"{p.model} is not installed (downloads wait for the user's approval)")
        return 1
    cap = max(memory.ram_budget(s, memory.Policy()), 2 * memory.GiB)
    srv = PrivateOllama(working_set_cap=cap)
    srv.start()
    guard = RunGuard(srv.proc, memory.Watchdog(), memory.snapshot,
                     on_change=lambda act, st: print(f"\n[memory guard: {act} -> {st}]")).start()
    local = ToolBox(proposer=propose if mode == "tweak" else None)
    tools = RemoteTools.start(local) if g.tools else local
    try:
        sess = Session(client=srv.client(p.model, options={"num_ctx": ctx}), gate=g, toolbox=tools,
                       audit=audit_log(), jobs_dir=sb.low_il_dir() / "jobs", lock_file=lock_file())
        print(f"{p.display} | mode {mode} | ctx {ctx} | RAM cap {cap / G:.1f} GiB | {why}. Empty line to quit.")
        while True:
            try:
                q = input("> ").strip()
            except EOFError:
                break
            if not q:
                break
            try:
                r = sess.ask(q)
            except Tripped as t:
                print("\nSTOPPED BY TRIPWIRE:", json.dumps(t.record, indent=1))
                print(explain(t.record, OllamaClient(EXPLAINER_MODEL)))
                return 3
            print(r["content"], f"\n[{r['status']}]")
    finally:
        guard.close()
        if tools is not local:
            tools.close()
        srv.stop()
    return 0


def cmd_sandbox_setup(a):
    if a.undo:
        hardening.sandbox_undo()
        print("AppContainer grants removed")
        return 0
    st = hardening.sandbox_setup(venv=a.venv)
    print(json.dumps(st, indent=1))
    print("tweak tests will run in the AppContainer (no network, no user files)" if hardening.tests_in_appcontainer()
          else "tweak tests still run at low integrity; run with --venv (after the user's OK) to switch")
    return 0


def cmd_protect_secrets(a):
    if a.undo:
        hardening.unprotect_secrets()
        print("labels removed")
        return 0
    t = hardening.protect_secrets(apply=a.apply)
    print(("labelled (sandboxed processes can no longer read these):" if a.apply else
           "dry run, would label (rerun with --apply):"), *[f"  {x}" for x in t] or ["  (none found)"], sep="\n")
    return 0


def cmd_incident_ack(_):
    lf = lock_file()
    if not lf.exists():
        print("no incident")
        return 0
    print(lf.read_text(encoding="utf-8"))
    if input("Type I HAVE READ THIS to unlock: ").strip() != "I HAVE READ THIS":
        return 1
    audit_log().write("incident-ack")
    lf.unlink()
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(prog="godmode", description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    sp.add_parser("doctor").set_defaults(fn=cmd_doctor)
    x = sp.add_parser("plan"); x.add_argument("slot", nargs="?"); x.set_defaults(fn=cmd_plan)
    x = sp.add_parser("gguf"); x.add_argument("path", nargs="?"); x.add_argument("--ollama"); x.set_defaults(fn=cmd_gguf)
    sp.add_parser("audit-verify").set_defaults(fn=cmd_audit_verify)
    x = sp.add_parser("tweak-check"); x.add_argument("file"); x.set_defaults(fn=cmd_tweak_check)
    x = sp.add_parser("tweak-run"); x.add_argument("file"); x.set_defaults(fn=cmd_tweak_run)
    x = sp.add_parser("proposal-show"); x.add_argument("id"); x.set_defaults(fn=cmd_proposal_show)
    x = sp.add_parser("chat"); x.add_argument("--slot", default="advanced", choices=["advanced", "ascendent", "ultron"])
    x.add_argument("--mode", default="read", choices=["chat", "read", "tweak"]); x.set_defaults(fn=cmd_chat)
    sp.add_parser("incident-ack").set_defaults(fn=cmd_incident_ack)
    x = sp.add_parser("sandbox-setup"); x.add_argument("--venv", action="store_true"); x.add_argument("--undo", action="store_true")
    x.set_defaults(fn=cmd_sandbox_setup)
    x = sp.add_parser("protect-secrets"); m = x.add_mutually_exclusive_group()
    m.add_argument("--apply", action="store_true"); m.add_argument("--undo", action="store_true")
    x.set_defaults(fn=cmd_protect_secrets)
    a = ap.parse_args(argv)
    return a.fn(a)
