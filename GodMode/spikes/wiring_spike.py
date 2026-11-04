"""Spike: the wiring, end to end, with real processes.
Part 1, reader split: the real low-IL reader child serves fs_read/fs_list; a NO_READ_UP-labelled scratch
folder is refused by the OS (not by our code); a tricky path trips in the broker.
Part 2, tests in the AppContainer: `sandbox-setup` (GOD mode folders only, no venv grant), then GOD mode's
own unit-test suite is copied and run through testgate.run_suite inside the AppContainer: no network,
no user files, private runtime.
Touches only its own scratch folders. Run: py -3 -I GodMode/spikes/wiring_spike.py"""
import shutil
import sys
import tempfile
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from godmode import hardening, paths, testgate  # noqa: E402
from godmode import sandbox_win as sb  # noqa: E402
from godmode.gate import Violation  # noqa: E402
from godmode.reader import RemoteTools  # noqa: E402
from godmode.tools import ToolBox  # noqa: E402


def part1(checks):
    d = Path(tempfile.mkdtemp(prefix="godwire-"))
    (d / "notes.txt").write_text("hello from a normal file\n", encoding="utf-8")
    sec = d / "vaultish"
    sec.mkdir()
    (sec / "keys.txt").write_text("pretend secret\n", encoding="utf-8")
    sb.set_label(sec, no_read_up=True)
    rt = RemoteTools.start(ToolBox(proposer=None))
    try:
        out = rt.call("fs_read", {"path": str(d / "notes.txt")})
        checks.append(("reader (low IL) reads a normal file", "hello from a normal file" in out))
        checks.append(("reader lists a folder", "notes.txt" in rt.call("fs_list", {"path": str(d)})))
        out = rt.call("fs_read", {"path": str(sec / "keys.txt")})
        print("labelled read ->", out[:120])
        checks.append(("OS refuses the labelled folder to the reader", "pretend secret" not in out))
        try:
            rt.call("fs_read", {"path": str(d / "notes.txt") + ":ads"})
            tripped = False
        except (Violation, paths.PathRejected):
            tripped = True
        checks.append(("tricky path trips in the broker", tripped))
        pids = rt.proc.pids()
        print("reader alive:", rt.proc.alive(), "job pids:", pids)
        checks.append(("reader runs in its own job (reader + its console host at most)", rt.proc.alive() and rt.proc.pid in pids and len(pids) <= 2))
    finally:
        rt.close()
        sb.set_label(sec, no_read_up=False)
        for f in sec.iterdir():
            sb.set_label(f, no_read_up=False)
        shutil.rmtree(d, ignore_errors=True)


def part2(checks):
    st = hardening.sandbox_setup(venv=False)
    f = hardening.ac_folders()
    work = f["work"] / f"spike-{uuid.uuid4().hex[:6]}"
    tmp = f["actmp"] / work.name
    tmp.mkdir(parents=True)
    try:
        n = testgate.make_copy(ROOT.parent, work, ["GodMode"], ["__pycache__", "spikes", "*.md"])
        suite = {"name": "godmode-unit", "cwd": "GodMode",
                 "argv": ["{venv_python}", "-B", "-m", "unittest", "discover", "-s", "tests", "-t", "."],
                 "pass": "OK", "timeout": 300}

        def runner(argv, cwd, env, timeout):
            return sb.run(argv, cwd=cwd, env=env, timeout=timeout, sandbox="appcontainer",
                          limits=sb.Limits(cpu_pct=60, private_commit=2 << 30))
        r = testgate.run_suite(suite, work, runner, {}, tmp, appcontainer=(f["runtime"] / "python.exe", ""))
        print(f"copied {n} files; AppContainer unit run: code={r.code} {r.seconds}s")
        print("  " + "\n  ".join(r.tail.strip().splitlines()[-4:]))
        checks.append(("GOD mode's unit tests pass inside the AppContainer", r.passed and "Ran " in r.tail))
        checks.append(("AppContainer path needs no venv grant for stdlib-only suites", "venv_site_packages" not in st))
    finally:
        shutil.rmtree(work, ignore_errors=True)
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    checks = []
    part1(checks)
    part2(checks)
    for name, ok in checks:
        print(("PASS " if ok else "FAIL ") + name)
    return 0 if all(ok for _, ok in checks) else 1


if __name__ == "__main__":
    sys.exit(main())
