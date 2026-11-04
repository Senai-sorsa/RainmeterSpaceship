import json
import tempfile
import unittest
from pathlib import Path

from godmode import audit, gate, paths, profiles


class FakeFacts:
    def __init__(self, attrs=None, default=0x10):
        self.attrs = {k.lower(): v for k, v in (attrs or {}).items()}
        self.default = default

    def attributes(self, p):
        return self.attrs.get(p.lower(), self.default)

    def exists(self, p):
        return True


class Canonical(unittest.TestCase):
    def test_rejects_tricks(self):
        for bad in ["", "relative\\x.txt", "\\\\server\\share\\x", "\\\\?\\C:\\x", "\\\\.\\PhysicalDrive0",
                    "C:\\a\\..\\b", "C:\\a\\.\\b", "C:\\x.txt:evil", "C:\\dir\\CON", "C:\\dir\\nul.txt",
                    "C:\\dir\\name.", "C:\\dir\\name ", "C:\\PROGRA~1\\x", "C:\\a\\*.txt", "C:\\a\x00b"]:
            with self.assertRaises(paths.PathRejected, msg=bad):
                paths.canonical(bad)

    def test_accepts_and_normalises(self):
        self.assertEqual(paths.canonical("C:/Users/Senai/notes.md"), "C:\\Users\\Senai\\notes.md")


class Policy(unittest.TestCase):
    def setUp(self):
        self.pol = paths.PathPolicy(FakeFacts({"C:\\Users\\Senai\\link": 0x410, "C:\\Users\\Senai\\cloud": 0x400010}))

    def test_ok(self):
        self.assertTrue(self.pol.check_read("C:\\Users\\Senai\\doc.txt").ok)

    def test_secrets_blocked_case_insensitive_not_violation(self):
        for p in ["C:\\Users\\Senai\\.SSH\\id_rsa", "C:\\x\\Google\\Chrome\\User Data\\Default\\Login Data",
                  "C:\\proj\\.env", "C:\\proj\\.env.local", "C:\\x\\db.KDBX", "C:\\x\\server.pem"]:
            v = self.pol.check_read(p)
            self.assertFalse(v.ok, p)
            self.assertTrue(v.privacy, p)

    def test_cloud_drive_excluded(self):
        self.assertFalse(self.pol.check_read("G:\\My Drive\\a.zip").ok)

    def test_reparse_anywhere_on_path_refused(self):
        v = self.pol.check_read("C:\\Users\\Senai\\link\\inner\\file.txt")
        self.assertFalse(v.ok)
        self.assertIn("link", v.reason)

    def test_placeholder_refused(self):
        self.assertFalse(self.pol.check_read("C:\\Users\\Senai\\cloud\\big.iso").ok)

    def test_extra_denied(self):
        pol = paths.PathPolicy(FakeFacts(), extra_denied=["C:\\Users\\Senai\\AppData\\Local\\CSpace"])
        self.assertFalse(pol.check_read("C:\\Users\\Senai\\AppData\\Local\\CSpace\\GodMode\\audit.jsonl").ok)


class Gate(unittest.TestCase):
    def test_matrix(self):
        for mode, allowed in gate.TOOLS_BY_MODE.items():
            g = gate.ModeGate(mode, "ultron" if mode == "ultron" else "advanced")
            for tool in gate.READ_TOOLS | {"apply_patch", "shell", "write_file"}:
                if tool in allowed:
                    g.check(tool, {})
                else:
                    with self.assertRaises(gate.Violation):
                        g.check(tool, {})

    def test_ultron_is_locked(self):
        with self.assertRaises(ValueError):
            gate.ModeGate("read", "ultron")
        with self.assertRaises(ValueError):
            gate.ModeGate("ultron", "advanced")
        self.assertEqual(gate.ModeGate("ultron", "ultron").tools, frozenset())

    def test_bad_args(self):
        with self.assertRaises(gate.Violation):
            gate.ModeGate("read", "advanced").check("fs_read", "C:\\x")

    def test_ultron_profile_never_has_tools(self):
        d = tempfile.mkdtemp()
        p = Path(d) / "m.json"
        p.write_text(json.dumps({"slots": {"ultron": {"display": "U", "runtime": "ollama", "model": "m",
                     "file_bytes": 1, "expert_bytes": 0, "n_layers": 1, "kv_bytes_per_token": 1,
                     "ctx_default": 2, "ctx_min": 1, "tools": True}}}))
        self.assertFalse(profiles.load(p)["ultron"].tools)

    def test_shipped_profiles_load(self):
        pr = profiles.load()
        self.assertEqual(set(pr), {"advanced", "ascendent", "ultron"})
        self.assertFalse(pr["ultron"].tools)


class Audit(unittest.TestCase):
    def setUp(self):
        self.p = Path(tempfile.mkdtemp()) / "a.jsonl"
        self.log = audit.AuditLog(self.p, clock=lambda: 1.0)
        for i in range(4):
            self.log.write("e", i=i)

    def test_verifies(self):
        self.assertTrue(self.log.verify(anchor=self.log.head())[0])

    def test_edit_detected(self):
        lines = self.p.read_text(encoding="utf-8").splitlines()
        lines[1] = lines[1].replace('"i": 1', '"i": 9')
        self.p.write_text("\n".join(lines) + "\n", encoding="utf-8")
        self.assertFalse(self.log.verify()[0])

    def test_removed_line_detected(self):
        lines = self.p.read_text(encoding="utf-8").splitlines()
        del lines[1]
        self.p.write_text("\n".join(lines) + "\n", encoding="utf-8")
        self.assertFalse(self.log.verify()[0])

    def test_truncation_detected_with_anchor(self):
        anchor = self.log.head()
        lines = self.p.read_text(encoding="utf-8").splitlines()[:-1]
        self.p.write_text("\n".join(lines) + "\n", encoding="utf-8")
        self.assertTrue(self.log.verify()[0])            # chain itself still fine...
        self.assertFalse(self.log.verify(anchor)[0])     # ...but the anchor catches it


if __name__ == "__main__":
    unittest.main()
