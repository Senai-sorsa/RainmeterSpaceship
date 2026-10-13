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

print("test_jarvis: OK")
