"""player: moved to jarvislib/voice/player.py (refactor phase 3). This name is an alias of that module (same object),
so `import jarvislib.player` and a test that sets an attribute on it still reach the code."""
import sys
from .voice import player as _moved

sys.modules[__name__] = _moved
