# SOL Review Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the findings in `SOL-JARVIS&SYSTEM-review.md` that survived a second check against the code, with the smallest change per finding and a test or build check for each.

**Architecture:** Independent small fixes in three code areas (TypeScript UI, C# host, JARVIS Python), one task per fix so each can be reviewed and rolled back on its own. Shared C# shutdown logic goes into one tested helper in `ShipCore.Core`; the WinForms runners in `ShipCore.App` (no test project) only use it.

**Tech Stack:** Preact + TypeScript (vitest, Playwright), .NET (`ShipCore.Core.Tests`), Python 3 (`Skins/Spaceship/@Resources/Jarvis`).

**Spec:** `SOL-JARVIS&SYSTEM-review.md` (repo root) as corrected by the verification table in this file.

## Global Constraints

- "Dont break anything" (user `CLAUDE.md`). Smallest change that fully solves each task; no refactors, no dependency changes, no framework changes.
- Read `CLAUDE-READ-BEFORE-RUNNING-ANYTHING.md` before running any test or script. Before running a Python test file, grep it for real recycle bin / power / sleep / Bluetooth / Wi-Fi / service / registry / process-kill / file-deletion calls (`shell32`, `ctypes`, `subprocess`, `os.remove`, `shutil.rmtree`, `powercfg`, `rundll32`). No test may reach a real destructive call.
- No power-plan switch, refresh-rate change, volume change or other real Windows action is run to verify a fix. Windows-only paths are verified by build plus a unit test on the pure part.
- Work on a new branch `fix/sol-review` from `main`. The working tree already has uncommitted JARVIS changes (`jarvis.py`, `jarvislib/*`, `test_jarvis.py`, etc.). Never `git add .`; stage only the files named in each task, and use `git add -p` for `jarvis.py`.
- Do not deploy, republish `publish/CSpace`, or restart CSpace. The user does that.
- Report exact commands and observed results; name any check that was skipped.
- Baseline gates before the first task (record the numbers, they are the "unchanged" reference): `cd SpaceshipApp/SpaceshipUI && npm test` (last known vitest 501/501), `dotnet test SpaceshipApp/ShipCore.Core.Tests` (last known 311/311), `npx tsc --noEmit`.

## Review Focus

- A `calendar.update` text with thousands of `E` lines or a 10 MB title must not freeze or bloat the HUD (Task 4).
- A dial write with an out-of-range step (power/refresh index 0 or 99) must show NOT SENT and never reach the host (Task 5).
- Shutting down while a calendar, ping, speed test, status script or mail check is in flight must not throw or post into a disposed WebView (Task 8).
- A `config.set` or `llt.set` id of `9007199254740993` must be refused by the C# host exactly as the page refuses it (Task 3).
- Two `TRAINWAKE` commands in a row must start one training, not two (Task 7).

---

## Verification results (what the second check found)

Method: every finding below that names code was read against the current files. Findings I could not tie to code, and the positive baselines (#24, #26, #44-#56), were not re-audited; they need no action.

**Confirmed real, fix (Tasks 1-9):** #14, #63, #59 (+#62 as its parity test), #21, #18, #38/#39/#40 (defensive), #72, #74, #60, #64, #65-#69, #70, #75, #12/#42, #28, #2, #5.

**Confirmed but latent (the trigger does not occur today); cheap hygiene, Task 10:** #7 (JarvisModule is mounted once, `Hud.tsx:180`), #8 (one core), #20 (`hostDialRunner` is called once at module load, `BottomModule.tsx:23`, so there is one listener for the app's life), #31 and #34 (`Root` mounts once; `startPreviewFeed` runs once in preview), #9 (double focus).

**Corrected (the review overstated it):**
- #20 was rated Critical. It is a latent leak only; downgraded to hygiene.
- #38/#40: `Ics.Text` already writes at most 40 events, soonest first (`Ics.cs`), so unbounded or unsorted input needs a hand-edited file or the skin's own writer. Kept as cheap defensive fixes, not bugs.
- #73 (pickle): `wake_<style>.pkl` lives in the skin's `Data` folder, beside `jarvis.py`; anyone who can write there can already edit the code that runs. Not a new privilege boundary. Left for the user to decide (see Decisions).
- #71: .NET `HttpClient` already refuses an https-to-http redirect. Plain `http://` feeds are a policy choice, not a bug (see Decisions).
- #64: the leaked objects are released by the garbage collector eventually; this is tidiness, not a growing leak. Needs a live audio check.

**Not a bug / withdrawn:** #11 (`dt` is meant to measure time since the last real step, so leaving `s.at` alone on a skipped frame is correct), #30 (metrics arrive about once a second; frozen-without-data is by design), #17 (`modules/drawer.ts` has no `duration` import; the file the review meant was not found), #57 (withdrawn in the review), #58 (unconfirmed), #43 (verified not a bug).

**Notes needing no code (kept in the review as records):** #1, #3, #4, #6, #10, #13, #16, #19, #22, #23 (map is bounded by user clicks), #25, #27, #29, #32, #33, #35, #36, #37, #39 (folded into Task 4), #41, #45, #54, #61.

## Decisions (answered by the user 2026-11-04: "do what you recommend")

1. **#71 calendar over plain HTTP: keep `http://` working and log `CAL_HTTP_LINK,<label>` when an http feed is fetched.** Done in Task 9, step 4. No refusal.
2. **#73 pickle wake model: leave as is**, accepted local risk (same trust level as the code beside it). No task.
3. **#15 VIDEO MEMORY graph: hide the source until the host sends VRAM.** No host protocol change. Done in Task 1, step 6. The source reappears by itself when a reading named `mVRAM` arrives.
4. **#36** control characters in notices: not done (parity only).
5. **Execution: subagent-driven**, one branch `fix/sol-review` in the main working tree (the uncommitted JARVIS work stays untouched).

---

## File Structure

| File | Change |
|---|---|
| `SpaceshipUI/src/modules/sources.ts` | Task 1 |
| `ShipCore.Core/PowerPlans.cs` (new), `ShipCore.App/WindowsDial.cs`, `ShipCore.Core.Tests/PowerPlansTests.cs` (new) | Task 2 |
| `ShipCore.Core/Protocol.cs`, `ShipCore.Core.Tests/ProtocolTests.cs` | Task 3 |
| `SpaceshipUI/src/modules/calendarSource.ts`, `tests/calendarSource.test.ts` | Task 4 |
| `SpaceshipUI/src/modules/dialSetter.ts`, `tests/dialSetter.test.ts` | Task 5 |
| `SpaceshipUI/src/modules/target.ts`, `tests/centerFrames.test.ts` | Task 6 |
| `Jarvis/jarvislib/voice/output.py`, `Jarvis/jarvis.py`, `Jarvis/tests/` | Task 7 |
| `ShipCore.Core/RunnerLifetime.cs` (new), `ShipCore.Core.Tests/RunnerLifetimeTests.cs` (new), `ShipCore.App/{CalendarRunner,NetRunner,SpeedRunner,StatusRunner,MailRunner,JarvisPipe}.cs` | Task 8 |
| `ShipCore.App/MailRunner.cs`, `ShipCore.App/WasapiLoopback.cs`, `ShipCore.App/HostServices.cs` | Task 9 |
| `SpaceshipUI/src/{main.tsx,modules/JarvisModule.tsx,host/previewFeed.ts,modules/console.ts,modules/dial.ts,Hud.tsx,host/HostBridge.ts,modules/jarvis.ts}` | Tasks 10-11 |
| `SOL-JARVIS&SYSTEM-review.md` | Task 12 |

Paths: `SpaceshipUI` = `SpaceshipApp/SpaceshipUI`; `ShipCore.*` = `SpaceshipApp/ShipCore.*`; `Jarvis` = `Skins/Spaceship/@Resources/Jarvis`.

---

### Task 0: Branch and baseline

- [ ] **Step 1:** `git switch -c fix/sol-review` (the dirty tree travels with the branch; do not stash or reset).
- [ ] **Step 2:** Run the three baseline gates in Global Constraints and write the counts at the top of the commit message of Task 1.

---

### Task 1: DISK I/O graph reads the key the host sends (#14)

**Files:** Modify `SpaceshipUI/src/modules/sources.ts:70`. Test: `SpaceshipUI/tests/sources.test.ts` (find the existing sources test with `grep -l "SOURCES" tests`; create this file if none).

**Interfaces:** Produces: `SOURCES.disk.get(r)` returns `{ value: r.mDiskIO, text: rate(r.mDiskIO) }`.

- [ ] **Step 1: Failing test** `disk source follows mDiskIO`: `SOURCES.disk.get({ mDiskIO: 52000 }).value` equals `52000`; with `{}` it equals `0`.
- [ ] **Step 2:** `npx vitest run tests/sources.test.ts` fails (value 0).
- [ ] **Step 3:** Change the getter to `const v = val(r, 'mDiskIO');`. The host sends one combined rate (`systemMetrics.ts:91`), so there is no read/write split.
- [ ] **Step 4:** the test passes; `npx tsc --noEmit` clean.
- [ ] **Step 5:** commit `fix(ui): disk I/O graph reads mDiskIO`.
- [ ] **Step 6 (#15, hide VRAM until the host sends it):** the VIDEO MEMORY source (`SOURCES.vram`, key `mVRAM`) has no host producer, so it always shows 0.0 GB. Make the list of sources offered to the user (where `ORDER` is consumed; `grep -rn "ORDER" src`) skip `vram` unless the current readings contain `mVRAM`. A graph slot already saved as `vram` must not crash: it falls back to the slot's default source. Test: with `{}` readings `vram` is not offered and a saved `vram` resolves to a valid source; with `{ mVRAM: 1e9 }` it is offered and resolves to itself. Commit `fix(ui): hide the VRAM graph until the host reports VRAM`.

---

### Task 2: Correct High Performance power-plan GUID (#63)

**Files:** Create `ShipCore.Core/PowerPlans.cs`; modify `ShipCore.App/WindowsDial.cs:12-16`; test `ShipCore.Core.Tests/PowerPlansTests.cs`.

**Interfaces:** Produces `public static class PowerPlans { public static readonly IReadOnlyDictionary<string,string> Guids; }` with keys `quiet`, `balance`, `performance`.

- [ ] **Step 1: Failing test** `PowerPlansTests.Performance_is_the_windows_high_performance_plan`: `PowerPlans.Guids["performance"] == "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c"`, `["balance"] == "381b4222-f694-41f0-9685-ff5bb260df2e"`, `["quiet"] == "a1841308-3541-4fab-bc81-f71556f20b4a"` (the values `jarvislib/actions.py:111` and `test_jarvis.py:301` already use).
- [ ] **Step 2:** `dotnet test SpaceshipApp/ShipCore.Core.Tests --filter PowerPlansTests` fails to compile or fails.
- [ ] **Step 3:** Add `PowerPlans`; make `WindowsDial.Plans` use `PowerPlans.Guids` (same dictionary type, same keys, so callers are unchanged).
- [ ] **Step 4:** full `dotnet test` passes (311 plus the new test); `dotnet build SpaceshipApp/ShipCore.App` 0 errors.
- [ ] **Step 5:** commit `fix(host): correct the performance power-plan GUID`. Do not switch plans to test it; the user checks `powercfg /list` and the dial live.

---

### Task 3: C# accepts only JavaScript-safe ids (#59, #62)

**Files:** Modify `ShipCore.Core/Protocol.cs:41-42,56-57,92-93`; test `ShipCore.Core.Tests/ProtocolTests.cs`.

**Interfaces:** Produces `const long MaxSafeId = 9007199254740991L` in `Protocol`; the three id checks add `&& n <= MaxSafeId`.

- [ ] **Step 1: Failing tests** for `config.set`, `llt.set` and `dial.set`: id `9007199254740991` is accepted; id `9007199254740992` and `9223372036854775807` return `"bad id"`. These three ids are also the parity fixture for the TypeScript side (Step 2).
- [ ] **Step 2:** add the same three ids to the existing contract test on the page (`grep -ln "bad id" SpaceshipUI/tests`) so both validators are pinned to one list; it should already pass.
- [ ] **Step 3:** run the new C# tests, see FAIL; apply the bound; see PASS; full `dotnet test` passes.
- [ ] **Step 4:** commit `fix(host): refuse ids above the JavaScript safe-integer range`.

---

### Task 4: Calendar text is bounded and sorted (#38, #39, #40)

**Files:** Modify `SpaceshipUI/src/modules/calendarSource.ts:26-45`; test `SpaceshipUI/tests/calendarSource.test.ts` (find or create).

**Interfaces:** Produces `parseCalendarTxt(text)` returning events sorted by `s` then `e`, at most 100, with `title` and `label` cut to 200 and 60 characters; `acceptCalendarUpdate` ignores `text.length > 262144`.

- [ ] **Step 1: Failing tests:** (a) three `E` lines out of order come back soonest first, and `rows()` for them shows the soonest as the first row; (b) 500 `E` lines give 100 events; (c) a 5000-character title is cut to 200; (d) a start of `99999999999999999999` (not a safe integer) drops that line; (e) `acceptCalendarUpdate` with a 300 000-character text leaves `calendarFeed` unchanged.
- [ ] **Step 2:** run, see FAIL. **Step 3:** implement with constants `MAX_TEXT = 262144`, `MAX_EVENTS = 100`, `MAX_TITLE = 200`, `MAX_LABEL = 60`; check `Number.isSafeInteger` on the parsed seconds. **Step 4:** PASS, plus the existing calendar tests (`grep -l calendar tests`). **Step 5:** commit.

---

### Task 5: Dial refuses an out-of-range step before sending (#21)

**Files:** Modify `SpaceshipUI/src/modules/dialSetter.ts:58-59,73-82`; test `SpaceshipUI/tests/dialSetter.test.ts`.

**Interfaces:** `createDialSetter(...).set('power', v)` and `set('hz', v)` return `{ note: 'NOT SENT', ok: false }` without calling the gate when `steps(...)[v - 1]` is undefined.

- [ ] **Step 1: Failing test:** with a runner spy, `set('power', 0)` and `set('hz', 99)` return `NOT SENT` and the spy is never called; `set('power', 1)` still reaches the gate (returns pending).
- [ ] **Step 2-4:** run FAIL; make `ROUTE.power`/`ROUTE.hz` return `null` for a missing step and have `set` return NOT SENT on `null`; PASS; existing dial tests pass.
- [ ] **Step 5:** commit. Not done: #20's listener disposer (latent; see Task 10).

---

### Task 6: Lock pulse advances once per move, not once per draw (#18)

**Files:** Modify `SpaceshipUI/src/modules/target.ts:88-95,118-128`; test `SpaceshipUI/tests/centerFrames.test.ts`.

**Interfaces:** `targetMove` decrements `state.lockAnim` by 1 per call (after the name-change and dwell checks set it); `targetFrame` only reads it. The unused `step` parameter of `targetFrame` stays for callers.

- [ ] **Step 1: Failing tests:** `targetFrame` called three times with the same state leaves `state.lockAnim` unchanged; after `targetMove` sets `lockAnim = 18` (new process name), the next `targetMove` takes it to 17.
- [ ] **Step 2:** run FAIL. **Step 3:** move the decrement; keep `zoom` and `flash` computed from the current value so the first frame after a lock looks the same. **Step 4:** the whole `centerFrames.test.ts` (9 tests) passes; `e2e` target/centre specs pass (`npx playwright test -g target`). **Step 5:** commit.

---

### Task 7: JARVIS Python: clean live text on failure, one wake training at a time (#72, #74)

**Files:** Modify `Jarvis/jarvislib/voice/output.py:89-99`; `Jarvis/jarvis.py:1621-1622` (stage only these hunks with `git add -p`; the file has other uncommitted edits); tests in `Jarvis/tests/test_session.py` or a new `Jarvis/tests/test_output_text_only.py`.

**Interfaces:** `say_text_only(sentences, collected)` always calls `live("")` before returning or raising. `TRAINWAKE` starts a thread only when `not wake.TRAINING.is_set()` and no start is already pending (a module-level `threading.Lock` try-acquire `_train_start`, released when the thread ends).

- [ ] **Step 1:** dry-run check per Global Constraints on the test files you touch.
- [ ] **Step 2: Failing tests:** (a) a `sentences` generator that raises after one item still leaves `live` last called with `""` (patch `live` with a recorder); (b) two `TRAINWAKE` lines handled back to back start one thread (patch `train_wake` with a blocking fake and `threading.Thread` spy; no microphone, no real training).
- [ ] **Step 3:** wrap the loop in `try/finally`; add the guard and a log line `wake training already running`.
- [ ] **Step 4:** `py -3 -I tests/run_all.py` and `py -3 -I test_jarvis.py` show no new failures versus the baseline you recorded in Task 0 (record that Python baseline too).
- [ ] **Step 5:** commit only the hunks for this task.

---

### Task 8: Runners stop cleanly at shutdown (#60, #65-#69)

**Files:** Create `ShipCore.Core/RunnerLifetime.cs`, test `ShipCore.Core.Tests/RunnerLifetimeTests.cs`; modify the six `ShipCore.App` runners listed in File Structure.

**Interfaces:**
```csharp
public sealed class RunnerLifetime : IDisposable {
  public CancellationToken Token { get; }
  public bool Disposed { get; }
  public bool Post(Action<string> post, string json);   // false (and no call) once disposed or if post throws ObjectDisposedException
  public void Dispose();                                // cancels Token, sets Disposed; idempotent
}
```

- [ ] **Step 1: Failing tests:** `Post` calls through before `Dispose` and not after; `Dispose` twice does not throw; `Token.IsCancellationRequested` after `Dispose`; `Post` swallows an `ObjectDisposedException` from the callback and returns false.
- [ ] **Step 2:** run FAIL; implement the class.
- [ ] **Step 3:** use it in each runner, one commit per runner so a problem can be reverted alone:
  - `CalendarRunner`: pass `Token` to `Http.GetStringAsync(uri, Token)`; `Tick`/`Read` return early when `Disposed`; route `post` through `Post`.
  - `NetRunner`: pass `Token` to the three HTTP calls and `_pinger.SendPingAsync` (use the overload that takes a timeout and run it with `Token` via `Task.WaitAsync`); catch `OperationCanceledException`; route `post` through `Post`; `Dispose` cancels before disposing `_pinger`.
  - `SpeedRunner`: add `IDisposable`; kill the speedtest process tree when `Token` is cancelled (`Token.Register`); skip `Send` once disposed.
  - `StatusRunner`: the continuation checks `Disposed` first and `Dispose` kills running script trees (keep a `Process` registry in `RunScript`'s caller, or pass `Token` to `RunScript` and kill on cancel).
  - `MailRunner`: link `Token` into the IMAP `cts`; skip the file write and `post` once disposed.
  - `JarvisPipe`: keep the `Serve` task; `Dispose` cancels, waits up to 2 s (`Task.Wait(2000)`), disposes `_stop`.
- [ ] **Step 4:** `dotnet test` all pass; `dotnet build SpaceshipApp/ShipCore.App` 0 errors, 0 new warnings. Wiring of `Dispose` for `SpeedRunner` into `Program.cs` is part of this step (find where the other runners are disposed: `grep -n "Dispose()" ShipCore.App/Program.cs`).
- [ ] **Step 5:** state plainly in the report that shutdown behaviour was build-checked only; the user closes CSpace once to confirm a clean exit.

---

### Task 9: Three small host hardening fixes (#70, #75, #64)

**Files:** `ShipCore.App/MailRunner.cs:67-77`, `ShipCore.App/HostServices.cs:33`, `ShipCore.App/WasapiLoopback.cs:52-78`.

- [ ] **Step 1 (#70):** in `Imap(...)` throw `InvalidDataException("reply too large")` when the accumulated text exceeds 65536 characters; `Check()` already maps it to `ERR`. Build check only.
- [ ] **Step 2 (#75):** replace the `Select` on line 33 with a loop that wraps each `p.ProcessName` in `try/catch (Exception e) when (e is InvalidOperationException or System.ComponentModel.Win32Exception)` and skips that process; dispose every `Process`. If the name list logic can be extracted as a pure function over `IEnumerable<Func<string>>`, put it in `ShipCore.Core` with a test that a throwing entry is skipped; otherwise build check only.
- [ ] **Step 3 (#64):** in `WasapiLoopback.Start`, release the local `device` (`Marshal.ReleaseComObject`) in a `finally` once `Activate` has returned, and on every failure path after `_client` is set call `Stop()` before returning false. Do not change the success path.
- [ ] **Step 4 (#71 decision 1):** in `CalendarRunner.Fetch`, when `uri.Scheme == Uri.UriSchemeHttp`, call `log($"CAL_HTTP_LINK,{src.Label}")` (label only, never the URL). Fetching is unchanged; nothing is refused.
- [ ] **Step 4b:** `dotnet build` 0 errors; `dotnet test` passes. **Step 5:** one commit per step. Ask the user to start and stop music once with CSpace to confirm the spectrum still works (WASAPI cannot be tested here).

---

### Task 10: Latent lifecycle hygiene in the page (#31, #34, #7, #9, #20)

**Files:** `SpaceshipUI/src/main.tsx:71`, `src/host/previewFeed.ts:13`, `src/modules/JarvisModule.tsx:69-77,128`, `src/modules/dialSetter.ts:35-42`; tests in `tests/previewFeed.test.ts` and the existing jarvis module test.

- [ ] **Step 1: Failing tests:** calling `startPreviewFeed()` twice leaves one interval pair (spy on `setInterval`); it returns a stop function that clears them.
- [ ] **Step 2:** implement: `startPreviewFeed(): () => void` with a module-level guard; `main.tsx` returns the `onMessage` disposer from the effect (`const off = host.onMessage(...); return typeof off === 'function' ? off : undefined`); give the two SVG filters ids from `useId()` (`orb-tint-${id}`, `orb-echo-${id}`) and reference the same ids; remove the redundant `autoFocus` prop and keep the `ref` focus.
- [ ] **Step 3:** `hostDialRunner` stays as is (one caller at module load); add a one-line comment saying so instead of code. This is deliberate: the fix would be larger than the risk.
- [ ] **Step 4:** `npx tsc --noEmit`, `npm test`, `npx playwright test -g "jarvis|preview"` pass. **Step 5:** commit.

---

### Task 11: Small logic hardening in the page (#12, #42, #28, #2, #5)

**Files:** `src/modules/console.ts:135-138`, `src/modules/dial.ts:43`, `src/Hud.tsx:66-69`, `src/host/HostBridge.ts:37-42`, `src/modules/jarvis.ts:47-72`; tests next to each.

- [ ] **Step 1: Failing tests:** (a) `cycle(['60','120','165'], '165')` and a list where one name contains another (`['bal','balanced']`, current `'balanced'`) pick the exact entry; (b) the dial's power `valueOf` does the same; (c) `hudLabel({ JarvisName: '', AssistantLabel: '###' })` returns a non-empty label (`deriveLabel(DEFAULT_NAME)`); (d) `MockHost` replies `config.ack` with `ok:false,error:'bad id'` when `id` is not a number; (e) `plexus(3)` does not throw.
- [ ] **Step 2:** run FAIL. **Step 3:** exact match first, `includes` only as the fallback (export `cycle` for the test if it is not exported, minimal); fall back to `validateName(v.JarvisName ?? '').value` in `hudLabel`; `typeof id === 'number'` guard; `for (m < Math.min(3, near.length))` in `plexus`.
- [ ] **Step 4:** `npm test`, `npx tsc --noEmit` pass; the existing console/dial tests unchanged. **Step 5:** commit.

---

### Task 12: Correct the review document

**Files:** `SOL-JARVIS&SYSTEM-review.md`.

- [ ] **Step 1:** Fill the empty body of #14 (the mismatch: graph reads `mDiskRead`+`mDiskWrite`, host sends `mDiskIO`; `strip.ts` already uses `mDiskIO`).
- [ ] **Step 2:** Renumber the "Confirmed bugs" list (it runs 1-6 then 2-11), and re-rate #20 and #7/#31/#34 as latent, #11 and #30 and #17 as withdrawn, #73/#71 as policy decisions, using the table above.
- [ ] **Step 3:** Mark each finding with `FIXED in <commit>` as the tasks land.
- [ ] **Step 4:** commit `docs: correct the SOL review after verification`.

---

## Final gate (after Task 12)

- [ ] `cd SpaceshipApp/SpaceshipUI && npx tsc --noEmit && npm test && npx vite build` all green; vitest count = baseline + new tests.
- [ ] `npx playwright test` (about 7 minutes): no new failures; list any that also failed on `main`.
- [ ] `dotnet test SpaceshipApp/ShipCore.Core.Tests` = baseline + new tests; `dotnet build SpaceshipApp/ShipCore.App` 0 errors.
- [ ] Python: same pass/fail as the Task 0 baseline.
- [ ] `py -3 -I tools/contract_check.py` ok (it is already modified in the tree; run it, do not edit it).
- [ ] Report: commands run, results, anything skipped (WASAPI, power plan, shutdown behaviour, real WebView2), files changed, rollback: `git revert <commit>` per task, or `git switch main` to leave the branch unmerged.

## Self-review

- **Coverage:** every "confirmed real" finding maps to a task; latent ones to Task 10/11; policy items are under Decisions; withdrawn items are listed with reasons.
- **Types:** `RunnerLifetime.Post(Action<string>, string)` matches the runners' `Action<string> post`; `PowerPlans.Guids` keeps `WindowsDial.Plans`' key set; `startPreviewFeed` change is the only signature change in the page and its one caller ignores the result.
- **Not in this plan on purpose:** Rainmeter skin edits, `draw/*`, `wizard/*`, `GodMode/*` (not audited by the review), and any change to the user's uncommitted JARVIS work beyond the two hunks in Task 7.

---

### Task 13 (added 2026-11-04 at the user's request): window shading follows the active frame

User: "there are window shading issues when switching from rendered to picture, due to how picture and rendered have different sizes - make sure to account for this and make the window shading sizing and other window features automatically change accordingly."

**Files:** `SpaceshipUI/src/ui/FrameLayers.tsx`, `SpaceshipUI/tools`/`tools/export_ui_assets.py` only if a picture variant of an asset must be exported; tests `SpaceshipUI/e2e/frame-modes.spec.ts` (or a new `e2e/window-shading.spec.ts`) and a unit test where the logic is pure.

**Known facts (read from the code, not yet measured):**
- `FrameLayers.tsx:67` draws `shade` for every frame mode; glass tint, glare, scanlines and mist already have `_pic` variants (`glass_pic`, `glass_fx_pic`, `scan_pic`, `mist_pic`). The skin also ships `window_mask_pic.png`, which `export_ui_assets.py` does not export, and the rendered-only finish layers (`Finish`, `TrimSpill`, `Grain`) use `window_mask` (rendered windows) and are skipped for pictures.
- The user already has uncommitted edits in `FrameLayers.tsx` (`decorClip`/`consoleCutout`), `panelSlab.ts`, `stage.ts`-adjacent files. Commit only this task's hunks (`git add -p`); never the user's.

- [ ] **Step 1 (measure first):** in the preview (`?preview=1`) at 1707x1067 and 2560x1600, screenshot Rendered then Picture and Picture (fitted) and compare the window areas of every layer with a window shape (`shade`, `glass_pic`/`Glass` parts, `glass_fx*`, `mist*`, `scan*`, `sheen`, `trimspill`). Write which layer is mis-registered and by how many px/units to the report. No code change in this step.
- [ ] **Step 2 (failing test):** an e2e test that, per frame mode, loads the page, reads each window-shaped layer's rendered box and mask/image source, and asserts the layer set and its box match the active mode (no rendered-only window layer in picture modes, no picture-only layer in rendered) and that switching Rendered -> Picture -> Rendered through the app's own settings write leaves each layer on the frame box (`.frame` rect) within 1 px.
- [ ] **Step 3:** fix the mis-registered layer(s) found in Step 1: use a picture-specific shade (export `shade_pic` from the picture's `window_mask_pic.png` via `export_ui_assets.py`, add it to `FRAME_IMAGES`, switch on `pic` in `FrameLayers`), or derive the layer's box from the active frame's own geometry, so every window feature follows the frame automatically. Keep the rendered path byte-identical.
- [ ] **Step 4:** `npx tsc --noEmit`, `npm test`, `npx playwright test e2e/frame-modes.spec.ts e2e/display-fit.spec.ts e2e/glass-fx.spec.ts e2e/panel-slab.spec.ts` pass; `py -3 -I tools/export_ui_assets.py --check` ok. Look at the screenshots again and report before/after.
- [ ] **Step 5:** commit only this task's files.

---

## Execution results (filled in 2026-11-04 on branch `fix/sol-review`)

Ruling on Task 12: `SOL-JARVIS&SYSTEM-review.md` is another reviewer's untracked document, so it was NOT edited or committed. The corrections to it live in this plan (the "Verification results" section above), and the finding-to-commit map is below.

| Finding(s) | Task | Commit(s) |
|---|---|---|
| #14 disk graph key; #15 hide VRAM graph (decision 3) | 1 | 6d27678, a05f2ab (fix round: settle when metrics arrive later) |
| #38/#39/#40 calendar bounds + sort | 4 | 75c9955 |
| #21 dial out-of-range step | 5 | 7ea3ba3 |
| #18 lock pulse once per move (+ cleared when the tick stops at tier 2+) | 6 | 48ce581, dfbe950 |
| #63 performance power-plan GUID | 2 | 0266cb1 |
| #59/#62 safe-integer ids + shared fixture | 3 | c7ce0bf |
| #60, #65-#69 runner/pipe shutdown | 8 | d8a91bd, 442dd36, bb2a6ac, f368825, 579c8b9, 10a3e69, a7479ca |
| #70 IMAP reply cap; #75 process snapshot; #64 WASAPI device release; #71 http log (decision 1) | 9 | bd5ce07, 47e1cb8, b362e82, de27ca7 |
| #72 live text cleanup; #74 one wake training | 7 | f0567ec, 34fdeb3 |
| #12/#42 exact match first; #28; #2; #5 | 11 | b5f9b7f |
| #31, #34, #7 (latent hygiene); #20 comment-only | 10 | d9d6706 |
| Window shading on Picture frames (user request) | 13 | 5226e0c |

Not done on purpose: #9 (autoFocus; the user is editing that input), #73 (decision 2), #36, all notes and withdrawn items.

### Follow-ups requested by the user after the review
| Request | Commit |
|---|---|
| The picture shade rebuilds itself when the window mask changes (`image_frame.py` calls it; `npm run gen` rebuilds only when stale; `npm test` fails with a clear message when out of date; hash kept in `src/assets/shade_pic.src.sha256`) | 38af726 |
| `test_jarvis.py` can be run safely through `Jarvis/tests/guarded_run.py` (tripwires on real process, delete outside temp, recycle bin, registry, lock, sleep calls): `test_jarvis.py` OK with 0 tripwires hit; `test_host_pipe.py` and `run_all.py` OK | b86c442 |
| `npm run build:check` builds into `node_modules/.build-check`, so a check never overwrites the deployed `dist` | 1322256 |
