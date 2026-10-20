#!/usr/bin/env python3
"""Turn a picture of the cockpit into the Frame's image layer (Settings.inc UseShipImage=1).

The picture should show the same cockpit as the reference (any size and aspect; it is scaled to cover
2560x1600). The windows are cut out along the reference window shapes, with a soft edge, so the
animated wallpaper and the theme-tinted glass show through. A picture that already has transparent
windows (PNG with alpha) keeps its own cut-outs unless --recut is given.

    python tools/image_frame.py art/cockpit-picture-source.png   # -> @Resources/Images/ship.png (+ *_pic.png layers)
    python tools/image_frame.py my-cockpit.png            # -> @Resources/Images/ship.png
    python tools/image_frame.py my-cockpit.jpg --feather 4 --out ship2.png
    python tools/image_frame.py my-cockpit.png --darken 0.15  # dim the hull a little under the HUD

A picture's own alpha is cleaned first (--clean-alpha LO,HI: faint haze in the windows becomes fully clear,
near-opaque hull becomes opaque). Its glass is then also written as window_mask_pic.png, glass_pic.png,
glass_fx_pic.png, scan_pic.png and mist_pic.png (the Frame's picture-mode glass layers, so tint, glare,
scanlines and mist follow the picture's windows, not the reference windows). art/cockpit-picture-source.png
is the original picture these were made from.

Then set UseShipImage=1 (and ShipImage=<file> if you used --out), or Control Center > THEME >
COCKPIT ART > PICTURE.
"""
import argparse
from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter

import frame_render as FR
import ref_layout as R

ROOT = Path(__file__).resolve().parent.parent
IMAGES = ROOT / "Skins" / "Spaceship" / "@Resources" / "Images"


def cover(im, w, h):
    """scale to cover w x h and centre-crop"""
    k = max(w / im.width, h / im.height)
    im = im.resize((round(im.width * k), round(im.height * k)), Image.LANCZOS)
    x, y = (im.width - w) // 2, (im.height - h) // 2
    return im.crop((x, y, x + w, y + h))


def stretch(im, w, h):
    return im.resize((w, h), Image.LANCZOS)


def clean_alpha(a, lo=64, hi=200):
    """uint8 alpha: <=lo -> 0, >=hi -> 255, linear ramp between (removes faint haze, closes near-opaque hull)"""
    a = np.asarray(a, dtype=np.float32)
    return (np.clip((a - lo) / max(1, hi - lo), 0, 1) * 255 + 0.5).astype(np.uint8)


def drop_specks(glass, min_px):
    """glass: bool array. Returns a copy without 4-connected components smaller than min_px
    (they become hull). Returns (cleaned, [kept sizes], [dropped sizes])."""
    h, w = glass.shape
    seen = np.zeros(glass.size, bool)
    flat = glass.ravel()
    out = np.zeros(glass.size, bool)
    kept, dropped = [], []
    for start in np.flatnonzero(flat):
        if seen[start]:
            continue
        seen[start] = True
        comp, q = [start], deque([start])
        while q:
            i = q.popleft()
            x = i % w
            for j in ((i - 1) if x else -1, (i + 1) if x < w - 1 else -1, i - w, i + w):
                if 0 <= j < flat.size and flat[j] and not seen[j]:
                    seen[j] = True
                    comp.append(j)
                    q.append(j)
        if len(comp) >= min_px:
            out[comp] = True
            kept.append(len(comp))
        else:
            dropped.append(len(comp))
    return out.reshape(h, w), kept, dropped


def components(glass):
    """list of (bbox y0,y1,x0,x1, bool mask slice) per connected glass area (for the live-tint gradient)"""
    h, w = glass.shape
    lab = np.zeros(glass.shape, np.int32)
    n = 0
    flat = glass.ravel()
    labf = lab.ravel()
    for start in np.flatnonzero(flat):
        if labf[start]:
            continue
        n += 1
        labf[start] = n
        q = deque([start])
        while q:
            i = q.popleft()
            x = i % w
            for j in ((i - 1) if x else -1, (i + 1) if x < w - 1 else -1, i - w, i + w):
                if 0 <= j < flat.size and flat[j] and not labf[j]:
                    labf[j] = n
                    q.append(j)
    return lab, n


def glass_layers(alpha, feather, min_px, out_dir):
    """picture-mode glass layers from the CLEANED picture alpha (glass = fully clear area)"""
    glass, kept, dropped = drop_specks(np.asarray(alpha) < 128, min_px)
    print(f"glass areas kept: {len(kept)} (px {sorted(kept, reverse=True)[:8]}), specks treated as hull: {len(dropped)}")
    m = Image.fromarray(glass.astype(np.uint8) * 255, "L")
    if feather > 0:
        m = m.filter(ImageFilter.GaussianBlur(feather))
    mf = np.asarray(m, dtype=np.float32) / 255
    # live tint: white, alpha = mask * the Glass.inc vertical gradient (0.75 -> 0.12 -> 0.3 over each window),
    # so ImageTint=#ColorAccent# + ImageAlpha=#GlassTint# gives the same look as the reference windows
    lab, n = components(glass)
    grad = np.ones(glass.shape, np.float32)
    for k in range(1, n + 1):
        ys, xs = np.nonzero(lab == k)
        t = (ys - ys.min()) / max(1, ys.max() - ys.min())
        grad[ys, xs] = np.interp(t, [0, 0.55, 1], [0.75, 0.12, 0.3])
    white = np.full(glass.shape + (3,), 255, np.uint8)
    layers = {
        "window_mask_pic.png": m,
        "glass_pic.png": Image.fromarray(np.dstack([white, (mf * grad * 255 + 0.5).astype(np.uint8)]), "RGBA"),
        "glass_fx_pic.png": FR.glass_fx_png(mf),
        "scan_pic.png": FR.scan_png(mf),
        # edge lines like the reference mist (4px lines around the windows)
        "mist_pic.png": FR.mist_png(ImageChops.subtract(m.point(lambda v: 255 if v > 127 else 0).filter(ImageFilter.MaxFilter(5)),
                                                         m.point(lambda v: 255 if v > 127 else 0).filter(ImageFilter.MinFilter(5)))),
    }
    for name, img in layers.items():
        img.save(out_dir / name, optimize=True)
        print(f"wrote {name} ({(out_dir / name).stat().st_size / 1e6:.2f} MB)")


def window_mask(w, h, feather):
    """255 = hull, 0 = glass"""
    m = Image.new("L", (w, h), 255)
    d = ImageDraw.Draw(m)
    sx, sy = w / R.RW, h / R.RH
    for win in R.WINDOWS:
        d.polygon([(x * sx, y * sy) for x, y in win], fill=0)
    for b in R.BEZELS:
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
    ap.add_argument("--clean-alpha", default="64,200", metavar="LO,HI",
                    help="picture's own alpha: <=LO -> 0, >=HI -> 255, ramp between (default 64,200)")
    ap.add_argument("--fit", choices=("cover", "stretch"), default="cover", help="cover = scale+centre-crop, stretch = distort to 2560x1600")
    ap.add_argument("--min-glass", type=int, default=500, help="glass areas smaller than this many px (at 2560x1600) are hull")
    ap.add_argument("--darken", type=float, default=0.0, help="0-1, dims the hull so the HUD reads better")
    args = ap.parse_args()

    src = Image.open(args.image)
    has_alpha = src.mode in ("RGBA", "LA") or "transparency" in src.info
    lo, hi = (int(v) for v in args.clean_alpha.split(","))
    src = src.convert("RGBA")
    if has_alpha:                    # clean the haze before scaling; resize premultiplied so no halo from the clear pixels
        a = Image.fromarray(clean_alpha(src.split()[3], lo, hi), "L")
        src.putalpha(a)
    fit = cover if args.fit == "cover" else stretch
    im = fit(src.convert("RGBa"), R.CW, R.CH).convert("RGBA")
    mask = window_mask(R.CW, R.CH, args.feather)
    if has_alpha and not args.recut:
        alpha = np.asarray(im.split()[3])
        alpha = Image.fromarray(clean_alpha(alpha, 8, 247), "L")   # tidy resampling ringing only
        print("keeping the picture's own transparency")
    else:
        alpha = mask if not has_alpha else ImageChops.multiply(im.split()[3], mask)
    if args.darken > 0:
        rgb = ImageEnhance.Brightness(im.convert("RGB")).enhance(1 - min(0.9, args.darken))
        im = rgb.convert("RGBA")
    if has_alpha and not args.recut:
        rgb = np.asarray(im.convert("RGB")).copy()
        rgb[np.asarray(alpha) == 0] = 0         # clear pixels carry no colour (smaller file)
        im = Image.fromarray(rgb, "RGB").convert("RGBA")
    im.putalpha(alpha)
    IMAGES.mkdir(parents=True, exist_ok=True)
    out = IMAGES / args.out
    im.save(out, optimize=True)
    if has_alpha and not args.recut:
        glass_layers(alpha, 2.0, args.min_glass, IMAGES)
    print(f"wrote {out.relative_to(ROOT)} ({out.stat().st_size / 1e6:.1f} MB). "
          f"Set UseShipImage=1{'' if args.out == 'ship.png' else f' and ShipImage={args.out}'} in Settings.inc.")


if __name__ == "__main__":
    main()
