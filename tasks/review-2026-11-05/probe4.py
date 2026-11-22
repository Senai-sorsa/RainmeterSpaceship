import os, sys, time
JD = sys.argv[1]; sys.path.insert(0, os.path.join(JD, "tools")); sys.argv[1:] = []
import golden_common as G
with G.Box() as b:
    J = b.jarvis; j = b.j
    from jarvislib import routing as R
    # 1. negation through the AI-reread gate
    for t in ["Please do not lower the volume.", "Don't set a timer.", "do not mute", "never turn the volume down", "please don't lock the pc", "I said don't mute",
              "Please set the volume to 30.", "stop lowering the volume", "no don't open chrome"]:
        b.reset(); r = R.route(t)
        print(f"ask_ai({t!r}) route={r[0]} -> {R.ask_ai(t, r)}")
    # 2. crisis line when Ollama is down / model missing
    said, probs = [], []
    j.reply_line = lambda text, quiet: said.append(text)
    j.problem = lambda msg, popup=True: probs.append(msg)
    j.ensure_ollama = lambda: False
    b.reset()
    J.turn(0, typed="I want to kill myself.")
    while J.busy.locked(): time.sleep(0.05)
    print("OLLAMA DOWN, crisis typed -> said:", said, "| problems:", probs)
    del said[:], probs[:]
    j.ensure_ollama = lambda: True
    j.pick_model = lambda tier: ""
    b.reset()
    J.turn(0, typed="I want to kill myself.")
    while J.busy.locked(): time.sleep(0.05)
    print("MODEL MISSING, crisis typed -> said:", said, "| problems:", probs)
    print("tripwires:", len(G.SL.TRIPS))
