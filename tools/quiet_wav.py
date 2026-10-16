"""8b: write a quieter copy of a 16-bit wav next to it: py -3 tools/quiet_wav.py <file.wav> [percent=25].
The original stays. Rainmeter's [Play] has no volume, so boot.lua plays the *_quiet.wav copy when it exists."""
import array
import sys
import wave

src, pct = sys.argv[1], float(sys.argv[2]) if len(sys.argv) > 2 else 25.0
dst = src[:-4] + "_quiet.wav"
with wave.open(src) as w:
    assert w.getsampwidth() == 2, "16-bit wav only"
    params, a = w.getparams(), array.array("h", w.readframes(w.getnframes()))
for i, v in enumerate(a):
    a[i] = int(v * pct / 100)
with wave.open(dst, "wb") as w:
    w.setparams(params)
    w.writeframes(a.tobytes())
print(dst, "at", pct, "%")
