"""Forced tests for a tweak (plan section 4, steps 5-7). The broker runs this, never the model.

1. Copy the target subtrees into a fresh work folder (medium integrity: the low-IL worker and the
   low-IL test run can read it but not change it). No links followed, heavy/personal folders skipped.
2. Hash every protected file in the copy.
3. Run every suite on the untouched copy (baseline), apply the patch, run again.
4. Accept only if: both runs exit 0 and print the pass line, test count >= baseline (when countable),
   and the protected hashes are unchanged after both runs (DGM lesson: nothing on the scoring path moves)."""
import fnmatch
import hashlib
import json
import os
import re
import shutil
import time
from dataclasses import dataclass, field
from pathlib import Path

from . import tweak
from .gate import Violation

HERE = Path(__file__).resolve().parent
REPARSE = 0x400


def load_config(path=None):
    return json.loads(Path(path or HERE / "testgate.json").read_text(encoding="utf-8"))


def _ignored(name, patterns):
    return any(fnmatch.fnmatch(name, p) for p in patterns)


def make_copy(repo, work, subtrees, ignore):
    """Plain copy (no links). Refuses if `work` already exists. Returns the number of files copied."""
    repo, work = Path(repo), Path(work)
    if work.exists():
        raise FileExistsError(f"work folder already exists: {work}")
    n = 0
    for sub in subtrees:
        rel = tweak.clean_rel(sub)
        src = repo / rel
        for root, dirs, files in os.walk(src, followlinks=False):
            rootp = Path(root)
            keep = []
            for d in dirs:
                dp = rootp / d
                if _ignored(d, ignore) or dp.is_symlink() or (getattr(os.lstat(dp), "st_file_attributes", 0) & REPARSE):
                    continue
                keep.append(d)
            dirs[:] = keep
            for f in files:
                fp = rootp / f
                if _ignored(f, ignore) or fp.is_symlink() or (getattr(os.lstat(fp), "st_file_attributes", 0) & REPARSE):
                    continue
                dst = work / fp.relative_to(repo)
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(fp, dst)
                n += 1
    return n


def protected_manifest(work, surfaces):
    out = {}
    work = Path(work)
    for root, _, files in os.walk(work, followlinks=False):
        for f in files:
            p = Path(root) / f
            rel = p.relative_to(work).as_posix()
            if tweak.is_protected(rel, surfaces):
                out[rel] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


def write_files(work, files):
    """Writes the patched texts into the copy only. Paths re-checked; no links on the way."""
    work = Path(work).resolve()
    for rel, text in files.items():
        rel = tweak.clean_rel(rel)
        dst = (work / rel)
        cur = work
        for part in rel.split("/"):
            cur = cur / part
            if cur.exists() and (cur.is_symlink() or getattr(os.lstat(cur), "st_file_attributes", 0) & REPARSE):
                raise Violation("link-in-path", rel)
        if work not in dst.resolve().parents:
            raise Violation("escape", rel)
        with open(dst, "w", encoding="utf-8", newline="") as f:
            f.write(text)


# Runs a suite inside the AppContainer with the private runtime: venv packages via site.addsitedir (so .pth
# files work), the suite's folder on sys.path, then the script or module as __main__.
# Measured 2026-11-03: Windows forces TEMP to the container's own AC\Temp folder, and Python 3.12 creates
# mkdtemp() folders (mode 0o700) with an owner-only DACL that the AppContainer identity cannot write into.
# Inside the sandboxed test process only, 0o700 folders get the normal inherited ACL (AC\Temp is private
# to the container anyway).
AC_BOOT = "\n".join([
    "import os,runpy,site,sys",
    "_mk=os.mkdir",
    "def _mkdir(p, mode=0o777, *a, **k): return _mk(p, 0o777 if mode == 0o700 else mode, *a, **k)",
    "os.mkdir=_mkdir",
    "sp=sys.argv[1]",
    "site.addsitedir(sp) if sp else None",
    "sys.path.insert(0, os.getcwd())",
    "rest=[a for a in sys.argv[2:] if a not in ('-B','-I','-E','-s','-u')]",
    "if rest[0]=='-m':",
    "    sys.argv=[rest[1]]+rest[2:]; runpy.run_module(rest[1], run_name='__main__', alter_sys=True)",
    "else:",
    "    sys.argv=rest; runpy.run_path(rest[0], run_name='__main__')",
]) + "\n"


def ac_argv(suite_argv, runtime_python, site_packages):
    """Turns ["{venv_python}", "-B", "test_jarvis.py"] into an AppContainer command line."""
    return [str(runtime_python), "-B", "-I", "-c", AC_BOOT, str(site_packages or ""), *suite_argv[1:]]


@dataclass
class SuiteRun:
    name: str
    code: int | None
    passed: bool
    count: int | None
    seconds: float
    tail: str


def run_suite(suite, work, runner, vars_, temp_dir, appcontainer=None):
    """appcontainer = (runtime_python, site_packages) to run with no network / no user files."""
    argv = [vars_.get(a[1:-1], a) if re.fullmatch(r"\{\w+\}", a) else a for a in suite["argv"]]
    if appcontainer:
        argv = ac_argv(suite["argv"], *appcontainer)
    env = {"TEMP": str(temp_dir), "TMP": str(temp_dir), "PYTHONDONTWRITEBYTECODE": "1", "PYTHONIOENCODING": "utf-8",
           "NO_PROXY": "*", "HTTP_PROXY": "http://127.0.0.1:9", "HTTPS_PROXY": "http://127.0.0.1:9"}
    env.update(suite.get("env") or {})
    t0 = time.monotonic()
    code, out = runner(argv, cwd=str(Path(work) / tweak.clean_rel(suite["cwd"])), env=env,
                       timeout=int(suite.get("timeout", 600)))
    out = out or ""
    count = None
    if suite.get("count"):
        m = re.search(suite["count"], out)
        count = int(m.group(1)) if m else None
    passed = code == 0 and suite["pass"] in out
    return SuiteRun(suite["name"], code, passed, count, round(time.monotonic() - t0, 1), out[-3000:])


@dataclass
class GateReport:
    ok: bool
    reasons: list = field(default_factory=list)
    baseline: list = field(default_factory=list)
    patched: list = field(default_factory=list)


def judge(baseline, patched, manifest_before, manifest_after):
    reasons = []
    for b in baseline:
        if not b.passed:
            reasons.append(f"baseline {b.name} does not pass (code {b.code}); fix the tests first, no tweak accepted")
    for b, p in zip(baseline, patched):
        if not p.passed:
            reasons.append(f"{p.name} fails after the tweak (code {p.code})")
        if b.count is not None and (p.count is None or p.count < b.count):
            reasons.append(f"{p.name}: fewer tests ran ({p.count} < {b.count})")
    if len(patched) != len(baseline):
        reasons.append("not every suite ran")
    if manifest_before != manifest_after:
        changed = sorted(set(manifest_before.items()) ^ set(manifest_after.items()))
        reasons.append(f"protected files changed during the run: {[c[0] for c in changed][:5]}")
    return GateReport(not reasons, reasons)


def run_gate(repo, work, patch, runner, temp_dir, vars_, surfaces=None, config=None, appcontainer=None):
    """Full pipeline on a fresh copy. Raises Violation for protected paths (tripwire)."""
    s = surfaces or tweak.Surfaces.load()
    cfg = config or load_config()
    make_copy(repo, work, cfg["copy"]["subtrees"], cfg["copy"]["ignore"])
    res = tweak.check(patch, lambda rel: (Path(work) / rel).read_text(encoding="utf-8"), s)
    if not res.ok:
        return res, GateReport(False, res.problems)
    m0 = protected_manifest(work, s)
    base = [run_suite(x, work, runner, vars_, temp_dir, appcontainer) for x in cfg["suites"]]
    m1 = protected_manifest(work, s)
    write_files(work, res.files)
    pat = [run_suite(x, work, runner, vars_, temp_dir, appcontainer) for x in cfg["suites"]]
    m2 = protected_manifest(work, s)
    rep = judge(base, pat, m0, m2)
    if m0 != m1:
        rep.ok = False
        rep.reasons.append("protected files changed during the baseline run")
    rep.baseline, rep.patched = base, pat
    return res, rep
