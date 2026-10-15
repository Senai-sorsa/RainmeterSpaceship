"""stopkey: moved verbatim from jarvis.py (refactor). See JARVIS-Repair-Plan.txt, REFACTOR."""
import ctypes
import time
from .base import busy, log, problem, setting, stop_now


STOP_KEYS = {"end": 0x23}                                     # VK_END


def stop_key_loop():
    """JarvisStopKey (End, or off): while he is busy the key stops him, like a click; when idle it is not taken, so it
    never wakes him and other apps keep it. A hotkey belongs to the thread that made it, so all of it runs here."""
    import ctypes
    from ctypes import wintypes
    user32 = ctypes.windll.user32
    msg, held, refused = wintypes.MSG(), None, None           # held: the key name now registered; refused: the one Windows said no to
    while True:
        try:
            key = setting("JarvisStopKey", "end").strip().lower()
            want = key if busy.locked() and key in STOP_KEYS and key != refused else None
            if held and held != want:
                user32.UnregisterHotKey(None, 1)
                held = None
            if want and not held:
                if user32.RegisterHotKey(None, 1, 0x4000, STOP_KEYS[want]):   # MOD_NOREPEAT
                    held = want
                else:
                    refused = want                             # not retried until the setting changes
                    log(f"stop key: Windows refused {want.upper()} (another app has it)")
                    problem(f"Stop key: {want.upper()} is taken by another app - pick another in Control Center", popup=False)
            if refused and key != refused:
                refused = None
            while user32.PeekMessageW(ctypes.byref(msg), None, 0x0312, 0x0312, 1):   # WM_HOTKEY, PM_REMOVE
                if held:
                    stop_now("stop key")
        except Exception as e:
            log(f"stop key: {e!r}")
            time.sleep(5)
        time.sleep(0.05)
