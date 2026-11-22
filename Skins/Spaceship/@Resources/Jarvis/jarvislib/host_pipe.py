"""host_pipe: JARVIS side of the standalone host's pipe (SpaceshipApp/ShipCore.App/JarvisPipe.cs).

Wire format and verdicts are shared with C# through contract/fixtures/host-pipe.json. Imports nothing from jarvislib,
so base.py can use it without a cycle.
"""
import ctypes
import json
import os
import re
import tempfile

PIPE_NAME = re.compile(r"SpaceshipHost-[A-Za-z0-9._-]{1,64}-[0-9a-f]{32}")
SESSION_FILE = os.path.join(tempfile.gettempdir(), "spaceship-app", "host-session.json")
ERROR_SEM_TIMEOUT = 121  # the pipe exists but every instance is busy


def read_session(path=SESSION_FILE):
    """The session the host wrote, or None when it is missing or does not name a pipe we accept."""
    try:
        with open(path, encoding="utf-8") as f:
            s = json.load(f)
    except (OSError, ValueError):
        return None
    if not isinstance(s, dict) or not PIPE_NAME.fullmatch(str(s.get("pipe", ""))):
        return None
    if not all(isinstance(s.get(k), str) for k in ("nonce", "session")) or not isinstance(s.get("pid"), int):
        return None
    return s


def wait_named_pipe(name):
    """(exists, last_error). WaitNamedPipe with timeout 0 only checks; it does not connect."""
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    ok = kernel32.WaitNamedPipeW("\\\\.\\pipe\\" + name, 0)
    return bool(ok), ctypes.get_last_error()


def host_live(session=None, wait=wait_named_pipe):
    """True while the host's pipe exists, including when it is busy with another client."""
    if os.name != "nt":
        return False
    s = session if session is not None else read_session()
    if s is None:
        return False
    ok, err = wait(s["pipe"])
    return ok or err == ERROR_SEM_TIMEOUT


def handshake(session, open_pipe):
    """Connect, send the hello, and return True only when the host answers ready. Closing the pipe ends the connection."""
    try:
        f = open_pipe("\\\\.\\pipe\\" + session["pipe"])
    except OSError:
        return False
    try:
        hello = {"type": "hello", "nonce": session["nonce"], "pid": os.getpid(), "session": session["session"]}
        f.write((json.dumps(hello) + "\n").encode("utf-8"))
        line = bytearray()
        while len(line) < 1024:
            c = f.read(1)
            if not c or c == b"\n":
                break
            line += c
        return json.loads(line.decode("utf-8", "replace")).get("type") == "ready"
    except (OSError, ValueError, AttributeError):
        return False
    finally:
        f.close()


def open_real_pipe(path):
    return open(path, "r+b", buffering=0)
