"""Third implementation of the UI-to-host message check (the others: src/host/contract.ts, ShipCore.Core/Protocol.cs).
JARVIS-side code can import this. contract/fixtures/ui-to-host.json is the shared test (tools/test_contract_check.py).
Pure functions: no OS calls."""
import re

KEY = re.compile(r"[A-Za-z][A-Za-z0-9_]{0,63}\Z", re.ASCII)
FLOWS = {"gmail", "calendars", "obsidian"}
LONE = re.compile("[\ud800-\udfff]")  # a lone surrogate is not text the host can read
CTRL_TEXT = re.compile("[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")  # tab and newline stay legal in free text
CTRL_VALUE = re.compile("[\x00-\x1f\x7f]")
# the newer host messages; each list copies ShipCore.Core (Protocol, DialGate, HitRegions, LltGate, JarvisStatus, AppLaunch)
DIAL_CONTROLS = {"brightness", "volume", "mic", "power", "refresh"}
DIAL_MODES = {"quiet", "balance", "performance"}
DIAL_RATES = {"60", "165"}
MAX_RECTS, MAX_COORD = 64, 16384
APP_ID = re.compile(r"[A-Za-z0-9_.-]{1,64}\Z", re.ASCII)
TARGETS = {"taskmgr", "taskperf", "todo", "sound", "display", "power", "mute", "prev", "playpause", "next",
           "terminal", "powershell", "about", "outlookcal", "gcal", "gmail", "update", "defender", "network", "wifi",
           "spx", "ollama", "tailscale", "drive", "battery", "audionext", "jarvislog"}
LLT_FEATURES = {"hybrid", "power", "refresh", "battery"}
LLT_WORD = re.compile(r"[A-Za-z0-9-]{1,32}\Z", re.ASCII)
REFRESH_KINDS = {"llt", "upkeep", "dev", "mail", "calendar"}
JARVIS_VERBS = {"wake", "cancel", "ask", "forget", "reindex", "train", "quit", "start"}
MAX_ASK = 500


def _whole(v, lo, hi):
    """A whole number in [lo, hi]; bool is not a number, and 1.0 counts as whole (as JS sees it)."""
    return not isinstance(v, bool) and isinstance(v, (int, float)) and float(v).is_integer() and lo <= v <= hi


def _s(m, name):
    v = m.get(name)
    return v if isinstance(v, str) else None


def problem(m, actions):
    """None when the message is well formed, else why not. `actions` = contract/config-keys.json "actions"."""
    if not isinstance(m, dict) or not isinstance(m.get("type"), str):
        return "not a message"
    t = m["type"]
    if t == "config.get":
        ks = m.get("keys")
        ok = isinstance(ks, list) and len(ks) <= 500 and all(isinstance(k, str) and KEY.match(k) for k in ks)
        return None if ok else "bad keys"
    if t == "config.set":
        k, v = _s(m, "key"), _s(m, "value")
        if k is None or not KEY.match(k):
            return "bad key"
        if v is None or len(v) > 256 or CTRL_VALUE.search(v) or LONE.search(v):
            return "bad value"
        i = m.get("id")
        # bool is an int in Python; floats such as 1.0 are what JS calls integers, so accept them like the TS side does
        ok = not isinstance(i, bool) and isinstance(i, (int, float)) and float(i).is_integer() and 0 <= i <= 2**53 - 1
        return None if ok else "bad id"
    if t in ("setup.get", "aboutme.get"):
        return None
    if t == "setup.finish":
        return None if m.get("mode") in ("defaults", "custom") else "bad mode"
    if t == "aboutme.set":
        x = _s(m, "text")
        return None if x is not None and len(x) <= 4000 and not CTRL_TEXT.search(x) and not LONE.search(x) else "bad text"
    if t == "action":
        return None if _s(m, "id") in set(actions) else "action not allowed"
    if t == "flow.open":
        return None if _s(m, "flow") in FLOWS else "bad flow"
    if t == "dial.set":
        c = _s(m, "control")
        if c not in DIAL_CONTROLS:
            return "bad control"
        if not _whole(m.get("id"), 0, 2**53 - 1):
            return "bad id"
        if "value" not in m:
            return "bad value"
        v = m["value"]
        if c in ("power", "refresh"):
            ok = isinstance(v, str) and v in (DIAL_MODES if c == "power" else DIAL_RATES)
        else:
            ok = _whole(v, 0, 100)
        return None if ok else "bad value"
    if t == "hit.regions":
        if not isinstance(m.get("keyboard"), bool):
            return "bad keyboard"
        rs = m.get("rects")
        if not isinstance(rs, list) or len(rs) > MAX_RECTS:
            return "bad rects"
        for r in rs:
            if not (isinstance(r, list) and len(r) == 4 and all(_whole(n, -2**31, 2**31 - 1) for n in r)):
                return "bad rects"
            x, y, w, h = r
            if not (-MAX_COORD <= x <= MAX_COORD and -MAX_COORD <= y <= MAX_COORD and 1 <= w <= MAX_COORD and 1 <= h <= MAX_COORD):
                return "bad rects"
        return None
    if t == "app.launch":
        a = _s(m, "id")
        return None if a is not None and APP_ID.match(a) else "bad app id"
    if t == "target.open":
        return None if _s(m, "what") in TARGETS else "bad target"
    if t == "llt.set":
        if _s(m, "feature") not in LLT_FEATURES:
            return "bad feature"
        v = _s(m, "value")
        if v is None or not LLT_WORD.match(v):
            return "bad value"
        return None if _whole(m.get("id"), 0, 2**53 - 1) else "bad id"
    if t == "status.refresh":
        return None if "kind" not in m or _s(m, "kind") in REFRESH_KINDS else "bad kind"
    if t == "speed.run":
        return None
    if t == "jarvis.cmd":
        c = _s(m, "cmd")
        if c not in JARVIS_VERBS:
            return "bad cmd"
        x = _s(m, "text")
        return None if c != "ask" or (x is not None and len(x) <= MAX_ASK) else "bad text"
    return "unknown type"
