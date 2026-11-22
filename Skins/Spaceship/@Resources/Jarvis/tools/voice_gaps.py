"""Voice seam report: how the reply is cut into chunks and how much silence sits at each seam, today vs JarvisVoiceSmooth=1.
    python -B tools/voice_gaps.py [--no-synth] [--out DIR] [--wav N] [--cases tools/voice_cases.txt]
Offline and SILENT: nothing is played, only synthesised (Kokoro, on the GPU if onnxruntime can, else the CPU) and measured.
Old way = chunks from sentences_from with the 5-word start, every chunk its own stream (modelled with the measured open cost,
OPEN_MS) plus the clip's own near-silence at both ends. New way = the smooth chunker + merge + trim/fade + chosen pauses, assembled
exactly as the Player writes them. Seam silence = the run of near-silence around the cut (below -45 dB), in ms.
The settings are read from the real @Resources/Settings.inc (read-only)."""
import argparse
import os
import re
import statistics
import sys
import time
import wave

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
OPEN_MS = 123          # measured: MME stream open + first write, median over 12 opens (tasks/jarvis-voice-plan-2026-11-03.md)
SIL_DB = -45.0


def fake_stream(text):
    """The model streaming the reply: a word and its space at a time."""
    for w in re.findall(r"\S+\s*", text):
        yield w


def words(t):
    return len(t.split())


def kind_of(prev_text):
    t = prev_text.rstrip()
    return "sentence" if re.search(r"[.!?][\"')]*$", t) else "clause" if re.search(r"[,;:—–-]$", t) else "mid"


def sil_ms(a, rate, end):
    """Near-silence at the start (end=False) or end (end=True) of a clip, in ms."""
    import numpy as np
    thr = 10 ** (SIL_DB / 20)
    idx = np.nonzero(np.abs(a) > thr)[0]
    if idx.size == 0:
        return len(a) * 1000.0 / rate
    n = (len(a) - 1 - idx[-1]) if end else idx[0]
    return n * 1000.0 / rate


def load_cases(path):
    with open(path, encoding="utf-8") as f:
        return [l.strip() for l in f if l.strip() and not l.startswith("#")]


def old_chunks(speech, text):
    return [c.strip() for c in speech.sentences_from(fake_stream(text), []) if c.strip()]


def new_chunks(speech, text):
    pieces = [c.strip() for c in speech.sentences_from(fake_stream(text), []) if c.strip()]
    return speech.plan_chunks(pieces)


def with_smooth(speech, flag):
    """Switch JarvisVoiceSmooth for this process (speech and player both read it through their own `setting`)."""
    from jarvislib import player
    real = (speech.setting, player.setting)
    fake = lambda n, d="": ("1" if flag else "0") if n == "JarvisVoiceSmooth" else real[0](n, d)
    speech.setting = player.setting = fake
    return real


def restore(speech, real):
    from jarvislib import player
    speech.setting, player.setting = real


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cases", default=os.path.join(HERE, "voice_cases.txt"))
    ap.add_argument("--no-synth", action="store_true", help="chunk statistics only")
    ap.add_argument("--out", default="", help="folder for the old/new WAVs")
    ap.add_argument("--wav", type=int, default=6, help="how many cases get WAVs")
    args = ap.parse_args()
    sys.argv[1:] = []                                   # jarvislib reads RES from argv[1]: none = the skin's @Resources
    from jarvislib import speech, tts
    cases = load_cases(args.cases)
    has_new = hasattr(speech, "plan_chunks")
    synth_cache = {}

    def clip(text):
        if text not in synth_cache:
            t0 = time.time()
            synth_cache[text] = tts.synth_audio(speech.speakable(re.sub(r"[*_#`>\[\]]", "", text).strip())) + (time.time() - t0,)
        return synth_cache[text]

    if not args.no_synth:
        clip("Warm up.")
        print(f"voice device: {tts._voice_dev[0] if hasattr(tts, '_voice_dev') else '?'}")
    report = {}
    for label in ("old", "new"):
        if label == "new" and not has_new:
            continue
        real = with_smooth(speech, label == "new")
        rows = []
        try:
            for ci, text in enumerate(cases):
                ch = (new_chunks if label == "new" else old_chunks)(speech, text)
                rows.append((text, ch))
        finally:
            restore(speech, real)
        seams, orph, nchunk, firstw, total, wavs = [], 0, 0, [], 0.0, []
        for ci, (text, ch) in enumerate(rows):
            nchunk += len(ch)
            firstw.append(words(ch[0]) if ch else 0)
            orph += sum(1 for c in ch[1:] if words(c) < 6)
            if args.no_synth:
                for a, b in zip(ch, ch[1:]):
                    seams.append((kind_of(a), None))
                continue
            import numpy as np
            parts = []
            for k, c in enumerate(ch):
                a, rate, st = clip(c)
                if label == "new":
                    from jarvislib import player
                    a = player.prepare(a, rate)
                    lead = 0 if k == 0 else player.pause_ms(player.boundary(ch[k - 1]))
                else:
                    lead = 0 if k == 0 else OPEN_MS
                if k:
                    prev = parts[-1][0]
                    gap = lead + (sil_ms(prev, rate, True) + sil_ms(a, rate, False))
                    seams.append((kind_of(ch[k - 1]), gap))
                parts.append((a, lead, rate))
            if ci < args.wav and args.out:
                rate = parts[0][2]
                wav = np.concatenate([np.concatenate([np.zeros(int(rate * l / 1000), np.float32), a]) for a, l, _ in parts])
                os.makedirs(args.out, exist_ok=True)
                p = os.path.join(args.out, f"{ci:02d}_{label}.wav")
                with wave.open(p, "wb") as wf:
                    wf.setnchannels(1), wf.setsampwidth(2), wf.setframerate(rate)
                    wf.writeframes((np.clip(wav, -1, 1) * 32767).astype("<i2").tobytes())
                wavs.append(p)
            total += sum(len(a) / r for a, _, r in parts)
        report[label] = (rows, seams, orph, nchunk, firstw, total)
    for label, (rows, seams, orph, nchunk, firstw, total) in report.items():
        print(f"\n== {label}: {len(rows)} replies, {nchunk} chunks, {len(seams)} seams, {orph} later chunks under 6 words, "
              f"first chunk {statistics.mean(firstw):.1f} words on average (min {min(firstw)}, max {max(firstw)})")
        for kind in ("mid", "clause", "sentence"):
            g = [s for k, s in seams if k == kind and s is not None]
            n = sum(1 for k, _ in seams if k == kind)
            if g:
                print(f"   {kind:8s} seams {n:3d}: silence median {statistics.median(g):5.0f} ms, mean {statistics.mean(g):5.0f}, max {max(g):5.0f}")
            else:
                print(f"   {kind:8s} seams {n:3d}")
        if not args.no_synth:
            print(f"   audio length {total:.1f} s")
    if args.no_synth or not report:
        return
    for label, (rows, *_rest) in report.items():
        if label == "old":
            print("\nchunks (old):")
            for text, ch in rows[:12]:
                print("  " + " | ".join(ch))
    if "new" in report:
        print("\nchunks (new):")
        for text, ch in report["new"][0][:12]:
            print("  " + " | ".join(ch))


if __name__ == "__main__":
    main()
