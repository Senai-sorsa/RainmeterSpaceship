#!/usr/bin/env python3
"""Parity harness: compare the rmsim render of the real skin with a UI screenshot.

  python tools/parity_diff.py REFERENCE.png CANDIDATE.png [--out diff.png] [--threshold 32] [--size WxH]

Both images are resized to --size (default: REFERENCE's size) before comparing; the sizes are printed.  Writes a diff PNG (|a-b| per channel, amplified x4) and prints the
mean absolute difference (0-255, over RGB) and the % of pixels whose max channel difference exceeds the threshold.
Needs Pillow (use ~/.venvs/rmsim/bin/python)."""
import argparse
from PIL import Image, ImageChops, ImageStat


def compare(ref_path, cand_path, out_path, threshold=32, size=None):
    ref = Image.open(ref_path).convert("RGB")
    cand = Image.open(cand_path).convert("RGB")
    print(f"compared sizes: reference={ref.size} candidate={cand.size} -> {size or ref.size}")
    size = size or ref.size
    ref, cand = (i if i.size == size else i.resize(size, Image.LANCZOS) for i in (ref, cand))
    diff = ImageChops.difference(ref, cand)
    n = ref.width * ref.height
    mad = sum(ImageStat.Stat(diff).sum) / (3 * n)
    over = ImageChops.lighter(ImageChops.lighter(*diff.split()[:2]), diff.split()[2])  # per-pixel max channel
    pct = 100.0 * sum(over.point(lambda v: 255 if v > threshold else 0).histogram()[255:]) / n
    diff.point(lambda v: min(255, v * 4)).save(out_path)
    return mad, pct


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("reference")
    ap.add_argument("candidate")
    ap.add_argument("--out", default="parity-diff.png")
    ap.add_argument("--threshold", type=int, default=32)
    ap.add_argument("--size", help="WxH to resize both images to (default: reference size)")
    a = ap.parse_args()
    size = tuple(int(v) for v in a.size.lower().split("x")) if a.size else None
    assert size is None or (len(size) == 2 and min(size) > 0), "--size must be WxH"
    mad, pct = compare(a.reference, a.candidate, a.out, a.threshold, size)
    print(f"mean_abs_diff={mad:.3f} pct_pixels_over_{a.threshold}={pct:.2f} diff={a.out}")


if __name__ == "__main__":
    main()
