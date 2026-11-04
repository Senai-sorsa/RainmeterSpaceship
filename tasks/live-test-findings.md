# Live test findings (UI and settings only; started 2026-11-03)

Status key: DONE = changed and checked, NOTE = logged, fix later (user asked to note first).

## From the user (live, in the real app)
| # | Finding | Status |
|---|---|---|
| U1 | Picture frame (`UseShipImage=1`) is not the right size, and should get filters and effects so it looks cooler. User suspects zoom/DPI settings on their PC. | NOTE. Checked: display is 1707x1067 logical at 150 %, `Scale=0.67`, `AutoFit=0`, `HomeSize=2560x1600`. Frame box = `min(100vw,160vh)*Scale/fit`, so it assumes a 16:10 viewport. Still to verify at other DPI/zoom/aspect. |
| U2 | Transparent backgrounds on the chrome and other parts look odd: remove them. | NOTE |
| U3 | The cockpit looks like lines, not a curved surface (example: below the JARVIS part). Wants full redesigns of such features. | NOTE |
| U4 | Find more ways to match the MAIN reference image more closely. Free range on UI changes, but only what makes it look cooler, not arbitrary moves/reshapes of objects. | NOTE |
| U5 | Targeter moves too fast and drifts oddly. | DONE in `src/modules/target.ts`: hop time `max(3.5, min(8, dist/90))` (was `dist/220`, 1.4-3.2 s), dwell 2 s (was 1 s), spin 0.9 deg/tick (was 1.6). `tests/centerFrames.test.ts` 9/9. Not yet seen live. |
| U6 | Control Center and other parts look very basic. They should look as good as the CARGO panel. | NOTE |
| U7 | CARGO panel is too transparent and slightly too bright. | NOTE |
| U9 | With two panels open at once (e.g. CARGO drawer and Control Center), sometimes NEITHER can be clicked, even when one is stacked over the other. Needs tests: two-overlay stacking, hit-region ownership and z-order, close/reopen order, focus; plus random logic/error cases (rapid open/close, host message errors, bad config values) added to the live test suite. | NOTE. Suspect area: `src/host/hitRegions.ts` (click-through regions sent to the host) vs overlay stacking. Not yet reproduced. |
| U8 | Do not pop up windows on the user's PC during tests. | DONE: `tools/live-test/sweep.cjs` is headless unless `VISIBLE=1`. |

## Tool bugs found while building the test tool
- The mock host drops any config value that is not a string. `proto.cjs` callers that passed numbers (`{"HullRender":1}`) got no change, so earlier `hr0` vs `hr1` screenshots were identical. `sweep.cjs` now stringifies.
- `browser.process()` does not exist in this Playwright version; the tool now spawns Chrome itself.

## Measurements
- Live app (CSpace, idle, 20 s, read-only): about 4.2 % of the whole 20-core CPU, renderer GPU 3D about 5.4 %, RAM about 1.27 GB (renderer 704 MB).
- Sweep: see `sweep3/results.md` in the scratchpad (headless GPU Chrome, strings fixed).

## U10: CSpace must follow Windows display settings (post-live change; NOT fixed yet)
User: "make sure the system takes the Windows settings and adjusts CSpace to them, so if I change settings later, CSpace changes with it and everything still looks right."

**Audit (confirmed by reading code, not yet reproduced live)**
- Host re-homes on `WM_DISPLAYCHANGE` / `WM_DPICHANGED` (`Program.cs` `Rehome`) and the page refits on `resize` (`Hud.tsx`). Good.
- **GAP 1 (confirmed in code):** `Hud.tsx:114` sets `Scale = Scale / fit`. That keeps the HUD the same size in logical px, so it fills the screen only at 150 % (fit about 0.667 gives 1.005). At 125 % the frame box is about 0.84 of the window; at 100 % about 0.67. A change of Windows display scale shrinks the HUD off the screen. The same expression also drives line widths and glow radius.
- **GAP 2:** `HomeScreen` picks the display by an exact `HomeSize` match (default 2560x1600, a manual setting). After a resolution change nothing matches, so it falls back to the primary display silently. `HomeSize` is never updated.
- **GAP 3:** the frame box assumes 16:10 (`min(100vw,160vh)`), so on other aspect ratios (ultrawide, 16:9, 3:2) the frame art is letterboxed or cropped. This may be the picture-frame size complaint (U1).
- **Not checked yet:** Windows text-size, dark/light mode, animation-effects off (should map to ReduceMotion), battery/power mode, monitor hot-plug while running, taskbar size or position change (`WM_SETTINGCHANGE`), WebView2 zoom.

**Planned change (after live):** treat `Scale=0.67` as "fills the screen" at the reference design, and derive the real size from the viewport (aspect-aware), so DPI, resolution and zoom changes keep the fill. Add an auto home-display choice (the display the HUD was last on, or the primary, instead of requiring a size match). Follow Windows animation/dark-mode settings where a matching setting exists.

**Tests to add**
- Frame fills the viewport (box within 1 px of the window) at: 1280x800@1, 1707x1067@1.5, 2048x1280@1.25, 2560x1600@1, 3840x2160@1.5, and non-16:10: 1920x1080, 3440x1440, 1600x1200.
- Glow registration (A8): glow sits on its line, offset at most 1 px, at the same sizes.
- Live resize in one session (viewport change event) refits the HUD without a reload; zoom 80 to 200 % in steps.
- `HomeScreen` / `PickHomeDisplay` unit tests: size match, no match, two monitors, monitor removed, resolution changed.
- Hit regions follow a resize (links to U9).
- Picture frame vs rendered frame fill the same box at each size (U1).

## U11 (post-live): add tests for random logic and error cases
Rapid open/close of panels, host message errors, bad config values, two overlays open at once (U9), settings changed mid-animation, tier changed while a panel is open.

## U12 (post-live): better fonts for the Control Center and setup wizard (NOT changed yet)
User: some fonts do not look good, and they feel like the ones Claude reaches for by default (mainly in the Control Center and setup); find better replacements.
- Fonts in use now (from `src/*.css`): Oxanium (4 rules), Rajdhani (3, also the `FontText` default), B612 Mono (title default `FontTitle`), Share Tech Mono, Orbitron, Michroma. Files live in `Skins/Spaceship/@Resources/Fonts/`; the Rainmeter skin uses the same files, so a swap in CSpace only must not change the skin.
- Plan: find which rules apply to the Control Center, wizard and pop-ups; pick 2 to 3 candidate pairings (a display face for titles, a clean readable face for settings rows, a mono for values); render the Control Center and wizard in each; the user picks. Must stay legible at the dim colour (contrast check, A9/C2) and at 100 % and 150 % scale. Licence: only open-licence fonts (OFL), bundled as local files (no network fetch).
- Test: every panel renders without a fallback font (check `document.fonts`), no layout overflow at 1280x800, hint tooltips still fit two lines.

## Sweep 1 results (headless GPU Chrome on the preview, 1 run per case, 8 s each; table in `tasks/live-test-sweep1-results.md`)
Caveats: ONE run per case; the machine noise is about +-15 points of one core; this is Chrome on the dev preview, not WebView2. Only differences well above the noise count.
- **Real:** tier LITE is about -60 CPU points (-33 %) and -0.9 GPU points vs FULL. `HullRender=1` costs about +550 MB RAM (2447 vs 1893 MB). Frame none saves about 500 MB. Music costs about +15 CPU.
- **No measurable cost** (inside the noise, under 7 points CPU and 0.3 GPU): `LensFx`, `DepthHaze`, `ScreenBezel`, `StateLight`, `ReduceMotion`, `FrameBrightness`, picture frame, `HullRender` CPU. So no "slight look, high cost" effect was found among the new layers. Removing them would not buy CPU or GPU.
- **Surprise, needs a repeat:** `BloomEngine=svg` measured about 46 points LOWER CPU than the canvas engine (and 0.5 GPU lower). This contradicts the design claim. One run could be noise or a first-run effect; repeat 3 interleaved rounds before acting.
- **Harmless:** every case logs one 404, which is `favicon.ico` on the dev server.
- **Tool defect:** the layer list showed the `frame=none` case still has 1 layer; fine. Per-case `msgs` only keeps the console text, not the URL. Fix when the tool is next edited.
- **Not measured:** the real WebView2 HUD under settings changes (it needs a HUD reload per change); live GPU/VRAM per setting.

## U13 (future improvement, NOT started): clean up the picture-frame art (`ship.png`, Picture mode)
User: the picture version of the frame was AI-generated and looks cool, but needs smoother edges and image editing to remove odd parts. Find ways to do this automatically with existing tools. Only record it for now.
- Where: `Skins/Spaceship/@Resources/Images/ship.png` (2560x1600), used by `FrameLayers.tsx` when `UseShipImage=1`; the Rainmeter skin may also use it, so keep the original and write the cleaned file to a new name (`ShipImage` setting already names the file).
- Candidate approaches to evaluate (none tried yet; check availability and licence first):
  1. **Edge and mask clean-up in Python (numpy + Pillow or OpenCV):** alpha-matte erode/blur of 1 to 2 px, defringe (remove light or dark halo by colour decontamination), anti-aliased re-threshold of the window cut-out against `window_mask.png`. No model, deterministic, can run in `tools/`.
  2. **Upscale / denoise with an existing model:** Real-ESRGAN or similar (local, offline) to remove AI artefacts and smooth edges; OpenCV `fastNlMeansDenoising` as a cheap alternative.
  3. **Remove odd parts:** inpainting (OpenCV `inpaint`, or LaMa / a local diffusion inpaint) over a mask of the flagged regions; the regions are marked by the user in a crop sheet first.
  4. **Blender:** the project already renders the hull in Blender (`tools/blender/`); a rendered shell may replace the AI picture entirely (`HullRender`), so decide whether to polish the picture or only offer it as the "AI art" style.
  5. **Runtime filters (no file edit):** CSS/canvas treatments on the picture layer (soft edge mask, vignette, bloom, colour grade, grain) as asked in U1.
- Plan: (a) list the odd parts together with the user on a crop sheet; (b) try 1 and 5 first (cheap, reversible); (c) only then models (2, 3); (d) compare before/after crops; keep the originals untouched; the clean-up script lives in `tools/` with a test that checks size, alpha IoU against the original silhouette, and no clipped pixels.
