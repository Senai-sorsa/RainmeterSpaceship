"""A private, minimal copy of the Python standard library for AppContainer children.

An AppContainer can only read folders granted to its SID. Granting the user's own Python install (3 GB,
with site-packages) would change ACLs outside GOD mode, so we copy just the interpreter + stdlib
(~50 MB, no site-packages) into %LOCALAPPDATA%\\CSpace\\GodMode\\runtime\\python and grant only that."""
import shutil
import sys
from pathlib import Path

SKIP = {"site-packages", "test", "idlelib", "tkinter", "turtledemo", "ensurepip", "lib2to3", "__pycache__",
        "venv", "pydoc_data"}


def build(dest, src=None):
    src = Path(src or sys.base_prefix)
    dest = Path(dest)
    if (dest / "python.exe").is_file():
        return dest
    tmp = dest.with_name(dest.name + ".partial")
    shutil.rmtree(tmp, ignore_errors=True)   # only our own partial copy
    tmp.mkdir(parents=True)
    for name in ("python.exe", "python3.dll", f"python{sys.version_info[0]}{sys.version_info[1]}.dll",
                 "vcruntime140.dll", "vcruntime140_1.dll"):
        if (src / name).is_file():
            shutil.copy2(src / name, tmp / name)
    shutil.copytree(src / "DLLs", tmp / "DLLs", ignore=shutil.ignore_patterns("tcl*", "tk*", "_tkinter*"))
    shutil.copytree(src / "Lib", tmp / "Lib", ignore=lambda d, names: [n for n in names if n in SKIP])
    tmp.rename(dest)
    return dest
