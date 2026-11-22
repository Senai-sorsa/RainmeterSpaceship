"""respath.pick_res (refactor phase 9): the folder argument wins, a tool's own flag is never a folder, JARVIS_RES is the explicit override,
and with neither it is @Resources two folders above jarvislib. Imports only respath: nothing is created on disk."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from jarvislib.respath import pick_res  # noqa: E402

here = os.path.join(os.path.dirname(HERE), "jarvislib")
skin = os.path.abspath(os.path.join(here, "..", ".."))
tmp = os.path.abspath(os.path.join(HERE, "some", "folder"))

assert pick_res(["jarvis.py", tmp], {}, here) == tmp                              # the host's argument
assert pick_res(["jarvis.py", f'"{tmp}"'], {}, here) == tmp                       # quoted, as the host passes it
assert pick_res(["jarvis.py"], {}, here) == skin and pick_res([], {}, here) == skin    # no argument: the skin's own, as before
assert pick_res(["tool.py", "--cases", "x.jsonl"], {}, here) == skin              # the trap: a flag was RES="--cases"
assert pick_res(["tool.py", "-v"], {}, here) == skin
assert pick_res(["tool.py", "--cases", "x"], {"JARVIS_RES": tmp}, here) == tmp    # a tool that keeps its flags names the folder in the environment
assert pick_res(["jarvis.py", os.path.join(tmp, "arg")], {"JARVIS_RES": tmp}, here) == os.path.join(tmp, "arg")   # an explicit argument still wins
assert pick_res(["x", ""], {"JARVIS_RES": "  "}, here) == skin                    # blanks are nothing
print("respath: OK")
