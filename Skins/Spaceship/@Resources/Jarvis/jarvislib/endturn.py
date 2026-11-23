"""E1/E2: has the speaker finished? Smart Turn v3.2 by Daily (pipecat-ai/smart-turn, BSD-2-Clause; turn/LICENSE-smart-turn.txt).
Input as in their inference.py: the last 8 s at 16 kHz (zeros in front if shorter), zero-mean/unit-variance, Whisper
log-mel 80x800; output is the chance the turn is complete. faster_whisper's FeatureExtractor makes the same features,
so transformers is not needed. JarvisSmartTurn=1 turns it on; any failure leaves the plain silence timers in charge."""
import os
import threading
from .base import log, setting

MODEL = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "turn", "smart-turn-v3.2-cpu.onnx")
N = 8 * 16000
_lock = threading.Lock()
_state = {"sess": None, "fe": None, "failed": False}


def enabled():
    return setting("JarvisSmartTurn", "0") == "1" and not _state["failed"] and os.path.exists(MODEL)


def _load():
    import onnxruntime as ort
    from faster_whisper.feature_extractor import FeatureExtractor
    so = ort.SessionOptions()
    so.intra_op_num_threads = so.inter_op_num_threads = 1      # small model: one thread, no fight with Whisper/Kokoro
    so.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
    _state["sess"] = ort.InferenceSession(MODEL, so, providers=["CPUExecutionProvider"])
    _state["fe"] = FeatureExtractor(feature_size=80, chunk_length=8)


def complete(audio):
    """Chance (0-1) that `audio` (float32 16 kHz, speech so far) is a finished turn; None if the model is unavailable."""
    import numpy as np
    with _lock:
        if _state["failed"]:
            return None
        try:
            if _state["sess"] is None:
                _load()
            a = np.asarray(audio, dtype=np.float32)[-N:]
            a = np.pad(a, (N - len(a), 0))
            a = (a - a.mean()) / np.sqrt(a.var() + 1e-7)
            feats = _state["fe"](a, padding=0)[None].astype(np.float32)
            return float(_state["sess"].run(None, {"input_features": feats})[0].ravel()[0])
        except Exception as e:                                  # missing package, bad file, ORT error: timers only from now on
            _state["failed"] = True
            log(f"smart turn off ({type(e).__name__}: {str(e)[:80]})")
            return None

