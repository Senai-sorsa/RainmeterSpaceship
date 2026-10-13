"""Self-check for jarvis.py: plain asserts, no test framework.  Run:  py -3 -B test_jarvis.py"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jarvis as j

# no disk, no keyboard: fixed app list, fixed window list, recorded key presses
j.start_apps = lambda: [("Google Chrome", "Chrome"), ("Microsoft Edge", "MSEdge"), ("Notepad", "notepad")]
j.read_kv = lambda name: "W chrome.exe\nW explorer.exe\nW Code.exe\n"
pressed = []
j.press_key = pressed.append

# routing: commands act, questions and dangerous phrases never do
assert j.route("lock my computer")[:2] == ("act", "lock")
assert j.route("lock my computer")[3], "lock must ask for confirmation"
assert j.route("should I restart my computer?")[0] == "chat"
assert j.route("jarvis, self destruct")[0] == "guard"
assert j.route("open chrome")[:2] == ("act", "open")
assert j.route("close chrome")[:3] == ("act", "close", "chrome.exe")

assert j.YES.search("yes") and j.YES.search("Go ahead.")
assert not j.YES.search("no") and not j.YES.search("")

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

# mute / unmute press the toggle key only when the state has to change
assert j.route("mute")[:2] == ("act", "mute") and j.route("unmute the sound")[:2] == ("act", "unmute")
for state, action, presses in ((False, "unmute", 0), (True, "unmute", 1), (False, "mute", 1), (True, "mute", 0)):
    pressed.clear()
    j.muted = lambda: state
    j.ACTIONS[action](None)
    assert len(pressed) == presses, (state, action, pressed)

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

print("test_jarvis: OK")
