# CSpace review snapshot

Only the code that runs CSpace (the desktop HUD) and the JARVIS assistant, copied from the working tree of
branch fix/sol-review. Rainmeter skins, .lua scripts, plans, logs, docs and build output are left out on purpose.

- `SpaceshipApp/ShipCore.App`: Windows host (C#, WinForms + WebView2): window, visibility, tray, JARVIS supervisor.
- `SpaceshipApp/ShipCore.Core`: host logic, protocol, settings, action gate (unit tested in `ShipCore.Core.Tests`).
- `SpaceshipApp/SpaceshipUI`: the HUD page (Preact + Vite, tests in `tests/` with vitest, `e2e/` with Playwright).
- `contract/`: message and settings contract shared by host and UI.
- `Skins/Spaceship/@Resources/Jarvis`: JARVIS (Python: Ollama LLM, Whisper STT, openWakeWord). Entry `jarvis.py`,
  logic in `jarvislib/`, tests `test_jarvis.py` and `tests/`, golden route/reply tables in `tests/golden/`.
- `Skins/Spaceship/@Resources/{Images,Fonts,Sounds,Scripts/*.ps1,*.inc,Apps.ini}`: assets and settings the host reads.

Wake model weights (*.onnx) are not included.
