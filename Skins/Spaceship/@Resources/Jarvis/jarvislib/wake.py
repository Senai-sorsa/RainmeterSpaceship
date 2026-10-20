"""wake: the wake word ("Hey Jarvis" / "Hey Clover"): which model, your trained check, the rule that decides, and the
training. Moved out of jarvis.py in Phase 10B (S2-4). The training needs the ding, reply_line and turn_id of the
knot, so train() takes them as arguments; this module never imports jarvis.py."""
import os
import threading
import time
from .base import DATA, RES, S, busy, cancel, live, log, mic, problem, setting
from .mic import mic_device
from .speech import muted, play_samples

# Your own "Hey Jarvis" becomes a small check next to the normal score (Fix Round 5 N1). It never wakes him alone:
# it only lets a soft "Hey Jarvis" in your voice through (HV). Phase 10B W1: the old "Hey" and bare "Jarvis" checks
# are gone - a bare name woke him on a normal score of 0.04.
# The recordings stay in memory and are never written; only the check is saved, as Data\wake_hey_jarvis.pkl.
WAKE_STYLES = (("hey_jarvis", "Hey {n}", 'say "Hey {n}"'),)   # style names are pickle names; {n} = wake_name()
OLD_CHECKS = ("wake_hey.pkl", "wake_jarvis.pkl", "wake_hey_pause.pkl")   # dropped styles: removed by the next training
WAKE_FLOOR = 0.1                       # the lowest normal score a moment needs to count as an example
HV_FLOOR = 0.3                         # the lowest normal score the trained "Hey Jarvis" check may wake on (0.1-0.26 were all accidents)
HV_NEED = 0.5                          # ... and the check's own score
REPEATS = 6                            # "Hey <name>" this many times after a ding
TALK_SECONDS = 15                      # then this much normal talk, the "not him" examples

TRAINING = threading.Event()           # set while train() runs: the wake loop does no barge-in and no stop words then

_wake_warned = [None]
_wake_bad = set()                                              # custom wake files that would not load: Hey Jarvis instead


def heard_speech(oww):
    """The speech filter heard speech 0.4-0.56 s ago, the same frames openWakeWord itself checks."""
    vad = list(getattr(getattr(oww, "vad", None), "prediction_buffer", []))[-7:-4]
    return bool(vad) and max(vad) >= 0.5


def oww_reset(m):
    m.reset()
    if hasattr(m, "vad"):
        m.vad.prediction_buffer.clear()                   # reset() keeps it: the last clip's speech would count here


def wake_model():
    """JarvisWakeModel -> (model argument, score key). A value ending in .onnx is a file in Jarvis\\wake\\."""
    v = setting("JarvisWakeModel", "hey_jarvis").strip()
    if v.lower().endswith(".onnx") and v not in _wake_bad:
        path = os.path.join(RES, "Jarvis", "wake", os.path.basename(v.replace("\\", "/")))
        if os.path.isfile(path):
            return path, os.path.basename(path)[:-5]
        if _wake_warned[0] != v:                               # once per value, not every 80 ms
            _wake_warned[0] = v
            log(f"wake: {v} not found - using Hey Jarvis")
    return "hey_jarvis", "hey_jarvis"


def wake_name():
    """The name to say after "Hey": Clover for the hey_clover model, else Jarvis."""
    return "Clover" if wake_model()[1].lower() == "hey_clover" else "Jarvis"


def wake_way(score, held, mine, need):
    """Which way wakes him on this 80 ms moment, or None.
    score: the normal "Hey <name>" score; held: it was >= need on the moment before too; mine: your trained check's
    score by style (only while speech is heard). Both ways need the normal model to score: a name alone never wakes him."""
    if score >= need and held:                                 # W0: the normal model, 2 moments in a row
        return "W0"
    if score >= HV_FLOOR and mine.get("hey_jarvis", 0.0) >= HV_NEED:   # HV: a soft "Hey Jarvis" in your voice
        return "HV"
    return None


def is_talking(locked, state, barge):
    """He is speaking and the wake loop may take the microphone for a barge-in (a stop word, "Hey <name>" over his voice).
    Never while the wake training runs: its prompts must not be cut off by a "stop" or by your own "Hey Jarvis"."""
    return bool(locked and state == "speaking" and barge != "off" and not TRAINING.is_set())


def wake_checks():
    """Your trained check from Data\\wake_<style>.pkl; a missing or broken one leaves that way off."""
    import pickle
    checks = {}
    for name, _, _ in WAKE_STYLES:
        path = os.path.join(DATA, f"wake_{name}.pkl")
        if os.path.exists(path):
            try:
                with open(path, "rb") as f:
                    checks[name] = pickle.load(f)
            except Exception as e:
                log(f"wake: check {name} not loaded ({type(e).__name__})")
    return checks


def need_level():
    """JarvisWakeSensitivity: the normal score that wakes him (0.2-0.9, default 0.5; lower = more sensitive)."""
    try:
        return max(0.2, min(0.9, float(setting("JarvisWakeSensitivity", "0.5"))))
    except ValueError:
        return 0.5


def load_model(**vad):
    """The openWakeWord model for JarvisWakeModel. A custom file that will not load falls back to Hey Jarvis (logged once);
    the first run fetches the shipped model."""
    import openwakeword
    from openwakeword.model import Model
    arg = wake_model()[0]
    try:
        return Model(wakeword_models=[arg], inference_framework="onnx", **vad)
    except ImportError:
        raise
    except Exception as e:
        if arg != "hey_jarvis" and os.path.isfile(arg):
            try:
                Model(wakeword_models=[arg], inference_framework="onnx")   # without the speech filter: is the file itself bad?
            except Exception as e2:
                _wake_bad.add(setting("JarvisWakeModel", "hey_jarvis").strip())
                log(f"wake: {os.path.basename(arg)} would not load ({type(e2).__name__}) - using Hey Jarvis")
                return load_model(**vad)                       # wake_model() now answers hey_jarvis
            raise e                                            # the file is fine, the speech filter is not: the caller handles it
        openwakeword.utils.download_models(model_names=[arg])   # first run: fetch the shipped model
        return Model(wakeword_models=[arg], inference_framework="onnx", **vad)


# shortcut: a click stops it only between clips (at most 15 s late); a stoppable recorder if that ever matters
def record(sec):
    """`sec` seconds from the microphone as 16 kHz int16, the form openWakeWord reads."""
    import sounddevice as sd
    if not mic.acquire(timeout=3):
        raise RuntimeError("The microphone is busy - try again")
    try:
        a = sd.rec(int(16000 * sec), samplerate=16000, channels=1, dtype="int16", device=mic_device())
        sd.wait()
        return a[:, 0]
    finally:
        mic.release()


def step(text):
    """The step now asked of you, kept in the pop-up until the next one: with the volume off it is the only cue."""
    S.set(pop="open")
    live(text)


def train(say, ding, turn_id):
    """Control Center WAKE WORD > TRAIN: "Hey <name>" six times after a ding, then 15 s of normal talk as the "not him"
    examples. Holds the turn lock, so the wake word lets go of the microphone; it also does no barge-in and no stop
    words meanwhile (TRAINING). A click, the End key or QUIT stops it. say(text, quiet), ding() and turn_id come from jarvis.py."""
    with busy:
        cancel.clear()
        turn_id[0] = time.time()
        TRAINING.set()
        try:
            import pickle
            import numpy as np
            from openwakeword.model import Model
            from openwakeword.custom_verifier_model import get_reference_clip_features, train_verifier_model
            name = wake_name()
            if muted():                                        # no voice and no ding: say where the steps will be
                say("The volume is off. I'll show each step here instead.", True)
            say(f'After each ding, say "Hey {name}". {REPEATS} times.', muted())
            clips = []
            for i in range(1, REPEATS + 1):
                step(f'Say "Hey {name}" after the ding - {i} of {REPEATS}')
                S.set(state="listening", level=0.0)            # not "speaking": the wake word would keep the microphone
                play_samples(*ding())
                if cancel.is_set():
                    return
                clips.append(record(3))
                if cancel.is_set():
                    return
            say(f"Now talk normally for {TALK_SECONDS} seconds, about anything, without my name.", muted())
            step(f"Talk normally now - {TALK_SECONDS} seconds")
            S.set(state="listening", level=0.0)
            neg = record(TALK_SECONDS)
            if cancel.is_set():
                return
            live("")
            arg, key = wake_model()
            try:                                               # the speech filter picks the moments of speech
                oww = Model(wakeword_models=[arg], inference_framework="onnx", vad_threshold=0.5)
            except Exception as e:
                log(f"train: without the speech filter ({type(e).__name__}) - the check stays off")
                oww = Model(wakeword_models=[arg], inference_framework="onnx")
            pad = np.zeros(16000, dtype=np.int16)              # the model scores 0 for its first frames
            oww.reset()
            negf = get_reference_clip_features(np.concatenate([pad, neg]), oww, key, threshold=0.0, N=1)
            for old in OLD_CHECKS:                             # the dropped styles must not outlive this training
                if os.path.exists(os.path.join(DATA, old)):
                    os.remove(os.path.join(DATA, old))
            made = 0
            for style, label, _ in WAKE_STYLES:
                if cancel.is_set():
                    return
                label = label.format(n=name)
                path = os.path.join(DATA, f"wake_{style}.pkl")
                peak, pos = 0.0, []
                for c in clips:
                    c = np.concatenate([pad, c])
                    oww.reset()
                    peak = max([peak] + [oww.predict(c[i:i + 1280])[key] for i in range(0, len(c) - 1280, 1280)])
                    oww.reset()
                    pos.append(get_reference_clip_features(c, oww, key, threshold=WAKE_FLOOR, N=3))
                pos = np.vstack(pos)
                log(f"train: {label} peaks {peak:.2f} ({len(pos)} examples)")
                if len(pos) == 0:                              # never reached the floor: that way stays off
                    if os.path.exists(path):
                        os.remove(path)                        # an older check must not outlive this training
                    continue
                check = train_verifier_model(np.vstack([pos, negf]), np.array([1] * len(pos) + [0] * len(negf)))
                with open(path + ".tmp", "wb") as f:
                    pickle.dump(check, f)
                os.replace(path + ".tmp", path)
                made += 1
            say(f"Done. I learned your Hey {name}." if made else "I couldn't learn it - the log says why.", muted())
        except ImportError as e:                               # reported, not a dead thread: the button said "will tell you"
            missing = getattr(e, "name", None) or str(e)
            log(f"wake training: missing module - {e}")
            problem(f"Wake word training needs {missing} - run Control Center > CLOVER > SETUP")
        except Exception as e:
            log(f"wake training failed: {e!r}")
            problem("Wake word training failed")
        finally:
            TRAINING.clear()
            live("")
            S.set(state="idle", level=0.0)
