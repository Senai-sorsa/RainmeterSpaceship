#!/usr/bin/env python3
"""CSpace's picture-frame shade: the skin's shade.png, made for the PICTURE's windows.

shade.png (tools/frame_render.shade_png) is made from the rendered hull's windows, whose side windows are split by a diagonal strut.
The picture's side windows are one pane, so over the picture shade.png left an unshaded diagonal band across each side window
(task 13, measured ~170 px tall at 1707x1067). This runs the same shade_png() with the picture's own glass, window_mask_pic.png
(written by tools/image_frame.py), the way image_frame.py makes glass_fx_pic / scan_pic.

Writes SpaceshipApp/SpaceshipUI/src/assets/shade_pic.png (a CSpace-only asset; the skin's Images/ are not touched) and
shade_pic.src.sha256 next to it: the hash of the window mask it was made from, so a changed picture is noticed.

It stays up to date by itself:
  * tools/image_frame.py calls run([]) after it writes a new picture's window mask;
  * `npm run gen` / `npm run build` (SpaceshipUI) run it with --if-stale: it rebuilds only when the mask changed;
  * `npm test` runs it with --check: exit 1 and a message when the shade is out of date (never writes).
By hand:  py -3 tools/shade_pic.py   (needs numpy and Pillow, as frame_render.py does; they are only imported when it must rebuild)
"""
import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "Skins" / "Spaceship" / "@Resources" / "Images" / "window_mask_pic.png"
OUT = ROOT / "SpaceshipApp" / "SpaceshipUI" / "src" / "assets" / "shade_pic.png"
STAMP = OUT.with_name("shade_pic.src.sha256")


def digest(src: Path) -> str:
    return hashlib.sha256(src.read_bytes()).hexdigest()


def is_stale(src: Path, out: Path, stamp: Path) -> bool:
    """The shade needs rebuilding: it is missing, or the mask it was made from is not the current one."""
    if not out.exists() or not stamp.exists():
        return True
    return stamp.read_text(encoding="ascii").strip() != digest(src)


def write_stamp(src: Path, stamp: Path) -> None:
    stamp.write_text(digest(src) + "\n", encoding="ascii")


def build(src: Path, out: Path) -> None:
    import numpy as np          # only when rebuilding
    from PIL import Image
    import frame_render as FR   # sibling module: run this file without -I
    glass = np.asarray(Image.open(src).convert("L"), dtype=np.float32) / 255
    if glass.shape != (FR.CH, FR.CW):
        raise SystemExit(f"{src.name} is {glass.shape[1]}x{glass.shape[0]}, expected {FR.CW}x{FR.CH}")
    FR.shade_png(glass).save(out, optimize=True)


def run(argv, src: Path = SRC, out: Path = OUT, stamp: Path = STAMP) -> int:
    """No flag: rebuild. --if-stale: rebuild only when needed. --check: report only, exit 1 when out of date."""
    check, only_stale = "--check" in argv, "--if-stale" in argv
    stale = is_stale(src, out, stamp)
    if check:
        if stale:
            print(f"shade_pic.png is out of date with {src.name}: run  py -3 tools/shade_pic.py", file=sys.stderr)
        return 1 if stale else 0
    if only_stale and not stale:
        return 0
    build(src, out)
    write_stamp(src, stamp)
    print(f"wrote {out.relative_to(ROOT) if out.is_relative_to(ROOT) else out} ({out.stat().st_size / 1e6:.2f} MB)")
    return 0


if __name__ == "__main__":
    sys.exit(run(sys.argv[1:]))
