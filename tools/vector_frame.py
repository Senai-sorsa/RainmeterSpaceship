#!/usr/bin/env python3
"""Build the cockpit as Rainmeter Shape meters from the traced reference (art/cockpit-trace.svg).

The trace (VTracer, 3485 stacked colour regions of the original 1260x709 image) is filtered down to the
ship itself and written as hundreds of Shape paths into Skins/Spaceship/Frame/Parts/*.inc:

  Glass.inc      theme-tinted window glass (gradient), drawn first
  Base.inc       hull silhouette fill (windows cut out), the backing for every traced piece
  Hull_NN.inc    the traced hull pieces, in the trace's stacking order, ~60 shapes per meter
  Lights.inc     strut lights with layered glow
  Decor.inc      HUD lines etched on the glass / dash, in the theme colour

Dropped from the trace: anything seen through the windows (space, planet), the reference's own HUD
(bright cyan / orange / pink marks, text) and regions our live widgets occupy (sphere, screens, plates).

Usage: python tools/vector_frame.py [--tolerance 0.45] [--min-area 1.2]
"""
import argparse
import colorsys
import re
import sys
from pathlib import Path

from shapely.geometry import LineString, MultiPolygon, Polygon, box
from shapely.ops import split, unary_union

sys.path.insert(0, str(Path(__file__).parent))
import ref_layout as R  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SVG = ROOT / "art" / "cockpit-trace.svg"
PARTS = ROOT / "Skins" / "Spaceship" / "Frame" / "Parts"
PER_METER = 60


# ---------------------------------------------------------------- SVG parsing
def parse_paths():
    text = SVG.read_text()
    out = []
    for d, fill, tx, ty in re.findall(r'<path d="([^"]*)" fill="(#[0-9A-Fa-f]{6})"(?: transform="translate\(([-\d.]+),([-\d.]+)\)")?', text):
        tx, ty = float(tx or 0), float(ty or 0)
        subs, cur = [], []
        toks = re.findall(r"[MCZ]|-?\d*\.?\d+(?:e-?\d+)?", d)
        i, cmd, pos = 0, None, (0.0, 0.0)
        while i < len(toks):
            t = toks[i]
            if t in "MCZ":
                cmd = t
                i += 1
                if t == "Z":
                    if len(cur) >= 3:
                        subs.append(cur)
                    cur = []
                continue
            if cmd == "M":
                pos = (float(toks[i]) + tx, float(toks[i + 1]) + ty)
                if len(cur) >= 3:
                    subs.append(cur)
                cur = [pos]
                i += 2
            elif cmd == "C":
                p1 = (float(toks[i]) + tx, float(toks[i + 1]) + ty)
                p2 = (float(toks[i + 2]) + tx, float(toks[i + 3]) + ty)
                p3 = (float(toks[i + 4]) + tx, float(toks[i + 5]) + ty)
                for k in (1, 2, 3, 4):
                    s = k / 4
                    a = (1 - s) ** 3
                    b = 3 * (1 - s) ** 2 * s
                    c = 3 * (1 - s) * s * s
                    e = s ** 3
                    cur.append((a * pos[0] + b * p1[0] + c * p2[0] + e * p3[0], a * pos[1] + b * p1[1] + c * p2[1] + e * p3[1]))
                pos = p3
                i += 6
            else:
                i += 1
        if len(cur) >= 3:
            subs.append(cur)
        rgb = tuple(int(fill[k:k + 2], 16) for k in (1, 3, 5))
        out.append((subs, rgb))
    return out


# ---------------------------------------------------------------- geometry helpers
def polys_of(geom):
    if geom.is_empty:
        return []
    if isinstance(geom, Polygon):
        return [geom]
    if isinstance(geom, MultiPolygon):
        return list(geom.geoms)
    return [g for g in getattr(geom, "geoms", []) if isinstance(g, Polygon)]


def hole_free(poly, depth=0):
    """Rainmeter paths have no holes: split polygons with interiors until none remain."""
    if not poly.interiors or depth > 12:
        return [Polygon(poly.exterior)]
    ring = poly.interiors[0]
    x = ring.centroid.x
    minx, miny, maxx, maxy = poly.bounds
    parts = split(poly, LineString([(x, miny - 1), (x, maxy + 1)]))
    out = []
    for p in polys_of(parts):
        out += hole_free(p, depth + 1)
    return out


def is_hud_colour(rgb):
    r, g, b = (v / 255 for v in rgb)
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    if v > 0.55 and s > 0.42:                       # saturated bright: cyan HUD, orange target, pink marks
        return True
    if 0.42 < h < 0.58 and s > 0.55 and v > 0.4:    # vivid cyan, even when dimmer
        return True
    return False


def hull_region():
    windows = unary_union([Polygon(R.WIN_CENTER), Polygon(R.WIN_LEFT), Polygon(R.WIN_RIGHT)]).buffer(0)
    hull = box(0, 0, R.RW, R.RH).difference(windows)
    hull = unary_union([hull, Polygon(R.STRUT_RIGHT)])
    return hull, windows


def widget_region():
    """zones of widgets that sit on the hull - their traced content (screens, sphere, plates) is replaced live"""
    keep = ("G1_cpu", "G2_select", "G3_select", "G4_ram", "C_sphere", "B_storage", "B_audio", "B_stripL", "B_stripR", "T_settings", "T_power", "T_battery", "T_alert")
    polys = []
    for z in R.ZONES:
        if z["id"] in keep:
            polys.append(Polygon([(x / R.SX, y / R.SY) for x, y in z["quad"]]))
    # the hologram glow spreads beyond its zone
    polys.append(Polygon([(x, y) for x, y in R._arc(628, 491, 100, 100, 0, 360, 40)]))
    return unary_union(polys)


# ---------------------------------------------------------------- emit
def fmt_pts(pts, closed=False):
    d = " | ".join(("%.1f,%.1f" if i == 0 else "LineTo %.1f,%.1f") % (x * R.SX, y * R.SY) for i, (x, y) in enumerate(pts))
    return d + (" | ClosePath 1" if closed else "")


def meter_block(name, shapes, tm=True):
    """shapes: list of (pathdef or None, spec). Returns ini text for one Shape meter."""
    lines = [f"[{name}]", "Meter=Shape", "X=0", "Y=0"]
    for k, (pdef, spec) in enumerate(shapes, 1):
        key = "Shape" if k == 1 else f"Shape{k}"
        if pdef is not None:
            lines.append(f"P{k}={pdef}")
            lines.append(f"{key}=Path P{k} | {spec}")
        else:
            lines.append(f"{key}={spec}")
    if tm:
        lines.append("TransformationMatrix=#Scale#;0;0;#Scale#;0;0")
    lines.append("DynamicVariables=0")
    return "\n".join(lines) + "\n\n"


def build(tol, min_area):
    paths = parse_paths()
    hull, windows = hull_region()
    widgets = widget_region()
    kept, stats = [], {"total": 0, "glass": 0, "hud": 0, "widget": 0, "tiny": 0}
    for subs, rgb in paths:
        for pts in subs:
            stats["total"] += 1
            try:
                poly = Polygon(pts).buffer(0)
            except Exception:
                continue
            if poly.is_empty or poly.area < min_area:
                stats["tiny"] += 1
                continue
            if poly.area > 0.9 * R.RW * R.RH:
                continue  # the full-image background rectangle (Base.inc replaces it)
            inside = poly.intersection(hull).area / poly.area
            if inside < 0.5:
                stats["glass"] += 1
                continue
            if is_hud_colour(rgb):
                stats["hud"] += 1
                continue
            if poly.intersection(widgets).area / poly.area > 0.6:
                stats["widget"] += 1
                continue
            clipped = poly.intersection(hull).simplify(tol, preserve_topology=False)
            for p in polys_of(clipped):
                for q in hole_free(p):
                    if q.area >= min_area and len(q.exterior.coords) >= 4:
                        kept.append((list(q.exterior.coords)[:-1], rgb))
    return kept, stats, hull


def write(kept, hull):
    PARTS.mkdir(parents=True, exist_ok=True)
    for f in PARTS.glob("*.inc"):
        f.unlink()
    header = "; GENERATED by tools/vector_frame.py from art/cockpit-trace.svg - edit the generator, not this file.\n"
    # Glass: theme tinted gradient over each window
    glass = []
    for i, w in enumerate((R.WIN_CENTER, R.WIN_LEFT, R.WIN_RIGHT), 1):
        glass.append((fmt_pts(w, True), f"Fill LinearGradient GlassGrad | StrokeWidth 0"))
    gtxt = meter_block("Glass", glass).replace("[Glass]\n", "[Glass]\nGlassGrad=90 | #ColorAccent#,(Min(255,#GlassTint#*0.75)) ; 0.0 | #ColorAccent#,(#GlassTint#*0.12) ; 0.55 | #ColorAccent#,(Min(255,#GlassTint#*0.3)) ; 1.0\n")
    (PARTS / "Glass.inc").write_text(header + gtxt, newline="\r\n")
    # Base: hull silhouette without holes
    base = []
    for p in polys_of(hull):
        for q in hole_free(p):
            base.append((fmt_pts(list(q.exterior.coords)[:-1], True), "Fill Color 5,10,15 | StrokeWidth 0"))
    (PARTS / "Base.inc").write_text(header + meter_block("Base", base), newline="\r\n")
    # Hull pieces in stacking order
    n = 0
    for start in range(0, len(kept), PER_METER):
        n += 1
        chunk = kept[start:start + PER_METER]
        shapes = [(fmt_pts(pts, True), "Fill Color %d,%d,%d | StrokeWidth 0" % rgb) for pts, rgb in chunk]
        (PARTS / f"Hull_{n:02d}.inc").write_text(header + meter_block(f"Hull{n:02d}", shapes), newline="\r\n")
    # Lights with layered glow
    lights = []
    for (x, y) in R.LIGHTS:
        X, Y = x * R.SX, y * R.SY
        for r, a in ((46, 20), (34, 34), (24, 60), (15, 110)):
            lights.append((None, f"Ellipse {X:.1f},{Y:.1f},{r} | Fill Color 40,130,255,{a} | StrokeWidth 0"))
        lights.append((None, f"Ellipse {X:.1f},{Y:.1f},7 | Fill Color 190,230,255,255 | StrokeWidth 0"))
    (PARTS / "Lights.inc").write_text(header + meter_block("Lights", lights), newline="\r\n")
    # Decor: HUD lines in the theme colour (glow pass + sharp pass)
    dec = []

    def line(pts, w=1.7, glow=True, alpha=235, closed=False):
        d = fmt_pts(pts, closed)
        if glow:
            dec.append((d, f"Fill Color 0,0,0,0 | Stroke Color #ColorAccent#,(#GlowAlpha#*0.9) | StrokeWidth {w * 3.2:.1f} | StrokeLineJoin Round"))
        dec.append((d, f"Fill Color 0,0,0,0 | Stroke Color #ColorAccent#,{alpha} | StrokeWidth {w:.1f} | StrokeLineJoin Round"))

    for l in R.CONSOLE_LINES:
        line(l)
    line(R.ARCH)
    line([(x, y + 22 / R.SY) for x, y in R.ARCH][1:-1], 1.2, False, 150)
    for x0, y0, x1, y1 in R.SCREENS:
        dec.append((fmt_pts([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], True), "Fill Color #ColorAccent#,64 | StrokeWidth 0"))
        line([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], 1.3, True, 150, closed=True)
    for t in R.TILTED:
        dec.append((fmt_pts(t, True), "Fill Color #ColorAccent#,60 | StrokeWidth 0"))
        line(t, 1.3, True, 180, closed=True)
        a, b, c, d4 = t
        for i in range(1, 8):
            v = i / 9
            l0 = (a[0] + (d4[0] - a[0]) * v, a[1] + (d4[1] - a[1]) * v)
            r0 = (b[0] + (c[0] - b[0]) * v, b[1] + (c[1] - b[1]) * v)
            w = 0.35 + 0.08 * ((i * 37) % 7)
            line([(l0[0] + (r0[0] - l0[0]) * 0.15, l0[1] + (r0[1] - l0[1]) * 0.15), (l0[0] + (r0[0] - l0[0]) * (0.15 + w), l0[1] + (r0[1] - l0[1]) * (0.15 + w))], 1, False, 140)
    for (x, y) in R.GLYPHS:
        s = 7
        line([(x - s, y - 3), (x - s, y - s), (x - 3, y - s)], 1.5)
        line([(x + s, y + 3), (x + s, y + s), (x + 3, y + s)], 1.5)
        line([(x - 4, y + 2), (x, y - 2), (x + 4, y + 2)], 1.5)
    cx, cy = R.CIRCLE_GLYPH
    line([(cx + 8 * __import__("math").cos(__import__("math").radians(a)), cy + 8 * __import__("math").sin(__import__("math").radians(a))) for a in range(30, 331, 15)], 1.8)
    line([(cx - 3, cy - 3), (cx + 2, cy), (cx - 3, cy + 3)], 1.8)
    x0, x1, y = R.COWL_DOTS
    for i in range(22):
        xx = (x0 + (x1 - x0) * i / 21) * R.SX
        dec.append((None, f"Rectangle {xx - 2:.1f},{y * R.SY - 4:.1f},4,8 | Fill Color #ColorAccent#,170 | StrokeWidth 0"))
    (PARTS / "Decor.inc").write_text(header + meter_block("Decor", dec), newline="\r\n")
    return n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tolerance", type=float, default=0.45, help="simplification in reference pixels")
    ap.add_argument("--min-area", type=float, default=1.2, help="drop traced regions smaller than this (ref px^2)")
    args = ap.parse_args()
    kept, stats, hull = build(args.tolerance, args.min_area)
    n = write(kept, hull)
    size = sum(f.stat().st_size for f in PARTS.glob("*.inc"))
    print(f"trace regions: {stats}")
    print(f"kept {len(kept)} hull shapes in {n} meters (+ glass, base, lights, decor); {size / 1e6:.2f} MB of ini")


if __name__ == "__main__":
    main()
