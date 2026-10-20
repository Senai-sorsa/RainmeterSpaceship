"""Self-check for export_ui_assets.py: plain asserts, no test framework.  Run:  python3 -I tools/test_export_ui_assets.py"""
import json
import os
import re
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import export_ui_assets as ex
import layoutlib

LUA = """-- header
local I = {}
I.a = {
  { 'l', 1,2, 3,4 }, { 'p', 0,0, 1,1, 2,0 }, -- c
  { 'c', 50,50, 6 }, { 'a', 50,50, 10, 0,90 }, { 'a', 50,50, 10, 0,90, 5.5 }, { 'e', 1,2, 3,4 },
}
return I
"""
d = ex.parse_icons(LUA)
assert d["box"] == 100 and [p[0] for p in d["icons"]["a"]] == list("lpcaae"), d
assert d["icons"]["a"][4] == ["a", 50, 50, 10, 0, 90, 5.5]


def raises(text):
    try:
        ex.parse_icons(text)
    except ex.ParseError as e:
        return str(e)
    raise AssertionError("expected ParseError")


assert "unknown primitive" in raises(LUA.replace("'e'", "'z'")) and "line " in raises(LUA.replace("'e'", "'z'"))
assert "arity" in raises(LUA.replace("{ 'c', 50,50, 6 }", "{ 'c', 50,50 }"))
assert "arity" in raises(LUA.replace("{ 'l', 1,2, 3,4 }", "{ 'l', 1,2, 3 }"))
raises(LUA.replace("3,4 }", "3,x4 }"))

ini = "; c\n[Variables]\nA=1\n\n[S.x]\nMeter=Shape\nShape=Path #P# | Fill Color #C#,5\n; skip\n[S.y]\nK = v=w\n"
assert ex.parse_ini(ini) == [["Variables", {"A": "1"}], ["S.x", {"Meter": "Shape", "Shape": "Path #P# | Fill Color #C#,5"}],
                             ["S.y", {"K": "v=w"}]]
try:
    ex.parse_ini("A=1\n")
    raise AssertionError("expected ParseError")
except ex.ParseError:
    pass

v, red = ex.parse_settings("[Variables]\nScale=1\nGmailPassword=hunter2\nCalendarId=x\nApiToken=t\nOrbSpeed=3\n")
assert v == {"Scale": "1", "OrbSpeed": "3"} and red == ["ApiToken", "CalendarId", "GmailPassword"], (v, red)

assert ex.parse_module_keys("[Variables]\nB_DX=0\nB_DY=0\nA_DX=0\n", ["DX=#A_DX#\nDX=#B_DX#\n"]) == ["A", "B"]
try:
    ex.parse_module_keys("A_DX=0\n", ["DX=#B_DX#\n"])
    raise AssertionError("expected ParseError")
except ex.ParseError:
    pass

with tempfile.TemporaryDirectory() as t1, tempfile.TemporaryDirectory() as t2:
    assert ex.main(["--out", t1, "--check"]) == 1                      # missing files
    assert ex.main(["--out", t1]) == 0
    assert ex.main(["--out", t1, "--check"]) == 0
    assert ex.main(["--out", t2]) == 0
    names = sorted(os.listdir(t1))
    assert names == sorted([f + ".json" for f in ex.GENS if f != "frame"] + ["_meta.json", "frame"]), names
    for n in names:                                                     # deterministic
        if n != "frame":
            assert (Path(t1) / n).read_bytes() == (Path(t2) / n).read_bytes(), n
            assert (Path(t1) / n).read_bytes().endswith(b"\n")
    fm = json.loads((Path(t1) / "frame/manifest.json").read_text())
    assert sorted(fm) == sorted(ex.FRAME_IMAGES) and all(re.fullmatch(r"%s\.[0-9a-f]{8}\.png" % n, f) for n, f in fm.items()), fm
    assert sorted(os.listdir(Path(t1) / "frame")) == sorted(list(fm.values()) + ["manifest.json"])
    for f in os.listdir(Path(t1) / "frame"):
        assert (Path(t1) / "frame" / f).read_bytes() == (Path(t2) / "frame" / f).read_bytes(), f
    first = Path(t1) / "frame" / fm["hull"]
    first.unlink()
    assert ex.main(["--out", t1, "--check"]) == 1                      # --check sees a missing image
    (Path(t1) / "frame" / "old.00000000.png").write_bytes(b"x")
    assert ex.main(["--out", t1]) == 0 and not (Path(t1) / "frame" / "old.00000000.png").exists() and first.is_file()
    assert ex.main(["--out", t1, "--check"]) == 0
    ic = json.loads((Path(t1) / "icons.json").read_text())
    assert len(ic["icons"]) > 50, len(ic["icons"])
    lay = json.loads((Path(t1) / "layout.json").read_text())
    assert len(lay["zones"]) == len(layoutlib.load()["zones"]) and len(lay["zones"][0]["matrix"]) == 6
    assert lay["margins"] == {"module": 18, "animationBleed": 12}, lay["margins"]
    st = json.loads((Path(t1) / "settings.json").read_text())
    assert not [k for k in st["variables"] if re.search(ex.REDACT.pattern, k, re.I)]
    mk = json.loads((Path(t1) / "modules.json").read_text())["keys"]
    offs = (ex.ROOT / ex.RES / "Offsets.inc").read_text()
    assert mk and mk == sorted(set(mk)) and all(re.search(r"^%s_DX=" % k, offs, re.M) for k in mk), mk
    meta = json.loads((Path(t1) / "_meta.json").read_text())
    assert meta["schema"] == 1 and all(len(h) == 64 for h in meta["sources"].values())
    (Path(t1) / "apps.json").write_text("x")
    assert ex.main(["--out", t1, "--check"]) == 1                      # differs
print("test_export_ui_assets: all checks passed")
