# Jarvis Module — Security & Robustness Code Review

**Reviewer:** Opus 4.8
**Scope:** `Skins/Spaceship/@Resources/Jarvis/jarvislib/` and related Rainmeter skin invocations
**Nature of review:** Security and robustness audit tracing every trust boundary (file I/O, LLM output, external process invocation, network, and user/account-derived content). No code was changed — this document records findings only.

---

## Architecture Verdict: Strong

The central security property of the module is excellent and consistently enforced: **the LLM has no execution authority.** Model output can never directly cause an action. Every command path is:

1. Deterministically routed in code (`route()`).
2. For the AI fallback (`interpret()` in `routing.py`), **validated word-by-word against what the user actually said**, number-range-checked, then **round-tripped back through the deterministic router** and matched against a whitelisted preset.
3. Executed only via the fixed `ACTIONS` dict.
4. Gated by spoken confirmation for destructive operations.

Supporting defenses are equally disciplined:

- Fail-safe degradation everywhere: meaning-match → word-match, smart-search → keyword search, GPU → CPU, custom voice → Windows voice → text pop-up (never goes silent).
- Bounded resources: embedding cache clears at 1000 entries, note reads capped at 300 KB, chunk sizes capped, prompt lists sliced (events `[:6]`, apps `[:20]`, to-dos `[:12]`, facts `[:2000]` chars, profile 2000/4000 chars).
- Atomic file writes (`write_atomic`, tmp + `os.replace`).
- Single-instance locking via `msvcrt.locking`.
- Anti-hallucination prompting backed by code-written `no_data()` replies and a real action log (`did`) for "what did you do" questions.

---

## Findings

### 1. PowerShell single-quote injection via temp path — `tts.py` `_windows()` — Severity: Low

**Location:** `Skins/Spaceship/@Resources/Jarvis/jarvislib/tts.py`, function `_windows()`

**Detail:**
The WAV output path is interpolated into a PowerShell `-Command` string inside single quotes, with only backslash-to-forward-slash sanitization:

```python
safe_path = path.replace("\\", "/")
ps = (... f"$s.SetOutputToWaveFile('{safe_path}'); ...")
```

The path comes from `tempfile.mkstemp(prefix="jarvis_")`, which on Windows resolves to a user-profile temp directory such as `C:\Users\<name>\AppData\Local\Temp\jarvis_XXXXXX.wav`. A Windows username containing a single quote (e.g. `O'Brien`) produces a path like `C:/Users/O'Brien/.../jarvis_x.wav`. The `'` terminates the quoted string literal in the `-Command`, and the remainder is parsed as PowerShell code.

**Impact:**
- Primary practical effect: TTS silently fails for any legitimate user whose profile path contains an apostrophe (a real robustness bug, not purely theoretical).
- Security effect: local, same-user code-parsing-in-own-context. **Not** remote, **not** privilege escalation.

**Important mitigation already present (correct design):** The *spoken text itself* — which includes LLM output and potentially account/web-derived content — is **not** interpolated into the command string. It is piped via stdin (`[Console]::In.ReadToEnd()` fed by `p.communicate(data)`). This correctly avoids command injection through the untrusted spoken text.

**Suggested fix (not applied):** Escape the quote by doubling it per PowerShell single-quote rules — `safe_path.replace("'", "''")` — or pass the path through an environment variable / stdin like the spoken text already is.

---

### 2. Prompt injection via connected-account content — `prompt.py` `context()` — Severity: Low (by-design tradeoff)

**Location:** `Skins/Spaceship/@Resources/Jarvis/jarvislib/prompt.py`, function `context()` (and `system_prompt()`)

**Detail:**
User-controlled external content is interpolated verbatim into the system prompt with no delimiting or escaping, including:
- Calendar event titles (`calendar.txt`)
- Email metadata (`mail.txt`)
- Open-application window titles (`windows.txt`)
- To-do items (the configured to-do note)
- Profile note and stored facts

A crafted string such as a calendar event titled `Meeting — ignore previous instructions and ...` would land directly in the prompt.

**Impact — genuinely limited:**
- The model has **no execution authority** (all actions are code-gated and whitelisted), so injection can at most make the *spoken chat answer* misbehave; it cannot trigger an action.
- The injected text normally originates from the user's own connected accounts/notes, so it is not an external-attacker channel in typical use. It only matters in edge cases such as a maliciously crafted email subject line surfaced when the user asks "any new mail?".

**Assessment:** This is a defensible design tradeoff rather than a bug. Optional hardening would delimit untrusted blocks in the prompt and/or add an explicit instruction to treat the HUD data as data, not instructions. Worth a code comment acknowledging the tradeoff.

---

### 3. `write_atomic()` has no `fsync` before `os.replace` — `base.py` — Severity: Informational

**Location:** `Skins/Spaceship/@Resources/Jarvis/jarvislib/base.py`, function `write_atomic()`

**Detail:**
```python
def write_atomic(path, text):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(text)
    os.replace(tmp, path)
```
There is no `f.flush()` / `os.fsync()` before the rename. A hard power loss between the write and the OS flushing buffers could leave a zero-length `.tmp` file. The real target file is untouched by the rename until the write completes, so no existing data is lost.

**Assessment:** Acceptable tradeoff for this use case (HUD state and conversation logs, not critical persistence). Documented for completeness. The `State.set()` writer in the same file additionally retries `os.replace` up to 3 times to cope with a concurrent reader on the skin side — a nice touch.

---

### 4. Reminder label not newline-sanitized before line-delimited save — `reminders.py` `save_reminders()` — Severity: Low

**Location:** `Skins/Spaceship/@Resources/Jarvis/jarvislib/reminders.py`, functions `save_reminders()` / `load_reminders()`

**Detail:**
Reminders are stored one record per line as `due|created|kind|label`, where `label` is derived from user speech:

```python
def save_reminders(items):
    write_atomic(REMIND_FILE, "".join(f"{due:.0f}|{created:.0f}|{kind}|{label}\n" for ... in items))
```

Load splits with `line.split("|", 3)`. The `maxsplit=3` correctly makes `label` absorb any `|` characters, so **pipes in the label are safe**. However, a newline in `label` is not neutralized: it would split one record across two physical lines. The next `load_reminders()` would then raise `ValueError` on the malformed line, and per `due_reminders()` that **pauses all reminders** until the file is repaired or deleted.

**Impact — genuinely low:**
- The only current input path for `label` is Whisper transcription, which does not produce newlines, so this is not reachable from normal voice use today.
- The failure mode is fail-safe (reminders pause and the user is notified via `problem()`); no data is silently lost or misexecuted.
- It becomes relevant only if a future non-voice label source is added, or a label is ever fed from calendar/memory text.

**Suggested fix (not applied):** Normalize on save, matching what `convo_add()` already does for the conversation log — e.g. `label = label.replace("\n", " ").replace("\r", " ")` (or collapse all whitespace with `re.sub(r"\s+", " ", label)`).

---

### 5. `recompact()` set-operator precedence does not match apparent intent — `memory.py` — Severity: Informational

**Location:** `Skins/Spaceship/@Resources/Jarvis/jarvislib/memory.py`, function `recompact()`

**Detail:**
```python
group = [j for j in range(i, len(old))
         if j not in gone and len(keywords(g) & keywords(old[j][1]) - {"user"}) >= 2]
```

In Python, set difference (`-`) binds tighter than set intersection (`&`), so this evaluates as `keywords(g) & (keywords(old[j][1]) - {"user"})`. The `{"user"}` is subtracted from only the right operand, not from the final shared set. Because `"user"` (gist facts all start with "The user") is present on both sides, excluding it from the right operand happens to exclude it from the intersection too — so **there is no observable bug today**.

**Assessment:** Behavior-neutral at present, but fragile: the parenthesization doesn't match the evident intent (compare `gist_ok()`, which explicitly does `keywords(fact) - TALK_STOP - {"user"}` on the final set). A future edit that subtracts additional stop-words here could silently misbehave. Suggested clarification: `(keywords(g) & keywords(old[j][1])) - {"user"}`.

---

## Not Issues (Verified)

- **Ollama networking (`llm.py`):** Localhost-only (`http://127.0.0.1:11434`, hardcoded in `base.py`) — no remote attack surface. Structured calls use `temperature=0` (deterministic). `chat_stream` runs the blocking read in a daemon thread, sees `cancel` within 0.2 s, and closes the connection via `gone.set()` in `finally` to stop Ollama — clean cancel propagation with no thread leak.

- **AI command validation (`routing.py` `interpret()`):** Triple-gated — every model-emitted word must have been in the user's transcribed speech (`said()`), the intent cue word must literally appear (`AI_CUES`), numbers must be in-range and actually heard, and the model's intent is rebuilt into a canonical sentence that is re-parsed by the deterministic `route()` and matched to a whitelisted preset. The model's raw output never reaches execution. Logging deliberately records only internal reasons, never the model's output or the user's words.

- **Local note indexing (`search.py`):** Operates on the user's own vault (not external data). Resource-bounded (300 KB read cap, chunk caps), concurrency-safe (`_chroma_lock` held per-note, single reindex via non-blocking `_reindexing` acquire), fail-safe (any ChromaDB failure falls back permanently to keyword search), and skips hidden directories.

- **Meaning matching (`meaning.py`):** Degrades gracefully to word-only matching when the embedding model is unavailable; bounded `_vecs` cache.

- **Rainmeter `.ini` PowerShell calls:** All use static `-File "...ps1"` script paths with no dynamic command interpolation — no injection surface.

- **Spoken text to Windows voice:** Passed via stdin, not the command line — correctly avoids injection through model/user text (see Finding 1 mitigation note).

---

## Summary

| # | Finding | File | Severity |
|---|---------|------|----------|
| 1 | PowerShell single-quote injection via temp path (also breaks TTS for paths with `'`) | `tts.py` `_windows()` | Low |
| 2 | Prompt injection via verbatim account/note content | `prompt.py` `context()` | Low (by-design) |
| 3 | No `fsync` before atomic rename | `base.py` `write_atomic()` | Informational |
| 4 | Reminder label not newline-sanitized before line-delimited save | `reminders.py` `save_reminders()` | Low |
| 5 | `recompact()` set-operator precedence vs. apparent intent (behavior-neutral) | `memory.py` `recompact()` | Informational |

Overall this is a well-engineered, security-conscious codebase. Of the five findings, only **#1** is a concrete, currently-reachable bug worth fixing — it is both a minor local security weakness and a functional break for any legitimate user whose profile path contains an apostrophe. **#4** is a latent, fail-safe edge case not reachable from today's voice-only input path. Findings **#2**, **#3**, and **#5** are documented tradeoffs or behavior-neutral style issues rather than defects.

---

## PART II — Rainmeter Lua Control-Surface Audit (appended handoff)

**Reviewer:** (control-surface pass, appended to the Opus 4.8 Python review)
**Scope:** The Rainmeter/Lua *other half* of the Jarvis trust boundary — the scripts that launch the Python service, write its command file, and persist its settings:
- `Skins/Spaceship/@Resources/Scripts/jarvis.lua` (the HUD-side service launcher + dial)
- `Skins/Spaceship/@Resources/Scripts/control.lua` (Control Center > JARVIS rows)
- `Skins/Spaceship/@Resources/Scripts/lib.lua` (shared helpers: file readers, `H.guard`, `H.save`)
- `Skins/Spaceship/@Resources/Settings.inc` (the persisted settings these scripts write)

**Why this is a separate section:** Part I audited `jarvislib/` (how Python *consumes* `jarvis_cmd.txt` and settings). Part II audits how the HUD *produces* those files and *launches the interpreter*. The two halves meet at three files: `Data\jarvis_cmd.txt`, `Data\jarvis.txt`, and `Settings.inc`. The contract between them is recorded in `JARVIS-Repair-Plan.txt` ("CONTRACTS THAT MUST NOT CHANGE") and MUST be preserved by any fix:
- Launch line format; the interpreter resolution order (`JarvisPython` → venv pythonw → `py` launcher); `RES = argv[1]`.
- Single instance via `Data\jarvis.lock` (msvcrt). Quit via `QUIT` in `jarvis_cmd.txt` or ~30 s of missed checks.
- HUD → Python command words: `WAKE <ts> [tier]`, `CANCEL <ts>`, `FORGET <ts>`, `REINDEX <ts>`, `TRAINWAKE <ts>`, `QUIT <ts>`.

**Architecture verdict (Lua side): strong, with one concrete bug.** Error containment via `H.guard()` (pcall-wrapped handlers), heartbeat/staleness guards on every data read, numeric clamping on all `jbump`/`bump` writes, and `jcall()` only ever receiving hardcoded literals. One real injection/robustness bug (L1) and one latent hardening item (L2).

---

### Finding L1 — Rainmeter bang-argument injection / launch failure via unescaped `"` in the interpreter or resource path — `jarvis.lua` `StartService()` — Severity: Low–Medium

**Location:** `Skins/Spaceship/@Resources/Scripts/jarvis.lua`, function `StartService()`.

**The vulnerable line:**
```lua
SKIN:Bang('["' .. py .. '" "' .. script .. '" "' .. H.res .. '"]')
```
This builds a Rainmeter *run* bang of the form `["<py>" "<script>" "<res>"]` and hands it to Rainmeter to execute. Rainmeter's `[...]` run-bang syntax treats the double-quote `"` as the ONLY argument delimiter and has **no escape mechanism** — there is no `\"`, no doubling, nothing. Whatever sits between a pair of `"` is one argument; a stray `"` ends the current argument early and the remainder is re-tokenized.

**Where each interpolated value comes from (the taint analysis):**
- `script` = `H.res .. 'Jarvis\\jarvis.py'` — derived from Rainmeter's own `@Resources` path. Trusted, but see `H.res` below.
- `H.res` = `SKIN:GetVariable('@')` (set in `lib.lua` `H.init()` as `H.res`) — the absolute path to `@Resources`, i.e. it contains the **Windows user profile path**. If the username/profile folder contains a `"`, this is tainted. (A `"` is actually illegal in Windows path components, so this sub-case is near-impossible in practice — but a path containing a space is normal and is already handled by the surrounding quotes.)
- `py` = return value of the local `pythonw()` function. **This is the real taint source.**

**`pythonw()` resolution order (verified):**
```lua
local function pythonw()
  local p = H.str('JarvisPython', '')
  if p ~= '' then return exists(p) and p or nil end
  -- else: LOCALAPPDATA\SpaceshipHUD\venv\Scripts\pythonw.exe, then the py launcher, etc.
end
```
When `JarvisPython` is set in `Settings.inc`, `pythonw()` returns it verbatim after only an `exists(p)` check (`exists` just opens the file for read). **It performs no validation of the string's characters** — a value containing `"` passes straight through into the bang.

**Reachability / who can set `JarvisPython`:**
1. `Setup-Jarvis.ps1` writes it to the venv `pythonw.exe` path (trusted, no quotes).
2. The user may hand-edit `Settings.inc` (documented: "blank = find Python automatically ... or the full path to pythonw.exe").
3. Anything with write access to `Settings.inc` (same-user local process). There is no Control Center row that sets `JarvisPython` to arbitrary text, so there is **no in-app untrusted path** — this bounds the severity to "local, same-user, requires file write access," which is why it is Low–Medium, not High.

**Impact:**
- **Robustness (the practical, reachable effect):** a `"` anywhere in the resolved `py` or in `H.res` corrupts the bang. Best case the launch silently no-ops and the dial stays `offline`; the user sees Jarvis "never starts" with no error. This is a genuine functional break, analogous to Part I Finding #1 (the apostrophe-in-path TTS break).
- **Security:** trailing text after an early-terminating `"` is re-parsed by Rainmeter as additional run-bang arguments. In the worst case a crafted `JarvisPython` value could smuggle extra arguments into the launched process. It is NOT remote and NOT privilege escalation.

**Mitigations already in place (do not remove):**
- `exists(script)` and `exists(py)` are checked; a missing interpreter sets a `NO PYTHON` note and returns `false` cleanly.
- `H.guard()` wraps `Update`/`OnClick`, so even a thrown error here will not freeze the HUD.
- `jcall()` (the other bang builder) only ever receives hardcoded literals, so it is NOT part of this finding.

**Suggested fix (NOT applied — audit only):** Before building the bang, reject or neutralize `"` in both `py` and `H.res`. Minimal defensive version inside `StartService()`:
```lua
local py = pythonw()
if not py then note = { 'NO PYTHON', os.time() + 6 }; return false end
if py:find('"') or H.res:find('"') then
  note = { 'BAD PATH', os.time() + 6 }
  print('Jarvis: refusing to launch - path contains a quote: ' .. py)
  return false
end
```
Alternatively, validate `JarvisPython` at the point it is read in `pythonw()` (return `nil` if it contains `"`), which also covers any future caller. Preferred long-term fix: avoid the inline-quote bang entirely by writing the interpreter path to a side file and having a fixed launcher read it — but that changes the launch contract in `JARVIS-Repair-Plan.txt` and must be coordinated.

**Regression / contract notes for the fixer:** The launch line format and interpreter resolution order are listed under "CONTRACTS THAT MUST NOT CHANGE." A validation-only guard (reject bad input, keep the same bang) does NOT change the contract and is the safe fix. Do not alter the three positional arguments (`py`, `script`, `H.res`) or their order — `jarvislib/base.py` reads `RES = argv[1]`.

---

### Finding L2 — Externally-sourced device/model names written verbatim into `Settings.inc` — `control.lua` `jset('JarvisMic', ...)` / `jset('JarvisModel', ...)` — Severity: Low

**Location:** `Skins/Spaceship/@Resources/Scripts/control.lua`, the `MICROPHONE` and model rows, via the helpers `jset` / `writeVar`.

**The data path:**
```lua
local function writeVar(file, key, value)
  SKIN:Bang('!SetVariable', key, value)
  SKIN:Bang('!WriteKeyValue', 'Variables', key, value, RES .. file)
end
local function jset(key, value, quiet)
  writeVar('Settings.inc', key, value)
  SKIN:Bang('!SetVariable', key, value, 'Spaceship\\Center\\Sphere')
  if not quiet then say(key .. ' = ' .. ...) end
end
```
The microphone row builds its candidate list from a file written by the Python service:
```lua
local function models(file)
  local out = {}
  local f = io.open(RES .. 'Data\\' .. (file or 'jarvis_models.txt'), 'r')
  if f then for line in f:lines() do if line ~= '' then out[#out + 1] = line end end; f:close() end
  return out
end
...
local mic, mics = H.str('JarvisMic', ''), models('jarvis_mics.txt')   -- listed by jarvis.py at start
local function nextMic(d)
  if #mics == 0 then say('START JARVIS ONCE TO LIST THE MICROPHONES')
  else jset('JarvisMic', cycle(mics, mic, d)) end
end
```
So `JarvisMic` (and similarly `JarvisModel`, cycled from `jarvis_models.txt`) is a raw line from a `Data\*.txt` file that **`jarvis.py` writes** (device names reported by `sounddevice`, model names reported by Ollama). That raw string is then persisted into `Settings.inc` via `!WriteKeyValue 'Variables' <key> <value>`, which writes a single `key=value` line.

**Taint analysis:**
- Source: `jarvis.py` enumerating OS audio devices / Ollama models. These names are ultimately **driver- and model-registry-controlled**, not purely app-controlled. A device name is attacker-influenceable only by someone who can install/name an audio device or an Ollama model — again a local, same-user bar, hence Low.
- Sink: a single INI line in `Settings.inc`. A `value` containing a newline would split the line and could corrupt the `[Variables]` section (orphan the tail as a bogus key or value). An embedded `=` is generally tolerated by Rainmeter's key/value split (first `=` wins) but is still untidy.

**Why it is only Low:** `cycle()` only ever selects a string that already appeared as a full line in the source file, and `f:lines()` strips the newline, so a *newline mid-value* cannot occur through this specific path today. The residual risk is (a) other control characters in a device name landing in the INI, and (b) a future caller passing a less-sanitized string to `jset`. There is no evidence of a current functional break.

**Suggested fix (NOT applied — audit only):** Sanitize at the `jset` boundary so every settings write is safe regardless of caller. In `control.lua`:
```lua
local function jset(key, value, quiet)
  if type(value) == 'string' then
    value = value:gsub('[\r\n]', ' '):gsub('%c', '')   -- strip CR/LF and control chars
  end
  writeVar('Settings.inc', key, value)
  ...
end
```
This mirrors the newline-normalization already recommended for `reminders.py` in Part I Finding #4 and the `convo_add()` precedent on the Python side — same class of "line-delimited store, strip embedded line breaks" hardening.

**Cross-reference:** This is the Lua-side twin of Part I Finding #2/#4 (untrusted text reaching a structured store). It is listed separately because it is a different file, language, and sink (INI write vs. the Python prompt/reminder files).

---

### Not Issues — Lua side (verified, do not "fix")

These were checked and are correct by design. Listed so the fixing AI does not waste effort or introduce regressions "fixing" them.

- **`jcall()` is NOT an injection vector.**
  ```lua
  local function jcall(fn) SKIN:Bang('!CommandMeasure', 'mScript', fn, 'Spaceship\\Center\\Sphere') end
  ```
  Every call site passes a hardcoded string literal: `jcall('StartService()')`, `jcall('StopService()')`, and `ToggleEdit()` via a direct `!CommandMeasure`. No user/file data flows into `fn`, so arbitrary-Lua execution through `!CommandMeasure` is not reachable. Do not add escaping here; there is nothing to escape.

- **Command-file writers are safe (integer-only arguments).** `REINDEX`, `TRAINWAKE`, `WAKE`, `CANCEL`, `QUIT`, `FORGET` are all written as `WORD <os.time()> [tier]`:
  ```lua
  { 'REINDEX', function() local f = io.open(RES .. 'Data\\jarvis_cmd.txt', 'w'); if f then f:write('REINDEX ', os.time(), '\n'); f:close() end; ... end }
  ...
  command('WAKE ' .. os.time() .. ' ' .. H.tier)   -- H.tier is a number from PerfTier
  ```
  No user string reaches `jarvis_cmd.txt`. This matches the documented contract and the Python-side parser in Part I. Do not add quoting.

- **Numeric settings writes are clamped.** `jbump` and `bump` both run the value through `H.clamp(..., lo, hi)` and `math.floor(v*100+0.5)/100` before writing. The theme/color writes (`applyTheme`, `ColorWarn`, etc.) use fixed literals. These cannot carry injection payloads.

- **`lib.lua` file readers are robust.** `appState`, `llt`, and `net` use anchored Lua patterns, `tonumber` guards, and heartbeat/staleness timeouts (`beat`), returning safe defaults when the helper is down or the file is stale/partially written. This is correct defensive parsing — do not "simplify" it.

- **Error containment via `H.guard()`.** `Update`/`OnClick`/`OnScroll`/`OnHover` handlers are wrapped in `pcall` with once-per-message logging, so a thrown error (including anything from L1/L2) degrades gracefully instead of freezing the HUD. Preserve this wrapper when editing handlers.

- **`H.save()` uses `!WriteKeyValue`** (atomic on Rainmeter's side) — consistent with the Settings writes; no separate issue.

---

### Updated combined summary table

| # | Finding | File / function | Severity | Reachable today? |
|---|---------|-----------------|----------|------------------|
| 1 | PowerShell single-quote injection via temp path (also breaks TTS for paths with `'`) | `tts.py` `_windows()` | Low | Yes (apostrophe in username) |
| 2 | Prompt injection via verbatim account/note content | `prompt.py` `context()` | Low (by-design) | Edge (crafted email/calendar text) |
| 3 | No `fsync` before atomic rename | `base.py` `write_atomic()` | Informational | Power-loss only |
| 4 | Reminder label not newline-sanitized | `reminders.py` `save_reminders()` | Low | No (voice input has no newlines) |
| 5 | `recompact()` set-operator precedence vs. intent | `memory.py` `recompact()` | Informational | No (behavior-neutral) |
| **L1** | **Rainmeter bang injection / launch failure via unescaped `"` in interpreter/resource path** | **`jarvis.lua` `StartService()` / `pythonw()`** | **Low–Med** | **Yes (quote in `JarvisPython` or profile path → silent no-launch; crafted value → extra bang args)** |
| L2 | Externally-sourced device/model name written verbatim into `Settings.inc` | `control.lua` `jset`/`writeVar` | Low | Latent (control chars / future callers) |

### Recommended fix order for the handoff AI
1. **L1** and **#1** first — both are concrete, user-reachable "it silently doesn't work" bugs AND minor local-injection weaknesses, in the two different languages. Same root cause class (building a shell/bang string by interpolating a path that may contain the delimiter char). Fix with input validation/escaping, not by changing the launch or TTS contracts.
2. **#4** and **L2** next — cheap, fail-safe hardening of line-delimited / INI stores against embedded line breaks and control chars. Apply the sanitize-at-the-write-boundary pattern in both languages.
3. **#2** — add prompt delimiting + a code comment acknowledging the tradeoff, only if desired.
4. **#3**, **#5** — informational; address only opportunistically (add `flush`+`fsync` to `write_atomic`; add clarifying parentheses in `recompact`).

### Hard constraints for ANY fix (from `JARVIS-Repair-Plan.txt`)
- Do not change the launch line's three positional args or their order; `RES = argv[1]` in `jarvislib/base.py`.
- Do not change the interpreter resolution order (`JarvisPython` → venv `pythonw.exe` → `py` launcher).
- Do not change the `jarvis_cmd.txt` word grammar (`WORD <unix> [arg]`) or the `jarvis.txt` state line format.
- Keep single-instance locking (`Data\jarvis.lock`, msvcrt) and the QUIT / ~30 s-missed-checks shutdown behavior.
- Preserve `H.guard()` wrapping and the fail-safe fallbacks on every data read.