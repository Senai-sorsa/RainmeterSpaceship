"""Run: python3 -I tools/test_contract_check.py   (reads files only; touches nothing else)"""
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # -I removes the script folder
import contract_check as cc  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load(*p):
    with open(os.path.join(ROOT, *p), encoding="utf-8") as f:
        return json.load(f)


class Fixtures(unittest.TestCase):
    def test_every_fixture_gets_its_declared_verdict(self):
        actions = load("contract", "config-keys.json")["actions"]
        fx = load("contract", "fixtures", "ui-to-host.json")
        wrong = [f["name"] for f in fx if (cc.problem(f["msg"], actions) is None) != f["valid"]]
        self.assertEqual(wrong, [])
        self.assertGreater(len(fx), 40)

    def test_keys_file_is_sane(self):
        keys = load("contract", "config-keys.json")["keys"]
        names = [k["key"] for k in keys]
        self.assertEqual(len(names), len(set(names)))
        self.assertTrue(all(cc.KEY.match(n) for n in names))
        self.assertNotIn("JarvisPython", names)  # executable paths are never writable from the page
        self.assertNotIn("LltPath", names)


if __name__ == "__main__":
    unittest.main()
