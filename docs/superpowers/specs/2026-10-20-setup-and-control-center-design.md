# First-run setup + Control Center redesign + frame modes (standalone UI)

Date: 2026-10-20. Status: DRAFT for review. Path: architectural (new subsystem). Target: `SpaceshipApp/SpaceshipUI` only.
Rules inherited: Rainmeter skin gets no new features (commit 003b6f4 stays as is); colours and look match the skin (theme values from Settings.inc); RefrenceImage.png only for frame/positioning; skip artefacts that look worse; plan v2 principles apply (test-first, MockHost, no Windows claims without proof).

## 1. Goal
1. A **setup page** shown once on first use that gets a non-technical person fully configured in about 2 minutes of clicking, with a one-click "Use defaults".
2. A **Control Center** that is easier and smoother to operate: categories, collapsible groups, Normal vs Advanced, search, undo/redo, visual state of what changed.
3. **The setup page and the Control Center are the same UI pattern and the same components**, so learning one teaches the other. The setup page is a guided walk through the Normal rows of the same categories, with Advanced behind a dropdown.
4. **Frame mode** in the standalone UI: RENDERED (typical frame), PICTURE (the new cockpit picture), NONE.
5. Customisable assistant identity: the name and the dotted label (e.g. "C.L.O.V.E.R") are independent settings.

Non-goals: any Rainmeter/Lua change; the Windows host; porting module content (P-F); training the wake word; changing how secrets are stored.

## 2. Defaults (user decision)
"Use defaults" applies the user's own current configuration: the values in their present `Settings.inc` (assistant name Jarvis, call-me "Sir", wake model hey_jarvis, scale, theme, etc.) plus their existing about-me note file. No personal text is hard-coded in the repo; defaults are read from the exported settings and the registry's `default` field, and a test asserts they agree.

## 3. Settings registry (single source of truth)
`src/settings/registry.ts`: a typed array. Each entry: `key`, `file` (Settings.inc | State.inc | Offsets.inc), `label`, `help` (one sentence, sourced from the guide), `category`, `group`, `level` (`normal` | `advanced`), `control` (`toggle` | `select` | `slider{min,max,step}` | `text{pattern,max}` | `color` | `action`), `default`, `wizard?` (step id), `restartRequired?`.
Used by: Control Center, wizard, MockHost/host `config.set` allowlist (anything not in the registry is refused), the exporter-fed "defaults agree with Settings.inc" test, search index.
Draft categories (mapped from the 10 flat Rainmeter tabs; exact row assignment is done in the plan by reading control.lua rows): **Display** (theme, glow, frame style, scale, hull/tints), **Layout** (module offsets, visibility, click-through, presets), **Apps**, **Sensors**, **Performance**, **Assistant** (name, label, call-me, voice, wake word, privacy, learning), **Integrations** (Gmail, calendars, Obsidian), **System** (startup, setup re-run, reset), **Data**.

## 4. Control Center behaviour
- Left rail of categories; right pane shows groups as collapsible sections (state remembered per viewer in localStorage, wrapped in try/catch).
- Header: **Normal / Advanced** switch (Normal shows `level: normal`; Advanced adds the rest, marked with a small tag), search box (matches label, help, key; jumps to and expands the row), undo/redo, "Reset group".
- Row anatomy: label, control, help on hover/focus, a "changed from default" dot (click = reset that row), restart-required badge.
- Changes apply immediately through `HostBridge.send({type:'config.set'})`; each change is one entry in an undo stack (coalesced for slider drags). Failed writes show inline and roll back the UI value.
- Keyboard: arrows move between rows, Space/Enter toggles, `/` focuses search, Esc closes. Targets sized for mouse use at 2560x1600 with Scale.
- Visual: same colour tokens as the HUD (theme variables), the skin's thin neon line style; no new palette.

## 5. Setup page (first run only)
- Shown when `SetupDone` (State.inc) is not 1. Never again after finish or "Use defaults". Re-run: Control Center > System > Run setup again. Reset flag: same place.
- Time budget: at most 6 steps, every step pre-filled so **Next is always enabled**; whole run is about 2 minutes; progress shown as step dots; Back/Skip on every step; **Use defaults** button on every step (applies section 2 and finishes).
- Steps (each is the Control Center pane for one category, Normal rows only, plus an "Advanced" dropdown that expands that category's advanced groups):
  1. Welcome: Use defaults, or Customize.
  2. You: your name, what the assistant calls you, optional about-me note.
  3. Assistant: assistant name, dotted label, wake word choice, voice basics, privacy.
  4. Look: frame style, theme colour, scale, which modules show.
  5. Apps and integrations: scan apps, optional Gmail / calendars / Obsidian (these open the existing secure flows; secrets are never typed into the registry).
  6. Review: a short list of what changed from default, Finish.
- Inline help in each step comes from the guide: the exporter turns `Spaceship-HUD-Guide.md` headings and first paragraphs into `generated/guide.json`; a "?" opens the relevant section in a side panel. The whole 696-line guide is not shown in the wizard.

## 6. Assistant identity
`JarvisName`: letters/digits, 1-24. New `AssistantLabel`: the dotted display label; default derives from the name ("Jarvis" -> "J.A.R.V.I.S"), editable to anything matching `^[A-Za-z0-9. ]{1,24}$`. Preview shown live. The wake phrase still follows the wake model (a rename does not retrain it; the row says so).
Note: `AssistantLabel` is new; the Rainmeter skin ignores it. Name/label are read by the UI through the registry only.

## 7. Frame modes
`frameStyle`: `rendered | picture | none`, persisted as the existing `UseShipImage` / `FrameOff` pair so both apps agree. The exporter copies the frame images (hull, ship, `*_pic`, glass_fx, scan, shade, mist, corners) into the UI build with content hashes. The UI draws the same layer order as `Frame.ini` (glass tint, glass fx, scan, shade, hull or picture, mist, corners for rendered only) with the theme tint. Live parts (accents, lights, spill, decor) arrive with the frame batch of P-F; this spec delivers the image layers and the switch. Parity: rendered and picture compared to the rmsim renders; none compared to rmsim `FrameOff=1`.

## 8. Host contract (MockHost now, real host later)
New messages in the shared contract: `config.get {keys[]}` -> `config.values {map}`; `config.set {file,key,value}` -> `config.ack {key, ok, error?}`; `setup.get` -> `{done}`; `setup.finish {mode:'defaults'|'custom'}`. Host validates against the allowlist generated from the registry. MockHost keeps an in-memory config (seeded from exported settings) and records sent messages for tests.

## 9. Tests (all on this Ubuntu box)
- vitest: registry (unique keys, all keys exist in Settings.inc/State.inc/Offsets.inc via the exporter output, defaults agree, every control has valid bounds); undo/redo + slider coalescing; Normal/Advanced filter; search; wizard state machine (shows only when not done, Back/Skip/Next, defaults path writes exactly the default map and sets done, finish writes only changed keys); label derivation and validation; frameStyle <-> UseShipImage/FrameOff mapping.
- Playwright (MockHost): screenshot of each wizard step; Control Center in Normal and Advanced; search result; a changed-from-default row; frame modes rendered/picture/none. Asserts on DOM state, plus saved PNGs for review.
- Python: exporter additions (frame image copy with hashes, guide.json) tested in `test_export_ui_assets.py`; `--check` stays green.

## 10. Acceptance
1. `npm run test:all` green; exporter tests green.
2. Fresh MockHost (no `SetupDone`) shows the wizard; "Use defaults" ends with the default config and never shows it again after reload; Customize path reaches Review in at most 6 clicks of Next with no field edited.
3. Control Center: every setting reachable by category and by search; Advanced rows hidden in Normal; undo/redo restores values; reset-dot works.
4. Frame switch changes the drawn layers; rendered/none match rmsim for the layers delivered (document the diff numbers).
5. No file under `Skins/` changed by this work (verified by `git status`).

## 11. Risks and rollback
- Registry drifting from the real settings: guarded by the exporter-fed test.
- Wizard writing settings the Rainmeter skin would misread: only registry keys with the same types/ranges are allowed; new keys (`AssistantLabel`) are additive.
- The row-to-category assignment of about 150 settings is judgment work: done in the plan with the user able to correct it in review.
- Unverified until Windows: real config writes, restart-required behaviour.
Rollback: the work is additive under `SpaceshipApp/SpaceshipUI`; revert the commits.

## 12. Open items for review
1. Category names and the Normal/Advanced split (draft in section 3; the plan will list every row).
2. Whether the wizard's step 5 should only link to the existing Gmail/calendar flows (my assumption) or reimplement them.
