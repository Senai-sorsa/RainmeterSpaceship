import os, time, wave
import numpy as np
import sounddevice as sd
from kokoro_onnx import Kokoro

d = r"C:\Users\Senai\Rainmeter\Skins\Spaceship\@Resources\Jarvis\kokoro"
print("files in folder:", os.listdir(d))

model = os.path.join(d, "kokoro-v1.0.onnx")
voices = os.path.join(d, "voices-v1.0.bin")
print("model exists:", os.path.exists(model), "| voices exists:", os.path.exists(voices))

t = time.time()
k = Kokoro(model, voices)
print(f"loaded in {time.time() - t:.1f}s")

t = time.time()
samples, rate = k.create("Hello, I am Jarvis.", voice="bm_lewis", speed=1.0, lang="en-gb")
samples = np.asarray(samples, dtype=np.float32)
print(f"made {len(samples) / rate:.1f}s of audio in {time.time() - t:.1f}s")
print("max amplitude:", float(np.max(np.abs(samples))), "| has NaN:", bool(np.isnan(samples).any()))

out = os.path.join(d, "test_lewis.wav")
with wave.open(out, "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(int(rate))
    w.writeframes((np.clip(np.nan_to_num(samples), -1, 1) * 32767).astype(np.int16).tobytes())
print("saved:", out)

print("default output device:", sd.query_devices(sd.default.device[1])["name"])
sd.play(samples, rate)
sd.wait()
print("done")