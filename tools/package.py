#!/usr/bin/env python3
"""Build the one-click installer: release/Spaceship_HUD_<version>.rmskin

Contents: Skins/Spaceship (every module + @Resources), Layouts/Spaceship/Rainmeter.ini (loads the
whole cockpit in the right z-order) and RMSKIN.ini. Runtime files (Start-menu scan, logs, preset
contents) are left out.

Usage: python tools/package.py [--version 1.0.0]
"""
import argparse
import io
import struct
import zipfile
from pathlib import Path

from layoutlib import ROOT, load

SKINS = ROOT / "Skins" / "Spaceship"
SKIP = {"StartApps.txt", "HWiNFO.txt", "llt.log", "stamp.txt"}


def layout_ini(layout):
    order = ["Frame", "Controller"] + [c for c in layout["skins"] if c not in ("Frame", "Controller")]
    lines = ["[Rainmeter]", ""]
    for i, cfg in enumerate(order):
        info = layout["skins"][cfg]
        overlay = "overlay" in info
        lines += [
            f"[Spaceship\\{cfg}]",
            f"Active={0 if overlay else 1}",
            "AlwaysOnTop=-2",
            f"LoadOrder={-10 if cfg == 'Frame' else (10 if overlay else 0)}",
            f"ClickThrough={1 if cfg == 'Frame' else 0}",
            "Draggable=0",
            "SnapEdges=0",
            "KeepOnScreen=0",
            "",
        ]
    return "\r\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", default="1.0.0")
    args = ap.parse_args()
    layout = load()
    lay = layout_ini(layout)
    (ROOT / "layout" / "rainmeter").mkdir(parents=True, exist_ok=True)
    (ROOT / "layout" / "rainmeter" / "Rainmeter.ini").write_text(lay, newline="")

    rmskin_ini = "\r\n".join([
        "[rmskin]",
        "Name=Spaceship HUD",
        "Author=Senai Sorsa",
        f"Version={args.version}",
        "MinimumRainmeter=4.5.0",
        "MinimumWindows=10.0",
        "LoadType=Layout",
        "Load=Spaceship",
        "",
    ])
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("RMSKIN.ini", rmskin_ini)
        z.writestr("Layouts/Spaceship/Rainmeter.ini", lay)
        for f in sorted(SKINS.rglob("*")):
            if f.is_dir() or f.name in SKIP or (f.parent.parent.name == "Presets" and f.name != "README.txt"):
                continue
            z.write(f, "Skins/Spaceship/" + f.relative_to(SKINS).as_posix())
    data = buf.getvalue()
    # Rainmeter's .rmskin footer: 8-byte zip size, 1 flag byte, "RMSKIN\0"
    data += struct.pack("<qB7s", len(data), 0, b"RMSKIN\x00")
    out = ROOT / "release" / f"Spaceship_HUD_{args.version}.rmskin"
    out.parent.mkdir(exist_ok=True)
    out.write_bytes(data)
    print(f"wrote {out} ({len(data) / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
