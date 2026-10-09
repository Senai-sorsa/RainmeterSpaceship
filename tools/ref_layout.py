#!/usr/bin/env python3
"""Generate layout/layout.json from coordinates traced off the reference image (1260 x 709).

Every zone, window and hull outline below is written in REFERENCE pixels, measured from zoomed,
gridded crops of the original cockpit image, and mapped onto the 2560 x 1600 canvas
(x * 2560/1260, y * 1600/709). Slanted panels are quads [TL, TR, BR, BL]; the build turns each quad
into a Rainmeter TransformationMatrix so text and graphics lean exactly like the reference.

Deviations from the reference are deliberate and listed in DEVIATIONS.
Run:  python tools/ref_layout.py && python tools/build.py && python tools/vector_frame.py
"""
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RW, RH = 1260, 709
CW, CH = 2560, 1600
SX, SY = CW / RW, CH / RH

DEVIATIONS = [
    "Widgets stay above the Windows taskbar band (72 px); the bottom info strip sits ~10 ref px higher.",
    "Left column slot 4 shares its block with the upkeep counters (the reference's small 3 / 4 counters).",
    "Right column gets a matching dev-status counter block left of ship 4.",
    "Right category page selector uses the reference's small triangle-and-number glyph.",
]


def P(x, y):
    return [round(x * SX, 2), round(y * SY, 2)]


def rect(x0, y0, x1, y1):
    return [P(x0, y0), P(x1, y0), P(x1, y1), P(x0, y1)]


def quad(*pts):
    return [P(x, y) for x, y in pts]


def zone(zid, group, q, content):
    tl, tr, br, bl = q
    w = math.hypot(tr[0] - tl[0], tr[1] - tl[1])
    h = math.hypot(bl[0] - tl[0], bl[1] - tl[1])
    return {"id": zid, "group": group, "x": tl[0], "y": tl[1], "w": round(w, 2), "h": round(h, 2), "quad": q,
            "content": content}


ZONES = [
    # ---------------------------------------------------------------- top console
    zone("T_power", "top", quad((335, 24), (432, 32), (432, 44), (335, 36)), "H ---- C bar -> power draw"),
    zone("T_battery", "top", quad((826, 33), (956, 21), (956, 33), (826, 45)), "PWR ---- bar -> battery"),
    zone("T_settings", "top", rect(470, 10, 805, 57), "COMBAT STARMAP... tabs -> GPU modes; RADR/IFCS + MISL..GFRC -> quick settings"),
    zone("T_alert", "top", rect(289, 53, 318, 72), "warning triangle + count"),
    zone("G1_cpu", "top", rect(333, 62, 447, 95), "OXYGEN LEVEL plate -> CPU (fixed)"),
    zone("G2_select", "top", rect(493, 62, 607, 95), "INTERNAL PRESSURE plate -> selectable"),
    zone("G3_select", "top", rect(663, 62, 787, 95), "HULL INTEGRITY plate -> selectable"),
    zone("G4_ram", "top", rect(828, 62, 940, 95), "FUEL LEVEL plate -> RAM (fixed)"),
    # ---------------------------------------------------------------- left column
    zone("L_tabs", "left", quad((74, 37), (256, 68), (256, 89), (74, 58)), "OVR WEAP AVI... -> category app tabs"),
    zone("L_category", "left", rect(62, 92, 232, 218), "ship schematic -> app wireframe"),
    zone("L_location", "left", quad((34, 222), (230, 232), (230, 302), (34, 292)), "LAT / LON / VRT block"),
    zone("L_dots", "left", rect(92, 304, 164, 318), "page dots -> category pages"),
    zone("L_app1", "left", rect(34, 324, 230, 388), "weapon 1 -> slot 1"),
    zone("L_app2", "left", rect(40, 394, 230, 450), "weapon 2 -> slot 2"),
    zone("L_app3", "left", rect(52, 455, 158, 510), "weapon 3 -> slot 3"),
    zone("L_app4", "left", rect(68, 516, 136, 574), "ship 4 -> slot 4"),
    zone("L_upkeep", "left", rect(140, 518, 180, 552), "3 / 4 counters -> updates / upgrades"),
    # ---------------------------------------------------------------- right column
    zone("R_tabs", "right", quad((1004, 70), (1182, 40), (1182, 61), (1004, 91)), "SUBSYS CARGO MAIL -> category app tabs"),
    zone("R_category", "right", rect(1030, 96, 1202, 212), "ship -> app wireframe"),
    zone("R_dots", "right", rect(1210, 186, 1240, 216), "triangle + 4 glyph -> category page"),
    zone("R_sysinfo", "right", rect(1028, 226, 1228, 302), "VANDUUL SCYTHE card -> BLACK-CLOVER"),
    zone("R_app1", "right", rect(1028, 324, 1228, 388), "card 1 -> slot 5"),
    zone("R_app2", "right", rect(1124, 394, 1226, 452), "card 2 -> slot 6"),
    zone("R_app3", "right", rect(1124, 456, 1226, 512), "card 3 -> slot 7"),
    zone("R_app4", "right", rect(1128, 516, 1200, 574), "ship 4 -> slot 8"),
    zone("R_dev", "right", rect(1084, 518, 1124, 552), "dev counters"),
    # ---------------------------------------------------------------- centre
    zone("C_target", "center", rect(583, 155, 709, 251), "orange target lock"),
    zone("C_hud", "center", rect(486, 256, 778, 401), "speed ladders, pipper, M/S THR"),
    zone("C_sphere", "center", rect(535, 407, 768, 582), "holographic sphere + DSP RNGE label"),
    # ---------------------------------------------------------------- dash
    zone("B_storage", "bottom", rect(395, 565, 488, 638), "ENG / ATMOS / DMG screen -> storage"),
    zone("B_audio", "bottom", rect(778, 568, 872, 638), "TARGET SNR screen -> audio"),
    zone("B_stripL", "bottom", rect(425, 644, 604, 672), "1500 / 7 / 0% / 443 boxed cells"),
    zone("B_stripR", "bottom", rect(742, 648, 822, 672), "20 / 20 open cells"),
]

# ---------------------------------------------------------------- the ship (reference pixels)
WIN_CENTER = [(325, 96), (480, 94), (630, 93), (780, 94), (930, 96), (778, 366), (505, 366)]
WIN_LEFT = [(52, 0), (205, 0), (215, 9), (262, 30), (452, 368), (232, 470), (0, 588), (0, 150), (10, 95), (28, 45)]
WIN_RIGHT = [(1208, 0), (1055, 0), (1045, 9), (998, 30), (808, 372), (1030, 474), (1260, 588), (1260, 150), (1250, 95), (1232, 45)]
def _arc(cx, cy, rx, ry, a0, a1, n=14):
    return [(cx + rx * math.cos(math.radians(a0 + (a1 - a0) * i / n)), cy + ry * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]


# visor bezel: dark rounded canopy rim outside the windows (top corners and bottom corners)
_RIM_L = _arc(62, 150, 56, 150, 270, 180) + [(6, 560)] + _arc(140, 560, 134, 149, 180, 90)
BEZEL_L = [(0, 0)] + _RIM_L + [(0, 709)]
BEZEL_R = [(RW - x, y) for x, y in BEZEL_L]
RIM_L = _RIM_L
RIM_R = [(RW - x, y) for x, y in _RIM_L]
STRUT_RIGHT = [(1080, 16), (1110, 16), (1260, 214), (1260, 254)]
PILLAR_L = [(262, 30), (325, 96), (505, 366), (470, 374), (452, 368)]
PILLAR_R = [(998, 30), (930, 96), (778, 366), (792, 376), (808, 372)]
BEAM_L = [(470, 374), (505, 380), (250, 500), (0, 610), (0, 584), (232, 470)]
BEAM_R = [(792, 376), (772, 384), (1012, 503), (1260, 612), (1260, 586), (1030, 474)]
LIGHTS = [(380, 195), (880, 195), (232, 495), (1030, 500)]
PLATES = [(330, 52, 450, 93), (490, 52, 610, 93), (660, 52, 790, 93), (825, 52, 943, 93)]
SCREENS = [(392, 562, 491, 641), (775, 565, 875, 641)]
TILTED = [[(305, 648), (348, 632), (360, 694), (318, 709)], [(955, 648), (912, 632), (900, 694), (942, 709)]]
ARCH = [(382, 706), (420, 668), (520, 650), (640, 645), (760, 650), (838, 668), (876, 706)]
CONSOLE = [(505, 366), (778, 366), (765, 420), (725, 600), (535, 600), (518, 420)]
STREAKS = [[(195, 585), (365, 518)], [(245, 625), (380, 572)], [(150, 650), (300, 600)],
           [(1065, 585), (895, 518)], [(1015, 625), (880, 572)], [(1110, 650), (960, 600)]]

# HUD lines that are part of the cockpit glass (decor layer, tinted with the theme colour)
CONSOLE_LINES = [
    [(482, 0), (510, 29), (750, 29), (778, 0)],
    [(280, 30), (445, 50), (462, 37), (602, 42), (620, 59)],
    [(642, 59), (660, 44), (800, 37), (817, 50), (980, 30)],
]
GLYPHS = [(118, 598), (148, 655), (1142, 598), (1112, 655)]
CIRCLE_GLYPH = (315, 372)
COWL_DOTS = (635, 700, 372)


def scale(pts):
    return [P(x, y) for x, y in pts]


def main():
    layout = {
        "_comment": "GENERATED by tools/ref_layout.py from the reference image (1260x709) - edit that file, not this one.",
        "deviations": DEVIATIONS,
        "reference": {"w": RW, "h": RH, "sx": SX, "sy": SY},
        "canvas": {"w": CW, "h": CH},
        "safe_area": {"inset": 10, "corner_radius": 110},
        "taskbar": {"height": 72},
        "min_gap": 8,
        "decor_gap": 1,
        "curves": {g: {"type": "flat"} for g in ("top", "left", "right", "center", "bottom")},
        "keepouts": [],
        "zones": ZONES,
        "decor": [
            {"id": f"D_glyph{i + 1}", "group": "center", "x": P(x - 7, y - 7)[0], "y": P(x - 7, y - 7)[1],
             "w": round(14 * SX, 2), "h": round(14 * SY, 2)} for i, (x, y) in enumerate(GLYPHS)
        ] + [
            {"id": "D_circle", "group": "center", "x": P(CIRCLE_GLYPH[0] - 9, 0)[0], "y": P(0, CIRCLE_GLYPH[1] - 9)[1],
             "w": round(18 * SX, 2), "h": round(18 * SY, 2)},
            {"id": "D_tiltL", "poly": scale(TILTED[0])},
            {"id": "D_tiltR", "poly": scale(TILTED[1])},
        ],
        "overlays": [
            {"id": "O_drawer", "x": 1000, "y": 240, "w": 560, "h": 560, "content": "CARGO drawer (transient)"},
            {"id": "O_control", "x": 760, "y": 300, "w": 1040, "h": 900, "content": "Control Center (transient)"},
        ],
        "frame": {
            "windows": [scale(WIN_CENTER), scale(WIN_LEFT), scale(WIN_RIGHT)],
            "hull_extra": [scale(STRUT_RIGHT), scale(BEZEL_L), scale(BEZEL_R)],
            "rims": [scale(RIM_L), scale(RIM_R)],
            "pillars": [scale(PILLAR_L), scale(PILLAR_R)],
            "beams": [scale(BEAM_L), scale(BEAM_R)],
            "lights": scale(LIGHTS),
            "plates": [P(a, b) + P(c, d) for a, b, c, d in PLATES],
            "screens": [P(a, b) + P(c, d) for a, b, c, d in SCREENS],
            "tilted": [scale(t) for t in TILTED],
            "arch": scale(ARCH),
            "console": scale(CONSOLE),
            "streaks": [scale(s) for s in STREAKS],
            "console_lines": [scale(l) for l in CONSOLE_LINES],
            "glyphs": scale(GLYPHS),
            "circle_glyph": P(*CIRCLE_GLYPH),
            "cowl_dots": [P(COWL_DOTS[0], COWL_DOTS[2]), P(COWL_DOTS[1], COWL_DOTS[2])],
        },
    }
    # keep the module list from the existing layout, updated for the new zones
    old = json.loads((ROOT / "layout" / "layout.json").read_text())
    skins = old["skins"]
    skins["Left\\Category"] = {"zones": ["L_tabs", "L_category", "L_dots"]}
    skins["Right\\Category"] = {"zones": ["R_tabs", "R_category", "R_dots"]}
    skins["Bottom\\Strip"] = {"zones": ["B_stripL", "B_stripR"]}
    layout["skins"] = skins
    (ROOT / "layout" / "layout.json").write_text(json.dumps(layout, indent=1))
    print(f"wrote layout.json: {len(ZONES)} zones")


if __name__ == "__main__":
    main()
