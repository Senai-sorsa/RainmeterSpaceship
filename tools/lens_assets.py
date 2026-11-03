"""Lens textures for the HUD's glass and grain (tasks/hyperrealism-plan.md Task 5). Deterministic; numpy only.

  bluenoise.png  128x128 grey ranking (void-and-cluster): grain/dither that has no visible low-frequency clumps
  dirt.png       640x400 white with alpha = smudges and wipe streaks: multiplied into the light canvas, so the smudges
                 only show where the HUD is bright (a lens-dirt mask)

Run:  py -3 -I tools/lens_assets.py [--check]      (writes only the two PNGs below; --check compares, writes nothing)"""
import struct
import sys
import zlib
from pathlib import Path

import numpy as np

OUT = Path(__file__).resolve().parent.parent / "SpaceshipApp" / "SpaceshipUI" / "src" / "assets" / "lens"


def _kernel(n, sigma):
    """Toroidal Gaussian energy kernel centred on (0, 0)."""
    d = np.minimum(np.arange(n), n - np.arange(n)).astype(float)
    return np.exp(-(d[:, None] ** 2 + d[None, :] ** 2) / (2 * sigma * sigma))


def blue_noise(n=128, sigma=1.5, seed=7):
    """Void-and-cluster ranking (Ulichney 1993, simplified: phases 2 and 3 both fill the largest void)."""
    rng = np.random.default_rng(seed)
    k = _kernel(n, sigma)
    ones = np.zeros((n, n), bool)
    ones.flat[rng.choice(n * n, n * n // 10, replace=False)] = True

    def energy(mask):
        return np.real(np.fft.ifft2(np.fft.fft2(mask.astype(float)) * np.fft.fft2(k)))

    def shifted(y, x):
        return np.roll(np.roll(k, y, 0), x, 1)

    e = energy(ones)
    while True:  # relax: move the tightest cluster into the largest void until that is a no-op
        c = np.unravel_index(np.argmax(np.where(ones, e, -np.inf)), e.shape)
        ones[c] = False
        e -= shifted(*c)
        v = np.unravel_index(np.argmin(np.where(ones, np.inf, e)), e.shape)
        ones[v] = True
        e += shifted(*v)
        if v == c:
            break
    rank = np.zeros((n, n), int)
    start = ones.copy()
    m, em, r = ones.copy(), e.copy(), int(ones.sum())
    while r > 0:  # phase 1: rank the initial points by removing the tightest cluster
        c = np.unravel_index(np.argmax(np.where(m, em, -np.inf)), em.shape)
        m[c] = False
        em -= shifted(*c)
        r -= 1
        rank[c] = r
    m, em, r = start, e, int(start.sum())
    while r < n * n:  # phases 2-3: fill the largest void
        v = np.unravel_index(np.argmin(np.where(m, np.inf, em)), em.shape)
        m[v] = True
        em += shifted(*v)
        rank[v] = r
        r += 1
    return (rank * 256 // (n * n)).astype(np.uint8)


def _blur(a, sigma):
    r = int(3 * sigma) + 1
    x = np.arange(-r, r + 1)
    g = np.exp(-x * x / (2 * sigma * sigma))
    g /= g.sum()
    a = np.apply_along_axis(lambda v: np.convolve(v, g, "same"), 0, a)
    return np.apply_along_axis(lambda v: np.convolve(v, g, "same"), 1, a)


def dirt(w=640, h=400, seed=11):
    """Soft round smudges (radius 6-40 px, alpha 20-90) plus faint long wipe streaks at 8-14 degrees."""
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:h, 0:w].astype(float)
    a = np.zeros((h, w))
    for _ in range(60):
        cx, cy, r, al = rng.uniform(0, w), rng.uniform(0, h), rng.uniform(6, 40), rng.uniform(20, 90)
        a = np.maximum(a, al * np.exp(-((xx - cx) ** 2 + (yy - cy) ** 2) / (2 * (r / 2) ** 2)))
    for _ in range(6):
        ang = np.radians(rng.uniform(8, 14) * rng.choice([-1, 1]))
        cx, cy, wid, al = rng.uniform(0, w), rng.uniform(0, h), rng.uniform(3, 9), rng.uniform(14, 30)
        dist = np.abs(-(xx - cx) * np.sin(ang) + (yy - cy) * np.cos(ang))
        along = (xx - cx) * np.cos(ang) + (yy - cy) * np.sin(ang)
        a = np.maximum(a, al * np.exp(-dist ** 2 / (2 * wid * wid)) * np.exp(-along ** 2 / (2 * 160.0 ** 2)))
    return np.clip(_blur(a, 1.5), 0, 255).round().astype(np.uint8)


def png_bytes(img):
    """8-bit grey (h, w) or RGBA (h, w, 4) to PNG bytes."""
    img = np.ascontiguousarray(img, np.uint8)
    h, w = img.shape[:2]
    ctype = 0 if img.ndim == 2 else 6
    raw = b"".join(b"\x00" + img[y].tobytes() for y in range(h))

    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, ctype, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


def write_png(path, img):
    Path(path).write_bytes(png_bytes(img))


def outputs():
    d = dirt()
    rgba = np.dstack([np.full_like(d, 255)] * 3 + [d])
    return {OUT / "bluenoise.png": png_bytes(blue_noise()), OUT / "dirt.png": png_bytes(rgba)}


def main(argv):
    check = "--check" in argv
    bad = 0
    for p, b in outputs().items():
        if check:
            if not p.exists() or p.read_bytes() != b:
                print("%s: out of date" % p.name)
                bad = 1
        else:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(b)
            print("%s: %d bytes" % (p.name, len(b)))
    return bad


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
