#!/usr/bin/env python3
"""rmsim - offline Rainmeter simulator + auditor for the Spaceship skin set.

It cannot replace testing in real Rainmeter, but it catches most mistakes before they reach Windows:
  * parses every skin .ini (with @Include, variables, formulas)
  * runs each module's real Lua (Lua 5.1 via lupa) against a mock SKIN/SELF API with mock sensor data
  * applies the bangs the Lua issues (!SetOption, !SetVariable, ...)
  * renders Shape / String / Image meters with their TransformationMatrix onto the 2560x1600 canvas
  * audits: undefined variables, missing files, unknown plugins/bangs/meters, Lua errors,
    malformed shapes, and ALIGNMENT - every drawn point of a zone's meters must stay inside that
    zone's curved outline (from layout.json), so modules can never overlap each other or the struts.

Usage:
  python tools/rmsim.py [--out composite.png] [--scenario full|bare|battery|stress] [--updates N] [--zones]
"""
import argparse
import json
import math
import random
import re
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, str(Path(__file__).parent))
from layoutlib import ROOT, load, shape  # noqa: E402

SKINS = ROOT / "Skins" / "Spaceship"
RES = SKINS / "@Resources"
FONTS = RES / "Fonts"

BUNDLED_PLUGINS = {"PowerPlugin", "UsageMonitor", "Win7AudioPlugin", "AudioLevel", "SysInfo", "PingPlugin",
                   "WiFiStatus", "RunCommand", "Process", "InputText", "ActionTimer"}
MEASURE_TYPES = {"Calc", "CPU", "PhysicalMemory", "NetIn", "NetOut", "FreeDiskSpace", "Uptime", "Time", "Plugin",
                 "Registry", "Script", "String", "WebParser", "Loop"}
KNOWN_BANGS = {"!setoption", "!setvariable", "!writekeyvalue", "!setvariablegroup", "!updatemeter", "!updatemeasure",
               "!redraw", "!showmeter", "!hidemeter", "!commandmeasure", "!activateconfig", "!deactivateconfig",
               "!toggleconfig", "!refresh", "!refreshgroup", "!updategroup", "!redrawgroup", "!showgroup",
               "!hidegroup", "!showfadegroup", "!hidefadegroup", "!move", "!zpos", "!draggable",
               "!clickthrough", "!keeponscreen", "!snapedges", "!setoptiongroup", "!showmetergroup",
               "!hidemetergroup", "!updatemetergroup", "!enablemeasure", "!disablemeasure",
               "!enablemeasuregroup", "!disablemeasuregroup", "!skinmenu", "!manage", "!log", "!refreshapp",
               "!setclip", "!togglemeter", "!clickthroughgroup", "!draggablegroup", "!settransparency",
               "!fadeduration", "!deactivateconfiggroup", "!hidefade", "!showfade", "!togglefade", "!show", "!hide", "!toggle"}

BUILTIN_VARS = {"CURRENTCONFIG", "CURRENTPATH", "ROOTCONFIGPATH", "SKINSPATH", "SETTINGSPATH", "PROGRAMPATH",
                "SCREENAREAWIDTH", "SCREENAREAHEIGHT", "WORKAREAWIDTH", "WORKAREAHEIGHT", "WORKAREAX", "WORKAREAY",
                "CURRENTFILE", "@", "CRLF", "PROGRAMDRIVE", "ADDONSPATH", "PLUGINSPATH", "CONFIGEDITOR",
                "CURRENTCONFIGX", "CURRENTCONFIGY", "CURRENTCONFIGWIDTH", "CURRENTCONFIGHEIGHT", "SCREENAREAX",
                "SCREENAREAY", "VSCREENAREAWIDTH", "VSCREENAREAHEIGHT"}

FONT_FILES = {
    ("rajdhani", 400): "Rajdhani-Medium.ttf", ("rajdhani", 500): "Rajdhani-Medium.ttf",
    ("rajdhani", 600): "Rajdhani-SemiBold.ttf", ("rajdhani", 700): "Rajdhani-Bold.ttf",
    ("share tech mono", 0): "ShareTechMono-Regular.ttf", ("orbitron", 0): "Orbitron.ttf",
    ("oxanium", 400): "Oxanium-Regular.ttf", ("oxanium", 500): "Oxanium-Medium.ttf",
    ("oxanium", 600): "Oxanium-SemiBold.ttf", ("oxanium", 700): "Oxanium-Bold.ttf",
    ("b612 mono", 400): "B612Mono-Regular.ttf", ("b612 mono", 500): "B612Mono-Regular.ttf",
    ("b612 mono", 600): "B612Mono-Bold.ttf", ("b612 mono", 700): "B612Mono-Bold.ttf",
    ("michroma", 0): "Michroma-Regular.ttf",
}


class Problems:
    def __init__(self):
        self.items = []

    def add(self, module, kind, msg):
        self.items.append((module, kind, msg))


# ----------------------------------------------------------------------------- INI
def read_text(path):
    raw = Path(path).read_bytes()
    if raw[:2] in (b"\xff\xfe", b"\xfe\xff"):
        return raw.decode("utf-16")
    return raw.decode("utf-8-sig", errors="replace")


def parse_ini(path, resolve_inc, probs, module):
    """Return ordered list of (section, [(key, value)]) with @Include expansion."""
    sections = []
    current = None
    for raw in read_text(path).splitlines():
        line = raw.strip()
        if not line or line.startswith(";"):
            continue
        m = re.match(r"^\[(.+)\]$", line)
        if m:
            current = (m.group(1), [])
            sections.append(current)
            continue
        if "=" not in line or current is None:
            continue
        k, v = line.split("=", 1)
        k, v = k.strip(), v.strip()
        if k.lower().startswith("@include"):
            inc = resolve_inc(v)
            if not inc or not Path(inc).exists():
                probs.add(module, "include", f"missing include {v} -> {inc}")
                continue
            for s in parse_ini(inc, resolve_inc, probs, module):
                sections.append(s)
            # keys after the include continue the section that held the @Include
            current = (current[0], current[1])
            continue
        current[1].append((k, v))
    return sections


# ----------------------------------------------------------------------------- formulas
FUNCS = {"min": min, "max": max, "round": lambda x, n=0: round(x, int(n)), "floor": math.floor, "ceil": math.ceil,
         "abs": abs, "sqrt": math.sqrt, "sin": math.sin, "cos": math.cos, "trunc": math.trunc, "clamp":
         lambda x, a, b: max(a, min(b, x)), "pi": math.pi}


def eval_formula(expr):
    e = expr.strip()
    e = re.sub(r"\bPI\b", "pi", e, flags=re.I)
    e = e.replace("^", "**")
    e = re.sub(r"(?<![<>=!])=(?!=)", "==", e)
    e = re.sub(r"\b([A-Za-z]+)\s*\(", lambda m: m.group(1).lower() + "(", e)
    # Rainmeter conditionals use C syntax ?: ; translate simple cases
    if "?" in e:
        cond, rest = e.split("?", 1)
        a, b = rest.split(":", 1)
        return eval_formula(a) if eval_formula(cond) else eval_formula(b)
    return float(eval(e, {"__builtins__": {}}, FUNCS))


def num(v, default=0.0):
    if v is None:
        return default
    v = str(v).strip()
    if not v:
        return default
    try:
        if v.startswith("("):
            return eval_formula(v)
        return float(v)
    except Exception:
        return default


# ----------------------------------------------------------------------------- mocks
def mock_value(name, opts, scenario, tick):
    """Return (number, string) for a measure."""
    rnd = random.Random(hash((name, tick)) & 0xFFFF)
    t = opts.get("measure", "")
    full = scenario != "bare"
    if t == "Plugin":
        p = opts.get("plugin", "")
        if p == "PowerPlugin":
            st = opts.get("powerstate", "").upper()
            on_batt = scenario == "battery"
            return {"PERCENT": (64, "64"), "ACLINE": (0 if on_batt else 1, ""), "LIFETIME": (11400 if on_batt else -1, ""),
                    "STATUS": (1, "")}.get(st, (0, ""))
        if p == "UsageMonitor":
            alias = opts.get("alias", "").upper()
            idx = int(num(opts.get("index", "0")))
            if alias == "CPU" and idx > 0:
                names = ["blender", "chrome", "SLDWORKS", "Code", "MATLAB", "explorer", "Discord", "obs64", "Rainmeter", "svchost"]
                return (max(1, 260 - idx * 27 + rnd.randint(0, 9)), names[(idx - 1) % len(names)])
            if alias == "RAM" and opts.get("name"):
                return (812 * 1024 * 1024, "")
            if alias == "GPU":
                return ({"stress": 97, "full": 41}.get(scenario, 12), "")
            if alias == "VRAM":
                return (5.6 * 1024 ** 3, "")
            counter = opts.get("counter", "").lower()
            if "performance" in counter:
                return (148 + rnd.randint(-5, 5), "")
            if "bytes" in counter:
                return (rnd.randint(0, 80) * 1024 * 1024, "")
            return (30, "")
        if p == "Win7AudioPlugin":
            return (42, "Speakers (Realtek(R) Audio)")
        if p == "AudioLevel":
            if opts.get("type", "").lower() == "band":
                b = int(num(opts.get("bandidx", "0")))
                return (abs(math.sin(b * 0.45 + tick)) * (0.9 - b * 0.02), "")
            return (0.4, "")
        if p == "SysInfo":
            return {"COMPUTER_NAME": (0, "BLACK-CLOVER"), "IP_ADDRESS": (0, "192.168.1.42"), "OS_VERSION": (0, "Windows 11"),
                    "NUM_PROCESSORS": (20, "20"), "USER_NAME": (0, "Senai"),
                    "IDLE_TIME": (754, "754"), "OS_BITS": (64, "64"), "NUM_MONITORS": (1, "1")}.get(opts.get("sysinfotype", "").upper(), (0, ""))
        if p == "PingPlugin":
            return (18, "18")
        if p == "WiFiStatus":
            return (82, "BLACKCLOVER-5G") if opts.get("wifiinfotype", "").upper() == "SSID" else (82, "82")
        if p == "Process":
            return (1 if "chrome" in opts.get("processname", "").lower() or "sldworks" in opts.get("processname", "").lower() else -1, "")
        if p == "RunCommand":
            prm = opts.get("parameter", "")
            for key, out in (("status.ps1", "dgpu=on\nllt=found\nhybrid=on\npower=balance\nrefresh=165\nbattery=conservation"),
                             ("upkeep.ps1", "3|4|MCAFEE|ON"), ("dev.ps1", "1|0|RUNNING|-1"), ("llt.ps1", "result=ok"),
                             ("location.ps1", ""), ("scan-apps.ps1", "apps=46"), ("hwinfo-scan.ps1", "sensors=0"),
                             ("media.ps1", "")):
                if key in prm:
                    return (0, out)
            return (0, "")
        return (0, "")
    if t == "CPU":
        return ({"stress": 93}.get(scenario, 23 + rnd.randint(0, 20)), "")
    if t == "PhysicalMemory":
        total = 32 * 1024 ** 3
        return (total if opts.get("total") == "1" else 0.46 * total, "")
    if t in ("NetIn", "NetOut"):
        return ((3.4 if t == "NetIn" else 0.4) * 1024 ** 2 * (0.5 + rnd.random()), "")
    if t == "FreeDiskSpace":
        total = 954 * 1024 ** 3
        if opts.get("drive", "").upper() == "D:":
            return (0, "") if scenario != "stress" else (500 * 1024 ** 3, "")
        return (total if opts.get("total") == "1" else (954 - 361) * 1024 ** 3, "")
    if t == "Uptime":
        return (3 * 86400 + 4 * 3600 + 1200, "3d 4:20")
    if t == "Time":
        return (0, "14:32:07" if "%H" in opts.get("format", "") else "THU 09 OCT")
    if t == "Registry":
        if not full:
            return (0, "")
        rv = opts.get("regvalue", "")
        vals = {"CpuTemp": 71.5, "GpuTemp": 64.0, "CpuPower": 38.2, "GpuPower": 61.0, "Fan1": 3120, "Fan2": 3380,
                "GpuClock": 1845, "ChargeRate": 0.0 if scenario == "battery" else 42.0, "RemainCap": 52400,
                "FullCap": 79800, "Wear": 3.1, "SsdTemp": 44}
        for k, v in vals.items():
            if name.endswith(k):
                if scenario == "battery" and k == "ChargeRate":
                    v = -54.0
                return (v, f"{v}")
        return (0, rv)
    if t == "WebParser":
        url = opts.get("url", "")
        if "thespacedevs" in url:
            return (0, '{"count":1,"results":[{"id":"x","name":"Falcon 9 Block 5 | Starlink Group 10-12","net":"2099-10-11T03:12:00Z"}]}')
        if "open-notify" in url:
            return (0, '{"iss_position": {"latitude": "21.3", "longitude": "-48.1"}, "message": "success", "timestamp": 1}')
        return (0, '{"status":"success","city":"Seattle","regionName":"Washington","countryCode":"US","lat":47.6062,"lon":-122.3321,"timezone":"America/Los_Angeles"}')
    return (0, "")


# ----------------------------------------------------------------------------- shapes
def split_args(s):
    """split on commas that are not inside parentheses"""
    out, depth, cur = [], 0, ""
    for ch in s:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        if ch == "," and depth == 0:
            out.append(cur)
            cur = ""
        else:
            cur += ch
    out.append(cur)
    return [x.strip() for x in out]


def parse_color(s, default=(255, 255, 255, 255)):
    parts = split_args(s)
    try:
        vals = [max(0, min(255, int(num(p) if p.startswith("(") else float(p)))) for p in parts]
    except ValueError:
        return default
    if len(vals) == 3:
        vals.append(255)
    return tuple(vals[:4])


def parse_path(defn):
    pts = []
    closed = False
    segs = [s.strip() for s in defn.split("|")]
    x, y = [float(v) for v in segs[0].split(",")[:2]]
    pts.append((x, y))
    for s in segs[1:]:
        if s.lower().startswith("lineto"):
            x, y = [float(v) for v in s[6:].split(",")[:2]]
            pts.append((x, y))
        elif s.lower().startswith("closepath"):
            closed = True
        else:
            raise ValueError(f"unsupported path segment '{s}'")
    return pts, closed


def parse_shape(spec, meter_opts):
    """Return dict: kind, geometry points (for audit) and draw params."""
    parts = [p.strip() for p in spec.split("|")]
    head = parts[0]
    kind, _, args = head.partition(" ")
    kind = kind.lower()
    sh = {"kind": kind, "fill": (255, 255, 255, 255), "stroke": (0, 0, 0, 255), "sw": 1.0}
    if kind == "path":
        name = args.strip()
        defn = meter_opts.get(name.lower())
        if defn is None:
            raise ValueError(f"path '{name}' not defined")
        sh["pts"], sh["closed"] = parse_path(defn)
    else:
        vals = [float(num(v)) for v in split_args(args)] if args.strip() else []
        sh["args"] = vals
        if kind == "rectangle":
            x, y, w, h = vals[:4]
            sh["pts"], sh["closed"] = [(x, y), (x + w, y), (x + w, y + h), (x, y + h)], True
        elif kind == "ellipse":
            cx, cy, rx = vals[:3]
            ry = vals[3] if len(vals) > 3 else rx
            sh["pts"] = [(cx + rx * math.cos(a / 24 * math.tau), cy + ry * math.sin(a / 24 * math.tau)) for a in range(24)]
            sh["closed"] = True
        elif kind == "line":
            sh["pts"], sh["closed"] = [(vals[0], vals[1]), (vals[2], vals[3])], False
        else:
            raise ValueError(f"unsupported shape '{kind}'")
    for mod in parts[1:]:
        k, _, v = mod.partition(" ")
        kl = k.lower()
        if kl == "fill":
            sub, _, col = v.partition(" ")
            if sub.lower() == "lineargradient":
                gdef = meter_opts.get(col.strip().lower())
                if gdef is None:
                    raise ValueError(f"gradient '{col}' not defined")
                parts = [x.strip() for x in gdef.split("|")]
                stops = []
                for st in parts[1:]:
                    c_, _, off = st.partition(";")
                    stops.append((float(off), parse_color(c_)))
                sh["grad"] = (float(num(parts[0])), stops)
                sh["fill"] = stops[0][1]
            else:
                sh["fill"] = parse_color(col)
        elif kl == "stroke":
            sub, _, col = v.partition(" ")
            sh["stroke"] = parse_color(col)
        elif kl == "strokewidth":
            sh["sw"] = float(num(v))
        elif kl in ("strokestartcap", "strokeendcap", "strokelinejoin", "strokedashes", "antialias"):
            pass
        else:
            raise ValueError(f"unsupported modifier '{mod}'")
    return sh


def tm_apply(tm, pts):
    a, b, c, d, tx, ty = tm
    return [(a * x + c * y + tx, b * x + d * y + ty) for x, y in pts]


# ----------------------------------------------------------------------------- skin model
class Skin:
    def __init__(self, ini, config, scenario, probs, var_overrides):
        self.ini, self.config, self.scenario, self.probs = Path(ini), config, scenario, probs
        self.dir = self.ini.parent
        self.vars = {"@": str(RES) + "\\", "CURRENTPATH": str(self.dir) + "\\", "SCREENAREAWIDTH": "2560",
                     "SCREENAREAHEIGHT": "1600", "WORKAREAWIDTH": "2560", "WORKAREAHEIGHT": "1552", "WORKAREAX": "0", "WORKAREAY": "0",
                     "CURRENTCONFIG": config, "ROOTCONFIGPATH": str(SKINS) + "\\", "SKINSPATH": str(SKINS.parent) + "\\",
                     "SETTINGSPATH": "/tmp/", "CRLF": "\n",
                     "SCREENAREAX@1": "0", "SCREENAREAY@1": "0", "SCREENAREAWIDTH@1": "2560", "SCREENAREAHEIGHT@1": "1600"}
        self.sections = parse_ini(ini, self.resolve_inc, probs, config)
        self.options = {}
        self.order = []
        for name, kv in self.sections:
            key = name.lower()
            if key not in self.options:
                self.options[key] = {"__name": name}
                self.order.append(key)
            for k, v in kv:
                if k.lower() in self.options[key] and key not in ("variables",):
                    probs.add(config, "duplicate", f"[{name}] {k} defined more than once")
                self.options[key][k.lower()] = v
                if key == "variables":
                    self.vars[k] = v
        self.vars.update(var_overrides)
        self.bang_log = []
        self.tick = 0

    def resolve_inc(self, v):
        v = v.replace("#@#", str(RES) + "\\").replace("#CURRENTPATH#", str(self.dir) + "\\")
        return v.replace("\\", "/")

    def var(self, name, default=None):
        for k, v in self.vars.items():
            if k.lower() == name.lower():
                return v
        return default

    def subst(self, s, depth=0, where=""):
        if s is None:
            return None
        s = s.replace("#@#", self.vars["@"])

        def rep(m):
            v = self.var(m.group(1))
            if v is None:
                if m.group(1).upper() not in BUILTIN_VARS and "@" not in m.group(1):   # NAME@n: monitor n, may not exist
                    self.probs.add(self.config, "variable", f"undefined #{m.group(1)}# in {where}")
                return m.group(0)
            return v
        out = re.sub(r"#([A-Za-z0-9_@]+)#", rep, s)
        if out != s and depth < 8 and "#" in out:
            return self.subst(out, depth + 1, where)
        return out

    def opt(self, section, key, default=None):
        sec = self.options.get(section.lower(), {})
        v = sec.get(key.lower())
        if v is None:
            style = sec.get("meterstyle")
            if style:
                for st in [x.strip() for x in style.split("|")]:
                    sv = self.options.get(st.lower(), {}).get(key.lower())
                    if sv is not None:
                        v = sv
                        break
        if v is None:
            return default
        return self.subst(v, where=f"[{section}] {key}")

    def is_measure(self, key):
        return "measure" in self.options[key]

    def is_meter(self, key):
        return "meter" in self.options[key]

    # ---- measures
    def measure_values(self):
        vals = {}
        for key in self.order:
            o = self.options[key]
            if "measure" in o and o["measure"] != "Script":
                resolved = {k: self.subst(v, where=f"[{o['__name']}] {k}") if isinstance(v, str) else v for k, v in o.items()}
                if num(resolved.get("disabled", "0")) == 1:
                    vals[key] = (0, "")
                else:
                    vals[key] = mock_value(o["__name"], resolved, self.scenario, self.tick)
        self.mvals = vals
        return vals

    # ---- bangs
    def bang(self, args):
        if not args:
            return
        if len(args) == 1 and isinstance(args[0], str) and args[0].strip().startswith("["):
            for b in re.findall(r"\[([^\[\]]*)\]", args[0]):
                parts = re.findall(r'"([^"]*)"|(\S+)', b)
                toks = [p[0] or p[1] for p in parts]
                if toks:
                    self.bang(toks)
            return
        name = str(args[0])
        lname = name.lower()
        self.bang_log.append([str(a) for a in args])
        if not lname.startswith("!"):
            return  # run command ["program" ...]
        if lname not in KNOWN_BANGS:
            self.probs.add(self.config, "bang", f"unknown bang {name}")
        a = [str(x) for x in args[1:]]
        if lname == "!setoption":
            if len(a) < 3:
                self.probs.add(self.config, "bang", f"!SetOption needs 3 args: {a}")
                return
            sec = a[0].lower()
            if sec not in self.options:
                self.probs.add(self.config, "bang", f"!SetOption on unknown section [{a[0]}]")
                return
            self.options[sec][a[1].lower()] = a[2]
        elif lname in ("!setvariable",):
            self.vars[a[0]] = a[1]
        elif lname == "!setvariablegroup":
            self.vars[a[0]] = a[1]
        elif lname in ("!showmeter", "!hidemeter"):
            if a[0].lower() not in self.options:
                self.probs.add(self.config, "bang", f"{name} on unknown meter {a[0]}")
            else:
                self.options[a[0].lower()]["hidden"] = "0" if lname == "!showmeter" else "1"
        elif lname in ("!commandmeasure",):
            if len(a) < 3 and a and a[0].lower() not in self.options:
                self.probs.add(self.config, "bang", f"!CommandMeasure on unknown measure {a[0]}")
        elif lname == "!writekeyvalue":
            if len(a) < 3:
                self.probs.add(self.config, "bang", f"!WriteKeyValue needs 3+ args: {a}")

    # ---- lua
    def run_lua(self, updates):
        script_keys = [k for k in self.order if self.options[k].get("measure") == "Script"]
        if not script_keys:
            return
        from lupa import lua51
        for sk in script_keys:
            path = self.subst(self.options[sk].get("scriptfile", ""), where="ScriptFile")
            fpath = Path(path.replace("\\", "/"))
            if not fpath.exists():
                self.probs.add(self.config, "file", f"ScriptFile missing: {path}")
                continue
            L = lua51.LuaRuntime(unpack_returned_tuples=True)
            g = L.globals()
            skin = self

            def getvar(n, d=None):
                if str(n) == "SpaceshipStrict":
                    return "1"      # lib.lua's error guard stays off, so Lua errors still reach the audits
                v = skin.var(str(n))
                if v is None:
                    return d
                return skin.subst(v, where=f"GetVariable({n})")

            def getmeasure(n):
                k = str(n).lower()
                if k in skin.options and "measure" in skin.options[k]:
                    return k
                return None

            def mval(k):
                return float(skin.mvals.get(k, (0, ""))[0])

            def msval(k):
                v = skin.mvals.get(k, (0, ""))
                return str(v[1]) if v[1] != "" else (str(int(v[0])) if float(v[0]).is_integer() else str(v[0]))

            def bang(*args):
                skin.bang(list(args))

            def getopt(n, d=None):
                v = skin.opt(sk, str(n))
                return d if v is None else v

            def replacevars(s):
                return skin.subst(str(s))

            def parseformula(s):
                return num(str(s))

            g.py_getvar, g.py_getmeasure, g.py_mval, g.py_msval = getvar, getmeasure, mval, msval
            g.py_bang, g.py_getopt, g.py_replace, g.py_formula = bang, getopt, replacevars, parseformula
            L.execute(r"""
              local _dofile, _open = dofile, io.open
              dofile = function(p) return _dofile((string.gsub(p, '\\', '/'))) end
              io.open = function(p, m) return _open((string.gsub(p, '\\', '/')), m) end
              local M = {}
              M.__index = M
              function M:GetValue() return py_mval(self.k) end
              function M:GetStringValue() return py_msval(self.k) end
              function M:GetRelativeValue() return py_mval(self.k) / 100 end
              SKIN = {}
              function SKIN:GetVariable(n, d) return py_getvar(n, d) end
              function SKIN:GetMeasure(n) local k = py_getmeasure(n); if not k then return nil end; return setmetatable({k = k}, M) end
              function SKIN:GetMeter(n) return {} end
              function SKIN:Bang(...) py_bang(...) end
              function SKIN:ReplaceVariables(s) return py_replace(s) end
              function SKIN:ParseFormula(s) return py_formula(s) end
              function SKIN:MakePathAbsolute(s) return s end
              SELF = {}
              function SELF:GetOption(n, d) return py_getopt(n, d) end
              function SELF:GetNumberOption(n, d) return tonumber(py_getopt(n, d)) or d end
            """)
            src = fpath.read_text()
            try:
                L.execute(src)
                if L.globals().Initialize:
                    L.globals().Initialize()
                for i in range(updates):
                    self.tick = i
                    self.measure_values()
                    if L.globals().Update:
                        L.globals().Update()
                # fire FinishAction callbacks (web / script results) with the mock outputs, then update again
                for key in self.order:
                    fa = self.options[key].get("finishaction", "")
                    for fn in re.findall(r'!CommandMeasure\s+mScript\s+"([A-Za-z_]+\(\))"', fa):
                        L.execute(fn)
                self.measure_values()
                if L.globals().Update:
                    L.globals().Update()
                self.lua = L
            except Exception as e:  # noqa: BLE001
                self.probs.add(self.config, "lua", f"{fpath.name}: {str(e).splitlines()[0][:300]}")
                self.lua = None

    def call(self, fn):
        """Invoke a Lua function by name for interaction tests, e.g. 'OnClick(1,2)'."""
        if getattr(self, "lua", None):
            try:
                self.lua.execute(fn)
            except Exception as e:  # noqa: BLE001
                self.probs.add(self.config, "lua", f"{fn}: {str(e).splitlines()[0][:300]}")

    # ---- geometry / rendering
    def window_pos(self):
        act = self.opt("Rainmeter", "OnRefreshAction", "") or ""
        m = re.search(r'\[!Move\s+"([^"]+)"\s+"([^"]+)"\]', act)
        if not m:
            return 0.0, 0.0
        return num(m.group(1)), num(m.group(2))

    def meters(self):
        return [k for k in self.order if self.is_meter(k)]


def font_for(face, weight, size_px):
    face = (face or "rajdhani").lower()
    w = int(num(weight, 600))
    f = FONT_FILES.get((face, min((400, 500, 600, 700), key=lambda x: abs(x - w)))) or FONT_FILES.get((face, 0))
    if not f:
        f = "Rajdhani-SemiBold.ttf"
    return ImageFont.truetype(str(FONTS / f), max(1, int(round(size_px))))


def render_skin(skin, canvas, audit_zones, probs, draw_zone_outlines=False):
    wx, wy = skin.window_pos()
    sc = num(skin.var("Scale", "1"))
    for key in skin.meters():
        o = skin.options[key]
        name = o["__name"]
        if num(skin.opt(name, "Hidden", "0")) == 1:
            continue
        mtype = skin.opt(name, "Meter")
        tm_raw = skin.opt(name, "TransformationMatrix")
        tm = (1, 0, 0, 1, 0, 0)
        if tm_raw:
            vals = [num(v) for v in tm_raw.split(";")]
            if len(vals) != 6:
                probs.add(skin.config, "meter", f"[{name}] TransformationMatrix needs 6 values")
            else:
                tm = tuple(vals)
        groups = [g.strip() for g in (skin.opt(name, "Group", "") or "").split("|")]
        zone_idx = next((int(g[4:]) for g in groups if g.startswith("Zone") and g[4:].isdigit()), None)
        zone_id = skin.var(f"Z{zone_idx}") if zone_idx else None
        mx, my = num(skin.opt(name, "X", "0")), num(skin.opt(name, "Y", "0"))

        def to_canvas(pts):
            return [(wx + x, wy + y) for x, y in tm_apply(tm, pts)]

        def audit(pts, what, pad=0):
            if not zone_id or zone_id not in audit_zones:
                return
            poly = audit_zones[zone_id]
            for (x, y) in pts:
                if not inside_grown(poly, (x / sc, y / sc), 4 + pad):
                    probs.add(skin.config, "align", f"[{name}] {what} at ({x / sc:.0f},{y / sc:.0f}) leaves zone {zone_id}")
                    return

        if mtype == "Shape":
            mopts = {k: skin.subst(v) for k, v in o.items()}
            keys = sorted([k for k in o if re.fullmatch(r"shape\d*", k)], key=lambda k: int(k[5:] or 1))
            for sk in keys:
                spec = skin.subst(o[sk])
                try:
                    sh = parse_shape(spec, mopts)
                except Exception as e:  # noqa: BLE001
                    probs.add(skin.config, "shape", f"[{name}] {sk}: {e}")
                    continue
                pts = [(mx + x, my + y) for x, y in sh["pts"]]
                cpts = to_canvas(pts)
                if name not in ("Bounds",) and not name.startswith("H"):
                    visible = sh["fill"][3] > 1 or (sh["sw"] > 0 and sh["stroke"][3] > 0)
                    # soft light halos (fill-only, faint) are allowed to bloom past the zone edge
                    halo = (sh["sw"] == 0 or sh["stroke"][3] == 0) and sh["fill"][3] <= 40
                    if visible and not halo:
                        audit(cpts, sk, pad=sh["sw"] / 2 * 0 + (2 if sh["sw"] > 3 else 0))
                draw_shape(canvas, sh, cpts, sc, tm)
        elif mtype == "String":
            txt = skin.opt(name, "Text", "") or ""
            size_pt = num(skin.opt(name, "FontSize", "10"))
            px = size_pt * 96 / 72
            font = font_for(skin.opt(name, "FontFace"), skin.opt(name, "FontWeight", "400"), px)
            col = parse_color(skin.opt(name, "FontColor", "255,255,255"))
            align = (skin.opt(name, "StringAlign", "LeftTop") or "LeftTop").lower()
            if txt == "":
                continue
            l, t, r, b = font.getbbox(txt)
            tw, th = r, font.getmetrics()[0] + font.getmetrics()[1]
            clipw = num(skin.opt(name, "W", "0"))
            if num(skin.opt(name, "ClipString", "0")) >= 1 and clipw > 0:
                tw = min(tw, clipw)
            ox = mx - (tw if align.startswith("right") else tw / 2 if align.startswith("center") else 0)
            oy = my - (th if align.endswith("bottom") else th / 2 if align.endswith("center") and align != "center" else 0)
            if align == "center":
                oy = my
            box = [(ox, oy + t), (ox + tw, oy + t), (ox + tw, oy + b), (ox, oy + b)]
            audit(to_canvas(box), f"text '{txt[:20]}'")
            shadow = None
            m = re.search(r"Shadow\s*\|\s*([-\d.]+)\s*\|\s*([-\d.]+)\s*\|\s*([-\d.]+)\s*\|\s*([^|]+)",
                          skin.opt(name, "InlineSetting", "") or "")
            if m and num(m.group(3)) > 0:
                shadow = (num(m.group(1)), num(m.group(2)), num(m.group(3)), parse_color(m.group(4).strip()))
            draw_text(canvas, txt, font, col, ox, oy, tm, wx, wy, tw, shadow)
        elif mtype == "Image":
            img = skin.opt(name, "ImageName", "")
            p = Path((img or "").replace("\\", "/"))
            if not p.exists():
                probs.add(skin.config, "file", f"[{name}] image missing {img}")
                continue
            im = Image.open(p).convert("RGBA")
            w, h = int(num(skin.opt(name, "W", str(im.width)))), int(num(skin.opt(name, "H", str(im.height))))
            if (w, h) != im.size:
                im = im.resize((w, h))
            cm = [skin.opt(name, f"ColorMatrix{i}") for i in range(1, 6)]
            if any(cm):
                # Rainmeter / GDI+ colour matrix: [r g b a 1] x M (rows 1-4 = inputs, row 5 = offsets)
                M = np.eye(5, dtype=np.float32)
                for i, row in enumerate(cm):
                    if row:
                        M[i] = [num(v) for v in row.split(";")][:5]
                arr = np.asarray(im, dtype=np.float32) / 255
                vec = np.concatenate([arr, np.ones(arr.shape[:2] + (1,), np.float32)], -1)
                out = np.clip(vec @ M, 0, 1)[..., :4]
                im = Image.fromarray((out * 255).astype(np.uint8), "RGBA")
            tint = skin.opt(name, "ImageTint")
            alpha = num(skin.opt(name, "ImageAlpha", "255"), 255)
            if tint or alpha < 255:
                tc = parse_color(tint) if tint else (255, 255, 255, 255)
                r, g, b, a = im.split()
                r = r.point(lambda v: v * tc[0] // 255)
                g = g.point(lambda v: v * tc[1] // 255)
                b = b.point(lambda v: v * tc[2] // 255)
                a = a.point(lambda v: int(v * tc[3] / 255 * alpha / 255))
                im = Image.merge("RGBA", (r, g, b, a))
            (px, py), = tm_apply(tm, [(mx, my)])
            canvas.alpha_composite(im, (int(wx + px), int(wy + py)))
        else:
            probs.add(skin.config, "meter", f"[{name}] unsupported meter type {mtype}")


def starfield(w, h, seed=3):
    """stand-in for the animated wallpaper behind the cockpit"""
    from PIL import ImageFilter
    rnd = random.Random(seed)
    bg = Image.new("RGBA", (w, h))
    d = ImageDraw.Draw(bg)
    for y in range(h):
        t = y / h
        d.line([(0, y), (w, y)], fill=(int(6 - 4 * t), int(10 - 7 * t), int(26 - 18 * t), 255))
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


def inside_grown(poly, p, pad):
    # point within pad px of a convex polygon
    x, y = p
    n = len(poly)
    inside = True
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        cross = (x2 - x1) * (y - y1) - (y2 - y1) * (x - x1)
        if cross < 0:
            inside = False
            break
    if inside:
        return True
    # distance to edges
    best = 1e9
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        dx, dy = x2 - x1, y2 - y1
        t = max(0, min(1, ((x - x1) * dx + (y - y1) * dy) / (dx * dx + dy * dy or 1)))
        best = min(best, math.hypot(x - (x1 + t * dx), y - (y1 + t * dy)))
    return best <= pad


def draw_shape(canvas, sh, cpts, sc, tm):
    xs, ys = [p[0] for p in cpts], [p[1] for p in cpts]
    pad = int(sh["sw"] * 2 + 4)
    x0, y0 = max(0, int(min(xs)) - pad), max(0, int(min(ys)) - pad)
    x1, y1 = min(canvas.width, int(max(xs)) + pad + 1), min(canvas.height, int(max(ys)) + pad + 1)
    if x1 <= x0 or y1 <= y0:
        return
    cpts = [(x - x0, y - y0) for x, y in cpts]
    layer = Image.new("RGBA", (x1 - x0, y1 - y0), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    det = abs(tm[0] * tm[3] - tm[1] * tm[2]) ** 0.5
    sw = sh["sw"] * det
    if sh["kind"] == "ellipse":
        cx, cy = sum(p[0] for p in cpts) / len(cpts), sum(p[1] for p in cpts) / len(cpts)
        pts = cpts + [cpts[0]]
    else:
        pts = cpts + ([cpts[0]] if sh.get("closed") else [])
    if sh.get("grad") and sh.get("closed") and len(cpts) >= 3:
        ang, stops = sh["grad"]
        # gradient runs across the shape's bounding box along the angle (0 = left->right, 90 = top->bottom)
        ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
        proj = [x * ca + y * sa for x, y in cpts]
        p0, p1 = min(proj), max(proj)
        n = 256
        lut = []
        for i in range(n):
            t = i / (n - 1)
            lo = max([s_ for s_ in stops if s_[0] <= t] or [stops[0]], key=lambda s_: s_[0])
            hi = min([s_ for s_ in stops if s_[0] >= t] or [stops[-1]], key=lambda s_: s_[0])
            k = 0 if hi[0] == lo[0] else (t - lo[0]) / (hi[0] - lo[0])
            lut.append(tuple(int(lo[1][j] + (hi[1][j] - lo[1][j]) * k) for j in range(4)))
        W, Hh = layer.size
        ys_, xs_ = np.mgrid[0:Hh, 0:W]
        t = np.clip(((xs_ * ca + ys_ * sa) - p0) / max(1e-6, p1 - p0), 0, 1)
        idx = (t * (n - 1)).astype(np.int32)
        grad = Image.fromarray(np.array(lut, dtype=np.uint8)[idx], "RGBA")
        m = Image.new("L", layer.size, 0)
        ImageDraw.Draw(m).polygon(cpts, fill=255)
        a = Image.composite(grad, layer, m)
        layer = a
    elif sh["fill"][3] > 0 and (sh.get("closed") or sh["kind"] == "path") and len(cpts) >= 3:
        # Direct2D fills open path figures too (implicitly closed); Fill defaults to white
        d.polygon(cpts, fill=sh["fill"])
    if sw > 0 and sh["stroke"][3] > 0 and len(pts) >= 2:
        d = ImageDraw.Draw(layer)
        d.line(pts, fill=sh["stroke"], width=max(1, int(round(sw))), joint="curve")
    canvas.alpha_composite(layer, (x0, y0))


def draw_text(canvas, txt, font, col, ox, oy, tm, wx, wy, clipw, shadow=None):
    pad = 4 + (int(shadow[2] * 2) if shadow else 0)
    tw = int(clipw) + pad * 2
    th = int(font.size * 1.6) + pad * 2
    tile = Image.new("RGBA", (max(1, tw), max(1, th)), (0, 0, 0, 0))
    if shadow:
        # D2D-style text shadow: blurred copy of the glyphs in the shadow colour, under the text
        sdx, sdy, blur, scol = shadow
        glow = Image.new("RGBA", tile.size, (0, 0, 0, 0))
        ImageDraw.Draw(glow).text((pad + sdx, pad + sdy), txt, font=font, fill=scol[:3] + (255,))
        glow = glow.filter(ImageFilter.GaussianBlur(blur / 2))
        ga = glow.split()[3].point(lambda v: min(255, int(v * scol[3] / 255 * 1.6)))
        glow.putalpha(ga)
        tile.alpha_composite(glow)
    ImageDraw.Draw(tile).text((pad, pad), txt, font=font, fill=col)
    if clipw < font.getbbox(txt)[2]:
        tile = tile.crop((0, 0, int(clipw) + pad, th))
    a, b, c, d, tx, ty = tm
    # tile pixel (u,v) -> skin (ox-pad+u, oy-pad+v) -> canvas via tm + window
    X0, Y0 = ox - pad, oy - pad
    # forward affine canvas = M * (X0+u, Y0+v) + T ; we need inverse for PIL
    det = a * d - b * c
    ia, ib, ic, id_ = d / det, -c / det, -b / det, a / det
    # canvas point (X,Y): skin = inv(M) * (X - wx - tx, Y - wy - ty); u = skin.x - X0
    cx0 = -(wx + tx)
    cy0 = -(wy + ty)
    coeffs = (ia, ib, ia * cx0 + ib * cy0 - X0, ic, id_, ic * cx0 + id_ * cy0 - Y0)
    layer = tile.transform(canvas.size, Image.AFFINE, coeffs, resample=Image.BILINEAR)
    canvas.alpha_composite(layer)


# ----------------------------------------------------------------------------- driver
def discover():
    out = []
    for ini in sorted(SKINS.rglob("*.ini")):
        if "@Resources" in ini.parts:
            continue
        rel = ini.parent.relative_to(SKINS)
        out.append(("Spaceship\\" + "\\".join(rel.parts), ini))
    return out


def lua_syntax_check(probs):
    from lupa import lua51
    L = lua51.LuaRuntime()
    for f in sorted((RES / "Scripts").glob("*.lua")) + [RES / "Data" / "zones.lua"]:
        try:
            L.execute("local f, e = loadstring(...); if not f then error(e) end", f.read_text())
        except Exception as e:  # noqa: BLE001
            probs.add("Scripts", "lua-syntax", f"{f.name}: {str(e).splitlines()[0]}")
        if any(ord(ch) > 127 for ch in f.read_text()):
            probs.add("Scripts", "encoding", f"{f.name}: non-ASCII characters (save as UTF-16 LE or remove)")
    for f in list(SKINS.rglob("*.ini")) + list(SKINS.rglob("*.inc")):
        if any(ord(ch) > 127 for ch in read_text(f)):
            probs.add(str(f.relative_to(SKINS)), "encoding", "non-ASCII characters in ini/inc")


def static_checks(skin, probs):
    for key in skin.order:
        o = skin.options[key]
        name = o["__name"]
        if "measure" in o:
            mt = o["measure"]
            if mt not in MEASURE_TYPES:
                probs.add(skin.config, "measure", f"[{name}] unknown Measure={mt}")
            if mt == "Plugin" and o.get("plugin") not in BUNDLED_PLUGINS:
                probs.add(skin.config, "plugin", f"[{name}] plugin {o.get('plugin')} is not bundled with Rainmeter")
        if "meter" in o:
            st = o.get("meterstyle")
            if st:
                for s in st.split("|"):
                    if s.strip().lower() not in skin.options:
                        probs.add(skin.config, "style", f"[{name}] MeterStyle {s.strip()} not found")
            mn = o.get("measurename")
            if mn and mn.lower() not in skin.options:
                probs.add(skin.config, "measure", f"[{name}] MeasureName {mn} not found")
        for k, v in o.items():
            if k.startswith("__"):
                continue
            skin.subst(v, where=f"[{name}] {k}")
            for ref in re.findall(r'!CommandMeasure\s+"?([A-Za-z0-9_]+)"?\s+"[^"]*"(\s+"[^"]+")?', v):
                if not ref[1] and ref[0].lower() not in skin.options:
                    probs.add(skin.config, "bang", f"[{name}] {k}: !CommandMeasure on unknown measure {ref[0]}")


MOCK_START = """7-Zip File Manager|{6D809377-6AF0-444B-8957-A3773F02200E}\\7-Zip\\7zFM.exe
Adobe Acrobat|{6D809377}\\Adobe\\Acrobat DC\\Acrobat\\Acrobat.exe
ArcGIS Pro|{6D809377}\\ArcGIS\\Pro\\bin\\ArcGISPro.exe
Workbench 2025 R1|{6D809377}\\ANSYS Inc\\v251\\Framework\\bin\\Win64\\RunWB2.exe
Bitwarden|com.bitwarden.desktop
Blender 5.2|{6D809377}\\Blender Foundation\\Blender 5.2\\blender-launcher.exe
Claude|AnthropicPBC.Claude_x!Claude
CrystalDiskInfo|{7C5A40EF}\\CrystalDiskInfo\\DiskInfo64.exe
Discord|com.squirrel.Discord.Discord
Ditto|{6D809377}\\Ditto\\Ditto.exe
Everything|{6D809377}\\Everything\\Everything.exe
Google Chrome|Chrome
HWiNFO64|{6D809377}\\HWiNFO64\\HWiNFO64.exe
KiCad 10.0|{6D809377}\\KiCad\\10.0\\bin\\kicad.exe
Lenovo Legion Toolkit|{6D809377}\\LenovoLegionToolkit\\Lenovo Legion Toolkit.exe
Lively Wallpaper|rocksdanister.LivelyWallpaper
MATLAB R2026b|{6D809377}\\MATLAB\\R2026b\\bin\\matlab.exe
Microsoft Clipchamp|Clipchamp.Clipchamp_yxz26nhyzhsrt!App
Microsoft Teams|MSTeams_8wekyb3d8bbwe!MSTeams
Microsoft To Do|Microsoft.Todos_8wekyb3d8bbwe!App
Notepad++|{6D809377}\\Notepad++\\notepad++.exe
NVIDIA App|NVIDIACorp.NVIDIAApp
OBS Studio|{6D809377}\\obs-studio\\bin\\64bit\\obs64.exe
Obsidian|md.obsidian
Octave (GUI)|{6D809377}\\GNU Octave\\octave.vbs
Ollama|{6D809377}\\Ollama\\ollama app.exe
OpenRocket|{6D809377}\\OpenRocket\\OpenRocket.exe
Outlook (new)|Microsoft.OutlookForWindows_8wekyb3d8bbwe!Microsoft.OutlookforWindows
ParaView 6.1.1|{6D809377}\\ParaView 6.1.1\\bin\\paraview.exe
PowerToys (Preview)|{6D809377}\\PowerToys\\PowerToys.exe
Rainmeter|{6D809377}\\Rainmeter\\Rainmeter.exe
Raspberry Pi Imager|{6D809377}\\Raspberry Pi Imager\\rpi-imager.exe
RASAero II|{7C5A40EF}\\RASAero II\\RASAero II.exe
Rufus|Rufus.exe
ShareX|{6D809377}\\ShareX\\ShareX.exe
SOLIDWORKS 2026|{6D809377}\\SOLIDWORKS Corp\\SOLIDWORKS\\SLDWORKS.exe
SOLIDWORKS Visualize 2026|{6D809377}\\SOLIDWORKS Corp\\Visualize\\Visualize.exe
Terminal|Microsoft.WindowsTerminal_8wekyb3d8bbwe!App
Ubuntu|CanonicalGroupLimited.Ubuntu_79rhkp1fndgsc!ubuntu
Visual Studio Code|Microsoft.VisualStudioCode
VLC media player|{6D809377}\\VideoLAN\\VLC\\vlc.exe
Windhawk|{6D809377}\\Windhawk\\windhawk.exe
WinDirStat|{6D809377}\\WinDirStat\\WinDirStat.exe
Wireshark|{6D809377}\\Wireshark\\Wireshark.exe
Zoom Workplace|zoom.us.Zoom Video Meetings
Zotero|{6D809377}\\Zotero\\zotero.exe
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "docs" / "sim-composite.png"))
    ap.add_argument("--scenario", default="full", choices=["full", "bare", "battery", "stress"])
    ap.add_argument("--updates", type=int, default=3)
    ap.add_argument("--zones", action="store_true", help="draw zone outlines on top")
    ap.add_argument("--wallpaper", help="image to use behind the cockpit")
    ap.add_argument("--only", help="substring filter on config names")
    ap.add_argument("--interact", action="store_true", help="also fire every click/scroll handler once")
    ap.add_argument("--set", action="append", default=[], metavar="VAR=VALUE", help="override a skin variable (repeatable)")
    args = ap.parse_args()

    start_file = RES / "Data" / "StartApps.txt"
    mock_start = not start_file.exists()
    if mock_start:
        start_file.write_text(MOCK_START)
    icon_dir = RES / "Icons"
    mock_icons = not icon_dir.exists()
    if mock_icons:
        make_mock_icons(icon_dir)
    try:
        _run(args)
    finally:
        if mock_start:
            start_file.unlink()
        if mock_icons:
            for f in icon_dir.glob("*"):
                f.unlink()
            icon_dir.rmdir()


def make_mock_icons(folder):
    """stand-ins for Scripts/app-icons.ps1 output (real app icons are extracted on Windows): each app's line
    icon filled in grey, 128 px, plus the blurred glow silhouette"""
    from lupa import lua51
    folder.mkdir()
    L = lua51.LuaRuntime()
    icons = L.execute(open(RES / "Scripts" / "icons.lua", encoding="utf-8").read())
    apps = {}
    cur = None
    for line in open(RES / "Apps.ini", encoding="utf-8", errors="replace"):
        m = re.match(r"\[App\.(.+)\]", line.strip())
        if m:
            cur = m.group(1)
        elif cur and line.startswith("Icon="):
            apps[cur] = line.split("=", 1)[1].strip()
    done = []
    for app, icon in apps.items():
        prims = icons[icon]
        if prims is None:
            continue
        big = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
        d = ImageDraw.Draw(big)
        P = lambda x, y: (56 + x * 4, 56 + y * 4)  # noqa: E731
        for prim in prims.values():
            v = list(prim.values())
            kind, nums = v[0], [float(x) for x in v[1:]]
            pts = [P(nums[i], nums[i + 1]) for i in range(0, len(nums) - 1, 2)]
            if kind == "p":
                d.polygon(pts, fill=(120, 120, 120, 255), outline=(255, 255, 255, 255), width=10)
            elif kind == "l":
                d.line(pts, fill=(235, 235, 235, 255), width=10, joint="curve")
            elif kind in ("c", "e", "a"):
                cx, cy = P(nums[0], nums[1])
                rx = nums[2] * 4
                ry = (nums[3] if kind == "e" else (nums[5] if kind == "a" and len(nums) > 5 else nums[2])) * 4
                if kind == "a":
                    d.arc([cx - rx, cy - ry, cx + rx, cy + ry], nums[3], nums[4], fill=(235, 235, 235, 255), width=10)
                else:
                    d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=(60, 60, 60, 255) if kind == "c" else None,
                              outline=(255, 255, 255, 255), width=10)
        im = big.resize((128, 128), Image.LANCZOS)
        im.save(folder / f"{app}.png")
        a = im.split()[3].filter(ImageFilter.GaussianBlur(6))
        glow = Image.new("RGBA", im.size, (255, 255, 255, 0))
        glow.putalpha(a.point(lambda x: min(255, int(x * 1.33))))
        glow.save(folder / f"{app}_glow.png")
        done.append(app)
    (folder / "_index.txt").write_text("\n".join(done))


def _run(args):
    layout = load()
    audit_zones = {z["id"]: shape(z, layout["curves"]) for z in layout["zones"]}
    probs = Problems()
    lua_syntax_check(probs)

    overrides = {}
    if args.scenario in ("full", "battery", "stress"):
        for i, k in enumerate(["CpuTemp", "GpuTemp", "CpuPower", "GpuPower", "Fan1", "Fan2", "GpuClock", "ChargeRate",
                               "RemainCap", "FullCap", "Wear", "SsdTemp"]):
            overrides[f"HW_{k}"] = str(i)
    if args.scenario == "stress":
        overrides["PerfTier"] = "2"
    for kv in args.set:
        k, _, v = kv.partition("=")
        overrides[k.strip()] = v.strip()

    if args.wallpaper:
        canvas = Image.open(args.wallpaper).convert("RGBA").resize((2560, 1600))
    else:
        canvas = starfield(2560, 1600)
    skins = []
    for config, ini in discover():
        if args.only and args.only.lower() not in config.lower():
            continue
        if config.endswith("Overlay\\Control") or config.endswith("Overlay\\Drawer"):
            continue  # transient overlays rendered separately below
        sk = Skin(ini, config, args.scenario, probs, overrides)
        static_checks(sk, probs)
        sk.measure_values()
        sk.run_lua(args.updates)
        if args.interact and getattr(sk, "lua", None):
            for k in sk.order:
                if k.startswith("h") and re.fullmatch(r"h\d+_\d+", k):
                    z, h = k[1:].split("_")
                    for fn in (f"OnHover({z},{h},1)", f"OnScroll({z},{h},1)", f"OnHover({z},{h},0)"):
                        sk.call(fn)
            sk.measure_values()
            sk.call("Update()")
        skins.append(sk)
    # Frame first, then the rest in order
    skins.sort(key=lambda s: 0 if s.config.endswith("Frame") else 1)
    for sk in skins:
        render_skin(sk, canvas, audit_zones, probs)
    if args.zones:
        d = ImageDraw.Draw(canvas)
        for zid, poly in audit_zones.items():
            d.line(poly + [poly[0]], fill=(255, 200, 0, 160), width=1)
    canvas.convert("RGB").save(args.out)

    # overlays rendered on their own images
    for name in ("Drawer", "Control"):
        ini = SKINS / "Overlay" / name / f"{name}.ini"
        if ini.exists() and (not args.only or args.only.lower() in name.lower()):
            sk = Skin(ini, f"Spaceship\\Overlay\\{name}", args.scenario, probs, overrides)
            static_checks(sk, probs)
            sk.measure_values()
            sk.run_lua(args.updates)
            if args.interact and getattr(sk, "lua", None):
                for fn in ("OnClick(1,1)", "OnClick(1,2)", "OnClick(1,3)"):
                    sk.call(fn)
            ov = Image.open(args.out).convert("RGBA")
            render_skin(sk, ov, audit_zones, probs)
            ov.convert("RGB").save(Path(args.out).with_name(Path(args.out).stem + f"-{name.lower()}.png"))

    by_kind = {}
    for mod, kind, msg in probs.items:
        by_kind.setdefault(kind, []).append(f"{mod}: {msg}")
    for kind, lst in sorted(by_kind.items()):
        print(f"== {kind} ({len(lst)})")
        seen = set()
        for m in lst:
            if m not in seen:
                print("  ", m)
                seen.add(m)
    print(f"rendered {len(skins)} modules -> {args.out}; {len(probs.items)} problems")
    sys.exit(1 if probs.items else 0)


if __name__ == "__main__":
    main()
