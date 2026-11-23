"""D2: record the wake test bank (git-ignored; your voice never leaves this PC). 16 kHz mono int16 wav, openWakeWord's input.

  python tools/record_wake_bank.py wake 15 desk      15 clips of "Hey Jarvis" (3 s each), file names tagged "desk"
  python tools/record_wake_bank.py wake 15 room      the same from across the room
  python tools/record_wake_bank.py room 30           30 minutes of normal room audio (talk, music, typing), 1-minute files

Optional last argument --mic=<part of the device name> (default: the Windows default input). Ctrl+C stops; files
already written are kept. JARVIS can keep running: Windows shares the microphone."""
import os
import sys
import time
import wave

import numpy as np
import sounddevice as sd

RATE = 16000
BANK = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tests", "wake_bank")


def device(args):
    want = next((a.split("=", 1)[1].lower() for a in args if a.startswith("--mic=")), "")
    if not want:
        return None
    hits = [i for i, d in enumerate(sd.query_devices()) if d["max_input_channels"] > 0 and want in d["name"].lower()]
    if not hits:
        sys.exit(f"no input device matches '{want}'")
    return hits[0]


def save(path, audio):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes((np.clip(audio, -1, 1) * 32767).astype(np.int16).tobytes())


def grab(sec, dev):
    a = sd.rec(int(sec * RATE), samplerate=RATE, channels=1, dtype="float32", device=dev)
    sd.wait()
    return a[:, 0]


def next_index(folder):
    names = os.listdir(folder) if os.path.isdir(folder) else []
    return 1 + max([int(n[:3]) for n in names if n[:3].isdigit()] or [0])


def main(args):
    if len(args) < 2 or args[0] not in ("wake", "room") or not args[1].isdigit():
        sys.exit(__doc__)
    kind, n, tag = args[0], int(args[1]), next((a for a in args[2:] if not a.startswith("--")), "x")
    dev, folder = device(args), os.path.join(BANK, args[0])
    i = next_index(folder)
    if kind == "wake":
        print(f"{n} clips. Say \"Hey Jarvis\" once, normally, after each GO. Vary how you say it a little.")
        for k in range(n):
            print(f"\n[{k + 1}/{n}] ready...", end="", flush=True)
            time.sleep(1.2)
            print(" GO", flush=True)
            a = grab(3.0, dev)
            peak = float(np.abs(a).max())
            save(os.path.join(folder, f"{i:03d}_{tag}.wav"), a)
            print(f"  saved {i:03d}_{tag}.wav (peak {peak:.2f}{', very quiet: check the mic' if peak < 0.02 else ''})")
            i += 1
    else:
        print(f"Recording {n} min of room audio in 1-minute files. Do NOT say the wake word. Ctrl+C to stop early.")
        for k in range(n):
            a = grab(60.0, dev)
            save(os.path.join(folder, f"{i:03d}_{tag}.wav"), a)
            print(f"  minute {k + 1}/{n} saved ({i:03d}_{tag}.wav, rms {float(np.sqrt(np.mean(a * a))):.3f})", flush=True)
            i += 1
    print(f"\ndone: {folder}")


if __name__ == "__main__":
    try:
        main(sys.argv[1:])
    except KeyboardInterrupt:
        print("\nstopped; files already saved are kept")
