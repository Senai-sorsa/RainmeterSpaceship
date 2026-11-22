"""Runs a test file with tripwires under every real destructive door, so a test that forgot a fake FAILS instead of acting.
The test's own fakes replace the attributes the tripwires sit on, so a properly faked call never reaches a tripwire.
Tripwires: subprocess.Popen (so subprocess.run), os.system/startfile/kill, os.remove/unlink/rmdir and shutil.rmtree outside the
temp folder, winreg writes, windll shell32/powrprof/advapi32 calls, user32 lock/exit/input calls, WinDLL of those DLLs.
Usage (from the Jarvis folder):  py -3 -B tests/guarded_run.py test_jarvis.py   (prints "tripwires hit: 0" when clean). No input, no network."""
import ctypes
import os
import runpy
import shutil
import subprocess
import sys
import tempfile

TMP = os.path.realpath(tempfile.gettempdir()).lower()
trips = []


def trip(what):
    trips.append(what)
    raise AssertionError("TRIPWIRE (a real destructive call was reached): " + what)


def under_tmp(p):
    try:
        return os.path.realpath(p).lower().startswith(TMP)
    except Exception:
        return False


_real_popen_init = subprocess.Popen.__init__


def popen_init(self, args, *a, **k):
    trip(f"subprocess.Popen({args!r})")


subprocess.Popen.__init__ = popen_init

for name in ("system", "startfile", "kill", "killpg", "_exit"):
    if hasattr(os, name) and name != "_exit":
        setattr(os, name, (lambda n: lambda *a, **k: trip(f"os.{n}{a!r}"))(name))

_real_remove, _real_unlink, _real_rmtree, _real_rmdir = os.remove, os.unlink, shutil.rmtree, os.rmdir


def guard_path(fn, label):
    def w(path, *a, **k):
        if not under_tmp(path):
            trip(f"{label}({path!r}) outside the temp folder")
        return fn(path, *a, **k)
    return w


os.remove = guard_path(_real_remove, "os.remove")
os.unlink = guard_path(_real_unlink, "os.unlink")
os.rmdir = guard_path(_real_rmdir, "os.rmdir")
shutil.rmtree = guard_path(_real_rmtree, "shutil.rmtree")

try:
    import winreg
    for n in ("SetValueEx", "SetValue", "DeleteValue", "DeleteKey", "CreateKey", "CreateKeyEx", "DeleteKeyEx"):
        if hasattr(winreg, n):
            setattr(winreg, n, (lambda nn: lambda *a, **k: trip(f"winreg.{nn}"))(n))
except ImportError:
    pass

_real_windll = ctypes.windll


class Guard:
    """windll: shell32/powrprof/advapi32 are refused unless the test installed its own fake; user32 refuses the dangerous calls."""
    BAD_DLL = {"shell32", "powrprof", "advapi32", "wlanapi", "bthprops"}
    BAD_USER32 = {"LockWorkStation", "ExitWindowsEx", "keybd_event", "SendInput", "mouse_event", "SetCursorPos", "BlockInput", "SetSuspendState"}

    def __init__(self):
        object.__setattr__(self, "_over", {})

    def __getattr__(self, name):
        o = object.__getattribute__(self, "_over")
        if name in o:
            return o[name]
        if name in self.BAD_DLL:
            class Trap:                      # fetching the attribute is harmless; CALLING anything on it is the tripwire
                def __getattr__(s, fn):
                    return lambda *a, **k: trip(f"ctypes.windll.{name}.{fn} called without a fake")
            return Trap()
        if name == "user32":
            real = getattr(_real_windll, "user32")
            bad = self.BAD_USER32

            class U:
                def __getattr__(s, n):
                    if n in bad:
                        trip(f"user32.{n}")
                    return getattr(real, n)
            return U()
        return getattr(_real_windll, name)

    def __setattr__(self, name, value):
        object.__getattribute__(self, "_over")[name] = value

    def __delattr__(self, name):
        object.__getattribute__(self, "_over").pop(name, None)


ctypes.windll = Guard()
_real_WinDLL = ctypes.WinDLL


def WinDLL(name, *a, **k):
    if str(name).lower().split(".")[0] in Guard.BAD_DLL:
        trip(f"ctypes.WinDLL({name!r}) used without a fake")
    return _real_WinDLL(name, *a, **k)


ctypes.WinDLL = WinDLL

path = os.path.abspath(sys.argv[1])
sys.argv = [path]
sys.path.insert(0, os.path.dirname(path))
try:
    runpy.run_path(path, run_name="__main__")
except SystemExit as e:
    print("exit:", e.code)
    sys.exit(e.code or 0)
finally:
    print(f"tripwires hit: {len(trips)}" + ("" if not trips else " -> " + "; ".join(trips)))
