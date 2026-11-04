"""Tests for the gap fixes: guard, reader split, hardening setup, AppContainer argv, private server wiring.
Fakes only: no real process, ACL, label or model."""
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from godmode import hardening, memory, reader, servers, testgate
from godmode.gate import Violation
from godmode.guard import RunGuard

G = memory.GiB


class FakeProc:
    def __init__(self):
        self.calls = []

    def freeze(self):
        self.calls.append("freeze")

    def thaw(self):
        self.calls.append("thaw")

    def kill(self):
        self.calls.append("kill")


def snaps(*gib):
    it = iter(gib)
    return lambda: memory.Snapshot(32 * G, int(next(it) * G), 0, 0, 12 * G, 0)


class Guard(unittest.TestCase):
    def test_freeze_then_thaw(self):
        p = FakeProc()
        g = RunGuard(p, memory.Watchdog(), snaps(3.5, 3.5, 3.5, 8, 8, 8, 8, 8))
        acts = [g.tick() for _ in range(8)]
        self.assertEqual(p.calls, ["freeze", "thaw"])
        self.assertEqual((acts[2], acts[7], g.state), ("pause", "resume", "running"))

    def test_critical_kills_once(self):
        p = FakeProc()
        g = RunGuard(p, memory.Watchdog(), snaps(2, 2))
        g.tick(), g.tick()
        self.assertEqual(p.calls, ["kill"])
        self.assertEqual(g.state, "killed")

    def test_close_never_leaves_server_frozen(self):
        p = FakeProc()
        g = RunGuard(p, memory.Watchdog(), snaps(3.5, 3.5, 3.5))
        for _ in range(3):
            g.tick()
        g.close()
        self.assertEqual(p.calls, ["freeze", "thaw"])


class FakeBox:
    def call(self, name, args):
        if args.get("path") == "C:\\boom":
            raise Violation("bad-path", "x")
        return f"{name} ok"


def run_reader(lines):
    out = io.BytesIO()
    reader.serve(io.BytesIO(b"".join(lines)), out, FakeBox())
    return [json.loads(x) for x in out.getvalue().splitlines()]


class Reader(unittest.TestCase):
    def test_runs_read_tools(self):
        r = run_reader([b'{"id": 1, "tool": "fs_read", "args": {"path": "C:\\\\a"}}\n'])
        self.assertEqual(r, [{"id": 1, "out": "fs_read ok"}])

    def test_refuses_non_read_tools_as_violation(self):
        for tool in ("apply_patch", "sys_memory", "shell"):
            r = run_reader([json.dumps({"id": 2, "tool": tool, "args": {}}).encode() + b"\n"])
            self.assertEqual(r[0]["violation"][0], "tool-not-allowed")

    def test_garbage_never_crashes(self):
        r = run_reader([b"not json\n", b'{"id": 3, "tool": "fs_read", "args": "x"}\n',
                        b'{"id": 4, "tool": "fs_read", "args": {"path": "C:\\\\boom"}}\n'])
        self.assertIn("error", r[0])
        self.assertIn("violation", r[1])
        self.assertEqual(r[2]["violation"][0], "bad-path")


class LoopProc:
    """Fake reader process: whatever the broker writes is served by reader.serve on the fly."""

    def __init__(self):
        self.stdin = self
        self._out = io.BytesIO()
        self.stdout = self

    def write(self, b):
        resp = io.BytesIO()
        reader.serve(io.BytesIO(b), resp, FakeBox())
        self._out = io.BytesIO(resp.getvalue())

    def flush(self):
        pass

    def readline(self, n=-1):
        return self._out.readline()


class Remote(unittest.TestCase):
    def setUp(self):
        local = mock.Mock()
        local.call.return_value = "local"
        self.local = local
        self.rt = reader.RemoteTools(LoopProc(), local)

    def test_read_goes_to_reader(self):
        self.assertEqual(self.rt.call("fs_list", {"path": "C:\\x"}), "fs_list ok")
        self.local.call.assert_not_called()

    def test_other_tools_stay_in_broker(self):
        self.assertEqual(self.rt.call("apply_patch", {"reason": "r", "edits": []}), "local")

    def test_violation_from_reader_reraised(self):
        with self.assertRaises(Violation):
            self.rt.call("fs_read", {"path": "C:\\boom"})

    def test_broker_trips_bad_path_before_sending(self):
        from godmode.paths import PathRejected
        with self.assertRaises(PathRejected):
            self.rt.call("fs_read", {"path": "C:\\x:ads"})


class Hardening(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.env = mock.patch.dict(os.environ, {"LOCALAPPDATA": self.tmp, "USERPROFILE": self.tmp,
                                                "APPDATA": os.path.join(self.tmp, "Roaming")})
        self.env.start()
        self.addCleanup(self.env.stop)

    def test_setup_without_venv_keeps_lowil_and_only_grants_own_folders(self):
        granted = []
        st = hardening.sandbox_setup(grant=lambda p, acc: granted.append((str(p), acc)) or "S-1-15-2-1",
                                     build=lambda d: Path(d).mkdir(parents=True, exist_ok=True))
        self.assertTrue(all(str(Path(self.tmp) / "CSpace" / "GodMode") in p for p, _ in granted))
        self.assertIsNone(hardening.tests_in_appcontainer())
        self.assertEqual(st["sid"], "S-1-15-2-1")

    def test_setup_with_venv_switches_tests_to_appcontainer_and_undo_revokes(self):
        sp = hardening.venv_site_packages()
        sp.mkdir(parents=True)

        def build(d):
            Path(d).mkdir(parents=True, exist_ok=True)
            (Path(d) / "python.exe").write_bytes(b"")
        hardening.sandbox_setup(venv=True, grant=lambda p, acc: "S", build=build)
        self.assertEqual(str(hardening.tests_in_appcontainer()[1]), str(sp))
        revoked = []
        hardening.sandbox_undo(revoke=revoked.append)
        self.assertIn(str(sp), [str(x) for x in revoked])
        self.assertIsNone(hardening.tests_in_appcontainer())

    def test_protect_secrets_dry_run_changes_nothing(self):
        (Path(self.tmp) / ".ssh").mkdir()
        labelled = []
        t = hardening.protect_secrets(apply=False, label=lambda p, **k: labelled.append(p))
        self.assertEqual([x.name for x in t], [".ssh"])
        self.assertEqual(labelled, [])

    def test_protect_and_undo(self):
        d = Path(self.tmp) / ".aws"
        d.mkdir()
        (d / "credentials").write_text("x")
        calls = []
        hardening.protect_secrets(apply=True, label=lambda p, no_read_up: calls.append((Path(p).name, no_read_up)))
        hardening.unprotect_secrets(label=lambda p, no_read_up: calls.append((Path(p).name, no_read_up)))
        self.assertEqual(calls, [(".aws", True), (".aws", False), ("credentials", False)])
        self.assertEqual(hardening.load_state()["labelled"], [])

    def test_browser_profiles_never_candidates(self):
        names = " ".join(str(p).lower() for p in hardening.secret_candidates())
        self.assertNotIn("chrome", names)
        self.assertNotIn("user data", names)


class ACArgv(unittest.TestCase):
    def test_script_and_module(self):
        a = testgate.ac_argv(["{venv_python}", "-B", "test_jarvis.py"], "C:\\rt\\python.exe", "C:\\sp")
        self.assertEqual(a[0], "C:\\rt\\python.exe")
        self.assertEqual(a[-2:], ["-B", "test_jarvis.py"])
        self.assertIn("C:\\sp", a)
        ns = {}
        code = a[a.index("-c") + 1]
        compile(code, "boot", "exec")   # valid Python
        self.assertIn("run_module", code)
        self.assertIn("run_path", code)

    def test_run_suite_uses_ac_argv(self):
        seen = {}

        def runner(argv, cwd, env, timeout):
            seen["argv"] = argv
            return 0, "test_jarvis: OK"
        suite = {"name": "s", "cwd": "x", "argv": ["{venv_python}", "-B", "t.py"], "pass": "test_jarvis: OK"}
        testgate.run_suite(suite, tempfile.mkdtemp(), runner, {"venv_python": "C:\\v.exe"}, "C:\\t",
                           appcontainer=("C:\\rt.exe", "C:\\sp"))
        self.assertEqual(seen["argv"][0], "C:\\rt.exe")
        self.assertNotIn("C:\\v.exe", seen["argv"])


class Servers(unittest.TestCase):
    def test_private_ollama_env_and_limits(self):
        s = servers.PrivateOllama(working_set_cap=5 * G, port=40123)
        env = s.env()
        self.assertEqual(env["OLLAMA_HOST"], "127.0.0.1:40123")
        self.assertEqual(env["OLLAMA_NOPRUNE"], "1")
        self.assertEqual(s.limits.working_set_cap, 5 * G)
        self.assertEqual(s.limits.private_commit, 0)
        c = s.client("m")
        self.assertEqual(c.base, "http://127.0.0.1:40123")
        self.assertGreaterEqual(c.timeout, 3600)

    def test_missing_exe(self):
        with self.assertRaises(FileNotFoundError):
            servers.PrivateOllama(G, exe="C:\\nope\\ollama.exe").start()


if __name__ == "__main__":
    unittest.main()
