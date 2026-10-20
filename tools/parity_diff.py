#!/usr/bin/env python3
"""Parity harness: compare the rmsim render of the real skin with a UI screenshot.

  python tools/parity_diff.py REFERENCE.png CANDIDATE.png [--out diff.png] [--threshold 32]

CANDIDATE is resized to REFERENCE's size.  Writes a diff PNG (|a-b| per channel, amplified x4) and prints the
mean absolute difference (0-255, over RGB) and the % of pixels whose max channel difference exceeds the threshold.
Needs Pillow (use ~/.venvs/rmsim/bin/python)."""
import argparse
from PIL import Image, ImageChops


def compare(ref_path, cand_path, out_path, threshold=32):
    ref = Image.open(ref_path).convert("RGB")
    cand = Image.open(cand_path).convert("RGB").resize(ref.size, Image.LANCZOS)
    diff = ImageChops.difference(ref, cand)
    n = ref.width * ref.height
    px = list(diff.getdata())
    mad = sum(sum(p) for p in px) / (3 * n)
    pct = 100.0 * sum(1 for p in px if max(p) > threshold) / n
    diff.point(lambda v: min(255, v * 4)).save(out_path)
    return mad, pct


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("reference")
    ap.add_argument("candidate")
    ap.add_argument("--out", default="parity-diff.png")
    ap.add_argument("--threshold", type=int, default=32)
    a = ap.parse_args()
    mad, pct = compare(a.reference, a.candidate, a.out, a.threshold)
    print(f"mean_abs_diff={mad:.3f} pct_pixels_over_{a.threshold}={pct:.2f} diff={a.out}")


if __name__ == "__main__":
    main()
