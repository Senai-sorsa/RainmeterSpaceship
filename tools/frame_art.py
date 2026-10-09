#!/usr/bin/env python3
"""Render the cockpit frame ("the ship") from layout/layout.json.

Output: Skins/Spaceship/@Resources/Images/frame.png (2560x1600 RGBA).
Glass areas are fully transparent so the animated wallpaper shows through;
the hull (bezel, header console, A-pillars, beams, dashboard) is opaque.
Decor from the layout (dividers, rails, glyphs, dash screens) and the screen
recesses for dash widgets are baked in, so they always match the layout.

Usage: python tools/frame_art.py [--preview preview.png]
"""
import argparse
import math
import random

from PIL import Image, ImageChops, ImageDraw, ImageFilter

from layoutlib import ROOT, by_id, load, shape

OUT = ROOT / "Skins" / "Spaceship" / "@Resources" / "Images" / "frame.png"
SS = 2  # supersampling factor

CYAN = (0, 210, 255)
HULL_TOP = (34, 43, 57)
HULL_BOT = (13, 17, 25)


def S(pts):
    return [(x * SS, y * SS) for x, y in pts]


def header_poly(fr, canvas_w):
    h = fr["header"]
    pts = [(h["x0"] - 18, h["top"]), (h["x1"] + 18, h["top"])]
    steps = 48
    for i in range(steps + 1):
        x = h["x1"] - (h["x1"] - h["x0"]) * i / steps
        u = (x - canvas_w / 2) / ((h["x1"] - h["x0"]) / 2)
        pts.append((x, h["base_y"] + (h["edge_y"] - h["base_y"]) * u * u))
    return pts


def header_edge(fr, canvas_w):
    return header_poly(fr, canvas_w)[2:]


def vertical_gradient(size, top, bot):
    w, h = size
    col = Image.new("RGB", (1, h))
    for y in range(h):
        t = y / max(1, h - 1)
        col.putpixel((0, y), tuple(int(top[i] + (bot[i] - top[i]) * t) for i in range(3)))
    return col.resize((w, h))


def glow_line(layer, pts, color, width, glow, alpha=255, closed=False):
    """Draw a neon line: blurred wide pass + sharp core."""
    g = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(g)
    seq = pts + [pts[0]] if closed else pts
    d.line(S(seq), fill=color + (int(alpha * 0.55),), width=int(width * SS * 3), joint="curve")
    g = g.filter(ImageFilter.GaussianBlur(glow * SS))
    layer.alpha_composite(g)
    d = ImageDraw.Draw(layer)
    d.line(S(seq), fill=color + (alpha,), width=max(1, int(width * SS)), joint="curve")


def offset_poly(poly, pad):
    cx = sum(p[0] for p in poly) / len(poly)
    cy = sum(p[1] for p in poly) / len(poly)
    out = []
    for x, y in poly:
        dx, dy = x - cx, y - cy
        n = math.hypot(dx, dy) or 1
        out.append((x + dx / n * pad * 1.2, y + dy / n * pad))
    return out


def build(layout):
    W, H = layout["canvas"]["w"], layout["canvas"]["h"]
    fr, curves = layout["frame"], layout["curves"]
    ids = by_id(layout)
    size = (W * SS, H * SS)
    rnd = random.Random(7)

    # ---- hull mask -------------------------------------------------------
    mask = Image.new("L", size, 0)
    md = ImageDraw.Draw(mask)
    md.rectangle([0, 0, size[0], size[1]], fill=255)
    inset, r = 22, layout["safe_area"]["corner_radius"]
    md.rounded_rectangle([inset * SS, inset * SS, (W - inset) * SS, (H - inset) * SS], radius=r * SS, fill=0)
    md.polygon(S(header_poly(fr, W)), fill=255)
    md.polygon(S([(1000, 250), (1560, 250), (1500, 292), (1060, 292)]), fill=255)
    for k in layout["keepouts"]:
        md.polygon(S(k["poly"]), fill=255)
    md.polygon(S(fr["dash"]["poly"]), fill=255)
    # heavier top corners, like the reference canopy
    for sx in (1, -1):
        x0 = 0 if sx == 1 else W
        pts = [(x0, 0), (x0 + sx * 300, 0), (x0 + sx * 230, 22), (x0 + sx * 120, 60), (x0 + sx * 46, 150), (x0 + sx * 22, 300), (x0, 340)]
        md.polygon(S(pts), fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(0.6 * SS)).point(lambda v: 255 if v > 127 else 0)

    # ---- hull surface ----------------------------------------------------
    hull = vertical_gradient(size, HULL_TOP, HULL_BOT).convert("RGBA")
    noise = Image.effect_noise(size, 18).convert("L").point(lambda v: int((v - 128) * 0.18 + 128))
    hull = Image.composite(ImageChops.add(hull, Image.merge("RGBA", (noise,) * 3 + (Image.new("L", size, 0),)), 1, -128),
                           hull, Image.new("L", size, 255))
    hd = ImageDraw.Draw(hull)
    # struts read as rounded tubes: light band along one side, dark along the other
    for k in layout["keepouts"]:
        p = k["poly"]
        for t, col in ((0.18, (64, 80, 102, 255)), (0.30, (52, 66, 84, 255)), (0.78, (10, 13, 19, 255)), (0.9, (6, 8, 12, 255))):
            a = (p[0][0] + (p[1][0] - p[0][0]) * t, p[0][1] + (p[1][1] - p[0][1]) * t)
            b = (p[3][0] + (p[2][0] - p[3][0]) * t, p[3][1] + (p[2][1] - p[3][1]) * t)
            hd.line(S([a, b]), fill=col, width=7 * SS)
    # panel seams along struts and dash
    for k in layout["keepouts"]:
        p = k["poly"]
        a, b = ((p[0][0] + p[1][0]) / 2, (p[0][1] + p[1][1]) / 2), ((p[2][0] + p[3][0]) / 2, (p[2][1] + p[3][1]) / 2)
        hd.line(S([a, b]), fill=(6, 9, 14, 255), width=3 * SS)
        hd.line(S([(a[0] + 2, a[1]), (b[0] + 2, b[1])]), fill=(48, 60, 76, 255), width=1 * SS)
        for t in (0.18, 0.5, 0.82):  # rivets
            x, y = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
            for off in (-22, 22):
                hd.ellipse(S([(x + off - 3, y - 3), (x + off + 3, y + 3)]), fill=(52, 64, 80, 255))
    # dash seams and vents
    for y in range(1340, 1600, 46):
        hd.line(S([(60, y), (700, y - 24)]), fill=(8, 11, 17, 255), width=2 * SS)
        hd.line(S([(W - 60, y), (W - 700, y - 24)]), fill=(8, 11, 17, 255), width=2 * SS)
    for i in range(9):
        x = 1130 + i * 34
        hd.rounded_rectangle(S([(x, 1306), (x + 18, 1384)]), radius=6, fill=(7, 10, 15, 255))
    # header: inner raised plate following the canopy arc, plus chamfered end caps
    h = fr["header"]
    edge = header_edge(fr, W)
    inner = [(x, y - 26) for x, y in edge[3:-3]]
    hd.line(S(inner), fill=(8, 11, 17, 255), width=3 * SS)
    hd.line(S([(x, y + 2) for x, y in inner]), fill=(58, 72, 92, 255), width=SS)
    for x0, x1 in ((h["x0"] + 40, 960), (1600, h["x1"] - 40)):
        hd.rounded_rectangle(S([(x0, 6), (x1, 20)]), radius=6 * SS, fill=(44, 55, 71, 255))
    for x in range(h["x0"] + 60, h["x1"] - 40, 120):  # header panel seams
        y = header_edge(fr, W)[0][1]
        hd.line(S([(x, 24), (x, 32)]), fill=(8, 11, 17, 255), width=2 * SS)
    # dash: raised console behind the info strip and side console plates
    hd.polygon(S([(752, 1410), (1808, 1410), (1880, 1600), (680, 1600)]), fill=(28, 36, 48, 255))
    hd.line(S([(752, 1410), (1808, 1410)]), fill=(70, 88, 110, 255), width=SS)
    for sx in (1, -1):
        x0 = 0 if sx == 1 else W
        plate = [(x0 + sx * 40, 1380), (x0 + sx * 520, 1350), (x0 + sx * 560, 1600), (x0 + sx * 40, 1600)]
        hd.polygon(S(plate), fill=(22, 29, 39, 255))
        hd.line(S(plate[:2]), fill=(64, 80, 100, 255), width=SS)

    # bevel: light from top-left, shadow bottom-right
    hi = ImageChops.subtract(mask, ImageChops.offset(mask, 3 * SS, 3 * SS)).filter(ImageFilter.GaussianBlur(1.5 * SS))
    lo = ImageChops.subtract(mask, ImageChops.offset(mask, -3 * SS, -3 * SS)).filter(ImageFilter.GaussianBlur(1.5 * SS))
    hull = Image.composite(Image.new("RGBA", size, (70, 88, 110, 255)), hull, hi.point(lambda v: v // 2))
    hull = Image.composite(Image.new("RGBA", size, (2, 3, 6, 255)), hull, lo.point(lambda v: v // 2))
    hull.putalpha(mask)

    img = Image.new("RGBA", size, (0, 0, 0, 0))

    # ---- glass: inner shadow + faint sheen (keeps wallpaper visible) -------
    glass = ImageChops.invert(mask)
    shadow_a = mask.filter(ImageFilter.GaussianBlur(26 * SS)).point(lambda v: int(v * 0.62))
    shadow_a = ImageChops.multiply(shadow_a, glass)
    img.alpha_composite(Image.merge("RGBA", (Image.new("L", size, 2), Image.new("L", size, 4), Image.new("L", size, 9), shadow_a)))
    sheen = Image.new("L", size, 0)
    sd = ImageDraw.Draw(sheen)
    sd.polygon(S([(700, 300), (1050, 300), (760, 900), (560, 900)]), fill=14)
    sd.polygon(S([(1700, 320), (1820, 320), (1600, 760), (1520, 760)]), fill=9)
    sheen = ImageChops.multiply(sheen.filter(ImageFilter.GaussianBlur(40 * SS)), glass)
    img.alpha_composite(Image.merge("RGBA", (Image.new("L", size, 190), Image.new("L", size, 230), Image.new("L", size, 255), sheen)))

    img.alpha_composite(hull)

    # ---- window gasket: a dark seal just inside the glass edge -----------------
    seal = ImageChops.subtract(mask.filter(ImageFilter.MaxFilter(13)), mask)
    img.alpha_composite(Image.merge("RGBA", (Image.new("L", size, 4), Image.new("L", size, 6), Image.new("L", size, 10), seal.point(lambda v: int(v * 0.85)))))

    # ---- rim light where hull meets glass ---------------------------------
    edge = ImageChops.subtract(mask.filter(ImageFilter.MaxFilter(5)), mask)
    rim = Image.new("RGBA", size, CYAN + (0,))
    rim.putalpha(edge.point(lambda v: int(v * 0.45)))
    rim_glow = rim.filter(ImageFilter.GaussianBlur(6 * SS))
    img.alpha_composite(rim_glow)
    img.alpha_composite(rim)

    fx = Image.new("RGBA", size, (0, 0, 0, 0))

    # header underglow line follows the canopy arc
    glow_line(fx, header_edge(fr, W)[4:-4], CYAN, 2, 6, alpha=150)
    glow_line(fx, [(1000, 262), (1060, 292), (1500, 292), (1560, 262)], CYAN, 1.6, 5, alpha=170)
    # accent strips along the dash top, like the lit console edges in the reference
    glow_line(fx, [(1040, 1060), (1110, 1205), (1280, 1240), (1450, 1205), (1520, 1060)], CYAN, 1.2, 4, alpha=90)

    # ---- dash recesses for dash widgets -----------------------------------
    pad = fr["recess_pad"]
    for z in layout["zones"]:
        if z["group"] != "bottom":
            continue
        poly = offset_poly(shape(z, curves), pad)
        d = ImageDraw.Draw(fx)
        d.polygon(S(poly), fill=(4, 8, 14, 245))
        glow_line(fx, poly, CYAN, 1.5, 4, alpha=110, closed=True)
        inner = offset_poly(shape(z, curves), pad - 4)
        ImageDraw.Draw(fx).line(S(inner + [inner[0]]), fill=(40, 60, 80, 255), width=SS)

    # ---- projector pedestal under the sphere --------------------------------
    pj = fr["projector"]
    d = ImageDraw.Draw(fx)
    d.ellipse(S([(pj["cx"] - pj["rx"] - 20, pj["cy"] - pj["ry"] - 8), (pj["cx"] + pj["rx"] + 20, pj["cy"] + pj["ry"] + 14)]), fill=(6, 10, 16, 255))
    for k, a in ((1.0, 200), (0.72, 140), (0.45, 110)):
        rx, ry = pj["rx"] * k, pj["ry"] * k
        ring = [(pj["cx"] + rx * math.cos(t / 40 * math.tau), pj["cy"] + ry * math.sin(t / 40 * math.tau)) for t in range(41)]
        glow_line(fx, ring, CYAN, 1.5, 5, alpha=a)

    # ---- decor --------------------------------------------------------------
    for dc in layout.get("decor", []):
        poly = shape(dc, curves)
        name = dc["id"]
        if name.startswith("D_div"):
            mid_l = ((poly[0][0] + poly[3][0]) / 2, (poly[0][1] + poly[3][1]) / 2)
            mid_r = ((poly[1][0] + poly[2][0]) / 2, (poly[1][1] + poly[2][1]) / 2)
            glow_line(fx, [mid_l, mid_r], CYAN, 1.6, 5, alpha=200)
            if name == "D_divR1":  # chevrons like the reference
                cx, cy = mid_l[0] + 30, mid_l[1]
                for o in (0, 12):
                    glow_line(fx, [(cx + o + 8, cy - 7), (cx + o, cy), (cx + o + 8, cy + 7)], CYAN, 1.6, 3)
        elif name.startswith("D_rail"):
            top, bot = poly[0], poly[3]
            right = name.endswith("R")
            pts = []
            n = 4
            for i in range(n + 1):
                t = i / n
                x = top[0] + (bot[0] - top[0]) * t
                y = top[1] + (bot[1] - top[1]) * t
                jog = (-10 if right else 10) if i % 2 else 0
                pts.append((x + jog, y))
            glow_line(fx, pts, CYAN, 1.4, 4, alpha=170)
            for x, y in pts[1:-1]:
                glow_line(fx, [(x, y), (x + (-14 if right else 14), y)], CYAN, 1.4, 3, alpha=170)
        elif name.startswith("D_glyph"):
            (x0, y0), (x1, y1) = poly[0], poly[2]
            m = 10
            glow_line(fx, [(x0 + m, y0), (x0, y0), (x0, y0 + m)], CYAN, 1.6, 3, alpha=160)
            glow_line(fx, [(x1 - m, y1), (x1, y1), (x1, y1 - m)], CYAN, 1.6, 3, alpha=160)
            glow_line(fx, [((x0 + x1) / 2 - 8, (y0 + y1) / 2), ((x0 + x1) / 2 + 8, (y0 + y1) / 2)], CYAN, 1.6, 3, alpha=120)
            glow_line(fx, [((x0 + x1) / 2, (y0 + y1) / 2 - 8), ((x0 + x1) / 2, (y0 + y1) / 2 + 8)], CYAN, 1.6, 3, alpha=120)
        elif name.startswith("D_dash"):
            d = ImageDraw.Draw(fx)
            d.polygon(S(poly), fill=(6, 18, 30, 235))
            glow_line(fx, poly, CYAN, 1.4, 4, alpha=150, closed=True)
            (ax, ay), (bx, by), (cx_, cy_), (dx_, dy_) = poly

            def P(u, v):  # u across, v down, both 0..1 inside the tilted screen
                top = (ax + (bx - ax) * u, ay + (by - ay) * u)
                bot = (dx_ + (cx_ - dx_) * u, dy_ + (cy_ - dy_) * u)
                return (top[0] + (bot[0] - top[0]) * v, top[1] + (bot[1] - top[1]) * v)
            dd = ImageDraw.Draw(fx)
            for i in range(7):  # mini bar graph
                h = 0.15 + 0.5 * rnd.random()
                u0, u1 = 0.12 + i * 0.11, 0.12 + i * 0.11 + 0.07
                dd.polygon(S([P(u0, 0.92), P(u1, 0.92), P(u1, 0.92 - h * 0.45), P(u0, 0.92 - h * 0.45)]), fill=CYAN + (90,))
            trace = [P(0.1 + 0.8 * t / 30, 0.28 + 0.1 * math.sin(t / 30 * math.tau * 2)) for t in range(31)]
            dd.line(S(trace), fill=CYAN + (140,), width=SS)
            dd.line(S([P(0.08, 0.45), P(0.92, 0.45)]), fill=CYAN + (50,), width=SS)

    # ---- strut lights --------------------------------------------------------
    for x, y in fr["lights"]:
        g = Image.new("RGBA", size, (0, 0, 0, 0))
        gd = ImageDraw.Draw(g)
        gd.ellipse(S([(x - 26, y - 26), (x + 26, y + 26)]), fill=(40, 120, 255, 150))
        g = g.filter(ImageFilter.GaussianBlur(14 * SS))
        fx.alpha_composite(g)
        d = ImageDraw.Draw(fx)
        d.ellipse(S([(x - 11, y - 11), (x + 11, y + 11)]), fill=(10, 16, 26, 255), outline=(60, 80, 110, 255), width=SS)
        d.ellipse(S([(x - 5, y - 5), (x + 5, y + 5)]), fill=(150, 210, 255, 255))

    img.alpha_composite(fx)

    # ---- glass tint mask (white; Rainmeter tints it with the theme colour) -----
    # stronger toward the frame edges and the top of the canopy, like a curved visor
    edge_t = mask.filter(ImageFilter.GaussianBlur(70 * SS))
    vert = Image.linear_gradient("L").resize(size).point(lambda v: int(255 - v * 0.55))
    tint_a = ImageChops.add(edge_t.point(lambda v: int(v * 0.6)), vert.point(lambda v: int(v * 0.55)))
    tint_a = ImageChops.multiply(tint_a, glass)
    tint = Image.merge("RGBA", (Image.new("L", size, 255),) * 3 + (tint_a,))
    return img.resize((W, H), Image.LANCZOS), tint.resize((W, H), Image.LANCZOS)


def starfield(w, h, seed=3):
    rnd = random.Random(seed)
    bg = vertical_gradient((w, h), (6, 10, 26), (2, 3, 8)).convert("RGBA")
    d = ImageDraw.Draw(bg)
    for _ in range(1600):
        x, y = rnd.randrange(w), rnd.randrange(h)
        b = rnd.randint(80, 255)
        d.point((x, y), fill=(b, b, min(255, b + 20), 255))
    neb = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    nd = ImageDraw.Draw(neb)
    nd.ellipse([1500, 300, 2500, 1000], fill=(60, 40, 120, 70))
    nd.ellipse([200, 900, 1100, 1500], fill=(20, 80, 120, 60))
    bg.alpha_composite(neb.filter(ImageFilter.GaussianBlur(120)))
    return bg


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", help="also write the frame over a stand-in starfield")
    args = ap.parse_args()
    layout = load()
    img, tint = build(layout)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUT, optimize=True)
    tint.save(OUT.with_name("glass.png"), optimize=True)
    print("wrote", OUT, img.size)
    if args.preview:
        bg = starfield(*img.size)
        t = tint.copy()
        r, g, b, a = t.split()
        t = Image.merge("RGBA", (r.point(lambda v: 0), g.point(lambda v: v * 210 // 255), b, a.point(lambda v: v * 40 // 255)))
        bg.alpha_composite(t)
        bg.alpha_composite(img)
        bg.convert("RGB").save(args.preview)
        print("preview", args.preview)


if __name__ == "__main__":
    main()
