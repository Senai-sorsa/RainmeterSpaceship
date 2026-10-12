import sounddevice as sd, openwakeword
from openwakeword.model import Model
openwakeword.utils.download_models(model_names=["hey_jarvis"])
m = Model(wakeword_models=["hey_jarvis"], inference_framework="onnx")
with sd.InputStream(samplerate=16000, channels=1, dtype="int16", blocksize=1280) as s:
    while True:
        d, _ = s.read(1280)
        print(round(max(m.predict(d[:, 0]).values()), 2))