"""Tests for tools/shade_pic.py's freshness logic: pure file/hash work, no numpy, Pillow or OS actions. Run: py -3 tools/test_shade_pic.py"""
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import shade_pic as SP


class Freshness(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        self.src, self.out, self.stamp = self.dir / "mask.png", self.dir / "shade_pic.png", self.dir / "shade_pic.src.sha256"
        self.src.write_bytes(b"mask-v1")

    def test_missing_output_is_stale(self):
        self.assertTrue(SP.is_stale(self.src, self.out, self.stamp))

    def test_matching_stamp_is_fresh(self):
        self.out.write_bytes(b"shade")
        SP.write_stamp(self.src, self.stamp)
        self.assertFalse(SP.is_stale(self.src, self.out, self.stamp))

    def test_changed_mask_makes_it_stale(self):
        self.out.write_bytes(b"shade")
        SP.write_stamp(self.src, self.stamp)
        self.src.write_bytes(b"mask-v2")
        self.assertTrue(SP.is_stale(self.src, self.out, self.stamp))

    def test_missing_stamp_is_stale(self):
        self.out.write_bytes(b"shade")
        self.assertTrue(SP.is_stale(self.src, self.out, self.stamp))

    def test_check_mode_reports_stale_without_writing(self):
        self.out.write_bytes(b"shade")
        before = self.out.read_bytes()
        self.assertEqual(SP.run(["--check"], self.src, self.out, self.stamp), 1)
        self.assertEqual(self.out.read_bytes(), before)
        self.assertFalse(self.stamp.exists())

    def test_if_stale_leaves_a_fresh_output_alone(self):
        self.out.write_bytes(b"shade")
        SP.write_stamp(self.src, self.stamp)
        self.assertEqual(SP.run(["--if-stale"], self.src, self.out, self.stamp), 0)
        self.assertEqual(self.out.read_bytes(), b"shade")


if __name__ == "__main__":
    unittest.main()
