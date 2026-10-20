# Setup Wizard, Control Center and Frame Modes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** In the standalone UI, add a first-run setup wizard, a categorised Normal/Advanced Control Center built from the same components, assistant name/label customisation, and RENDERED/PICTURE/NONE frame modes.

**Architecture:** One typed settings registry drives a pure store (values, undo/redo, filters, search), shared Preact components (`SettingsPanel`), the Control Center shell and the wizard. All reads/writes go through `HostBridge` messages; `MockHost` implements them in memory (persisted in localStorage when available) so everything is testable on Ubuntu. Frame layers are exported by `tools/export_ui_assets.py` and drawn by a `FrameLayers` component.

**Tech Stack:** Preact 10 + @preact/signals, TypeScript strict, Vite, vitest (pure logic only), Playwright (DOM/screenshots), Python 3.12 exporter. No new npm dependencies.

**Spec:** `docs/superpowers/specs/2026-10-20-setup-and-control-center-design.md`

## Global Constraints
- Work only under `SpaceshipApp/SpaceshipUI/` and `tools/` (+ tests); **no file under `Skins/` may change** (check `git status --porcelain -- Skins` is empty before every commit).
- Colours and look = Rainmeter theme variables via the existing `src/lib/theme.ts`/`tokens.css`; no new palette. `RefrenceImage.png` is not used.
- Run from `SpaceshipApp/SpaceshipUI`: `npm test` (exporter `--check` + vitest), `npm run test:e2e`, `npm run test:all`. One heavy command at a time (3.8 GB RAM).
- Defaults = the user's current configuration: registry `default` values equal `Settings.inc` where the key exists; where the key is absent the skin's own fallback is used, except `JarvisName` whose default is `Jarvis` (user decision; skin fallback is Clover). No personal text in the repo.
- Wizard: at most 6 steps, every step pre-filled, Next always enabled, "Use defaults" on every step, shown only while `setup.done` is false.
- `config.set` accepts only registry keys (allowlist); new key `AssistantLabel` is additive.
- Storage (`localStorage`) only for per-viewer conveniences and MockHost persistence, always in try/catch; the app must render with it blocked.
- Commit after every task with message ending `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. Do not commit `generated/` (git-ignored).
- Report only commands actually run, with results.

## Review Focus
1. Storage blocked/corrupt (`localStorage` throws or holds garbage): app, wizard gating and Control Center still work from host state.
2. Host write fails (`config.ack ok:false`): UI value rolls back, error shown inline, wizard does not mark done.
3. Slider drag spam: one undo entry per drag, at most one write per 100 ms, final value always sent.
4. Hostile or odd name/label text (empty, 200 chars, unicode, `<script>`, only dots): rejected or normalised per rules, rendered as text, empty falls back to default.
5. Reload mid-wizard and "Use defaults" pressed twice: idempotent, no duplicate writes; optional keys missing from `Settings.inc` show their default without error.

---

## File Structure
```
src/settings/types.ts         SettingDef, Category, Level, Control types
src/settings/registry.ts      REGISTRY: SettingDef[], INTERNAL_KEYS, CATEGORIES
src/settings/dynamic.ts       per-module keys (Off_/CT_/_DX/_DY) from layout.json
src/settings/store.ts         createSettingsStore(host, defs): values, set, undo/redo, reset, filter, search
src/settings/identity.ts      deriveLabel, validateName, validateLabel
src/settings/frameStyle.ts    frameStyleOf(values), applyFrameStyle(style)
src/wizard/wizard.ts          pure state machine
src/ui/SettingRow.tsx, ControlWidget.tsx, GroupSection.tsx, CategoryRail.tsx, SettingsPanel.tsx
src/ui/ControlCenter.tsx      shell: header, Normal/Advanced, search, undo/redo
src/ui/Wizard.tsx             steps built on SettingsPanel
src/ui/HelpPanel.tsx          guide side panel
src/ui/FrameLayers.tsx        frame image layers
src/host/HostBridge.ts        + config/setup/aboutme messages in MockHost
tests/*.test.ts, e2e/*.spec.ts
tools/export_ui_assets.py     + frame images (hashed copy) and guide.json
```
Appendix A holds the full key-to-category assignment the registry is built from (the user's review item 1).

---

### Task 1: Registry types, data and consistency test
**Files:** Create `src/settings/types.ts`, `src/settings/registry.ts`, `src/settings/dynamic.ts`; Test `tests/registry.test.ts`.
**Interfaces:**
- Produces: `type Level = 'normal'|'advanced'`; `type Control = {kind:'toggle'}|{kind:'select',options:{value:string,label:string}[]}|{kind:'slider',min:number,max:number,step:number}|{kind:'text',pattern:string,max:number}|{kind:'color'}|{kind:'action',id:string}`; `interface SettingDef {key:string; file:'Settings.inc'|'State.inc'|'Offsets.inc'; label:string; help:string; category:CategoryId; group:string; level:Level; control:Control; default:string; optional?:boolean; wizard?:'you'|'assistant'|'look'|'modules'|'integrations'; restartRequired?:boolean}`; `CATEGORIES: {id:CategoryId,label:string}[]` (ids `display layout apps sensors performance assistant integrations system`); `REGISTRY: SettingDef[]`; `INTERNAL_KEYS: Set<string>`; `moduleDefs(layout): SettingDef[]` in `dynamic.ts` producing `Off_<Key>`, `CT_<Key>` (State.inc) and `<Key>_DX/_DY` (Offsets.inc) for each zone group key.
- [ ] **Step 1: Write failing tests** in `tests/registry.test.ts` (reads `src/generated/settings.json` and `layout.json` via `fs`): `every Settings.inc key is registered or internal`; `every registry key exists in Settings.inc or is optional`; `defaults equal Settings.inc values for present keys` (colour and numeric strings compared after trim); `keys are unique`; `slider bounds valid (min<max, step>0, default within)`; `select default is an option`; `JarvisName default is Jarvis`; `dynamic defs cover every zone`.
- [ ] **Step 2: Run** `npx vitest run tests/registry.test.ts` — expect FAIL (modules missing).
- [ ] **Step 3: Implement** types and data from Appendix A in the registry; ranges for sliders taken from the existing Control Center (`Skins/Spaceship/@Resources/Scripts/control.lua` bump calls; read, do not edit). Add `help` strings from `Docs/Spaceship-HUD-Guide.md` wording, one sentence each.
- [ ] **Step 4: Run** the test file and `npm test` — expect PASS.
- [ ] **Step 5: Commit** `feat(ui): settings registry and consistency test`.

### Task 2: Host contract and MockHost config
**Files:** Modify `src/host/HostBridge.ts`; Test `tests/mockhost.test.ts`.
**Interfaces:**
- Consumes: `REGISTRY`, `moduleDefs` (Task 1).
- Produces: messages `{type:'config.get',keys:string[]}` → `{type:'config.values',values:Record<string,string>}`; `{type:'config.set',key,value,id:number}` → `{type:'config.ack',id,key,ok:boolean,error?:string}`; `{type:'setup.get'}` → `{type:'setup.state',done:boolean}`; `{type:'setup.finish',mode:'defaults'|'custom'}` → `{type:'setup.state',done:true}`; `{type:'aboutme.get'}`/`{type:'aboutme.set',text}` → `{type:'aboutme.value',text}`. `class MockHost` gains constructor `new MockHost(opts?:{seed?:Record<string,string>; allow?:(key:string)=>boolean; storage?:Storage|null; failKeys?:Set<string>})`; unknown key → ack `ok:false,error:'not allowed'`; `failKeys` forces failure; state persisted under localStorage `mockhost.v1` when `storage` works, memory otherwise; `chooseHost()` passes seed from `generated/settings.json` and the registry allowlist; `?fresh=1` clears persisted state.
- [ ] **Step 1: Failing tests:** `config.set of a registry key is acked ok and readable via config.get`; `config.set of an unknown key is refused`; `failKeys forces ok:false and leaves value unchanged`; `setup.get is false on fresh host, true after setup.finish`; `state survives a second MockHost on the same storage`; `blocked storage (getItem throws) falls back to memory without throwing` (Review Focus 1); `corrupt JSON in storage is ignored`.
- [ ] **Step 2–4:** run (FAIL), implement, run (PASS).
- [ ] **Step 5: Commit** `feat(ui): config/setup contract and MockHost implementation`.

### Task 3: Settings store (undo/redo, filter, search, reset)
**Files:** Create `src/settings/store.ts`; Test `tests/store.test.ts`.
**Interfaces:**
- Consumes: `HostBridge`, `SettingDef[]`.
- Produces: `createSettingsStore(host:HostBridge, defs:SettingDef[], opts?:{now?:()=>number; throttleMs?:number}): SettingsStore` with `values: ReadonlySignal<Record<string,string>>`; `level: Signal<Level>`; `query: Signal<string>`; `error: ReadonlySignal<{key:string,message:string}|null>`; `set(key:string,value:string,opts?:{coalesce?:boolean}): void`; `undo(): void`; `redo(): void`; `canUndo/canRedo: ReadonlySignal<boolean>`; `resetKey(key)`, `resetGroup(category,group)`; `isChanged(key): boolean`; `visibleDefs(): SettingDef[]` (level + query filter; Normal hides advanced); `search(q:string): SettingDef[]` (label, help, key; case-insensitive, ranked label-first); `applyDefaults(): Promise<void>` (writes only keys whose value differs from default).
- [ ] **Step 1: Failing tests:** `set sends config.set and updates value on ack`; `ack ok:false rolls value back and sets error` (Review Focus 2); `undo/redo restore values and send writes`; `slider drag coalesces to one undo entry, writes at most one per 100ms, last value always sent` (fake clock; Review Focus 3); `Normal hides advanced defs, Advanced shows all`; `search finds by label/help/key and ranks label first`; `isChanged false at default, true otherwise`; `resetGroup resets only that group`; `applyDefaults writes only differing keys and twice writes nothing the second time` (Review Focus 5); `missing optional key shows default`.
- [ ] **Step 2–4:** run/implement/run. Optimistic update on `set`, rollback on failed ack, per-key throttle with trailing send.
- [ ] **Step 5: Commit** `feat(ui): settings store with undo/redo, search and filters`.

### Task 4: Identity rules (name and dotted label)
**Files:** Create `src/settings/identity.ts`; Test `tests/identity.test.ts`.
**Interfaces:** Produces `validateName(s:string): {ok:boolean; value:string; reason?:string}` (letters/digits, 1–24, trimmed; empty → default `Jarvis`); `deriveLabel(name:string): string` (`"Jarvis"`→`"J.A.R.V.I.S"`); `validateLabel(s:string): {ok:boolean; value:string; reason?:string}` (`^[A-Za-z0-9. ]{1,24}$`, trimmed, collapses repeated spaces; only-dots rejected; empty → `deriveLabel(name)`). `AssistantLabel` registry entry (optional, default `''` meaning derived).
- [ ] **Step 1: Failing tests:** `deriveLabel("Jarvis")==="J.A.R.V.I.S"`, `deriveLabel("Clover")==="C.L.O.V.E.R"`; `validateName("")` falls back to `Jarvis`; `validateName("<script>")` not ok; `validateName("a".repeat(200))` not ok; `validateName("Zoë")` not ok with reason (letters/digits ASCII only, matching skin's `[^%w]` rule); `validateLabel("....")` not ok; `validateLabel("C.L.O.V.E.R")` ok; `validateLabel("  A  B ")` → `"A B"` (Review Focus 4).
- [ ] **Step 2–4:** run/implement/run. **Step 5: Commit** `feat(ui): assistant name and label rules`.

### Task 5: Shared settings components
**Files:** Create `src/ui/ControlWidget.tsx`, `SettingRow.tsx`, `GroupSection.tsx`, `CategoryRail.tsx`, `SettingsPanel.tsx`; Test `e2e/settings-panel.spec.ts`; Modify `src/tokens.css` (layout classes only, existing tokens).
**Interfaces:**
- Consumes: `SettingsStore`, `CATEGORIES`.
- Produces: `<SettingsPanel store categories mode:'center'|'wizard' only?:(def:SettingDef)=>boolean onHelp?:(key:string)=>void />` rendering groups as `<details>`-style collapsible sections (open state in localStorage `ui.groups.v1`, try/catch); `<SettingRow def store/>` = label, `ControlWidget`, help on hover/focus (`aria-describedby`), changed dot (button, `aria-label="Reset <label> to default"`), restart badge; `ControlWidget` renders the five control kinds; all interactive elements keyboard-operable (arrows move between rows, Space/Enter activates). In wizard mode, advanced defs are inside one "Advanced" disclosure per panel, closed by default.
- [ ] **Step 1: Failing Playwright tests** (page loads `?host=mock&panel=demo`, a dev route rendering `SettingsPanel` for category `display`): `normal level hides advanced rows`; `toggling a row writes config.set (read MockHost.sent via window.__host)`; `changed dot appears after change and resets on click`; `keyboard: ArrowDown moves focus to next row, Space toggles`; `group collapsed state survives reload; with localStorage blocked the page still renders` (Review Focus 1); `wizard mode shows an Advanced disclosure closed by default`.
- [ ] **Step 2–4:** run (`npx playwright test e2e/settings-panel.spec.ts`), implement, run. Expose `window.__host` only when `?host=mock`.
- [ ] **Step 5: Commit** `feat(ui): shared SettingsPanel components`.

### Task 6: Control Center shell
**Files:** Create `src/ui/ControlCenter.tsx`; Modify `src/Hud.tsx` (open button), `src/main.tsx`; Test `e2e/control-center.spec.ts`.
**Interfaces:** Consumes Task 3/5. Produces `<ControlCenter store onClose/>`: left `CategoryRail`, header with Normal/Advanced switch (`role="switch"`), search input (`/` focuses, Esc clears/closes), undo/redo buttons (Ctrl+Z / Ctrl+Y), "Reset group" per group, results list when query non-empty that jumps to and expands the row. Opened from a HUD control button and `?panel=control`.
- [ ] **Step 1: Failing e2e:** `every registry category is listed in the rail`; `search "scale" shows the Scale row and clicking the result expands its group`; `Normal→Advanced reveals advanced rows and tags them`; `undo reverts the last change`; `reset group resets only that group`; `Esc closes`; `a failed write (host failKeys via ?fail=Scale) shows an inline error and reverts` (Review Focus 2); screenshots `artifacts/control-center-normal.png`, `-advanced.png`, `-search.png`.
- [ ] **Step 2–4:** run/implement/run; view screenshots with Read and note defects honestly.
- [ ] **Step 5: Commit** `feat(ui): Control Center with categories, levels, search and undo`.

### Task 7: Wizard state machine
**Files:** Create `src/wizard/wizard.ts`; Test `tests/wizard.test.ts`.
**Interfaces:** Produces `STEPS: {id:'welcome'|'you'|'assistant'|'look'|'apps'|'review'; categories:CategoryId[]; wizard:string|null}[]` (exactly 6); `createWizard(store:SettingsStore, host:HostBridge): Wizard` with `step: Signal<number>`, `next()/back()/skip()`, `useDefaults(): Promise<void>` (store.applyDefaults then `setup.finish{mode:'defaults'}`), `finish(): Promise<void>` (`setup.finish{mode:'custom'}` only after all pending acks succeeded), `changes(): {key,label,from,to}[]` (review list), `shouldShow(host): Promise<boolean>` (from `setup.get`).
- [ ] **Step 1: Failing tests:** `has exactly 6 steps and next is never blocked`; `back/skip move without writing`; `useDefaults writes only differing keys and finishes; calling it twice sends no extra writes` (Review Focus 5); `finish waits for acks and does not finish if a write failed` (Review Focus 2); `changes() lists only changed keys`; `shouldShow false after finish, true on fresh host`; `reload mid-wizard (new wizard on same host) starts at welcome with already-applied values prefilled`.
- [ ] **Step 2–4:** run/implement/run. **Step 5: Commit** `feat(ui): setup wizard state machine`.

### Task 8: Wizard UI and first-run gating
**Files:** Create `src/ui/Wizard.tsx`; Modify `src/main.tsx` (gate), `src/settings/registry.ts` (`wizard` tags per Appendix A), registry entry for System > "Run setup again" and "Reset setup" (`action` controls: `setup.rerun`, `setup.reset`); Test `e2e/wizard.spec.ts`.
**Interfaces:** Consumes Task 5/7. Produces `<Wizard wizard store/>`: step dots, Back/Skip/Next, "Use defaults" on every step, panels via `SettingsPanel mode="wizard" only={d=>d.wizard===stepId}`; step "you" has call-me text row and an about-me textarea (via `aboutme.get/set`, 4000 chars max, never logged); step "assistant" has name, label with live preview via `identity.ts`, wake word select, voice basics; step "apps" explains Gmail/calendar/Obsidian and shows buttons that send `{type:'flow.open',flow:'gmail'|'calendars'|'obsidian'}` (host opens the existing secure flows; MockHost records only); review lists `changes()`.
- [ ] **Step 1: Failing e2e (`?host=mock&fresh=1`):** `fresh host shows the wizard, not the HUD controls`; `clicking Next 5 times without editing reaches Review and Finish works`; `Use defaults on step 2 finishes immediately and the wizard never reappears after reload`; `customize path writes only edited keys (assert MockHost.sent)`; `label preview updates live and an invalid label shows the reason` (Review Focus 4); `Advanced disclosure on the assistant step is closed and expands`; `with localStorage blocked the wizard still gates correctly from host state` (Review Focus 1); screenshots of all 6 steps in `artifacts/wizard-1..6.png`; check each step fits without scrolling at 1280x800.
- [ ] **Step 2–4:** run/implement/run; view the six screenshots and judge the 2-minute flow honestly (count clicks).
- [ ] **Step 5: Commit** `feat(ui): first-run setup wizard`.

### Task 9: Frame modes
**Files:** Modify `tools/export_ui_assets.py`, `tools/test_export_ui_assets.py`; Create `src/settings/frameStyle.ts`, `src/ui/FrameLayers.tsx`; Modify `src/Hud.tsx`, registry (`frameStyle` select under Display > Frame, virtual key mapped to `UseShipImage`+`FrameOff`); Test `tests/frameStyle.test.ts`, `e2e/frame.spec.ts`.
**Interfaces:** Exporter produces `src/generated/frame/<name>.<hash8>.png` for hull, ship, glass_fx, glass_fx_pic, glass_pic, scan, scan_pic, shade, mist, mist_pic, corners (copy only, source dir `Skins/Spaceship/@Resources/Images`) and `frame/manifest.json` `{name: file}`; deterministic, `--check` aware. `frameStyleOf(values:Record<string,string>): 'rendered'|'picture'|'none'` (`FrameOff=1`→none; else `UseShipImage=1`→picture; else rendered); `applyFrameStyle(style): {UseShipImage:string; FrameOff:string}`. `<FrameLayers style values/>` draws, in order, glass tint, glass fx, scan (if `ScanLines=1`), shade, hull or picture, mist, corners (rendered only), using the `*_pic` variants for picture, with the same alpha formulas as `Frame.ini` (`GlassGlare*21`, `ScanAlpha*18`, `ShadeAlpha`, `MistAlpha`, `HullAlpha`; glass tint = `ColorAccent` at `GlassTint`).
- [ ] **Step 1: Failing tests:** python: `exporter copies frame images with hash names and manifest, twice is byte-identical, --check detects a missing file`; vitest: `frameStyleOf/applyFrameStyle round-trip for all three styles`; e2e: `switching style changes the drawn layer set (rendered has corners, picture has ship image and no corners, none has no frame layers)`.
- [ ] **Step 2–4:** run each (`python3 -I tools/test_export_ui_assets.py`, vitest, playwright), implement, run.
- [ ] **Step 5: Parity:** render rmsim Frame-only for `UseShipImage=0/1` and `FrameOff=1` via `tools/run_rmsim_safe.py --set ... --only`-style args if supported (else full scene) and the UI at 2560x1600; run `tools/parity_diff.py`; record numbers in the commit body (informational, not a gate).
- [ ] **Step 6: Commit** `feat(ui): frame modes (rendered, picture, none)`.

### Task 10: Guide export and help panel
**Files:** Modify `tools/export_ui_assets.py`, its test; Create `src/ui/HelpPanel.tsx`; Test `e2e/help.spec.ts`.
**Interfaces:** Exporter produces `generated/guide.json`: `{sections:[{id:string (slug), title:string, level:number, text:string}]}` from `Skins/Spaceship/@Resources/Docs/Spaceship-HUD-Guide.md` (headings and the paragraphs under them; no code blocks; plain text); `<HelpPanel sectionId onClose/>`; registry `helpId?:string` on defs; `onHelp` in `SettingsPanel` opens it.
- [ ] **Step 1: Failing tests:** python: `guide.json has >0 sections, unique ids, no markdown fences, deterministic`; e2e: `clicking ? on a row with helpId opens the matching section; Esc closes`.
- [ ] **Step 2–4:** run/implement/run. **Step 5: Commit** `feat(ui): guide export and help panel`.

### Task 11: Acceptance run and status
**Files:** Modify `tasks/spaceship-migration-plan-v2.md` (status lines only).
- [ ] **Step 1:** Run `python3 -I tools/test_export_ui_assets.py`, `python3 -I tools/export_ui_assets.py --check`, then from `SpaceshipApp/SpaceshipUI`: `npx tsc --noEmit`, `npm run test:all`. Expected: all exit 0.
- [ ] **Step 2:** Check spec acceptance 1-5 one by one and note evidence (counts, screenshot paths); `git status --porcelain -- Skins` empty.
- [ ] **Step 3:** Update the status of P-B+ in plan v2; commit `docs: record setup/control-center/frame-mode status`.

---

## Appendix A: key → category / group / level (draft for the user's review)
Format: Category > Group [N=normal, A=advanced]: keys. `*` = `wizard` step tag. `opt` = optional (absent from Settings.inc until first change; skin fallback applies).
**Display**
- Theme [N]: ColorAccent* look, ColorWarn, GlowAlpha. [A]: ColorDim ColorText ColorAlert ColorGood ColorHighlight ColorWhite ColorPanel CoreWhite GlowWidth TextGlow TextGlowAlpha.
- Frame [N]: frameStyle* look (virtual: UseShipImage+FrameOff), FrameBrightness, HullAlpha. [A]: FrameBehindTaskbar GlassTint GlassGlare ScanLines ScanAlpha ShadeAlpha MistAlpha HullDark HullMid HullLight HullEdge ShipImage.
- Size and text [N]: Scale* look, HudAlpha, AutoFit. [A]: FontTitle FontText FontNum TextScaleLarge TextScaleSmall CaptionStyle HomeMonitor HomeSize OriginX OriginY.
- Startup [N]: BootAnim BootSound.
**Layout**
- Modules [N]: per-module `Off_<Key>`* modules, `CT_<Key>` (dynamic). [A]: per-module `<Key>_DX/_DY`.
- Edit [N]: EditMode (action: toggle edit), Presets (action).
**Apps**: Apps [N]: scan apps (action)*apps, per-app visibility (State.inc `Sel_*`). [A]: icon rebuild (action).
**Sensors**
- Graphs [N]: GraphA_Source GraphB_Source Drive1 Drive2. [A]: DataDivider.
- Network [N]: PingHost AutoSpeedTestHours. [A]: LinkDownMbps LinkUpMbps IpMask LocationEnabled LocationMask.
- Battery [N]: WarnBattery ChargeLimit. [A]: BatteryMinTier.
- Warnings [N]: WarnCpuTemp WarnGpuTemp WarnDiskPct.
- HWiNFO labels [A]: HW_ChargeRate HW_CpuPower HW_CpuTemp HW_Fan1 HW_Fan2 HW_FullCap HW_GpuClock HW_GpuPower HW_GpuTemp HW_RemainCap HW_SsdTemp HW_Wear.
**Performance**: Tier [N]: PerfTier PerfOverride. [A]: TierLite TierLow TierStealth. Hardware control [A]: LltPath LltPowerFeature LltPowerModes LltRefreshFeature LltRefreshRates LltHybridFeature LltHybridAUTO LltHybridDGPU LltHybridECO LltHybridHYBRID LltBatteryFeature LltBatteryNormal LltBatteryConserve.
**Assistant**
- Identity [N]: JarvisName* assistant (opt, default Jarvis), AssistantLabel* assistant (opt), JarvisCallMe* you (default Sir), JarvisEnabled, JarvisAutoStart.
- Wake word [N]: JarvisWakeModel* assistant. [A]: JarvisWakeSensitivity JarvisWakeWord JarvisNameAliases(opt) JarvisStopKey(opt) JarvisBargeIn(opt).
- Voice [N]: JarvisKokoroVoice* assistant, JarvisVoiceSpeed(opt). [A]: JarvisVoice JarvisVoiceRate JarvisSpeed JarvisSilence JarvisChime JarvisChimeVolume(opt) JarvisDuck(opt) JarvisDuckLevel(opt).
- Model [A]: JarvisModel JarvisModelFast JarvisKeepAlive JarvisWhisper JarvisWhisperDevice JarvisContext JarvisGPU(opt) JarvisIdleUnload(opt) JarvisPython JarvisAIRouter(opt).
- Behaviour [N]: JarvisPrivacy* assistant (opt), JarvisLearn(opt), JarvisTalkLess(opt). [A]: JarvisRecall JarvisSeriousTopics JarvisRoomAsk JarvisFollowUp JarvisFollowUpWait JarvisFollowNameWindow JarvisFirstWords JarvisPersonality JarvisSmartSearch JarvisQuietCalendar JarvisDiagnose JarvisWatch JarvisProfile (all opt except JarvisProfile).
- Orb and panel [A]: JarvisOrbBright JarvisOrbSize JarvisOrbits JarvisShell JarvisDial JarvisBars JarvisTint JarvisFrameRate JarvisBlackBackground JarvisColorIdle JarvisColorListen JarvisColorSpeak JarvisMutedPopup JarvisMic(opt).
**Integrations**: Obsidian [N]: ObsidianVault* apps, ObsidianTodo, ReticleTodo, JarvisVault. Mail and calendar [N]: Gmail / calendars (actions `flow.open`)* apps.
**System**: Setup [N]: Run setup again (action), Reset setup (action). [A]: Defaults for everything (action).
(The old DATA tab folds into Integrations; the Rainmeter PRESETS tab folds into Layout > Edit.)
**INTERNAL (never shown as rows; `INTERNAL_KEYS`):** runtime state: MasterPrev, LastSpeedTest, LastAppScan, MonX, MonY, SensorStatus, CtlTab, CtlPage, CtlMod, DialSel; mapped by the virtual `frameStyle` row (real keys, read/written only through it): UseShipImage, FrameOff. `EditMode` is a registry action row (Layout > Edit), not internal.
