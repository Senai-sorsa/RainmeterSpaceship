"""gpu: moved verbatim from jarvis.py (refactor). See JARVIS-Repair-Plan.txt, REFACTOR."""
import os
from .base import problem


# ------------------------------------------------------------------ GPU or capped CPU
def gpu():
    """True while an NVIDIA card is attached (a hybrid laptop powers it off on battery)."""
    try:
        import ctranslate2
        return ctranslate2.get_cuda_device_count() > 0
    except Exception:
        return False


def cpu_threads():
    """Threads a model may use when it has to run on the CPU: a quarter of the cores, so a turn can't take the PC."""
    return max(2, (os.cpu_count() or 8) // 4)


def cpu_in_use(what, why):
    """Say so in the log and on the hologram, without opening the pop-up."""
    problem(f"CPU in use - {what} is not on the GPU ({str(why)[:60]})", popup=False)
