"""Hearing and wake-word evaluator (plan steps H1 and J6-1): measure before changing how he hears.

1) Record labelled clips once (needs you at the microphone; clips stay in a gitignored folder, never sent anywhere):
       python -B tools/hearing_eval.py record --out tools/hearing-clips --condition quiet
   It shows a line, you read it after the beep, 16 kHz mono WAV is saved with what you were asked to say.
   Run it again per condition: quiet, music, fan, tv, far (across the room), soft (quiet voice).
   Add "talk" clips (normal talk with no "Hey Jarvis") with --talk: those count false wakes.

2) Replay offline through the SAME Whisper settings and the SAME wake model JARVIS uses (no microphone, no speakers):
       python -B tools/hearing_eval.py score --clips tools/hearing-clips
   Prints word error rate per condition, and for the wake word the hit rate and false wakes at each sensitivity,
   so JarvisWakeSensitivity can be picked from numbers. --whisper-only / --wake-only run one half.

Nothing here changes a setting. It only reads clips and prints numbers."""
import argparse
import json
import os
import re
import sys
import tempfile
import time
import wave

HERE = os.path.dirname(os.path.abspath(__file__))
JARVIS_DIR = os.path.dirname(HERE)
LINES = ["Hey Jarvis, what time is it?", "Hey Jarvis, set a timer for ten minutes.", "Hey Jarvis, open Spotify.",
         "Hey Jarvis, turn the volume down.", "Hey Jarvis, what's on my calendar tomorrow?",
         "Hey Jarvis, remind me to call mom at six.", "Hey Jarvis, how hot is my graphics card?",
         "Hey Jarvis, tell me a joke.", "Hey Jarvis, pause the music.", "Hey Jarvis, what's the capital of Australia?"]
TALK = ["I think we should order pizza tonight.", "Did you finish the physics homework yet?",
        "The service at that place was really slow.", "Travis said he'd be here around seven.",
        "Hey, are you coming to the game on Friday?", "I need to charge my phone before we leave."]


def words(s):
    return re.sub(r"[^a-z0-9' ]", " ", (s or "").lower().replace("’", "'")).split()


def wer(ref, hyp):
    """Word error rate: (substitutions + insertions + deletions) / words in the reference."""
    r, h = words(ref), words(hyp)
    d = list(range(len(h) + 1))
    for i in range(1, len(r) + 1):
        prev, d[0] = d[0], i
        for k in range(1, len(h) + 1):
            cur = min(d[k] + 1, d[k - 1] + 1, prev + (r[i - 1] != h[k - 1]))
            prev, d[k] = d[k], cur
    return d[len(h)] / max(1, len(r))


def record(args):
    import numpy as np
    import sounddevice as sd
    os.makedirs(args.out, exist_ok=True)
    labels_path = os.path.join(args.out, "labels.jsonl")
    lines = TALK if args.talk else LINES
    with open(labels_path, "a", encoding="utf-8") as lab:
        for i, line in enumerate(lines[:args.count]):
            input(f"\n[{args.condition}] {i + 1}/{min(args.count, len(lines))}  Press Enter, then after the beep say:\n   {line}\n")
            sd.play(0.2 * np.sin(np.linspace(0, 2 * np.pi * 880 * 0.15, int(16000 * 0.15))).astype(np.float32), 16000)
            sd.wait()
            audio = sd.rec(int(16000 * args.seconds), samplerate=16000, channels=1, dtype="int16")
            sd.wait()
            name = f"{args.condition}-{'talk' if args.talk else 'cmd'}-{int(time.time())}-{i}.wav"
            with wave.open(os.path.join(args.out, name), "wb") as w:
                w.setnchannels(1)
                w.setsampwidth(2)
                w.setframerate(16000)
                w.writeframes(audio.tobytes())
            lab.write(json.dumps({"file": name, "text": line, "condition": args.condition, "wake": not args.talk}) + "\n")
            print(f"   saved {name}")


def load_clip(path):
    import numpy as np
    with wave.open(path, "rb") as w:
        assert w.getframerate() == 16000 and w.getnchannels() == 1 and w.getsampwidth() == 2, f"{path}: needs 16 kHz mono 16-bit"
        return np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16)


def score(args):
    import numpy as np
    labels = [json.loads(l) for l in open(os.path.join(args.clips, "labels.jsonl"), encoding="utf-8") if l.strip()]
    sys.argv[1:] = [tempfile.mkdtemp()]                        # jarvis' Data folder: a temp one, never the real one
    sys.path.insert(0, JARVIS_DIR)
    from jarvislib import hearing, wake
    if not args.wake_only:
        by = {}
        for lab in labels:
            if not lab["wake"]:
                continue
            a = load_clip(os.path.join(args.clips, lab["file"])).astype(np.float32) / 32768.0
            t0 = time.time()
            got = hearing.transcribe(a)
            ref = re.sub(r"^hey jarvis,?\s*", "", lab["text"], flags=re.I)   # the wake words are not part of the command
            hyp = re.sub(r"^(?:hey,? )?(?:jarvis|clover)[,.]?\s*", "", got, flags=re.I)
            e = wer(ref, hyp)
            by.setdefault(lab["condition"], []).append(e)
            if args.verbose:
                print(f"  {lab['file']}: WER {e:.2f} ({time.time() - t0:.2f}s)  said: {ref!r}  heard: {hyp!r}")
        print("\nWHISPER (word error rate, lower is better; the wake words are left out)")
        for cond, es in sorted(by.items()):
            print(f"  {cond:10s} {sum(es) / len(es):.3f}  over {len(es)} clips")
        all_e = [e for es in by.values() for e in es]
        if all_e:
            print(f"  {'ALL':10s} {sum(all_e) / len(all_e):.3f}  over {len(all_e)} clips")
    if not args.whisper_only:
        model = wake.load_model(vad_threshold=0.5)
        key = wake.wake_model()[1]
        peaks = []
        for lab in labels:
            wake.oww_reset(model)
            a = load_clip(os.path.join(args.clips, lab["file"]))
            pad = np.zeros(16000, dtype=np.int16)              # a second of silence first, as the live loop has
            a = np.concatenate([pad, a])
            best, prev, held2 = 0.0, 0.0, 0.0                  # held2: best score that held 2 blocks in a row (W0)
            for i in range(0, len(a) - 1279, 1280):
                s = float(model.predict(a[i:i + 1280]).get(key, 0.0))
                best, held2, prev = max(best, s), max(held2, min(s, prev)), s
            peaks.append((lab, best, held2))
        print("\nWAKE WORD (W0 rule: the score on 2 blocks in a row; your trained check is not used here)")
        wakes = [p for p in peaks if p[0]["wake"]]
        talks = [p for p in peaks if not p[0]["wake"]]
        for need in (0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.7):
            hit = sum(h >= need for _, _, h in wakes)
            false = sum(h >= need for _, _, h in talks)
            print(f"  sensitivity {need:.2f}: woke on {hit}/{len(wakes)} 'Hey Jarvis'"
                  + (f", false wakes {false}/{len(talks)} talk clips" if talks else ""))
        by = {}
        for lab, best, held in wakes:
            by.setdefault(lab["condition"], []).append(held)
        for cond, hs in sorted(by.items()):
            print(f"  {cond:10s} median held score {sorted(hs)[len(hs) // 2]:.2f}, lowest {min(hs):.2f} ({len(hs)} clips)")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("record")
    r.add_argument("--out", default=os.path.join(HERE, "hearing-clips"))
    r.add_argument("--condition", required=True)
    r.add_argument("--talk", action="store_true")
    r.add_argument("--count", type=int, default=10)
    r.add_argument("--seconds", type=float, default=4.0)
    s = sub.add_parser("score")
    s.add_argument("--clips", default=os.path.join(HERE, "hearing-clips"))
    s.add_argument("--whisper-only", action="store_true")
    s.add_argument("--wake-only", action="store_true")
    s.add_argument("--verbose", action="store_true")
    a = ap.parse_args()
    record(a) if a.cmd == "record" else score(a)


if __name__ == "__main__":
    main()
