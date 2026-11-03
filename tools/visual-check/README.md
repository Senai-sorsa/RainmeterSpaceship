# Visual check scripts (screenshots and CPU for the CSpace HUD preview)

Used during the 2026-11-02 visual overhaul. Plain Node + the UI's own Playwright; nothing here touches the system.
Start the dev server first, on its own port so it does not clash with the e2e server (5173):

    cd SpaceshipApp/SpaceshipUI && npx vite --port 5199 --strictPort

Run the scripts from this folder (they load Playwright from `SpaceshipApp/SpaceshipUI/node_modules` by absolute path)
and write PNGs where you point them (use a scratch folder, not the repo).

| Script | What it does |
|---|---|
| `proto.cjs <out.png> '<json config>' [url] [w h dpr] [x y w h]` | One screenshot, optional crop. Config overrides settings through the mock host (e.g. `'{"FontText":"Rajdhani"}'`). Default view 1707x1067 @1.5 = a 2560x1600 screen at 150 %. Marks the session booted (no boot sequence). |
| `bootat.cjs <out.png> <frame>` | The boot sequence held on one frame (`?bootat=`), without the booted flag. |
| `sweep.cjs <outdir>` | Every page and pop-up: wizard 1-4, Control Center x8 + advanced, search, help sheet, row tip, notices, kit/demo pages, log. |
| `sheet.cjs <out.png> <cols> <cellW> <cellH> <img...>` | A labelled contact sheet (cheap to look at: one image instead of many). |
| `crop.cjs <in> <out> x y w h`, `pair.cjs <a> <b> <out>` | Crop a PNG; two PNGs side by side. |
| `burst.cjs <prefix>` | Four audio-ring frames 150 ms apart with `?audio=demo` (checks the ring moves). |
| `hold.cjs [css]` + `cpu.ps1 15` | Hold the HUD open 26 s (optionally inject CSS, e.g. `.bloom{filter:none!important}`), and measure the headless browser's CPU over 15 s. Run hold in the background, wait ~7 s, then cpu.ps1. |
| `spec.cjs` | JS mirror of `ShipCore.Core/SpectrumBands.cs`, to check the C# test expectations when Smart App Control blocks `dotnet test`. |

Preview switches (plain browser only, ignored in WebView2): `?preview=1&module=all`, `?jarvis=<state>`,
`?jarvislog=demo`, `?drawer=1|<folder>`, `?bootat=<frame>`, `?audio=demo`, `?notices=demo`, `?panel=control|kit|demo`,
`?level=advanced`, `?debug=1`.

Token note: images stay in the conversation and are re-read on every later request. Prefer crops and contact sheets
(`sheet.cjs`) over full-frame screenshots.
