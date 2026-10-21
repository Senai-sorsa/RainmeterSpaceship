# Improvement documentation

Running log of what changed since the Rainmeter Spaceship started moving to the standalone app (C# host + WebView2 + Preact UI). Newest entries go at the top of section 1; section 2 explains every improvement made so far; section 3 says honestly what is not done.
Facts come from git history (`git log`) and from test runs on the Ubuntu VM. Nothing here was run on Windows, in Rainmeter, or in WebView2.

## 1. Progress log

### 2026-10-20 (session 3): audit follow-ups
- Audit item 4 done: `tools/contract_check.py` (Python version of the message check) + `tools/test_contract_check.py`; `python3 -I tools/test_contract_check.py` passes and agrees with all 47 shared fixtures. It checks message shape only; JARVIS does not import it yet, and no pipe round trip exists.
- Audit item 6 (part): the e2e failure-injection option (`?host=mock&fail=Key`) is now a real `MockHost` option, not a poke into a private field in `main.tsx`. vitest 86, tsc clean, Playwright 33 passed afterwards.
- Audit item 1 done with your approval (the one deliberate edit under `Skins/`): `Setup-Jarvis.ps1` now checks the SHA-256 of the three Kokoro files and deletes a file that does not match. Hashes were computed on 2026-10-20 from a fresh download of the `model-files-v1.0` release (they can only prove the file is the one that existed that day, not that the release was clean). The PowerShell was NOT run (no PowerShell here); the hashes were computed with `sha256sum`.
- Audit item 2 corrected: `core.ps1` rebuilds `Bin/ShipCore.exe` from `ShipCore.cs` on skin load when the source is newer (JARVIS-Repair-Plan.txt), so the committed .exe is only a cache. It is stale in git (exe committed 10-12, source 10-17), which is harmless on your machine but means the .rmskin may ship an older helper. No change made.
- Left alone on purpose, because they change the Rainmeter skin (standing ruling: skin untouched) or need your call: item 3 (restrict launch targets), 5 (untrack tool output), 7 (untrack the .rmskin). Store teardown needs a host `offMessage` API and waits for the real host.

### 2026-10-20 (session 3): audit of the risky existing code (report only, no code changed)
Read: `jarvislib/actions.py`, `confirm.py`, the action table in `routing.py`, `Setup-Jarvis.ps1`, requirements, tracked-file sizes, `ShipCore.cs` entry points. Not read: most of the 116k lines (Lua meters, the rest of `jarvis.py`, tools). Findings and their status are in the chat report; fixes are listed under "Audit follow-ups" below once done.

### 2026-10-20 (session 3): host logic, exam-browser list, P-D prototype
- `contract/exam-browsers.json`: Respondus LockDown Browser (the one TAMU's LMS lists, `LockDown.exe` from one third-party file database), Safe Exam Browser, Examplify; Honorlock and Proctorio are Chrome extensions (no process); Zoom deliberately excluded. **Every name is unverified**; confirm in Task Manager on your machine.
- Core, with tests (83 pass): `ExamBrowserList` (feeds `VisibilityPolicy`), `AutoStart` (HKCU Run only, opt-in, path-validated), `Lifecycle` (tray Refresh / Switch to Rainmeter / Quit, `WM_QUERYENDSESSION` never blocks, teardown once).
- `SpaceshipApp/ShipCore.Proto` + `docs/P-D-PROTOTYPE.md`: the go/no-go prototype. Compiles here; never run.

### 2026-10-20 (session 3): fixes from the whole-branch review
Reviewed `4d3f2d2..HEAD` with an Opus subagent (read only). Fixed items 1-11 of its report:

| # | Problem | Fix | Where |
|---|---|---|---|
| 1 | Keys with leading spaces (`   JarvisSilence=` in the real `Settings.inc`) were not found, so a write added a second line; matching was case-sensitive | Match ignores indent and case; the original indent and the line's own `\r` are kept | `ShipCore.Core/ConfigStore.cs` |
| 2 | A lone surrogate or a non-ASCII digit (`١,2,3`) could throw inside the C# checker | `[0-9]` instead of `\d`; the checker catches `InvalidOperationException`/`FormatException`; the TS checker now also refuses lone surrogates, so both sides agree | `Protocol.cs`, `ConfigSchema.cs`, `src/host/contract.ts` |
| 3 | The page could set `JarvisPython` and `LltPath`, which the skin later runs | Removed from the Control Center and from the writable key list (decision: safest option; edit `Settings.inc` by hand) | `registry.ts`, `contract/config-keys.json` |
| 4 | A stale validation error blocked Finish forever | A valid value for the same key clears the error even when nothing needs sending | `store.ts` |
| 5 | A late `config.values` overwrote edits already made | Keys with a write in flight or pending keep the user's value | `store.ts` |
| 6 | About-me save failures were silent and the host's old text replaced the typed text | The wizard checks the text first, shows a message on refusal, and keeps what was typed | `Wizard.tsx`, `HostBridge.ts` |
| 7 | TS accepted ids C# refused (1e20) | `Number.isSafeInteger`; fixture added. C# stays stricter on `1.0`/`1e2`; JS never produces those | `contract.ts`, fixtures |
| 8 | Failed hellos could be retried until the TTL ran out; a null nonce threw | Three attempts per gate, null nonce refused | `PipeGate.cs` |
| 9 | `action` with id `flow.open` was accepted with no `flow` | Flow rows now send a `flow.open` message with the flow; the bare action is no longer allowed | `ControlWidget.tsx`, contract test |
| 10 | Timed-out "Use defaults" rolled back the screen though the host may have written | After a failure the UI re-reads the host's values | `store.ts` |
| 11 | Mixed CRLF/LF files merged lines and duplicated keys | Each line keeps its own ending; new lines copy the file's style | `ConfigStore.cs` |

Tests added: 5 C# (indented/case key, mixed endings, lone surrogate x2, non-ASCII digits, hello cap), 3 vitest (stale error, late values, timed-out defaults), 5 shared fixtures.
Results after the last edit: `dotnet test` 72 passed; `npm test` 86 passed (10 files); `npx tsc --noEmit` clean; `npm run test:e2e` 33 passed.

### 2026-10-20 (session 3): earlier in the session
- Committed the untracked work in three commits: `e23cbb2` (ignore .NET `bin/` `obj/`), `bc6f684` (`ShipCore.Core` + tests, 66 tests), `869559e` (shared host contract + fixtures, empty colour allowed where the default is empty).

### 2026-10-20 (sessions 1-2): setup wizard, Control Center, frame modes
Tasks 1-11 of `docs/superpowers/plans/2026-10-20-setup-and-control-center.md`, commits `6c0f566` to `eba54e4` (explained in section 2).

## 2. What was improved since moving off Rainmeter

**Why:** the Rainmeter skin stays the default and untouched (checked each commit with `git status --porcelain -- Skins`). New UI work goes into the standalone UI (`SpaceshipApp/SpaceshipUI`), per the standing ruling.

### Foundation
- **UI scaffold** (`841fcff`): Vite + Preact + signals + strict TypeScript. A `MockHost` stands in for the C# host so the UI can be built and tested on Linux.
- **Asset exporter** (`98f38d8`, `tools/export_ui_assets.py`): reads the skin's real settings, module keys, frame images and guide into `src/generated/`, deterministically, with a `--check` mode so drift fails the tests. The UI therefore uses the skin's real values, not copies typed by hand.
- **Theme fix** (`8650201`): the UI uses the Rainmeter theme colours, which fixed a dim HUD.
- **Parity tooling** (`d0ea922`, `tools/run_rmsim_safe.py`, `tools/parity_diff.py`): renders the skin in a simulator and diffs it against the UI. Only the safe runner is used because the raw simulator writes inside `Skins/`.
- **Plan v2 and review** (`tasks/spaceship-migration-plan-v2.md`, `tasks/migration-review-2026-10-20.md`): the migration plan, after reviewing and correcting an earlier plan.

### Setup wizard (first run only)
- **State machine** (`src/wizard/wizard.ts`): six steps (welcome, you, assistant, look, apps, review). Back, Skip and Next are never blocked and write nothing. "Use defaults" is on every step: it applies the defaults (your current configuration, assistant Jarvis, call-me Sir, wake model hey_jarvis, no personal text in the repo), then marks setup finished only if every write was acknowledged.
- **UI** (`src/ui/Wizard.tsx`): customise the assistant name and the dotted label (the "C.L.O.V.E.R" part) with a live preview that shows the reason when a value is invalid; about-me text; Gmail, calendar and Obsidian connect buttons that ask the host to open the existing secure flows (no secrets in the UI); a Review step listing only what changed.
- **First run only:** the host reports `setup.done`; the wizard appears only while it is false. System > "Run setup again" / "Reset setup" bring it back on purpose.
- **Verified:** 8 Playwright tests, including that all six steps fit 1280x800 without scrolling.

### Control Center (usability, not looks)
- **Registry** (`src/settings/registry.ts`): one list of every setting with label, help, control type, default, category, group, and a normal/advanced level. 8 categories (Display, Layout, Apps, Sensors, Performance, Assistant, Integrations, System); module settings are generated from the skin's real module keys.
- **Store** (`src/settings/store.ts`): every write is validated first, sent to the host, and rolled back if refused; undo/redo with typing and slider drags merged into one step; search ranked by label, key, then help text; per-setting and per-group reset; Normal vs Advanced switch.
- **Components**: category rail, collapsible groups, rows with badges for advanced settings, reset-group strip, help panel opened with `?` (built from the Quick Guide).
- **Fixes along the way:** rollback by write identity, slider defaults on their step grid, module keys from the real skin.

### Frame modes
- RENDERED, PICTURE and NONE in the standalone UI (`FrameLayers.tsx`, `frameStyle.ts`), layered like `Skins/Spaceship/Frame/Frame.ini`; the same modes exist on the Rainmeter side (`003b6f4`, additive). Parity numbers against the simulator were recorded as informational.

### Host contract and the C# core (this session)
- **Shared contract** (`contract/config-keys.json`, `contract/fixtures/ui-to-host.json`): the list of writable keys is generated from the registry and the same message fixtures are run by both the TypeScript and the C# checker, so the two cannot disagree silently.
- **`ShipCore.Core`**: `ConfigStore` (atomic writes that keep comments, BOM and line endings, only schema keys and valid values), `Protocol` (shape check for untrusted WebView messages), `ActionGate` (exact allowlist, no shell, power actions need confirmation and go through an interface so tests use fakes), `PipeGate` (nonce, session and OS-reported pid), `VisibilityPolicy`.
- **Safety rules kept:** tests touching OS actions use fakes first; no real recycle-bin, power or process calls in tests.

### Testing and process
- Fail-fast Playwright config, one heavy command at a time, foreground with a timeout (after a crash from memory pressure).
- Reviews batched into one whole-branch review instead of one per task, and subagents used only where they saved tokens.
- Token changes already applied by the user: TokenWise disabled and its routing block removed from `CLAUDE.md` (`676fa8b`).

## 3. Not done (and why)

The two requests pasted into this session were: (A) setup page + Control Center redesign, (B) finish the remaining migration phases so the Rainmeter app runs in the standalone UI. A is done (section 2). B is only partly possible on this VM:

| Requirement | Status |
|---|---|
| Starts at power-on with little delay (opt-in `HKCU\...\Run`, no admin) | Logic written and tested (`AutoStart`); the Windows registry glue is not; the delay must be measured, not assumed |
| Fluid animation (WebView2 composition hosting) | Not built. Needs the Windows transparent-window prototype (P-D go/no-go) |
| CPU/GPU no higher than Rainmeter | Not measurable here. Windows baselines first (`tools/gpu_baseline.ps1` exists) |
| Easy close and refresh (tray: Refresh / Quit / Switch to Rainmeter; `WM_QUERYENDSESSION`) | Logic tested (`Lifecycle`); the prototype wires it up but has never run |
| No interference with other apps (never topmost, no hooks, suspend when an exam browser runs) | Policy + list tested; names unverified; not wired into a running host |
| Modules ported from Rainmeter into the UI | Not started; the host messages they need are not defined yet |
| Merge `feature/setup-control-center` to `main` | Waiting for your yes |
| Windows run of `py -3 -B test_jarvis.py` | Waiting for you |
| Module positions in PICTURE frame mode | Not changed |

Token use: the remaining cost is outside the repo (claude.ai connectors you do not use, switched off in `/mcp` or claude.ai > Settings > Connectors; superpowers can be turned off once the review work is finished). I did not change global settings.
