"""#72 say_text_only always clears the live text, even when the reply stream raises. Fakes only: no speakers, no files."""
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.argv[1:] = [tempfile.mkdtemp()]                            # temp RES: no real Settings.inc, no real jarvis.log

from jarvislib.voice import output  # noqa: E402

calls = []
output.live = calls.append                                     # fake the pop-up text; the fake must be the one installed
assert output.live == calls.append, "live must be the recorder"
output.S.set = lambda **k: None                                # no HUD state file written


def boom():
    yield "one"
    raise RuntimeError("stream died")


try:
    output.say_text_only(boom(), [])
    raise AssertionError("the stream error must still propagate")
except RuntimeError:
    pass
assert calls and calls[0] == "one" and calls[-1] == "", calls
calls.clear()
output.say_text_only(iter(["a", "b"]), [])
assert calls == ["a", "a b", ""], calls
print("text-only clears live on failure: OK")
