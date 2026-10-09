#!/usr/bin/env python3
"""Turn a picture of the cockpit into the Frame's image layer (Settings.inc UseShipImage=1).

The picture should show the same cockpit as the reference (any size and aspect; it is scaled to cover
2560x1600). The windows are cut out along the reference window shapes, with a soft edge, so the
animated wallpaper and the theme-tinted glass show through. A picture that already has transparent
windows (PNG with alpha) keeps its own cut-outs unless --recut is given.

    python tools/image_frame.py my-cockpit.png            # -> @Resources/Images/ship.png
    python tools/image_frame.py my-cockpit.jpg --feather 4 --out ship2.png
    python tools/image_frame.py my-cockpit.png --darken 0.15  # dim the hull a little under the HUD

Then set UseShipImage=1 (and ShipImage=<file> if you used --out), or Control Center > THEME >
COCKPIT ART > PICTURE.
"""
import argparse
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter

import ref_layout as R

ROOT = Path(__file__).resolve().parent.parent
IMAGES = ROOT / "Skins" / "Spaceship" / "@Resources" / "Images"


def cover(im, w, h):
    """scale to cover w x h and centre-crop"""
    k = max(w / im.width, h / im.height)
    im = im.resize((round(im.width * k), round(im.height * k)), Image.LANCZOS)
    x, y = (im.width - w) // 2, (im.height - h) // 2
    return im.crop((x, y, x + w, y + h))


def window_mask(w, h, feather):
    """255 = hull, 0 = glass"""
    m = Image.new("L", (w, h), 255)
    d = ImageDraw.Draw(m)
    sx, sy = w / R.RW, h / R.RH
    for win in R.WINDOWS:
        d.polygon([(x * sx, y * sy) for x, y in win], fill=0)
    for b in (R.BEZEL_L, R.BEZEL_R):
        d.polygon([(x * sx, y * sy) for x, y in b], fill=255)
    if feather > 0:
        m = m.filter(ImageFilter.GaussianBlur(feather))
    return m


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("image", help="cockpit picture (png/jpg/webp)")
    ap.add_argument("--out", default="ship.png", help="file name inside @Resources/Images")
    ap.add_argument("--feather", type=float, default=2.5, help="soft window edge in px")
    ap.add_argument("--recut", action="store_true", help="cut the reference windows even if the picture has alpha")
    ap.add_argument("--darken", type=float, default=0.0, help="0-1, dims the hull so the HUD reads better")
    args = ap.parse_args()

    src = Image.open(args.image)
    has_alpha = src.mode in ("RGBA", "LA") or "transparency" in src.info
    im = cover(src.convert("RGBA"), R.CW, R.CH)
    mask = window_mask(R.CW, R.CH, args.feather)
    if has_alpha and not args.recut:
        alpha = im.split()[3]
        print("keeping the picture's own transparency")
    else:
        alpha = mask if not has_alpha else ImageChops.multiply(im.split()[3], mask)
    if args.darken > 0:
        rgb = ImageEnhance.Brightness(im.convert("RGB")).enhance(1 - min(0.9, args.darken))
        im = rgb.convert("RGBA")
    im.putalpha(alpha)
    IMAGES.mkdir(parents=True, exist_ok=True)
    out = IMAGES / args.out
    im.save(out, optimize=True)
    print(f"wrote {out.relative_to(ROOT)} ({out.stat().st_size / 1e6:.1f} MB). "
          f"Set UseShipImage=1{'' if args.out == 'ship.png' else f' and ShipImage={args.out}'} in Settings.inc.")


if __name__ == "__main__":
    main()
