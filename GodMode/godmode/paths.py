"""Path rules for every file the model asks about. Pure checks + a small OS-facts interface (fakeable).

A privacy block is NOT a tripwire (the model can't know a file is secret); a malformed or tricky path is."""
import fnmatch
import ntpath
import os
import re
import stat
from dataclasses import dataclass

PLACEHOLDER_MASK = 0x00400000 | 0x00040000 | 0x00001000   # RECALL_ON_DATA_ACCESS | RECALL_ON_OPEN | OFFLINE
REPARSE = 0x400
DEVICE_NAMES = {"con", "prn", "aux", "nul", "conin$", "conout$", *(f"com{i}" for i in range(1, 10)),
                *(f"lpt{i}" for i in range(1, 10))}
EXCLUDED_DRIVES = {"g:"}   # Google Drive for Desktop (cloud-backed)

# Matched case-insensitively against each path segment (dirs) or the file name.
SECRET_DIRS = {".ssh", ".gnupg", ".aws", ".azure", ".kube", ".docker", "credentials", "protect", "vault", "keys",
               "bitwarden", "1password", "keepass", "keepassxc", "user data", "profiles", "wallets", "exodus",
               "electrum", "metamask", ".password-store"}
SECRET_FILES = ["login data*", "cookies*", "local state", "web data*", "key3.db", "key4.db", "logins.json",
                "*.kdbx", "*.kdb", ".env", ".env.*", "*credential*", "*.pem", "*.pfx", "*.p12", "*.key", "id_rsa*",
                "id_ed25519*", "id_ecdsa*", "*.ovpn", ".npmrc", ".pypirc", ".netrc", "_netrc", ".git-credentials",
                "*secret*", "*token*", "wallet.dat", "ntuser.dat*", "sam", "system", "security"]
MAX_READ = 2 * 1024 * 1024


class PathRejected(ValueError):
    """Tricky or malformed path: treated as a violation."""


@dataclass(frozen=True)
class Verdict:
    ok: bool
    reason: str
    privacy: bool = False   # blocked by a privacy rule (not a violation)


class OSFacts:
    """Real file facts. Tests pass a fake with the same two methods."""

    def attributes(self, path):
        try:
            return os.lstat(path).st_file_attributes
        except (OSError, AttributeError):
            return None

    def exists(self, path):
        return os.path.lexists(path)


def canonical(path):
    """Absolute, normalised Windows path or PathRejected. No ADS, device, UNC, \\\\?\\ or relative paths."""
    if not isinstance(path, str) or not path or "\x00" in path or len(path) > 4096:
        raise PathRejected("empty or invalid path")
    p = path.replace("/", "\\")
    if p.startswith("\\\\"):
        raise PathRejected("UNC and device paths are not allowed")
    if not re.match(r"^[A-Za-z]:\\", p):
        raise PathRejected("path must be absolute, like C:\\...")
    if ":" in p[2:]:
        raise PathRejected("alternate data streams are not allowed")
    if "~" in p and re.search(r"~\d", p):
        raise PathRejected("8.3 short names are not allowed; use the long name")
    for seg in p[3:].split("\\"):
        if not seg:
            continue
        if seg in (".", ".."):
            raise PathRejected("'.' and '..' are not allowed")
        if seg != seg.rstrip(" ."):
            raise PathRejected("trailing dots or spaces are not allowed")
        if seg.split(".")[0].lower() in DEVICE_NAMES:
            raise PathRejected("device names are not allowed")
        if any(c in seg for c in '<>"|?*'):
            raise PathRejected("wildcards and reserved characters are not allowed")
    return ntpath.normpath(p)


def _segments(p):
    return [s for s in p[3:].split("\\") if s]


def is_secret(p):
    segs = [s.lower() for s in _segments(p)]
    if any(s in SECRET_DIRS for s in segs[:-1]):
        return True
    name = segs[-1] if segs else ""
    return name in SECRET_DIRS or any(fnmatch.fnmatchcase(name, pat) for pat in SECRET_FILES)


def under(p, root):
    p, root = p.lower().rstrip("\\"), root.lower().rstrip("\\")
    return p == root or p.startswith(root + "\\")


class PathPolicy:
    def __init__(self, facts=None, extra_denied=(), excluded_drives=EXCLUDED_DRIVES):
        self.facts = facts or OSFacts()
        self.extra_denied = [canonical(d) for d in extra_denied]
        self.excluded = {d.lower() for d in excluded_drives}

    def check_read(self, path):
        p = canonical(path)          # raises PathRejected (violation)
        if p[:2].lower() in self.excluded:
            return Verdict(False, "that drive is excluded (cloud drive)", privacy=True)
        if any(under(p, d) for d in self.extra_denied):
            return Verdict(False, "blocked by a GOD mode rule", privacy=True)
        if is_secret(p):
            return Verdict(False, "blocked by privacy rule", privacy=True)
        # Walk every segment: no reparse points (symlinks/junctions) anywhere on the way.
        cur = p[:3]
        for seg in _segments(p):
            cur = ntpath.join(cur, seg)
            a = self.facts.attributes(cur)
            if a is None:
                return Verdict(False, "not found or not readable")
            if a & REPARSE:
                return Verdict(False, "path goes through a link or junction, not followed")
            if a & PLACEHOLDER_MASK:
                return Verdict(False, "cloud placeholder, not downloaded on purpose", privacy=True)
        return Verdict(True, "ok")


def is_dir_attr(a):
    return bool(a is not None and a & stat.FILE_ATTRIBUTE_DIRECTORY)
