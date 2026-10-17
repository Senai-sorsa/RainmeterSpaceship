"""actions: moved verbatim from jarvis.py (refactor). See JARVIS-Repair-Plan.txt, REFACTOR."""
import ctypes
import os
import re
import subprocess
import time
import winreg
from .audio import mic_volume, speakers
from .base import BT_FILE, DATA, NO_WINDOW, RES, log, read_kv, setting


def start_apps():
    """The installed apps the HUD scanned, or None while that list is missing (not the same as no apps)."""
    out = []
    try:
        with open(os.path.join(DATA, "StartApps.txt"), "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                if "|" in line:
                    name, appid = line.rstrip("\n").split("|", 1)
                    out.append((name.strip(), appid.strip()))
    except OSError:
        return None
    return out


def best_app(name):
    """The installed app whose name best matches what you said."""
    want = re.sub(r"[^a-z0-9 ]", "", name.lower()).strip()
    if not want:
        return None
    best, score = None, 0
    for disp, appid in start_apps() or []:
        d = disp.lower()
        if any(x in d for x in ("uninstall", "help", "readme", "documentation")):
            continue
        # a prefix needs 3+ letters and anything looser a whole word, so "open e" matches nothing
        sc = 3 if d == want else (2 if len(want) >= 3 and d.startswith(want) else
                                  (1 if re.search(r"\b" + re.escape(want) + r"\b", d) else 0))
        if sc > score or (sc == score and sc and best and len(disp) < len(best[0])):
            best, score = (disp, appid), sc
    return best if score else None


def running_window(name):
    """An open app (from the HUD's window list) whose exe matches what you said, e.g. 'chrome' -> chrome.exe."""
    stems = [(exe, re.sub(r"[^a-z0-9]", "", os.path.splitext(exe)[0].lower())) for exe in open_windows()]
    words = name.lower().split()
    # the whole name first, then its last word: "google chrome" -> chrome.exe
    for want in dict.fromkeys([re.sub(r"[^a-z0-9]", "", name.lower()), re.sub(r"[^a-z0-9]", "", words[-1]) if words else ""]):
        # exact name first, then a 3+ letter prefix, then a 4+ letter fragment: "close e" must not pick explorer
        for ok in (lambda s: s == want, lambda s: len(want) >= 3 and s.startswith(want), lambda s: len(want) >= 4 and want in s):
            for exe, stem in stems:
                if want and ok(stem):
                    return exe
    return None


def act_volume(change):
    how, n = change                                           # ("set", 30) or ("step", -10)
    if how == "step":
        n += speakers()[1]
    speakers(volume=max(0, min(100, n)) / 100)


def screen_brightness(percent=None):
    """The laptop panel's brightness (WMI): set it when given, then return what Windows reports. One fixed PowerShell
    line; the only thing put into it is an integer. A desktop monitor has no WMI brightness: that raises OSError."""
    wmi = "Get-CimInstance -Namespace root/WMI -ClassName "
    cmd = (f"({wmi}WmiMonitorBrightnessMethods).WmiSetBrightness(1,{int(percent)});" if percent is not None else "") +           f"({wmi}WmiMonitorBrightness).CurrentBrightness"
    out = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", cmd], creationflags=NO_WINDOW,
                         capture_output=True, text=True, timeout=15)
    if out.returncode or not out.stdout.split():
        raise OSError("Windows has no brightness control for this screen")
    level = int(out.stdout.split()[-1])
    if percent is not None and abs(level - percent) > 2:
        raise OSError("Windows did not change the brightness")
    return level


def act_brightness(change):
    how, n = change                                           # ("set", 60) or ("step", -10), as for the volume
    if how == "step":
        n += screen_brightness()
    screen_brightness(max(0, min(100, n)))


THEME_KEY = r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"


def theme_mode(mode=None):
    """Windows colour mode: set "dark" or "light" for the apps AND Windows itself (0 = dark), then return what the registry says.
    Only two fixed values are ever written. Mixed values read as "mixed"."""
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, THEME_KEY, 0, winreg.KEY_READ | winreg.KEY_SET_VALUE) as key:
        if mode is not None:
            for name in ("AppsUseLightTheme", "SystemUsesLightTheme"):
                winreg.SetValueEx(key, name, 0, winreg.REG_DWORD, 0 if mode == "dark" else 1)
        got = {winreg.QueryValueEx(key, n)[0] for n in ("AppsUseLightTheme", "SystemUsesLightTheme")}
    return "dark" if got == {0} else "light" if got == {1} else "mixed"


def act_theme(mode):
    if mode not in ("dark", "light") or theme_mode(mode) != mode:
        raise OSError("Windows did not take the colour mode")


# 7d: power plans. Only plans that keep the CPU, GPU, microphone and network running; the ids are fixed Windows ids and a
# plan counts only if the machine lists it (powercfg /list). Power saver is never picked.
POWER_OK = {"balanced": ("381b4222-f694-41f0-9685-ff5bb260df2e",),
            "performance": ("8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c", "e9a42b02-d5df-448d-aa00-03f14749eb61")}
POWER_NAMES = {"balanced": "Balanced", "performance": "Best performance"}


def power_plans():
    """(active plan id, ids the machine lists) read from powercfg; one fixed command, nothing from speech."""
    def run(arg):
        out = subprocess.run(["powercfg", arg], creationflags=NO_WINDOW, capture_output=True, text=True, timeout=10)
        if out.returncode:
            raise OSError("powercfg ended with code %d" % out.returncode)
        return out.stdout.lower()
    listed = re.findall(r"guid: ([0-9a-f-]{36})", run("/list"))
    active = re.search(r"guid: ([0-9a-f-]{36})", run("/getactivescheme"))
    return (active.group(1) if active else None), listed


def power_key(guid):
    return next((k for k, ids in POWER_OK.items() if guid in ids), None)


def act_power(key, plan=None):
    """Switch to a plan from POWER_OK that the machine lists, then check powercfg reports it active.
    `key` is "balanced" / "performance", or a plan id (undo: the one that was active, only if it is in POWER_OK)."""
    _, listed = power_plans()
    guid = next((g for g in (POWER_OK.get(key) or (key,)) if g in listed and power_key(g)), None)
    if not guid:
        raise OSError("this PC has no such power plan")
    subprocess.run(["powercfg", "/setactive", guid], creationflags=NO_WINDOW, capture_output=True, timeout=10, check=True)
    if power_plans()[0] != guid:
        raise OSError("Windows did not switch the power plan")


# 7b: the Bluetooth radio (Windows.Devices.Radios, from one fixed PowerShell script). The only thing put into it is the
# literal "On" or "Off", chosen here from a two-word table, never from speech.
BT_SCRIPT = """$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Runtime.WindowsRuntime
$t = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object { $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' })[0]
function Await($op, $type) { $x = $t.MakeGenericMethod($type).Invoke($null, @($op)); $x.Wait(-1) | Out-Null; $x.Result }
[Windows.Devices.Radios.Radio, Windows.System.Devices, ContentType = WindowsRuntime] | Out-Null
$radio = (Await ([Windows.Devices.Radios.Radio]::GetRadiosAsync()) ([System.Collections.Generic.IReadOnlyList[Windows.Devices.Radios.Radio]])) | Where-Object { $_.Kind -eq 'Bluetooth' } | Select-Object -First 1
if (-not $radio) { exit 3 }
%s
$radio.State
"""
BT_SET = "Await ($radio.SetStateAsync('%s')) ([Windows.Devices.Radios.RadioAccessStatus]) | Out-Null"


def bluetooth_radio(state=None):
    """The Bluetooth radio: set "on" / "off" when given, then return what Windows reports ("on", "off", ...). OSError if the PC
    has no Bluetooth radio, Windows refuses, or the radio ends up in another state than asked."""
    script = BT_SCRIPT % (BT_SET % {"on": "On", "off": "Off"}[state] if state else "")
    out = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", script], creationflags=NO_WINDOW,
                         capture_output=True, text=True, timeout=25)
    if out.returncode or not out.stdout.split():
        raise OSError("Windows has no Bluetooth radio to control" if out.returncode == 3 else "Windows would not change Bluetooth")
    got = out.stdout.split()[-1].lower()
    if state and got != state:
        raise OSError("Bluetooth did not change")
    return got


def act_bluetooth(state):
    bluetooth_radio(state)


# 7b: paired Bluetooth AUDIO devices (bthprops.cpl: class of device = audio). List = read only. Link turns the device's audio
# services on (off then on, which makes Windows reconnect) or off; the only thing put into the script is a 12-digit hex
# address that came from the list, checked below. Not yet run against a real headset: see LIVE TEST 1b-15.
BT_DEV_SCRIPT = """$ErrorActionPreference = 'Stop'
Add-Type -TypeDefinition @'
using System; using System.Collections.Generic; using System.Runtime.InteropServices; using System.Threading;
public static class Bt {
  [StructLayout(LayoutKind.Sequential)] public struct ST { public ushort a, b, c, d, e, f, g, h; }
  [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)] public struct DEV {
    public int size; public ulong addr; public uint cls; public int connected, remembered, authenticated; public ST seen, used;
    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 248)] public string name; }
  [StructLayout(LayoutKind.Sequential)] public struct FIND { public int size, auth, remembered, unknown, connected, inquiry; public byte timeout; public IntPtr radio; }
  [DllImport("bthprops.cpl")] static extern IntPtr BluetoothFindFirstDevice(ref FIND p, ref DEV d);
  [DllImport("bthprops.cpl")] static extern bool BluetoothFindNextDevice(IntPtr h, ref DEV d);
  [DllImport("bthprops.cpl")] static extern bool BluetoothFindDeviceClose(IntPtr h);
  [DllImport("bthprops.cpl")] static extern uint BluetoothSetServiceState(IntPtr radio, ref DEV d, ref Guid svc, uint flags);
  public static List<DEV> All() {
    var r = new List<DEV>(); var p = new FIND(); p.size = Marshal.SizeOf(p); p.auth = 1; p.remembered = 1; p.connected = 1;
    var d = new DEV(); d.size = Marshal.SizeOf(d);
    IntPtr h = BluetoothFindFirstDevice(ref p, ref d); if (h == IntPtr.Zero) return r;
    do { if (((d.cls >> 8) & 0x1F) == 4) r.Add(d); d.size = Marshal.SizeOf(d); } while (BluetoothFindNextDevice(h, ref d));
    BluetoothFindDeviceClose(h); return r; }
  public static string List() { var s = new System.Text.StringBuilder();
    foreach (var d in All()) s.Append(d.addr.ToString("X12") + "|" + d.connected + "|" + d.name + "\\n"); return s.ToString(); }
  public static int Link(ulong addr, bool on) {
    var guids = new[] { new Guid("0000110b-0000-1000-8000-00805f9b34fb"), new Guid("0000111e-0000-1000-8000-00805f9b34fb"), new Guid("00001108-0000-1000-8000-00805f9b34fb") };
    foreach (var d0 in All()) { if (d0.addr != addr) continue; var d = d0;
      foreach (var g in guids) { var gg = g; if (on) BluetoothSetServiceState(IntPtr.Zero, ref d, ref gg, 0); BluetoothSetServiceState(IntPtr.Zero, ref d, ref gg, on ? 1u : 0u); }
      for (int i = 0; i < 24; i++) { Thread.Sleep(500); foreach (var n in All()) if (n.addr == addr && (n.connected != 0) == on) return on ? 1 : 0; }
      return on ? 0 : 1; }
    return -1; }
}
'@
%s
"""


def _bt_ps(call, timeout=40):
    try:
        out = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", BT_DEV_SCRIPT % call], creationflags=NO_WINDOW,
                             capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        raise OSError("Windows timed out listing or changing Bluetooth devices")
    if out.returncode:
        raise OSError("Windows would not list or change Bluetooth devices")
    return out.stdout


def bt_devices():
    """Paired Bluetooth audio devices as [(address, name, connected)]. OSError if Windows will not say."""
    rows = [ln.split("|", 2) for ln in _bt_ps("[Bt]::List()").splitlines() if ln.count("|") >= 2]
    devs = [(a, n.strip(), c == "1") for a, c, n in rows if re.fullmatch(r"[0-9A-F]{12}", a)]
    try:                                                       # the Control Center's BLUETOOTH NAMES row shows these
        with open(BT_FILE, "w", encoding="utf-8") as f:
            f.write("".join(d[1].replace("\n", " ") + "\n" for d in devs))
    except OSError:
        pass
    return devs


def bt_link(addr, on):
    """Connect (on) or disconnect a device from bt_devices(); succeeds only if Windows then reports that state."""
    if not re.fullmatch(r"[0-9A-F]{12}", addr):
        raise ValueError("not a Bluetooth address")
    got = _bt_ps("[Bt]::Link(0x%s, $%s)" % (addr, "true" if on else "false"), timeout=60).split()
    if got != ["1" if on else "0"]:
        raise OSError("the device did not %s" % ("connect" if on else "disconnect"))


BT_GENERIC = ("headphones", "headset", "earbuds", "airpods", "speaker", "speakers", "earphones", "bluetooth", "device")


def bt_names():
    """JarvisBtNames = "<Bluetooth name>=<what you call it>;..." as {spoken name (lower): Bluetooth name}."""
    pairs = (p.split("=", 1) for p in setting("JarvisBtNames", "").split(";") if "=" in p)
    return {s.strip().lower(): b.strip() for b, s in pairs if s.strip() and b.strip()}


def pick_bt(term, devs):
    """The paired device meant by `term`: your own name for it first, then part of its Bluetooth name, then a plain
    "headphones" when only one is paired. Returns one (address, name, connected), a list when several fit, None for none."""
    t = re.sub(r"^(?:my|the)\s+", "", term.strip().lower())
    words = [t] + ([t.rsplit(" ", 1)[0]] if " " in t and t.rsplit(" ", 1)[1] in BT_GENERIC else [])
    mine = bt_names()
    for w in words:
        hit = [d for d in devs if mine.get(w) == d[1]]
        hit = hit or [d for d in devs if w and w in d[1].lower()]
        if hit:
            return hit[0] if len(hit) == 1 else hit
    return devs[0] if t in BT_GENERIC and len(devs) == 1 else (list(devs) if t in BT_GENERIC and devs else None)


def act_mic_level(change):
    how, n = change                                           # ("set", 80) or ("step", -10), the same as act_volume
    if how == "step":
        n += mic_volume()[1]
    mic_volume(volume=max(0, min(100, n)) / 100)


MEDIA_KEYS = {"playpause": 0xB3, "next": 0xB0, "prev": 0xB1}
# 7c: the fixed settings-pages table. Windows has no switch for most of these, so he opens the page; speech never builds a link
PAGES = {"bluetooth": ("ms-settings:bluetooth", "Bluetooth"), "sound": ("ms-settings:sound", "Sound"),
         "display": ("ms-settings:display", "Display"), "night light": ("ms-settings:nightlight", "Night light"),
         "focus": ("ms-settings:quiethours", "Focus"), "wifi": ("ms-settings:network-wifi", "Wi-Fi"),
         "apps": ("ms-settings:appsfeatures", "Installed apps"), "startup": ("ms-settings:startupapps", "Startup apps"),
         "storage": ("ms-settings:storagesense", "Storage"), "update": ("ms-settings:windowsupdate", "Windows Update"),
         "power": ("ms-settings:powersleep", "Power and sleep"), "battery saver": ("ms-settings:batterysaver", "Battery saver")}


def act_page(target):
    key, _ = target                                           # (page key, note); only a key of PAGES can open
    os.startfile(PAGES[key][0])


def press_keys(*vks):
    """Hold the keys in order, release them in reverse (a shortcut like Win+D). Windows gives no result back."""
    for flags, keys in ((0, vks), (2, vks[::-1])):
        for vk in keys:
            ctypes.windll.user32.keybd_event(vk, 0, flags, 0)


def pictures_folder():
    buf = ctypes.create_unicode_buffer(260)
    ctypes.windll.shell32.SHGetFolderPathW(None, 0x27, None, 0, buf)   # CSIDL_MYPICTURES: follows a OneDrive move
    return buf.value


def act_screenshot(_):
    """Win+PrintScreen saves a PNG in Pictures\\Screenshots; the action succeeds only if a new file really appears."""
    folder, start = os.path.join(pictures_folder(), "Screenshots"), time.time() - 1
    press_keys(0x5B, 0x2C)
    for _ in range(20):
        time.sleep(0.25)
        if os.path.isdir(folder) and any(os.path.getmtime(os.path.join(folder, f)) >= start for f in os.listdir(folder)):
            return
    raise OSError("no screenshot file appeared")


def act_recycle(_):
    code = ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, 0x7) & 0xFFFFFFFF   # no prompt, no progress window, no sound
    if code not in (0, 0x8000FFFF):                           # 0x8000FFFF: it was already empty
        raise OSError(f"the recycle bin call ended with {code:#x}")



def press_key(vk):
    """Press and release one key. Windows gives no result back, so nobody can tell whether a player took it."""
    for flags in (0, 2):                                      # down, up
        ctypes.windll.user32.keybd_event(vk, 0, flags, 0)


def done_line(action, target):
    """What to say after an action that worked: the value Windows reports, never the one asked for."""
    if action == "micdev":                                     # the HUD writes the setting a moment later: this is what was asked
        return f"Listening through {target}. It applies the next time I listen." if target else "Back to the Windows default microphone."
    if action == "open":
        return f"Opening {target[0]}."
    if action == "volume":
        return f"Volume at {speakers()[1]} percent."
    if action in ("bluetooth", "bluetooth_off"):
        return f"Bluetooth is {bluetooth_radio()}."
    if action == "btlink":                                     # bt_link already checked that Windows reports it
        return f"{'Connected to' if target[1] else 'Disconnected from'} {target[2]}."
    if action == "power":
        return f"Power mode is {POWER_NAMES.get(power_key(power_plans()[0]), 'a plan I do not switch')}."
    if action == "page":
        key, note = target
        title = PAGES[key][1]
        return (f"Windows has no switch for that, so I opened the {title} settings." if note == "noswitch" else
                f"I can't read that list yet, so I opened the {title} settings." if note == "nolist" else f"I can't connect devices by voice yet, so I opened the {title} settings. Pick it there." if note == "noconnect" else f"Opening the {title} settings.")
    if action == "screenshot":
        return "Screenshot saved in Pictures, Screenshots."
    if action == "recycle":
        return "Recycle bin emptied."
    if action == "desktop":
        return "Sent."
    if action == "theme":
        return f"{theme_mode().capitalize()} mode is on."
    if action == "brightness":
        return f"Brightness is at {screen_brightness()} percent."
    if action in ("mic_mute", "mic_unmute", "mic_level"):      # read back from Windows, not what was asked
        is_muted, percent = mic_volume()
        return "Microphone muted." if is_muted else "Microphone unmuted." if action == "mic_unmute" else f"Microphone at {percent} percent."
    if action == "sleep" and screen_only[0]:
        return "This PC can't sleep that way, so I turned the screen off."
    return "Sent." if action == "media" else "Done."


def run_ok(args):
    """Run one fixed command: anything but exit code 0 within 10 s is a failure (TimeoutExpired / OSError)."""
    code = subprocess.run(args, creationflags=NO_WINDOW, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                          timeout=10).returncode
    if code:
        raise OSError(f"{args[0]} ended with code {code}")


def open_windows():
    return re.findall(r"^W (.+)$", read_kv("windows.txt"), re.M)


# action handlers: (description for the confirmation, function). Only these can ever run.
def act_open(app):
    target = app[1] if os.path.isabs(app[1]) else "shell:AppsFolder\\" + app[1]
    exe = os.path.basename(app[1]).lower() if app[1].lower().endswith(".exe") else running_window(app[0])
    core = os.path.join(RES, "Bin", "ShipCore.exe")
    if exe and exe in open_windows() and os.path.exists(core):  # 7-A8: already open: bring that window forward, no second copy
        run_ok([core, "focus", exe, target])
        return
    os.startfile(target)


def act_close(exe):
    from .diag import is_own_model, is_protected             # here, not at the top: diag imports other modules of this package
    if is_protected(exe) or is_own_model(exe):                # 9e: defence in depth, the route already refuses
        raise OSError("Windows needs it")
    if exe not in open_windows():                             # it went away while you were being asked
        raise OSError("it is not open any more")
    # taskkill only asks the windows to close, and its exit code is non-zero for any helper process without a
    # window (a browser has many), so the result is read from the HUD's window list instead (rewritten every 1.5 s)
    subprocess.run(["taskkill", "/IM", exe], creationflags=NO_WINDOW, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                   timeout=10)
    for _ in range(10):
        time.sleep(0.5)
        text = read_kv("windows.txt")                         # gone only by a fresh list: an unreadable or stale one proves nothing
        t = re.match(r"T (\d+)", text)
        if t and time.time() - int(t.group(1)) < 10 and exe not in re.findall(r"^W (.+)$", text, re.M):
            return
    raise OSError("it is still open (it may be asking to save)")


def act_lock(_):
    if not ctypes.windll.user32.LockWorkStation():
        raise OSError("Windows refused to lock")


screen_only = [False]                                          # 7-L1: the last sleep only turned the screen off


def act_sleep(_):
    # asked directly so the answer comes back (rundll32 always exits 0); it returns once the PC wakes again
    screen_only[0] = False
    if ctypes.WinDLL("powrprof", use_last_error=True).SetSuspendState(0, 1, 0):
        return
    screen_only[0] = True
    # S2-11: Modern Standby laptops (S0, no S3) refuse it; turning the screen off is how they enter standby
    log(f"sleep: suspend refused (error {ctypes.get_last_error()}) - screen off for Modern Standby")
    if not ctypes.windll.user32.PostMessageW(0xFFFF, 0x0112, 0xF170, 2):   # broadcast WM_SYSCOMMAND SC_MONITORPOWER off
        raise OSError("Windows refused to sleep")
