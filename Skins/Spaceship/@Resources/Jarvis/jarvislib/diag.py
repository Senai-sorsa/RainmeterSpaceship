"""diag: moved verbatim from jarvis.py (refactor). See JARVIS-Repair-Plan.txt, REFACTOR."""
import ctypes
import os
import re
import shutil
import subprocess
import time
from .audio import speakers
from .base import NO_WINDOW, read_kv, settings
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
