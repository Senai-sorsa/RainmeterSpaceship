"""Voice health check: makes one sentence in memory with the Python that runs it. Plays nothing, writes no log.
Run it with the Python the HUD starts:  "%LOCALAPPDATA%\\SpaceshipHUD\\venv\\Scripts\\python.exe" -B check_voice.py
Exit code 0 = the voice in JarvisVoice works (or none is set and the Windows voice works); 1 = it does not."""
import importlib.metadata as meta
import sys

import jarvis as j

said = []
j.log = said.append
j.problem = lambda msg, popup=True: said.append(msg)
print("python:", sys.executable)
for pkg in ("numpy", "onnxruntime", "kokoro-onnx", "piper-tts"):
    try:
        print(f"  {pkg} {meta.version(pkg)}")
    except meta.PackageNotFoundError:
        print(f"  {pkg} not installed")
wanted = j.setting("JarvisVoice", "").strip().strip('"')
out = j.synth_audio("Jarvis online.")
for line in said:
    print("  " + line[:160])
used = "the voice in JarvisVoice" if j._engines else "the Windows voice"
ok = out is not None and (bool(j._engines) or not wanted)
print("no voice at all" if out is None else f"{len(out[0]) / out[1]:.1f} s of speech at {out[1]} Hz from {used}")
print("check_voice:", "OK" if ok else "FAILED")
sys.exit(0 if ok else 1)
