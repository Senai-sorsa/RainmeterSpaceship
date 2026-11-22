"""Voice health check: makes one sentence in memory with the Python that runs it. Plays nothing, writes no log.
Run it with the Python the HUD starts:  "%LOCALAPPDATA%\\SpaceshipHUD\\venv\\Scripts\\python.exe" -B check_voice.py
Exit code 0 = the voice in JarvisVoice works (or none is set and the Windows voice works); 1 = it does not."""
import importlib.metadata as meta
import os
import shutil
import sys
import tempfile

_real_res = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
_tmp = tempfile.mkdtemp(prefix="jarvis_check_voice_")
sys.argv[1:] = [_tmp]                          # Data\ (state, logs) is a temp folder, never the skin's (same as test_jarvis)

import jarvis as j
import jarvislib.base as _base
import jarvislib.tts as _tts

_base.RES = _tts.RES = j.RES = _real_res       # Settings.inc and relative voice paths still come from the real @Resources (read only)
said = []
_base.log = _tts.log = j.log = said.append
_base.problem = _tts.problem = j.problem = lambda msg, popup=True: said.append(msg)
try:
    print("python:", sys.executable)
    for pkg in ("numpy", "onnxruntime", "kokoro-onnx", "piper-tts"):
        try:
            print(f"  {pkg} {meta.version(pkg)}")
        except meta.PackageNotFoundError:
            print(f"  {pkg} not installed")
    wanted = j.setting("JarvisVoice", "").strip().strip('"')
    out = j.synth_audio("Clover online.")
    for line in said:
        print("  " + str(line)[:160])
    used = "the voice in JarvisVoice" if j._engines else "the Windows voice"
    ok = out is not None and (bool(j._engines) or not wanted)
    print("no voice at all" if out is None else f"{len(out[0]) / out[1]:.1f} s of speech at {out[1]} Hz from {used}")
    print("check_voice:", "OK" if ok else "FAILED")
finally:
    shutil.rmtree(_tmp, ignore_errors=True)
sys.exit(0 if ok else 1)
