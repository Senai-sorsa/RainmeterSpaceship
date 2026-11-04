# JARVIS review

## Scope and status

- Review the JARVIS runtime and its Rainmeter, host-process, and UI integrations.
- **Status:** Static review is continuing. The latest pass also checked command polling, wake-loop recovery, microphone handling, LLM startup, and related host command writers.
- This is a static review; no JARVIS source files were changed.
- Findings are recorded as confirmed only when supported by a concrete code path.
- Recheck and append new findings on subsequent review requests; do not silently replace prior entries.
- Tests and live JARVIS/audio/microphone/Rainmeter behavior were not exercised. The test suite's file-deletion and Windows-action behavior was not verified as safe for execution in this pass.

## Findings

### JARVIS-001 — Muted and typed replies can still play audio

- **Severity:** Medium
- **Confidence:** High
- **Location:** `Skins/Spaceship/@Resources/Jarvis/jarvislib/voice/speaker.py`, `_speak_queue()`; `jarvis.py`, `exchange()`
- **Evidence:** Typed turns set `quiet_talk.typed[0]`, which makes `quiet.now()` and then `muted()` true. The main reply path uses `say_text_only()` only when `JarvisMutedPopup=1`; with that setting at `0`, it sends the typed/quiet reply through `speak_all()`. In `_speak_queue()`, `as_text` is also conditioned on `JarvisMutedPopup=1`, and even when `as_text` is true the audio playback call is not skipped.
- **Impact:** A typed chat answer can be spoken aloud when the pop-up option is disabled, despite the typed-turn text-only intent. Quiet-calendar replies can likewise become audible under that setting, contrary to quiet mode's pop-up-only behavior.
- **Suggested fix:** When `as_text` is true, skip `play_samples()` and advance the live text by the existing text-only timing behavior; add a regression test that asserts no audio playback for typed/muted turns.

### JARVIS-002 — Root-relative app paths pass the local-path check on supported Python 3.12

- **Severity:** Medium
- **Confidence:** High
- **Location:** `Skins/Spaceship/@Resources/Jarvis/jarvislib/launch.py`, `launch_target()`; `actions.py`, `act_open()`
- **Evidence:** The project supports Python 3.10+ and Setup installs Python 3.12. In those versions, `ntpath.isabs()` treats a path beginning with one backslash (for example, `\Windows\System32\app.exe`) as absolute. `launch_target()` rejects UNC paths but does not require a drive component, so this rooted-but-drive-less path passes the extension and traversal checks and is returned to `os.startfile()`.
- **Impact:** A malformed or tampered `Data\StartApps.txt` entry can be treated as an allowed local executable/shortcut path, despite the code's stated requirement for a drive-qualified local path. This also makes behavior depend on Python's version-specific `ntpath.isabs()` semantics.
- **Suggested fix:** Require a local drive-qualified path (for example, validate `ntpath.splitdrive(a)` and reject a missing drive) and add a test case for a single-leading-backslash path on Python 3.12.

### JARVIS-003 — Mood changes are recorded as the bare word “mood”

- **Severity:** Low
- **Confidence:** High
- **Location:** `Skins/Spaceship/@Resources/Jarvis/jarvislib/turnstate.py`, `DID` / `did_add()`; `tests/test_action_table.py`
- **Evidence:** `mood` is an action in `routing.ACTION_TABLE`, and `run_action()` records each action through `did_add()`. `DID` has no `mood` entry, so `did_add()` falls back to the action name. The action-table test explicitly exempts this known gap.
- **Impact:** When JARVIS summarizes actions or answers what it recently did, a mood change is represented as “mood” rather than a useful description.
- **Suggested fix:** Add an appropriate `DID["mood"]` description and remove the known-gap exemption from the action-table test.

### JARVIS-004 — News-feed redirects can downgrade the HTTPS-only fetch

- **Severity:** Low
- **Confidence:** High
- **Location:** `Skins/Spaceship/@Resources/Jarvis/jarvislib/online.py`, `fetch()`
- **Evidence:** `fetch()` checks that the initial URL starts with `https://`, then calls `urllib.request.urlopen()`, whose default redirect handler follows redirects without enforcing that the final URL remains HTTPS.
- **Impact:** A configured HTTPS news feed can redirect the request to HTTP, contrary to the module's stated HTTPS-only policy.
- **Suggested fix:** Reject redirects that change the scheme away from HTTPS and add a test for an HTTPS-to-HTTP redirect.

### JARVIS-005 — Malformed topic entries pass validation and can break memory operations

- **Severity:** Low
- **Confidence:** High
- **Location:** `Skins/Spaceship/@Resources/Jarvis/jarvislib/memory.py`, `load_topics()` and callers such as `topic_text()` / `topics_about()`
- **Evidence:** `load_topics()` checks only that each list element is a dictionary containing `kw`, `talk`, and `used`; it does not validate their types or nested structure. For example, a JSON entry with `"talk": "bad"` passes this check, then `topic_text()` raises while unpacking each character as a three-item talk row. Callers handle `OSError` and `ValueError`, but not this `TypeError`.
- **Impact:** A syntactically valid but malformed `jarvis_topics.json` can turn recall/list/forget operations into a failed JARVIS turn, or terminate the daily compaction worker, rather than producing the existing memory-unreadable response.
- **Suggested fix:** Validate the entry and nested row types in `load_topics()` and raise `ValueError` for invalid structures; add malformed-structure cases to the memory tests.

### JARVIS-006 — A duplicate learnable sentence blocks later new facts in the same message

- **Severity:** Low
- **Confidence:** High
- **Location:** `Skins/Spaceship/@Resources/Jarvis/jarvis.py`, `learnable()`
- **Evidence:** `learnable()` scans sentence parts in order. When a matching fact is already saved, it immediately returns `""` instead of continuing to later sentences. Thus, if the first learnable sentence is a duplicate, a later new learnable sentence is never offered or saved.
- **Impact:** JARVIS silently misses a possible memory offer for a new fact in a multi-sentence chat message.
- **Suggested fix:** Continue the sentence scan after finding an already-saved fact; add a regression case with a duplicate learnable sentence followed by a new one.

### JARVIS-007 — A non-finite command timestamp bypasses the freshness check

- **Severity:** Low
- **Confidence:** High
- **Location:** `Skins/Spaceship/@Resources/Jarvis/jarvis.py`, `main()` command polling
- **Evidence:** The command reader checks `abs(now - float(parts[1])) > 30` before dispatching a command. Python accepts `"nan"` as a float, and comparisons involving NaN are false, so `abs(now - float("nan")) > 30` does not reject the line. The normal Rainmeter and standalone host writers emit integer timestamps; this requires a malformed or externally modified command file.
- **Impact:** A malformed or stale recognized command line can bypass the intended 30-second freshness check and be dispatched. The subsequent command and action handling still applies, so this finding is limited to the freshness guarantee.
- **Suggested fix:** Parse the timestamp and reject it unless `math.isfinite(timestamp)` and it is within the allowed time window; add a regression case for `nan`.
