"""actions: moved verbatim from jarvis.py (refactor). See JARVIS-Repair-Plan.txt, REFACTOR."""
import ctypes
import os
import re
import subprocess
import time
from .audio import mic_volume, speakers
from .base import DATA, NO_WINDOW, log, read_kv


def start_apps():
    """The installed apps the HUD scanned, or None while that list is missing (not the same as no apps)."""
    out = []
    try:
        with open(os.path.join(DATA, "StartApps.txt"), "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                if "|" in line:
                    name, appid = line.rstrip("\n").split("|", 1)
                    out.append((name.strip(), appid.strip()))
    except OSError:
        return None
    return out


def best_app(name):
    """The installed app whose name best matches what you said."""
    want = re.sub(r"[^a-z0-9 ]", "", name.lower()).strip()
    if not want:
        return None
    best, score = None, 0
    for disp, appid in start_apps() or []:
        d = disp.lower()
        if any(x in d for x in ("uninstall", "help", "readme", "documentation")):
            continue
        # a prefix needs 3+ letters and anything looser a whole word, so "open e" matches nothing
        sc = 3 if d == want else (2 if len(want) >= 3 and d.startswith(want) else
                                  (1 if re.search(r"\b" + re.escape(want) + r"\b", d) else 0))
        if sc > score or (sc == score and sc and best and len(disp) < len(best[0])):
            best, score = (disp, appid), sc
    return best if score else None


def running_window(name):
    """An open app (from the HUD's window list) whose exe matches what you said, e.g. 'chrome' -> chrome.exe."""
    want = re.sub(r"[^a-z0-9]", "", name.lower())
    stems = [(exe, re.sub(r"[^a-z0-9]", "", os.path.splitext(exe)[0].lower())) for exe in open_windows()]
    # exact name first, then a 3+ letter prefix, then a 4+ letter fragment: "close e" must not pick explorer
    for ok in (lambda s: s == want, lambda s: len(want) >= 3 and s.startswith(want), lambda s: len(want) >= 4 and want in s):
        for exe, stem in stems:
            if want and ok(stem):
                return exe
    return None


def act_volume(change):
    how, n = change                                           # ("set", 30) or ("step", -10)
    if how == "step":
        n += speakers()[1]
    speakers(volume=max(0, min(100, n)) / 100)


def act_mic_level(change):
    how, n = change                                           # ("set", 80) or ("step", -10), the same as act_volume
    if how == "step":
        n += mic_volume()[1]
    mic_volume(volume=max(0, min(100, n)) / 100)


MEDIA_KEYS = {"playpause": 0xB3, "next": 0xB0, "prev": 0xB1}


def press_key(vk):
    """Press and release one key. Windows gives no result back, so nobody can tell whether a player took it."""
    for flags in (0, 2):                                      # down, up
        ctypes.windll.user32.keybd_event(vk, 0, flags, 0)


def done_line(action, target):
    """What to say after an action that worked: the value Windows reports, never the one asked for."""
    if action == "open":
        return f"Opening {target[0]}."
    if action == "volume":
        return f"Volume at {speakers()[1]} percent."
    if action in ("mic_mute", "mic_unmute", "mic_level"):      # read back from Windows, not what was asked
        is_muted, percent = mic_volume()
        return "Microphone muted." if is_muted else "Microphone unmuted." if action == "mic_unmute" else f"Microphone at {percent} percent."
    if action == "sleep" and screen_only[0]:
        return "This PC can't sleep that way, so I turned the screen off."
    return "Sent." if action == "media" else "Done."


def run_ok(args):
    """Run one fixed command: anything but exit code 0 within 10 s is a failure (TimeoutExpired / OSError)."""
    code = subprocess.run(args, creationflags=NO_WINDOW, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                          timeout=10).returncode
    if code:
        raise OSError(f"{args[0]} ended with code {code}")


def open_windows():
    return re.findall(r"^W (.+)$", read_kv("windows.txt"), re.M)


# action handlers: (description for the confirmation, function). Only these can ever run.
def act_open(app):
    os.startfile("shell:AppsFolder\\" + app[1]) if not os.path.isabs(app[1]) else os.startfile(app[1])


def act_close(exe):
    if exe not in open_windows():                             # it went away while you were being asked
        raise OSError("it is not open any more")
    # taskkill only asks the windows to close, and its exit code is non-zero for any helper process without a
    # window (a browser has many), so the result is read from the HUD's window list instead (rewritten every 1.5 s)
    subprocess.run(["taskkill", "/IM", exe], creationflags=NO_WINDOW, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                   timeout=10)
    for _ in range(10):
        time.sleep(0.5)
        text = read_kv("windows.txt")                         # gone only by a fresh list: an unreadable or stale one proves nothing
        t = re.match(r"T (\d+)", text)
        if t and time.time() - int(t.group(1)) < 10 and exe not in re.findall(r"^W (.+)$", text, re.M):
            return
    raise OSError("it is still open (it may be asking to save)")


def act_lock(_):
    if not ctypes.windll.user32.LockWorkStation():
        raise OSError("Windows refused to lock")


screen_only = [False]                                          # 7-L1: the last sleep only turned the screen off


def act_sleep(_):
    # asked directly so the answer comes back (rundll32 always exits 0); it returns once the PC wakes again
    screen_only[0] = False
    if ctypes.WinDLL("powrprof", use_last_error=True).SetSuspendState(0, 1, 0):
        return
    screen_only[0] = True
    # S2-11: Modern Standby laptops (S0, no S3) refuse it; turning the screen off is how they enter standby
    log(f"sleep: suspend refused (error {ctypes.get_last_error()}) - screen off for Modern Standby")
    if not ctypes.windll.user32.PostMessageW(0xFFFF, 0x0112, 0xF170, 2):   # broadcast WM_SYSCOMMAND SC_MONITORPOWER off
        raise OSError("Windows refused to sleep")
