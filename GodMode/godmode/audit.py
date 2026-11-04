"""Hash-chained audit log (JSONL). Each line carries the hash of the previous line, so an edited, removed
or truncated line is detected. Lives where the low-integrity worker can't write."""
import hashlib
import json
import time
from pathlib import Path

GENESIS = "0" * 64


def _hash(prev, body):
    return hashlib.sha256((prev + "\n" + body).encode("utf-8")).hexdigest()


class AuditLog:
    def __init__(self, path, clock=time.time):
        self.path = Path(path)
        self.clock = clock

    def _last(self):
        if not self.path.exists():
            return GENESIS, 0
        prev, n = GENESIS, 0
        with open(self.path, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    prev, n = json.loads(line)["h"], n + 1
        return prev, n

    def write(self, event, **data):
        prev, n = self._last()
        rec = {"n": n, "t": round(self.clock(), 3), "event": event, "data": data, "prev": prev}
        body = json.dumps(rec, sort_keys=True, ensure_ascii=False)
        rec["h"] = _hash(prev, body)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, sort_keys=True, ensure_ascii=False) + "\n")
        return rec

    def verify(self, anchor=None):
        """(ok, reason). anchor = the last hash stored elsewhere, which catches truncation of the tail."""
        if not self.path.exists():
            return (anchor in (None, GENESIS)), "no log"
        prev, n = GENESIS, 0
        with open(self.path, encoding="utf-8") as f:
            for i, line in enumerate(f, 1):
                if not line.strip():
                    continue
                try:
                    rec = json.loads(line)
                    h = rec.pop("h")
                except (ValueError, KeyError):
                    return False, f"line {i} is not a valid record"
                if rec.get("prev") != prev or rec.get("n") != n:
                    return False, f"chain broken at line {i}"
                if _hash(prev, json.dumps(rec, sort_keys=True, ensure_ascii=False)) != h:
                    return False, f"line {i} was edited"
                prev, n = h, n + 1
        if anchor is not None and anchor != prev:
            return False, "log was truncated or replaced (anchor mismatch)"
        return True, f"{n} records verified"

    def head(self):
        return self._last()[0]
