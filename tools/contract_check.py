"""Third implementation of the UI-to-host message check (the others: src/host/contract.ts, ShipCore.Core/Protocol.cs).
JARVIS-side code can import this. contract/fixtures/ui-to-host.json is the shared test (tools/test_contract_check.py).
Pure functions: no OS calls."""
import re

KEY = re.compile(r"[A-Za-z][A-Za-z0-9_]{0,63}\Z", re.ASCII)
FLOWS = {"gmail", "calendars", "obsidian"}
LONE = re.compile("[\ud800-\udfff]")  # a lone surrogate is not text the host can read
CTRL_TEXT = re.compile("[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")  # tab and newline stay legal in free text
CTRL_VALUE = re.compile("[\x00-\x1f\x7f]")


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
    return "unknown type"
