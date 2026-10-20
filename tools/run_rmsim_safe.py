#!/usr/bin/env python3
"""Run tools/rmsim.py against a throw-away COPY of the skin so the repo's Skins/ tree is never touched.

  python3 -I tools/run_rmsim_safe.py --scale 1.0 --scenario full --updates 3 --out some/dir/render.png [--strict]

Exit: 0 render ok (rmsim audit problems, exit 1, are printed and tolerated unless --strict), 1 = --strict and
problems, 2 = failure (rmsim crashed, no PNG, bad args, or the repo's Skins tree changed during the run)."""
import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
VENV_PY = Path.home() / ".venvs" / "rmsim" / "bin" / "python"


def _ignore(src, names):
    s = Path(src)
    out = {n for n in names if n.endswith(".onnx") or n == "__pycache__"}
    if s.name == "@Resources":
        out |= {"Icons"} & set(names)
    if s.name == "Data":
        out |= {n for n in names if n.lower().startswith("jarvis")}
    if s.name == "Images":
        out |= {"Jarvis"} & set(names)
    return out


def skins_status(repo):
    r = subprocess.run(["git", "-C", str(repo), "status", "--porcelain", "--", "Skins"],
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"git status failed: {r.stderr.strip()}")
    return r.stdout


def run_safe(repo, out, scale="1.0", rm_args=(), strict=False, python=VENV_PY):
    repo, out = Path(repo), Path(out)
    if out.suffix.lower() != ".png" or not out.parent.is_dir():
        print("error: --out must end in .png and its parent must exist", file=sys.stderr)
        return 2
    if not re.fullmatch(r"\d+(\.\d+)?", str(scale)):
        print("error: --scale must be a number", file=sys.stderr)
        return 2
    before = skins_status(repo)
    systmp = Path(tempfile.gettempdir()).resolve()
    tmp = Path(tempfile.mkdtemp(prefix="rmsim-safe-")).resolve()
    try:
        assert tmp.parent == systmp and tmp.name.startswith("rmsim-safe-")
        (tmp / "tools").mkdir()
        for f in ("rmsim.py", "layoutlib.py"):
            shutil.copy2(repo / "tools" / f, tmp / "tools" / f)
        shutil.copytree(repo / "layout", tmp / "layout")
        shutil.copytree(repo / "Skins" / "Spaceship", tmp / "Skins" / "Spaceship", ignore=_ignore)
        si = tmp / "Skins" / "Spaceship" / "@Resources" / "Settings.inc"
        new, n = re.subn(r"(?im)^Scale=.*$", f"Scale={scale}", si.read_text(encoding="utf-8-sig"))
        if n:
            si.write_text(new, encoding="utf-8")
        png = tmp / "render.png"
        r = subprocess.run([str(python), "-I", str(tmp / "tools" / "rmsim.py"), "--out", str(png), *rm_args],
                           cwd=tmp, capture_output=True, text=True)
        if r.returncode not in (0, 1) or not png.exists():
            print(f"error: rmsim failed (exit {r.returncode})\n{r.stdout[-2000:]}\n{r.stderr[-2000:]}", file=sys.stderr)
            return 2
        shutil.copy2(png, out)
        print(next((l for l in reversed(r.stdout.splitlines()) if l.startswith("rendered ")), f"rmsim exit {r.returncode}"))
    finally:
        if tmp.parent == systmp:
            shutil.rmtree(tmp, ignore_errors=True)
    after = skins_status(repo)
    if after != before:
        print(f"error: Skins/ changed in git during the run!\nbefore: {before!r}\nafter: {after!r}", file=sys.stderr)
        return 2
    return 1 if (r.returncode == 1 and strict) else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", required=True)
    ap.add_argument("--scale", default="1.0")
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--scenario")
    ap.add_argument("--updates")
    a = ap.parse_args()
    rm = []
    for k in ("scenario", "updates"):
        if getattr(a, k) is not None:
            rm += [f"--{k}", getattr(a, k)]
    sys.exit(run_safe(REPO, a.out, a.scale, rm, a.strict))


if __name__ == "__main__":
    main()
