#!/usr/bin/env python3
"""Deterministic exporter: Rainmeter skin UI source data -> JSON for the Preact UI. Stdlib only, no LLM, no network.
Run:  python3 -I tools/export_ui_assets.py [--out DIR] [--check] [--only icons,layout,frameparts,apps,orb,settings,modules,frame,guide]"""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
ROOT = TOOLS.parent
sys.path.insert(0, str(TOOLS))
import layoutlib  # noqa: E402

RES = Path("Skins/Spaceship/@Resources")
PARTS = ["Accents", "Decor", "Glass", "Lights", "Spill"]
REDACT = re.compile(r"(?i)(pass|secret|token|key|credential|gmail|calendar)")
ARITY = {"l": lambda n: n >= 4 and n % 2 == 0, "p": lambda n: n >= 4 and n % 2 == 0, "c": lambda n: n == 3,
         "a": lambda n: n in (5, 6), "e": lambda n: n == 4}
TOKEN = re.compile(r"\s+|(?P<punct>[{},=])|(?P<op>'[^']*'|\"[^\"]*\")|(?P<num>-?\d+(?:\.\d+)?)|(?P<name>[A-Za-z_][\w.]*)|(?P<bad>.)")


class ParseError(Exception):
    pass


def parse_icons(text):
    """Lua icon table -> {name: [[op, n, ...], ...]}; raises ParseError('line N: ...') on anything unexpected."""
    toks, pos = [], 0
    for ln, line in enumerate(text.split("\n"), 1):
        line = line.split("--", 1)[0]
        for m in TOKEN.finditer(line):
            if m.lastgroup:
                toks.append((ln, m.lastgroup, m.group()))
    i = 0

    def err(msg):
        raise ParseError("line %d: %s" % (toks[min(i, len(toks) - 1)][0] if toks else 0, msg))

    def peek():
        return toks[i] if i < len(toks) else (0, "eof", "")

    def take(val=None):
        nonlocal i
        t = peek()
        if t[1] == "eof" or (val is not None and t[2] != val):
            err("expected %r, got %r" % (val, t[2]))
        i += 1
        return t

    take("local"), take("I"), take("="), take("{"), take("}")
    icons = {}
    while peek()[2] != "return":
        t = take()
        if t[1] != "name" or not t[2].startswith("I.") or t[2] == "I.":
            err("expected icon name I.xxx, got %r" % t[2])
        name = t[2][2:]
        if name in icons:
            err("duplicate icon %s" % name)
        take("="), take("{")
        prims = []
        while peek()[2] != "}":
            take("{")
            op = take()
            if op[1] != "op" or op[2][1:-1] not in ARITY:
                err("unknown primitive %r in %s" % (op[2], name))
            nums = []
            while peek()[2] != "}":
                take(",")
                if peek()[2] == "}":
                    break
                n = take()
                if n[1] != "num":
                    err("bad number %r in %s" % (n[2], name))
                nums.append(float(n[2]) if "." in n[2] else int(n[2]))
            take("}")
            o = op[2][1:-1]
            if not ARITY[o](len(nums)):
                err("%s in %s has bad arity %d" % (o, name, len(nums)))
            prims.append([o] + nums)
            if peek()[2] == ",":
                take(",")
        take("}")
        if peek()[2] == ",":
            take(",")
        icons[name] = prims
    take("return"), take("I")
    if peek()[1] != "eof":
        err("trailing content %r" % peek()[2])
    return {"box": 100, "icons": icons}


def parse_ini(text):
    """Raw INI -> [[section, {key: value}], ...] in file order (';' comments and blanks skipped; later duplicate key wins)."""
    out, cur = [], None
    for ln, line in enumerate(text.splitlines(), 1):
        s = line.strip().lstrip("﻿")
        if not s or s.startswith(";"):
            continue
        if s.startswith("[") and s.endswith("]"):
            cur = {}
            out.append([s[1:-1], cur])
        elif "=" in s:
            if cur is None:
                raise ParseError("line %d: key outside any section" % ln)
            k, v = s.split("=", 1)
            cur[k.strip()] = v.strip()
        else:
            raise ParseError("line %d: not a section or key=value: %r" % (ln, s[:40]))
    return out


def parse_settings(text):
    """-> (variables without redacted keys, sorted list of redacted key names)."""
    sec = dict(parse_ini(text)).get("Variables", {})
    return ({k: v for k, v in sec.items() if not REDACT.search(k)}, sorted(k for k in sec if REDACT.search(k)))


def build_layout(root):
    L = layoutlib.load(root / "layout" / "layout.json")
    m = re.search(r"^MARGIN\s*=\s*(\d+)", (root / "tools" / "build.py").read_text(), re.M)
    if not m:
        raise ParseError("MARGIN not found in tools/build.py")
    keep = ("id", "group", "x", "y", "w", "h", "quad", "content")
    def items(k):
        return [dict({f: it[f] for f in keep if f in it}, matrix=list(layoutlib.matrix(it, L["curves"])))
                for it in L.get(k, [])]
    return {"canvas": L["canvas"], "safe_area": L["safe_area"], "taskbar": L["taskbar"], "curves": L["curves"],
            "keepouts": L["keepouts"], "zones": items("zones"), "decor": items("decor"), "overlays": items("overlays"),
            "margins": {"module": int(m.group(1)), "animationBleed": 12}}


def orb_info(d):
    names = sorted(p.name for p in d.iterdir() if p.is_file())
    pats = sorted({re.sub(r"\d+", "N", n) for n in names})
    return {"count": len(names), "first": names[0] if names else None, "last": names[-1] if names else None, "patterns": pats}


def rd(root, rel):
    return (root / rel).read_text(encoding="utf-8-sig")


def gen_icons(root):
    d = parse_icons(rd(root, RES / "Scripts/icons.lua"))
    return d, len(d["icons"]), [RES / "Scripts/icons.lua"]


def gen_layout(root):
    d = build_layout(root)
    return d, len(d["zones"]) + len(d["decor"]) + len(d["overlays"]), [Path("layout/layout.json"), Path("tools/build.py")]


def gen_frameparts(root):
    srcs = [Path("Skins/Spaceship/Frame/Parts/%s.inc" % p) for p in PARTS]
    d = {s.name: parse_ini(rd(root, s)) for s in srcs}
    return d, sum(len(v) for v in d.values()), srcs


def gen_apps(root):
    d = parse_ini(rd(root, RES / "Apps.ini"))
    return d, len(d), [RES / "Apps.ini"]


def gen_orb(root):
    base = RES / "Images/Jarvis"
    d = {"idle": orb_info(root / base / "Idle"), "active": orb_info(root / base / "Active")}
    return d, d["idle"]["count"] + d["active"]["count"], []


def gen_settings(root):
    v, red = parse_settings(rd(root, RES / "Settings.inc"))
    return {"variables": v, "redacted": red}, len(v), [RES / "Settings.inc"]


FRAME_IMAGES = ["hull", "ship", "glass_fx", "glass_fx_pic", "glass_pic", "scan", "scan_pic", "shade", "mist", "mist_pic",
                "corners", "window_mask"]


def frame_files(root):
    """{name: (hashed filename, source path)}; the hash is of the file content, so unchanged art keeps its URL."""
    out = {}
    for n in FRAME_IMAGES:
        src = RES / "Images" / (n + ".png")
        out[n] = ("%s.%s.png" % (n, hashlib.sha256((root / src).read_bytes()).hexdigest()[:8]), src)
    return out


def gen_frame(root):
    f = frame_files(root)
    return {n: v[0] for n, v in f.items()}, len(f), [v[1] for v in f.values()]


def parse_module_keys(offsets_text, geometry_texts):
    """Module keys = every <Key>_DX in Offsets.inc; must equal the keys the skins' Geometry.inc reference as DX=#<Key>_DX#."""
    a = set(re.findall(r"^(\w+)_DX\s*=", offsets_text, re.M))
    b = {m for t in geometry_texts for m in re.findall(r"^DX=#(\w+)_DX#", t, re.M)}
    if not a or a != b:
        raise ParseError("module keys differ: Offsets.inc only %s, Geometry.inc only %s" % (sorted(a - b), sorted(b - a)))
    return sorted(a)


def _plain(s):
    """Markdown inline -> plain text: links keep their label, emphasis and code marks go."""
    return re.sub(r"\*\*|`", "", re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", s)).strip()


def parse_guide(text):
    """Guide markdown -> {"sections": [{id, title, level, text}]}: headings with the prose under them; code fences,
    rules and table separators dropped, table rows flattened to 'a — b'. Ids are GitHub-style slugs, made unique."""
    sections, seen, fence = [], set(), False
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("```"):
            fence = not fence
            continue
        if fence:
            continue
        m = re.match(r"(#{1,6})\s+(.+)", line)
        if m:
            title = _plain(m.group(2))
            base = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-") or "section"
            sid, n = base, 1
            while sid in seen:
                n += 1
                sid = "%s-%d" % (base, n)
            seen.add(sid)
            sections.append({"id": sid, "title": title, "level": len(m.group(1)), "lines": []})
        elif sections and s and not re.fullmatch(r"[-*_]{3,}|\|?[\s:|-]+\|?", s):
            if s.startswith("|"):
                s = " — ".join(c.strip() for c in s.strip("|").split("|") if c.strip())
            sections[-1]["lines"].append(_plain(s))
    if fence:
        raise ParseError("unclosed code fence")
    return {"sections": [{"id": x["id"], "title": x["title"], "level": x["level"], "text": "\n".join(x["lines"])} for x in sections]}


def gen_guide(root):
    src = RES / "Docs/Spaceship-HUD-Guide.md"
    d = parse_guide(rd(root, src))
    return d, len(d["sections"]), [src]


def gen_modules(root):
    geo = sorted((root / "Skins/Spaceship").glob("*/Geometry.inc")) + sorted((root / "Skins/Spaceship").glob("*/*/Geometry.inc"))
    keys = parse_module_keys(rd(root, RES / "Offsets.inc"), [g.read_text(encoding="utf-8-sig") for g in geo])
    return {"keys": keys}, len(keys), [RES / "Offsets.inc"] + [g.relative_to(root) for g in geo]


GENS = {"icons": gen_icons, "layout": gen_layout, "frameparts": gen_frameparts, "apps": gen_apps, "orb": gen_orb,
        "settings": gen_settings, "modules": gen_modules, "frame": gen_frame, "guide": gen_guide}


def dump(obj):
    return (json.dumps(obj, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode()


def generate(root, only=None):
    """-> {filename: (bytes, items)}, sources {relpath: sha256}"""
    out, sources = {}, {}
    for name in only or GENS:
        data, n, srcs = GENS[name](root)
        if name == "frame":  # copied images beside their manifest: frame/<name>.<hash8>.png + frame/manifest.json
            out["frame/manifest.json"] = (dump(data), n)
            for fn, src in frame_files(root).values():
                out["frame/" + fn] = ((root / src).read_bytes(), 1)
        else:
            out[name + ".json"] = (dump(data), n)
        for s in srcs:
            sources[s.as_posix()] = hashlib.sha256((root / s).read_bytes()).hexdigest()
    return out, sources


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "SpaceshipApp/SpaceshipUI/src/generated"))
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--only", default="")
    a = ap.parse_args(argv)
    only = [x for x in a.only.split(",") if x]
    if set(only) - set(GENS):
        print("unknown --only: %s" % ",".join(sorted(set(only) - set(GENS))), file=sys.stderr)
        return 2
    try:
        files, sources = generate(ROOT, only)
    except (ParseError, OSError, KeyError, ValueError) as e:
        print("export failed: %s: %s" % (type(e).__name__, e), file=sys.stderr)
        return 1
    # _meta lists sources of the selected outputs only, so --only runs stay self-consistent
    files["_meta.json"] = (dump({"sources": sources, "generator": "tools/export_ui_assets.py", "schema": 1}), len(sources))
    out = Path(a.out)
    bad = 0
    if not a.check:
        out.mkdir(parents=True, exist_ok=True)
    for fn, (b, n) in sorted(files.items()):
        p = out / fn
        if not a.check:
            p.parent.mkdir(parents=True, exist_ok=True)
        same = p.is_file() and p.read_bytes() == b
        if a.check:
            if not same:
                print("%s: %s" % (fn, "differs" if p.is_file() else "missing"))
                bad = 1
            continue
        if not same:
            p.write_bytes(b)
        print("%s: %s, %d items, %d bytes" % (fn, "unchanged" if same else "written", n, len(b)))
    if "frame" in (only or GENS):  # hashed names change with the art; leftovers would pile up
        stale = [p for p in (out / "frame").glob("*.png") if "frame/" + p.name not in files]
        for p in stale:
            print("frame/%s: %s" % (p.name, "stale" if a.check else "removed"))
            if a.check:
                bad = 1
            else:
                p.unlink()
    return bad


if __name__ == "__main__":
    sys.exit(main())
