Jarvis\wake\  -  custom wake-word models (Phase 10B, W2)

What goes here: ONE .onnx file per wake phrase you trained yourself, e.g. hey_clover.onnx.
Nothing is shipped in this folder. "Hey Jarvis" needs no file (openWakeWord downloads its own model).

How the file is made (once, OFF this PC; nothing is installed in the HUD's Python):
  1. openWakeWord trains a new phrase from 100 percent synthetic (text-to-speech) speech. Use the project's own
     training notebook (openWakeWord repo, "automatic_model_training") in Colab or a throw-away folder. The official
     notebook can break on the default Colab runtime; the plan (JARVIS-Repair-Plan.txt, S2-4) notes a patched copy.
  2. Target phrase: "hey clover". Export the model as ONNX (not tflite: the HUD loads only ONNX).
  3. Copy the file to this folder under the name hey_clover.onnx.
  4. Control Center > CLOVER: set JarvisWakeModel to hey_clover.onnx (Settings.inc: JarvisWakeModel=hey_clover.onnx).
     No restart is needed: the wake loop loads the new model by itself within a second. The log says
     "wake word ready - say 'Hey Clover'". A file that will not load, or is missing, falls back to Hey Jarvis (logged once).

Rules:
  - Only load a model file you made or trust. A model from someone else is never loaded.
  - Keep Hey Jarvis as the fallback until the new phrase passes both checks below.

Acceptance (the plan's B1 and B2, done by hand, results into the plan):
  B1  Say "Hey Clover" 10 times, normal voice and distance. At least 9 must wake him.
  B2  Five minutes of TV or room talk with the HUD listening. Zero wakes. The log shows every wake as
      "wake word heard (score, way)" and, once a minute, "wake: best <score> this minute".
If the model scores too low or wakes too easily, adjust Control Center > WAKE WORD > EASIER / STRICTER (JarvisWakeSensitivity).
Your own voice check (Control Center > WAKE TRAINING) can be trained afterwards; it only filters, it never wakes him alone.
