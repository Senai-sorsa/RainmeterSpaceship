"""Self-check for jarvis.py: plain asserts, no test framework.  Run:  py -3 -B test_jarvis.py"""
import builtins
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.argv[1:] = [tempfile.mkdtemp()]          # RES = argv[1]: Data\ (state, logs) is a temp folder, never the skin's
import jarvis


class Everywhere:
    """j.X = fake sets X in jarvis.py AND in every jarvislib module bound to the same object, so the fake reaches the
    code that calls X wherever it lives now (refactor R1). A fake for a name no module has fails: it would test nothing."""
    def __init__(self, main):
        object.__setattr__(self, "_main", main)

    def _mods(self):
        return [self._main] + [m for n, m in sorted(sys.modules.items()) if n.startswith("jarvislib.") and m]

    def __getattr__(self, name):
        for m in self._mods():
            if name in vars(m):
                return vars(m)[name]
        raise AttributeError(name)

    def __setattr__(self, name, value):
        mods = self._mods()
        if any(name in vars(m) for m in mods):
            old = getattr(self, name)
            for m in mods:
                if name in vars(m) and vars(m)[name] is old:
                    setattr(m, name, value)
        elif hasattr(builtins, name):                              # j.open: shadow the builtin in every jarvis module
            for m in mods:
                setattr(m, name, value)
        else:
            raise AttributeError(f"the test fakes {name}, which no jarvis module has")

    def __delattr__(self, name):
        for m in self._mods():
            if name in vars(m):
                delattr(m, name)


j = Everywhere(jarvis)
real_convo_add = jarvis.convo_add                                 # faked further down; the BUG-05 test needs the real one
j.DUCK_FILE = os.path.join(tempfile.mkdtemp(), "duck.txt")       # never the real Data folder
j.MICS_FILE = os.path.join(tempfile.mkdtemp(), "mics.txt")

# no disk, no sound card, no processes: fixed app list, fixed window list, recorded mute calls and commands
real_start_apps, real_transcribe, mic_listen = j.start_apps, j.transcribe, j.listen
real_brightness, real_theme = j.screen_brightness, j.theme_mode
j.start_apps =lambda: [("Google Chrome", "Chrome"), ("Microsoft Edge", "MSEdge"), ("Notepad", "notepad")]
j.read_kv = lambda name: "W chrome.exe\nW explorer.exe\nW Code.exe\n"
muted_to, ran = [], []
j.REMIND_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "no-such-reminders")
j.MEMORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "no-such-memory")   # never the real one
j.TOPICS_FILE = os.path.join(tempfile.mkdtemp(), "topics.json")
j.GIST_FILE = os.path.join(tempfile.mkdtemp(), "gist.txt")
j.speakers_mute = muted_to.append


class _Done:
    returncode = 0


def _run(args, **kw):
    assert kw.get("timeout"), "every command needs a timeout"
    ran.append(args)
    return _Done()


j.subprocess.run = _run
real_sleep = j.time.sleep
j.time.sleep = lambda s: None

# routing: commands act, questions and dangerous phrases never do
assert j.route("lock my computer")[:2] == ("act", "lock")
assert j.route("lock my computer")[3], "lock must ask for confirmation"
assert j.route("should I restart my computer?")[0] == "chat"
assert j.route("jarvis, self destruct")[0] == "guard"
assert j.route("open chrome")[:2] == ("act", "open")
assert j.route("close chrome")[:3] == ("act", "close", "chrome.exe")

# confirmation: the whole reply must be a plain yes, and in time
due = {"action": "shutdown", "target": None, "expires": 100}
assert j.confirmed(due, "yes", 99) and j.confirmed(due, " Go ahead. ", 99) and j.confirmed(due, "Yes, please!", 99)
for no in ("no", "", None, "yes, but don't do it", "yes no", "okay wait", "sure, restart instead", "yesterday"):
    assert not j.confirmed(due, no, 99), no
assert not j.confirmed(due, "yes", 100) and not j.confirmed(due, "yes", 500), "expired"
for yes in ("Yes, Jarvis.", "yes sir", "Jarvis, yes.", "Yes please, sir.", "Go ahead now."):   # S2-11: name / sir around it
    assert j.confirmed(due, yes, 99), yes
for no in ("yes jarvis but wait", "sir", "jarvis", "no sir"):
    assert not j.confirmed(due, no, 99), no

assert j.best_app("chrome") == ("Google Chrome", "Chrome")
assert j.best_app("") is None
assert j.running_window("chrome") == "chrome.exe"
assert j.running_window("") is None

# short or partial names must not pick an app or a window by accident
assert j.best_app("e") is None and j.best_app("ch") is None and j.best_app("rome") is None
assert j.best_app("edge") == ("Microsoft Edge", "MSEdge") and j.best_app("note") == ("Notepad", "notepad")
assert j.route("open e")[0] == "chat"
assert j.running_window("e") is None and j.running_window("ex") is None and j.running_window("exe") is None
assert j.running_window("code") == "Code.exe" and j.running_window("explorer") == "explorer.exe"
assert j.running_window("plorer") == "explorer.exe" and j.running_window("chr") == "chrome.exe"

# mute / unmute set the state they name, never a toggle
assert j.route("mute")[:2] == ("act", "mute") and j.route("unmute the sound")[:2] == ("act", "unmute")
j.ACTIONS["mute"](None), j.ACTIONS["unmute"](None)
assert muted_to == [True, False], muted_to

# volume and media: commands act, questions and other sentences do not, and the level stays inside 0-100
vol, keys = [40], []


def _speakers(mute=None, volume=None):
    if volume is not None:
        vol[0] = round(volume * 100)
    return (False, vol[0])


brist = [60]                                                     # the screen brightness


def _bright(percent=None):
    if percent is not None:
        brist[0] = percent
    return brist[0]


j.screen_brightness = _bright
themest = ["dark"]                                               # the Windows colour mode


def _theme(mode=None):
    if mode is not None:
        themest[0] = mode
    return themest[0]


j.theme_mode = _theme
micst = [False, 70]                                              # the microphone: (muted, percent)


def _mic(mute=None, volume=None):
    if volume is not None:
        micst[1] = round(volume * 100)
    if mute is not None:
        micst[0] = bool(mute)
    return tuple(micst)


j.mic_volume = _mic
j.speakers, j.press_key = _speakers, keys.append
for heard, want in (("set volume to 30", ("set", 30)), ("volume 5 percent", ("set", 5)), ("turn it up", ("step", 10)),
                    ("Jarvis, can you turn the volume down?", ("step", -10)), ("louder", ("step", 10)),
                    ("turn down the music", ("step", -10))):
    assert j.route(heard)[:3] == ("act", "volume", want), heard
assert j.route("set volume to 130") == ("say", None, None, "I can set it between 0 and 100.")
for heard, want in (("pause", "playpause"), ("resume the music", "playpause"), ("stop the music", "playpause"),
                    ("next track", "next"), ("skip", "next"), ("previous song", "prev"), ("go back a song", "prev")):
    assert j.route(heard)[:3] == ("act", "media", want), heard
for heard in ("should I turn it up?", "how do I pause a download?", "play despacito", "what volume is 30 decibels", "stop"):
    assert j.route(heard)[0] == "chat", heard
j.ACTIONS["volume"](("set", 30))
assert vol == [30] and j.done_line("volume", None) == "Volume at 30 percent."
j.ACTIONS["volume"](("step", -10)), j.ACTIONS["volume"](("step", -50))
assert vol == [0]
j.ACTIONS["volume"](("set", 95)), j.ACTIONS["volume"](("step", 10))
assert vol == [100]
j.ACTIONS["media"]("next")
assert keys == [0xB0] and j.done_line("media", "next") == "Sent."

# actions report what really happened: every failure is "not done" plus one problem line
j.log = lambda *a: None
failed = []
j.problem = lambda msg, popup=True: failed.append(msg)
assert j.run_action("shutdown", None, ("shutdown", None)) and ran[-1] == ["shutdown", "/s", "/t", "10"] and not failed
assert not j.run_action("format disk", None), "only listed actions can run"
# 7-L1: a PC that cannot sleep (Modern Standby) only turns the screen off, and the reply says so
import types as _t
_wd, _win, _susp = j.ctypes.WinDLL, j.ctypes.windll, [0]
j.ctypes.WinDLL = lambda *a, **k: _t.SimpleNamespace(SetSuspendState=lambda *x: _susp[0])
j.ctypes.windll = _t.SimpleNamespace(user32=_t.SimpleNamespace(PostMessageW=lambda *x: 1))
try:
    j.ACTIONS["sleep"](None)
    assert j.done_line("sleep", None) == "This PC can't sleep that way, so I turned the screen off."
    _susp[0] = 1
    j.ACTIONS["sleep"](None)
    assert j.done_line("sleep", None) == "Done."
finally:
    j.ctypes.WinDLL, j.ctypes.windll = _wd, _win
# 7-0: the action table. An "ask" row never runs without the pending action the user said yes to
assert set(j.ACTIONS) == set(j.ACTION_TABLE) and all(r.risk in ("read", "change", "ask") and r.desc for r in j.ACTION_TABLE.values())
for name, row in j.ACTION_TABLE.items():
    if row.risk == "ask":
        ran.clear()
        assert not j.run_action(name, None) and not ran, f"{name}: ask-first, refused without a yes"
        assert not j.run_action(name, None, ("other", None)) and not ran, "a yes for another action is not a yes"
# 7c: brightness. Said phrases reach the fixed action; "a bit" is 10; 0 is allowed; the reply is what Windows reports
for heard, want in (("set the brightness to 40", ("set", 40)), ("brightness to 0", ("set", 0)), ("set the screen brightness to eighty percent", ("set", 80)),
                    ("dim the screen", ("step", -10)), ("make the screen brighter", ("step", 10)), ("turn up the brightness", ("step", 10)),
                    ("turn the brightness down a bit", ("step", -10)), ("lower the brightness", ("step", -10)), ("brighten the display", ("step", 10))):
    assert j.route(heard) == ("act", "brightness", want, None), (heard, j.route(heard))
assert j.route("set the brightness to 150")[0] == "say" and j.route("why is my screen dim?")[0] == "chat"
brist[0] = 60
assert j.run_action("brightness", ("set", 30)) and brist[0] == 30 and j.done_line("brightness", None) == "Brightness is at 30 percent."
assert j.undo_last() == "Brightness back at 60 percent." and brist[0] == 60
assert j.run_action("brightness", ("step", -500)) and brist[0] == 0 and j.run_action("brightness", ("step", 500)) and brist[0] == 100
# the real reader: one fixed PowerShell line, only an integer in it; a level Windows did not take is an error
_run, cmds = j.subprocess.run, []
j.subprocess.run = lambda args, **k: cmds.append(args[-1]) or _t.SimpleNamespace(returncode=0, stdout="45\r\n")
try:
    assert real_brightness(45) == 45 and "WmiSetBrightness(1,45)" in cmds[-1] and real_brightness() == 45 and "Set" not in cmds[-1]
    try:
        real_brightness(80)
        assert False, "a brightness Windows did not take is an error"
    except OSError:
        pass
finally:
    j.subprocess.run = _run
# 7c: dark and light mode: both registry values, only two fixed values, read back; "turn off dark mode" is light
for heard, want in (("switch to dark mode", "dark"), ("turn on light mode", "light"), ("dark mode", "dark"), ("use the light theme", "light"),
                    ("turn off dark mode", "light"), ("turn off light mode", "dark"), ("go to dark mode", "dark")):
    assert j.route(heard) == ("act", "theme", want, None), (heard, j.route(heard))
assert j.route("why is dark mode better?")[0] == "chat"
themest[0] = "dark"
assert j.run_action("theme", "light") and themest[0] == "light" and j.done_line("theme", "light") == "Light mode is on."
assert j.undo_last() == "Back to dark mode." and themest[0] == "dark"
# 7c/7d: settings pages (a fixed table), screenshot, show desktop, recycle bin
for heard, want in (("open bluetooth settings", ("bluetooth", "")), ("open the sound settings", ("sound", "")), ("open wi-fi settings", ("wifi", "")),
                    ("open installed apps", ("apps", "")), ("open startup apps", ("startup", "")), ("open storage settings", ("storage", "")),
                    ("open windows update", ("update", "")), ("are there updates", ("update", "")), ("turn on night light", ("night light", "noswitch")),
                    ("turn off do not disturb", ("focus", "noswitch")), ("battery saver on", None), ("what starts with windows", ("startup", "nolist")),
                    ("open night light settings", ("night light", ""))):
    got = j.route(heard)
    assert (got == ("act", "page", want, None)) if want else got[1] != "page", (heard, got)
assert j.route("open sound")[1] != "page" and j.route("open the display")[1] != "page"   # a bare common word could be an app
assert j.route("take a screenshot") == ("act", "screenshot", None, None) and j.route("show the desktop") == ("act", "desktop", None, None)
assert j.route("empty the recycle bin")[:3] == ("act", "recycle", None) and "can't be undone" in j.route("empty the recycle bin")[3]
opened, _sf = [], j.os.startfile
j.os.startfile = opened.append
try:
    assert j.run_action("page", ("wifi", "")) and opened == ["ms-settings:network-wifi"]
    assert j.done_line("page", ("update", "")) == "Opening the Windows Update settings."
    assert j.done_line("page", ("night light", "noswitch")) == "Windows has no switch for that, so I opened the Night light settings."
    assert j.undo_last() == "I can't undo that."
finally:
    j.os.startfile = _sf
assert not j.run_action("recycle", None)                  # ask-first: refused without the yes (and so never reaches Windows)
class _Shell:                                                    # a fake shell32: the recycle bin and the screenshot folder
    code = 0
    SHEmptyRecycleBinW = lambda s, *a: s.code
    SHGetFolderPathW = lambda s, *a: None
_sh, j.ctypes.windll.shell32 = j.ctypes.windll.shell32, _Shell()
try:
    assert j.run_action("recycle", None, ("recycle", None)) and j.done_line("recycle", None) == "Recycle bin emptied."   # the fake, never the real bin
    _Shell.code = 0x8000FFFF
    j.act_recycle(None)
    _Shell.code = 5
    try:
        j.act_recycle(None)
        assert False, "a failed empty must be an error"
    except OSError:
        pass
finally:
    j.ctypes.windll.shell32 = _sh
shots, _pk, _pf, _sl = tempfile.mkdtemp(), j.press_keys, j.pictures_folder, j.time.sleep
os.makedirs(os.path.join(shots, "Screenshots"))
j.pictures_folder, j.time.sleep = lambda: shots, lambda s: None
try:
    j.press_keys = lambda *k: None                               # no file appears: not "saved"
    try:
        j.act_screenshot(None)
        assert False, "no new file must be an error"
    except OSError:
        pass
    j.press_keys = lambda *k: open(os.path.join(shots, "Screenshots", "a.png"), "w").close()
    j.act_screenshot(None)
finally:
    j.press_keys, j.pictures_folder, j.time.sleep = _pk, _pf, _sl
# 7d: power mode: only Balanced / Best performance, only plans the machine lists, asks first, read back, undo
BAL, HIGH, SAVER = "381b4222-f694-41f0-9685-ff5bb260df2e", "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c", "a1841308-3541-4fab-bc81-f71556f20b4a"
pw = {"active": BAL, "listed": [BAL, HIGH, SAVER], "calls": []}


def _powercfg(args, **k):
    pw["calls"].append(args)
    if args[1] == "/setactive":
        pw["active"] = args[2]
        return _t.SimpleNamespace(returncode=0, stdout="")
    ids = pw["listed"] if args[1] == "/list" else [pw["active"]]
    return _t.SimpleNamespace(returncode=0, stdout=" ".join(f"Power Scheme GUID: {g}  (x)" for g in ids))


_run = j.subprocess.run
j.subprocess.run = _powercfg
try:
    assert j.route("switch the power mode to balanced")[:3] == ("act", "power", "balanced") and "Confirm with yes" in j.route("best performance mode")[3]
    assert j.route("set the power plan to best performance")[2] == "performance" and j.route("use the balanced power mode")[2] == "balanced"
    r = j.route("switch to power saver mode")
    assert r[0] == "say" and "power saver" in r[3] and j.route("battery saver mode")[0] == "say"
    assert not j.run_action("power", "performance") and pw["active"] == BAL           # ask-first: refused without the yes
    assert j.run_action("power", "performance", ("power", "performance")) and pw["active"] == HIGH
    assert j.done_line("power", "performance") == "Power mode is Best performance."
    assert j.undo_last() == "Power mode back to Balanced." and pw["active"] == BAL
    pw["listed"] = [BAL]                                         # this PC lists only Balanced: no performance plan, nothing switched
    assert not j.run_action("power", "performance", ("power", "performance")) and pw["active"] == BAL
    assert not j.run_action("power", SAVER, ("power", SAVER)) and pw["active"] == BAL   # a raw id outside the allowed list never runs
    assert all(a[1] != "/setactive" or a[2] in (BAL, HIGH) for a in pw["calls"])
    pw["listed"] = [BAL, HIGH, SAVER]
    assert not j.run_action("power", SAVER, ("power", SAVER)) and pw["active"] == BAL
finally:
    j.subprocess.run = _run
# 7b: Bluetooth radio on/off (off asks first), pairing and connecting open the page, undo, nothing from speech in the script
btst = ["off"]
btcalls = []


def _btrun(args, **k):
    btcalls.append(args[-1])
    if "SetStateAsync('On')" in args[-1]:
        btst[0] = "on"
    elif "SetStateAsync('Off')" in args[-1]:
        btst[0] = "off"
    return _t.SimpleNamespace(returncode=0, stdout=btst[0].capitalize() + " ")


_run = j.subprocess.run
j.subprocess.run = _btrun
try:
    for heard in ("turn on bluetooth", "turn bluetooth on", "enable bluetooth", "switch on the bluetooth"):
        assert j.route(heard) == ("act", "bluetooth", "on", None), (heard, j.route(heard))
    for heard in ("turn off bluetooth", "turn bluetooth off", "disable my bluetooth"):
        assert j.route(heard)[:3] == ("act", "bluetooth_off", None) and "Confirm with yes" in j.route(heard)[3], heard
    assert j.route("pair a new device") == ("act", "page", ("bluetooth", ""), None)
    _bd = j.bt_devices
    def _nolist():
        raise OSError("x")
    j.bt_devices = _nolist                                     # a list Windows will not give: the page opens, as before 7b-connect
    for heard in ("connect my airpods", "disconnect from the headphones", "connect to my sony headphones"):
        assert j.route(heard) == ("act", "page", ("bluetooth", "noconnect"), None), (heard, j.route(heard))
    j.bt_devices = _bd
    assert j.route("how do I turn on bluetooth?")[0] == "chat"
    btst[0] = "off"
    assert j.run_action("bluetooth", "on") and btst[0] == "on" and j.done_line("bluetooth", "on") == "Bluetooth is on."
    assert j.undo_last() == "Bluetooth back off." and btst[0] == "off"
    assert j.run_action("bluetooth", "on")
    assert not j.run_action("bluetooth_off", None) and btst[0] == "on"                      # ask-first: refused without the yes
    assert j.run_action("bluetooth_off", None, ("bluetooth_off", None)) and btst[0] == "off"
    assert j.undo_last() == "Bluetooth back on." and btst[0] == "on"
    assert all(c.count("SetStateAsync") <= 1 for c in btcalls) and all("'On'" in c or "'Off'" in c for c in btcalls if "SetStateAsync" in c)
    assert j.done_line("page", ("bluetooth", "noconnect")).startswith("I can't connect devices by voice yet")
    j.subprocess.run = lambda args, **k: _t.SimpleNamespace(returncode=3, stdout="")       # a PC with no Bluetooth radio
    assert not j.run_action("bluetooth", "on")
    j.subprocess.run = lambda args, **k: _t.SimpleNamespace(returncode=0, stdout="Off")    # Windows says on, radio stays off
    try:
        j.bluetooth_radio("on")
        assert False, "a radio that did not change is an error"
    except OSError:
        pass
finally:
    j.subprocess.run = _run
# 7-A6: stealth by voice: asks first, only the whitelisted name goes to the HUD, no voice undo
for heard in ("stealth mode", "go into stealth mode", "turn on stealth mode", "enter stealth"):
    assert j.route(heard)[:3] == ("act", "stealth", None) and "Confirm with yes" in j.route(heard)[3], heard
assert j.route("mute yourself") == ("act", "mute", None, None)
assert j.route("what is stealth mode")[0] == "chat"
sent = []
_ss = j.set_setting
j.set_setting = sent.append
try:
    assert not j.run_action("stealth", None) and sent == []                    # ask-first: refused without the yes
    assert j.run_action("stealth", None, ("stealth", None)) and sent == ["stealth"]
    assert j.undo_last() == "I can't undo that."                         # it cannot be put back by voice
finally:
    j.set_setting = _ss
try:
    j.set_setting("PerfOverride")
    assert False, "only whitelisted names may be sent"
except ValueError:
    pass
import re as _re
_jb = sys.modules["jarvislib.base"]
_sf0, _jb.STATE_FILE = _jb.STATE_FILE, os.path.join(tempfile.mkdtemp(), "jarvis.txt")   # never the live Data folder
try:
    j.set_setting("stealth")
    with open(_jb.STATE_FILE, encoding="utf-8") as f:
        assert _re.search(r"^HUD \d+ stealth$", f.read(), _re.M)
finally:
    _jb.STATE_FILE = _sf0
# 7-A6b: which microphone he listens to, by voice: a name that matches exactly one listed device, asks first, undo
_mics = {"headset": "Headset Microphone (USB Audio)", "array": "Microphone Array (Realtek)"}
_pm = j.pick_mic
j.pick_mic = lambda t: "" if t == "default" else _mics[t] if t in _mics else ["a", "b"] if t == "mic" else None
_set, sent, _cur = j.setting, [], ["Microphone Array (Realtek)"]
_ss = j.set_setting
j.set_setting = lambda n, v="": (sent.append((n, v)), _cur.__setitem__(0, v))
j.setting = lambda n, d="": _cur[0] if n == "JarvisMic" else _set(n, d)
try:
    r = j.route("use the headset microphone")
    assert r[:3] == ("act", "micdev", "Headset Microphone (USB Audio)") and "Confirm with yes" in r[3], r
    assert j.route("use the default mic")[:3] == ("act", "micdev", "")
    assert j.route("use the webcam microphone")[0] == "say" and "can't find" in j.route("use the webcam microphone")[3]
    assert j.route("use the mic microphone")[0] == "say" and "More than one" in j.route("use the mic microphone")[3]
    assert j.route("which microphone are you using")[3] == "I'm using the Microphone Array (Realtek) microphone."
    assert j.route("mute the microphone")[1] != "micdev"
    assert not j.run_action("micdev", "Headset Microphone (USB Audio)") and sent == []          # ask-first
    assert j.run_action("micdev", "Headset Microphone (USB Audio)", ("micdev", "Headset Microphone (USB Audio)"))
    assert sent == [("mic", "Headset Microphone (USB Audio)")]
    assert j.done_line("micdev", "Headset Microphone (USB Audio)").startswith("Listening through Headset Microphone")
    assert j.undo_last() == "Back to Microphone Array (Realtek)." and sent[-1] == ("mic", "Microphone Array (Realtek)")
finally:
    j.pick_mic, j.setting, j.set_setting = _pm, _set, _ss
import re as _re2
_jb2 = sys.modules["jarvislib.base"]
_sf1, _jb2.STATE_FILE = _jb2.STATE_FILE, os.path.join(tempfile.mkdtemp(), "jarvis.txt")
try:
    j.set_setting("mic", "Head\nset\x00 Mic")                  # control characters never reach the setting file
    with open(_jb2.STATE_FILE, encoding="utf-8") as f:
        assert _re2.search(r"^HUD \d+ mic Headset Mic$", f.read(), _re2.M)
finally:
    _jb2.STATE_FILE = _sf1
_jm = sys.modules["jarvislib.mic"]
_mf = _jm.MICS_FILE
_jm.MICS_FILE = os.path.join(tempfile.mkdtemp(), "mics.txt")
with open(_jm.MICS_FILE, "w", encoding="utf-8") as f:
    f.write("Headset Microphone (USB Audio)\nMicrophone Array (Realtek)\n")
assert _jm.pick_mic("headset") == "Headset Microphone (USB Audio)" and _jm.pick_mic("array") == "Microphone Array (Realtek)"
assert len(_jm.pick_mic("microphone")) == 2 and _jm.pick_mic("webcam") is None and _jm.pick_mic("the Windows default") == ""
_jm.MICS_FILE = _mf
# 7b: connect / disconnect a paired Bluetooth audio device: fake list, asks first, undo, no real device touched
_devs = [["AABBCCDDEEFF", "WH-1000XM4", False], ["112233445566", "AirPods Pro", True]]
_bd, _bl, _set = j.bt_devices, j.bt_link, j.setting
j.bt_devices = lambda: [tuple(d) for d in _devs]
j.setting = lambda n, d="": "WH-1000XM4=sony;AirPods Pro=my pods" if n == "JarvisBtNames" else _set(n, d)
linked = []
def _fake_link(addr, on):
    linked.append((addr, on))
    for d in _devs:
        if d[0] == addr:
            d[2] = on
j.bt_link = _fake_link
try:
    r = j.route("connect my sony headphones")
    assert r[:3] == ("act", "btlink", ("AABBCCDDEEFF", True, "WH-1000XM4")) and "Confirm with yes" in r[3], r
    assert j.route("connect the sony")[:3] == r[:3]                        # your own name for it, no generic word needed
    assert "already connected" in j.route("connect my airpods")[3]         # it is connected, so nothing to ask
    assert j.route("disconnect my airpods")[:3] == ("act", "btlink", ("112233445566", False, "AirPods Pro"))
    assert "More than one" in j.route("connect my headphones")[3]          # two paired and the word fits both
    assert j.route("connect to the vpn")[0] != "act"                       # not an audio device word: not touched
    assert "WH-1000XM4" not in j.route("which bluetooth devices are connected")[3] and "AirPods Pro" in j.route("which bluetooth devices are connected")[3]
    assert not j.run_action("btlink", ("AABBCCDDEEFF", True, "WH-1000XM4")) and linked == []     # ask-first
    ok = j.run_action("btlink", ("AABBCCDDEEFF", True, "WH-1000XM4"), ("btlink", ("AABBCCDDEEFF", True, "WH-1000XM4")))
    assert ok and linked == [("AABBCCDDEEFF", True)]
    assert j.done_line("btlink", ("AABBCCDDEEFF", True, "WH-1000XM4")) == "Connected to WH-1000XM4."
    assert j.done_line("btlink", ("AABBCCDDEEFF", False, "WH-1000XM4")) == "Disconnected from WH-1000XM4."
    assert j.undo_last() == "Disconnected from WH-1000XM4 again." and linked[-1] == ("AABBCCDDEEFF", False)
    _devs[:] = []
    assert "turn it on first" in j.route("connect my headphones")[3]
finally:
    j.bt_devices, j.bt_link, j.setting = _bd, _bl, _set
try:
    j.bt_link("AA; calc", True)
    assert False, "only a 12-digit hex address may reach the script"
except ValueError:
    pass
# 7-A9: a live-internet question gets a plain "can't look that up", not a guess; ordinary talk is not caught
for heard in ("What's the weather like today?", "what is the forecast for tomorrow", "any news today", "what's the latest news", "bitcoin price",
              "what's the exchange rate for euros"):
    assert j.no_data(heard, set()) == "I can't look that up yet.", heard
for heard in ("write a story about a storm", "what's a good name for a weather app", "explain how a news feed works", "tell me a joke"):
    assert j.no_data(heard, set()) is None, heard
# 7-A8: "open <app>" brings an app that is already open forward (ShipCore focus) and starts one that is not
ran, started, _ow, _sf, _ro, _ex = [], [], j.open_windows, j.os.startfile, j.run_ok, j.os.path.exists
j.open_windows, j.os.startfile, j.run_ok, j.os.path.exists = (lambda: ["chrome.exe"]), started.append, ran.append, (lambda p: True)
try:
    j.act_open(("Google Chrome", "C:/Apps/chrome.exe"))
    assert ran and ran[0][1:] == ["focus", "chrome.exe", "C:/Apps/chrome.exe"] and not started, (ran, started)
    ran.clear()
    j.act_open(("Notepad", "C:/Apps/notepad.exe"))                  # not running: started as before
    assert not ran and started == ["C:/Apps/notepad.exe"]
    started.clear()
    j.act_open(("Calculator", "Microsoft.WindowsCalculator_8wekyb3d8bbwe!App"))
    assert not ran and started == ["shell:AppsFolder\\Microsoft.WindowsCalculator_8wekyb3d8bbwe!App"], started
finally:
    j.open_windows, j.os.startfile, j.run_ok, j.os.path.exists = _ow, _sf, _ro, _ex
class _Reg:                                                      # a fake winreg: nothing of the real registry is touched
    HKEY_CURRENT_USER, KEY_READ, KEY_SET_VALUE, REG_DWORD, vals = 1, 1, 2, 4, {"AppsUseLightTheme": 0, "SystemUsesLightTheme": 0}
    class _K:
        __enter__, __exit__ = lambda s: s, lambda s, *a: None
    OpenKey = lambda s, *a: s._K()
    SetValueEx = lambda s, key, name, r, t, v: s.vals.__setitem__(name, v)
    QueryValueEx = lambda s, key, name: (s.vals[name], 4)
_wr, j.winreg = j.winreg, _Reg()
try:
    assert real_theme() == "dark" and real_theme("light") == "light" and _Reg.vals == {"AppsUseLightTheme": 1, "SystemUsesLightTheme": 1}
    _Reg.vals["AppsUseLightTheme"] = 0
    assert real_theme() == "mixed"
finally:
    j.winreg = _wr
# 7a: the microphone. Said phrases reach the fixed actions; mute asks first; the reply is what Windows reports
for heard, want in (("mute the microphone", ("act", "mic_mute", None)), ("mute my mic", ("act", "mic_mute", None)),
                    ("unmute the microphone", ("act", "mic_unmute", None)), ("set the microphone to 80 percent", ("act", "mic_level", ("set", 80))),
                    ("set my mic to fifty", ("act", "mic_level", ("set", 50))), ("turn the mic up a bit", ("act", "mic_level", ("step", 10))),
                    ("turn down the microphone", ("act", "mic_level", ("step", -10))), ("lower the microphone", ("act", "mic_level", ("step", -10))),
                    ("mute", ("act", "mute", None)), ("set the microphone to 150", ("say", None, None))):
    r = j.route(heard)
    assert r[:3] == want[:3] and (r[3] is None) == (want[1] != "mic_mute" and want[0] != "say"), (heard, r)
assert j.route("mute the microphone")[3].endswith("Confirm with yes.")
micst[:] = [False, 70]
assert j.run_action("mic_level", ("set", 80)) and micst == [False, 80] and j.done_line("mic_level", None) == "Microphone at 80 percent."
assert j.undo_last() == "Microphone back at 70 percent." and micst == [False, 70]
assert j.run_action("mic_level", ("step", 50)) and micst[1] == 100 and j.run_action("mic_level", ("step", -500)) and micst[1] == 0
assert j.run_action("mic_mute", None, ("mic_mute", None)) and micst[0] and j.done_line("mic_mute", None) == "Microphone muted."
assert j.undo_last() == "Microphone unmuted." and not micst[0]
micst[0] = True
assert j.run_action("mic_unmute", None) and j.done_line("mic_unmute", None) == "Microphone unmuted." and j.undo_last() == "Microphone muted." and micst[0]
micst[:] = [False, 70]
_Done.returncode = 1190                                           # non-zero exit code
assert not j.run_action("restart", None, ("restart", None))
_Done.returncode = 0


def _hang(args, **kw):
    raise j.subprocess.TimeoutExpired(args, kw["timeout"])


j.subprocess.run = _hang                                          # the command never comes back
assert not j.run_action("shutdown", None, ("shutdown", None))
j.subprocess.run = _run


def _api_down(on):
    raise OSError("no audio endpoint")


j.speakers_mute = _api_down                                       # the Windows call fails
assert not j.run_action("mute", None)
j.speakers = lambda **kw: _api_down(kw)
assert not j.run_action("volume", ("set", 30)) and vol == [100]
j.speakers = _speakers
ran.clear()
assert not j.run_action("close", "notepad.exe", ("close", "notepad.exe")) and not ran, "missing target: nothing is sent"
assert not j.run_action("close", "chrome.exe", ("close", "chrome.exe")) and ran == [["taskkill", "/IM", "chrome.exe"]], "asked, but it stayed open"
now_t = int(j.time.time())
j.read_kv = lambda name: f"T {now_t}\nW chrome.exe\n" if not ran else f"T {now_t - 60}\nW explorer.exe\n"
ran.clear()
assert not j.run_action("close", "chrome.exe", ("close", "chrome.exe")), "a stale window list (ShipCore stopped) proves nothing"
j.read_kv = lambda name: f"T {now_t}\nW chrome.exe\n" if not ran else ""
ran.clear()
assert not j.run_action("close", "chrome.exe", ("close", "chrome.exe")), "an unreadable window list (mid-swap) is not 'closed'"
j.read_kv = lambda name: f"T {now_t}\nW chrome.exe\n" if not ran else f"T {now_t}\nW explorer.exe\n"
ran.clear()
assert j.run_action("close", "chrome.exe", ("close", "chrome.exe")), "closed once the window is gone"
assert len(failed) == 13, failed
j.read_kv = lambda name: "W chrome.exe\nW explorer.exe\nW Code.exe\n"
j.time.sleep = real_sleep

# HUD readings: every source that answers gets a line; an unmapped or missing sensor, a stale file or a hanging tool
# costs only its own line
real_settings, real_gpu = j.settings, j.gpu
j.settings = lambda: {"HW_CpuTemp": "3", "HW_GpuTemp": "-1", "HW_Fan1": "9"}


def _hw(n):
    if n == 9:
        raise OSError("no such sensor")
    return 61.4


class _Smi:
    returncode, stdout = 0, "37, 2048, 8192\n"


ticks = iter([(100, 1000), (150, 1200)])
j.hw_value, j.cpu_times, j.gpu = _hw, lambda: next(ticks), lambda: True
j.subprocess.run = lambda args, **kw: _Smi()
j.read_kv = lambda name: f"T {int(j.time.time())}\nBRIGHT 70\nMIC -1\nMICMUTE 0\n"
real_load, j.load_reminders = j.load_reminders, lambda: [(j.time.time() + 600, 0, "reminder", "to cook")]
got = j.sensors()
assert "Pending: reminder at " in got and "cook" not in got, got   # what kind and when, not what it says
for line in ("CPU temperature: 61 C", "CPU load: 75%", "GPU load: 37%, video memory 2.0 of 8 GB in use",
             "Speaker volume: 100%", "Screen brightness: 70%", "GB free of"):
    assert line in got, (line, got)
assert "GPU temperature" not in got and "Fan 1" not in got and "Microphone" not in got, got
j.subprocess.run, j.read_kv = _hang, lambda name: "T 5\nBRIGHT 70\n"
got = j.sensors()                                                 # nvidia-smi hangs, the HUD's file is old, no CPU sample
assert "CPU temperature: 61 C" in got and not [x for x in ("GPU load", "brightness", "CPU load") if x in got], got
j.load_reminders = lambda: [(j.time.time() + 60, 0, "timer", ""), (j.time.time() + 600, 0, "reminder", "alarm")]
assert "Pending: timer with 1 minute left; alarm at " in j.sensors()   # an alarm is named an alarm, never a timer
j.load_reminders = lambda: []
assert "Pending: no alarms, reminders or timers" in j.sensors()     # nothing pending is said, so the model never guesses
j.subprocess.run, j.settings, j.gpu, j.load_reminders = _run, real_settings, real_gpu, real_load
j.read_kv = lambda name: "W chrome.exe\nW explorer.exe\nW Code.exe\n"

# model choice: the wanted model, else the other configured one, never an arbitrary or embedding model
real_setting, conf = j.setting, {"JarvisModel": "big:7b", "JarvisModelFast": "small:3b"}
j.setting = lambda name, default="": conf.get(name, default)
j.installed_models = lambda: ["big:7b", "nomic-embed-text:latest", "small:3b"]
assert j.pick_model(0) == "big:7b" and j.pick_model(1) == "small:3b"
j.installed_models = lambda: ["nomic-embed-text:latest", "small:3b"]
assert j.pick_model(0) == "small:3b", "missing model: the other configured one"
j.installed_models = lambda: ["aaa-embed:latest", "nomic-embed-text:latest"]
assert j.pick_model(0) is None and j.pick_model(1) is None, "embedding models only: no model"
j.installed_models = lambda: []
assert j.pick_model(0) is None
j.installed_models = lambda: None                                 # Ollama not answering: keep the wanted name
assert j.pick_model(0) == "big:7b"

# vault: a folder you set is trusted; the to-do note's folder counts only with .obsidian in it or up to three above
import tempfile
tmp = tempfile.mkdtemp()
for d in (("vault", ".obsidian"), ("vault", "a", "b"), ("loose",)):
    os.makedirs(os.path.join(tmp, *d))
for p in (("vault", "a", "b", "todo.md"), ("loose", "todo.md")):
    open(os.path.join(tmp, *p), "w").close()
conf["ObsidianTodo"] = os.path.join(tmp, "loose", "todo.md")
assert j.vault_dir() == "", "a to-do note outside a vault: no vault"
conf["ObsidianTodo"] = os.path.join(tmp, "vault", "a", "b", "todo.md")
assert j.vault_dir() == os.path.join(tmp, "vault")
conf["JarvisVault"] = os.path.join(tmp, "loose")
assert j.vault_dir() == os.path.join(tmp, "loose")
j.setting = real_setting

# app list: a missing file is "not ready", an empty one is "no apps"
fake_apps, j.start_apps, real_data, j.DATA = j.start_apps, real_start_apps, j.DATA, tmp
assert j.start_apps() is None and j.best_app("chrome") is None
assert j.route("open chrome") == ("say", None, None, "The app list isn't ready yet.")
open(os.path.join(tmp, "StartApps.txt"), "w").close()
assert j.start_apps() == [] and j.route("open chrome")[0] == "chat"
j.start_apps, j.DATA = fake_apps, real_data

# memory: a failed Windows call leaves the line out instead of reporting 0 %
real_settings, j.settings = j.settings, lambda: {}
assert "Memory in use" in j.context()
j.ctypes.windll.kernel32.GlobalMemoryStatusEx = lambda p: 0
assert "Memory in use" not in j.context()
del j.ctypes.windll.kernel32.GlobalMemoryStatusEx

# 6a: only the HUD blocks a question needs reach the prompt; a briefing, or no question, gets all of them
import time as _t
kv = {"mail.txt": "UNREAD 3", "windows.txt": "W chrome.exe", "net.txt": "DOWN 1000\nUP 1000",
      "calendar.txt": f"E {int(_t.time()) + 3600}|{int(_t.time()) + 7200}|0||Physics quiz"}
real_kv, real_mem, j.read_kv, j.load_memory = j.read_kv, j.load_memory, lambda name: kv.get(name, ""), lambda: []
heads = {"calendar": "Physics quiz", "mail": "Unread Gmail", "apps": "Open apps", "net": "Network right now",
         "pc": "Memory in use"}


def blocks(text, kind=None):
    c = j.context(text, kind)
    assert c.startswith("Now:"), c                                # the time is always there
    return {b for b, h in heads.items() if h in c}


assert blocks("Tell me a joke.") == blocks("What's the capital of France?") == set()
assert blocks("What's on tomorrow?") == blocks("Do I have a quiz this week?") == {"calendar"}
assert blocks("How hot is my GPU?") == blocks("Why is the computer so slow") - {"apps"} == {"pc"}
assert blocks("Any new email?") == {"mail"} and blocks("Is the wifi working?") == {"net"}
assert blocks("Is Chrome open?") == {"apps"}
assert blocks("Anything Friday?") == blocks("What's due this weekend") == {"calendar"}
assert "pending" in j.wants("Did you set it?") and "pending" in j.wants("wake me at 7 am")
assert "pending" not in j.wants("Tell me a joke.") and "pending" not in j.wants("What's the capital of France?")
assert blocks("Good morning.", "brief") == blocks(None) == set(heads)
assert "Physics quiz" not in j.system_prompt("Tell me a joke.") and "Physics quiz" in j.system_prompt()
assert "Answer only what was asked." in j.system_prompt("Tell me a joke.")
real_me, j.about_me = j.about_me, lambda: "word " * 400                 # the profile: only for questions about you
assert "ABOUT THE USER" not in j.system_prompt("Tell me a joke.")
mine = j.system_prompt("What's my sister's name?")
assert "ABOUT THE USER" in mine and "word " * 99 in mine and "word " * 101 not in mine
assert "word " * 399 in j.system_prompt() and "word " * 399 in j.system_prompt("Good morning.", "brief")
j.read_kv, j.load_memory, j.about_me = real_kv, real_mem, real_me
j.settings = real_settings

# the model stream: normal replies come through, and a cancel ends it even while the request is still blocked
import threading
import time


class _Resp(list):
    __enter__ = lambda self: self
    __exit__ = lambda self, *a: False


j.urllib.request.urlopen = lambda *a, **k: _Resp([b'{"message":{"content":"hi"}}\n', b'\n', b'{"done":true}\n'])
assert list(j.chat_stream("m", [])) == ["hi"]
j.urllib.request.urlopen = lambda *a, **k: time.sleep(3)          # a model that is still loading
threading.Timer(0.3, j.cancel.set).start()
t0 = time.time()
assert list(j.chat_stream("m", [])) == [] and time.time() - t0 < 1.5, time.time() - t0
j.cancel.clear()

# idle unload: only after the idle time, never during a turn, never when switched off
j.log = lambda *a: None
minutes = ["10"]
j.setting = lambda key, default="": minutes[0] if key == "JarvisIdleUnload" else default
j._whisper, j._engines["v"] = object(), object()
assert not j.unload_idle(599, 0) and j._whisper is not None
minutes[0] = "0"
assert not j.unload_idle(9999, 0)
minutes[0] = "10"
with j.busy:
    assert not j.unload_idle(9999, 0)
assert j.unload_idle(601, 0) and j._whisper is None and not j._engines
assert not j.unload_idle(9999, 0)                                 # nothing left to unload

# note index: while a reindex runs, a second one is skipped and the search lock stays free
j.vault_dir = lambda: "R"
j._chroma.update(col="COL", root="R", last=0.0, failed=False)
with j._reindexing:
    assert j.chroma_index(force=True) == "COL" and not j._chroma_lock.locked()
assert not j._reindexing.locked()


class _Col:
    def delete(self, where):
        dropped.append(where["path"])


# a note that is gone from the vault is taken out of the index
dropped, empty = [], os.path.join(tmp, "loose", "none")
os.makedirs(empty)
j.vault_dir = lambda: empty
j._chroma.update(col=_Col(), root=empty, seen={"old.md": 1.0}, last=0.0, failed=False)
assert j.chroma_index(force=True) is j._chroma["col"] and dropped == ["old.md"] and not j._chroma["seen"]

# a note locked or deleted mid-sync is skipped, not the end of smart search; the next pass tries it again
with open(os.path.join(empty, "locked.md"), "w", encoding="utf-8") as f:
    f.write("x")
def _locked(*a, **k):
    raise PermissionError("locked")
j.open = _locked                                                   # shadows the builtin inside jarvis only
try:
    assert j.chroma_index(force=True) is j._chroma["col"] and not j._chroma["failed"] and not j._chroma["seen"]
finally:
    del j.open
os.remove(os.path.join(empty, "locked.md"))

# GPU asked for but absent: speech recognition lands on a capped CPU model and says so without a pop-up
import types
made, said = [], []
class FakeWhisper:
    def __init__(self, size, device, compute_type, cpu_threads=0):
        if device == "cuda":
            raise RuntimeError("no CUDA device")
        made.append(cpu_threads)
sys.modules["faster_whisper"] = types.SimpleNamespace(WhisperModel=FakeWhisper)
j.setting = lambda name, default: "cuda" if name == "JarvisWhisperDevice" else default
j.problem = lambda msg, popup=True: said.append((msg, popup))
j.gpu = lambda: True                                              # the card is there, the load still failed
j._whisper = None
j.whisper()
assert made == [j.cpu_threads()] and 2 <= made[0] <= max(2, (os.cpu_count() or 8) // 4)
assert len(said) == 1 and said[0][0].startswith("CPU in use") and said[0][1] is False
j.setting = lambda name, default: "gpu" if name == "JarvisWhisperDevice" else default     # a mistyped device
j._whisper = None
j.whisper()
assert "JarvisWhisperDevice=gpu" in said[-1][0], said[-1]

# Phase 2: off the card only until it is back
card, made = [False], []
class CardWhisper:
    def __init__(self, size, device, compute_type, cpu_threads=0):
        if device == "cuda" and not card[0]:
            raise RuntimeError("no CUDA device")
        real_sleep(0.05)                                          # slow enough that two loads at once would overlap
        self.device = device
        made.append(device)
    def transcribe(self, audio, **k):
        if self.device == "cuda" and not card[0]:
            raise RuntimeError("CUDA error: device lost")
        return [types.SimpleNamespace(text="hello")], None
def until(check):
    for _ in range(200):
        if check():
            return True
        real_sleep(0.02)
    return False
sys.modules["faster_whisper"] = types.SimpleNamespace(WhisperModel=CardWhisper)
j.setting = lambda name, default: default
j.gpu = lambda: card[0]
j._whisper = None
j.whisper()                                                       # the card is off: the plain reason, no pop-up
assert made == ["cpu"] and j._whisper_dev[0] == "cpu"
assert said[-1] == ("RTX is off - switch the laptop to hybrid graphics", False), said[-1]
card[0], t = True, j._gpu_try[0]                                  # the card comes back
with j.busy:
    assert not j.gpu_watch(t + 61)                                # never during a turn
assert not j.gpu_watch(t + 30)                                    # at most once a minute
j.S.err = "RTX is off - switch the laptop to hybrid graphics"
assert j.gpu_watch(t + 61) and until(lambda: j._whisper_dev[0] == "cuda") and made == ["cpu", "cuda"]
assert until(lambda: j.S.err == ""), j.S.err                      # back on the card: the warning goes too
assert not j.gpu_watch(t + 200)                                   # already on the card
card[0] = False                                                   # the card drops out mid-turn: that sentence on the CPU
assert real_transcribe("audio") == "hello" and j._whisper_dev[0] == "cpu"
card[0], t = True, j._gpu_try[0]
j.S.err = "No microphone found"
assert not j.gpu_watch(t + 30) and j.gpu_watch(t + 61) and until(lambda: j._whisper_dev[0] == "cuda")
assert j.S.err == "No microphone found"                           # other problems stay
j.S.err = ""
made.clear()                                                      # two threads at once load one model
j._whisper = None
both = [threading.Thread(target=j.whisper) for _ in range(2)]
[x.start() for x in both], [x.join() for x in both]
assert made == ["cuda"], made
# the chat model off the card: reloaded once, not on every turn, and not while the card is away
real_http, real_warm, posts = j.http_json, j.warm, []
j.http_json = lambda path, payload=None, timeout=5: posts.append(payload) or {}
j.warm = lambda m: posts.append("warm " + m)
assert j.chat_to_gpu("m") and not j.chat_to_gpu("m")
assert until(lambda: len(posts) == 2) and posts == [{"model": "m", "keep_alive": 0}, "warm m"], posts
card[0] = False
assert not j.chat_to_gpu("other")
j.http_json, j.warm, j.gpu = real_http, real_warm, real_gpu
j._moved.clear()
j._whisper = None
# the voice on the CPU is the design, not a problem line
vdir = tempfile.mkdtemp()
open(os.path.join(vdir, "voices-v1.0.bin"), "wb").close()
class FakeKokoro:
    def get_voices(self):
        return ["bm_lewis"]
    def create(self, text, voice, speed, lang):
        return [0.0, 0.1], 24000
real_mods, n = {m: sys.modules.get(m) for m in ("kokoro_onnx", "onnxruntime")}, len(said)
sys.modules["kokoro_onnx"] = types.SimpleNamespace(Kokoro=types.SimpleNamespace(from_session=lambda s, b: FakeKokoro()))
sys.modules["onnxruntime"] = types.SimpleNamespace(SessionOptions=types.SimpleNamespace, InferenceSession=lambda *a, **k: None)
assert j._kokoro(os.path.join(vdir, "kokoro-v1.0.int8.onnx"), "hi")[1] == 24000 and len(said) == n
assert j._voice_dev[0] == "cpu"                                   # no full model next to it: the CPU, as before
# Phase 2e: the full model on the RTX when it is there, the int8 one on the CPU otherwise
sessions, avail, broken = [], ["CUDAExecutionProvider", "CPUExecutionProvider"], [False]
class FakeSess:
    def __init__(self, path, opts=None, providers=None):
        self.path, self.prov = os.path.basename(path), [p[0] if isinstance(p, tuple) else p for p in providers or []]
        sessions.append(self)
    def get_providers(self):
        return [p for p in self.prov if p in avail]
class BreakingKokoro(FakeKokoro):
    def create(self, text, voice, speed, lang):
        if broken[0]:
            raise RuntimeError("CUDA error: device lost")
        return FakeKokoro.create(self, text, voice, speed, lang)
sys.modules["kokoro_onnx"] = types.SimpleNamespace(Kokoro=types.SimpleNamespace(from_session=lambda s, b: BreakingKokoro()))
sys.modules["onnxruntime"] = types.SimpleNamespace(SessionOptions=types.SimpleNamespace, InferenceSession=FakeSess,
                                                   get_available_providers=lambda: avail)
open(os.path.join(vdir, "kokoro-v1.0.onnx"), "wb").close()
int8 = os.path.join(vdir, "kokoro-v1.0.int8.onnx")
j._engines.clear()
real_dlls = j._cuda_dlls
j.gpu, j._cuda_dlls = lambda: True, lambda: None
assert j._kokoro(int8, "hi")[1] == 24000 and j._voice_dev[0] == "cuda"
assert (sessions[-1].path, sessions[-1].prov[0]) == ("kokoro-v1.0.onnx", "CUDAExecutionProvider")
broken[0] = True                                                  # the card drops out mid-sentence
try:
    j._kokoro(int8, "hi")
    assert False, "the error must reach synth_audio, which retries with a fresh engine"
except RuntimeError:
    j._engines.pop(int8, None)
broken[0] = False
assert j._kokoro(int8, "hi")[1] == 24000 and j._voice_dev[0] == "cpu"   # the retry runs on the CPU
assert (sessions[-1].path, sessions[-1].prov) == ("kokoro-v1.0.int8.onnx", ["CPUExecutionProvider"])
j._engines.clear(); j._voice_gpu_off[0] = 0.0
j.gpu = lambda: False                                             # card off: the CPU
assert j._kokoro(int8, "hi") and sessions[-1].path == "kokoro-v1.0.int8.onnx" and j._voice_dev[0] == "cpu"
j._engines.clear()
j.gpu = lambda: True; avail.remove("CUDAExecutionProvider")      # the CPU-only onnxruntime: the CPU
assert j._kokoro(int8, "hi") and sessions[-1].path == "kokoro-v1.0.int8.onnx" and j._voice_dev[0] == "cpu"
j.gpu, j._engines, j._cuda_dlls = real_gpu, {}, real_dlls
assert len(said) == n                                             # none of this is a problem line
for m, mod in real_mods.items():
    if mod is None:
        del sys.modules[m]
    else:
        sys.modules[m] = mod
j._engines.clear()

# muted: Windows is asked first, the HUD's file only when that fails
j.ENV_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "no-such-file")
j.speakers_mute = lambda on=None: True
assert j.muted() is True
j.speakers_mute = _api_down
assert j.muted() is False

# ---- the speech path, with fakes for the microphone, the voice, the speakers and the HUD state
states, played, words = [], [], []


class _S:
    def set(self, **kw):
        states.append(kw)


def within(seconds, fn, *args):
    """Run fn on a thread: a hang fails the check instead of freezing it. Returns the result or the exception."""
    out = []

    def run():
        try:
            out.append(fn(*args))
        except Exception as e:
            out.append(e)
    t = threading.Thread(target=run, daemon=True)
    t.start()
    t.join(seconds)
    assert not t.is_alive(), "still waiting"
    return out[0]


j.S, j.muted, j.live, j.filler_done = _S(), lambda: False, words.append, lambda: None
j.setting = lambda name, default="": default
real_synth_audio, real_play_samples, real_speak_all, real_windows = j.synth_audio, j.play_samples, j.speak_all, j._windows
j.synth_audio = lambda text: (text, 1)
j.play_samples = lambda a, rate, *_: played.append(a)
many =[str(i) for i in range(20)]

# more sentences than the queue holds: all spoken, in order
assert within(5, j.speak_all, many) == " ".join(many) and played == many   # 8-A2: returns what was said


# L8: while a sentence plays, the pop-up's live line types it word by word, after what was already said
def _typing(a, rate, progress=None):
    for f in (0.0, 0.5, 1.0):
        progress(f)


words.clear()
j.play_samples = _typing
within(5, j.speak_all, ["Hello there.", "How are you today?"])
assert words == ["Hello", "Hello there.", "Hello there. How", "Hello there. How are you",
                 "Hello there. How are you today?", ""], words
j.play_samples = lambda a, rate, *_: played.append(a)


def _breaks():
    yield "one"
    raise j.urllib.error.URLError("gone")


# the model stream dies mid-reply: the reader is not stranded and the turn gets the error
played.clear()
assert isinstance(within(5, j.speak_all, _breaks()), j.urllib.error.URLError) and played == ["one"]


def _no_voice(text):
    raise RuntimeError("voice broke")


# the voice fails: the words are shown instead and it still ends
j.synth_audio, n = _no_voice, len(said)
assert within(5, j.speak_all, ["hi"]) == "hi" and "hi" in words and said[n:] == [("Couldn't speak (voice failed) - the reply is in the log", False)]
j.synth_audio = lambda text: (text, 1)

# cancelled mid-utterance: the queued sentences are dropped, and a full queue does not hold the producer
played.clear()
j.play_samples = lambda a, rate, *_: (played.append(a), j.cancel.set())
assert within(5, j.speak_all, many) == "0" and played == ["0"]   # 8-A2: cut off: only the first sentence began
j.cancel.clear()
j.play_samples = lambda a, rate, *_: played.append(a)

# cancelled while a sentence is still being made
j.synth_audio = lambda text: time.sleep(3)
threading.Timer(0.2, j.cancel.set).start()
t0 = time.time()
within(5, j.speak_all, ["slow"])
assert time.time() - t0 < 1.5, time.time() - t0
j.cancel.clear()

# one owner of the microphone: a second taker is refused, and it is always handed back
with j.mic:
    assert isinstance(within(2, j.listen, 0.1), RuntimeError)
j._listen = lambda patience: "audio"
assert j.listen() == "audio" and not j.mic.locked()
j._listen = lambda patience: _no_voice("")
assert isinstance(within(2, j.listen), RuntimeError) and not j.mic.locked()

# a whole turn: every way out ends idle with the turn lock free
j.missing_packages, j.ensure_ollama, j.pick_model, j.warm = lambda: [], lambda: True, lambda tier: "m", lambda m: None
j.http_json = lambda *a, **k: (_ for _ in ()).throw(OSError("no Ollama in tests"))   # the AI fallback falls back
real_chime = j.chime
j.prepare_fillers, j.chime, j.watchdog, j.sensors = lambda: None, lambda: 0, lambda started: None, lambda: "Fan 1: 900 RPM"
idle = {"state": "idle", "level": 0.0}
states.clear()
with j.busy:                                                      # a second click while a turn runs does nothing
    j.turn(0)
assert not states
j.listen = lambda: None                                           # nobody spoke
j.turn(0)
assert states[-1] == idle and not j.busy.locked()
j.listen, j.transcribe = lambda: "audio", _no_voice               # speech recognition fails
j.turn(0)
assert said[-1] == ("voice broke", True) and states[-1] == idle and not j.busy.locked()
# JarvisGPU=require with the card off: the fixed line, no listening, no model
real_setting, real_listen, touched = j.setting, j.listen, []
j.setting = lambda name, default="": "require" if name == "JarvisGPU" else default
j.gpu, j.ensure_ollama, j.listen = lambda: False, lambda: touched.append("ollama"), lambda *a, **k: touched.append("mic")
j.turn(0)
assert touched == [] and j.recent["me"] == "My graphics card is off." and states[-1] == idle and not j.busy.locked()
j.setting, j.listen, j.ensure_ollama, j.gpu = real_setting, real_listen, lambda: True, real_gpu

# ---- timers and reminders: read by code (never the model), kept in a file, rung by alarm()
from datetime import datetime


def cmd(text):
    kind, op, args, _ = j.route(text)
    return (op,) + tuple(args) if kind == "remind" else None


def ahead(text):
    """(kind, seconds from now, label) of a "set" command."""
    _, kind, due, label, _ = cmd(text)
    return kind, None if due is None else round(due - time.time()), label


for text, want in (
        ("Remind me to cook in 20 minutes.", ("reminder", 1200, "to cook")),
        ("remind me in 20 minutes to cook food", ("reminder", 1200, "to cook food")),
        ("Hey Jarvis, remind me to call my mum in an hour and a half", ("reminder", 5400, "to call your mum")),
        ("remind me about the meeting in two hours", ("reminder", 7200, "about the meeting")),
        ("remind me in half an hour", ("reminder", 1800, "")),
        ("remind me to look at the oven in twenty five minutes", ("reminder", 1500, "to look at the oven")),
        ("set a reminder for the dentist in 1 hour 30 minutes", ("reminder", 5400, "about the dentist")),
        ("remind me to cook", ("reminder", None, "to cook")),
        ("Set a timer for 10 minutes.", ("timer", 600, "")),
        ("Can you set a timer for 10 minutes?", ("timer", 600, "")),
        ("ten minute timer for the pasta", ("timer", 600, "the pasta")),
        ("set a 5-minute timer", ("timer", 300, "")),
        ("start a timer for the eggs for 90 seconds", ("timer", 90, "the eggs")),
        ("set a pasta timer for two minutes and 30 seconds", ("timer", 150, "pasta")),
        ("set a timer", ("timer", None, ""))):
    assert ahead(text) == want, (text, ahead(text))
for text in ("How do I set a timer in Python?", "what is a timer", "open timer", "What's the best reminder app?",
             "should I set a timer?", "remind", "stop the music", "what timer should I buy",
             "Can you remind me what the capital of France is?", "remind me how this works"):
    assert cmd(text) is None, text
assert ahead("remind me of the dentist in 2 hours") == ("reminder", 7200, "about the dentist")
assert cmd("What reminders do I have?") == ("list", "reminder") and cmd("list my timers") == ("list", "timer")
assert cmd("how much time is left on the timer") == ("list", "timer")
assert cmd("cancel the cooking reminder") == ("cancel", "reminder", "cooking")
assert cmd("Cancel all reminders.") == ("cancel", "reminder", "all") and cmd("stop the timer") == ("cancel", "timer", "")
assert cmd("cancel the timer for the pasta") == ("cancel", "timer", "the pasta")

# clock times, from 3 PM: the next time the clock shows it; anything unreadable is None, never a guess
at3 = datetime(2026, 10, 13, 15, 0).timestamp()


def hm(text):
    due = j.when(text, at3)
    return due and datetime.fromtimestamp(due).strftime("%d %H:%M")


for text, want in (("at 6:30 pm", "13 18:30"), ("at 18:30", "13 18:30"), ("at 6 30", "13 18:30"), ("at 7", "13 19:00"),
                   ("at 2", "14 02:00"), ("at 9 a.m.", "14 09:00"), ("at 12", "14 00:00"), ("at 12 pm", "14 12:00"),
                   ("at 25", None), ("at 6:75", None), ("at seven", "13 19:00"), ("in a bit", None), ("in 0 minutes", "13 15:00")):
    assert hm(text) == want, (text, hm(text))
assert j.clock(at3 + 12600, at3) == "6:30 PM" and j.clock(at3 + 65100, at3) == "9:05 AM tomorrow"
assert j.clock(at3 + 3 * 86400, at3) == "3:00 PM on Friday"
assert (j.span(600), j.span(5400), j.span(600, ""), j.span(90)) == ("10 minutes", "1 hour 30 minutes", "10 minute", "1 minute 30 seconds")
for item, want in (((at3, at3 - 1200, "reminder", "to cook food"), "Time to cook food."),
                   ((at3, at3 - 600, "timer", ""), "Your 10 minute timer is done."),
                   ((at3, at3 - 600, "timer", "the pasta"), "Your timer for the pasta is done."),
                   ((at3, at3 - 600, "reminder", "about the meeting"), "Reminder about the meeting."),
                   ((at3, at3 - 600, "reminder", "that the oven is on"), "Reminder: the oven is on."),
                   ((at3, at3 - 600, "reminder", ""), "This is your reminder.")):
    assert j.ring_line(item, at3 + 1) == want, j.ring_line(item, at3 + 1)
assert j.ring_line((at3, at3 - 60, "reminder", "to cook"), at3 + 600) == "Missed reminder from 3:00 PM: time to cook."

# set, list and cancel against a file in a temp folder; he says back what he set
j.REMIND_FILE = os.path.join(tmp, "reminders.txt")
asked, convo, acted = [], [], []
j.reply_line = lambda text, quiet: asked.append(text)
j.convo_add = lambda who, text: convo.append((who, text))


def do(text):
    kind, op, args, _ = j.route(text)
    assert kind == "remind", text
    return j.remind_reply(op, args, False)


assert j.due_reminders(time.time()) is False                      # no file yet: nothing due, nothing wrong
assert do("list my timers") == "You have no timers."
assert do("remind me to cook in 20 minutes") == "I'll remind you to cook in 20 minutes."
assert do("set a timer for 10 minutes") == "Timer set for 10 minutes."
assert do("ten minute timer for the pasta") == "Timer set for 10 minutes, for the pasta."
assert [r[2:] for r in j.load_reminders()] == [("timer", ""), ("timer", "the pasta"), ("reminder", "to cook")]
assert do("what reminders do I have").startswith("You have 1 reminder: to cook at ")
assert do("list my timers").startswith("You have 2 timers: ") and "for the pasta" in do("list my timers")
assert do("cancel the pasta timer").startswith("Cancelled: ") and len(j.load_reminders()) == 2
assert do("cancel the cooking reminder").startswith("Cancelled: to cook at ")
assert do("cancel the cooking reminder").startswith("I don't see a reminder like that. You have: ")   # the timer left
assert do("cancel all timers").startswith("Cancelled: ") and j.load_reminders() == []
j.listen, j.transcribe = lambda: "audio", lambda a: "Twenty minutes."       # no time said: he asks once and listens
assert do("remind me to stretch") == "I'll remind you to stretch in 20 minutes." and asked[-1] == "When?"
j.listen = lambda: None
assert do("set a timer") == "I didn't catch the time." and asked[-1] == "How long?"
assert do("set a timer for 2 seconds") == do("remind me to rest in 200 hours") == "I can set that from 5 seconds to 7 days ahead."
j.save_reminders([(time.time() + 900 + i, time.time(), "timer", "") for i in range(20)])
assert do("set a timer for 10 minutes") == "You already have 20 pending. Cancel one first."
assert j.due_reminders(time.time()) is False and j.due_reminders(time.time() + 901) is True

# a file that cannot be read is an error, not "no reminders": said once, and nothing is written over it
with open(j.REMIND_FILE, "w", encoding="utf-8") as f:
    f.write("not a reminder\n")
n = len(said)
assert do("set a timer for 10 minutes") == "I can't read the reminders file, so I left it alone."
assert j.due_reminders(time.time()) is False and j.due_reminders(time.time()) is False
assert len(said) == n + 1 and said[-1][1] is False, said[n:]
with open(j.REMIND_FILE, encoding="utf-8") as f:
    assert f.read() == "not a reminder\n"

# the alarm: ding and line until a stop word, a click or the last round; always ends idle with the turn lock free
real_ding = j.ding
j.ding, j.synth_audio = lambda: ("ding", 1), lambda text: (text, 1)


def ring(heard, mute=False, late=1):
    """One reminder that is due and a timer that is not, then the alarm: (dings played, what is left in the file)."""
    now, back = time.time(), iter(heard)
    j.save_reminders([(now - late, now - 1200 - late, "reminder", "to cook"), (now + 900, now, "timer", "")])
    played.clear(), convo.clear(), states.clear()
    j.muted, j.listen, j.transcribe = lambda: mute, lambda: "audio", lambda a: next(back, "")
    assert within(5, j.alarm) is None
    assert states[-1] == idle and not j.busy.locked() and time.time() - j.turn_id[0] < 5   # the idle timer was reset
    return played.count("ding"), [r[2] for r in j.load_reminders()]


assert ring(["", "Stop."]) == (2, ["timer"]) and convo == [("J", "Time to cook."), ("J", "(stopped)")]
assert played == ["ding", "Time to cook.", "ding", "Time to cook."]
for word in ("shush", "Shut up!", "Shutup.", "okay, thanks", "don't stop believing"):
    assert ring([word])[0] == 1, word
assert ring(["what's for dinner"] * 20) == (j.RINGS, ["timer"]) and ("J", "(stopped)") not in convo   # nobody stopped it
assert ring([], mute=True) == (0, ["timer"]) and played == [] and {"pop": "open"} in states       # muted: shown, not rung
assert convo == [("J", "Time to cook.")]
j.hud_tier = lambda: 3                                            # STEALTH is silent too
assert ring([]) == (0, ["timer"]) and {"pop": "open"} in states
j.hud_tier = lambda: 0
assert ring([], late=600)[0] == j.RINGS and convo[0][1].startswith("Missed reminder from ") and convo[0][1].endswith(": time to cook.")
j.play_samples = lambda a, rate, *_: (played.append(a), j.cancel.set())           # a click while it rings
assert ring([]) == (1, ["timer"]) and played == ["ding"] and convo[-1] == ("J", "(stopped)")
j.play_samples = lambda a, rate, *_: played.append(a)
j.synth_audio = _no_voice                                         # it breaks mid-way: one problem line, still idle
assert ring([]) == (0, ["timer"]) and said[-1] == ("A reminder could not ring", True) and convo == [("J", "Time to cook.")]
j.synth_audio = lambda text: (text, 1)
with j.busy:                                                      # a turn is running: the alarm waits for it
    waiting = threading.Thread(target=j.alarm, daemon=True)
    j.save_reminders([(time.time() - 1, time.time() - 9, "timer", "")])
    played.clear()
    waiting.start()
    waiting.join(0.3)
    assert waiting.is_alive() and played == []
waiting.join(5)
assert played.count("ding") == j.RINGS and j.load_reminders() == [] and not j.busy.locked()

# whole turns: a timer is set from speech, and a confirmation is still heard through the same second listen
j.setting = lambda name, default="": "0" if name == "JarvisFollowUp" else default     # one turn each: no follow-up
turns = iter(["Set a timer for 10 minutes.", "Lock my computer.", "Yes."])
j.muted, j.listen, j.transcribe = lambda: False, lambda: "audio", lambda a: next(turns)
real_run_action = j.run_action
j.run_action = lambda action, target, pending=None: acted.append(action) or True
j.turn(0)
assert asked[-1] == "Timer set for 10 minutes." and states[-1] == idle and not j.busy.locked()
j.turn(0)
assert acted == ["lock"] and asked[-1] == "Done." and states[-1] == idle and not j.busy.locked()
# 8a: past the direct window the hologram goes to STANDBY (idle) and returns to listening if speech starts there
import numpy as _np
import importlib.util as _ilu
_spec = _ilu.spec_from_file_location("jarvislib.mic_fresh", os.path.join(os.path.dirname(os.path.abspath(__file__)), "jarvislib", "mic.py"))
_mic = _ilu.module_from_spec(_spec)                           # a fresh copy: the tests above replaced _listen in the real one
_spec.loader.exec_module(_mic)
class _Strm:
    def __init__(self, loud_at): self.n, self.loud_at = 0, loud_at
    def __enter__(self): return self
    def __exit__(self, *a): return False
    def close(self): pass
    def read(self, block):
        self.n += 1
        return _np.full((block, 1), 0.5 if self.n >= self.loud_at else 0.0, dtype=_np.float32), False
class _Sd:
    def __init__(self, loud_at): self.loud_at = loud_at
    def InputStream(self, **k): return _Strm(self.loud_at)
_seen, _real_S, _real_sd = [], _mic.S, sys.modules.get("sounddevice")
class _FakeS:
    def set(self, **k):
        if "state" in k: _seen.append(k["state"])
_mic.S = _FakeS()
for _loud, _want in ((10 ** 6, ["idle"]), (20, ["idle", "listening"])):   # nobody speaks / speaks in the dim part
    del _seen[:]
    sys.modules["sounddevice"] = _Sd(_loud)
    _mic._listen(0.9, 0.3)                                    # 30 blocks of 30 ms; dim from 0.3 s
    assert _seen == _want, (_loud, _seen)
_mic.S = _real_S
if _real_sd is None: del sys.modules["sounddevice"]
else: sys.modules["sounddevice"] = _real_sd
assert j.ask_text("ASK 1 what time\nis it  now\n") == "what time is it now" and j.ask_text("ASK 1\n") == ""
assert len(j.ask_text("ASK 1 " + "x" * 600)) == 500 and j.ask_text("ASK 1 ") == ""
# 8d: typed text takes the same turn with no microphone; a confirmation it needs is never taken from the microphone
def _no_mic(*a, **k): raise AssertionError("typed turn used the microphone")
keep_listen, keep_transcribe, j.listen, j.transcribe = j.listen, j.transcribe, _no_mic, _no_mic
n_acted = len(acted)
j.turn(0, typed="Set a timer for 5 minutes.")
assert asked[-1] == "Timer set for 5 minutes." and states[-1] == idle and not j.busy.locked() and not j.typed_turn[0] is False
j.turn(0, typed="Lock my computer.")
assert len(acted) == n_acted and not j.busy.locked()          # asked, never confirmed by voice, so nothing ran
j.listen, j.transcribe = keep_listen, keep_transcribe
try:                                                              # the ding itself, where numpy is installed
    import numpy
    tone, rate = real_ding()
    assert rate == 24000 and tone.dtype == numpy.float32 and 0.2 < abs(tone).max() <= 0.4 and len(tone) == 21600
except ImportError:
    pass

# ---- snooze: heard in the same gap as "stop" and checked first; one minute unless a length is said
assert j.snooze_for("Snooze.") == j.snooze_for("okay, later") == j.snooze_for("Not now!") == j.SNOOZE == 300
assert j.snooze_for("snooze 5 minutes") == 300 and j.snooze_for("Ten more minutes.") == 600
assert j.snooze_for("snooze for half an hour") == 1800
assert j.snooze_for("snooze 5 hours") == 0 and j.snooze_for("snooze 10 seconds") == 0     # out of range: keeps ringing
assert j.snooze_for("again in ten") == j.snooze_for("snooze for 10") == 600 and j.snooze_for("5 minutes more") == 300   # P0-07
assert j.snooze_for("snooze for 30") == 1800 and j.snooze_for("again in 90 seconds") == 90 and j.snooze_for("snooze for 0") == 0
assert j.snooze_for("stop") is None and j.snooze_for("") is None and j.snooze_for("no more") is None
t0 = time.time()
assert ring(["Snooze."]) == (1, ["reminder", "timer"]) and asked[-1] == "Snoozed for 5 minutes."
assert 295 < j.load_reminders()[0][0] - t0 < 310 and j.load_reminders()[0][3] == "to cook"
assert ring(["", "okay, snooze 10 minutes"]) == (2, ["reminder", "timer"]) and asked[-1] == "Snoozed for 10 minutes."
assert ring(["okay"]) == (1, ["timer"])
assert ring(["snooze 5 hours", "stop"]) == (2, ["timer"])
assert ring(["hey jarvis"] * 20)[0] == j.RINGS                    # a reminder keeps the RINGS loop: the name alone is no stop


# ---- 5a: an alarm rings until it is answered (5-minute cap); the label every 30 s; a fake clock moves 2 s per gap
class _Clock:
    def __init__(self):
        self.t = time.time()

    def time(self):
        return self.t

    def __getattr__(self, name):
        return getattr(time, name)


def ring_alarm(heard, timer_due=False):
    """An alarm that is due (and a timer, due or not): (dings, labels said, gaps listened, kinds left in the file)."""
    clk, back, gaps = _Clock(), iter(heard), []
    now = clk.t
    j.save_reminders(sorted([(now - 1, now - 600, "reminder", "alarm"), (now - 1 if timer_due else now + 900, now - 600, "timer", "")]))
    played.clear(), convo.clear(), states.clear()

    def gap(**k):
        gaps.append(k.get("patience"))
        clk.t += 2
        return "audio" if next(back, "") else None

    words = iter(w for w in heard if w)
    j.time, j.muted, j.listen, j.transcribe = clk, lambda: False, gap, lambda a: next(words)
    try:
        assert within(5, j.alarm) is None
    finally:
        j.time = time
    assert states[-1] == idle and not j.busy.locked()
    return played.count("ding"), sum(1 for p in played if p != "ding"), gaps, [r[2] for r in j.load_reminders()]


j.rang.clear()
dings, labels, gaps, left = ring_alarm([])                        # nobody answers: 5 minutes, then a missed line
assert (dings, labels, left) == (150, 10, ["timer"]) and set(gaps) == {1.5}
assert convo[-1][1].startswith("Missed alarm from ") and {"pop": "open"} in states and j.rang
assert ring_alarm(["", "", "stop"])[:2] == (3, 1) and convo[-1] == ("J", "(stopped)")
assert ring_alarm(["", "Hey Jarvis."])[0] == 2 and convo[-1] == ("J", "(stopped)")      # the name alone stops an alarm
assert ring_alarm(["Jarvis"])[0] == 1
assert ring_alarm(["what time is it"] + [""] * 20)[0] == 150      # other words: it keeps ringing
assert ring_alarm(["", "", "snooze"])[3] == ["reminder", "timer"] and asked[-1].startswith("Snoozed until ")
assert asked[-1].endswith(("AM.", "PM.")) and not j.rang
assert ring_alarm([], timer_due=True)[0] == 150                   # a timer due with an alarm: the batch rings long
j.play_samples = lambda a, rate, *_: (played.append(a), j.cancel.set())           # a click in the first ding
assert ring_alarm([])[:2] == (1, 0) and convo[-1] == ("J", "(stopped)")
j.play_samples = lambda a, rate, *_: played.append(a)
j.save_reminders([])
# 5c: asking about alarms and timers is answered by code
assert cmd("when is my next alarm") == ("list", "alarm") and cmd("what timers are running") == ("list", "timer")

# ---- repeating reminders: the rule lives in the kind field, and the next time is saved before it rings
mon9 = datetime(2026, 10, 12, 9, 0).timestamp()                   # a Monday
day = lambda ts: datetime.fromtimestamp(ts).strftime("%a %d %H:%M")
assert day(j.next_due(mon9, "daily", mon9)) == "Tue 13 09:00"
assert day(j.next_due(mon9 + 4 * 86400, "weekdays", mon9 + 4 * 86400)) == "Mon 19 09:00"      # Friday -> Monday
assert day(j.next_due(mon9, "mon", mon9)) == "Mon 19 09:00"
assert day(j.next_due(mon9, "daily", mon9 + 3 * 86400 + 60)) == "Fri 16 09:00"               # three missed days: one next time
op, kind, due, label, said_time = cmd("remind me every day at 9 to take vitamins")
assert (op, kind, label) == ("set", "daily", "to take vitamins") and due > time.time()
op, kind, due, label, _ = cmd("Remind me every weekday at 8:30 to check mail.")
assert (kind, label) == ("weekdays", "to check mail") and datetime.fromtimestamp(due).weekday() < 5
op, kind, due, label, _ = cmd("remind me to put the bins out every Monday at 7")
assert (kind, label) == ("mon", "to put the bins out") and datetime.fromtimestamp(due).weekday() == 0
assert ahead("remind me to cook in 20 minutes") == ("reminder", 1200, "to cook")             # a single one is as before
j.save_reminders([])
assert do("remind me every day at 9 am to take vitamins") == "I'll remind you to take vitamins every day at 9:00 AM."
assert do("remind me every day in 20 minutes to stretch") == "A repeating reminder needs a clock time, like every day at 9."
assert do("remind me every day to stretch") == "A repeating reminder needs a clock time, like every day at 9."
assert "to take vitamins, every day at 9:00 AM" in do("what reminders do I have") and do("list my timers") == "You have no timers."
assert do("cancel the vitamins reminder").startswith("Cancelled: ") and j.load_reminders() == []   # the whole series
now = time.time()
j.save_reminders([(now - 1, now - 100, "daily", "to take vitamins")])
back = iter(["stop"])
j.muted, j.listen, j.transcribe = lambda: False, lambda: "audio", lambda a: next(back, "")
convo.clear()
assert within(5, j.alarm) is None and convo[0] == ("J", "Time to take vitamins.")
left = j.load_reminders()
assert len(left) == 1 and left[0][2:] == ("daily", "to take vitamins") and 80000 < left[0][0] - now < 92000
j.save_reminders([(now - 3 * 86400, now - 4 * 86400, "daily", "to take vitamins")])           # the PC was off for three days
back = iter(["snooze"])
convo.clear()
assert within(5, j.alarm) is None and convo[0][1].startswith("Missed reminder from ")
assert sorted(r[2] for r in j.load_reminders()) == ["daily", "reminder"]     # the series goes on; the snooze is a single ring
assert all(r[0] > now for r in j.load_reminders())
j.save_reminders([])

# ---- remembered facts: kept in a file, said back in your own words, forgotten by word; questions never save
j.context = lambda *a: ""
j.MEMORY_FILE = os.path.join(tmp, "memory.txt")


def mem(text):
    kind, op, target, _ = j.route(text)
    assert kind == "memory", text
    return j.memory_reply(op, target)


assert mem("What do you remember?") == "You haven't asked me to remember anything."
assert mem("Remember that my dentist is on Fridays.") == "Noted: my dentist is on Fridays."
assert mem("Jarvis, remember my bike is in the shed") == "Noted: my bike is in the shed."
assert mem("remember my bike is in the shed") == "Noted: my bike is in the shed." and len(j.load_memory()) == 2   # not twice
assert mem("what have I told you to remember") == "I remember 2 things: my dentist is on Fridays; my bike is in the shed."
for text in ("Do you remember that film?", "do you remember that film", "remember to buy milk", "forget it", "Remember that film?"):
    assert j.route(text)[0] == "chat", text
assert j.route("forget the cooking reminder")[0] == "remind"
assert "FACTS THE USER TOLD YOU (use them exactly):\n- my dentist is on Fridays\n- my bike is in the shed" in j.system_prompt()
assert "TOLD YOU" not in j.system_prompt("Tell me a joke.")                  # M4a: only the facts the question is about
p = j.system_prompt("When is my dentist?")
assert "- my dentist is on Fridays\n" in p and "bike" not in p
assert "my bike is in the shed" in j.system_prompt("Good morning.", "brief")   # a briefing still gets them all
j.save_memory([f"car fact {i}" for i in range(6)] + ["my car is blue"])
p = j.system_prompt("Is my car still blue?").split("(use them exactly):\n")[1].split("\n\n")[0].splitlines()
assert len(p) == 5 and p[0] == "- my car is blue"                             # 5 at most, most shared words first
j.save_memory(["my dentist is on Fridays", "my bike is in the shed"])
assert j.route("forget everything") == ("act", "forget_all", None, "Forget all 2 things I remember? Confirm with yes.")
assert mem("forget that my dentist is on Fridays") == "Forgotten: my dentist is on Fridays."
assert mem("forget the dentist") == "I don't have that." and j.load_memory() == ["my bike is in the shed"]
j.ACTIONS["forget_all"](None)
assert j.load_memory() == [] and j.route("forget everything")[:2] == ("say", None)
assert "TOLD YOU" not in j.system_prompt()
j.save_memory([f"fact {i}" for i in range(50)])
assert mem("remember one more thing") == "You've told me 50 things. Forget one first." and len(j.load_memory()) == 50
j.save_memory([])
assert mem("remember " + "x" * 300) == "Noted: " + "x" * 200 + "."
with open(j.MEMORY_FILE, "wb") as f:                              # unreadable: said, left alone, and the prompt still works
    f.write(b"\xff\xfe\xff")
assert mem("remember the milk is off") == mem("what do you remember") == "I can't read my memory file, so I left it alone."
assert j.route("forget everything")[:2] == ("say", None) and "You are JARVIS" in j.system_prompt()
with open(j.MEMORY_FILE, "rb") as f:
    assert f.read() == b"\xff\xfe\xff"
assert j.route("what do you know about my dentist")[3] == j.MEMORY_BAD
os.remove(j.MEMORY_FILE)

# ---- M4a-2: more save phrases, "Replace?", forget reads back, "what do you know about X" by code
assert mem("Note that my locker code is in my phone.") == "Noted: my locker code is in my phone."
assert mem("Don't forget that the boiler is serviced in May.") == "Noted: the boiler is serviced in May."
assert mem("keep in mind that I'm vegetarian") == "Noted: I'm vegetarian."
for text, fact in (("Hey Jarvis, remember my sister's name is Ana.", "my sister's name is Ana"),   # clear: saved at once
                   ("Oh and remember my sister is Ana.", "my sister is Ana"), ("Remember, the gym shuts at nine.", "the gym shuts at nine"),
                   ("I want you to remember that my sister is Ana", "my sister is Ana"),
                   ("Hey Jarvis, my sister's name is Ana, remember that.", "my sister's name is Ana"),
                   ("My sister's name is Ana. Remember that.", "My sister's name is Ana"),
                   ("the bins go out on Tuesday, don't forget that", "the bins go out on Tuesday")):
    assert j.route(text)[:3] == ("memory", "save", fact), text
for text in ("Jarvis, remember that.", "remember it", "Did you see the film? Remember that.", "I can't remember that",
             "do you remember that film", "I want you to remember to call mum"):
    assert j.route(text)[0] != "memory", text
for text in ("note to self buy eggs", "don't forget to call mum", "keep in mind I'm tired", "note that down"):
    assert j.route(text)[0] != "memory", text
j.save_memory(["my dentist is on Fridays", "my bike is in the shed"])
r = j.route("remember my dentist is on Mondays")
assert r == ("act", "replace_fact", ("my dentist is on Fridays", "my dentist is on Mondays"),
             "You told me 'my dentist is on Fridays'. Replace it with this? Confirm with yes.")
j.ACTIONS["replace_fact"](r[2])
assert j.load_memory() == ["my dentist is on Mondays", "my bike is in the shed"]
assert j.route("remember my dentist is on Mondays")[0] == "memory"          # already saved: no question
assert j.route("remember the wifi box is upstairs")[0] == "memory"          # nothing in common: saved straight away
assert j.route("what do you know about my dentist") == ("say", None, None, "You told me: my dentist is on Mondays.")
assert j.route("What do you know about me?")[3] == "You told me: my dentist is on Mondays; my bike is in the shed."
assert j.route("what do you know about black holes")[0] == "chat"         # nothing saved about it: the model answers
j.save_memory(["my bike is in the shed", "my bike is blue"])
r = j.route("forget my bike")
assert r == ("act", "forget_facts", ["my bike is in the shed", "my bike is blue"],
             "Forget 2 things: my bike is in the shed; my bike is blue? Confirm with yes.")
j.ACTIONS["forget_facts"](r[2])
assert j.load_memory() == []
j.save_memory(["my friend Oscar is tall", "my car is red"])                # whole words only: "car" is not in "Oscar"
assert mem("forget car") == "Forgotten: my car is red." and j.load_memory() == ["my friend Oscar is tall"]
assert j.undo_last() == "Put back: my car is red." and j.load_memory() == ["my friend Oscar is tall", "my car is red"]
assert mem("forget the") == "I don't have that." and len(j.load_memory()) == 2
j.save_memory(["my dentist is on Fridays", "my bike is in the shed"])      # P0-03: a confirmed replace / forget can be undone
assert real_run_action("replace_fact", ("my dentist is on Fridays", "my dentist is on Mondays"), ("replace_fact", ("my dentist is on Fridays", "my dentist is on Mondays"))) and j.load_memory()[0] == "my dentist is on Mondays"
assert j.undo_last() == "Put back: my dentist is on Fridays." and j.load_memory() == ["my dentist is on Fridays", "my bike is in the shed"]
assert real_run_action("forget_facts", ["my bike is in the shed"], ("forget_facts", ["my bike is in the shed"])) and j.undo_last() == "Put back: my bike is in the shed."
assert real_run_action("forget_all", None, ("forget_all", None)) and j.load_memory() == [] and j.undo_last().startswith("Put back: ") and len(j.load_memory()) == 2
j.save_memory(["my dentist is on Fridays"])

# ---- to-do by voice: asked first, appended to the note (never rewritten, never created), the text kept out of the log
note = os.path.join(tmp, "todo.md")
j.todo_note = lambda: note if os.path.exists(note) else ""
assert j.route("add buy milk to my to-do list")[0] == "say"       # no note set: said, nothing staged
with open(note, "wb") as f:
    f.write(b"- [ ] old")                                         # no line break at the end
assert j.route("Add buy milk to my to-do list.") == ("act", "todo", "buy milk", "Add 'buy milk' to your to-do list? Confirm with yes.")
for text, item in (("put call the bank on my todo list", "call the bank"), ("Add a task: renew passport.", "renew passport"),
                   ("new to-do buy milk", "buy milk"), ("Jarvis, add feed the cat to my tasks", "feed the cat"),
                   ("could you add water the plants to the to do list", "water the plants"),
                   ("Add call Dr Smith to my to-do list", "call Dr Smith")):
    assert j.route(text)[1:3] == ("todo", item), text
for text in ("How do I add a task in Jira?", "what's on my to-do list", "add 2 and 3", "put the kettle on"):
    assert j.route(text)[0] == "chat", text
turns = iter(["Add buy milk to my to-do list.", "No, wait.", "Add buy milk to my to-do list.", "Yes."])
j.listen, j.transcribe = lambda: "audio", lambda a: next(turns)
acted.clear()
j.turn(0)
assert acted == [] and asked[-1] == "Cancelled." and not j.busy.locked()
j.turn(0)
assert acted == ["todo"] and asked[-1] == "Added." and not j.busy.locked()
with open(note, "rb") as f:
    assert f.read() == b"- [ ] old"                               # run_action is a fake here: the note is untouched
turns = iter(["Remember my dentist is on Mondays.", "No."])          # M4a-2: no yes keeps the old fact AND saves the new one
j.transcribe = lambda a: next(turns)
j.turn(0)
assert asked[-1] == "Noted: my dentist is on Mondays. I kept the old one too." and acted == ["todo"]
assert j.load_memory() == ["my dentist is on Fridays", "my dentist is on Mondays"]
os.remove(j.MEMORY_FILE)
j.setting = lambda name, default="": default
j.ACTIONS["todo"]("buy milk")
j.ACTIONS["todo"]("call\nthe   bank")
with open(note, "rb") as f:
    assert f.read() == b"- [ ] old\n- [ ] buy milk\n- [ ] call the bank\n"
logged, keep = [], j.log
j.log = logged.append
assert real_run_action("todo", "secret item", ("todo", "secret item")) is True and "secret" not in "".join(logged)
os.remove(note)
n = len(said)
assert real_run_action("todo", "secret item", ("todo", "secret item")) is False and not os.path.exists(note)     # a missing note is not created
assert "secret" not in "".join(logged) + said[-1][0] and tmp not in "".join(logged) + said[-1][0] and len(said) == n + 1
j.log = keep

# personality: one sentence of the prompt follows JarvisPersonality; an unknown or unset value is the playful one
j.context = lambda *a: ""
for mood, sentence in (("proper", "a little dry"), ("playful", "same spirit"), ("brief", "one short sentence"), ("nonsense", "same spirit")):
    j.setting = lambda name, default="", mood=mood: mood if name == "JarvisPersonality" else default
    assert sentence in j.system_prompt() and j.system_prompt().count("You are JARVIS") == 1, mood
j.setting = lambda name, default="": default
assert "same spirit" in j.system_prompt() and "a little dry" not in j.system_prompt()

# ---- briefing and follow-up, as whole turns with a fake model
for text in ("Good morning.", "good evening jarvis", "Brief me", "Hey Jarvis, daily briefing.", "What's my day look like?"):
    assert j.route(text)[0] == "brief", text
for text in ("Good morning, can you open Chrome?", "brief me on quantum physics", "is it a good morning?"):
    assert j.route(text)[0] == "chat", text
prompts, heard, speaks, temps = [], [0], [0], []
j.chat_stream = lambda model, messages, temperature=0.5: temps.append(temperature) or prompts.append(messages[0]["content"])
j.sentences_from = lambda stream, collected: collected.append("Ha.") or iter(["Ha."])
j.speak_all = j.say_text_only = lambda sentences, *a: list(sentences)
j.ollama_on_cpu = lambda model: None


def _listen(**k):
    heard[0] += 1
    return "audio" if heard[0] <= speaks[0] else None


def talk(times, mute=False, follow="1", words="Tell me a joke."):
    """One turn in which you speak up to `times` times in a row: how often the microphone was opened."""
    heard[0], speaks[0] = 0, times
    j.muted, j.listen, j.transcribe = lambda: mute, _listen, lambda a: words
    j.setting = lambda name, default="": follow if name == "JarvisFollowUp" else default
    j.turn(0)
    assert states[-1] == idle and not j.busy.locked()
    return heard[0]


assert talk(1) == 2                                               # he answers, then listens once more and hears nothing
assert talk(30) == 31                                             # D2: no cap, he listens until you stop answering
assert talk(99, mute=True) == 1 and talk(99, follow="0") == 1     # shown instead of spoken, or switched off: none
n = len(prompts)
assert talk(1, words="Set a timer for 10 minutes.") == 2 and len(prompts) == n   # S2-10: a command opens the ear too
j.save_reminders([])


def ear(lines):
    """A turn of several lines in a row: (how often the mic opened, the model calls made)."""
    seq, n = iter(lines), len(prompts)
    heard[0], speaks[0] = 0, len(lines)
    j.muted, j.listen, j.transcribe = (lambda: False), _listen, (lambda a: next(seq, ""))
    j.setting = lambda name, default="": default
    j.offer.clear()
    j.turn(0)
    assert states[-1] == idle and not j.busy.locked()
    return heard[0], len(prompts) - n


# "undo" in the window: done at once, no extra yes ("Never mind Jarvis, undo" left the alarm before)
for undo_line in ("Undo that.", "Never mind Jarvis, undo."):
    assert ear(["Set a timer for 10 minutes.", undo_line]) == (3, 0) and j.load_reminders() == [], undo_line
    assert asked[-1] == "Removed that timer.", asked[-2:]
# room talk in the window: a fragment is ignored, 3+ words with no cue are asked about, a question is answered
assert ear(["Set a timer for 10 minutes.", "Uh huh."]) == (2, 0) and asked[-1] != "Uh huh."
assert ear(["Set a timer for 10 minutes.", "Mom the pasta is boiling over."])[1] == 0 and asked[-1] in j.ROOM_ASKS
assert ear(["Set a timer for 10 minutes.", "Mom the pasta is boiling over.", "Yes."]) == (4, 1)   # yes: answered
assert ear(["Set a timer for 10 minutes.", "Mom the pasta is boiling over.", "No."]) == (3, 0)    # no: ended
assert ear(["Set a timer for 10 minutes.", "What is the capital of France?"]) == (3, 1)
j.save_reminders([])
for text, want in (("Uh huh.", "no"), ("okay", "no"), ("Mom the pasta is boiling over.", "ask"), ("What's the time?", "yes"),
                   ("Thank you.", "yes"), ("No.", "yes"), ("Jarvis, the pasta.", "yes"), ("set a timer for 2 minutes", "yes"),
                   ("Tell me a joke", "yes"), ("I think you are right", "yes"), ("the pasta is boiling", "ask")):
    assert j.directed(text, False) == want, (text, j.directed(text, False))
assert j.directed("the pasta is boiling", True) == "yes"           # he had just asked something: it is the answer
assert "BRIEFING:" not in prompts[-1]
talk(1, words="Good morning.")
assert "BRIEFING:" in prompts[-1] and "at most three" in prompts[-1]
assert "Fan 1: 900 RPM" in prompts[-1]                            # a briefing has the readings
j.history.clear()

# ---- slice C, L10: an info question about empty data gets a fixed reply, never the model
real_close, real_kv = j.closeness, j.read_kv
j.closeness = lambda text, others: 0.52 if others is j.BLOCK_EXAMPLES["calendar"] else 0.1
assert j.info_blocks("What do I have today?") == {"calendar"}
assert "calendar" in j.wants("What do I have today?")                  # its data goes in too (0.6 alone would miss)
assert j.info_blocks("What's on today?") == set()                       # not about you: needs 0.55
for talk_line in ("Tell me about your weekend.", "Is it a busy week for you?", "Today was long."):
    assert j.info_blocks(talk_line) == set(), talk_line                 # about him, or not a question: chat
assert j.lane_of("chat", {"calendar"}) == "info" and j.lane_of("chat", set()) == "chat"
assert j.lane_of("notes", set()) == "info" and j.lane_of("remind", set()) == "command"
for cal, want in (("", "I can't see a calendar"), ("T 1" + chr(10) + "C 1 0", "Nothing is coming up")):
    j.read_kv = lambda name, cal=cal: cal if name == "calendar.txt" else ""
    n = len(prompts)
    talk(1, words="What do I have today?")
    assert len(prompts) == n and j.history[-1]["content"].startswith(want), (cal, j.history[-1:])   # no model call
real_context, j.context = j.context, lambda *a: "Upcoming calendar events: Thu 15 Oct 09:00 - Dentist"   # faked "" above
n = len(prompts)
talk(1, words="What do I have today?")
assert len(prompts) == n + 1 and "Dentist" in prompts[-1] and "INFO QUESTION" in prompts[-1] and temps[-1] == 0   # data: the model, strict
j.closeness, j.read_kv, j.context = real_close, real_kv, real_context
talk(1, words="Tell me a joke.")
assert "INFO QUESTION" not in prompts[-1] and temps[-1] == 0.5
j.history.clear()
real_sensors, j.sensors = j.sensors, lambda: "Fan 1: 900 RPM\nPending: alarm at 7:00 AM"
talk(1, words="Tell me a joke.")
assert "Fan 1: 900 RPM" not in prompts[-1]                        # 6a: readings only when asked about the PC
assert "alarm at 7:00 AM" not in prompts[-1]                      # unrelated chat: no schedule either
j.history.clear()
talk(1, words="Did you do what I asked?")
assert "Pending (don't bring it up unless asked" in prompts[-1] and "alarm at 7:00 AM" in prompts[-1]   # checkable
assert "Fan 1: 900 RPM" not in prompts[-1]
j.history.clear()
talk(1, words="How hot is the GPU?")
assert "Fan 1: 900 RPM" in prompts[-1] and "\nPending: alarm at 7:00 AM" in prompts[-1]
j.sensors = real_sensors
j.setting = lambda name, default="": default

# ---- FR5 N3: long room talk -> "Were you talking to me?"; "yes" answers what was said, "no" ends it
ROOM = ("So I'm going to go ahead and get started on the essay now and then we will see how it goes after lunch "
        "with the others, okay okay okay.")
assert j.room_talk(ROOM) and not j.room_talk(ROOM[:-1] + "?") and not j.room_talk("Jarvis, " + ROOM)
assert not j.room_talk("I think you should go ahead " + ROOM) and not j.room_talk("Tell me a joke.")
for answer, answered in (("Yes.", True), ("No.", False)):
    j.offer.clear(), j.history.clear()
    seq, n = iter([ROOM, answer]), len(prompts)
    heard[0], speaks[0] = 0, 2
    j.muted, j.listen, j.transcribe = (lambda: False), _listen, (lambda a: next(seq, ""))
    j.turn(0)
    assert not j.busy.locked() and heard[0] == (3 if answered else 2), (answer, heard[0])
    assert (len(prompts) == n + 1) is answered, answer                 # the model ran only after "yes"
    assert (j.history[:1] == [{"role": "user", "content": ROOM}]) is answered, j.history
    assert asked[-1] in j.ROOM_ASKS                 # asked once (reply_line is faked above)
assert j.route("I'm still in four loop, so what's the name for it?")[0] == "chat" and not j.room_talk(
    "I'm still in four loop, so what's the name for it?")                         # a question is answered as before
j.offer.clear(), j.history.clear()

# ---- slice B, L2: a lone level is a half-heard volume command
j.did.clear(), j.heard_score.__setitem__(0, 0.0)
assert j.understand("About 20%.", "m", True, "") == ("act", "volume", ("set", 20), "Did you mean the volume at 20 percent?", "context")
assert j.understand("Twenty percent", "m", True, "")[1:4] == ("volume", ("set", 20), "Did you mean the volume at 20 percent?")
for no in ("20.", "Seven", "About 200%.", "About the weather.", "Tell me a joke."):
    assert j.understand(no, "m", True, "")[0] != "act", no                 # no volume talk, no "percent": as before
j.did_add("volume", ("set", 50))
assert j.understand("about 20", "m", True, "") == ("act", "volume", ("set", 20), None, "context")   # right after: set
j.heard_score[0] = -2.0
assert j.understand("About 20%.", "m", True, "")[3].startswith("Did you say")       # Whisper unsure: asked
j.did.clear(), j.heard_score.__setitem__(0, 0.0)
assert j.understand("set the volume to 30", "m", True, "") == ("act", "volume", ("set", 30), None, "rule")

# ---- the name as Whisper writes it: removed only as the first words, so every command works after it
real_time = j.time.time
j.time.time = lambda: 2e9                                         # reminder times compare exactly
clean = ("set the volume to 30", "open chrome", "lock my computer", "remind me to cook in 20 minutes", "mute",
         "set a timer for 10 minutes", "what reminders do I have", "turn it up", "next track", "close chrome")
names = ("Travis, ", "Jervis, ", "Javis, ", "Jarvus, ", "Service, ", "Droves, ", "Drovis, ", "Hey Travis, ", "Hi Jervis ",
         "Okay Travis, ", "OK, Javis. ", "Travis. ", "hey service ", "Jarvis, ", "Hey Droves, ", "Jarvus! ", "Hi, Drovis, ",
         "ok drovis ", "Travis ,", "Okay Jarvus ")
for i, name in enumerate(names):
    text = clean[i % len(clean)]
    assert j.route(name + text) == j.route(text), name + text
j.time.time = real_time
for text in ("play Travis Scott", "Travis Scott is playing", "Service the car", "Travis.", "service"):
    assert j.strip_name(text) == text, text
assert j.route("play Travis Scott")[0] == "chat"
j.setting = lambda name, default="": "Jarbis, Garvis" if name == "JarvisNameAliases" else default
assert j.strip_name("Jarbis, mute") == "mute" and j.strip_name("hey garvis open chrome") == "open chrome"
j.setting = lambda name, default="": default

# ---- alarms: a reminder labelled "alarm" (older code reads it as a plain reminder), set by length or clock time
assert ahead("set an alarm for in one minute") == ahead("Set an alarm for one minute.") == ("alarm", 60, "alarm")
assert ahead("wake me up in 10 minutes") == ("alarm", 600, "alarm") and ahead("set an alarm") == ("alarm", None, "alarm")
assert datetime.fromtimestamp(cmd("alarm at 7 am")[2]).strftime("%H:%M") == "07:00"
assert datetime.fromtimestamp(cmd("Wake me up at 6:30.")[2]).minute == 30
assert cmd("do I have an alarm set") == cmd("Do I have any alarms?") == cmd("what alarms do I have") == ("list", "alarm")
assert cmd("cancel my alarm") == cmd("turn off the alarm") == ("cancel", "alarm", "")
for text in ("wake me up when september ends", "alarm clocks are loud", "what is an alarm", "I set an alarm yesterday"):
    assert cmd(text) is None, text
j.save_reminders([])
assert do("set an alarm for one minute").startswith("Alarm set for ") and do("Wake me up in 10 minutes.").startswith("Alarm set")
assert [r[2:] for r in j.load_reminders()] == [("reminder", "alarm")] * 2
assert do("do I have an alarm set").startswith("You have 2 alarms: ") and do("what reminders do I have") == do("do I have an alarm set")
first = j.load_reminders()[0]
assert j.ring_line(first, first[0]) == "This is your alarm." and j.ring_line(first, first[0] + 600).startswith("Missed alarm from ")
j.listen, j.transcribe = lambda: "audio", lambda a: "Both."         # two alarms: he asks which (Round 4)
assert do("cancel my alarm").startswith("Cancelled: ") and j.load_reminders() == [] and asked[-1].endswith("Which one?")
assert do("cancel my alarm") == "I don't see an alarm like that."

# ---- more ways to say the volume; the reply is still what Windows reports
for phrase, want in (("set the volume to thirty", ("set", 30)), ("volume 30", ("set", 30)), ("set it to 30", ("set", 30)),
                    ("Travis, set the volume to thirty.", ("set", 30)), ("turn it down a bit", ("step", -10)),
                    ("a little louder", ("step", 10)), ("turn the volume up a little", ("step", 10)),
                    ("slightly quieter", ("step", -10)), ("make it a bit louder", ("step", 10)), ("max volume", ("set", 100)),
                    ("set the volume to max", ("set", 100)), ("half volume", ("set", 50)), ("volume to half", ("set", 50)),
                    ("set the volume to twenty five percent", ("set", 25)), ("turn it all the way up", ("set", 100)),
                    ("set volume to eighty", ("set", 80)), ("set the volume to a hundred", ("set", 100))):
    assert j.route(phrase)[:3] == ("act", "volume", want), (phrase, j.route(phrase))
assert j.route("set the volume to two hundred")[0] != "act" and j.route("set it to five minutes")[0] != "act"

# ---- he never claims an action: a command no parser took gets a fixed line, and the model is not asked
for text in ("Change the screen colour to blue.", "set the volume to 30 decibels", "please open the settings app"):
    assert j.route(text) == ("say", None, None, j.NEAR_MISS), (text, j.route(text))
# S2-8: a request for something not built is said plainly by code, before the model (it said "done" for brightness)
for text in ("unpair my headphones", "turn off wifi", 
             "change my wallpaper", "hibernate", "sign out", "log me off"):
    assert j.route(text) == ("say", None, None, j.CANT), (text, j.route(text))
for text in ("why is my screen dim?", "how do I turn on bluetooth?", "what is screen brightness"):
    assert j.route(text)[0] == "chat", text
# S2-11: the short ways to say sleep / restart / shut down / lock reach the action (with its yes), never the model
for text, act in (("sleep", "sleep"), ("put my pc in sleep mode", "sleep"), ("sleep mode", "sleep"), ("put the laptop on sleep", "sleep"),
                  ("go to sleep", "sleep"), ("restart", "restart"), ("reboot", "restart"), ("reboot the computer", "restart"),
                  ("shut down", "shutdown"), ("shut the computer down", "shutdown"), ("power down the pc", "shutdown"),
                  ("lock", "lock"), ("lock it", "lock"), ("Jarvis, lock the computer.", "lock")):
    r = j.route(text)
    assert r[:2] == ("act", act) and r[3].endswith("Confirm with yes."), (text, r)
for text in ("should I restart my computer?", "restart the song", "I need some sleep"):
    assert j.route(text)[0] != "act", text
# alarm questions go to the list by rule however they are asked (one went to the model and mixed in the calendar)
for text in ("can you tell me if I have any alarms for tomorrow", "Do I have any alarms for tomorrow?",
             "could you check whether I have an alarm set", "are there any alarms tomorrow"):
    assert j.route(text)[:2] == ("remind", "list"), text
assert j.route("I have an alarm at 7 but")[0] == "chat"
for text in ("how do I change the volume on my phone?", "what timer should I buy", "can you explain how to set an alarm",
             "why won't my bluetooth connect", "I set an alarm yesterday", "who can change the brightness", "play Travis Scott"):
    assert j.route(text)[0] == "chat", text
n = len(prompts)
talk(1, words="Change the screen colour to blue.")
assert len(prompts) == n and asked[-1] == j.NEAR_MISS
for s in ("Alarm set for 5 pm.", "I've turned the volume up.", "Volume is now 30 percent.", "I have set a reminder.",
          "Reminder added.", "I’ve opened Chrome.", "Done, I've muted it.", "I've dimmed the screen.", "Brightness is now 40 percent.",
          "Bluetooth is now on.", "I'll turn on the night light.", "I just restarted it.", "Done.", "Your screen is dimmed now.",
          "I've lowered the brightness for you.", "Wi-Fi has been turned off.", "The brightness has been lowered."):
    got = []
    assert list(j.no_claims(iter(["Sure.", s, "More."]), got)) == ["Sure.", j.CLAIM_LINE] and got == [j.CLAIM_LINE], s
for s in ("You can set an alarm on your phone.", "Set a timer for that.", "The volume knob is on the left.",
          "I can't change the brightness yet.", "Brightness is set in Windows settings.", "When you're done, say so.",
          "It is on your calendar for Friday."):
    assert list(j.no_claims(iter([s]), [])) == [s], s
keep_sf, keep_sa, spoken = j.sentences_from, j.speak_all, []
j.sentences_from = lambda stream, collected: collected.append("Alarm set for 5 pm.") or iter(["Alarm set for 5 pm."])
j.speak_all = lambda sentences, *a: spoken.extend(sentences)
convo.clear()
talk(1, words="Wake me at sunrise.")                              # no clock time: not an alarm, so the model answers
assert spoken == [j.CLAIM_LINE] and convo[-1] == ("J", j.CLAIM_LINE)
j.sentences_from, j.speak_all = keep_sf, keep_sa
# 8-A2: talked over mid-reply: the log and the history keep only what he got to say
j.sentences_from = lambda stream, collected: collected.extend(["First part. ", "Second part."]) or iter(["First part.", "Second part."])
j.speak_all = lambda sentences, *a: (j.cancel.set(), "First part.")[1]
convo.clear()
talk(1, words="Tell me a joke.")
assert convo[-1] == ("J", "First part."), convo
assert j.history[-1] == {"role": "assistant", "content": "First part."}, j.history[-1]
j.cancel.clear()
j.sentences_from, j.speak_all = keep_sf, keep_sa
assert "Never say you set or changed something." in j.system_prompt() and "You cannot set alarms" not in j.system_prompt()

# ---- the voice: one failure is retried at once; failing twice uses the Windows voice for 60 s, then tries again
model_file = os.path.join(tmp, "kokoro-v1.0.onnx")
open(model_file, "w").close()
calls, fails = [], [1]


def _kokoro(path, text):
    calls.append(text)
    if fails[0]:
        fails[0] -= 1
        raise RuntimeError("secret detail")
    return ("kokoro", text)


j.synth_audio, j._kokoro, j._windows, j.resolve_voice = real_synth_audio, _kokoro, lambda text: ("windows", text), lambda v: v
j.setting = lambda name, default="": model_file if name == "JarvisVoice" else default
n = len(said)
assert j.synth_audio("hi") == ("kokoro", "hi") and len(calls) == 2 and len(said) == n     # failed once: retried, no problem
assert j.synth_audio("hi") == ("kokoro", "hi") and len(calls) == 3
fails[0] = 2
assert j.synth_audio("hi") == ("windows", "hi") and len(calls) == 5 and len(said) == n + 1 and "secret" not in said[-1][0]
assert j.synth_audio("hi") == ("windows", "hi") and len(calls) == 5                     # not tried again within 60 s
j.time.time = lambda: real_time() + 61
assert j.synth_audio("hi") == ("kokoro", "hi") and len(calls) == 6
j.time.time = real_time
j.synth_audio, j.setting = lambda text: (text, 1), lambda name, default="": default

# ---- answers by code: the clock, dates, sums and conversions never reach the model
j.time.time = lambda: datetime(2026, 10, 14, 15, 5).timestamp()   # a Wednesday afternoon
for text, want in (("What time is it?", "It's 3:05 PM."), ("what's the time", "It's 3:05 PM."),
                   ("Jarvis, can you tell me the time?", "It's 3:05 PM."), ("What's the date?", "It's Wednesday, October 14."),
                   ("what day is it today", "It's Wednesday."), ("what day is the 3rd", "November 3 is a Tuesday."),
                   ("How many days until Friday?", "2 days until Friday, October 16."),
                   ("how many days until December 25th", "72 days until Friday, December 25."),
                   ("what's the date in 2 weeks", "That's Wednesday, October 28."),
                   ("What's 12 times 9?", "108."), ("twelve times nine", "108."), ("What's 15 percent of 240?", "36."),
                   ("what is 15% of 240", "36."), ("240 divided by 7", "About 34.3."), ("square root of 81", "9."),
                   ("what's 2 to the power of 10", "1024."), ("1,000 plus 250", "1250."), ("7 squared", "49."),
                   ("what is 10 minus 12.5", "-2.5."),
                   ("How many km in 26 miles?", "About 41.8 kilometres."),
                   ("how many kilometres is 26 miles", "About 41.8 kilometres."),
                   ("5 feet 10 in centimetres", "177.8 centimetres."),
                   ("100 fahrenheit in celsius", "About 37.8 degrees Celsius."), ("200 grams in ounces", "About 7.05 ounces."),
                   ("2 hours in seconds", "7200 seconds."), ("convert 60 mph to km/h", "About 96.6 kilometres per hour."),
                   ("how many feet in a mile", "5280 feet."), ("1 gigabyte in megabytes", "1000 megabytes.")):
    assert j.route(text) == ("fact", None, None, want), (text, j.route(text))
assert j.route("what's 2 to the power of 9999999")[3] == "That number is too big to say."
assert j.route("what's 5 divided by zero")[3] == "You can't divide by zero."
for text in ("what is the time complexity of quicksort", "what's 2 plus 3 times 4", "what is x times y",
             "how many people live in Paris", "3 km plus 2 miles", "what day is christmas", "26 miles in pounds",
             "what is love", "how many days until my birthday", "what's 12 times the speed of light"):
    assert j.route(text)[0] == "chat", (text, j.route(text))
n = len(prompts)
talk(1, words="What's 12 times 9?")
assert len(prompts) == n and asked[-1] == "108."
j.time.time = real_time

# ---- "undo that": one change, for 2 minutes, put back to what Windows had before
j.run_action, j.speakers, vol[0], ran[:] = real_run_action, _speakers, 45, []
j.undo.clear()                                                     # left by the tests above
assert j.route("undo that") == j.route("Jarvis, undo.") == j.route("put it back") == ("undo", None, None, None)
assert j.undo_last() == "There's nothing to undo."
assert j.run_action("volume", ("set", 30)) and vol == [30]
assert j.undo_last() == "Volume back at 45 percent." and vol == [45]
assert j.undo_last() == "There's nothing to undo." and vol == [45]
assert j.run_action("volume", ("step", 10)) and vol == [55]
j.time.time = lambda: real_time() + 121
assert j.undo_last() == "There's nothing to undo." and vol == [55]
j.time.time = real_time
assert j.run_action("lock", None, ("lock", None)) and j.undo_last() == "I can't undo that."
j.save_reminders([])
do("set a timer for 10 minutes")
assert j.undo_last() == "Removed that timer." and j.load_reminders() == []
j.save_memory([])
j.memory_reply("save", "my bike is blue")
assert j.undo_last() == "Forgotten: my bike is blue." and j.load_memory() == []
n = len(ran)
talk(2, words="shut down the PC")                                  # asked, the answer is not a yes: cancelled
assert asked[-1] == "Cancelled." and len(ran) == n and j.undo_last() == "There's nothing to undo."

# ---- "what did you hear?" and "say that again": memory only
talk(1, words="Tell me a joke.")
talk(1, words="What did you hear?")
assert asked[-1] == "I heard: Tell me a joke."
talk(1, words="Say that again.")
assert asked[-1] == "Ha."

# ---- live test of phase 1: a word before the command, more ways to ask for an alarm, "never mind", the volume read
# from Windows every time it is asked, and a longer wait for a follow-up
for text in ("then change the volume to 30%.", "And set the volume to 30.", "Okay, set the volume to 30", "so, set volume to 30"):
    assert j.route(text) == ("act", "volume", ("set", 30), None), text
for text in ("Set me an alarm for one minute.", "Set up an alarm for one minute", "Create an alarm for 1 minute.",
             "Set an alarm for one minute from now.", "Then set an alarm for one minute.", "Okay, set an alarm for 1 minute"):
    assert ahead(text) == ("alarm", 60, "alarm"), (text, j.route(text))
for text in ("Set a timer for actually don't set a timer.", "Set a timer for... never mind.", "Never mind.",
             "Set an alarm, never mind", "actually, don't set a timer"):
    assert j.route(text) == ("say", None, None, "Okay, never mind."), text
j.save_reminders([])
for answer, op, want in (("Never mind.", "set a timer", "Okay, no timer."), ("No.", "set an alarm", "Okay, no alarm."),
                         ("Cancel that.", "remind me to cook", "Okay, no reminder."), ("forget it", "set a timer", "Okay, no timer.")):
    j.listen, j.transcribe = lambda: "audio", lambda a: answer
    assert do(op) == want and j.load_reminders() == [], (answer, do(op))
j.speakers, vol[0] = _speakers, 45
for text in ("What's the volume?", "what is the volume at", "How loud is it?", "Is it muted?", "what's the volume set to"):
    assert j.route(text) == ("level", None, None, None), text
assert j.route("what volume is 30 decibels")[0] == "chat"
talk(1, words="What's the volume?")
assert asked[-1] == "The volume is at 45 percent."
vol[0] = 70                                                        # changed by hand in Windows: read again, not remembered
talk(1, words="What's the volume?")
assert asked[-1] == "The volume is at 70 percent."
waits = []
real_listen = _listen
_listen = lambda **k: waits.append(k.get("patience")) or real_listen()
talk(1)
assert waits == [None, 10.0], waits                               # the first listen as before; 8a: the open ear lasts 10 s (3 s direct)
j.setting = lambda name, default="": "99" if name == "JarvisFollowUpWait" else default
assert j.follow_wait() == 30.0
assert j.follow_name_wait() == 30.0                               # never shorter than the direct window
j.setting = lambda name, default="": default

# ---- live test 2: more ways to ask for the volume and about an alarm; an alarm is never called a timer
for text, want in (("Can you change the volume to 30 please?", ("set", 30)), ("Change the volume to 30 percent please.", ("set", 30)),
                   ("Turn the volume up to 50.", ("set", 50)), ("Turn the volume down to 20%.", ("set", 20)),
                   ("Raise the volume to 60.", ("set", 60)), ("I want the volume at 40.", ("set", 40)),
                   ("Put the volume on 40.", ("set", 40)), ("Set the volume at 30%, please.", ("set", 30)),
                   ("Lower the volume.", ("step", -10)), ("Increase the volume.", ("step", 10)),
                   ("Could you decrease the sound a bit?", ("step", -10)), ("Volume up.", ("step", 10))):
    assert j.route(text) == ("act", "volume", want, None), (text, j.route(text))
for text in ("When is my alarm?", "How long until my alarm?", "Is my alarm set?"):
    assert cmd(text) == ("list", "alarm"), (text, j.route(text))
j.save_reminders([])
do("set an alarm for 7 am"), do("set an alarm for 8 am"), do("set a timer for 10 minutes")
assert do("cancel the alarm for 7").startswith("Cancelled: alarm at 7:00 AM") and len(j.load_reminders()) == 2
assert do("Remove my 8 am alarm.").startswith("Cancelled: alarm at 8:00 AM") and len(j.load_reminders()) == 1
do("set an alarm for 7 am"), do("set an alarm for 8 am")
j.listen, j.transcribe = lambda: "audio", lambda a: "All of them."  # two alarms: he asks which (Round 4)
assert do("Delete the alarm I set.").count("alarm at") == 2 and [r[2] for r in j.load_reminders()] == ["timer"]
do("set an alarm for 7 am")
said_back = do("cancel the reminder")                              # one schedule: no reminder, so the one alarm goes
assert said_back.startswith("Cancelled: alarm at 7:00 AM") and [r[2] for r in j.load_reminders()] == ["timer"], said_back
j.save_reminders([])

# ---- live test 3: clock words and 24-hour times, several alarms at once, "no, AM" just after, a cancel put back,
# a follow-up after commands and after "didn't catch", and code replies kept in the chat history
for text, want in (("at 7 o'clock", "13 19:00"), ("at 7 in the morning", "14 07:00"), ("at 7 tonight", "13 19:00"),
                   ("at seven am", "14 07:00"), ("at seven thirty pm", "13 19:30"), ("at 1900 hours", "13 19:00"),
                   ("at 0700 hours", "14 07:00"), ("at 07:00", "14 07:00"), ("at nineteen hundred hours", "13 19:00"),
                   ("at noon", "14 12:00"), ("at midnight", "14 00:00"), ("at 7 a.m. tomorrow", "14 07:00"),
                   ("at 9 tomorrow", "14 09:00"), ("at tomorrow at 9 pm", "14 21:00"), ("at 6 in the evening", "13 18:00")):
    assert hm(text) == want, (text, hm(text))
for text in ("at 2 hours", "at a picture", "at 7 and 8", "at seven minutes", "at the stars at 9"):
    assert j.when(text, at3) is None, text
assert datetime.fromtimestamp(j.when("at 7", at3 + 6 * 3600)).strftime("%d %H:%M") == "14 07:00"   # from 9 PM: the morning
# the alarm tests below read the clock: pin it to 3 AM today (still ticking), so they pass at any hour
at_3am = datetime.now().replace(hour=3, minute=0, second=0, microsecond=0).timestamp() - real_time()
j.time.time = lambda: real_time() + at_3am
assert j.clock(cmd("set an alarm for 2 am")[2]) == "2:00 AM tomorrow"            # a time already gone: the next day
for text in ("set an alarm for 1900 hours", "Set an alarm for 7 o'clock.", "set an alarm for 7 in the morning",
             "set an alarm for seven am", "set an alarm for 7 tonight", "set an alarm for 7 a.m. tomorrow",
             "yo can you set an alarm for 7", "I need an alarm at 7"):
    assert cmd(text)[:2] == ("set", "alarm") and cmd(text)[2] is not None, (text, j.route(text))
assert cmd("set an alarm for 1900 hours")[2] - time.time() <= 86400                     # never "in 1900 hours"
two = cmd("hey set an alarm for 7 and 8 am")
assert [datetime.fromtimestamp(d).strftime("%H:%M") for d in two[2]] == ["07:00", "08:00"], two
j.save_reminders([])
said_back = do("set alarms for 7 and 8 am")
assert said_back.startswith("Alarms set for 7:00 AM") and "and 8:00 AM" in said_back and len(j.load_reminders()) == 2
assert j.undo_last() == "Removed those 2 alarms." and j.load_reminders() == []
j.time.time = real_time
# "no, AM": the alarm just set moves 12 hours; with nothing just set it is not a correction
assert j.route("No, AM.")[1] != "flip"
do("set an alarm for 7 pm")
assert j.route("No, AM.") == j.route("I meant the morning") == ("remind", "flip", ("alarm", "am"), None)
assert j.route("Morning.")[1] != "flip"
assert do("no, in the morning").startswith("Changed to 7:00 AM") and datetime.fromtimestamp(j.load_reminders()[0][0]).hour == 7
assert do("make it pm").startswith("Changed to 7:00 PM") and do("PM").startswith("It's already set for 7:00 PM")
assert len(j.load_reminders()) == 1
# a cancel is put back by "undo that"
j.save_reminders([])
do("set an alarm for 7 am"), do("set a timer for 10 minutes")
assert do("cancel my alarm").startswith("Cancelled: alarm at 7:00 AM") and len(j.load_reminders()) == 1
assert j.undo_last().startswith("Put back: alarm at 7:00 AM") and len(j.load_reminders()) == 2
assert j.undo_last() == "There's nothing to undo."
# two commands in one sentence: done one after the other when each is safe on its own
both = j.route("set an alarm for 7 am and remind me to cook in 10 minutes")
assert both[0] == "multi" and [p[:2] for p in both[2]] == [("remind", "set"), ("remind", "set")], both
assert j.route("cancel my alarm and set one for 8")[3] == j.NEAR_MISS
for text in ("lock my computer and mute", "tell me a joke and set a timer", "set a timer and set an alarm for 7"):
    assert j.route(text)[0] != "multi", text
j.save_reminders([])
j.undo.clear()
talk(1, words="Set an alarm for 7 am and remind me to cook in 10 minutes.")   # P0-03: "undo that" takes back both
assert len(j.load_reminders()) == 2 and j.undo_last() == "Removed that reminder. Removed that alarm." and j.load_reminders() == []
j.save_reminders([])
talk(1, words="Set an alarm for 7 am and set a timer for 10 minutes.")
assert asked[-1].startswith("Alarm set for 7:00 AM") and "Timer set for 10 minutes." in asked[-1] and len(j.load_reminders()) == 2
# follow-ups: after a command, not after "never mind", and once after words that could not be made out
assert talk(1, words="Set a timer for 10 minutes.") == 2
assert j.history[-2]["content"].endswith("] Set a timer for 10 minutes.")
n = len(j.history)
assert talk(99, words="Never mind.") == 1 and len(j.history) == n   # FR6: a control word ends it quietly, kept nowhere
assert j.re.match(r"\[\w{3} \d\d \w{3}, \d\d:\d\d [AP]M\] ", j.history[-2]["content"]), j.history[-2]   # day, date and time
assert talk(1, words="") == 2 and asked[-1] == "Sorry, I didn't catch that."
assert talk(99, words="") == 2                                    # silence after "didn't catch" ends it: no loop
real_turn, n = j.turn, len(asked)
j.turn = lambda tier, follow=0, woke=False: real_turn(tier, follow, True)
assert talk(99, words="") == 1 and len(asked) == n                # FR6 L9: nothing after the wake word: no reply
j.turn = real_turn
j.save_reminders([])
j.undo.clear()

# ---- 6j: one route line per turn - the path and the total, never words from the question
routes, keep = [], j.log
j.log = lambda line: routes.append(line) if line.startswith("route:") else None
for words, want, result in (("Tell me a joke.", "route: chat.chat via model, total ", "answered"),
                            ("What's the volume?", "route: info.level via rule, total ", "said"),
                            ("Set a timer for 10 minutes.", "route: command.remind set via rule, total ", "said"),
                            ("New topic.", "route: new_topic via rule, total ", "said"),
                            ("Show me what you've said.", "route: log via rule, total ", "said"),
                            ("Turn off the wifi.", "route: ", "refused - not built")):
    routes.clear()
    talk(1, words=words)
    assert len(routes) == 1 and routes[0].startswith(want), (words, routes)
    assert j.re.search(r" total \d+\.\d\ds -> " + result + "$", routes[0]), (words, routes)   # S2-9: the outcome, last
    assert not (set(j.re.findall(r"[a-z]+", words.lower())) - {"new", "topic", "set"}) & set(routes[0].split(" -> ")[0].split()), routes   # the outcome is a fixed word
# S2-9: turns that used to leave no route line: a false wake, room talk in the open ear, a command left without a yes
j.muted, j.listen, j.transcribe = (lambda: False), (lambda **k: "audio"), (lambda a: "")
routes.clear()
j.turn(0, woke=True)
assert len(routes) == 1 and routes[0].startswith("route: false_wake via rule") and routes[0].endswith("-> nothing said"), routes
routes.clear()
ear(["Set a timer for 10 minutes.", "Uh huh."])
assert routes[-1].startswith("route: ear via rule") and routes[-1].endswith("-> not for me - quiet"), routes
routes.clear()
ear(["Lock the computer.", "No."])
assert routes[-1].startswith("route: command.") and routes[-1].endswith("-> left - no yes"), routes
routes.clear()
ear(["Lock the computer.", "Yes, Jarvis."])
assert routes[-1].endswith("-> done"), routes
j.log = keep
j.save_reminders([])
j.undo.clear()
j.did.clear()
# 8a: speech that starts after the 3 s window counts only with his name; before it, as always; fake onset = seconds waited
for late, line, taken in ((2.0, "Tell me a joke.", True), (5.0, "Tell me a joke.", False), (5.0, "Jarvis, tell me a joke.", True)):
    j.onset[0] = late
    n_ask = ear(["Tell me about the moon.", line])[1]
    assert (n_ask == 2) == taken, (late, line, n_ask)
j.onset[0] = 0.0
# 8b: the chime goes through play_samples scaled by JarvisChimeVolume (default 25 %); 0 = silent
real_ps, real_set, real_res, got = j.play_samples, j.setting, j.RES, []
j.RES = tempfile.mkdtemp()                                          # a one-second stereo wav, peak 16384 (0.5)
os.mkdir(os.path.join(j.RES, "Sounds"))
with j.wave.open(os.path.join(j.RES, "Sounds", "chime.wav"), "wb") as wf:
    wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(8000)
    wf.writeframes(bytes([0, 64, 0, 64]) * 8000)
j.play_samples = lambda a, rate, progress=None: got.append(float(abs(a).max()))
for cvol, ratio in (("25", 0.25), ("100", 1.0), ("0", 0.0)):
    got.clear()
    j.setting = lambda name, default="", v=cvol: v if name == "JarvisChimeVolume" else default
    assert 0 < real_chime() <= 0.8
    for _ in range(50):
        if got: break
        time.sleep(0.05)
    assert got and abs(got[0] - ratio * 0.5) < 0.004, (cvol, got)
j.play_samples, j.setting, j.RES = real_ps, real_set, real_res
# 8c: quiet during class - a timed event of the named calendar running now; "you can talk" ends it for that event only
from jarvislib import quiet as Q
real_set, real_kv8, cal = j.setting, j.read_kv, [""]
j.read_kv = lambda name: cal[0] if name == "calendar.txt" else ""


def _cal(*events):
    cal[0] = "".join(f"E {a}|{b}|{allday}|{label}|Maths"+chr(10) for a, b, allday, label in events)
    Q._cache[0] = 0.0


t_now = int(time.time())
j.setting = lambda name, default="": "School" if name == "JarvisQuietCalendar" else default
_cal((t_now - 60, t_now + 3000, 0, "School"))
assert Q.now()                                                    # class running: muted() is true (pop-up only)
_cal((t_now - 60, t_now + 3000, 1, "School"))
assert not Q.now()                                                # an all-day event is not a class
_cal((t_now - 60, t_now + 3000, 0, "Home"))
assert not Q.now()                                                # another calendar
_cal((t_now + 600, t_now + 3000, 0, "School"))
assert not Q.now()                                                # not started yet
_cal((t_now - 60, t_now + 3000, 0, "School"))
assert Q.TALK.fullmatch("you can talk") and Q.TALK.fullmatch("speak normally") and not Q.TALK.fullmatch("you can talk to me")
assert Q.talk() and not Q.now()                                   # told he can talk: speaks until the next event
_cal((t_now - 60, t_now + 3000, 0, "School"))
assert not Q.now()
_cal((t_now - 10, t_now + 6000, 0, "School"))
assert Q.now()                                                    # the next class starts quiet again
j.setting = lambda name, default="": default
Q._cache[0] = 0.0
assert not Q.now()                                                # empty setting: never quiet
j.setting, j.read_kv = real_set, real_kv8
Q._off[0] = 0
Q._cache[0] = 0.0
# S2-8: the log names the capability (a class from the table, never your words)
caps, keep = [], j.log
j.log = caps.append
for text, cap in (("unpair my headphones", "bluetooth"), ("turn off wifi", "wifi"),
                  ("hibernate", "account"), ("sign out", "account"), ("turn on the keyboard light", "keyboard light")):
    caps.clear()
    assert j.route(text)[3] == j.CANT and f"capability: {cap} not built yet - said so" in caps, (text, caps)
j.log = keep
j.history.clear()

# ---- M4a-3: he offers to remember a lasting fact said in chat; only a yes saves it
j.save_memory(["my dentist is on Fridays"])
for text, fact in (("My sister's name is Ana and she loves cats.", "My sister's name is Ana and she loves cats"),
                   ("I'm allergic to peanuts. What snacks are safe?", "I'm allergic to peanuts"),
                   ("Jarvis, so I work at the library now.", "I work at the library now"),
                   ("My favourite colour is green.", "My favourite colour is green")):
    assert j.learnable(text) == fact, text
for text in ("Tell me a joke.", "Is my sister's name Ana?", "My bank PIN is 4821.", "My password is hunter2abc.",
             "My phone number is 0123 456 789.", "My head is killing me.", "my dentist is on Fridays",
             "My account code is X7."):
    assert j.learnable(text) == "", text
asked.clear()
talk(2, words="My sister's name is Ana.")                          # he answers, offers, then the follow-up hears it again: no yes
assert asked == ["Want me to remember that?", "Want me to remember that?"] and j.load_memory() == ["my dentist is on Fridays"]
turns = iter(["My sister's name is Ana.", "Yes."])
heard[0], speaks[0] = 0, 2
j.transcribe = lambda a: next(turns)
j.turn(0)
assert asked[-1] == "Noted: My sister's name is Ana." and j.load_memory() == ["my dentist is on Fridays", "My sister's name is Ana"]
assert j.offer == {} and j.learnable("My sister's name is Ana.") == ""        # already saved: no second offer
assert all(j.is_yes(x) for x in ("Yes, Jarvis.", "Yes sir", "Carry on", "continue")) and not j.is_yes("yes but don't")
turns = iter(["My cat is called Tom.", "Yes, Jarvis."])                 # P0-04: a name after the yes still counts
heard[0], speaks[0] = 0, 2
j.transcribe = lambda a: next(turns)
j.turn(0)
assert "My cat is called Tom" in j.load_memory()
turns = iter(["I live in Leeds.", "Yes."])                           # a late yes is just a yes
heard[0], speaks[0] = 0, 1
j.transcribe = lambda a: next(turns)
j.turn(0)
real_now = j.time.time
j.time.time = lambda: real_now() + 60
heard[0], speaks[0] = 0, 1
j.turn(0)
j.time.time = real_now
assert "I live in Leeds" not in j.load_memory()
j.setting = lambda name, default="": "off" if name == "JarvisLearn" else default
assert j.learnable("I live in Leeds.") == ""
j.setting = lambda name, default="": default
os.remove(j.MEMORY_FILE)
asked.clear()

# ---- M4b: what he actually did - the last 20 actions really run, only for questions about him
j.did.clear()
assert "You ran nothing in this session." in j.system_prompt("What did you do?")
assert "WHAT YOU ACTUALLY DID" not in j.system_prompt("Tell me a joke.")
real_actions = j.ACTIONS
j.ACTIONS = dict(real_actions, lock=lambda _: None, sleep=lambda _: 1 / 0)
assert j.run_action("lock", None, ("lock", None)) and not j.run_action("sleep", None, ("sleep", None))
j.ACTIONS = real_actions
j.memory_reply("save", "my bike is red")
r = j.route("set a timer for 10 minutes")
j.remind_reply(r[1], r[2], False)
assert [w for _, w, _ in j.did][:3] == ["locked the PC", "put the PC to sleep", "saved a fact"]
assert j.did[3][1].startswith("set a timer for ") and [ok for _, _, ok in j.did] == [True, False, True, True]
p = j.system_prompt("Did you set a timer?")
assert ": locked the PC\n" in p and "put the PC to sleep (it failed)" in p and "ran nothing" not in p
j.did_add("open", None)                                            # an odd target: a plain line, no error
assert j.did[-1][1] == "open"
for _ in range(25):
    j.did_add("media")
assert len(j.did) == 20
os.remove(j.MEMORY_FILE)
j.save_reminders([])
j.undo.clear()
j.did.clear()

# ---- M3: old topics into checked facts (fake model, fake clock), monthly re-compaction
import json
real_http, real_pick, real_gpu, real_tier = j.http_json, j.pick_model, j.gpu, j.hud_tier
j.pick_model, j.gpu, j.hud_tier = (lambda tier: "m"), (lambda: True), (lambda: 0)
answer, calls = [None], []


def _gist_model(path, payload=None, timeout=5):
    calls.append(payload["messages"][1]["content"])
    if answer[0] is None:
        raise OSError("model down")
    return {"message": {"content": json.dumps({"facts": answer[0]})}}


j.http_json = _gist_model
now = 2e9
j.save_topics([{"kw": [f"thing{i}"], "talk": [[now, f"I like thing{i} a lot", "Nice."]], "used": now - 1000 + i}
               for i in range(101)])
answer[0] = ["The user likes thing0 a lot", "The user likes Bob", "The user likes thing0 42 times"]
assert j.compact(now) and len(calls) == 1 and "I like thing0 a lot" in calls[0]   # the 101st: only the oldest
assert len(j.load_topics()) == 100 and "thing0" not in json.dumps(j.load_topics())
assert j.load_gist()[0] == [(datetime.fromtimestamp(now).strftime("%Y-%m-%d"), "The user likes thing0 a lot")]   # Bob, 42 dropped
calls.clear()
assert j.compact(now) and calls == []                             # 100 topics, none old: no model call
topics = j.load_topics()
topics[0]["used"] = now - 8 * 86400                               # unused 7 days
j.save_topics(topics)
answer[0] = None
assert j.compact(now) and len(j.load_topics()) == 100 and "tries" not in j.load_topics()[0]   # model down: kept, not counted
answer[0] = ["The user met Bob"]                                  # all dropped: kept, tried again; gone after the 3rd
for n in (1, 2):
    j.compact(now)
    assert len(j.load_topics()) == 100 and j.load_topics()[0]["tries"] == n
j.compact(now)
assert len(j.load_topics()) == 99 and len(j.load_gist()[0]) == 1
calls.clear()
topics = j.load_topics()
topics[0]["used"] = now - 8 * 86400
j.save_topics(topics)
assert j.compact(now, stop=lambda: True) is False and calls == [] and len(j.load_topics()) == 99   # a turn started
assert "- earlier: The user likes thing0 a lot" in j.recall("Do I still like thing0?")   # the gist comes back when asked
assert j.recall("Tell me a joke.") == ""
assert j.talk_list("thing0") == "From before: The user likes thing0 a lot."
assert j.compact_due(now, now - 601) and not j.compact_due(now, now - 10)
j.hud_tier = lambda: 1
assert not j.compact_due(now, now - 601)                          # LITE: a game has the card
j.hud_tier = lambda: 0
with j.busy:
    assert not j.compact_due(now, now - 601)
# M3b: only over 200 lines, once a month; the oldest lines about one thing merge into fewer, under the same check
j.save_memory(["my bike is red"])
with open(j.MEMORY_FILE, "rb") as f:
    facts_before = f.read()
apples = ["The user likes red apples", "The user likes red apples a lot", "The user eats red apples daily", "The user likes red apples"]
j.save_gist([("2026-01-01", a) for a in apples] + [("2026-01-02", f"The user saw film{i}") for i in range(197)], "")
calls.clear()
answer[0] = ["The user likes red apples a lot", "The user loves bananas"]
j.recompact(now)
lines, month = j.load_gist()
assert len(calls) == 1 and month == datetime.fromtimestamp(now).strftime("%Y-%m") and len(lines) == 198
assert lines[0] == ("2026-01-01", "The user likes red apples a lot") and lines[1] == ("2026-01-02", "The user saw film0")
j.save_gist(lines + [("2026-01-03", f"The user saw show{i}") for i in range(10)], month)
calls.clear()
j.recompact(now)
assert calls == [] and len(j.load_gist()[0]) == 208                # this month already done
j.save_gist(lines[:150], "")
j.recompact(now)
assert calls == [] and j.load_gist()[1] == ""                      # 200 lines or fewer: nothing
with open(j.MEMORY_FILE, "rb") as f:
    assert f.read() == facts_before                               # your facts are never compacted
os.remove(j.MEMORY_FILE)
os.remove(j.GIST_FILE)
j.save_topics([])
j.http_json, j.pick_model, j.gpu, j.hud_tier = real_http, real_pick, real_gpu, real_tier

# ---- M1: the active window - the last 2 exchanges for 2 minutes, while the question links to them
assert j.keywords("[Mon 14 Oct, 07:00 PM] What's the Eiffel Tower's height?") == {"eiffel", "tower", "height"}
assert j.keywords("How tall are the towers?") == {"tall", "tower"}
for text in ("New topic.", "new topic", "Jarvis, new topic.", "Okay, let's change the subject.", "New topic, why is the sky blue?"):
    assert j.NEW_TOPIC.match(j.strip_name(text)), text
for text in ("A new subject at school is hard.", "New topics in physics?", "what's a new topic for my essay"):
    assert not j.NEW_TOPIC.match(j.strip_name(text)), text
sent, real_stream = [], j.chat_stream
j.chat_stream = lambda model, messages, *a: sent.append(messages) or real_stream(model, messages, *a)
past = lambda: [m["content"] for m in sent[-1][1:-1]]             # what went in between the system prompt and the question
j.history.clear()
talk(1, words="Tell me about the Eiffel Tower.")
assert past() == []
talk(1, words="How tall is the Eiffel Tower?")                     # a shared keyword
assert past() == ["Tell me about the Eiffel Tower.", "Ha."]
talk(1, words="And why is it made of iron?")                       # a follow-up start
talk(1, words="Really?")                                           # 3 words or fewer
assert len(past()) == 4 and past()[0] == "How tall is the Eiffel Tower?"   # only the last 2 exchanges
talk(1, words="Never mind.")                                       # "never mind" keeps the window
assert "Really?" in [m["content"] for m in j.history]
talk(1, words="What's a good pasta recipe for dinner?")            # unlinked: filed and emptied
assert past() == [] and [m["content"] for m in j.history] == ["What's a good pasta recipe for dinner?", "Ha."]
talk(1, words="New topic.")                                        # files it, a fixed "Okay.", nothing kept
assert asked[-1] == "Okay." and j.history == []
talk(1, words="What's a good pasta sauce?")
talk(1, words="New topic, which pasta sauce goes with fish?")      # the rest is asked with no window
assert past() == [] and j.history[0]["content"] == "which pasta sauce goes with fish?"
j.last_turn -= 180                                                 # 3 minutes later: no window, even when linked
talk(1, words="And which pasta sauce goes with chicken?")
assert past() == [] and len(j.history) == 2
talk(1, words="Good morning.")                                     # a briefing neither sends nor files the window
assert past() == [] and len(j.history) == 2

# ---- words OR meaning (6a strict, M1 loose); a fake model with fixed vectors, so the test never needs ChromaDB
ids = {}


def fake_vec(t):
    v = [0.0] * 3000
    if j.re.search(r"teeth|dentist", t, j.re.I):
        v[0] = 1.0
    elif j.re.search(r"overheating|How hot is my computer running", t):
        v[1] = 1.0
    elif "kinda warm" in t:                                       # 0.45 from the PC example: talk yes, 6a no
        v[1], v[2] = 0.45, (1 - 0.45 ** 2) ** 0.5
    else:
        v[3 + ids.setdefault(t, len(ids))] = 1.0                 # anything else: unrelated to everything
    return v


assert not j.related("When should I see the dentist?", ["My teeth have been hurting."])   # model off: words only
j._embed[0] = lambda texts: [fake_vec(t) for t in texts]
assert j.wants("Is the machine overheating?") == {"pc"}          # no PC word, but the same as a PC example
assert j.wants("It's kinda warm in here.") == set()              # 6a is strict: 0.45 is not close enough
assert j.meaning("It's kinda warm in here.", j.BLOCK_EXAMPLES["pc"], j.MEANING_TALK)   # talk would count it
assert j.wants("Tell me a joke.") == set() and "pc" in j.wants("How hot is the GPU?")  # words still work
assert j.related("When should I see the dentist?", ["[Mon 14 Oct, 07:00 PM] My teeth have been hurting."])
j.history.clear()
talk(1, words="My teeth have been hurting all week.")
talk(1, words="When should I see the dentist?")                  # no shared word, same meaning: the window stays
assert past() == ["My teeth have been hurting all week.", "Ha."]
talk(1, words="What's the capital of France these days?")        # unrelated in words and meaning
assert past() == []
j._embed[0] = lambda texts: 1 / 0                                # the model breaks: words only, the turn goes on
assert not j.meaning("When should I see the dentist?", ["My teeth hurt."], 0.1)
j._embed[0] = None
j._vecs.clear()
real_ef = sys.modules.get("chromadb.utils.embedding_functions")
sys.modules["chromadb.utils.embedding_functions"] = None         # no ChromaDB: load_meaning leaves it off
j.load_meaning()
assert j._embed[0] is None
if real_ef is None:
    sys.modules.pop("chromadb.utils.embedding_functions")
else:
    sys.modules["chromadb.utils.embedding_functions"] = real_ef

# ---- M1b: the last results. Code picks the item from what he just listed or did; the model never does
j.save_reminders([]), j.last.clear()
assert j.route("cancel the second one") == ("say", None, None, "Which one?")      # nothing listed yet
assert j.route("cancel that")[0] == "undo" and j.route("stop it")[3] != "Which one?"   # both left as they were
do("set an alarm for 7 am"), do("set an alarm for 8 am"), do("remind me to cook in 20 minutes")
do("what alarms do I have")
second = [r for r in j.load_reminders() if r[2] != "timer"][1]                      # the order they were read out
assert do("cancel the second one") == f"Cancelled: {j.describe(second, time.time())}."
assert second not in j.load_reminders() and len(j.load_reminders()) == 2
do("what alarms do I have")
assert j.route("cancel the fourth one")[3] == "Which one?" and j.route("cancel it")[3] == "Which one?"   # 2 listed
j.last["when"] -= 180                                                              # 3 minutes later
assert j.route("cancel the first one")[3] == "Which one?"
assert do("set a timer for 10 minutes") == "Timer set for 10 minutes."
assert do("cancel it").startswith("Cancelled: ") and not [r for r in j.load_reminders() if r[2] == "timer"]
j.history.clear()
talk(1, words="What alarms do I have?")
talk(1, words="Tell me a joke.")                                                   # a joke after a list: no list
assert past() == []
talk(1, words="New topic.")
assert j.last == {}
real_open, real_owin = j.ACTIONS["open"], j.open_windows
j.ACTIONS["open"], j.open_windows = lambda target: None, lambda: ["chrome.exe"]
assert j.run_action("open", ("Google Chrome", "Chrome")) and j.last["items"] == [("Google Chrome", "Chrome")]
assert j.route("close it")[:3] == ("act", "close", "chrome.exe")                   # same confirmation as by name
assert j.route("open it again") == ("act", "open", ("Google Chrome", "Chrome"), None)
assert j.route("cancel the first one")[3] == "Which one?"                          # an app is not a reminder
j.last.update(kind="app", items=["chrome.exe"])                                   # after "close chrome"
assert j.route("reopen it") == ("act", "open", ("Google Chrome", "Chrome"), None)
j.ACTIONS["open"], j.open_windows = real_open, real_owin
j.save_reminders([]), j.last.clear(), j.undo.clear()
# ---- M2: topic memory - talk that leaves the window is filed by topic, and comes back only when it's about it
pair = lambda you, him="Ha.": [{"role": "user", "content": you}, {"role": "assistant", "content": him}]
j.save_topics([])                                                             # the M1 turns above filed talk
j.file_talk(pair("My card is 4111111111111111 and the code is hunter2abc9.", "Keep those private."))
j.file_talk(pair("[Tue 14 Oct, 07:00 PM] Set a timer for 10 minutes.", "Timer set."))   # a command reply: not filed
saved = j.json.dumps(j.load_topics())
assert len(j.load_topics()) == 1 and "4111" not in saved and "hunter2" not in saved and saved.count("[number]") == 2
j.save_topics([])
j.file_talk(pair("Tell me about the Eiffel Tower in Paris.", "It is an iron tower."))
j.file_talk(pair("What's a good pasta recipe for dinner?", "Try a carbonara."))
j.file_talk(pair("How tall is the Eiffel Tower?", "About 330 metres."))          # 2 shared keywords: the same topic
j.file_talk(pair("Is the weather nice in Tokyo?", "Mild in spring."))
topics = j.load_topics()
assert len(topics) == 3 and [len(t["talk"]) for t in topics if "eiffel" in t["kw"]] == [2]
assert j.recall("What's the capital of Japan?") == ""                         # unrelated: nothing
assert j.recall("What time is it in Tokyo?") == ""                            # one shared word is under the floor
r = j.recall("When was the Eiffel Tower built?")
assert "About 330 metres." in r and "It is an iron tower." in r and "carbonara" not in r, r
assert max(t["used"] for t in j.load_topics()) == [t for t in j.load_topics() if "eiffel" in t["kw"]][0]["used"]
for n in range(8):                                                            # 6 exchanges a topic, 200 characters a line
    j.file_talk(pair(f"Eiffel Tower fact {n}?", "The Eiffel Tower " + "very " * 60 + "tall."))
assert [len(t["talk"]) for t in j.load_topics() if "eiffel" in t["kw"]] == [6]
assert max(len(x[2]) for t in j.load_topics() for x in t["talk"]) == 200 and len(j.recall("Eiffel Tower height?")) < 700
j.save_topics([])
j._embed[0] = lambda texts: [fake_vec(t) for t in texts]                    # no shared word, the same meaning
j.file_talk(pair("My teeth have been hurting all week.", "Sorry to hear it."))
assert "My teeth" in j.recall("When should I see the dentist?") and j.recall("Any good films out?") == ""
j.save_memory(["my teeth hurt on cold drinks"])                              # M4a facts: no shared word, the same meaning
assert "cold drinks" in j.system_prompt("When should I see the dentist?") and "TOLD YOU" not in j.system_prompt("Any good films out?")
j.save_memory([])
j._embed[0] = None
j._vecs.clear()
j.setting = lambda name, default="": "off" if name == "JarvisRecall" else default
j.file_talk(pair("Tell me more about my teeth and the dentist."))
assert len(j.load_topics()) == 1 and j.recall("My teeth again?") == ""        # off: nothing filed, nothing recalled
j.setting = lambda name, default="": default
with open(j.TOPICS_FILE, "w", encoding="utf-8") as f:
    f.write("{broken")
j.file_talk(pair("My teeth again and the dentist."))
assert open(j.TOPICS_FILE, encoding="utf-8").read() == "{broken" and j.recall("My teeth and dentist?") == ""
# M2b by voice: "what do you remember about X" is said by code; "forget what we said about X" reads back, then yes
j.save_topics([])
j.file_talk(pair("Tell me about the Eiffel Tower in Paris.", "It is an iron tower."))
j.file_talk(pair("How tall is the Eiffel Tower?", "About 330 metres."))
j.file_talk(pair("What's a good pasta recipe for dinner?", "Try a carbonara."))
assert j.route("What do you remember about the Eiffel Tower?") == (
    "say", None, None, "You asked me: How tall is the Eiffel Tower; Tell me about the Eiffel Tower in Paris.")
assert j.route("What did we say about pasta?")[3] == "You asked me: What's a good pasta recipe for dinner."
assert j.route("What do you remember about the moon?")[3] == j.NO_TALK
assert j.route("Forget everything we talked about the moon.")[3] == j.NO_TALK
kind, action, gone, prompt = j.route("Jarvis, forget what we said about the Eiffel Tower.")
assert (kind, action) == ("act", "forget_talk") and prompt == (
    "Forget 1 earlier talk about that, starting with: Tell me about the Eiffel Tower in Paris.? Confirm with yes."), prompt
assert len(j.load_topics()) == 2                                              # nothing is gone before the yes
logged, keep = [], j.log
j.log = logged.append
assert j.run_action(action, gone, (action, gone)) and [t["kw"] for t in j.load_topics()] == [["carbonara", "dinner", "good", "pasta", "recipe", "try"]]
j.log = keep
assert logged == ["action: forget_talk "]                                    # no words of the talk in the log
assert j.route("What do you remember about the Eiffel Tower?")[3] == j.NO_TALK
j.save_gist([("2026-01-02", "The user likes the Eiffel Tower")], "2026-10")           # P0-06: a compacted gist line is forgotten too
kind, action, gone, prompt = j.route("forget what we said about the Eiffel Tower")
assert action == "forget_talk" and gone == ["The user likes the Eiffel Tower"] and "Forget 1 earlier item about that" in prompt, (gone, prompt)
assert j.run_action(action, gone, (action, gone)) and j.load_gist() == ([], "2026-10")                  # the #month header stays
assert j.route("forget what we said about the Eiffel Tower")[3] == j.NO_TALK
assert j.route("Forget that my dentist is on Fridays.")[:2] == ("memory", "forget")   # facts: as before
with open(j.TOPICS_FILE, "w", encoding="utf-8") as f:
    f.write("[1]")
assert j.route("What do you remember about pasta?")[3] == j.TOPICS_BAD == j.route("forget what we said about pasta")[3]
j.save_topics([])
j.history.clear()
talk(1, words="Tell me about the Eiffel Tower.")
talk(1, words="What's a good pasta recipe for dinner?")                       # unlinked: the Eiffel talk is filed
assert len(j.load_topics()) == 1 and "FROM EARLIER TALKS" not in sent[-1][0]["content"]
talk(1, words="New topic, how tall is the Eiffel Tower?")                     # no window, but the topic comes back
assert "the user said: Tell me about the Eiffel Tower." in sent[-1][0]["content"] and past() == []
j.save_topics([])
j.history.clear()

j.chat_stream = real_stream
j.history.clear()

# ---- one schedule: alarms and reminders are listed and cancelled together; timers stay apart
do("set an alarm for 7 am"), do("remind me to cook in 20 minutes"), do("set a timer for 10 minutes")
listed = do("what reminders do I have")
assert listed.startswith("You have 1 alarm and 1 reminder: ") and "alarm at 7:00 AM" in listed and "to cook" in listed, listed
assert do("what alarms do I have") == listed and do("list my timers").startswith("You have 1 timer: ")
assert do("cancel the cooking alarm").startswith("Cancelled: to cook at ")          # found by its words, whatever the noun
j.undo_last()
assert do("Cancel all reminders.").count(";") == 1 and [r[2] for r in j.load_reminders()] == ["timer"]
assert j.undo_last().startswith("Put back: ") and len(j.load_reminders()) == 3
assert do("cancel the reminder for 7").startswith("Cancelled: alarm at 7:00 AM")      # by clock time, either kind
j.save_reminders([])
assert do("what alarms do I have") == "You have no alarms or reminders."

# ---- the AI fallback: only for a near-miss, or a chat line with a command word that is not a question. The model
# names the intent and copies the words; code checks they were said, builds a fixed sentence, route() must agree
real_http = j.http_json


def ai(cmds, raw=None):
    j.http_json = lambda path, payload=None, timeout=5: {"message": {"content": raw or j.json.dumps({"commands": cmds})}}


ai([{"intent": "alarm_set", "when": "at 7"}, {"intent": "alarm_set", "when": "8 am"}])
two = j.interpret("m", "I'd love alarms at 7 and 8 am")
assert two[:2] == ("remind", "set") and [datetime.fromtimestamp(d).strftime("%H:%M") for d in two[2][1]] == ["07:00", "08:00"], two
ai([{"intent": "alarm_set", "when": "at 7"}, {"intent": "reminder_set", "label": "to cook", "when": "in 10 minutes"}])
both = j.interpret("m", "get me up at 7 and ping me to cook in 10 minutes")
assert both[0] == "multi" and [p[2][0] for p in both[2]] == ["alarm", "reminder"] and both[2][1][2][2] == "to cook", both
ai([{"intent": "volume_step"}])
assert j.interpret("m", "knock the volume down a notch") == ("act", "volume", ("step", -10), None)
ai([{"intent": "volume_step"}])                                    # P0-01: "too loud" is DOWN; both or neither way is refused
assert j.interpret("m", "the music is too loud") == ("act", "volume", ("step", -10), None)
assert j.interpret("m", "make the music a bit softer") == ("act", "volume", ("step", -10), None)
assert j.interpret("m", "the music is too quiet") == ("act", "volume", ("step", 10), None)
assert j.interpret("m", "um just be quiet, turn up the music") is None
ai([{"intent": "volume_step", "number": 20}])                      # the number said is kept; one not said is dropped
assert j.interpret("m", "knock the volume down by 20") == ("act", "volume", ("step", -20), None)
assert j.interpret("m", "knock the volume down by 5") == ("act", "volume", ("step", -10), None)
ai([{"intent": "media", "label": "next"}])
assert j.interpret("m", "bin this song") == ("act", "media", "next", None)
for text, cmds in (("wake me at 7", [{"intent": "alarm_set", "when": "at 7 am"}]),               # an invented am
                   ("set the brightness to 50", [{"intent": "volume_set", "number": 50}]),      # no volume word said
                   ("bump the sound up", [{"intent": "volume_set", "number": 40}]),             # a number not said
                   ("shut down the pc", [{"intent": "shutdown"}]),                              # not on its list
                   ("alarm clocks are loud", [{"intent": "chat"}]),
                   ("set an alarm and a timer", [{"intent": "alarm_set"}, {"intent": "timer_set"}])):   # each would ask
    ai(cmds)
    assert j.interpret("m", text) is None, text
for raw in ("not json", '{"commands": "x"}', "{}"):
    ai(None, raw)
    assert j.interpret("m", "wake me at 7") is None, raw
j.http_json = real_http
j.OLLAMA = "http://127.0.0.1:9"                                    # nothing listens there: down, never a hang
assert j.interpret("m", "wake me at 7") is None
for text, routed in (("get me up at 7", ("chat", None, None, None)), ("Change the screen colour to blue.", j.route("Change the screen colour to blue."))):
    assert j.ask_ai(text, routed), text
for text in ("should I set an alarm?", "I set an alarm yesterday", "what's a good alarm sound", "Tell me a joke.",
             "can you explain how volume works", "Is the music too loud?", "tell me about alarms"):
    assert not j.ask_ai(text, ("chat", None, None, None)), text
j.setting = lambda name, default="": "0" if name == "JarvisAIRouter" else default
assert not j.ask_ai("get me up at 7", ("chat", None, None, None))                # switched off: exactly as before
j.setting = lambda name, default="": default
# a whole turn: the AI's alarm is set and said back by code; with the AI down the model answers as before
ai([{"intent": "alarm_set", "when": "at seven thirty"}])
real_filler, said_fillers = j.filler, []
j.filler = lambda key, quiet: said_fillers.append(key)
talk(1, words="Get me up at seven thirty.")
assert asked[-1].startswith("Alarm set for 7:30") and len(j.load_reminders()) == 1, asked[-1]
assert said_fillers == ["confirm_wait"], said_fillers                # "One moment." while the AI reads it
talk(1, words="Set an alarm for 9 am.")                               # understood at once: no AI, no filler
assert said_fillers == ["confirm_wait"] and len(j.load_reminders()) == 2
j.filler = real_filler
j.save_reminders([])
j.http_json = lambda *a, **k: (_ for _ in ()).throw(OSError("down"))
n = len(prompts)
talk(1, words="Get me up at seven thirty.")
assert len(prompts) == n + 1 and j.load_reminders() == []
j.save_reminders([])
j.undo.clear()
j.http_json = real_http

# ---- Round 4: spoken clock forms, weekdays, "which one?", duplicates, move, snooze, enders, phantoms, "by N"
for text, want in (("at half past six", "13 18:30"), ("at quarter to 8", "13 19:45"), ("at quarter past 7", "13 19:15"),
                   ("at quarter to 1", "14 00:45"), ("on Monday at 7", "19 07:00"), ("next Friday at 9 am", "16 09:00"),
                   ("at 7 tomorrow morning", "14 07:00"), ("at 6 tomorrow night", "14 18:00"),
                   ("on Tuesday at 2", "20 02:00"),                    # today's weekday, time gone: next week, under 7 days
                   ("on Tuesday at 4", "13 16:00"), ("tomorrow at 9", "14 09:00")):
    assert hm(text) == want, (text, hm(text))
assert j.duration("a minute and a half") == 90 and j.duration("an hour and a half") == 5400
tomorrow9 = lambda due: datetime.fromtimestamp(due).strftime("%H:%M") == "09:00" and 0 < due - time.time() < 2 * 86400
for text, label in (("remind me to call mom tomorrow at 9", "to call mom"), ("remind me tomorrow at 9 to call mom", "to call mom"),
                    ("remind me on Friday at 9 to pay rent", "to pay rent")):
    _, op, (kind, due, got, said), _ = j.route(text)
    assert (op, kind, got) == ("set", "reminder", label) and datetime.fromtimestamp(due).strftime("%H:%M") == "09:00", text
assert tomorrow9(j.route("remind me to call mom tomorrow at 9")[2][1])
assert cmd("what time is my alarm set for") == ("list", "alarm")
assert j.route("turn it up by 20") == ("act", "volume", ("step", 20), None)
assert j.route("turn the volume down by 5")[2] == ("step", -5) and j.route("turn it up by banana")[0] == "chat"

# cancel with two alarms asks which; the answer picks one, both, or none
j.time.time = lambda: real_time() + at_3am
j.save_reminders([])
j.undo.clear()


def which(text, answer):
    j.listen, j.transcribe = lambda: "audio", lambda a: answer
    return do(text)


do("set an alarm for 7 am"), do("set an alarm for 8 am")
assert which("turn off my alarm", "the 7").startswith("Cancelled: alarm at 7:00 AM") and asked[-1].endswith("Which one?")
assert len(j.load_reminders()) == 1 and j.undo_last().startswith("Put back: alarm at 7:00 AM")
assert which("turn off my alarm", "nothing") == "Okay, I left them." and len(j.load_reminders()) == 2
assert which("turn off my alarm", "both").count(";") == 1 and j.load_reminders() == []
j.undo_last()
assert do("cancel my alarms").count(";") == 1 and j.load_reminders() == []               # plural: all, no question
j.undo_last()
# the same alarm twice is kept once
assert do("set an alarm for 7 am") == "You already have an alarm for 7:00 AM." and len(j.load_reminders()) == 2
# move: asks which with two, moves one, undo puts it back
assert which("move my alarm to 9 am", "the 8").startswith("Moved your 8:00 AM alarm to 9:00 AM")
assert sorted(datetime.fromtimestamp(r[0]).strftime("%H:%M") for r in j.load_reminders()) == ["07:00", "09:00"]
assert j.undo_last().startswith("Put back: alarm at 8:00 AM")
assert sorted(datetime.fromtimestamp(r[0]).strftime("%H:%M") for r in j.load_reminders()) == ["07:00", "08:00"]
assert which("change my alarm to 9", "") == "Okay, I left them." and asked[-1].endswith("Which one?")
j.save_reminders([])                                               # P0-03: undo after "no, PM" puts the alarm back, not deletes it
j.undo.clear()
do("set an alarm for 7 am")
first = j.load_reminders()
assert do("no, PM").startswith("Changed to") and j.load_reminders() != first
assert do("no, AM").startswith("Changed to") and j.load_reminders() == first         # a flip can be flipped again
do("no, PM")
assert j.undo_last().startswith("Put back: alarm at 7:00 AM") and j.load_reminders() == first
j.save_reminders([])
j.time.time = lambda: 2e9                                          # N7: whole seconds, so the stored round() cannot cost one
do("set a timer for 10 minutes")
before = j.load_reminders()[0][0]
assert do("add 5 minutes to the timer").startswith("The timer now has 15 minutes") and j.load_reminders()[0][0] == before + 300
assert do("make the timer 2 minutes").startswith("The timer now has 2 minutes")
assert j.undo_last().startswith("Put back: ") and j.load_reminders()[0][0] == before + 300
j.save_reminders([])
j.undo.clear()
_save = j.save_reminders                                           # P0-08: a failed save is said, not left to the popup
j.save_reminders = lambda items: (_ for _ in ()).throw(PermissionError("locked"))
_k, _op, _args, _ = j.route("set a timer for 10 minutes")
assert j.command_reply(_k, _op, _args, None, False) == "I couldn't save the reminders file, so nothing changed."
j.save_reminders = _save
assert j.load_reminders() == []
j.time.time = real_time
# snooze after the ringing stopped: only within 5 minutes of something ringing
j.rang.clear()
assert do("snooze for 10 minutes") == "Nothing is ringing right now." and j.load_reminders() == []
j.rang[:] = [time.time(), [(time.time() - 5, time.time() - 600, "reminder", "to cook")]]
assert do("snooze for 10 minutes") == "Snoozed for 10 minutes." and [r[2:] for r in j.load_reminders()] == [("reminder", "to cook")]
assert abs(j.load_reminders()[0][0] - time.time() - 600) < 5 and j.rang == []     # the file keeps whole seconds
assert do("snooze for 10 minutes") == "Nothing is ringing right now."
assert j.CLAIM.search("I've snoozed your alarm.") and j.CLAIM.search("Your alarm has been snoozed.")
j.save_reminders([])
j.undo.clear()

# enders end a follow-up without a reply; a turn you started still gets one; phantoms are silence
n, m = len(prompts), len(asked)
for words in ("Shut up.", "Be quiet!", "That's enough.", "Jarvis, stop.", "Stop talking.", "No thank you."):
    assert talk(99, words=words) == 1 and len(prompts) == n and len(asked) == m, words   # FR6 L1: never reaches the model
# courtesy: a short proper answer from code, no model, no follow-up
for words, reply in (("Thanks.", "You're welcome."), ("Okay, thank you Jarvis!", "You're welcome."),
                     ("Thank you. Thank you.", "You're welcome."), ("Bye.", "Goodbye."), ("Good night.", "Good night."),
                     ("Sorry.", "No problem.")):
    assert talk(99, words=words) == 1 and len(prompts) == n and asked[-1] == reply, words
for words in ("Hello Jarvis!", "Hey Jarvis.", "Hi there."):        # S2-10: a hello starts a talk, so the ear stays open
    assert talk(1, words=words) == 2 and len(prompts) == n and asked[-1] == "Hello.", words
real_talk_setting = j.setting                                     # JarvisCallMe: his name at the end of greetings and goodbyes
j.setting = lambda name, default="": "Senai" if name == "JarvisCallMe" else default
for words, reply in (("Hello Jarvis!", "Hello, Senai."), ("Goodbye.", "Goodbye, Senai."), ("Good night Jarvis.", "Good night, Senai."),
                     ("Thanks.", "You're welcome.")):
    heard[0], speaks[0] = 0, 1
    j.muted, j.listen, j.transcribe = lambda: False, _listen, lambda a, w=words: w
    j.turn(0)
    assert asked[-1] == reply and len(prompts) == n, (words, asked[-1])
j.setting = real_talk_setting
assert not any(rx.fullmatch("hello can you set a timer") for rx, _ in j.COURTESY)
for words in ("thanks for the help with my essay", "sorry to bother you, what time is it", "bye the way"):
    assert not any(rx.fullmatch(words) for rx, _ in j.COURTESY), words
m, j.heard_score[0] = len(asked), -1.5                           # Whisper unsure of "Thank you." after a wake: noise, silence
real_turn = j.turn
j.turn = lambda tier, follow=0, woke=False: real_turn(tier, follow, True)
assert talk(99, words="Thank you.") == 1 and len(asked) == m
j.turn, j.heard_score[0] = real_turn, 0.0
for words in ("Okay, thanks Jarvis!", "That’s all.", "no thank you", "Nope.", "I'm good."):
    assert j.ENDERS.fullmatch(" ".join(j.re.sub(r"[^a-z' ]", " ", words.lower().replace("’", "'")).split())), words
for words in ("no am", "no, set it for 8", "thanks for the help with my essay"):
    assert not j.ENDERS.fullmatch(" ".join(j.re.sub(r"[^a-z' ]", " ", words.lower()).split())), words
real_whisper = j.whisper
for phrase, want in (("Thanks for watching!", ""), (" you", ""), ("Subtitles by the Amara.org community", ""), ("...", ""),
                     ("Thank you.", "Thank you."), ("you said seven", "you said seven"), ("open chrome", "open chrome")):
    j.whisper = lambda: types.SimpleNamespace(transcribe=lambda a, **k: ([types.SimpleNamespace(text=phrase)], None))
    assert real_transcribe("audio") == want, phrase
j.whisper = real_whisper                                          # an empty transcript is already silence in turn()

# ---- Phase 3: hearing you correctly
# 3a: Whisper is told what to expect; VAD trims the silence, and an empty result is decoded once more without it
calls = []
S_ = types.SimpleNamespace


class OptWhisper:
    def __init__(self, segs):
        self.segs = segs

    def transcribe(self, audio, **k):
        calls.append(k)
        return (self.segs if k["vad_filter"] else [S_(text="yes", avg_logprob=-0.2)]), None


for dev, beam in (("cuda", 5), ("cpu", 3)):
    calls.clear()
    j._whisper_dev[0] = dev
    j.whisper = lambda: OptWhisper([S_(text="set a timer", avg_logprob=-0.3), S_(text="for ten minutes", avg_logprob=-1.4)])
    assert real_transcribe("audio") == "set a timer for ten minutes" and len(calls) == 1, calls
    k = calls[0]
    assert k["beam_size"] == beam and k["vad_filter"] is True and k["hotwords"] == "Jarvis" and k["language"] == "en", k
    assert "Jarvis" in k["initial_prompt"] and k["condition_on_previous_text"] is False, k
    assert j.heard_score[0] == -1.4, j.heard_score
calls.clear()
j.whisper = lambda: OptWhisper([])                                # VAD cut a short "yes"
assert real_transcribe("audio") == "yes" and [c["vad_filter"] for c in calls] == [True, False]
assert "initial_prompt" not in calls[1], "no prompt without VAD: on near-silence Whisper can say the prompt back"
assert j.heard_score[0] == -0.2
j.whisper, j._whisper_dev[0], j.heard_score[0] = real_whisper, None, 0.0
# the "Jarvis" hotword made real Whisper hear a short "Yes." as "Jarvis Yes." (bench, small.en on the RTX)
real_listen, real_tr = j.listen, j.transcribe
j.listen, j.transcribe = lambda: "audio", lambda audio: "Jarvis Yes."
assert j.hear() == "Yes." and j.confirmed({"expires": 2}, j.hear(), 1)
j.transcribe = lambda audio: "Jarvis"                             # the name alone stays as said
assert j.hear() == "Jarvis"
j.listen, j.transcribe = real_listen, real_tr
# a confirmation: an unsure "Okay." (a cough, Whisper's noise phrase) is never a yes; a clear one is
real_hear, real_rl = j.hear, j.reply_line
j.hear, j.reply_line = lambda: "Okay.", lambda text, quiet: None
j.heard_score[0] = -1.5
assert not j.ask_yes("Shut down the computer? Confirm with yes.", True)
j.heard_score[0] = -0.3
assert j.ask_yes("Shut down the computer? Confirm with yes.", True)
j.hear = lambda: "Shut down the computer. Confirm with yes."      # 8-A1: his own prompt back through the mic
assert not j.ask_yes("Shut down the computer? Confirm with yes.", True)
j.hear = lambda: "Yes."                                            # a short real yes still counts
assert j.ask_yes("Shut down the computer? Confirm with yes.", True)
j.hear, j.reply_line, j.heard_score[0] = real_hear, real_rl, 0.0

# 3b: a command Whisper got slightly wrong is corrected; chat is never rewritten
j.setting = lambda name, default="": default
same = lambda a, b: j.fix_route(a, j.route(a))[:3] == j.route(b)[:3]
assert same("uh could you put volume on thirty please", "set the volume to 30")    # route() reads this one itself
for heard, meant in (("set the volyum to 30", "set the volume to 30"), ("make the volume 30", "set the volume to 30"),
                     ("set the value to 30", "set the volume to 30"), ("Jarvis, valume up", "volume up")):
    assert j.route(heard)[0] != "act" and same(heard, meant), (heard, j.fix_route(heard, j.route(heard)))
for heard in ("set a tymer for 5 minutes", "set a time are for 5 minutes", "set an alarn for ate"):
    assert j.route(heard)[0] != "remind" and j.fix_route(heard, j.route(heard))[:2] == ("remind", "set"), heard
for heard in ("three volumes of a book", "tell me a joke", "what is the value of pi", "I like the music",
              "please set the volyum to 30 and then tell me a long story about it"):      # over 8 words: as said
    r = j.route(heard)
    assert j.fix_route(heard, r) is r, heard
r = j.fix_route("enmute the sound", j.route("enmute the sound"))
assert r[0] == "say" and r[3].startswith("Did you mean ") and r[3].endswith("? Say it once more."), r
assert "unmute" in r[3] and " mute" in r[3], r
r = j.fix_route("um lock my computer please", ("chat", None, None, None))
assert r[:2] == ("act", "lock") and r[3], "a correction never skips the yes"
# 3b.3: Whisper unsure + a command that acts at once -> he asks first; chat is never asked about
j.speakers, j.muted, vol[0] = _speakers, lambda: False, 40
asked.clear()
back = iter(["set the volume to 30", "no"])
j.listen, j.transcribe = lambda: "audio", lambda a: next(back, "")
j.setting = lambda name, default="": "0" if name == "JarvisFollowUp" else default
j.heard_score[0] = -1.5
j.turn(0)
assert asked[0] == "Did you say: set the volume to 30?" and asked[-1] == "Cancelled." and vol[0] == 40, asked
asked.clear()
back = iter(["set the volume to 30"])
j.heard_score[0] = 0.0
j.turn(0)
assert vol[0] == 30 and not any(a.startswith("Did you say") for a in asked), asked
asked.clear()                                                      # P0-02: the same gate for the other commands that change something
for heard, answer in (("set an alarm for 7 am", "no"), ("remember that my cat is called Tom", "no")):
    j.save_reminders([])
    back = iter([heard, answer])
    j.heard_score[0] = -1.5
    j.turn(0)
    assert asked[0] == f"Did you say: {heard}?" and asked[-1] == "Cancelled." and j.load_reminders() == [], (heard, asked)
    assert "my cat is called Tom" not in j.load_memory()
    asked.clear()


def _sure_yes(audio):                                              # the question was unsure, the yes after it is not
    word = next(back, "")
    j.heard_score[0] = 0.0 if word == "yes" else j.heard_score[0]
    return word


j.transcribe = _sure_yes
back = iter(["set an alarm for 7 am", "yes"])                    # a yes Whisper was sure of: it runs
j.heard_score[0] = -1.5
j.turn(0)
assert asked[0] == "Did you say: set an alarm for 7 am?" and len(j.load_reminders()) == 1, asked
j.save_reminders([])
asked.clear()
back = iter(["set the volume to 30", "yes"])                      # the act then says the real volume, not just "Done."
j.heard_score[0] = -1.5
j.turn(0)
assert asked[0] == "Did you say: set the volume to 30?" and asked[-1] == "Volume at 30 percent." and vol[0] == 30, asked
vol[0] = 40
j.transcribe = lambda a: next(back, "")
n, asked[:] = len(prompts), []
back = iter(["Tell me a joke."])
j.heard_score[0] = -1.5
j.turn(0)
assert len(prompts) == n + 1 and not any(a.startswith("Did you say") for a in asked), asked
j.heard_score[0] = 0.0
j.setting = lambda name, default="": default

# 3d: the microphone you picked, MME first; unknown or empty = the Windows default
lines = []
j.log = lines.append
real_sd = sys.modules.get("sounddevice")
sys.modules["sounddevice"] = S_(
    query_hostapis=lambda: [{"name": "MME"}, {"name": "Windows WASAPI"}],
    query_devices=lambda: [{"name": "Microphone (USB Mic)", "hostapi": 1, "max_input_channels": 1},
                           {"name": "Microsoft Sound Mapper - Input", "hostapi": 0, "max_input_channels": 2},
                           {"name": "Microphone (USB Mic)", "hostapi": 0, "max_input_channels": 1},
                           {"name": "Speakers (USB Mic)", "hostapi": 0, "max_input_channels": 0}])
for want, dev in (("usb MIC", 2), ("", None), ("Studio", None), ("Studio", None)):
    j.setting = lambda name, default="", want=want: want if name == "JarvisMic" else default
    assert j.mic_device() == dev, (want, j.mic_device())
assert len([x for x in lines if "studio" in x]) == 1, lines               # unknown: one line, not one per listen
j.list_mics()
with open(j.MICS_FILE, encoding="utf-8") as f:
    assert f.read().split("\n")[:-1] == ["Microphone (USB Mic)"]
j.setting = lambda name, default="": default

# 3e: other sound down while he listens, put back after; yours wins if you changed it meanwhile
heard_at = []
j.listen, j.speakers, vol[0] = mic_listen, _speakers, 50
j._listen = lambda patience: heard_at.append(vol[0]) or "audio"
assert j.listen() == "audio" and heard_at == [15] and vol[0] == 50 and not os.path.exists(j.DUCK_FILE)
j._listen = lambda patience: _no_voice("")
assert isinstance(within(2, j.listen), RuntimeError) and vol[0] == 50 and not j.mic.locked()
j._listen = lambda patience: vol.__setitem__(0, 70) or "audio"
j.listen()
assert vol[0] == 70 and not os.path.exists(j.DUCK_FILE)
heard_at.clear()
j._listen = lambda patience: heard_at.append(vol[0]) or "audio"
j.setting = lambda name, default="": "0" if name == "JarvisDuck" else default
j.listen()
assert heard_at == [70] and vol[0] == 70                          # turned off
j.setting = lambda name, default="": "50" if name == "JarvisDuckLevel" else default
j.listen()
assert heard_at[-1] == 35 and vol[0] == 70                        # the level is yours
j.setting = lambda name, default="": default
vol[0] = 0
j.listen()
assert heard_at[-1] == 0 and vol[0] == 0                          # nothing to lower
set_to = []
j.speakers = lambda mute=None, volume=None: set_to.append(volume) or (True, 60)
j.listen()
assert set_to == [None] * len(set_to), "muted: left alone"
j.speakers, vol[0] = _speakers, 15
with open(j.DUCK_FILE, "w", encoding="utf-8") as f:              # a crash while he listened
    f.write("60 15")
j.unduck()
assert vol[0] == 60 and not os.path.exists(j.DUCK_FILE)
vol[0] = 15
j.unduck()
assert vol[0] == 15, "put back once"

# 3c: why the wake word is off goes to the log; a model or microphone failure to the Control Center
class Stop(BaseException):
    pass


def stop(s):
    raise Stop


class WakeModel:
    def __init__(self, **k):
        if wake_fail[0]:
            raise RuntimeError("no model file")


def run_wake(conf):
    lines.clear()
    j.problem = lambda msg, popup=True: lines.append(("problem", msg, popup))
    j.setting = lambda name, default="": conf.get(name, default)
    j.time.sleep = stop
    try:
        j.wake_loop()
    except Stop:
        pass
    j.time.sleep = lambda s: None
    return lines


def _no_mic(**k):
    raise OSError("no input device")


wake_fail = [False]
real_oww = {m: sys.modules.get(m) for m in ("openwakeword", "openwakeword.model")}
sys.modules["openwakeword"] = S_(utils=S_(download_models=lambda model_names: None))
sys.modules["openwakeword.model"] = S_(Model=WakeModel)
sys.modules["sounddevice"].InputStream = _no_mic
assert "wake off: turned off" in run_wake({"JarvisWakeWord": "0"})
j.hud_tier = lambda: 3
assert "wake off: HUD tier 3" in run_wake({})
j.hud_tier = lambda: 0
assert "wake off: Jarvis off" in run_wake({"JarvisEnabled": "0"})
assert any(x[0] == "problem" and x[1].startswith("Wake word") and x[2] is False for x in run_wake({}) if type(x) is tuple), lines
wake_fail[0] = True
assert any(x[0] == "problem" and x[1].startswith("Wake word") and x[2] is False for x in run_wake({}) if type(x) is tuple), lines
for m, mod in list(real_oww.items()) + [("sounddevice", real_sd)]:
    if mod is None:
        sys.modules.pop(m, None)
    else:
        sys.modules[m] = mod
j.log, j.setting = (lambda *a: None), (lambda name, default="": default)

# ---- Phase 4: stopping him, and talking over him
import ctypes
import subprocess
import numpy as np
j.S = _S()
default_setting = lambda name, default="": default
# 4a: one stop: cancel set, the HUD idle at once
states.clear()
j.stop_now("test")
assert j.cancel.is_set() and states[-1] == idle
j.cancel.clear()
# a late "speaking" from a dying turn never shows after a stop; once a new turn clears it, it shows again
real_state_file, j.STATE_FILE = j.STATE_FILE, os.path.join(tempfile.mkdtemp(), "state.txt")
st = j.State()
j.cancel.set()
st.set(state="speaking")
assert st.state == "idle"
j.cancel.clear()
st.set(state="speaking")
assert st.state == "speaking"
j.STATE_FILE = real_state_file
# the sound stops mid-sentence: the stream is aborted (queued audio dropped), nothing more is written
out_log = []


class _Out:
    def __init__(self, **k):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *a):
        out_log.append("closed")

    def write(self, chunk):
        out_log.append("w")
        if out_log.count("w") == 3:
            j.cancel.set()

    def abort(self):
        out_log.append("abort")


sys.modules["sounddevice"] = S_(OutputStream=_Out)
states.clear()
real_play_samples(np.zeros(24000, np.float32), 24000)
assert out_log == ["w", "w", "w", "abort", "closed"] and states[-1] == {"level": 0.0}, out_log
j.cancel.clear()
out_log.clear()
real_play_samples(np.zeros(1920, np.float32), 24000)               # not stopped: played to the end, never aborted
assert out_log == ["w", "w", "closed"], out_log
if real_sd is None:
    sys.modules.pop("sounddevice", None)
else:
    sys.modules["sounddevice"] = real_sd
# stopped while the first sentence was made: he never shows "speaking" and plays nothing
played.clear(), states.clear()
j.play_samples = lambda a, rate, *_: played.append(a)
j.synth_audio = lambda text: (j.cancel.set(), (text, 1))[1]
assert within(5, real_speak_all, ["one", "two"]) == "" and played == [] and not any(s.get("state") == "speaking" for s in states), states
j.cancel.clear()
# his own "Jarvis": the wake word ignores it for that sentence and a second after
j.synth_audio = lambda text: (text, 1)
j.name_until[0] = 0.0
within(5, real_speak_all, ["I am Jarvis."])
assert j.name_until[0] > time.time() + 5
j.name_until[0] = 0.0
within(5, real_speak_all, ["Hello there."])
assert j.name_until[0] == 0.0
# the Windows voice: killed on a stop, killed after 60 s, and a normal run as before
procs = []


class _Proc:
    hang = False

    def __init__(self, args, **kw):
        assert "timeout" not in kw and kw.get("stdin") == subprocess.PIPE
        self.n, self.killed, self.args = 0, False, args
        procs.append(self)

    def communicate(self, data=None, timeout=None):
        self.n += 1
        assert (data is not None) == (self.n == 1), "the text is sent once"
        if _Proc.hang:
            if self.n == 3:
                j.cancel.set()
            raise subprocess.TimeoutExpired("powershell", timeout)

    def kill(self):
        self.killed = True

    def wait(self):
        return 1


real_popen, j.subprocess.Popen = j.subprocess.Popen, _Proc
assert real_windows("hello") is None and not procs[-1].killed        # ran, made no file (fake): no audio
real_mkstemp = tempfile.mkstemp                                    # a quote in the profile path is doubled
tempfile.mkstemp = lambda **k: (os.open(os.devnull, os.O_RDONLY), "C:\\Users\\O'Brien\\jarvis_x.wav")
assert real_windows("hello") is None and "('C:/Users/O''Brien/jarvis_x.wav')" in procs[-1].args[-1]
tempfile.mkstemp = real_mkstemp
_Proc.hang = True
t0 = time.time()
assert real_windows("hello") is None and procs[-1].killed and procs[-1].n == 3 and time.time() - t0 < 1
j.cancel.clear()
clock = [real_time()]
j.time.time = lambda: clock.__setitem__(0, clock[0] + 10) or clock[0]
j.cancel.set = lambda: None                                        # never stopped: only the 60 s limit ends it
assert real_windows("hello") is None and procs[-1].killed
j.time.time = real_time
del j.cancel.set
_Proc.hang, j.subprocess.Popen = False, real_popen
# a click while the model reads a missed command: it never runs, and no follow-up opens
acts, listens = [], [0]
real_ask_ai, real_interpret, real_filler = j.ask_ai, j.interpret, j.filler
j.ask_ai, j.filler = (lambda text, r: True), (lambda *a: None)
j.interpret = lambda model, text: (j.stop_now("click"), ("act", "volume", "30", None))[1]
j.run_action = lambda action, target, pending=None: acts.append(action) or True
j.muted, j.transcribe = (lambda: False), (lambda a: "make it louder")
j.listen = lambda **k: listens.__setitem__(0, listens[0] + 1) or "audio"
j.setting = default_setting
states.clear()
routes, keep = [], j.log
j.log = lambda line: routes.append(line) if line.startswith("route:") else None
j.turn(0)
j.log = keep
assert acts == [] and listens[0] == 1 and states[-1] == idle and not j.busy.locked(), (acts, listens)
assert len(routes) == 1 and routes[0].startswith("route: act volume via ai-reread, total "), routes   # 6j
j.ask_ai, j.interpret, j.filler = real_ask_ai, real_interpret, real_filler
# stopped mid-reply: no follow-up; and the HUD is idle before the slow GPU check, not after it
j.transcribe = lambda a: "Tell me a joke."
j.speak_all = lambda sentences, *a: (list(sentences), j.stop_now("click"), "")[-1]
listens[0] = 0
j.turn(0)
assert listens[0] == 1 and states[-1] == idle and not j.busy.locked()
j.speak_all = lambda sentences, *a: list(sentences)
j.ollama_on_cpu = lambda model: states.append("gpu check")
states.clear()
j.listen = lambda **k: listens.__setitem__(0, 9) or "audio" if listens[0] < 9 else None
listens[0] = 0
j.turn(0)
assert states.index(idle) < states.index("gpu check"), states
j.ollama_on_cpu = lambda model: None
# "never mind" / "quiet" / "enough" end a follow-up; a command with the word in it does not
for text in ("never mind", "quiet", "enough", "okay never mind", "stop jarvis"):
    assert j.ENDERS.fullmatch(text), text
for text in ("quiet the music", "enough of this song", "never mind the timer, set an alarm"):
    assert not j.ENDERS.fullmatch(text), text
# a stop while an alarm rings (the stop key calls stop_now): it ends, no snooze
j.ding, j.synth_audio = lambda: ("ding", 1), lambda text: (text, 1)
j.play_samples = lambda a, rate, *_: (played.append(a), j.stop_now("stop key"))
assert ring([]) == (1, ["timer"]) and convo[-1] == ("J", "(stopped)")
j.play_samples = lambda a, rate, *_: played.append(a)


# 4a-2: the stop key, registered only while he is busy, with a fake Windows
class _U32:
    def __init__(self, ok=True):
        self.calls, self.ok, self.msgs = [], ok, 0

    def RegisterHotKey(self, hwnd, n, mods, vk):
        self.calls.append(("reg", mods, vk))
        return 1 if self.ok else 0

    def UnregisterHotKey(self, hwnd, n):
        self.calls.append(("unreg",))
        return 1

    def PeekMessageW(self, *a):
        if self.msgs:
            self.msgs -= 1
            return 1
        return 0


def run_key(u32, steps, conf={}):
    """Runs stop_key_loop; after each pass the next step runs, and after the last one the loop ends."""
    j.setting = lambda name, default="": conf.get(name, default)
    real_windll, ctypes.windll, it = ctypes.windll, S_(user32=u32), iter(steps)

    def sleep(s):
        step = next(it, None)
        if step is None:
            raise Stop
        step()
    j.time.sleep = sleep
    try:
        j.stop_key_loop()
    except Stop:
        pass
    finally:
        ctypes.windll, j.time.sleep, j.setting = real_windll, (lambda s: None), default_setting
    return u32.calls


u = _U32()
lines.clear()
j.problem = lambda msg, popup=True: lines.append(("problem", msg, popup))
states.clear()
calls = run_key(u, [j.busy.acquire, lambda: None, lambda: setattr(u, "msgs", 1),
                    lambda: (lines.append(("cancelled", j.cancel.is_set())), j.busy.release())])
assert calls == [("reg", 0x4000, 0x23), ("unreg",)] and ("cancelled", True) in lines and states[-1] == idle, (calls, lines)
j.cancel.clear()
u = _U32()                                                         # idle: not registered, a stray message does nothing
assert run_key(u, [lambda: setattr(u, "msgs", 1), lambda: None]) == [] and not j.cancel.is_set()
lines.clear()
with j.busy:
    assert run_key(_U32(), [lambda: None] * 3, {"JarvisStopKey": "off"}) == []          # switched off
    assert run_key(_U32(ok=False), [lambda: None] * 3) == [("reg", 0x4000, 0x23)]       # refused once, not retried
assert [x for x in lines if x[0] == "problem"] == [("problem", "Stop key: END is taken by another app - pick another in Control Center", False)]
j.listen = lambda **k: None
j.turn(0)                                                          # a refused key changes nothing for a turn
assert states[-1] == idle and not j.busy.locked()


# 4b: talking over him, in the wake loop (fake openWakeWord and microphone)
class BargeModel:
    def __init__(self, **k):
        self.vad = S_(prediction_buffer=[]) if k.get("vad_threshold") and with_vad[0] else None
        if self.vad is None:
            del self.vad

    def reset(self):
        pass

    def predict(self, data):
        if hasattr(self, "vad"):
            self.vad.prediction_buffer.append(vad_score[0])
        return {"hey_jarvis": score[0]}


class BargeMic:
    def __init__(self, **k):
        assert j.mic.locked(), "the wake word holds the microphone while it reads"
        mic_opens.append(1)

    def start(self):
        pass

    def close(self):
        pass

    def read(self, n):
        reads[0] -= 1
        if reads[0] < 0:
            raise Stop
        return np.zeros((n, 1), np.int16), False


class _BS:
    """The HUD state, keeping the last state like the real one."""
    state = "speaking"

    def set(self, **kw):
        states.append(kw)
        self.state = kw.get("state", self.state)


barges, mic_opens, score, vad_score, with_vad, reads = [], [], [0.0], [0.0], [True], [0]
real_turn, real_thread = j.turn, threading.Thread
j.barge_turn = lambda follow: barges.append(follow)
j.turn = lambda tier, follow=0, woke=False: barges.append(("turn" if woke else "click", follow))   # a wake says so
sys.modules["openwakeword"] = S_(utils=S_(download_models=lambda model_names: None))
sys.modules["openwakeword.model"] = S_(Model=BargeModel)
sys.modules["sounddevice"] = S_(InputStream=BargeMic)
j.threading.Thread = lambda target, args=(), daemon=None: S_(start=lambda: target(*args))
j.S, j.log = _BS(), lines.append


def barge(conf, passes, speaking=True):
    """The wake loop while he speaks (holding the turn lock), for `passes` microphone reads (3 idle sleeps at most):
    what it started."""
    barges.clear(), mic_opens.clear()
    j.S.state, reads[0], n = ("speaking" if speaking else "thinking"), passes, [0]

    def sleep(s):
        n[0] += 1
        if n[0] > 3:
            raise Stop
    j.setting = lambda name, default="": conf.get(name, default)
    j.time.sleep = sleep
    with j.busy:
        try:
            j.wake_loop()
        except Stop:
            pass
    j.time.sleep, j.setting = (lambda s: None), default_setting
    if j.mic.locked():                                             # Stop came mid-read: hand the microphone back
        j.mic.release()
    return barges


score[0] = 0.8                                                     # "Hey Jarvis" over him: stopped, then one normal turn
assert barge({}, 1) == [0] and j.cancel.is_set() and len(mic_opens) == 1
j.cancel.clear()
score[0] = 0.6                                                     # over the default 0.5, but not 0.5 + 0.2 while he talks
assert barge({}, 1) == [] and not j.cancel.is_set()
score[0] = 0.8
j.name_until[0] = time.time() + 60                                 # he is saying "Jarvis" himself
assert barge({}, 1) == [] and not j.cancel.is_set()
j.name_until[0] = 0.0
assert barge({"JarvisBargeIn": "off"}, 1) == [] and mic_opens == []          # off: the microphone is dropped, as before
assert barge({}, 1, speaking=False) == [] and mic_opens == []                # busy but not talking (thinking, listening)
score[0], vad_score[0] = 0.0, 0.9                                  # voice: 0.56 s of speech, then a follow-up turn
assert barge({"JarvisBargeIn": "voice"}, 9) == [1] and j.cancel.is_set()
j.cancel.clear()
vad_score[0] = 0.9
assert barge({"JarvisBargeIn": "wake"}, 9) == []                   # wake: speech alone never stops him
with_vad[0] = False                                                # voice without the speech filter: acts as wake
lines.clear()
assert barge({"JarvisBargeIn": "voice"}, 9) == [] and any("no speech filter" in str(x) for x in lines)
score[0] = 0.8
assert barge({"JarvisBargeIn": "voice"}, 1) == [0]
j.cancel.clear()
j.S.state = "idle"                                                 # idle: a wake starts a normal turn, as before
score[0], barges[:], reads[0] = 0.8, [], 5
j.time.sleep = lambda s: (_ for _ in ()).throw(Stop())
try:
    j.wake_loop()
except Stop:
    pass
assert barges == [("turn", 0)] and not j.cancel.is_set()
j.time.sleep = lambda s: None

# ---- redesign slice F: stop words while he speaks (fake Vosk and echo canceller)
assert j.stop_heard("[unk] stop [unk]") == "stop" and j.stop_heard("[unk] that's enough") == "that's enough"
assert j.stop_heard("[unk] up [unk]") is None and j.stop_heard("[unk]") is None and j.stop_heard("") is None
assert j.stop_heard("stop", "You can stop the timer.") is None                   # he is saying it himself
assert j.stop_heard("be quiet", "Keep it quiet.") is None
assert j.stop_heard("shut up", "Pick it up later.") == "shut up"                 # his "up" is not "shut up"
j.far.clear()
j.far_add(np.ones(960, np.float32), 24000)                                     # 40 ms at Kokoro's rate -> 16 kHz
assert len(j.far) == 1 and len(j.far[0]) == 640
heard_vosk = ["[unk] stop [unk]"]


class StopRec:
    def __init__(self, model, rate, grammar):
        assert rate == 16000 and "stop" in json.loads(grammar)

    def AcceptWaveform(self, pcm):
        return True

    def Result(self):
        return json.dumps({"text": heard_vosk[0]})


real_stop = {m: sys.modules.get(m) for m in ("vosk", "pywebrtc_audio")}
sys.modules["vosk"] = S_(SetLogLevel=lambda n: None, Model=lambda path: path, KaldiRecognizer=StopRec)
sys.modules["pywebrtc_audio"] = S_(AudioProcessor=lambda **k: S_(process=lambda near, far: near))
score[0], vad_score[0], j.saying[0] = 0.0, 0.0, "Here is the weather."
lines.clear()
assert barge({}, 1) == [] and j.cancel.is_set() and "stop word heard (stop)" in lines   # stopped; no new turn
j.cancel.clear()
j.saying[0] = "You can stop the timer."                                        # his own "stop": ignored
assert barge({}, 1) == [] and not j.cancel.is_set()
sys.modules["vosk"] = None                                                     # not installed: off, logged once
lines.clear()
assert barge({}, 3) == [] and not j.cancel.is_set() and sum("stop words off" in str(x) for x in lines) == 1, lines
for m, mod in real_stop.items():
    if mod is None:
        sys.modules.pop(m, None)
    else:
        sys.modules[m] = mod
j.far.clear()
for m, mod in list(real_oww.items()) + [("sounddevice", real_sd)]:
    if mod is None:
        sys.modules.pop(m, None)
    else:
        sys.modules[m] = mod
j.threading.Thread, j.turn, j.S = real_thread, real_turn, _S()
j.log, j.setting = (lambda *a: None), default_setting

# ---- R5-6 6a: wake word training. Fake clips carry their score as the sample value (500 = 0.5)
try:
    import numpy as np
except ImportError:
    np = None
if np is not None:
    class TrainOww:
        def __init__(self, **k):
            self.model_inputs = {"hey_jarvis": 2}
            self.preprocessor = S_(get_features=lambda n: np.ones((1, n, 2)))
            if k.get("vad_threshold"):
                self.vad = S_(prediction_buffer=[])

        def reset(self):
            pass

        def predict(self, chunk):
            if hasattr(self, "vad"):
                self.vad.prediction_buffer.append(0.9 if chunk.max() > 0 else 0.0)   # any sound is speech here
            return {"hey_jarvis": float(chunk.max()) / 1000}

    def _feats(clip, oww, name, threshold=0.5, N=3):
        return np.ones((1 if clip.max() / 1000 >= threshold else 0, 2, 2))

    # "Hey Jarvis" never reaches the 0.1 floor here; "Hey" and "Jarvis" are words: every moment with speech counts
    level = {"hey_jarvis": 50, "hey": 200, "jarvis": 300}
    said = []

    def _record(sec):
        style = WAKE_ORDER[min(len(said) // 6, 2)] if sec == 3 else None
        said.append(sec)
        return np.full(int(16000 * sec), level[style] if style else 0, dtype=np.int16)

    real_oww = {m: sys.modules.get(m) for m in ("openwakeword.model", "openwakeword.custom_verifier_model")}
    sys.modules["openwakeword.model"] = S_(Model=TrainOww)
    sys.modules["openwakeword.custom_verifier_model"] = S_(get_reference_clip_features=_feats,
                                                           train_verifier_model=lambda f, y: {"pos": int(sum(y)), "all": len(y)})
    WAKE_ORDER = [s[0] for s in j.WAKE_STYLES]
    assert WAKE_ORDER == ["hey_jarvis", "hey", "jarvis"]
    real_data, j.DATA = j.DATA, tempfile.mkdtemp()
    for old in ("wake_hey_jarvis.pkl", "wake_hey_pause.pkl"):          # left from an older training
        with open(os.path.join(j.DATA, old), "wb") as f:
            f.write(b"old")
    j.record, j.play_samples, j.reply_line = _record, (lambda *a: None), (lambda text, quiet: lines.append(text))
    j.log, j.S, lines[:] = lines.append, _S(), []
    assert within(5, j.train_wake) is None and not j.busy.locked() and said == [3] * 18 + [15]
    files = sorted(os.listdir(j.DATA))
    assert files == ["wake_hey.pkl", "wake_jarvis.pkl"], files       # no recording written; old ones gone
    import pickle
    with open(os.path.join(j.DATA, "wake_hey.pkl"), "rb") as f:
        hey = pickle.load(f)
    with open(os.path.join(j.DATA, "wake_jarvis.pkl"), "rb") as f:
        jar = pickle.load(f)
    # each word learns the 15 s of talk (1 example here) AND the other word as "not it"
    assert hey["pos"] == jar["pos"] > 0 and hey["all"] == jar["all"] == 2 * hey["pos"] + 1, (hey, jar)
    assert "train: Hey Jarvis peaks 0.05 (0 examples)" in lines, lines
    assert lines[-1] == "Done. I learned 2 of the 3 ways. The log says which." and states[-1]["state"] == "idle"
    for name in files:                                                 # a click part-way: nothing new saved
        os.remove(os.path.join(j.DATA, name))
    said[:] = []
    j.play_samples = lambda *a: j.cancel.set() if len(said) == 6 else None
    assert within(5, j.train_wake) is None and os.listdir(j.DATA) == [] and not j.busy.locked()
    j.cancel.clear()
    j.DATA = real_data
    for m, mod in real_oww.items():
        if mod is None:
            sys.modules.pop(m, None)
        else:
            sys.modules[m] = mod
    j.log = lambda *a: None

# ---- FR5 N1: the ways to wake. wake_way(score, held, mine, now, hey_until, need, easy, hard, gap)
W = lambda score=0.0, held=False, now=100.0, until=0.0, **mine: j.wake_way(score, held, mine, now, until, 0.5, 0.5, 0.35, 5.0)
assert W(0.9) == (None, 0.0)                                        # W0: one moment is not enough (S1)
assert W(0.9, held=True) == ("W0", 0.0) and W(0.5, held=True)[0] == "W0"
assert W(0.45, held=True) == (None, 0.0)                            # under the backup's 0.5
assert W(hey=0.9) == (None, 105.0)                                  # "Hey" alone never wakes: it waits 5 s
assert W(now=103.0, until=105.0, jarvis=0.4) == ("HJ", 0.0)         # ... and "Jarvis" inside the wait does
assert W(now=106.0, until=105.0, jarvis=0.9) == (None, 105.0)       # "Jarvis" 6 s after "Hey": no
assert W(jarvis=0.9) == (None, 0.0)                                 # "Jarvis" without "Hey": no
assert W(now=103.0, until=105.0, jarvis=0.3) == (None, 105.0)       # under JarvisWakeHard
assert W(now=103.0, until=105.0, hey=0.9) == (None, 105.0)          # a second "Hey" does not stretch the wait
assert W(0.2, hey_jarvis=0.6) == ("HV", 0.0) and W(0.2, hey_jarvis=0.3) == (None, 0.0)   # your soft "Hey Jarvis"
assert W(0.05, hey_jarvis=0.9) == (None, 0.0)                       # ... still needs the normal score's 0.1
assert j.wake_way(0.0, False, {"hey": 0.9}, 100.0, 0.0, 0.5, 0.0, 0.35, 5.0) == (None, 0.0)   # JarvisWakeEasy=0: HJ off
real_data, j.DATA = j.DATA, tempfile.mkdtemp()                       # the checks: only the 3 styles, broken = off
for name, body in (("wake_hey.pkl", b"broken"), ("wake_hey_pause.pkl", b"old"), ("wake_jarvis.pkl", None)):
    with open(os.path.join(j.DATA, name), "wb") as f:
        f.write(body) if body else __import__("pickle").dump({"a": 1}, f)
lines[:], j.log = [], lines.append
assert j.wake_checks() == {"jarvis": {"a": 1}} and any("check hey not loaded" in str(x) for x in lines), lines
j.DATA, j.log = real_data, (lambda *a: None)

# ---- FR5 N2: Whisper's repetition loops
Seg = lambda text, cr=1.2, ns=0.1, lp=-0.3: S_(text=text, compression_ratio=cr, no_speech_prob=ns, avg_logprob=lp)
lines[:], j.log = [], lines.append
assert [s.text for s in j.no_loops([Seg(" Okay."), Seg(" Okay. Okay. Okay.", cr=2.6), Seg(" hm", ns=0.9, lp=-1.5),
                                    Seg(" quiet but sure", ns=0.9, lp=-0.2)])] == [" Okay.", " quiet but sure"]
assert lines == ["transcript: dropped (loop) 2 of 4 parts"]                   # counts only, never the words
assert j.no_repeats("So that's it. Okay. Okay. Okay. okay.") == "So that's it. Okay."
assert j.no_repeats("Yes. Yes. Set a timer.") == "Yes. Yes. Set a timer."   # twice is kept: it can be real
assert j.no_repeats("Set a timer for ten minutes.") == "Set a timer for ten minutes." and j.no_repeats("") == ""
fake_whisper = S_(transcribe=lambda audio, **k: ([Seg(" Okay."), Seg(" Okay."), Seg(" Okay."), Seg(" Okay.")], None))
j._whisper_dev[0] = "cpu"
assert j._decode(fake_whisper, "audio") == "Okay."
j.log = lambda *a: None

# S2-11: Modern Standby (S0) refuses SetSuspendState; the fallback turns the screen off, and only both failing is an error
real_windll, real_WinDLL, posted, dlls = ctypes.windll, ctypes.WinDLL, [], []
for suspend, post, want in ((1, 1, []), (0, 1, [(0xFFFF, 0x0112, 0xF170, 2)]), (0, 0, "raise")):
    posted.clear()
    dlls.clear()
    ctypes.WinDLL = lambda name, use_last_error=False, r=suspend: (                # 9-L2: the error number is kept
        dlls.append((name, use_last_error)) or S_(SetSuspendState=lambda *a: r))
    ctypes.windll = S_(user32=S_(PostMessageW=lambda *a, r=post: posted.append(a) or r))
    try:
        j.act_sleep(None)
        assert want != "raise" and posted == want, (suspend, post, posted)
        assert dlls == [("powrprof", True)], dlls
    except OSError:
        assert want == "raise"
    finally:
        ctypes.windll, ctypes.WinDLL = real_windll, real_WinDLL

# review BUG-05: the turn, an alarm and problem() may log at once; no line is lost, no .tmp clash
jb = sys.modules["jarvislib.base"]
real_convo, jb.CONVO_FILE = jb.CONVO_FILE, os.path.join(tempfile.mkdtemp(), "convo.txt")
writers = [threading.Thread(target=lambda n=n: [real_convo_add("U", f"{n} {i}") for i in range(25)]) for n in range(4)]
[w.start() for w in writers]
[w.join() for w in writers]
with open(jb.CONVO_FILE, encoding="utf-8") as f:
    assert len(f.read().splitlines()) == 100
_arch = os.path.join(os.path.dirname(jb.CONVO_FILE), time.strftime("jarvis_log-%Y-%m.txt"))
with open(_arch, encoding="utf-8") as f:                      # the monthly archive got every line too
    assert len(f.read().splitlines()) == 100
jb.CONVO_FILE = real_convo
# 7-P: the log pop-up file is a display file. Only convo_add may use it; the model never reads it back as memory
import glob as _glob
_users = [os.path.basename(p) for p in _glob.glob(os.path.join(os.path.dirname(os.path.abspath(__file__)), "jarvislib", "*.py"))
          + [os.path.join(os.path.dirname(os.path.abspath(__file__)), "jarvis.py")]
          if p.endswith("base.py") is False and "CONVO_FILE" in open(p, encoding="utf-8", errors="ignore").read().replace("CONVO_FILE,", "")]
assert _users == [], _users                                  # jarvis.py only imports the name; base.py holds convo_add
# review BUG-09: a line break in a label stays one reminder
j.save_reminders([(time.time() + 900, time.time(), "reminder", "to call\nmum\r\n")])
assert [r[3] for r in j.load_reminders()] == ["to call mum"]
j.save_reminders([])

# 9-L1: an error the HUD shows with no pop-up goes after 60 s; the last error and its time stay for "what went wrong?"
_st = j.State()
_st.set(err="No microphone found")
assert _st.err and j.LAST_ERR[0] == "No microphone found" and j.LAST_ERR[1] == _st.err_at
_st.expire_err(_st.err_at + 59)
assert _st.err, "still inside the minute"
_st.expire_err(_st.err_at + 61)
assert _st.err == "" and j.LAST_ERR[0] == "No microphone found", "the HUD line goes, the record stays"
_st.err, _st.err_at = "typed by hand", 0.0                    # no time known: its minute starts now, it is not wiped at once
_st.expire_err(1000.0)
assert _st.err == "typed by hand" and _st.err_at == 1000.0
_st.expire_err(1061.0)
assert _st.err == ""
_st.set(err="")
assert j.LAST_ERR[0] == "No microphone found", "clearing never erases the record"

# 9-2/9-3: diag.snapshot runs diag.ps1 read-only; no spoken text in its arguments, nothing but part and time in the log
import json as _json
_diag_ran, _diag_log, _diag_keep = [], [], j.log
j.log = _diag_log.append


class _Out:
    def __init__(self, code, out):
        self.returncode, self.stdout = code, out


def _diag_fake(result):
    def run(args, **kw):
        _diag_ran.append((args, kw))
        if isinstance(result, BaseException):
            raise result
        return result
    return run


_dreal = j.subprocess.run
_diag_fake_ok = _diag_fake(_Out(0, _json.dumps({"cpus": 8, "procs": [{"name": "secretapp", "pid": 1}]})))
j.subprocess.run = _diag_fake_ok
assert j.subprocess.run is _diag_fake_ok and j.subprocess.run is not _dreal, "the fake must be installed"
assert j.snapshot("processes")["cpus"] == 8
_a, _kw = _diag_ran[-1]
assert _a[-4:] == ["-Part", "processes", "-Hours", "24"] and _a[0] == "powershell" and "-File" in _a
assert _kw["timeout"] and _kw["creationflags"] == j.NO_WINDOW
assert j.snapshot("logs", 99999) and _diag_ran[-1][0][-1] == "720"
assert j.snapshot("logs", 0) and _diag_ran[-1][0][-1] == "1"
for _bad in (_Out(1, "{}"), _Out(0, ""), _Out(0, "not json"), _Out(0, "[1, 2]"),
             j.subprocess.TimeoutExpired("powershell", 15), OSError("no powershell")):
    j.subprocess.run = _diag_fake(_bad)
    assert j.snapshot("network") is None, _bad
j.subprocess.run = _diag_fake_ok
_n = len(_diag_ran)
for _bad_part in ("nope", "processes; calc", ""):
    try:
        j.snapshot(_bad_part)
        raise AssertionError("a bad part must raise")
    except ValueError:
        pass
try:
    j.snapshot("logs", "abc")
    raise AssertionError("hours must be a number")
except ValueError:
    pass
assert len(_diag_ran) == _n, "a bad part or hours never reaches PowerShell"
assert all(m.startswith("diag: ") and "secretapp" not in m for m in _diag_log) and _diag_log, _diag_log
j.subprocess.run = _run
j.log = _diag_keep

_procs = [{"name": "chrome", "pid": 100 + i, "cpu": 1.0, "mem": 1000, "io": 5} for i in range(31)] + [
    {"name": "Game.exe", "pid": 7, "cpu": 80.0, "mem": 5, "io": None}, {"name": "idle1", "pid": 8, "cpu": None}]
_t = j.top_apps(_procs, 8, "cpu")
assert _t[1] == {"name": "chrome", "count": 31, "value": 3.9}, _t[1]
assert _t[0] == {"name": "game", "count": 1, "value": 10.0}, _t[0]
assert j.top_apps(_procs, 8, "mem")[0]["value"] == 31000 and j.top_apps(None, 8, "io") == []
_g = j.gpu_apps([{"pid": 7, "util": 60}, {"pid": 7, "util": 70}, {"pid": 100, "util": 5}, {"pid": 999, "util": 90}],
                [{"pid": 7, "bytes": 2048}, {"pid": 999, "bytes": 1}], _procs)
assert _g == [{"name": "game", "util": 100, "bytes": 2048}, {"name": "chrome", "util": 5, "bytes": 0}], _g

_ev = [{"provider": "Microsoft-Windows-Kernel-Power", "id": 41, "time": 500}] * 3 + [
    {"provider": "Microsoft-Windows-DistributedCOM", "id": 10016, "time": 500},
    {"provider": "Application Error", "id": 1000, "time": 500, "app": "chrome.exe"},
    {"provider": "Application Error", "id": 1000, "time": 500, "app": "chrome.exe"},
    {"provider": "Application Hang", "id": 1002, "time": 500, "app": "Notepad.exe"},
    {"provider": "Microsoft-Windows-WHEA-Logger", "id": 17, "time": 500},
    {"provider": "Strange-Source", "id": 99, "time": 500, "message": "C:\\Users\\Bob\\secret.docx", "app": "x.exe"},
    {"provider": "Display", "id": 4101, "time": 10}]
_e = j.group_events(_ev)
assert _e[0] == {"text": "the PC shut down unexpectedly or lost power", "count": 3, "known": True}, _e
_texts = [x["text"] for x in _e]
assert "chrome crashed" in _texts and "notepad stopped responding" in _texts
assert "the processor or hardware reported an error" in _texts and "the graphics driver stopped responding and recovered" in _texts
assert {"text": "Strange-Source event 99", "count": 1, "known": False} in _e
assert not any("DistributedCOM" in t for t in _texts), "noise is skipped"
assert "secret" not in str(_e) and "Bob" not in str(_e) and "x.exe" not in str(_e)
assert all("Display" not in x["text"] and "graphics" not in x["text"] for x in j.group_events(_ev, since=100))
assert j.group_events(None) == []

# 9-4: findings() fixed rules, worst first; summary() the all-clear line
_big = [{"name": "Game.exe", "pid": 7, "cpu": 640.0, "mem": 5 * 2**30}] + _procs[:31]
_f = j.findings({"cpus": 8, "procs": _big, "mem_pct": 91})
assert _f[0]["text"] == "game is using 80% of the CPU" and _f[0]["closable"] and _f[0]["app"] == "game", _f
assert _f[0]["sev"] > _f[1]["sev"] and _f[1]["text"] == "game is using 5.0 GB of memory", _f
_f = j.findings({"cpus": 1, "procs": [dict(p, cpu=2.0) for p in _procs[:31]]})     # 31 chrome processes summed: 62%
assert [x["text"] for x in _f] == ["chrome is using 62% of the CPU"] and _f[0]["closable"], _f
assert j.findings({"cpus": 8, "procs": _procs[:31]}) == [], "31 x 1% of 8 CPUs is 3.9%, below 50"
_clean = {"cpus": 8, "procs": _procs[:31], "cpu_pct": 12.4, "mem_pct": 55, "disks": [{"drive": "C:", "free_gb": 200, "total_gb": 500}],
          "events": [], "gateway": {"ms": 3}, "public": [{"ms": 20}], "wifi": {"signal": 90}, "temps": {"cpu": 60}}
assert j.findings(_clean) == []
assert j.summary(_clean) == "I can't see anything wrong: CPU 12%, memory 55%, disk fine, no errors today.", j.summary(_clean)
assert j.summary({"cpu_pct": 5}) == "I can't see anything wrong: CPU 5%." and j.summary({}) == "I couldn't read that."
_t = lambda snap: [x["text"] for x in j.findings(snap)]
assert _t({"disks": [{"drive": "C:", "free_gb": 50, "total_gb": 1000}]}) == ["drive C is almost full, 50 GB free"]
assert _t({"disks": [{"drive": "D:", "free_gb": 5, "total_gb": 10}]}) == ["drive D is almost full, 5 GB free"]
assert not _t({"disks": [{"drive": "C:", "free_gb": 50, "total_gb": 100}]})
assert _t({"disk_busy": 95}) == ["the disk is busy 95% of the time"]
assert _t({"temps": {"gpu": 91}}) == ["the PC is running hot: GPU 91 C"] and "slowed down" in _t({"throttle": True})[0]
assert "battery saver" in _t({"battery_saver": True})[0]
assert _t({"wifi": {"signal": 30}}) == ["the Wi-Fi signal is weak, 30%"]
assert _t({"gateway": {"ms": 150}}) == ["the router is slow to answer, 150 ms"]
assert _t({"gateway": {"ms": 5}, "public": [{"ms": None}, {"ms": None}]}) == ["the router is fine but the internet is not answering"]
assert _t({"gateway": {"ms": None}, "public": [{"ms": None}]}) == ["I can't reach the router"]
assert not _t({"gateway": {"ms": 5}, "public": [{"ms": None}, {"ms": 9}]})
assert "2 device" in _t({"faulty_devices": 2})[0]
assert _t({"events": [{"text": "chrome crashed", "count": 3, "known": True}]}) == ["chrome crashed, 3 time(s)"]
assert _t({"reboot_pending": True}) == ["a restart is pending"] and _t({"uptime_days": 20}) == ["the PC has been on for 20 days"]
assert _t({"jarvis_on_cpu": True}) == ["my voice model is running on the CPU"]
_gp = [{"name": "ollama.exe", "pid": 50, "cpu": 1.0}, {"name": "chrome", "pid": 51, "cpu": 1.0}]
_f = j.findings({"procs": _gp, "gpu_util": 95, "gpu": [{"pid": 50, "util": 90}, {"pid": 51, "util": 5}]})
assert _f[0]["text"] == "my own model is using the GPU" and _f[0]["closable"] is False, _f
_f = j.findings({"procs": _gp, "gpu_util": 95, "gpu": [{"pid": 51, "util": 90}]})
assert _f[0]["text"] == "chrome is using the GPU" and _f[0]["closable"], _f
_f = j.findings({"cpus": 1, "procs": [{"name": "explorer.exe", "pid": 1, "cpu": 90.0}]})
assert _f[0]["text"] == "explorer is using 90% of the CPU" and _f[0]["closable"] is False, _f
assert j.is_protected("Explorer.EXE") and not j.is_protected("python") and not j.is_protected("chrome")
for _k in ("cpus", "procs", "cpu_pct", "mem_pct", "disks", "disk_busy", "gpu_util", "gpu", "gpumem", "temps", "throttle", "battery_saver",
           "battery", "wifi", "gateway", "public", "faulty_devices", "events", "reboot_pending", "uptime_days", "jarvis_on_cpu"):
    for _v in (None, [], {}):
        j.findings({_k: _v})
    j.summary({_k: None})
assert j.findings({}) == [] and j.findings(None) == []
_all = j.findings({"cpus": 1, "procs": _big, "mem_pct": 95, "disks": [{"drive": "C", "free_gb": 1, "total_gb": 9}], "disk_busy": 99,
                   "gpu_util": 99, "temps": {"cpu": 99}, "throttle": True, "battery_saver": True, "wifi": {"signal": 1},
                   "gateway": {"ms": None}, "faulty_devices": 1, "events": _e, "reboot_pending": True, "jarvis_on_cpu": True})
assert len(_all) > 10 and _all == sorted(_all, key=lambda x: x["sev"], reverse=True)
assert not any("broken" in x["text"].lower() for x in _all)

print("test_jarvis: OK")
