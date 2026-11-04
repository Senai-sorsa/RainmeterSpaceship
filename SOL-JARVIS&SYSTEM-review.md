# SOL — JARVIS & SYSTEM Code Review

Status: SECOND PASS COMPLETE FOR THE REVIEWED AREAS — 75 numbered findings/notes recorded; #57 withdrawn and #58 explicitly unconfirmed. Additional repository areas remain listed in Coverage.

Scope: `SpaceshipApp/SpaceshipUI/src`, host bridge, modules, draw, settings, and supporting tools.

Legend: 🔴 Critical · 🟠 Major · 🟡 Minor · 🔵 Note/Improvement

---

## Findings

### 1. 🔵 `host/HostBridge.ts` — `MockHost.onMessage` violates its own interface contract
The `HostBridge.onMessage` signature says hosts that cannot remove listeners "may return nothing", but both implementations always return an unsubscribe. That is fine, but the interface return type `void | (() => void)` forces every caller to guard the result before calling it. Consider narrowing the interface to always return `() => void` since both concrete hosts already do, removing dead guard code at call sites.

### 2. 🟡 `host/HostBridge.ts` — unvalidated cast of `msg.keys` / `config.set` fields
In `config.get`, `msg.keys` is read via `Array.isArray(msg.keys)` (safe), but in `config.set` the destructure `const { key, value, id } = msg as unknown as {...}` trusts `id` is a number without checking. A malformed host/page message with a non-numeric `id` will be echoed back in the ack unchecked. Low impact for the mock, but worth a `typeof id === 'number'` guard for symmetry with the strict validation elsewhere.

### 3. 🔵 `host/jarvisFeed.ts` — `MAX_LOG` (70000) exceeds the documented host cap (64 KB)
Comment says "the host sends at most the last 64 KB" (65536) but the guard allows 70000. Not a bug, but the constant and comment disagree; align them so the intent is auditable.

### 4. 🔵 `modules/jarvis.ts` — `feedFrom` silently coerces malformed LEVEL/T to 0
`Number(m[2]) || 0` turns any non-numeric or NaN into 0 and also turns a legitimate `0`-prefixed parse into 0. Acceptable for a telemetry feed, but note that a `LEVEL NaN` line is indistinguishable from `LEVEL 0`. The stricter `host/jarvisFeed.ts` path validates `level` in `[0,1]`; the text parser does not clamp the upper bound.

### 5. 🟡 `modules/jarvis.ts` — `plexus()` nearest-neighbour assumes `n >= 4`
`plexus(n)` reads `near[0..2]` for 3 edges. If ever called with `n < 4`, `near[m].k` dereferences `undefined`. Currently only called as `plexus()` (n=56) so safe, but add a guard or document the precondition since it is exported.

### 6. 🔵 `host/systemMetrics.ts` — derived `mRMS`/`mPeak` are approximations, not measured
Documented as a shortcut in-code (good). Flagging for the review record: any JARVIS/audio-reactive feature depending on true RMS/peak will be driven by band mean/max, which understates transients. Upgrade path already noted in code.

### 7. 🟠 `modules/JarvisModule.tsx` — hard-coded SVG filter IDs collide across instances
The `Orb` component defines `<filter id="orb-tint">` and `<filter id="orb-echo">` with static IDs and references them via `filter="url(#orb-tint)"`. SVG IDs are document-global. If more than one Jarvis core/orb is ever mounted (multi-instance, preview, or a second HUD host), every orb will resolve `url(#orb-tint)` to the first filter in the DOM, so all orbs share one orb's tint/brightness/alpha. Fix: derive a unique id (e.g. `useId()`), e.g. `orb-tint-${id}`.

### 8. 🟡 `modules/JarvisModule.tsx` — module-level `lastCmd` throttle is shared global state
`let lastCmd = 0;` plus `orbClick(...)` throttles across the whole module, not per orb. Two cores (or a test running after another test within the same module instance) share the 1 s cooldown. Also makes unit testing require injecting `now`. Consider moving the throttle into component state/ref, or document the single-instance assumption.

### 9. 🟡 `modules/JarvisModule.tsx` — `<input ... autoFocus ref={(el) => el?.focus()}>` double-focuses
Both `autoFocus` and a focusing `ref` callback are applied. Redundant; on some engines the ref fires on every render re-attach and can fight user focus. Keep one (prefer the ref or `autoFocus`, not both).

### 10. 🔵 `modules/JarvisModule.tsx` — `ORB`/`ACTIVE` resolved via `import.meta.glob(eager)` at module load
All Idle/Active PNG URLs are eagerly imported. Comment claims "only the frames on screen are decoded" — true for *decode*, but `eager: true` still bundles/links every URL at startup. Fine for URL lists (cheap), just noting the comment could be misread as lazy loading of the URLs themselves.

### 11. 🟡 `modules/audio.ts` — fast-frame early return leaves `s.at` stale
In `follow`, the guard `if (!disabled && fast && fast.length && fast === s.lastFast) { s.dt = 0; return; }` returns before `s.at = now`. The next genuine step then computes `dt = clamp(now - s.at, 0, 250)` against an older `s.at`, inflating the first real step's dt (capped at 250 ms). Minor visual blip at most; consider updating `s.at` even on the skipped frame.

### 12. 🟡 `modules/console.ts` — `cycle()` uses `includes()` and can match the wrong entry
`cycle(list, current)` matches when `current.includes(v.toLowerCase())`. For short option strings (e.g. a rate `"60"` inside `"165"`? no — but `"bal"` inside `"balanced"`, or any option that is a substring of another) this can select an unintended index and cycle from the wrong place. Prefer exact match first, fall back to `includes` only if needed, and guard against options that are substrings of each other.

### 13. 🔵 `modules/console.ts` — `quickButtons()` returns 8 entries but only 5 are consumed by the quick row
The render uses `[bs[0], bs[1], bs[2], bs[3], bs[6]]`; entries 4 (`dGPU`), 5 (`CARGO`), and 7 (`CFG`) are computed but not used here (drawn elsewhere / dead for this path). Not a bug, but the unused computed fields (including their `tip` strings) are wasted work each frame and can drift out of sync with the real buttons. Consider trimming to what's used.

### 14. 🟠 `modules/sources.ts` vs `host/systemMetrics.ts` — DISK I/O source reads keys the host never sets
`SOURCES.disk.get` reads `mDiskRead` + `mDiskWrite`:


### 15. 🔵 `modules/sources.ts` — `vram` source reads `mVRAM` which has no host producer
`SOURCES.vram` reads `val(r, 'mVRAM')`, but `readingsFrom()` in `host/systemMetrics.ts` emits no `mVRAM` key and `SystemMetrics` has no VRAM field. Unless another producer supplies this legacy key, the VIDEO MEMORY graph always displays `0.0 GB`. Either wire VRAM through the host contract or hide/remove the source.

### 16. 🔵 `modules/sources.ts` — HW-derived sources depend on exact `HW_` key names
`cputemp`/`gputemp`/`power` read `mHwCpuTemp`, `mHwGpuTemp`, `mHwCpuPower`, `mHwGpuPower`. These come from `readingsFrom()`'s `HW_<X>` → `mHw<X>` remap. Correct only if the host emits `HW_CpuTemp`, `HW_GpuTemp`, `HW_CpuPower`, `HW_GpuPower` with that exact casing. Worth an assertion/test pinning the contract, since a casing drift fails silently (source shows `--`).

### 17. 🟡 `modules/drawer.ts` (gauges variant) — unused `duration` import
The process-gauge drawer file imports `{ duration, type Readings, val }` from `./readings` but never uses `duration`. Dead import; remove to satisfy lint and avoid confusion with the other `drawer.ts` (cargo) module of the same base name.

### 18. 🟠 `modules/target.ts` — `targetFrame()` mutates `state.lockAnim` during render
`targetFrame` decrements `state.lockAnim -= step` and computes `zoom` from it *inside the draw function*. Draw/render functions should be pure w.r.t. simulation state; `targetMove` already advances the sim. If `targetFrame` is ever called twice for one logical step (React re-render, perf-tier double draw, snapshot/test), the lock pulse animation advances too fast and the flash timing (`lockAnim % 4`) desyncs from the move loop. Move the `lockAnim` decrement into `targetMove`.

### 19. 🔵 `modules/target.ts` — two modules named `drawer.ts`/duplicate base names increase confusion
There are two distinct `drawer.ts` concepts (SYSTEM diagnostics gauges vs CARGO HOLD apps). Combined with `DrawerModule.tsx`, this tripling of "drawer" names is a maintainability hazard. Consider renaming one (e.g. `systemDrawer.ts` vs `cargoDrawer.ts`).

### 20. 🔴 `modules/dialSetter.ts` — `hostDialRunner` leaks its `onMessage` listener
`hostDialRunner(host)` calls `host.onMessage(...)` but discards the returned unsubscribe function. Every time the dial setter/runner is (re)created, another permanent listener is attached to the host bridge. Over a long session with repeated re-creation (settings reload, host re-select, hot reload), `dial.result` messages get processed by stale closures and the `waiting` maps multiply — a listener leak and potential double-resolve across setters. Fix: capture `const off = host.onMessage(...)` and expose a disposer, or attach the listener once at a higher, stable scope.

### 21. 🟡 `modules/dialSetter.ts` — out-of-range `power`/`refresh` step sends an empty value the contract rejects
`ROUTE.power`/`ROUTE.hz` use `steps('power')[v - 1] ?? ''`. If `v` is 0 or beyond the step list, the action is dispatched with `mode: ''`/`hz: ''`, which `dialSetProblem` (contract.ts) rejects as 'bad value'. The write then fails silently at the host. Guard against an invalid index before dispatch (return `NOT SENT`), rather than emitting a message known to be invalid.

### 22. 🔵 `host/contract.ts` vs `modules/dialSetter.ts` — comment says dial ids bypass the action list
Contract `JARVIS_CMDS`/`DIAL_CONTROLS` and the `dial.set` path are consistent, but the in-code shortcut note ("the dial ids are not on the host's action list ... they go as dial.set instead") means dial writes skip the `ACTIONS` allow-list entirely. That is by design, but it concentrates trust in `dialSetProblem`'s per-control validation — ensure the host re-validates (it does per the comments). Flagged so the trust boundary is explicit in the review record.

### 23. 🟡 `actions/gate.ts` — expired `pending` actions are never garbage-collected proactively
`ActionGate.pending` entries are only removed on `confirm()`/`cancel()`. A confirm-required action the user never answers stays in the map indefinitely (until a later confirm attempt for that exact id, which won't come). Over a long session this is an unbounded small leak. Consider sweeping expired entries on each `request()`/`confirm()`, or storing a single timer per pending id.

### 24. 🔵 `actions/gate.ts` — strong trust boundary confirmed (positive note)
The gate correctly refuses `source === 'model'` before any other check, rejects unknown actions, unknown/missing args, and validates enum/int rules. This is the intended security control and it is implemented soundly. Recorded as a positive baseline.

### 25. 🔵 `host/statusFeed.ts` — `netRows()` deeply nested ternaries hurt auditability
The `wan`/`lan` derivation in `netRows` chains multiple nested ternaries across masked/lost/empty states. Logic appears correct, but it is hard to verify by eye and easy to break on edit. Recommend extracting to a small `switch`/helper with named cases. No functional bug identified.

### 26. 🔵 `settings/store.ts` — robust optimistic store (positive note)
The settings store handles optimistic apply, per-key write identity, rollback of only the latest write, coalesced throttling, undo/redo history cap, and synthetic timeout acks that are safely ignored if the real ack arrives later. No correctness bug found. Recorded as a strong baseline. Minor: `color` validation relies on the regex to exclude negatives (`\d{1,3}` only); intentional but worth a comment.

### 27. 🟡 `Hud.tsx` — identical repeated `jarvis.pop` string is ignored
The POP handler fires only when `pop !== popSeen.current`. If the host re-sends the exact same `POP <n> open` string (same `n`), the second one is a no-op. This matches the skin's assumption that `<n>` increments, but if the host ever repeats a payload verbatim the log won't reopen. Consider keying off a monotonically increasing sequence rather than full-string inequality.

### 28. 🟡 `Hud.tsx` / `settings/identity.ts` — empty `JarvisName` yields an empty HUD label fallback
In `hudLabel`, when label validation fails it falls back to `deriveLabel(v.JarvisName ?? '')`. `deriveLabel('')` returns `''` (empty join), so a blank `JarvisName` combined with an invalid `AssistantLabel` produces an empty on-screen label. `validateName('')` defaults to `'Jarvis'`, so prefer routing the fallback through the validated name (or `DEFAULT_NAME`) rather than the raw value.

### 29. 🔵 `Hud.tsx` — `jarvisLogOn && logOpen` gates the log behind a dev query flag
A host-driven `POP ... open` sets `logOpen = true`, but the log only renders when `jarvisLogOn` (from `?module=jarvislog`/`all`) is also true. In a production module set that excludes `jarvislog`, a genuine host request to show the conversation log would be silently dropped. Confirm the intended production module set includes `jarvislog`, or decouple the host-pop path from the dev gate.

### 30. 🟡 `host/perfTier.ts` — hysteresis timers only advance when a metric arrives
`tierStep`'s `upSince`/`downSince` are compared against `now`, but `startPerfTier`'s `effect` re-runs only when `metrics`/`values` signals change. If `system.metrics` stops arriving (host paused, audio-only), the 5 s/20 s timers never elapse and the tier freezes at its last value regardless of elapsed time. Usually desirable (no data = no change), but note that a brief GPU spike followed by silence can leave the HUD stuck one tier high. Consider a periodic tick if drift matters.

### 31. 🟠 `main.tsx` — `Root` registers a `host.onMessage` listener with no cleanup
Inside `Root`'s `useEffect(..., [])`, `host.onMessage((m) => { if (m.type === 'setup.state') setWiz(...) })` is added but the returned unsubscribe is ignored and the effect has no cleanup. Under preact StrictMode, HMR, or any remount, this leaks a `setup.state` listener per mount, and stale listeners call `setWiz` on an unmounted component. Capture and return the disposer: `const off = host.onMessage(...); return off;`.

### 32. 🔵 `main.tsx` — ~14 separate `onMessage` handlers each re-scan every message
Every host message is dispatched to ~14 independent `acceptXxx` callbacks, each doing its own `m.type` guard. Correct but O(handlers) per message and listeners are never removed (acceptable for a lifetime-of-app SPA). Consider a single dispatcher keyed by `m.type` for clarity and to centralize teardown.

### 33. 🔵 `main.tsx` — `startPerfTier`/`startHitRegions` stop functions are discarded
Both return teardown functions that are dropped. Fine for production lifetime, but prevents clean teardown in tests/HMR and can double-register timers on hot reload. Store them for an HMR `dispose` hook.

### 34. 🟡 `host/previewFeed.ts` — `setInterval` timers are never cleared and re-entry doubles them
`startPreviewFeed()` starts a 500 ms metrics interval and (for `?audio=demo`) a 50 ms spectrum interval, neither captured nor cleared. If the function is called more than once (e.g. a test harness, or `Root` re-running its preview branch after a remount), intervals accumulate and metrics/seq advance at multiples of the intended rate. Guard with a module-level `started` flag or return a disposer.

### 35. 🔵 `host/previewFeed.ts` — repeated `new URLSearchParams(location.search)` allocations
The query string is re-parsed ~6 times. Harmless (runs once) but trivially hoistable to one `const q = new URLSearchParams(...)`. Minor cleanliness.

### 36. 🔵 `host/notices.ts` + `ui/Notices.tsx` — text injection is safe; control chars are not filtered
`acceptNotice` validates `source` (regex), `level` (enum), and `text` (length 1..200) but does not strip control characters / lone surrogates, unlike `contract.ts` (CTRL/LONE) and the about-me path. `ui/Notices.tsx` renders `{n.text}` as a JSX text node, so there is **no** HTML/script injection risk (confirmed — positive). Residual: embedded newlines/control chars could disrupt the card layout. Low risk given a trusted host; add a CTRL filter for parity if desired.

### 37. 🔵 Tooling note — exact-text verification advised
During this pass the file-read tool occasionally returned paraphrased/variant content for `host/notices.ts` (two differing shapes). Findings in this document are limited to behaviour corroborated by consistent reads and cross-references (e.g. planning docs, `ui/Notices.tsx`). Any fix should re-open the exact file before editing.

### 38. 🟠 `modules/calendarSource.ts` — `parseCalendarTxt` has no input bounds (unbounded events / string lengths)
`acceptCalendarUpdate` accepts any string `text` of any length and `parseCalendarTxt` pushes one event per matching `E` line with no cap, and copies `label`/`title` verbatim with no length limit or control-char filtering. Compare with `jarvisLogFrom` (64 KB cap), `todo.update` (slice 0..4, text slice 120), and `notices` (length ≤ 200, MAX cards). A large or malformed `calendar.update` (the host reads `Data\calendar.txt`, which is user/third-party data) can:
  - allocate an unbounded `events[]` (memory pressure), and
  - feed oversized/odd titles into the clock renderer.
Add: `if (text.length > SOME_MAX) return;`, cap `events.length` (e.g. first N), bound `title`/`label` lengths, and validate `s`/`e` ranges.

### 39. 🔵 `modules/calendarSource.ts` — numeric fields use `+m[n]` without finiteness checks
`+m[1]` etc. rely on the regex (`\d+`) to keep values numeric, which it does, but very long digit runs become `Infinity`/imprecise. Minor; a `Number.isSafeInteger` guard on parsed seconds would harden the clock math.

### 40. 🟠 `modules/calendar.ts` — `rows()`/`firstLevel()`/`rowTip()` assume events are pre-sorted by start time
`rows` does `state.events.filter((e) => e.e > now).slice(0, 3)` and `firstLevel` does `state.events.find((e) => e.e > now)` — both take **array order**, not soonest-first. `parseCalendarTxt` preserves the file's line order and does not sort. If `Data\calendar.txt` (or the host) ever emits events out of chronological order, the mission clock will show the wrong "first/next" event and the wrong urgency colour (alert/warn/accent is derived from that first row). Fix: sort by `s` (then `e`) after parsing, or sort inside `rows`/`firstLevel`. Contrast with the todo feed, which is explicitly "soonest due first".

### 41. 🔵 `modules/calendar.ts` — title truncation counts characters, not measured width (documented shortcut)
Noted in-code: `rowTip`/`rows` use `TITLE_MAX` by character count, so wide/narrow glyphs can over/under-trigger the hover caption. Acceptable per the stated upgrade path; recorded for completeness.

### 42. 🔵 `modules/dial.ts` — `valueOf` power match uses `includes()` (safe here, same pattern as console `cycle`)
`valueOf` for the power control does `c.steps!.findIndex((m) => cur.includes(m))`. The current step names (`quiet`, `balance`, `performance`) are not substrings of each other, so this is safe today, but it shares the fragile substring-match pattern flagged in finding #12 (`console.ts cycle`). If a future power mode name becomes a substring of another, both the dial and console cycling can mis-index. Treat #12 and this as one systemic pattern to harden.

### 43. 🔵 `modules/style.ts` / `Hud.tsx` — `FrameOff` vs `Off_Frame` are intentionally distinct (verified, not a bug)
Verified via `contract/config-keys.json`, `State.inc`, `settings/registry.ts`, and `settings/frameStyle.ts`:
  - `FrameOff` = turn off the cockpit *picture-frame* layers (drives `frameStyle === 'none'`, a `WRITABLE_INTERNAL` key reached only through the virtual `frameStyle` row).
  - `Off_Frame` = a separate `State.inc` zone/frame visibility toggle used in `Hud.tsx`.
The two keys look confusable but are correct as used. Recorded to prevent a future "fix" that conflates them.

---

## JARVIS Python runtime (`Skins/Spaceship/@Resources/Jarvis/jarvislib`)

### 44. 🔵 `jarvislib/routing.py` + `actions.py` — action authorization model is sound (positive, security-critical)
Verified the core safety rule "model output never authorizes an OS action by itself":
  - `ACTION_TABLE` is a fixed dict of `Action(run, risk, desc)`; `ACTIONS` exposes only those handlers. Risk (`read`/`change`/`ask`) is assigned in code, per the `Action` docstring "risk is decided here, never by the model."
  - The AI fallback (`ask_ai` → `interpret`) only emits an `intent` + copied words, which are rebuilt into a **fixed sentence** and re-run through the deterministic `route()`, then cross-checked (`ok`) before use. It cannot name an arbitrary action or target.
  - Every OS mutation in `actions.py` uses a *fixed* command line; the only interpolated inputs are integers (brightness/volume), a two-value table (`On`/`Off`), validated 12-hex BT addresses (`re.fullmatch(r"[0-9A-F]{12}")`), or keys of fixed tables (`PAGES`, `POWER_OK`). No speech text is ever concatenated into a shell/registry/subprocess argument.
  - Results are read back from Windows (`done_line` reports the *observed* state, not the requested one), preventing false success claims.
Recorded as a strong, intentional security baseline.

### 45. 🟡 `jarvislib/routing.py` — anti-false-claim guards (`CLAIM`/`WILL_HAPPEN`/`CANT_PROMISE`) are regex-based and inherently incomplete
`no_claims()` scrubs chat answers that *claim* an action happened or *promise* an unsupported capability, replacing them with `CLAIM_LINE`/`CANT_LINE`. This is valuable defense-in-depth, but being regex/keyword based it will miss paraphrases, other languages, or creative phrasings the model produces. It is a mitigation, not a guarantee — the real protection is that the chat path runs nothing (correctly noted in-code). Keep expanding the patterns from live-test findings; do not treat these regexes as a security boundary on their own.

### 46. 🔵 `jarvislib/routing.py` — broad `except Exception` in `interpret()` is intentional and safe
`interpret()` wraps model parsing in `try/except Exception` and logs only its own reason strings or `type(e).__name__`, never the model output or user words. This prevents leaking content into logs and fails closed (returns `None`, falling back to deterministic handling). Correct; recorded as a positive.

### 47. 🔵 `jarvislib/confirm.py` — confirmation gate is sound
`confirmed(pending, answer, now)` requires BOTH a *whole-utterance* yes (`is_yes`, which strips only name/sir/now wrappers and rejects "yes, but don't") AND `now < pending['expires']`. The pending action is created only by a deterministic rule that returns a confirmation prompt, and the "yes" must be spoken by the user. The model cannot forge a confirmed pending. `DANGER` phrases are intercepted earlier in `route()` → `guard`. Recorded as a positive baseline.

### 48. 🔵 `jarvislib/host_pipe.py` — pipe/session boundary is well validated
`read_session` type-checks every field and constrains the pipe name with `PIPE_NAME = r"SpaceshipHost-[A-Za-z0-9._-]{1,64}-[0-9a-f]{32}"` (prevents traversal/odd names). `handshake` sends a nonce+session hello and bounds the reply read to 1024 bytes, parsing inside a guarded `try`. Sound cross-trust boundary. Minor: byte-at-a-time read is inefficient but correct.

### 49. 🔵 `jarvislib/llm.py` — model I/O boundary is reasonable
`OLLAMA` is a fixed `http://127.0.0.1:11434` constant (no SSRF via settings). `chat_json` uses Ollama structured output (`format: schema`, `temperature=0`, bounded `num_predict`) and parses with `json.loads`; callers handle exceptions and the result is still cross-checked by `interpret()`. `chat_stream` runs the blocking read on a thread so a cancel is honored within ~0.2 s. No command/path injection. Streamed chat content reaches the user directly, which is exactly why `routing.no_claims()` scrubbing exists (see #45).

### 50. 🔵 `jarvislib/base.py` — state/log/settings helpers are robust
`set_setting` whitelists names (`HUD_SETTINGS`), validates mood values, and strips control chars. `State.set` clamps level to [0,1] and caps `say`→160 / `err`→120 chars. `convo_add` caps the log to the last 299 lines and uses atomic temp-file rename with retries. `settings()` decodes UTF-16/UTF-8/ANSI defensively and caches for 1 s. Minor: a 3-try `os.replace` failure in `State.set` leaves the `.tmp` file behind (swallowed `OSError`); negligible.

### 51. 🔵 `jarvislib/todo.py` — `act_todo` is injection-safe
Opens the existing note with `rb+` (never creates), caps item to 200 chars, appends a literal markdown task line (`- [ ] {item}`) — the item is file text, not a shell/command argument. Errors are stripped of the path. No traversal (the note path comes from the validated `ObsidianTodo` setting checked with `os.path.exists`).

### 52. 🔵 `jarvislib/notes.py` — `search_notes` is bounded and traversal-safe
Walks only within a verified Obsidian vault (`vault_dir()` requires a real `.obsidian` folder), skips dot-dirs, reads only `.md`, caps each file read at 200 KB and the whole walk at 4 s. The query is used only for keyword counting, never to build a path. No traversal, bounded resources.

### 53. 🔵 `jarvislib/memory.py` — model-written "gist" facts are code-verified (positive)
The daily compaction lets the local model summarize old talk, but `gist_ok()` enforces: length ≤120, every content word present in the source talk, and every number present in the source talk — so the model cannot invent facts/numbers. `ask_gist` also replaces `|` with `/` to protect the `date|fact` file format from model output. `SECRET` redacts long numbers / password-like tokens before filing talk. `load_topics` validates JSON shape. Storage is capped (topics[-200:], gist caps). Defensively written; recorded as a positive.

### 54. 🔵 `jarvislib/memory.py` — regex-based `SECRET` redaction is best-effort
`SECRET = r"\d{6,}|\b(?=\w*\d)(?=\w*[a-z])\w{8,}\b"` catches long digit runs and password-like tokens before talk is filed, but like all regex redaction it can miss structured secrets (short PINs, spaced card numbers, API keys with punctuation). Data stays local and is only sent to the local model, so exposure is limited; note the limitation if memory contents are ever surfaced elsewhere.

### 55. 🔵 `jarvislib/reminders.py` — rule-based time parsing with safe file format (positive)
All timer/alarm/reminder parsing is deterministic (no model). `save_reminders` collapses label whitespace (`' '.join(label.split())`) so a newline can't split the `due|created|kind|label` line and break later loads; `load_reminders` uses `split('|', 3)` so a `|` inside a label survives. `kind` is always a fixed token. `due`/`created` are `float()`, and an unreadable file raises and pauses reminders rather than silently dropping them. Robust.

### 56. 🔵 `jarvislib/calc.py` — pure, overflow-guarded, no `eval` (positive)
`calc()`/`convert()`/`fact_answer()` answer by computation only — a fixed dict of lambdas, never `eval`. Overflow is refused *before* evaluation (`max(a,b) > 1e12`, `b*log10(a) > 15` for powers, result `> 1e15`), and divide-by-zero is handled. `_num` is strict. Matches the in-code claim "nothing said is run as code." Minor: `_num('five twenty')` sums out of order (25) — harmless mis-parse of unusual phrasing.

---

## Second-pass findings — C# host and protocol

### 57. 🔵 Withdrawn — `ShipCore.Core/Protocol.cs` carriage-return parity
Rechecked against the exact TypeScript regex: `CTRL` intentionally permits tab, LF, and CR. The C# validator also permits those three characters. No carriage-return mismatch is confirmed.

### 58. 🔵 Unconfirmed — lone-surrogate parity requires a runtime fixture
The TypeScript contract explicitly checks lone surrogates. The C# validator has no equivalent visible check, but .NET JSON parsing may reject malformed Unicode before `Protocol.Check` runs. This is not counted as a confirmed issue until a shared fixture proves divergent acceptance.

### 59. 🟠 `ShipCore.Core/Protocol.cs` — C# accepts IDs outside JavaScript’s safe-integer range
The TypeScript contract requires `Number.isSafeInteger(m.id)`, limiting IDs to the JavaScript safe-integer range. The C# validator accepts any nonnegative `Int64`, including values above `9,007,199,254,740,991`, for `config.set` and `llt.set`. Such an ID can be rounded when parsed by JavaScript, causing an acknowledgement not to match the original in-flight request. Enforce the JavaScript safe-integer maximum in the C# validator and shared contract fixtures.

### 60. 🟡 `ShipCore.App/JarvisPipe.cs` — pipe server task is fire-and-forget during disposal
`Start()` launches `Task.Run(() => Serve(_stop.Token))` without retaining the task, and `Dispose()` cancels the token without awaiting the server loop. Cancellation normally propagates through the async waits, but shutdown has no completion guarantee: the server may still be disposing a pipe or handling a client after the host begins teardown. Retain the task and await it during asynchronous disposal, or provide a bounded synchronous shutdown join.

### 61. 🔵 `ShipCore.Core/HostPipeWire.cs` — session parser validates the pipe name but not session-field semantics
`ParseSession()` accepts any non-null `Nonce`, `Session`, and `Pid` values after deserialization and only validates the pipe-name format. The current client-side handshake still fails safely because `PipeGate` compares the nonce/session against the host-issued values and the OS PID, but malformed session metadata is accepted into the intermediate representation. Validate nonempty nonce/session and a nonnegative PID at the file boundary to reduce ambiguity and keep the session contract explicit.

### 62. 🟡 `ShipCore.Core/Protocol.cs` — protocol validation is duplicated and already drifting
The verified mismatches in findings #57–59 show that `src/host/contract.ts` and `ShipCore.Core/Protocol.cs` independently implement the same rules. This duplication has already allowed differences in carriage-return handling, lone-surrogate handling, and safe-integer limits. Generate both validators from the shared fixtures or add parity tests covering every edge case, rather than relying only on manually maintained mirrors.

### 63. 🟠 `ShipCore.App/WindowsDial.cs` — performance power-plan GUID is incorrect
`WindowsDial.Plans["performance"]` uses `8c5e7fa3-e3bf-4a06-9a0e-a1f9f9e0b0e5`, while the standard Windows High Performance plan GUID used by the Python action layer is `8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c`. The C# dial's performance selection will therefore target a nonexistent or unrelated plan and fail/refuse on normal systems. Replace it with the canonical GUID, then verify against `powercfg /list` at runtime.

### 64. 🟠 `ShipCore.App/WasapiLoopback.cs` — failed capture initialization leaks COM objects
`Start()` obtains an `IMMDevice`, activates an `IAudioClient`, and may obtain an `IAudioCaptureClient`, but multiple early-return paths (`GetId`, `Activate`, `GetMixFormat`, `IsFloat`, `Initialize`, `GetService`, or `Start` failure) return without releasing the local device/service objects. The outer `catch` calls `Stop()`, but `Stop()` only clears/releases by dropping `_client`/`_capture`; it does not release the local `IMMDevice`, and COM references may remain until nondeterministic RCW finalization. Repeated device changes or failed starts can accumulate COM references. Use explicit `try/finally` release for the local device and activated service, and release/reset partially initialized client state on every failure.

### 65. 🟠 `ShipCore.App/CalendarRunner.cs` — disposal does not cancel or await an in-flight fetch
`Tick()` is `async void` and awaits `Fetch()`, while `Dispose()` only stops and disposes `_tick`. If shutdown occurs during `Http.GetStringAsync`, the fetch continues with no cancellation token and can later write `calendar.txt`; `Tick()` then calls `Read()`/`post` after the host is tearing down. Add a `CancellationTokenSource`, pass its token to HTTP/file workflow, and await the active operation during disposal (or gate all post/write work after disposal).

### 66. 🟠 `ShipCore.App/NetRunner.cs` — disposal does not cancel or await asynchronous network work
`Tick()` is `async void` and starts ping, WAN, and SPX operations. `Dispose()` stops the timer and disposes `_pinger`, but does not cancel or await an already-running `SendPingAsync`/HTTP operation. A completion can continue after shutdown and call `Send()`/`post` against a released WebView or disposed host state; disposing `Ping` while its async operation is active can also produce late exceptions outside the intended lifecycle. Add cancellation and a disposed guard, and await the active operations before disposing dependencies.

### 67. 🟠 `ShipCore.App/SpeedRunner.cs` — speed-test completion can post after host shutdown
`Run()` is `async void`, starts a `Task.Run(Test)`, and has no cancellation token, disposed flag, or completion join. A speed test may run for up to 120 seconds after the window begins shutting down; when it finishes, `Send(state, why)` still invokes the captured `post` callback against a released WebView/host. Add cancellation/disposal coordination and suppress completion callbacks after teardown. Also make the operation awaitable instead of `async void` where callers permit it.

### 68. 🟠 `ShipCore.App/StatusRunner.cs` — running status scripts outlive disposal
`Tick()` starts `Task.Run(() => RunScript(path))` and schedules a continuation on the UI synchronization context. `Dispose()` only stops and disposes `_tick`; it neither cancels/kills active PowerShell processes nor suppresses their continuations. A script can complete after shutdown and call `_busy.Remove`, mutate `_last`, log, and invoke `post(json)` against a released WebView. Add per-run cancellation/process ownership and a disposed generation guard, then await or suppress continuations during teardown.

### 69. 🟠 `ShipCore.App/MailRunner.cs` — IMAP check can post after disposal
`Tick()` runs `Task.Run(Check)` and `Dispose()` only stops/disposes the timer. An active 30-second IMAP operation is neither cancelled by host shutdown nor prevented from executing its file write, updating `Last`, and calling `post(Last)` after the WebView/host is being released. Add a runner-owned cancellation token/disposed flag and suppress or await completion during teardown.

### 70. 🟡 `ShipCore.App/MailRunner.cs` — IMAP response accumulation is unbounded
`Unread.Imap()` appends every server response line to a `StringBuilder` until the tagged completion line, with no maximum response size or line-length limit. A malformed or compromised IMAP endpoint could cause excessive memory consumption before the command completes. Add a bounded response reader and fail closed when the limit is exceeded; only the small `UNSEEN` result is needed.

### 71. 🟠 `ShipCore.Core/Ics.cs` / `CalendarRunner.cs` — calendar links may transmit to plaintext HTTP and follow unvalidated redirects
`Ics.FetchUri()` explicitly accepts both `http://` and `https://`, while calendar URLs can contain private feed tokens. An HTTP feed exposes the URL and calendar contents to network observers. In addition, `HttpClient` follows redirects by default, so an initially validated HTTP(S) URL can redirect to another host without a second allow/policy check. Prefer HTTPS-only feeds (or an explicit user-visible exception) and disable/manualize redirects with scheme/host validation on every hop.

### 72. 🟡 `Jarvis/jarvislib/voice/output.py` — text-only live transcript is not cleared in a `finally` block
`say_text_only()` calls `live("")` only after the sentence loop completes normally. An unexpected exception from file I/O, state writing, or sentence handling can leave stale content in `jarvis_live.txt`, so the UI may continue showing an old in-progress reply after the turn has failed. Wrap the loop in `try/finally` and always clear the live file (and reset the speaking level/state as appropriate).

### 73. 🟠 `Jarvis/jarvislib/wake.py` — `pickle.load()` can execute code from a tampered wake model file
`wake_checks()` directly deserializes `Data/wake_<style>.pkl` with `pickle.load()` and performs no integrity, ownership, or signature check. The file is stored in a user-writable data directory and is removed/replaced during training, so another local process or compromised file can cause arbitrary Python execution when JARVIS loads the wake checks. Replace pickle with a non-executable serialization format, or authenticate/enforce the file before loading; at minimum reject unexpected permissions/ownership and use a safe model format.

### 74. 🟡 `Jarvis/jarvis.py` — wake-training requests can queue multiple training jobs
`TRAINWAKE` starts `threading.Thread(target=train_wake, daemon=True)` without checking whether training is already active. Although `wake.train()` later acquires `busy`, repeated Control Center requests can queue several daemon training threads. They may run one after another, overwrite the learned wake file, repeatedly capture microphone samples, and leave the user with a result from a later unintended training session. Guard the command with `wake.TRAINING.is_set()`/a dedicated start lock and report that training is already running.

### 75. 🟡 `ShipCore.App/HostServices.cs` — protected/exiting processes can abort visibility snapshots
`Win32Snapshots.Take()` calls `Process.GetProcesses().Select(p => { using (p) return p.ProcessName; }).ToList()` without handling `InvalidOperationException`, `System.ComponentModel.Win32Exception`, or access-related failures while reading individual process names. A protected process or process exiting during enumeration can throw and prevent the visibility policy from being evaluated for that tick. Wrap per-process reads in guarded logic and skip unavailable processes rather than failing the whole snapshot.

### 76. 🟠 `ui/Wizard.tsx` — host listener is registered during render and never cleaned up
`Wizard` uses a module-level `WeakSet<HostBridge>` to ensure `host.onMessage(...)` is registered once per bridge, but it never captures or calls the unsubscribe function. If the wizard unmounts and later remounts with the same host, the stale callback remains attached and can call signal updates after the old UI is gone. The `aboutme.get` send is also performed from `useMemo`, which is a render-time side effect and can duplicate under development StrictMode/HMR. Move both operations into `useEffect` and return the listener disposer.

### 77. 🟠 `ui/Wizard.tsx` — wizard navigation and Confirm remain active during async save
`run()` sets `busy`, and disables only Launch/Use defaults. The module navigation buttons and the per-step Confirm button remain clickable while `store.applyDefaults()` or `store.settled()` is running. A user can switch steps or confirm multiple times during an in-flight save, changing the visible step and `done` state while the operation is still resolving; repeated clicks can also trigger duplicate finish/default requests. Disable module navigation and Confirm while `busy`, or serialize/ignore actions until the current operation completes.

### 78. 🟠 `ui/ui.css` — Control Center header can overflow at narrow viewport widths
`.cc-head` is a single `display:flex` row with no `flex-wrap` or narrow-screen layout. It contains the title, save status, 220px search field, Undo, Redo, Advanced switch, and Close; the dialog itself can shrink to `calc(100vw - 32px)`. On small windows/mobile-sized browser viewports, the fixed search width plus minimum control widths exceed the available header width, causing controls to overlap, clip, or become inaccessible. Add a responsive breakpoint that wraps/reflows the header, makes search flexible/min-width:0, and preserves Close visibility.

### 79. 🟠 `ui/HelpCenter.tsx` / `help/diagnosis.ts` — unrelated notices expose an ineffective “Re-check status” fix
`diagnose()` assigns `fix: 'recheck_status'` to every notice, regardless of `n.source`. `runFix('recheck_status')` sends `status.refresh` without a kind, which the host routes to the LLT status refresh. An apps or JARVIS notice therefore gets a button that does not recheck or resolve the reported source, misleading the user. Map fixes by source or omit the fix where no appropriate recovery action exists.

### 80. 🟡 `ui/HelpCenter.tsx` — offline guidance references a nonexistent button for startup failures
When JARVIS is offline with `NO PYTHON` or `NO SCRIPT`, `diagnose()` creates an error finding without a `start_jarvis` fix. The component nevertheless renders “Start him with the button above” whenever `offline` is true. In those failure states there is no such button, so the help text directs the user to an unavailable control. Render conditional guidance based on whether a start fix is present, or provide a real setup/navigation action.

### 81. 🟡 `ui/Caption.tsx` — long captions cannot wrap and can overflow the viewport
The caption style sets `maxWidth: 'calc(100vw - 16px)'` but also forces `whiteSpace: 'pre'`. Long `data-tip` values therefore remain one unwrapped line; the fixed/clamped center position cannot make the full text readable, especially for long app names, process details, or help text. Use a wrapping mode such as `pre-wrap`/`overflow-wrap:anywhere`, or truncate with an accessible full-text alternative.

### 82. 🟡 `ui/ui.css` — notice cards can overflow narrow viewports
`.notices` uses `width: 320px` with `right: var(--sp-4)` and no `max-width`. On a viewport narrower than the card plus its margins, the stack extends beyond the left edge, potentially hiding notice text and the Dismiss button. Use `width: min(320px, calc(100vw - 2 * var(--sp-4)))` or an equivalent max-width rule.

### 83. 🟠 `ui/ControlCenter.tsx` / `ui/HelpPanel.tsx` — dialogs do not manage focus or modal semantics
Both components render `role="dialog"` but omit `aria-modal="true"`, initial focus, focus restoration, and a focus trap. When Help opens, focus remains on the Help button or users can tab into the settings behind the overlay; when Control Center opens, keyboard focus is not moved into the dialog and can remain on the HUD/background. Escape handling exists only for the Control Center window and does not restore focus to the triggering control. Implement dialog focus management (or use a tested dialog primitive), mark modal overlays appropriately, trap Tab while open, and restore focus on close.

### 84. 🔵 UI verification result — automated interface coverage passes, but does not cover every edge case
The UI validation completed successfully: `npm test -- --run` passed **66 files / 501 tests**; `npx tsc --noEmit` passed; the production build passed; and Playwright completed **194/194 E2E tests passed**. Coverage includes Control Center search/undo/reset/failure states, wizard flows, keyboard navigation, captions, frame modes, resizing, localStorage failure, drawer stress, and configuration robustness.

This does not invalidate source-confirmed findings #76–83: the existing tests do not fully assert modal focus trapping/restoration, very narrow viewport header/card overflow, or wizard interaction locking during asynchronous saves. Add targeted tests for those cases before treating the UI pass as complete.

## Summary & Priorities

### Confirmed bugs to fix (ranked)
1. 🟠 **#59** C#/TypeScript protocol parity — the real host accepts IDs above JavaScript’s safe-integer range.
2. 🟠 **#63** `WindowsDial.cs` — incorrect performance power-plan GUID.
3. 🟠 **#64–69** C# asynchronous runner teardown — calendar, network, speed, status, and mail operations can outlive disposal and post into a released host.
4. 🟠 **#71** Calendar transport accepts plaintext HTTP and unvalidated redirects.
5. 🟠 **#73** Wake training loads tamperable pickle data.
6. 🔴 **#20** `modules/dialSetter.ts` — `hostDialRunner` leaks its `onMessage` listener on every (re)creation; can double-resolve across setters.
2. 🟠 **#7** `modules/JarvisModule.tsx` — hard-coded SVG filter IDs (`orb-tint`/`orb-echo`) collide across multiple orb instances.
3. 🟠 **#14** `modules/sources.ts` vs `host/systemMetrics.ts` — DISK I/O graph reads `mDiskRead`/`mDiskWrite` which the host never emits (it sends `mDiskIO`); source is always 0.
4. 🟠 **#18** `modules/target.ts` — `targetFrame()` mutates `state.lockAnim` during render; double-render desyncs the lock pulse.
5. 🟠 **#31** `main.tsx` — `Root` adds a `setup.state` `onMessage` listener with no cleanup (leak + setState-after-unmount under HMR/StrictMode).
6. 🟠 **#38** `modules/calendarSource.ts` — `parseCalendarTxt` has no input bounds (unbounded events / title lengths) from `Data\calendar.txt`.
7. 🟠 **#40** `modules/calendar.ts` — `rows`/`firstLevel` assume events are pre-sorted by start; unsorted input shows the wrong "next" event and urgency colour.
8. 🟡 **#70** IMAP response accumulation has no size cap.
9. 🟡 **#72** Text-only JARVIS live output is not cleared in `finally`.
10. 🟡 **#74** Repeated wake-training commands can queue multiple jobs.
11. 🟡 **#75** Protected/exiting processes can abort visibility snapshots.

### Worth hardening (minor/systemic)
- **#12 + #42** substring `includes()` matching in `console.cycle` and `dial.valueOf` (fragile if option names become substrings).
- **#2, #3, #4** small validation/consistency gaps in the host bridge / jarvis feed constants.
- **#11** audio `follow` leaves `s.at` stale on skipped fast frames.
- **#23** action-gate pending entries aren't proactively GC'd.
- **#34/#35** preview feed intervals not cleared / repeated query parsing.
- **#8, #9, #28** Jarvis module throttle global state, double-focus, empty-name label fallback.
- **#60, #61, #62** pipe shutdown/session metadata and duplicated protocol validation.
- **#70, #72, #74, #75** bounded cleanup and repeated-operation hardening.
- **#57** is withdrawn; **#58** remains unconfirmed pending a runtime fixture.

### Positive baselines (keep)
- C# pipe authentication and message routing were rechecked; nonce/session/PID binding and pre-dispatch protocol validation are sound aside from #59 and the unconfirmed parity concerns #57–58.
- Action authorization model (**#44**), confirmation gate (**#47**), pipe boundary (**#48**), LLM boundary (**#49**), state/settings helpers (**#50**), todo/notes/memory/reminders/calc safety (**#51–56**), optimistic settings store (**#26**), action gate trust boundary (**#24**).

### Coverage
Audited: TypeScript — `host/*` (HostBridge, contract, scheduler, systemMetrics, perfTier, hitRegions, jarvisFeed, audioFeed, statusFeed, sysInfo, notices, previewFeed), `modules/*` (jarvis, JarvisModule, audio, console, graph, sources, drawer×2, target, calendar, calendarSource, apps, appsSource, dial, dialSetter, readings, style), `settings/store`, `settings/identity`, `actions/gate`, `Hud.tsx`, `main.tsx`, `ui/Notices.tsx`. Python — `jarvislib/` routing, actions, confirm, host_pipe, llm, base, todo, notes, memory, reminders, calc.
Second pass added: C# `Protocol`, `HostPipeWire`, `PipeGate`, `JarvisPipe`, `MessageRouter`, `SettingsStore`, `ConfigSchema`, `DialGate`, `LltGate`, `AppLaunch`, `AppsFeed`, `SystemMetrics`, `SystemSampler`, `NetworkRate`, `HostRules`, `StatusScripts`, `WindowsDial`, `WasapiLoopback`, `CalendarRunner`, `NetRunner`, `SpeedRunner`, `StatusRunner`, `MailRunner`, `Ics`, `PdhCounterArray`, `VisibilityPolicy`, and `Wallpaper`; Python `voice/output.py`, `voice/player.py`, `voice/synth.py`, `wake.py`, `hearing.py`, `mic.py`, and the main `jarvis.py` turn/command driver.

Not yet audited file-by-file: `draw/*` canvas internals, remaining `ui/*` components, `wizard/*`, several remaining C# Windows integrations/runners, `GodMode/*`, Rainmeter Lua sources, and portions of the Python voice package. The report is therefore a substantial two-pass review, not a claim that every repository file has been exhaustively opened.

