"""Tests for jarvislib/host_pipe.py with fake streams only: no real pipe is opened and the real session file is never read.
Run: py -3 -I test_host_pipe.py   (-I does not add this folder to sys.path, so it is added here)
"""
import io
import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from jarvislib import host_pipe  # noqa: E402

FIXTURE = os.path.join(HERE, "..", "..", "..", "..", "contract", "fixtures", "host-pipe.json")
SESSION = {"pipe": "SpaceshipHost-Senai-0123456789abcdef0123456789abcdef", "nonce": "n1", "session": "s1", "pid": 42}
READY = b'{"type":"ready"}\n'


class FakePipe:
    """Stands in for the pipe: reads come from `reply`, writes are kept in `sent`."""

    def __init__(self, reply=b""):
        self.reply = io.BytesIO(reply)
        self.sent = b""
        self.closed = False

    def read(self, n):
        return self.reply.read(n)

    def write(self, b):
        self.sent += b
        return len(b)

    def close(self):
        self.closed = True


def refuse(path):
    raise OSError("fake: no pipe at " + path)


def test_pipe_names_match_the_shared_fixture():
    with open(FIXTURE, encoding="utf-8") as f:
        cases = json.load(f)["pipe_names"]
    for c in cases:
        assert bool(host_pipe.PIPE_NAME.fullmatch(c["name"])) == c["valid"], repr(c["name"])


def test_read_session_accepts_a_good_file_and_refuses_bad_ones():
    path = os.path.join(tempfile.mkdtemp(), "host-session.json")  # this test's own folder

    def read_obj(obj):
        with open(path, "w", encoding="utf-8") as f:
            f.write(obj if isinstance(obj, str) else json.dumps(obj))
        return host_pipe.read_session(path)

    assert read_obj(SESSION) == SESSION
    assert read_obj({**SESSION, "pipe": "..\\evil-0123456789abcdef0123456789abcdef"}) is None
    assert read_obj({k: v for k, v in SESSION.items() if k != "pid"}) is None
    assert read_obj({**SESSION, "pid": "42"}) is None
    assert read_obj("not json") is None
    assert host_pipe.read_session(path + ".missing") is None


def test_handshake_sends_a_hello_and_returns_true_on_ready():
    pipe = FakePipe(READY)
    seen = []

    def open_pipe(path):
        seen.append(path)
        return pipe

    assert host_pipe.handshake(SESSION, open_pipe) is True
    assert seen == ["\\\\.\\pipe\\" + SESSION["pipe"]]
    hello = json.loads(pipe.sent.decode("utf-8"))
    assert hello == {"type": "hello", "nonce": "n1", "pid": os.getpid(), "session": "s1"}
    assert pipe.closed


def test_handshake_is_false_without_ready():
    assert host_pipe.handshake(SESSION, lambda p: FakePipe(b'{"type":"config"}\n')) is False
    assert host_pipe.handshake(SESSION, lambda p: FakePipe(b"")) is False
    assert host_pipe.handshake(SESSION, refuse) is False


def test_host_live_reads_the_pipe_state_without_connecting():
    assert host_pipe.host_live(SESSION, wait=lambda name: (True, 0)) is True
    assert host_pipe.host_live(SESSION, wait=lambda name: (False, host_pipe.ERROR_SEM_TIMEOUT)) is True  # busy, still up
    assert host_pipe.host_live(SESSION, wait=lambda name: (False, 2)) is False  # ERROR_FILE_NOT_FOUND: host is gone


if __name__ == "__main__":
    failed = 0
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print("PASS", name)
            except AssertionError as e:
                failed += 1
                print("FAIL", name, e)
    print("failed:", failed)
    sys.exit(1 if failed else 0)
