"""One-time setup steps that change permissions. Each is explicit, recorded and undoable. No admin needed.

sandbox-setup        AppContainer for tests: private Python runtime + grants on GOD mode's own folders only.
sandbox-setup --venv also grant the AppContainer READ on the JARVIS venv site-packages (needs the user's OK),
                     so model-modified code is tested with NO network and NO access to the user's files.
protect-secrets      dry run: list secret folders that would get a NO_READ_UP label (low-IL processes can't
                     read them; normal apps are unaffected). --apply / --undo change them (needs the user's OK).
State: %LOCALAPPDATA%\\CSpace\\GodMode\\hardening.json"""
import json
import os
from pathlib import Path

from . import pyruntime
from . import sandbox_win as sb

STATE = "hardening.json"


def state_path():
    return sb.broker_dir() / STATE


def load_state():
    p = state_path()
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def save_state(s):
    p = state_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(s, indent=1), encoding="utf-8")


def venv_site_packages():
    return Path(os.environ.get("LOCALAPPDATA", "")) / "SpaceshipHUD" / "venv" / "Lib" / "site-packages"


def ac_folders():
    b = sb.broker_dir()
    return {"runtime": b / "runtime" / "python", "work": b / "work", "actmp": b / "ac-tmp"}


def sandbox_setup(venv=False, grant=sb.grant_appcontainer, build=pyruntime.build):
    f = ac_folders()
    build(f["runtime"])
    f["work"].mkdir(parents=True, exist_ok=True)
    f["actmp"].mkdir(parents=True, exist_ok=True)
    s = load_state()
    s["sid"] = grant(f["runtime"], "RX")
    grant(f["work"], "RX")
    grant(f["actmp"], "M")
    s["ac_granted"] = sorted({*s.get("ac_granted", []), str(f["runtime"]), str(f["work"]), str(f["actmp"])})
    if venv:
        sp = venv_site_packages()
        if not sp.is_dir():
            raise FileNotFoundError(sp)
        grant(sp, "RX")
        s["venv_site_packages"] = str(sp)
        s["ac_granted"] = sorted({*s["ac_granted"], str(sp)})
    save_state(s)
    return s


def sandbox_undo(revoke=sb.revoke_appcontainer):
    s = load_state()
    for p in s.get("ac_granted", []):
        if Path(p).exists():
            revoke(p)
    s.pop("ac_granted", None)
    s.pop("venv_site_packages", None)
    save_state(s)
    return s


def tests_in_appcontainer():
    """(runtime python, site-packages) if the AppContainer test path is fully set up, else None."""
    s = load_state()
    rt = ac_folders()["runtime"] / "python.exe"
    if s.get("venv_site_packages") and rt.is_file():
        return rt, s["venv_site_packages"]
    return None


# ---------------- secrets ----------------

def secret_candidates(env=os.environ):
    home = Path(env.get("USERPROFILE", str(Path.home())))
    appdata, local = Path(env.get("APPDATA", home / "AppData" / "Roaming")), Path(env.get("LOCALAPPDATA", home / "AppData" / "Local"))
    # Browser profiles are deliberately NOT here: some browser helper processes may run sandboxed and need them.
    return [home / ".ssh", home / ".gnupg", home / ".aws", home / ".azure", home / ".kube",
            home / ".docker", appdata / "Bitwarden", appdata / "KeePass", appdata / "KeePassXC",
            local / "1Password", appdata / "gnupg"]


def protect_secrets(apply=False, label=sb.set_label, candidates=None):
    targets = [p for p in (candidates if candidates is not None else secret_candidates()) if p.exists()]
    if not apply:
        return targets
    s = load_state()
    done = set(s.get("labelled", []))
    for p in targets:
        label(p, no_read_up=True)
        done.add(str(p))
    s["labelled"] = sorted(done)
    save_state(s)
    return targets


def unprotect_secrets(label=sb.set_label, max_files=20000):
    s = load_state()
    for p in s.get("labelled", []):
        root = Path(p)
        if not root.exists():
            continue
        label(root, no_read_up=False)
        n = 0
        for dirpath, dirs, files in os.walk(root):
            for name in dirs + files:
                if n >= max_files:
                    break
                try:
                    label(Path(dirpath) / name, no_read_up=False)
                except OSError:
                    pass
                n += 1
    s["labelled"] = []
    save_state(s)
    return s
