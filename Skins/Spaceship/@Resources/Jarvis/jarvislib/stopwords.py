"""stopwords: moved verbatim from jarvis.py (refactor). See JARVIS-Repair-Plan.txt, REFACTOR."""
import json
import os
import re
from collections import deque
from .base import RES, mic


# ------------------------------------------------------------------ stop words while he speaks (redesign slice F, L1)
# While he speaks, the wake-word thread's microphone blocks also go to Vosk, which knows only the stop phrases. First a
# WebRTC echo canceller takes his own voice out (the samples play_samples is playing are the reference), and a stop
# phrase that is in what he is saying right now is ignored. About 4 % of one CPU core while he speaks, none otherwise.
STOP_PHRASES = ("jarvis stop", "that's enough", "shut up", "be quiet", "stop", "quiet", "cancel", "enough")
far = deque(maxlen=50)                  # what he played, in 16 kHz pieces (about 2 s): the echo canceller's reference
saying = [""]                           # his current and previous sentence: the text guard


def far_add(a, rate):
    """Keep what is being played, at the microphone's 16 kHz, for the echo canceller."""
    import numpy as np
    a = a if a.ndim == 1 else a.mean(axis=1)
    n = int(len(a) * 16000 / rate)
    far.append(np.interp(np.arange(n) * (rate / 16000), np.arange(len(a)), a).astype(np.float32))


def stop_heard(text, guard=""):
    """The stop phrase in Vosk's text, unless he is saying it himself (its last word is in his sentence)."""
    text, guard = text.lower(), guard.lower()
    for p in STOP_PHRASES:
        key = p if p == "shut up" else p.split()[-1]
        if re.search(rf"\b{p}\b", text) and not re.search(rf"\b{key}\b", guard):
            return p
    return None


class StopWords:
    """Vosk on echo-cancelled microphone audio. One echo canceller for the session: it stays tuned to the room."""
    def __init__(self):
        import numpy as np
        import pywebrtc_audio
        import vosk
        vosk.SetLogLevel(-1)
        self.np, self.vosk = np, vosk
        self.model = vosk.Model(os.path.join(RES, "Jarvis", "vosk", "vosk-model-small-en-us-0.15"))
        self.grammar = json.dumps(list(STOP_PHRASES) + ["[unk]"])
        # gain control after the echo canceller: offline, a "stop" said over him was caught 18 of 22 times, not 14
        self.aec = pywebrtc_audio.AudioProcessor(sample_rate=16000, num_channels=1, echo_cancellation=True,
                                                 auto_gain_control=True, stream_delay_ms=40)
        self.rec, self.ref = None, np.zeros(0, np.float32)

    def feed(self, block, fresh):
        """One 16 kHz int16 microphone block -> the stop phrase heard, or None. fresh: he just started speaking."""
        np = self.np
        if fresh or self.rec is None:
            self.rec = self.vosk.KaldiRecognizer(self.model, 16000, self.grammar)
            self.ref = np.concatenate(list(far) or [np.zeros(0, np.float32)])[-4800:]   # what he played in the last 0.3 s
            far.clear()
        while len(self.ref) < len(block) and far:
            self.ref = np.concatenate([self.ref, far.popleft()])
        ref = np.pad(self.ref[:len(block)], (0, max(0, len(block) - len(self.ref))))
        self.ref = self.ref[len(block):]
        mic = block.astype(np.float32) / 32768
        out = np.concatenate([self.aec.process(mic[i:i + 160], ref[i:i + 160]) for i in range(0, len(mic), 160)])
        if self.rec.AcceptWaveform((np.clip(out, -1, 1) * 32767).astype(np.int16).tobytes()):
            return stop_heard(json.loads(self.rec.Result()).get("text", ""), saying[0])
        return None
