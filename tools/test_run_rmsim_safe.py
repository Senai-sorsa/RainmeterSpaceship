"""Self-check for run_rmsim_safe.py using a FAKE rmsim in a temp repo (never the real renderer).  Run:
  python3 -I tools/test_run_rmsim_safe.py"""
import glob
import os
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import run_rmsim_safe as rs

FAKE = '''import sys
from pathlib import Path
a = sys.argv
sc = Path(__file__).parent.parent / "Skins/Spaceship/@Resources/Settings.inc"
assert "Scale=2.5" in sc.read_text(), sc.read_text()
assert not (sc.parent / "Icons").exists() and not list((sc.parent / "Data").glob("jarvis*"))
assert (sc.parent / "Data/keep.txt").exists() and Path(__file__).with_name("layoutlib.py").exists()
Path(a[a.index("--out") + 1]).write_bytes(b"PNG")
if "--mutate" in a:
    open(ORIG, "a").write("!")
print("rendered 1 modules -> x; 3 problems")
sys.exit(int(a[a.index("--code") + 1]) if "--code" in a else 0)
'''

with tempfile.TemporaryDirectory() as d:
    repo = Path(d) / "repo"
    res = repo / "Skins/Spaceship/@Resources"
    for p in ("tools", "layout", "Skins/Spaceship/@Resources/Icons", "Skins/Spaceship/@Resources/Data"):
        (repo / p).mkdir(parents=True)
    (repo / "tools/rmsim.py").write_text(f"ORIG = {str(res / 'Settings.inc')!r}\n" + FAKE)
    (repo / "tools/layoutlib.py").write_text("")
    (repo / "layout/layout.json").write_text("{}")
    (res / "Settings.inc").write_text("[V]\nScale=0.67\n")
    (res / "Icons/a.png").write_text("x")
    (res / "Data/keep.txt").write_text("k")
    (res / "Data/jarvis_x.txt").write_text("secret")
    git = lambda *a: subprocess.run(["git", "-C", str(repo), *a], check=True, capture_output=True)  # noqa: E731
    git("init", "-q"); git("add", "-A"); git("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "i")
    out = Path(d) / "o.png"
    tmpglob = os.path.join(tempfile.gettempdir(), "rmsim-safe-*")
    pre = set(glob.glob(tmpglob))
    py = sys.executable

    assert rs.run_safe(repo, out, "2.5", [], python=py) == 0 and out.read_bytes() == b"PNG"
    out.unlink()
    assert rs.run_safe(repo, out, "2.5", ["--code", "1"], python=py) == 0 and out.exists()   # audit problems tolerated
    assert rs.run_safe(repo, out, "2.5", ["--code", "1"], strict=True, python=py) == 1
    out.unlink()
    assert rs.run_safe(repo, out, "2.5", ["--code", "3"], python=py) == 2 and not out.exists()  # failure
    assert rs.run_safe(repo, Path(d) / "o.txt", "2.5", python=py) == 2     # bad extension
    assert rs.run_safe(repo, Path(d) / "nope" / "o.png", "2.5", python=py) == 2
    assert rs.run_safe(repo, out, "x;rm", python=py) == 2
    assert "Scale=0.67" in (res / "Settings.inc").read_text()              # real file untouched
    assert set(glob.glob(tmpglob)) == pre                                  # temp dirs cleaned up

    # a run that modifies the repo's Skins tree must fail loudly
    assert rs.run_safe(repo, out, "2.5", ["--mutate"], python=py) == 2
    assert set(glob.glob(tmpglob)) == pre
print("ok")
