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
| U9 | With two panels open at once (e.g. CARGO drawer and Control Center), sometimes NEITHER can be clicked, even when one is stacked over the other. Needs tests: two-overlay stacking, hit-region ownership and z-order, close/reopen order, focus; plus random logic/error cases (rapid open/close, host message errors, bad config values) added to the live test suite. | DONE (part 2). Root cause confirmed: `regionsOf` capped at 64 in DOM order; base HUD = 56 regions, +CARGO drawer = 69, so the last (topmost) overlay lost regions. Fix: drop boxes inside another box, keep the LAST 64. 3 new tests in `tests/hitRegions.test.ts`. Not yet seen live in the real app; the real two-window case (Control Center is its own WebView) is still to check. |
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

## Part 3 (2026-11-03): brightness, and what the look-again pass found
- **U14 DONE:** everything was too bright against the MAIN reference (dark, desaturated, a few lit focal points). `ui.css`: `#hud` opacity 0.82 and `.bloom-layer` opacity 0.6. Checked side by side on the preview; unit 453/453, bloom and hud e2e 21/21. Tune the two numbers if it is still too bright or now too dim.
- **U1 detail (picture frame), seen in the preview at 1707x1067:** the frame fills the window correctly, but the HUD modules are laid out for the rendered hull, not the picture: the top graphs (CPU, GPU, NET, MEM) collide with the picture's top crossbar and bracket, the app rows run over the left and right struts, and the picture's blue lamps do not line up with the HUD. So "not the right size" is probably module-to-picture misregistration, not the frame box. Still need what the user sees on their real screen; the live HUD could not be seen (hidden behind open windows).
- Not yet re-checked after the dim: Control Center look (U6), CARGO (U7).
- **U7 DONE (part 4):** `src/draw/popup.ts` `popupFrame` (shared by CARGO, JARVIS log and the boot check): body fill 215 to 250 of 255 (HUD no longer shows through), header and top light about -25 %, outer glow 60 to 42, frame and bracket strokes about -20 %. Looked at on the preview.
- **U12 note:** the CARGO title "CARGO HOLD" rendered in a serif-looking face in the preview (`fontTitle` = B612 Mono by default), so a font may be falling back; check `document.fonts` when doing U12.
- **U10 gap 1 DONE (part 5):** `Hud.tsx` now uses `Scale / DESIGN_FIT` (2/3), not `Scale / fit`. Reproduced first with the new `e2e/display-fit.spec.ts`: 6 of 8 sizes failed (2560x1600: frame 1715 px, wanted 2560; 1280x800 overhung by 435 px); after the fix 8/8 pass (1280x800, 1707x1067, 2048x1280, 2560x1600, 1920x1080, 3440x1440, 1600x1200, and a live resize). Full run: unit 453/453, e2e 75/76; the one failure was `bloom.spec` "idle light is not re-blurred" under full-suite load, 3/3 passing alone (watch it; the handoff calls a real failure a regression of `fb9eeda`). Not yet seen in the real app.
- **U10 gaps 2 and 3 still open:** automatic home-display choice (`HomeScreen` exact `HomeSize` match) and other aspect ratios (frame letterboxed in a 16:10 box; the new test only checks the box, not module registration).
- **U2 DONE (part 6):** the two pinned-app rows (Google Chrome, Everything) no longer draw the translucent plate (`src/modules/slot.ts`, `if (isCat)` around the plate fill and texture); category rows keep theirs. Looked at on the preview. If the user meant ALL rows, remove the same two lines' condition.
- **U3 / U4 (curved, realism, distortion):** assessed, not done. `HullRender=1` (Blender hull) looks WORSE than the default against the main reference (smooth grey fog, blown-out cyan light blobs), so flipping the default is not the answer. A real fix is a Blender scene rework (hull detail, dark metal, a wide-angle lens) plus bending the HUD zones to the same lens (`curve.json` zones). That is a multi-session project; see the plan in the chat.
- **U6 first pass DONE (part 7):** Control Center and wizard restyled with one appended CSS block at the end of `src/ui/ui.css` ("Control Center finish v2", delete it to revert): solid lit glass (no more see-through `backdrop-filter: blur`, which was also a full-window GPU cost), lit section headers with an accent bar, row banding and a lit hover bar, lit switches, input focus glow, lit active nav strip. e2e control-center, settings-panel, wizard 30/30. Looked at on the preview. Still plain compared to CARGO: the toggles read as grey squares, the pop-ups other than CARGO are untouched, and the fonts (U12) are next.
- **U10 gaps 2 and 3 DONE (part 8):**
  - Gap 2: `HostRules.PickHomeDisplayNearest` (exact `HomeSize` match first, else closest aspect within 2 %, then nearest pixel count), used by `Program.HomeScreen`. 3 new tests; `dotnet test` 311/311; `ShipCore.App` builds (0 errors). Not run in the live app (it needs a rebuild and restart of CSpace; not done).
  - Gap 3: the modules (svg) and the frame share one area at 16:9, 21:9 (3440x1440), 4:3 and 150 % (4 new e2e tests, `e2e/display-fit.spec.ts` now 12/12). On a non-16:10 window the HUD is a centred 16:10 area with the desktop visible beside it by design; nothing is stretched. If the user wants the hull to extend to fill ultrawide screens, that is a new feature.
  - Still not covered: Windows text-size, dark mode, animation-effects-off mapping, taskbar changes (`WM_SETTINGCHANGE`), monitor hot-plug while running.

## Part 9: bug check (2026-11-03)
- **Regression caught and fixed:** the bloom test "idle light is not re-blurred" failed 10/10 under load (`--repeat-each=10 --workers=10`) on my branch and passed 10/10 on unchanged UI. Bisected: the two stacked full-window CSS opacity layers (`#hud` 0.82 and `.bloom-layer` 0.6) together caused it; either alone passed. Fix: the glow trim is now `LIGHT_TRIM = 0.6` applied with `globalAlpha` inside the light canvas draw (`BloomLayer.tsx`), no compositing layer; `#hud { opacity: .82 }` stays. 10/10 under load after the fix. Lesson: a full-window `opacity` is a real cost in software rendering; see the CPU/GPU review.
- **U9 / U11 tests added:** `e2e/robustness.spec.ts` (17 garbage-config cases, e.g. `Scale` 'abc' or '1e9', a bad `PerfOverride`, `ShipImage` '../../etc/passwd', `UseShipImage` and `FrameOff` both on; rapid CARGO clicking with a resize) all pass; no page error, HUD still draws.
- **Gates on `fix/live-test`:** `tsc` clean; vitest 453/453; `vite build` ok; Playwright 98/98; `dotnet test` 311/311; the 4 Python tool checks exit 0.
- **Not covered:** anything that needs the real WebView2 or Windows (the Control Center is its own window in the real app; the real two-panel click case; text size, dark mode, animation settings, taskbar change, monitor hot-plug).

## Part 10: CPU / GPU review (2026-11-03). Evidence grade is stated for every item.
Repeat sweep (`tools/live-test/sweep.cjs`, 3 interleaved rounds, medians, headless GPU Chrome on the preview, branch tip):
| case | CPU % of 1 core (3 runs, median) | GPU 3D % (median) | RAM MB (median) |
|---|---|---|---|
| base FULL idle | 159 / 144 / 158 (158) | 4.06 | 2217 |
| base FULL music | 171 / 168 / 137 (168) | 4.83 | 2237 |
| BloomEngine=svg | 164 / 163 / 178 (164) | 1.48 | 2119 |
| LensFx+Haze+Bezel+Light all 0 | 153 / 159 / 161 (159) | 3.68 | 2206 |
| frame=none | 154 / 152 / 148 (152) | 3.59 | 1451 |
| tier LITE | 190 / 178 / 191 (190) | 4.49 | 2106 |

**What the data supports**
1. **CPU numbers from this method are not usable for small or medium differences.** Run-to-run spread is about 15 to 35 points, and sweep 1 vs sweep 2 disagree on LITE (-60 then +32) and on `BloomEngine=svg` (-46 then +6). Conclusion: do not choose CPU optimisations from headless numbers. The real WebView2 HUD must be measured (needs the user's OK to reload CSpace per setting; the read-only sampler `tools/live-test/sample.ps1` already works on `CSpace.exe`).
2. **Effects are cheap (confirmed twice):** glass/lens, depth haze, screen bezels and orb light together change nothing measurable (159 vs 158 CPU; 3.7 vs 4.1 GPU). Removing them saves nothing, so keep them. No "slight look, high cost" effect was found among the new layers.
3. **Memory is the one clear cost (consistent in both sweeps):** frame art is about 0.5 to 0.75 GB of RAM (`frame=none` 1451 vs 2217 MB; `HullRender=1` +550 MB). That is the largest saving available.
4. **`BloomEngine=svg` shows lower GPU 3D in both sweeps (1.15 and 1.48 vs 1.65 and 4.06).** It contradicts "canvas is easier on the GPU", BUT the preview is nearly static, which favours SVG blur (cached while nothing changes). Needs a test with live-changing data and the real GPU before any change.

**Recommendations, least visual loss first**
- A. (RAM, no visible change) Pre-composite the static frame layers offline (hull + corners + shade, and the other fixed ones) into one or two images, so fewer 2560x1600 bitmaps are decoded. Expect a few hundred MB back. Evidence: item 3. Verify by looking at `frame=none` vs the new frame and the RAM sample.
- B. (GPU/CPU, no visible change) Replace full-window opacity (`#hud { opacity: .82 }`, the dimming) by baking the dim into the colour constants (text/line alphas). Evidence: the bisect in part 9 (two stacked opacity layers broke a timing test under load). Low risk, but a real saving is unmeasured.
- C. (done) The Control Center and wizard no longer use `backdrop-filter: blur` (a full-window blur while open).
- D. (CPU, tiny loss) The centre module re-renders the whole target + sphere zone at about 16 fps via `setTick`; at FULL, drop the target to about 10 fps (its motion is slow now) and keep the sphere at 16. Evidence: code inventory only (not measured).
- E. (CPU, no visible change) Hit regions are polled every 250 ms with layout reads; drive them from a ResizeObserver or MutationObserver instead. Evidence: code inventory only; likely tiny.
- F. (decision, not a pure win) `HullRender=1` costs +550 MB and looks worse than the current hull; leave the default at 0.
- G. (measure first) A repeat of the BloomEngine test with live data, and a live GPU/VRAM baseline with `tools/gpu_baseline.ps1` once the GPU is quiet.

## Part 11: recommendations B, D(not yet), E(not yet) and the Blender hull removal (2026-11-03)
- **User decision:** delete the unnecessary Blender hull. Removed `HullRender` and everything only it used: the setting (`registry.ts`, `Settings.inc`, `contract/config-keys.json`), the 6 images in `Skins/Spaceship/@Resources/Images/Render/`, `tools/blender/cockpit_scene.py`, `tools/test_render_frame.py`, the `RENDER_IMAGES` wiring in `tools/export_ui_assets.py`, the render/light-pass code and `OrbPass` in `FrameLayers.tsx`, the `curve` hookup in `style.ts`, and the tests/sweep cases for it. Frame art in `src/generated/frame/` is now 7.5 MB. **Revert with `git revert <this commit>`.**
- **Left in place, dormant:** `src/draw/curve.ts`, the `Canvas` zone-bend hook, `tools/frame_src/curve.json` (no setting turns them on now; a future curve project can reuse them). The user's `settings.json` still has a `HullRender` key; the host only serves keys in the schema, so it is ignored (checked in `SettingsStore`).
- **B DONE:** the dim is baked in. `HUD_TRIM = 0.85` multiplies `hudA` in `modules/style.ts` (every op's alpha), and the glow uses `LIGHT_TRIM = 0.6` in `BloomLayer.tsx`. No full-window opacity layer is left (`#hud { opacity }` removed). `tests/ops.test.ts` expects `hudA` 217.
- **Test hardening:** the bloom test "idle light is not re-blurred" waits for `document.fonts.ready` first. When it failed, all four timer-driven tiles rebuilt at once (a global event, consistent with a late font reflow under load). Under 10 parallel copies: before 10/0/6 of 10 on this branch (and 9/10/7 on unchanged `main`, so it was load-sensitive there too), after 9/10/10/10. One occasional miss remains under that artificial load; the normal full suite passed.
- **Gates:** `tsc` clean, vitest 451/451 (2 curve gate tests removed with the setting), Playwright 94/94, `dotnet test` 311/311, `export --check` ok, Python tool checks ok (`test_export_ui_assets.py` fixed for the removed `RENDER_IMAGES`), `vite build` ok.
- **Still to do from the list:** D (lower the targeter's redraw rate at FULL) and E (hit regions driven by observers instead of the 250 ms poll), then A (pre-composite static frame layers; evidence: the frame costs about 0.5 to 0.75 GB of RAM).

## Part 12: where does the frame's RAM go? (experiment, 2 rounds, 6 s each)
Hiding layers with CSS after load does NOT free memory: base 2249/2222 MB, all frame layers `display:none` 2279/2247, css-gradient layers hidden 2264/2265, hull+corners+shade hidden 2267/2270, glass_fx+scan+mist hidden 2314/2176. (Browsers keep decoded images; GPU 3D % also stayed 2.7 to 3.6 and CPU noise stayed +-15.) So this method cannot localise the cost; the only measurement that moved RAM is not rendering the frame at all (`frame=none`, about -500 to -770 MB in two sweeps).
- **Reading:** the frame images are about 110 MB raw (7 images of 15.6 MB) but the saving is 5 to 7 times that, so each image costs several copies (decoded, GPU texture, layer, mask). That makes fewer or smaller images the lever (recommendation A), roughly 150 to 200 MB for merging hull + corners + shade, which is an ESTIMATE, not measured.
- **Not done, on purpose:** A (merge frame images), D (target redraw rate) and E (observer-driven hit regions). A would change the frame's brightness maths and needs a before/after RAM measurement in the real app; D and E have no evidence of benefit (the hit-region poll costs nothing when layout is clean; the target and sphere share one timer, so slowing only the target needs a timer split). Revisit after a live WebView2 measurement.

## Part 13: merged and deployed (2026-11-03, on the user's request)
- `fix/live-test` merged into `main` as a normal merge commit (no push). `main` had moved (JARVIS refactor, 13 commits, no UI files); my branch touched 0 JARVIS files; the merge was clean. Verified on merged `main`: `tsc`, vitest 451/451, `vite build`, `dotnet test` 311/311, `export --check`, `contract_check`.
- Real app: UI is loaded from `SpaceshipApp/SpaceshipUI/dist` (rebuilt from the merged tree), config schema and skin resources from this checkout. The host exe was republished with `dotnet publish ShipCore.App -p:PublishProfile=Folder` into `SpaceshipApp/publish/CSpace` (adds `PickHomeDisplayNearest`). Backup of the previous publish: `SpaceshipApp/publish/CSpace-backup-pre-livetest-20261103-2253`. To roll back: close CSpace, delete `publish/CSpace`, copy the backup folder back as `publish/CSpace`.
- CSpace was NOT running when deployed and was not started; the user starts it. Not seen live yet.

## Part 14: picture frame was 1.5x too big in the live app; fit fix; alignment review (2026-11-04)
- **Root cause (U1, from the user's live screenshot):** the frame was exactly 1.5x the size of the modules, anchored top-left. The frame width multiplied by the page's `Scale` value (after `/ DESIGN_FIT`), while the modules' positions follow the window only, so any `Scale` other than the design 0.67 on the page (1 gives 1.5x) made the frame drift from the modules. Reproduced in `e2e/display-fit.spec.ts` (8 cases failed: Scale 0.4, 1, 1.5, 2.5 x picture, rendered). Fix in `FrameLayers.tsx`: no `Scale` multiplier; the frame is the same 16:10 area the modules letterbox into (`.frame` CSS), from the window size alone. 20/20 display-fit tests; vitest 451/451; Playwright 102/102. Deployed and CSpace restarted 2026-11-04 00:00 (the old process had to be force-stopped; it did not close gracefully).
- **Why the live page's `Scale` was not 0.67 is NOT established.** `settings.json` says 0.67 and the registry default is 0.67; the host does not rewrite it (grep found no host code that touches `Scale`). The fix removes the dependency, so it no longer matters for the frame; it still drives line widths and glow radius.
- **JARVIS core spin** set to 2/3 (`SPIN_TRIM` in `modules/jarvis.ts`: rings, plexus and the ball; not the voice-reactive activity or the thinking sweep).
- **Alignment review of the picture frame at the correct fit (preview, 1707x1067):** it is much closer than the screenshot. The orb sits in the picture's console dome; the GPU and NET boxes sit in the picture's top pockets. Remaining differences, top and bottom:
  1. The HUD's own cyan "Decor" trim (88 shapes, drawn for the line-art hull's windscreen) runs a few px off the picture's own edges: a doubled line along the top beam and at the bottom console. With the Decor hidden, the top is clean but flat; at the bottom the picture's ridge is a dark curved arch and the HUD's straight lit lines do not follow it.
  2. CPU and MEM boxes straddle the picture's pocket seams (about 20 px); GPU and NET are in the pockets.
  3. The windscreen strut angles of the picture differ from the line-art hull, so the centre trim never matches.
  4. The bottom status chips sit well on the picture's ridge.
- **Proposed scope (needs the user's OK after seeing the live fit):** (a) a picture-mode trim: replace the Decor with lit lines traced to the picture's own edges (top beam, the bottom arch); (b) seat the four stat boxes in the pockets; (c) keep the chips, orb, dials; (d) side panels stay. This needs hand-traced geometry in 2560x1600 art space and several look-and-adjust passes, so it is a design task, not a quick fix.

## Part 15: "Picture (fitted)" frame mode; hover captions (2026-11-04)
- **New frame choice, additive:** the Cockpit frame row now has Rendered, Picture, **Picture (fitted)**, None. The plain Picture mode is unchanged (it keeps the original layout). Fitted is the same picture art plus a HUD layout seated into the picture's slots. New hidden key `PictureFit` (0/1) in `Settings.inc`, `contract/config-keys.json` (regenerated, identical), `registry.ts`; `frameStyle.ts` maps 'fitted' to `UseShipImage=1, PictureFit=1`; `Style.fitted`; `FrameLayers` draws the picture for both. Tests: `tests/frameStyle.test.ts` (4 styles round-trip, option list, writes), `tests/pictureSlots.test.ts`, `tests/registry.test.ts`, `e2e/picture-slots.spec.ts` (plain picture and line-art keep the original layout; fitted seats everything).
- **Slots, measured on `ship.png` (canvas units, 2560x1600; display coords x1.28):** stepped top band x 883..1677, y 147..243 with a centre divider at x 1280; the side window is bounded below by the rail `y = 1261 - 0.307 x` (the right side mirrors it); the dome slab around the orb (the orb already sits in it); the dash arch ridge at the bottom (the status chips already sit on it). Table in `src/modules/pictureSlots.ts`: the four stat boxes scale 0.78 into the band (two and two either side of the divider); the left and right stacks (hologram 0.85, location/sysinfo 0.85, dots, four app rows 0.8) are compressed and lifted so every row clears the rail by about 29 css px at 1707x1067, identical left and right. Shifts are measured from each zone's DRAWN centre (the skew moves it); an earlier attempt used the unskewed centre and put the right stack 42 px lower than the left (caught by measuring in the page).
- **Verified in the page at 1707x1067, 2560x1600, 1920x1200:** rail clearance, left/right mirror, stat boxes inside the band, plain picture/line-art unchanged. NOT yet seen in the real app; not done: the top/bottom Decor trim (the HUD's cyan lines still run a few px off the picture's own edges and double them in places; the picture has no lit edges of its own to trace, so this needs a design decision).
- **Hover captions (user: "popups don't disappear immediately when I stop hovering"):** `Caption.tsx` hid only on `pointerover` onto another element, or after 6 s. Over transparent parts the HUD window is click-through, so no further event reaches the page and the caption lingered. Now it also hides on `pointerout` (leaving the tipped element), when the pointer leaves the document, and on window blur; moving inside one element keeps its caption, and moving to another swaps it. `e2e/caption-hide.spec.ts` 4/4 (the leave case failed before the fix). In the real WebView2, whether the leave event arrives over a click-through area is assumed (Chromium sends one when the pointer leaves its window), not verified.
- **Gates:** tsc clean; vitest 462/462; Playwright 112 (one `picture-slots` case failed once in the full run, passes 24/24 in repeated parallel runs after the test waits for the boxes to settle); dotnet 311/311; export and contract checks ok.
