"""A/B files to LISTEN to (S3, V12): the same three replies in several speeds and voices, each assembled the smooth way
(chunks, trim, fade, chosen pauses). Nothing is played; WAVs are written.
    python -B tools/voice_ab.py --out DIR [--speeds 0.92,0.96,1.0] [--voices bm_lewis,bm_george,bm_fable,bm_daniel,default]
File names: <voice>_<speed>_<n>.wav. Your pick -> JarvisKokoroVoice / JarvisVoiceSpeed in Settings."""
import argparse
import os
import sys
import wave

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
LINES = ["Good morning, sir. You have three meetings today, and the first is at nine.",
         "It is quite late, sir, and you have an early class tomorrow, so I would suggest getting some rest.",
         "Disk usage is at 91 percent. I would clear something soon."]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--speeds", default="0.92,0.96,1.0")
    ap.add_argument("--voices", default="bm_lewis,bm_george,bm_fable,bm_daniel,default")
    a = ap.parse_args()
    sys.argv[1:] = []
    import numpy as np
    from jarvislib import player, speech, tts
    os.makedirs(a.out, exist_ok=True)
    cur = {}
    real = tts.setting
    tts.setting = lambda n, d="": cur.get(n, real(n, d))
    for voice in a.voices.split(","):
        for speed in a.speeds.split(","):
            cur.update(JarvisKokoroVoice=voice, JarvisVoiceSpeed=speed)
            for i, line in enumerate(LINES):
                pieces = list(speech.smooth_sentences_from(iter([line]), []))
                parts, prev = [], ""
                for c in speech.plan_chunks(pieces):
                    x, rate = tts.synth_audio(speech.speakable(c))
                    lead = int(rate * player.pause_ms(player.boundary(prev)) / 1000) if prev else 0
                    parts += [np.zeros(lead, np.float32), player.prepare(x, rate)]
                    prev = c
                wav = np.concatenate(parts)
                p = os.path.join(a.out, f"{voice}_{speed}_{i + 1}.wav")
                with wave.open(p, "wb") as wf:
                    wf.setnchannels(1), wf.setsampwidth(2), wf.setframerate(rate)
                    wf.writeframes((np.clip(wav, -1, 1) * 32767).astype("<i2").tobytes())
            print("wrote", voice, speed, flush=True)


if __name__ == "__main__":
    main()
