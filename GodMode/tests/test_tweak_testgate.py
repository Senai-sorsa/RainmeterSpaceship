import os
import tempfile
import unittest
from pathlib import Path

from godmode import testgate as TG
from godmode import tweak as T
from godmode.gate import Violation

J = "Skins/Spaceship/@Resources/Jarvis"
MOOD = f"{J}/jarvislib/mood.py"
SRC = '''import re

LINES = {"happy": "Good to hear.", "sad": "I am sorry."}


def reply(mood, name="sir"):
    """Pick a line."""
    text = LINES.get(mood, "Noted.")
    return f"{text} {name}"


class Tone:
    def level(self, x):
        return x * 2
'''


def surfaces():
    return T.Surfaces.load()


def patch(search, replace, path=MOOD, reason="tune wording"):
    return {"reason": reason, "edits": [{"path": path, "search": search, "replace": replace}]}


def check(p, files=None):
    files = files or {MOOD: SRC}
    return T.check(p, lambda rel: files[rel], surfaces())


class Surfaces(unittest.TestCase):
    def test_protected_always_wins(self):
        s = surfaces()
        for rel in ["GodMode/godmode/tweak.py", f"{J}/test_jarvis.py", f"{J}/jarvislib/actions.py",
                    "SpaceshipApp/ShipCore.Core/ActionGate.cs", ".git/config", "CLAUDE.md", f"{J}/tools/semi_live.py",
                    f"{J}/Setup-Jarvis.ps1", "contract/config-keys.json"]:
            self.assertTrue(T.is_protected(rel, s), rel)
            self.assertFalse(T.is_editable(rel, s), rel)

    def test_editable(self):
        self.assertTrue(T.is_editable(MOOD, surfaces()))
        self.assertTrue(T.is_editable(f"{J}/persona.txt", surfaces()))

    def test_bad_paths_are_violations(self):
        for bad in ["../x.py", "C:/x.py", "/etc/x", f"{J}/../GodMode/x.py", "a//b.py", "a/./b.py", "x.py:ads", "a/b. "]:
            with self.assertRaises(Violation, msg=bad):
                T.clean_rel(bad)

    def test_editing_protected_trips(self):
        with self.assertRaises(Violation):
            check(patch("x", "y", path="GodMode/godmode/gate.py"))
        with self.assertRaises(Violation):
            check(patch("x", "y", path=f"{J}/test_jarvis.py"))
        with self.assertRaises(Violation):
            check(patch("x", "y", path=f"{J}\\jarvislib\\..\\test_jarvis.py"))


class Gate(unittest.TestCase):
    def test_body_tweak_ok(self):
        r = check(patch('"Noted."', '"Understood."'))
        self.assertTrue(r.ok, r.problems)
        self.assertIn("Understood", r.files[MOOD])
        self.assertEqual(r.changed_lines, 2)

    def test_table_value_ok_but_keys_locked(self):
        self.assertTrue(check(patch('"I am sorry."', '"I am sorry to hear that."')).ok)
        r = check(patch('"sad": "I am sorry."', '"sad": "I am sorry.", "angry": "Easy."'))
        self.assertFalse(r.ok)
        self.assertTrue(any("table keys" in p for p in r.problems))

    def test_signature_change_rejected(self):
        r = check(patch('def reply(mood, name="sir"):', 'def reply(mood, name="sir", extra=1):'))
        self.assertFalse(r.ok)

    def test_new_function_rejected(self):
        r = check(patch("class Tone:", "def helper():\n    return 1\n\n\nclass Tone:"))
        self.assertFalse(r.ok)

    def test_method_change_rejected(self):
        self.assertFalse(check(patch("def level(self, x):", "def level(self, x, y=0):")).ok)

    def test_new_import_rejected_even_inside_function(self):
        r = check(patch('    text = LINES.get(mood, "Noted.")', '    import os\n    text = LINES.get(mood, "Noted.")'))
        self.assertFalse(r.ok)

    def test_banned_calls_rejected(self):
        for code in ['open("x", "w").write("y")', 'eval("1")', 'getattr(re, "sub")', '__import__("os")']:
            r = check(patch('    text = LINES.get(mood, "Noted.")', f'    {code}\n    text = LINES.get(mood, "Noted.")'))
            self.assertFalse(r.ok, code)

    def test_words_in_strings_are_fine(self):
        self.assertTrue(check(patch('"Noted."', '"I will open the eval report, sir."')).ok)

    def test_godmode_mentions_rejected(self):
        self.assertFalse(check(patch('"Noted."', '"GOD mode says hi."')).ok)

    def test_syntax_error_rejected(self):
        self.assertFalse(check(patch('return x * 2', 'return x *')).ok)

    def test_search_must_be_unique_and_present(self):
        self.assertFalse(check(patch("nothing like this", "y")).ok)
        files = {MOOD: SRC + "\n# Noted.\n"}
        self.assertFalse(check(patch("Noted.", "Fine."), files).ok)

    def test_size_and_file_caps(self):
        big = '"' + "x" * 7000 + '"'
        self.assertFalse(check(patch('"Noted."', big)).ok)
        p = {"reason": "r", "edits": [{"path": f"{J}/jarvislib/{n}.py", "search": "a", "replace": "b"}
                                      for n in ("mood", "calc", "say", "quiet")]}
        self.assertFalse(T.check(p, lambda rel: "a = 1\n", surfaces()).ok)

    def test_needs_reason_and_edits(self):
        self.assertFalse(check({"edits": []}).ok)
        self.assertFalse(check({"reason": "", "edits": [{"path": MOOD, "search": "a", "replace": "b"}]}).ok)

    def test_text_file(self):
        rel = f"{J}/persona.txt"
        r = T.check(patch("Be brief.", "Be brief and warm.", path=rel), lambda _: "You are Jarvis. Be brief.\n",
                    surfaces())
        self.assertTrue(r.ok, r.problems)


def make_repo():
    root = Path(tempfile.mkdtemp())
    (root / J / "jarvislib").mkdir(parents=True)
    (root / J / "Data").mkdir()
    (root / J / "jarvislib" / "mood.py").write_text(SRC, encoding="utf-8")
    (root / J / "test_jarvis.py").write_text("print('test_jarvis: OK')\n", encoding="utf-8")
    (root / J / "Data" / "private.txt").write_text("secret", encoding="utf-8")
    (root / J / "model.onnx").write_bytes(b"\0" * 10)
    return root


class Copy(unittest.TestCase):
    def test_copy_skips_ignored_and_refuses_existing(self):
        repo = make_repo()
        work = Path(tempfile.mkdtemp()) / "w"
        cfg = TG.load_config()
        n = TG.make_copy(repo, work, cfg["copy"]["subtrees"], cfg["copy"]["ignore"])
        self.assertEqual(n, 2)
        self.assertFalse((work / J / "Data").exists())
        self.assertFalse((work / J / "model.onnx").exists())
        with self.assertRaises(FileExistsError):
            TG.make_copy(repo, work, cfg["copy"]["subtrees"], cfg["copy"]["ignore"])

    def test_manifest_covers_tests(self):
        repo = make_repo()
        m = TG.protected_manifest(repo, surfaces())
        self.assertIn(f"{J}/test_jarvis.py", m)
        self.assertNotIn(MOOD, m)

    def test_write_files_refuses_escape(self):
        with self.assertRaises(Violation):
            TG.write_files(tempfile.mkdtemp(), {"../x.py": "y"})


def ok_runner(argv, cwd, env, timeout):
    return 0, "...\ntest_jarvis: OK\n"


class Judge(unittest.TestCase):
    def run_gate(self, runner, p=None):
        repo = make_repo()
        work = Path(tempfile.mkdtemp()) / "w"
        return TG.run_gate(repo, work, p or patch('"Noted."', '"Understood."'), runner, tempfile.mkdtemp(),
                           {"venv_python": "C:\\py.exe"})

    def test_pass(self):
        res, rep = self.run_gate(ok_runner)
        self.assertTrue(rep.ok, rep.reasons)
        self.assertEqual(len(rep.baseline), 1)

    def test_runner_gets_temp_and_no_proxy_env(self):
        seen = {}

        def r(argv, cwd, env, timeout):
            seen.update(env=env, argv=argv, cwd=cwd)
            return ok_runner(argv, cwd, env, timeout)
        self.run_gate(r)
        self.assertEqual(seen["argv"][0], "C:\\py.exe")
        self.assertIn("TEMP", seen["env"])
        self.assertEqual(seen["env"]["TZ"], "ABC+12")
        self.assertTrue(seen["cwd"].replace("\\", "/").endswith(J))

    def test_failing_after_patch_rejected(self):
        calls = []

        def r(argv, cwd, env, timeout):
            calls.append(1)
            return (0, "test_jarvis: OK") if len(calls) == 1 else (1, "AssertionError")
        self.assertFalse(self.run_gate(r)[1].ok)

    def test_baseline_failure_blocks_everything(self):
        self.assertFalse(self.run_gate(lambda *a, **k: (1, "boom"))[1].ok)

    def test_exit_zero_without_pass_line_rejected(self):
        self.assertFalse(self.run_gate(lambda *a, **k: (0, "nothing"))[1].ok)

    def test_tampering_with_tests_during_run_detected(self):
        def r(argv, cwd, env, timeout):
            Path(cwd, "test_jarvis.py").write_text("print('test_jarvis: OK')  # weakened\n", encoding="utf-8")
            return 0, "test_jarvis: OK"
        rep = self.run_gate(r)[1]
        self.assertFalse(rep.ok)
        self.assertTrue(any("protected" in x for x in rep.reasons))

    def test_static_rejection_skips_tests(self):
        calls = []
        res, rep = self.run_gate(lambda *a, **k: calls.append(1) or (0, "test_jarvis: OK"),
                                 patch('def reply(mood, name="sir"):', 'def reply(mood):'))
        self.assertFalse(rep.ok)
        self.assertEqual(calls, [])

    def test_count_drop_rejected(self):
        b = TG.SuiteRun("s", 0, True, 10, 1, "")
        p = TG.SuiteRun("s", 0, True, 9, 1, "")
        self.assertFalse(TG.judge([b], [p], {}, {}).ok)


if __name__ == "__main__":
    unittest.main()
