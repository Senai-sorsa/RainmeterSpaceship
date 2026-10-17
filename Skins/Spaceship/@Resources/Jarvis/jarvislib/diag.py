"""diag: moved verbatim from jarvis.py (refactor). See JARVIS-Repair-Plan.txt, REFACTOR."""
import ctypes
import json
import os
import re
import shutil
import subprocess
import threading
import time
from .audio import speakers
from .base import LAST_ERR, MEMORYSTATUSEX, NO_WINDOW, SYSTEM_POWER_STATUS, WAKE_OFF, log, read_kv, setting, settings
from .calc import clock, unit
from .gpu import gpu
from .reminders import load_reminders, span


# the HWiNFO sensors the HUD shows: Settings.inc key (the sensor's number, -1 = not mapped), spoken name, unit
HW_LINES = (("HW_CpuTemp", "CPU temperature", "C"), ("HW_GpuTemp", "GPU temperature", "C"), ("HW_CpuPower", "CPU power", "W"),
            ("HW_GpuPower", "GPU power", "W"), ("HW_Fan1", "Fan 1", "RPM"), ("HW_Fan2", "Fan 2", "RPM"),
            ("HW_SsdTemp", "SSD temperature", "C"))


def hw_value(index):
    """One HWiNFO reading, from the same registry values HWiNFO.inc shows on the HUD. Not there = OSError."""
    import winreg
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"SOFTWARE\HWiNFO64\VSB") as key:
        return float(winreg.QueryValueEx(key, f"ValueRaw{index}")[0])


def cpu_times():
    idle, kernel, user = ctypes.c_ulonglong(), ctypes.c_ulonglong(), ctypes.c_ulonglong()
    if not ctypes.windll.kernel32.GetSystemTimes(ctypes.byref(idle), ctypes.byref(kernel), ctypes.byref(user)):
        raise OSError("GetSystemTimes failed")
    return idle.value, kernel.value + user.value              # kernel time includes the idle time


def sensors():
    """Readings the HUD shows that context() leaves out. Takes about 0.2 s (two CPU samples), so a turn reads it on a
    thread while you speak. Each source stands alone: one that is missing or fails costs its own line only."""
    lines, st = [], settings()

    def part(fn):
        try:
            lines.extend(fn())
        except Exception:
            pass

    def hw(key, name, unit):
        n = int(float(st.get(key, "-1")))
        return [f"{name}: {hw_value(n):.0f} {unit}"] if n >= 0 else []

    def cpu():
        idle0, all0 = cpu_times()
        time.sleep(0.2)
        idle1, all1 = cpu_times()
        return [f"CPU load: {100 * (1 - (idle1 - idle0) / (all1 - all0)):.0f}%"]

    def card():
        if not gpu():                                         # asking a sleeping card for numbers would wake it
            return []
        r = subprocess.run(["nvidia-smi", "--query-gpu=utilization.gpu,memory.used,memory.total",
                            "--format=csv,noheader,nounits"], creationflags=NO_WINDOW, capture_output=True, text=True, timeout=2)
        if r.returncode:
            return []
        load, used, total = (float(x) for x in r.stdout.splitlines()[0].split(","))
        return [f"GPU load: {load:.0f}%, video memory {used / 1024:.1f} of {total / 1024:.0f} GB in use"]

    def sound():
        is_muted, percent = speakers()
        return [f"Speaker volume: {percent}%" + (" (muted)" if is_muted else "")]

    def panel():
        kv = dict(re.findall(r"^(T|BRIGHT|MIC|MICMUTE) (-?\d+)", read_kv("sys.txt"), re.M))
        if time.time() - int(kv.get("T", 0)) > 30:            # the HUD is off: old numbers are not current numbers
            return []
        out = [f"Screen brightness: {kv['BRIGHT']}%"] if int(kv.get("BRIGHT", -1)) >= 0 else []
        if int(kv.get("MIC", -1)) >= 0:
            out.append(f"Microphone level: {kv['MIC']}%" + (" (muted)" if kv.get("MICMUTE") == "1" else ""))
        return out

    def disk():
        drive = os.environ.get("SystemDrive", "C:")
        use = shutil.disk_usage(drive + "\\")
        return [f"Disk {drive} {use.free / 2**30:.0f} GB free of {use.total / 2**30:.0f} GB"]

    def pending():                                            # what kind and when, never the label: the text stays in its file
        items, now = load_reminders(), time.time()
        each = [f"timer with {span(r[0] - now)} left" if r[2] == "timer" else
                f"{'alarm' if r[3] == 'alarm' else 'reminder'} at {clock(r[0], now)}" for r in items[:5]]
        return [f"Pending: {'; '.join(each) or 'no alarms, reminders or timers'}" + (f"; and {len(items) - 5} more" if len(items) > 5 else "")]
    for line in HW_LINES:
        part(lambda: hw(*line))
    for fn in (cpu, card, sound, panel, disk, pending):
        part(fn)
    return "\n".join(lines)


# "what is wrong with my PC?": diag.ps1 reads, this file adds up and names. Nothing spoken ever reaches the PowerShell arguments.
PS1 = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "diag.ps1")
PARTS = ("processes", "logs", "network", "system")

# event (provider, id) -> plain words. Only these are named; anything else is reported as source, number and count.
EVENTS = {("Microsoft-Windows-Kernel-Power", 41): "the PC shut down unexpectedly or lost power",
          ("EventLog", 6008): "the previous shutdown was not clean",
          ("BugCheck", 1001): "Windows had a blue screen",
          ("Display", 4101): "the graphics driver stopped responding and recovered",
          ("Application Error", 1000): "an app crashed",
          ("Application Hang", 1002): "an app stopped responding",
          ("Service Control Manager", 7031): "a Windows service stopped unexpectedly",
          ("Service Control Manager", 7034): "a Windows service stopped unexpectedly",
          ("disk", 7): "the disk reported errors", ("disk", 11): "the disk reported errors",
          ("disk", 51): "the disk reported errors", ("disk", 153): "the disk reported errors",
          ("Ntfs", 55): "the disk reported errors",
          ("Microsoft-Windows-Resource-Exhaustion-Detector", 2004): "Windows ran low on memory"}
ANY_ID = {"Microsoft-Windows-WHEA-Logger": "the processor or hardware reported an error"}   # the id does not matter
NOISE = {("Microsoft-Windows-DistributedCOM", 10010), ("Microsoft-Windows-DistributedCOM", 10016),
         ("Microsoft-Windows-CertificateServicesClient-CertEnroll", 87)}                      # seen here, harmless
APP_EVENTS = {("Application Error", 1000): "crashed", ("Application Hang", 1002): "stopped responding"}


def snapshot(part, hours=24, timeout=15):
    """One read-only look from diag.ps1 as a dict, or None for anything that goes wrong. Logs the part and the time only."""
    if part not in PARTS:
        raise ValueError(f"unknown diag part: {part!r}")
    hours = max(1, min(720, int(hours)))
    start = time.time()
    try:
        r = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File", PS1,
                            "-Part", part, "-Hours", str(hours)],
                           creationflags=NO_WINDOW, capture_output=True, text=True, timeout=timeout)
        data = json.loads(r.stdout) if r.returncode == 0 and r.stdout.strip() else None
    except (subprocess.TimeoutExpired, OSError, ValueError):
        data = None
    if isinstance(data, dict):
        log(f"diag: {part} {(time.time() - start) * 1000:.0f} ms")
        return data
    log(f"diag: {part} failed")
    return None


def top_apps(procs, cpus, key):
    """Processes of one app added up by name. key: cpu (percent of the whole CPU), mem or io (bytes). Biggest first."""
    total, count = {}, {}
    for p in procs or []:
        name = re.sub(r"\.exe$", "", str(p.get("name") or "").lower())
        total[name] = total.get(name, 0) + (p.get(key) or 0)
        count[name] = count.get(name, 0) + 1
    scale = max(1, cpus or 1) if key == "cpu" else 1
    out = [{"name": n, "count": count[n], "value": round(v / scale, 1) if key == "cpu" else v} for n, v in total.items()]
    return sorted(out, key=lambda a: a["value"], reverse=True)


def gpu_apps(gpu, gpumem, procs):
    """GPU use per app: pids named through procs (an unknown pid is skipped), load capped at 100, by load then memory."""
    names = {p.get("pid"): re.sub(r"\.exe$", "", str(p.get("name") or "").lower()) for p in procs or []}
    apps = {}
    for g, field in ((gpu, "util"), (gpumem, "bytes")):
        for x in g or []:
            n = names.get(x.get("pid"))
            if n:
                a = apps.setdefault(n, {"name": n, "util": 0, "bytes": 0})
                a[field] += x.get(field) or 0
    for a in apps.values():
        a["util"] = min(100, round(a["util"], 1))
    return sorted(apps.values(), key=lambda a: (a["util"], a["bytes"]), reverse=True)


def group_events(events, since=None):
    """Error events as plain words with counts, most first. Reads only provider, id, time and app: never any message."""
    groups = {}
    for e in events or []:
        provider, eid, app = e.get("provider"), e.get("id"), e.get("app")
        if (provider, eid) in NOISE or (since is not None and (e.get("time") or 0) < since):
            continue
        what = EVENTS.get((provider, eid)) or ANY_ID.get(provider)
        if (provider, eid) in APP_EVENTS and app:
            text = f"{str(app).lower().removesuffix('.exe')} {APP_EVENTS[(provider, eid)]}"
        else:
            text = what or f"{provider} event {eid}"
        g = groups.setdefault(text, {"text": text, "count": 0, "known": bool(what)})
        g["count"] += 1
    return sorted(groups.values(), key=lambda g: g["count"], reverse=True)


# 9d rules: thresholds and severities in one place (starting values, tune after a week). Higher sev = worse.
T = {"app_cpu": 50, "mem": 90, "disk_pct": 10, "disk_gb": 10, "disk_busy": 90, "gpu": 90, "temp": 90, "wifi": 40, "ping_ms": 100,
     "uptime_days": 14}
SEV = {"heat": 90, "cpu_app": 80, "mem": 78, "disk_full": 76, "gpu": 70, "disk_busy": 68, "internet": 66, "router": 65, "faulty": 60,
       "crash": 55, "wifi": 45, "slow_router": 44, "unknown_event": 40, "battery": 35, "own_cpu": 30, "own_wake": 25, "reboot": 20}
# Windows' own and the HUD's processes: never offered for closing. python and ollama are left out on purpose:
# they are named "my own model" and are never closable (OWN_MODEL).
PROTECTED = frozenset({"explorer", "svchost", "csrss", "wininit", "winlogon", "lsass", "services", "smss", "dwm", "system",
                       "registry", "fontdrvhost", "sihost", "ctfmon", "audiodg", "msmpeng", "searchhost", "taskhostw",
                       "rainmeter", "jarvis", "shipcore"})
OWN_MODEL = frozenset({"ollama", "python"})


def is_protected(name):
    return re.sub(r"\.exe$", "", str(name or "").lower()) in PROTECTED


def is_own_model(name):
    """ollama, python, pythonw...: the stem starts with one of OWN_MODEL; closing one would cut off his own brain."""
    return re.sub(r"\.exe$", "", str(name or "").lower()).startswith(tuple(OWN_MODEL))


def findings(snap):
    """Fixed rules (9d) over a snapshot dict, worst first. Every key is optional: a missing one skips its rule. Pure."""
    out, snap = [], snap or {}

    def add(sev, text, app=None, closable=False):
        out.append({"sev": sev, "text": text, "app": app,
                    "closable": bool(closable and app and not is_protected(app) and app not in OWN_MODEL)})

    procs, cpus = snap.get("procs"), snap.get("cpus")
    top = top_apps(procs, cpus, "cpu")[:1]
    if top and top[0]["value"] > T["app_cpu"]:
        add(SEV["cpu_app"], f"{top[0]['name']} is using {top[0]['value']:.0f}% of the CPU", top[0]["name"], True)
    if (snap.get("mem_pct") or 0) > T["mem"]:
        m = (top_apps(procs, cpus, "mem") or [None])[0]
        add(SEV["mem"], f"{m['name']} is using {m['value'] / 2**30:.1f} GB of memory" if m and m["value"] else f"memory is {snap['mem_pct']:.0f}% full",
            m["name"] if m and m["value"] else None, True)
    for d in snap.get("disks") or []:
        free, total = d.get("free_gb"), d.get("total_gb")
        if free is not None and (free < T["disk_gb"] or (total and 100 * free / total < T["disk_pct"])):
            add(SEV["disk_full"], f"drive {str(d.get('drive')).rstrip(':').upper()} is almost full, {free:.0f} GB free")
    if (snap.get("disk_busy") or 0) > T["disk_busy"]:
        add(SEV["disk_busy"], f"the disk is busy {snap['disk_busy']:.0f}% of the time")
    if (snap.get("gpu_util") or 0) > T["gpu"]:
        g = (gpu_apps(snap.get("gpu"), snap.get("gpumem"), procs) or [None])[0]
        if g and g["name"] in OWN_MODEL:
            add(SEV["gpu"], "my own model is using the GPU", g["name"])
        elif g:
            add(SEV["gpu"], f"{g['name']} is using the GPU", g["name"], True)
        else:
            add(SEV["gpu"], f"the GPU is {snap['gpu_util']:.0f}% busy")
    hot = [f"{k.upper()} {v:.0f} C" for k, v in (snap.get("temps") or {}).items() if v is not None and v >= T["temp"]]
    if hot or snap.get("throttle"):
        add(SEV["heat"], "the PC is running hot: " + (", ".join(hot) if hot else "the processor is being slowed down"))
    if snap.get("battery_saver"):
        add(SEV["battery"], "battery saver is on, so the PC is running slower on purpose")
    signal = (snap.get("wifi") or {}).get("signal")
    if signal is not None and signal < T["wifi"]:
        add(SEV["wifi"], f"the Wi-Fi signal is weak, {signal:.0f}%")
    gw, pub = snap.get("gateway"), snap.get("public")
    if gw:
        if gw.get("ms") is None:
            add(SEV["router"], "I can't reach the router")
        else:
            if gw["ms"] > T["ping_ms"]:
                add(SEV["slow_router"], f"the router is slow to answer, {gw['ms']:.0f} ms")
            if pub and all(p.get("ms") is None for p in pub):
                add(SEV["internet"], "the router is fine but the internet is not answering")
    if (snap.get("faulty_devices") or 0) > 0:
        add(SEV["faulty"], f"Windows reports {snap['faulty_devices']} device(s) with a problem")
    for e in snap.get("events") or []:
        if e.get("count", 0) >= 1:
            add(SEV["crash"] if e.get("known") else SEV["unknown_event"], f"{e['text']}, {e['count']} time(s)")
    if snap.get("reboot_pending") or (snap.get("uptime_days") or 0) > T["uptime_days"]:
        add(SEV["reboot"], "a restart is pending" if snap.get("reboot_pending") else f"the PC has been on for {snap['uptime_days']:.0f} days")
    if snap.get("jarvis_on_cpu"):
        add(SEV["own_cpu"], "my voice model is running on the CPU")
    if snap.get("wake_off"):
        add(SEV["own_wake"], f"my wake word is off ({snap['wake_off']})")
    return sorted(out, key=lambda f: f["sev"], reverse=True)


def summary(snap):
    """The fixed all-clear line, from the numbers that are there."""
    snap = snap or {}
    parts = ([f"CPU {snap['cpu_pct']:.0f}%"] if snap.get("cpu_pct") is not None else []) + \
            ([f"memory {snap['mem_pct']:.0f}%"] if snap.get("mem_pct") is not None else []) + \
            (["disk fine"] if snap.get("disks") else []) + (["no errors today"] if snap.get("events") == [] else [])
    return f"I can't see anything wrong: {', '.join(parts)}." if parts else "I couldn't read that."


# ---- 9a: one topic -> one snapshot -> a line made by code (never the model) or findings for the model to word
NEEDS = {"cpu": ("processes",), "memory": ("processes",), "gpu": ("processes",), "disk": ("processes",), "storage": (),
         "fan": ("processes",), "crash": ("logs",), "net": ("network",), "sound": (),
         "wrong": ("processes", "logs", "network", "system"), "lasterr": ()}
COULDNT = "I couldn't read that."


def drives():
    """Free space of every fixed drive, from Windows' own counters (no PowerShell)."""
    out, mask = [], ctypes.windll.kernel32.GetLogicalDrives()
    for i in range(26):
        d = chr(65 + i) + ":\\"
        if mask >> i & 1 and ctypes.windll.kernel32.GetDriveTypeW(d) == 3:
            try:
                u = shutil.disk_usage(d)
                out.append({"drive": d[0], "free_gb": u.free / 2**30, "total_gb": u.total / 2**30})
            except OSError:
                pass
    return out


def memory_percent():
    m = MEMORYSTATUSEX()
    m.dwLength = ctypes.sizeof(m)
    return float(m.dwMemoryLoad) if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m)) else None


def battery_saver():
    p = SYSTEM_POWER_STATUS()
    return bool(ctypes.windll.kernel32.GetSystemPowerStatus(ctypes.byref(p)) and p.SystemStatusFlag == 1)


def temps():
    out = {}
    for key, name, _ in HW_LINES:
        if name.endswith("temperature"):
            try:
                n = int(float(settings().get(key, "-1")))
                if n >= 0:
                    out[name.split()[0].lower()] = hw_value(n)
            except (OSError, ValueError):
                pass
    return out


def gather(topic, hours=24, own_cpu=False):
    """The snapshot dict for findings() with the parts the topic needs, read side by side. None: nothing could be read."""
    need, got = NEEDS[topic], {}

    def read(part):
        got[part] = snapshot(part, hours)
    threads = [threading.Thread(target=read, args=(p,)) for p in need]
    for t in threads:
        t.start()
    for t in threads:
        t.join(20)
    if need and not any(got.get(p) for p in need):
        return None
    snap = {"disks": drives(), "mem_pct": memory_percent(), "temps": temps(), "battery_saver": battery_saver(),
            "jarvis_on_cpu": own_cpu, "wake_off": WAKE_OFF[0]}
    p = got.get("processes")
    if p:
        procs, cpus = p.get("procs") or [], p.get("cpus") or 1
        apps = gpu_apps(p.get("gpu"), p.get("gpumem"), procs)
        snap.update(procs=procs, cpus=cpus, cpu_pct=min(100.0, sum(x.get("cpu") or 0 for x in procs) / max(1, cpus)),
                    gpu=p.get("gpu"), gpumem=p.get("gpumem"), disk_busy=p.get("disk_busy"),
                    gpu_util=max((a["util"] for a in apps), default=0))
    n, s = got.get("network"), got.get("system")
    if n:
        snap.update(wifi=n.get("wifi"), gateway=n.get("gateway"), public=n.get("public"))
    if s:
        snap.update(reboot_pending=s.get("reboot_pending"), uptime_days=s.get("uptime_days"),
                    faulty_devices=s.get("faulty_devices"))
    lg = got.get("logs")
    if lg:
        snap["boot"] = lg.get("boot")
        snap["raw_events"] = lg.get("events")                  # kept so "since the restart" cuts these, not a second read
        snap["events"] = group_events(lg.get("events"))
    return snap


def _pct(v):
    return f"{v:.0f}%"


def diagnose(topic, span=None, own_cpu=False):
    """-> (line, items). line: the whole answer from code, or None when the findings must be worded by the model.
    items: findings, worst first. span: None = JarvisLogHours, "boot" = since the last restart, 168 = this week."""
    if topic == "lasterr":
        err, at = LAST_ERR
        return (f"The last problem was: {err}, at {time.strftime('%I:%M %p', time.localtime(at)).lstrip('0')}." if err
                else "I haven't had a problem since I started."), []
    if topic == "sound":
        try:
            muted, percent = speakers()
        except OSError:
            return COULDNT, []
        return ("The speakers are muted." if muted else "The volume is at 0." if percent <= 0 else
                f"The speakers are on at {percent}%, so it isn't muted here. Check the app's own volume or the output device."), []
    try:
        hours = int(setting("JarvisLogHours", "24"))
    except ValueError:
        hours = 24
    hours = 24 * 7 if span == 168 else 720 if span == "boot" else hours
    snap = gather(topic, hours, own_cpu)
    if snap is None:
        return COULDNT, []
    if span == "boot" and snap.get("boot") and snap.get("events") is not None:   # the read covered 30 days: cut at the restart
        if snap.get("raw_events") is not None:
            snap["events"] = group_events(snap["raw_events"], since=snap["boot"])
    items = findings(snap)
    procs, cpus = snap.get("procs"), snap.get("cpus")
    if topic == "wrong":
        return (None, items) if items else (summary(snap), [])
    if topic == "storage":
        return (" ".join(f"Drive {x['drive']} has {x['free_gb']:.0f} GB free of {x['total_gb']:.0f}." for x in snap["disks"])
                or COULDNT), items
    if topic == "crash":
        ev = snap.get("events")
        if ev is None:
            return COULDNT, []
        return (("In that time: " + "; ".join(f"{e['text']}, {e['count']} time(s)" for e in ev[:5]) + ".") if ev
                else "I can't see any errors in that time."), []
    if topic == "net":
        gw, pub = snap.get("gateway"), snap.get("public") or []
        if not gw and not pub:
            return COULDNT, []
        if gw and gw.get("ms") is None:
            return "I can't reach the router.", []
        if pub and all(x.get("ms") is None for x in pub):
            return "The router answers, but the internet does not.", []
        sig = (snap.get("wifi") or {}).get("signal")
        up = min((x["ms"] for x in pub if x.get("ms") is not None), default=None)
        return ("Yes, the internet is working" + (f": the router answers in {gw['ms']:.0f} ms" if gw else "")
                + (f", the internet in {up:.0f} ms" if up is not None else "")
                + (f", Wi-Fi signal {sig:.0f}%" if sig is not None else "") + "."), []
    if not procs:
        return COULDNT, []
    cpu_top, mem_top = top_apps(procs, cpus, "cpu")[:3], top_apps(procs, cpus, "mem")[:1]
    gpu_top = gpu_apps(snap.get("gpu"), snap.get("gpumem"), procs)[:1]

    def who(a):
        return "my own model" if a["name"] in OWN_MODEL else a["name"] + (f" ({a['count']} processes)" if a.get("count", 1) > 1 else "")
    if topic == "cpu":
        busy = [a for a in cpu_top if a["value"] >= 1]
        return (f"The CPU is at {_pct(snap['cpu_pct'])}. " + ", then ".join(f"{who(a)} is using {_pct(a['value'])}" for a in busy) + "."
                if busy else "The CPU is nearly idle."), items
    if topic == "memory":
        m = mem_top[0] if mem_top else None
        return (f"Memory is {_pct(snap['mem_pct'])} full." if snap.get("mem_pct") is not None else "") \
            + (f" {who(m)} is using the most, {m['value'] / 2**30:.1f} GB." if m and m["value"] else "") or COULDNT, items
    if topic == "gpu":
        g = gpu_top[0] if gpu_top else None
        return (f"{who(g)} is using {_pct(g['util'])} of the GPU, {g['bytes'] / 2**30:.1f} GB of its memory."
                if g and (g["util"] or g["bytes"]) else "I can't see any GPU use."), items
    if topic == "disk":
        io = top_apps(procs, cpus, "io")[:1]
        return (f"The disk is busy {_pct(snap['disk_busy'])} of the time." if snap.get("disk_busy") is not None else "") \
            + (f" {who(io[0])} is doing the most." if io and io[0]["value"] else "") or COULDNT, items
    if topic == "fan":
        heat = ", ".join(f"{k.upper()} {v:.0f} C" for k, v in (snap.get("temps") or {}).items())
        return ((f"It is {heat}. " if heat else "I can't read the temperatures. ")
                + (f"The CPU is busiest with {who(cpu_top[0])}. " if cpu_top and cpu_top[0]["value"] >= 5 else "")
                + (f"The GPU is busiest with {who(gpu_top[0])}." if gpu_top and gpu_top[0]["util"] >= 5 else "")).strip(), items
    return COULDNT, []


def prompt_findings(items):
    """What the model gets for "what's wrong": the findings only, and one instruction."""
    return ("\nDIAGNOSIS FINDINGS (worst first, found by code from real readings):\n" + "\n".join("- " + f["text"] for f in items[:6])
            + "\nExplain these in two sentences, most serious first. Say only what they say; invent nothing.")


# ---- 9e: the silent watch. Every WATCH_EVERY seconds, one cheap look (no PowerShell). A problem seen WATCH_NEED times in a row is
# named once in the chat (no sound, no model), then left alone for WATCH_REPEAT seconds. The app is named only then, by one snapshot.
WATCH_EVERY, WATCH_NEED, WATCH_REPEAT = 300, 3, 1800
_watch = {"at": 0.0, "streak": 0, "shown": 0.0, "cpu": None, "busy": False}


def on_battery():
    p = SYSTEM_POWER_STATUS()
    return bool(ctypes.windll.kernel32.GetSystemPowerStatus(ctypes.byref(p)) and p.ACLineStatus == 0)


def watch_trips():
    """What looks wrong right now, from numbers Windows hands over at once. The CPU is the average since the last look."""
    out, now = [], cpu_times()
    prev, _watch["cpu"] = _watch["cpu"], now
    if prev and now[1] > prev[1] and 100 * (1 - (now[0] - prev[0]) / (now[1] - prev[1])) > 90:
        out.append("the CPU has been nearly full")
    if (memory_percent() or 0) > T["mem"]:
        out.append("memory is nearly full")
    for d in drives():
        if d["free_gb"] < T["disk_gb"] or d["free_gb"] < d["total_gb"] * T["disk_pct"] / 100:
            out.append(f"drive {d['drive']} is nearly full")
    out += [f"the {k.upper()} is hot" for k, v in temps().items() if v > T["temp"]]
    return out


def watch(now, skip, show):
    """Called from the 2 s tick. skip(): True while he is busy or the HUD is in a low tier. show(line): put one line in the chat."""
    if setting("JarvisWatch", "1") != "1" or now - _watch["at"] < WATCH_EVERY:
        return False
    _watch["at"] = now
    try:
        if skip() or on_battery():
            return False
        trips = watch_trips()
    except OSError as e:
        log(f"watch: {e}")
        return False
    if not trips:
        _watch["streak"] = 0
        return False
    _watch["streak"] += 1
    if _watch["streak"] < WATCH_NEED or now - _watch["shown"] < WATCH_REPEAT or _watch["busy"]:
        return False
    _watch["shown"], _watch["streak"], _watch["busy"] = now, 0, True

    def name_it():
        try:
            snap = gather("cpu" if any(("CPU" in t or "memory" in t) for t in trips) else "storage", 24, False)
            top = (findings(snap) or [None])[0] if snap else None
            show("Heads up: " + (top["text"] if top else trips[0]) + ".")
        finally:
            _watch["busy"] = False
    threading.Thread(target=name_it, daemon=True).start()
    return True
