# JARVIS (Clover) System Usability Audit, 11-Product Competitive Benchmark & Unified One-Time Setup Architecture

## Part 1: Deep-Dive Feature Mechanics, Usability Bottlenecks & 11-Product Competitive Benchmark

### 1.1 Forensic Breakdown of Existing JARVIS Features & "Sorry, What Did You Say?" Mechanics

Across `Skins\Spaceship\@Resources\Jarvis\jarvis.py` and the 20 submodules in `jarvislib\`, the assistant (named **Clover** by default on the HUD and **JARVIS** in the underlying daemon) processes voice interactions through a multi-stage local pipeline (`openWakeWord` $\rightarrow$ `sounddevice` RMS capture $\rightarrow$ `faster-whisper` STT $\rightarrow$ deterministic `route()` / `fix_route()` / LLM `interpret()` $\rightarrow$ `Ollama` streaming $\rightarrow$ `Kokoro-82M` / `Piper` / Windows SAPI TTS).

When users experience repetition, missed commands, or clarification loops (such as *"Sorry, I didn't catch that."*, *"Did you say: ...?"*, or *"Sorry, were you speaking to me, sir?"*), six specific code paths in the current infrastructure are responsible:

| Feature / Subsystem | Current Code Location & Exact Mechanism | Why It Triggers Usability Friction | Targeted Low-Cost Infrastructure Modification |
| :--- | :--- | :--- | :--- |
| **1. Blank-Transcript Apology (`"Sorry, I didn't catch that."`)** | `jarvis.py:919–924` (`exchange()`), `hearing.py:88–121` (`real_words()`, `no_loops()`) | When triggered via hologram click (`not woke` and `not follow`), if `transcribe(audio)` returns `""`—either because `PHANTOM` stripped Whisper's noise hallucinations (*"Thank you for watching"*) or `no_loops()` dropped segments with `compression_ratio > 2.4` or `no_speech_prob > 0.6` and `avg_logprob < -1.0`—JARVIS says `"Sorry, I didn't catch that."` without explaining *why* (muted mic, low gain, or clipping). | **Diagnostic-Aware 2-Stage Re-Prompt:** Pass peak RMS from `mic._listen()` alongside `audio`. If `peak_rms < 0.018`, reply `"I barely heard anything—check your mic level."` On a first normal miss, use a 2-word prompt (`"Pardon, {callme}?"`); on a second consecutive miss, auto-open the `Overlay\Jarvis` text input box (`mAsk`). |
| **2. Low-Confidence Confirmation Nagging (`"Did you say: {text}?"`)** | `jarvis.py:770–775` (`understand()`), `hearing.py:98, 110` (`heard_score[0]`) | `hearing.py:110` computes `heard_score[0] = min(getattr(s, "avg_logprob", 0.0) for s in segs)`. Because it takes the **minimum** across all segments rather than a duration- or token-weighted average, a 0.4-second trailing breath or chair creak at the end of a crystal-clear command drops `heard_score[0]` below `-1.0`, forcing a 15-second `ask_yes("Did you say: ...?")` detour on every mutating command (`act`, `multi`, `remind`, `memory`). | **Token-Weighted Confidence + Action-Verb Isolation:** Compute `heard_score[0]` as a token-count-weighted mean of `avg_logprob` across segments with `no_speech_prob < 0.45`, ignoring trailing `<2`-word segments. Only trigger `"Did you say: ...?"` when the command verb or target entity token falls below `-1.05`. |
| **3. Open-Ear & Long-Utterance Ambiguity (`ROOM_ASKS`: `"Sorry, were you speaking to me, sir?"`)** | `jarvis.py:686–729, 931–949, 1039–1047` (`directed()`, `room_talk()`, `room_ask()`) | During the follow-up ear window (`ear_wait()`, default `3 s` direct / `10 s` name window) or on main turns $\ge 25$ words without `"?"`, `"you"`, or the assistant's name (`room_talk()`), `directed()` returns `"ask"`. When `JarvisRoomAsk=1`, JARVIS interrupts with `"Are you talking to me, sir?"` / `"Was that for me, sir?"` / `"Sorry, were you speaking to me, sir?"` and caches the text in `offer["room"]`. | **Semantic Topic-Continuity Check Before `ROOM_ASKS`:** In `directed()`, check `related(text, [m["content"] for m in history[-2:]])` (using the already-loaded `ONNXMiniLM_L6_V2` embedder in `meaning.py`) before returning `"ask"`. Follow-up statements that semantically continue the active topic execute directly without asking. |
| **4. Command Near-Miss Dead Ends (`NEAR_MISS` & 8-Word Cap)** | `jarvislib/routing.py:23–65, 191, 280–302, 685–690` (`fix_route()`, `ask_ai()`, `interpret()`) | `fix_route()` aborts fuzzy command correction if `len(text.split()) > 8` (`routing.py:283`)—measured *before* `tidy()` strips polite filler words (`"Hey Jarvis, could you please go ahead and turn the volume down"` = 12 words, so `fix_route()` skips it!). Worse, `AI_CUES` (`routing.py:27–31`) only covers 11 intents (alarms, timers, reminders, volume, mute, media), leaving brightness, Bluetooth, apps, dark mode, and power modes to hit `NEAR_MISS = "I heard a command but couldn't work it out..."` | **Measure Word Count After `tidy()` + Slot Elicitation (`ask_slot()`):** Check `len(base.split()) <= 12` *after* `tidy(text)` strips filler words, expand `AI_CUES` to cover `brightness`, `bluetooth`, `theme`, `open_app`, and `power`, and add a reusable `ask_slot(question)` helper so incomplete commands ask only for the missing parameter (*"What brightness level?"*). |
| **5. Fixed 2-Second RMS Silence Cutoff vs. Mid-Sentence Pauses** | `jarvislib/mic.py:143–207` (`_listen()`), `Settings.inc:238` (`JarvisSilence=2`) | `_listen()` uses a raw amplitude threshold `thresh = max(floor * 3.0, 0.012)` and waits for `JarvisSilence` seconds of quiet (`2.0 s` in `Settings.inc:238`). Every short command (*"Mute"*, *"What time is it?"*) incurs a mandatory 2-second dead pause before transcription begins, while mechanical keyboard clicks or desk bumps reset `silent = 0` and drag recording out toward the 25-second timeout. | **Silero VAD Gate + Adaptive Two-Tier Silence (`0.65 s` / `1.4 s`):** Feed 30 ms frames through the already-installed Silero VAD (`openwakeword` / `faster_whisper.vad`) so non-vocal clicks never reset `silent = 0`. End capture after `0.65 s` of silence for crisp commands (`< 2.2 s` speech) and allow `1.4 s` when the transcript ends on an incomplete clause. |
| **6. Mid-Clause 5-Word TTS Split & Path Mismatch** | `jarvislib/speech.py:138–169` (`sentences_from()`), `jarvislib/tts.py:186–200` (`resolve_voice()`), `Settings.inc:234` | `sentences_from()` releases the first 5 words (`JarvisFirstWords=5`) even mid-phrase, giving `Kokoro-82M` an incomplete clause with flat prosody and an audible splice when the rest of sentence 1 plays. Additionally, `Setup-Jarvis.ps1:90` installs Kokoro into `Jarvis\voices\`, whereas `Settings.inc:234` points to `Jarvis\kokoro\kokoro-v1.0.onnx` and `resolve_voice()` (`tts.py:193`) only searches `Jarvis\kokoro`, causing fallback to the robotic Windows SAPI voice if paths diverge. | **Clause-Aware First Chunk + Cross-Fade + Unified Voice Path:** Release the first TTS chunk at the first punctuation/clause boundary between 4 and 9 words, apply a 15 ms cosine fade between chunks in `play_samples()`, and add `os.path.join(RES, "Jarvis", "voices")` to `resolve_voice()` in `tts.py:193`. |

### 1.2 Detailed Code-Level Infrastructure Modifications for JARVIS

#### Modification A: Token-Weighted Whisper Confidence & Diagnostic Re-Prompt (`hearing.py` & `jarvis.py`)
Instead of letting a single noisy trailing segment force `"Did you say: ...?"` or giving a blind `"Sorry, I didn't catch that."` when the user's mic is muted or too quiet, update `hearing.py` and `jarvis.py`:

```python
# In Skins/Spaceship/@Resources/Jarvis/jarvislib/hearing.py:
heard_score = [0.0]            # token-weighted avg_logprob across speech segments
last_drop_reason = [""]        # "phantom" | "loop_or_noise" | ""

def _decode(model, audio):
    last_drop_reason[0] = ""
    opts = dict(beam_size=5 if _whisper_dev[0] == "cuda" else 3, language="en", condition_on_previous_text=False)
    segs = list(model.transcribe(audio, vad_filter=True, hotwords="Clover Jarvis", initial_prompt=HINT, **opts)[0])
    if not segs:
        segs = list(model.transcribe(audio, vad_filter=False, **opts)[0])
    raw_count = len(segs)
    segs = no_loops(segs)
    if raw_count > 0 and not segs:
        last_drop_reason[0] = "loop_or_noise"
    # Weight avg_logprob by word count, ignoring 1-word trailing noise segments
    core_segs = [s for s in segs if len(s.text.split()) > 1 or len(segs) == 1]
    total_words = sum(max(1, len(s.text.split())) for s in core_segs)
    heard_score[0] = (
        sum(getattr(s, "avg_logprob", 0.0) * max(1, len(s.text.split())) for s in core_segs) / total_words
        if core_segs else 0.0
    )
    cleaned = no_repeats(" ".join(s.text for s in segs).strip())
    out = real_words(cleaned)
    if cleaned and not out:
        last_drop_reason[0] = "phantom"
    return out
```

And in `jarvis.py` (`exchange()` lines 919–924), replace the static apology with context-aware feedback that tracks consecutive misses (`_missed_count`):

```python
# In Skins/Spaceship/@Resources/Jarvis/jarvis.py:
        if not text and not follow and not cancel.is_set():
            way.update(result="asked again")
            quiet = muted()
            _missed_count[0] += 1
            if peak_rms[0] < 0.016:
                msg = "I barely heard anything—check your microphone level."
            elif _missed_count[0] >= 2:
                msg = "Still didn't catch that. You can type to me in the pop-up."
                S.set(pop="open")
            else:
                call = setting("JarvisCallMe", "sir").strip()
                msg = f"Pardon{', ' + call if call else ''}?"
            reply_line(msg, quiet)
            left["again"] = not quiet and "ear"
            return
        _missed_count[0] = 0
```

#### Modification B: Post-`tidy()` Fuzzy Routing & Missing-Slot Elicitation (`routing.py`)
In `jarvislib/routing.py:280–302`, move the word-count check *after* `tidy(text)` so polite prefixes (`"Hey Jarvis, could you please..."`) never disable typo/soundalike recovery:

```python
# In Skins/Spaceship/@Resources/Jarvis/jarvislib/routing.py:
def fix_route(text, routed):
    if not (routed[0] == "chat" or routed[3] == NEAR_MISS):
        return routed
    base = tidy(text)
    if len(base.split()) > 12:                                 # check AFTER stripping filler words
        return routed
    # ... existing difflib.get_close_matches logic ...
```

### 1.3 Competitive Benchmark: 11 Virtual Assistant Products, Their Flaws & How JARVIS Avoids Them

To ensure JARVIS (Clover) delivers higher everyday usability than commercial and open-source alternatives, the table below benchmarks **11 products** across architecture, onboarding/setup, documented real-world user complaints, and concrete defensive guardrails in JARVIS:

| Product | Core Architecture & Key Strengths | Documented Flaws & User Complaints | How JARVIS Avoids or Fixes This Flaw |
| :--- | :--- | :--- | :--- |
| **1. [Amazon Alexa / Echo](https://www.google.com/search?q=https%3A%2F%2Fwww.amazon.science%2Fblog%2Falexa-scientists-present-two-new-techniques-that-improve-wake-word-performance)** | Dual-stage wake word (on-device acoustic DNN + [cloud wake-word verification](https://www.google.com/search?q=https%3A%2F%2Fdeveloper.amazon.com%2Fblogs%2Falexa%2Fpost%2Fb136b3e7-0ba8-4589-aaf9-2a037fc4e9c9%2Fcloud-based-wake-word-verification-improves-alexa-wake-word-accuracy-on-your-avs-products)), smart-home routines, and multi-device arbitration. | High false-reject rates on hardware like the [Echo Show 15 (\<50% wake success)](https://www.google.com/search?q=https%3A%2F%2Fwww.reddit.com%2Fr%2Famazonecho%2Fcomments%2Fyalwxl%2Fecho_show_15_less_than_50_success_on_wake_word%2F), [false wakes from TV/radio](https://www.google.com/search?q=https%3A%2F%2Fwww.reddit.com%2Fr%2Famazonecho%2Fcomments%2F3lzoqf%2Fanyone_else_noticing_way_more_false_positives_for%2F), [progressive voice recognition degradation](https://www.google.com/search?q=https%3A%2F%2Fwww.reddit.com%2Fr%2Famazonecho%2Fcomments%2F117l1hn%2Fhas_anyone_else_noticed_that_amazon_echos_voice%2F), and [higher false rejections in independent Sensory benchmarks](https://www.google.com/search?q=https%3A%2F%2Fsensory.com%2Frevisiting-wake-word-accuracy-and-privacy%2F). | Uses 100% local `openWakeWord` + Silero VAD + 3 user-trained voice verifiers (`wake_hey_jarvis.pkl`, `wake_hey.pkl`, `wake_jarvis.pkl` in `jarvis.py:1336–1422`) and logs `wake: best <score> this minute` (`jarvis.py:1525`) so wake threshold tuning is transparent and local. |
| **2. [Rabbit R1 (rabbitOS \$\\rightarrow\$ rabbitOS 2 \$\\rightarrow\$ rabbit OS3)](https://www.google.com/search?q=https%3A%2F%2Fwww.rabbit.tech%2Fsupport%2Farticle%2Frabbitos-3)** | Dedicated hardware Push-to-Talk button, [card-based UI in rabbitOS 2](https://www.google.com/search?q=https%3A%2F%2Fwww.rabbit.tech%2Fnewsroom%2Frabbitos-2-launch), [Hermes agent \& OpenClaw v4 / BYOK in 2.3](https://www.google.com/search?q=https%3A%2F%2Fwww.rabbit.tech%2Fupdates), and cross-device web/Telegram/computer orchestration in [rabbit OS3](https://www.google.com/search?q=https%3A%2F%2Fwww.rabbit.tech%2F). | Launch versions were criticized as ["barely reviewable"](https://www.google.com/search?q=https%3A%2F%2Fwww.youtube.com%2Fwatch%3Fv%3DddTV12hErTc) with [early usability hiccups](https://www.google.com/search?q=https%3A%2F%2Fwww.producthunt.com%2Fproducts%2Frabbit-inc) due to slow cloud LAM Playwright execution, fragile web scrapers breaking on UI changes, and lack of local OS API hooks. | Executes deterministic Windows actions (`ShipCore.exe`, Win32 Core Audio, Registry, `powercfg`, `llt.ps1`) locally in `<50 ms` via `ACTION_TABLE` (`routing.py:154–188`), and adds a global keyboard Push-to-Talk / Tap-to-Wake hotkey (`JarvisTalkKey`) alongside wake-word activation. |
| **3. [Apple Siri (iOS / macOS / Apple Intelligence)](https://www.google.com/search?q=https%3A%2F%2Fwww.pcmag.com%2Fnews%2Fapples-siri-struggle-new-report-exposes-reasons-behind-recent-problems)** | Tight OS integration via declarative App Intents, on-device semantic index, and hardware voice isolation. | [Persistent context misunderstandings and dictation bugs](https://www.google.com/search?q=https%3A%2F%2Fwww.reddit.com%2Fr%2Fios%2Fcomments%2F1jyc62v%2Fpsa_if_siri_keeps_misunderstanding_you_it_might%2F), [architectural split between legacy Siri and LLM layers](https://www.google.com/search?q=https%3A%2F%2Fwww.pcmag.com%2Fnews%2Fapples-siri-struggle-new-report-exposes-reasons-behind-recent-problems), [six categories of user harm from repeated assistant misunderstandings (CMU HCII study)](https://www.google.com/search?q=https%3A%2F%2Fhcii.cmu.edu%2Fnews%2Fdesigning-for-harm-reduction), and a [\$95M privacy lawsuit settlement over unintended wake recordings](https://www.google.com/search?q=https%3A%2F%2Fwww.theguardian.com%2Ftechnology%2F2025%2Fjan%2F03%2Fapple-siri-privacy-lawsuit-settlement). | Never uploads audio to the cloud (`INV-4` redacts all transcripts from `jarvis.log`), unifies deterministic rules (`route()`) and bounded JSON intent fallback (`interpret()`) in one pipeline, and provides instant `"undo"` (`undo_last()`) for every state change. |
| **4. [Google Assistant / Gemini Live](https://www.google.com/search?q=https%3A%2F%2Fwww.nngroup.com%2Farticles%2Fintelligent-assistant-usability%2F)** | Full-duplex streaming voice in Gemini Live, deep Android/Workspace context, and broad general knowledge. | Transitioning from Google Assistant to Gemini triggered widespread complaints of [slower voice startup latency](https://www.google.com/search?q=https%3A%2F%2Fwww.reddit.com%2Fr%2FAndroid%2Fcomments%2F1x12i6d%2Fgemini_as_the_google_assistant_is_a_disaster%2F), [broken deterministic home/timer commands](https://www.google.com/search?q=https%3A%2F%2Fwww.reddit.com%2Fr%2Fgooglehome%2Fcomments%2F1sikzq1%2Fgemini_for_home_is_a_major_disappointment%2F), and [worse utility for fast device actions compared to classic Assistant](https://www.google.com/search?q=https%3A%2F%2Fwww.reddit.com%2Fr%2FGooglePixel%2Fcomments%2F1flszzk%2Fgoogle_assistant_is_a_lot_better_than_gemini_for%2F). | Never sends deterministic commands (timers, alarms, volume, brightness, app launch, math/clock) to the LLM—`route()` and `calc.py` handle them in `<10 ms`, reserving Ollama strictly for open-ended conversation and checked `interpret()` fallbacks. |
| **5. [OpenAI ChatGPT Advanced Voice Mode](https://www.google.com/search?q=https%3A%2F%2Fhelp.openai.com%2Fen%2Farticles%2F20001274-chatgpt-voice)** | Native speech-to-speech prosody, low-latency emotional inflection, and natural barge-in interruption. | Users heavily report [constant mid-sentence interruptions during natural thinking pauses](https://www.google.com/search?q=https%3A%2F%2Fcommunity.openai.com%2Ft%2Fadvanced-voice-mode-constantly-interrupting-me%2F963973), [VAD timing misalignment](https://www.google.com/search?q=https%3A%2F%2Fcommunity.openai.com%2Ft%2Fvoice-mode-interruption-issue-timing-misalignment-during-conversations%2F988102), [degraded Bluetooth SCO call-audio quality](https://www.google.com/search?q=https%3A%2F%2Fwww.reddit.com%2Fr%2FOpenAI%2Fcomments%2F1fun73u%2Fvoice_mode_has_an_easilysolvable_issue_that%2F), and [accelerated/high-pitched speech bugs](https://www.google.com/search?q=https%3A%2F%2Fcommunity.openai.com%2Ft%2Fadvanced-voice-mode-bug-accelerated-and-high-pitched-speech-in-chatgpt-consistent-replication%2F1158295). | Uses MME/WASAPI full-bandwidth playback (`speech.py:22`) rather than low-bitrate hands-free telephony profiles, clamps Kokoro speed strictly to `0.6–1.6x` (`tts.py:106`), and adds clause-aware VAD patience so mid-thought pauses don't cut the user off. |
| **6. [Humane AI Pin (CosmOS)](https://www.google.com/search?q=https%3A%2F%2Fwww.layer3labs.io%2Fgear%2Freviews%2Fhumane-ai-pin)** | Screenless wearable form factor with laser ink palm projection and modular AI agent routing (`CosmOS`). | Suffered from [severe cloud round-trip latency](https://www.google.com/search?q=https%3A%2F%2Fwww.swept.ai%2Fpost%2Fthe-bold-vision-and-harsh-reality-of-the-humane-ai-pin), [frequent thermal overheating shutdowns](https://www.google.com/search?q=https%3A%2F%2Fjohnhayes.medium.com%2Fthe-reviews-of-the-humane-ai-pin-are-already-obsolete-73448a8e8c6b), [unreliable gesture/laser readability in daylight](https://www.google.com/search?q=https%3A%2F%2Fwww.engadget.com%2Fthe-humane-ai-pin-is-the-solution-to-none-of-technologys-problems-120002469.html), and [4/10 critical review scores](https://www.google.com/search?q=https%3A%2F%2Fwww.businessinsider.com%2Freviews-humane-ai-pin-2024-4). | Runs on a rich 2560x1600 desktop HUD (`Overlay\Jarvis` + 10-tab Control Center) with automatic GPU thermal/load tiering (`FULL` $\rightarrow$ `LITE` $\rightarrow$ `LOW` $\rightarrow$ `STEALTH` in `Settings.inc:74–85`) and `JarvisModelFast` fallback when the RTX GPU is busy. |
| **7. [Samsung Bixby](https://www.google.com/search?q=https%3A%2F%2Fwww.samsung.com%2Fus%2Fsupport%2Fowners%2Fapp%2Fbixby)** | Deep device-setting control, [on-device command execution \& custom wake phrase](https://www.google.com/search?q=https%3A%2F%2Fnews.samsung.com%2Fglobal%2Fsamsung-announces-enhancement-of-bixby), and capsule-based slot filling. | Frequently criticized for [poor natural-language understanding outside rigid device commands](https://www.google.com/search?q=https%3A%2F%2Fwww.reddit.com%2Fr%2Fsamsung%2Fcomments%2F1j0wixy%2Fbixby_is_truly_terrible%2F), [voice wake-up registration failures](https://www.google.com/search?q=https%3A%2F%2Fwww.samsung.com%2Fus%2Fsupport%2Ftroubleshoot%2FTSG10004627%2F), and [weak general Q\&A compared to Google Assistant](https://www.google.com/search?q=https%3A%2F%2Fwww.reddit.com%2Fr%2Fsamsung%2Fcomments%2F1c1gyhu%2Fis_it_that_im_stupid_as_hell_or_is_it_bixby%2F). | Combines Bixby-style deep hardware/OS control (`ShipCore.exe`, `llt.ps1`, Windows Settings pages, Bluetooth endpoints) with a full local LLM (`llama3.1:8b` / `qwen2.5`) and semantic Obsidian vault search (`search.py`) for open-ended reasoning. |
| **8. [Home Assistant Assist](https://www.google.com/search?q=https%3A%2F%2Fwww.home-assistant.io%2Fvoice_control%2Fbest_practices%2F)** | 100% open-source local pipeline (`openWakeWord` + `faster-whisper` + `Piper` + `HassIL` intents) with [visual pipeline debugging](https://www.google.com/search?q=https%3A%2F%2Fwww.home-assistant.io%2Fvoice_control%2Ftroubleshooting%2F). | Struggles with [low wake-word and STT accuracy on far-field satellite hardware](https://www.google.com/search?q=https%3A%2F%2Fcommunity.home-assistant.io%2Ft%2Fvery-low-wake-word-detection-and-speech-recognition-rate-on-voice-pe%2F834067), [background TV audio corrupting instructions after the wake word](https://www.google.com/search?q=https%3A%2F%2Fwww.reddit.com%2Fr%2Fhomeassistant%2Fcomments%2F1j8p75f%2Fhome_assistant_voice_experiences%2F), and rigid entity naming requirements. | Automatically ducks background PC audio to 30% while listening (`mic._duck()` in `mic.py:88–104`), filters background TV monologues via the 25-second `for_me()` judge (`routing.py:243–256`), and uses `pywebrtc` acoustic echo cancellation (`stopwords.py`). |
| **9. [OpenVoiceOS (OVOS) / Mycroft AI](https://www.google.com/search?q=https%3A%2F%2Fgithub.com%2FOpenVoiceOS%2Fovos-core)** | Hackable, privacy-first modular voice stack ([successor to Mycroft](https://www.google.com/search?q=https%3A%2F%2Fmedium.com%2F%40goldyfruit%2Ffrom-mycroft-and-ansible-to-openvoiceos-making-open-voice-assistants-boring-066caae846d4)) with skill plugins. | Notorious for [fragile manual JSON edits in mycroft.conf causing silent startup failures](https://www.google.com/search?q=https%3A%2F%2Fcommunity.openconversational.ai%2Ft%2Fpicroft-configuration-issue-no-audio-mic-or-speakers-following-setup-although-both-work-fine-in-testing%2F7446), [Linux ALSA/PulseAudio soundcard routing headaches](https://www.google.com/search?q=https%3A%2F%2Fcommunity.openconversational.ai%2Ft%2Funsatisfying-audio-troubles%2F8229), and [broken skill setup.py dependencies](https://www.google.com/search?q=https%3A%2F%2Fcommunity.openconversational.ai%2Ft%2Fmycroft-on-respeaker-core-v2%2F5763%3Fpage%3D3). | Isolates all Python dependencies in a pinned private `%LOCALAPPDATA%\SpaceshipHUD\venv`, auto-selects MME 16 kHz input devices (`mic.py:27–42`), sanitizes all `Settings.inc` writes, and never crashes on a malformed setting (`base.py`). |
| **10. [Microsoft Copilot Voice (Windows 11)](https://www.google.com/search?q=https%3A%2F%2Fsupport.microsoft.com%2Fen-us%2Fprivacy%2Fmicrosoft-copilot%2Ftransparency-note)** | Native Windows 11 shipping integration, cloud LLM + Bing grounding, and M365 document access. | Criticized for [removing local Cortana/Windows control capabilities in favor of a web-wrapper chat UI](https://www.google.com/search?q=https%3A%2F%2Fwww.reddit.com%2Fr%2Fmicrosoft%2Fcomments%2F1ky9g5z%2Fthe_nightmare_of_copilot_continues%2F), [mobile/desktop voice mode regressions](https://www.google.com/search?q=https%3A%2F%2Fwww.reddit.com%2Fr%2Fmicrosoft_365_copilot%2Fcomments%2F1fviya6%2Fthe_new_mobile_copilot_update_is_awful%2F), and [requiring explicit prompt engineering for basic tasks](https://www.google.com/search?q=https%3A%2F%2Fwww.visualsp.com%2Fblog%2Fcommon-mistakes-with-microsoft-copilot-and-how-to-fix-them%2F). | Runs 100% locally with zero cloud telemetry, reads live HUD sensors/calendar/mail/to-dos automatically (`jarvis.py:892, 1157`), and enforces `CLAIM` filtering (`no_claims()` in `routing.py:305–313`) so the LLM can never falsely claim it changed a Windows setting. |
| **11. [Perplexity Assistant](https://www.google.com/search?q=https%3A%2F%2Fbeebom.com%2Ftried-perplexity-assistant-google-should-be-worried%2F)** | Fast real-time web citations, multimodal screen/camera context, and Android app chaining. | Users report [hallucinated facts despite citations](https://www.google.com/search?q=https%3A%2F%2Foriginality.ai%2Fblog%2Fperplexity-assistant-key-insights), [microphone permission deadlocks where voice commands fail to register](https://www.google.com/search?q=https%3A%2F%2Fwww.reddit.com%2Fr%2Fperplexity_ai%2Fcomments%2F1i8z2qy%2Fvoice_commands_not_working_in_perplexity_assistant%2F), and [repetitive failure loops when summarizing articles](https://www.google.com/search?q=https%3A%2F%2Fwww.reddit.com%2Fr%2Fperplexity_ai%2Fcomments%2F1kaj8es%2Fperplexity_assistant_has_difficulties_summarizing%2F). | Auto-unmutes a muted OS microphone when the user clicks the orb (`jarvis.py:868–873`), detects missing mic permissions with a clear HUD banner (`mic.py:158`), and uses `no_data()` (`prompt.py`) to state honestly when live data is unavailable rather than hallucinating. |

## Part 2: Unified One-Time "SETUP" Architecture, Onboarding Outline & Complete Pseudocode

### 2.1 Why the Current Setup Experience Fragments Usability

Currently, following `JARVIS-HUD-Quick-Guide.txt` and `Docs\SETUP.txt` requires a new user to manually configure settings across **8 separate tools and interfaces**:
1. **Windows 11 OS Settings**: Manually adding `Rainmeter.exe` to Graphics *Power saving* (so it stays off the RTX 5070), hiding desktop icons, configuring the taskbar, and enabling Microphone privacy permissions (`Quick-Guide` Section 1.2).
2. **HWiNFO64 Registry Gadget**: Manually ticking 12 sensor values in HWiNFO64 and then opening `Control Center > SENSORS > DETECT` (`Quick-Guide` Section 1.3).
3. **Lenovo Legion Toolkit (`llt.exe`)**: Enabling the CLI in Legion Toolkit and manually editing `LltPath` / `Llt...` keys in `@Resources\Settings.inc` (`Quick-Guide` Section 1.4).
4. **Display Auto-Fit & Theme**: Opening `Control Center > LAYOUT > AUTO-FIT` and `Control Center > THEME` (`Quick-Guide` Section 1.5 & 2).
5. **Account & Note Links (`DATA` Tab)**: Opening `Control Center > DATA` to run `ShipCore.exe setup-gmail`, `ShipCore.exe setup-calendars`, and `ShipCore.exe pick-todo`, plus toggling `RETICLE TO-DOS ON` (`Quick-Guide` Section 3).
6. **App Catalog Scan (`APPS` Tab)**: Running `Control Center > APPS > RESCAN` and editing `Apps.ini` (`Quick-Guide` Section 4).
7. **PowerShell Dependency Installer (`Setup-Jarvis.ps1`)**: Running `Jarvis\Run-Setup.cmd`, which installs Python, `requirements.txt`, `onnxruntime-gpu`, Whisper `small.en`, Ollama, Kokoro `bm_lewis`, `openWakeWord`, Vosk, and ChromaDB—**but** hardcodes `JarvisKokoroVoice=bm_lewis` and leaves out naming the assistant, setting what he calls the user, picking voice speed/persona, training the wake word, or linking notes (`Quick-Guide` Section 5.1).
8. **Manual Post-Setup Tweaks in `CLOVER` Tab (36 Rows) & Text Files**: Manually cycling through 36 rows in `Control Center > CLOVER` to set `NAME` (`CLOVER` vs. `JARVIS`), `CALL ME` (`Sir` / custom title), `KOKORO VOICE` (`Lewis`, `Emma`, `Michael`, `Heart`, `Default blend`), `VOICE SPEED`, `PERSONALITY` (`Playful`, `Mirror`, `Serious`, `Brief`), `ABOUT ME` (`about-me.md`), `WAKE TRAINING`, and manually editing `Settings.inc` for `JarvisNameAliases` and `JarvisBtNames` (`Quick-Guide` Sections 5.2–5.10 & 7).

### 2.2 Unified One-Time Setup Outline (`Setup-SpaceshipHUD-And-Jarvis`)

Inspired by commercial out-of-box flows (such as [Apple Siri's 5-phrase enrollment](https://www.google.com/search?q=https%3A%2F%2Fwww.pcmag.com%2Fnews%2Fapples-siri-struggle-new-report-exposes-reasons-behind-recent-problems), [Samsung Bixby's unified voice registration \& button setup](https://www.google.com/search?q=https%3A%2F%2Fwww.samsung.com%2Fus%2Fsupport%2Fowners%2Fapp%2Fbixby), and [Home Assistant Assist's guided pipeline wizard](https://www.google.com/search?q=https%3A%2F%2Fwww.home-assistant.io%2Fvoice_control%2Fbest_practices%2F)), the redesigned **Unified Setup Wizard** consolidates every step from Sections 1–7 of `JARVIS-HUD-Quick-Guide.txt` into **one interactive, idempotent wizard** (`Setup-Jarvis.ps1` + a companion `setup_wizard.py` GUI/TUI launched from `Run-Setup.cmd` or automatically on first skin load when `FirstRunComplete=0` in `Settings.inc`):

1. **Stage 1 — System & Display Auto-Calibration (User Guide Section 1)**
   - Detects primary/laptop screen resolution (`2560x1600` or custom) and calculates `Scale`, `OriginX`, and `OriginY` (`AutoFit=1`).
   - Registers `Rainmeter.exe` in Windows Graphics Settings (`HKCU:\Software\Microsoft\DirectX\UserGpuPreferences` $\rightarrow$ `GpuPreference=1;` for Power Saving iGPU) so Rainmeter never wakes the discrete RTX GPU.
   - Offers one-click toggles for hiding desktop icons, setting `FrameBehindTaskbar`, and selecting the initial HUD color theme (`CYAN`, `AMBER`, `EMERALD`, `CRIMSON`, `VIOLET`, `ICE`).
   - Automatically locates Lenovo Legion Toolkit (`llt.exe`), writes `LltPath`, checks `HWiNFO64` `VSB` registry keys (`HKCU:\Software\HWiNFO64\VSB`), runs `hwinfo-scan.ps1` auto-detection if present, and triggers `scan-apps.ps1` / `app-icons.ps1` in the background.
2. **Stage 2 — Core AI & Audio Infrastructure Provisioning (User Guide Section 5.1)**
   - Verifies/installs Python 3.12 (`winget`), creates `%LOCALAPPDATA%\SpaceshipHUD\venv`, installs `requirements.txt` + `requirements-gpu.txt` (`onnxruntime-gpu`), and verifies CUDA availability.
   - Enumerates all MME microphone devices, lets the user pick their preferred microphone (`JarvisMic`), verifies Windows Microphone privacy permissions, and runs a 3-second live RMS + Silero VAD mic check.
   - Verifies/installs Ollama (`winget`), recommends a primary model (`JarvisModel`, e.g. `llama3.1:8b`) and fast gaming-tier model (`JarvisModelFast`, e.g. `llama3.2:3b`) based on detected VRAM, and pulls them automatically.
   - Downloads `faster-whisper` (`tiny.en`, `base.en`, `small.en`, or `medium.en`), `Kokoro-82M` (`kokoro-v1.0.onnx`, `kokoro-v1.0.int8.onnx`, `voices-v1.0.bin`), `openWakeWord`, `Vosk` stop-word model, and `ChromaDB` `ONNXMiniLM_L6_V2`.
3. **Stage 3 — Naming the Assistant, User Identity & Persona (User Guide Sections 5.6, 5.7 & 7)**
   - **System Naming in One Space**: Prompts the user to choose the assistant's name (`JARVIS`, `CLOVER`, `FRIDAY`, `COMPUTER`, or any custom name), writes `JarvisName`, auto-populates phonetic STT aliases in `JarvisNameAliases` (e.g., `"jarvis,jarvus,travis,gervais"` or `"clover,clova,grover,clever"`), and links the matching `.onnx` wake model (`hey_jarvis.onnx` or `hey_clover.onnx`) or enables Vosk grammar wake-spotting for custom names so the spoken wake phrase and UI name never diverge.
   - **User Form of Address (`JarvisCallMe`)**: Sets how the assistant addresses the user (`"Sir"`, `"Ma'am"`, `"Boss"`, user's first/last name, or blank).
   - **Personality & Brevity**: Selects `JarvisPersonality` (`playful`, `mirror`, `serious`, `brief`), `JarvisSeriousTopics` (`1`/`0`), and `JarvisTalkLess` (`1`/`0`), and guides the user through creating `Jarvis\about-me.md` right inside the wizard.
4. **Stage 4 — Speaking Features, Voice Audition & Listening Tuning (User Guide Sections 5.4, 5.5, 5.10 & 7)**
   - **Interactive Voice Audition Loop**: Lets the user audition all 5 Kokoro voices (`bm_lewis`, `bf_emma`, `am_michael`, `af_heart`, `default` Lewis+Michael blend) plus Piper and Windows SAPI right in the wizard—speaking *"Hello {JarvisCallMe}, {JarvisName} online and ready."* at the chosen `JarvisVoiceRate` (`-5..+5`) and `JarvisVoiceSpeed` (`0.80..1.20`) until the user locks in their favorite voice.
   - **Listening, Barge-In & Wake Training**: Configures `JarvisWakeWord`, `JarvisWakeSensitivity`, `JarvisBargeIn` (`wake` / `voice` / `off`), `JarvisDuck` (`30%`), `JarvisFollowUp` (`3 s` / `10 s`), `JarvisSilence` (`1.0 s`), and `JarvisChimeVolume` (`25%`), and optionally runs the 90-second interactive `train_wake()` voice enrollment (`Hey {Name}`, `Hey`, `{Name}`, plus 15 s negative speech) immediately.
5. **Stage 5 — Data Links, Privacy & Atomic Commit (User Guide Section 3 & Presets)**
   - Links the user's Obsidian To-Do file (`ObsidianTodo`), Obsidian Notes Vault (`JarvisVault`), Gmail unread check (`ShipCore.exe setup-gmail`), and iCal calendar feeds (`ShipCore.exe setup-calendars`), plus `JarvisQuietCalendar` (auto-mute during classes/meetings).
   - Sets `JarvisLearn` (`auto` / `ask` / `off`), `JarvisRecall` (`on` / `off`), and `JarvisPrivacy` (`0` / `1`).
   - Writes all settings atomically to `Settings.inc`, saves a backup to `Presets\1\`, starts `ShipCore.exe` and `jarvis.py`, refreshes Rainmeter, and plays the personalized greeting.

### 2.3 Complete Pseudocode for the Unified One-Time `SETUP` Process

The pseudocode below is structured so it can be dropped directly into `Skins\Spaceship\@Resources\Jarvis\Setup-Jarvis.ps1` (and called via `Control Center > CLOVER > SETUP > RUN SETUP` or `Jarvis\Run-Setup.cmd`), replacing the fragmented 8-place manual setup with a single, guided, one-stop experience:

```python
# ==============================================================================
# MODULE: unified_setup_wizard.py (invoked by Setup-Jarvis.ps1 / Run-Setup.cmd)
# PURPOSE: Single-space onboarding for Spaceship HUD + JARVIS/Clover Assistant
# ==============================================================================

import os
import re
import sys
import time
import json
import shutil
import subprocess
from dataclasses import dataclass, asdict

@dataclass
class UnifiedSetupConfig:
    # --- Stage 1: HUD, Display & Hardware (User Guide Sec 1 & 2) ---
    Scale: float = 0.67
    OriginX: int = 0
    OriginY: int = 0
    AutoFit: int = 1
    FrameBehindTaskbar: int = 1
    ColorAccent: str = "0,210,255"       # CYAN default
    ColorDim: str = "0,110,150"
    ColorText: str = "170,235,255"
    LltPath: str = ""
    BootAnim: int = 1
    BootSound: int = 0                   # Off by default so skin reloads stay quiet

    # --- Stage 2: AI Models, STT & Hardware Acceleration (User Guide Sec 5.1-5.4) ---
    JarvisEnabled: int = 1
    JarvisAutoStart: int = 1
    JarvisModel: str = "llama3.1:8b"
    JarvisModelFast: str = "llama3.2:3b"
    JarvisGPU: str = "prefer"            # "prefer" | "require"
    JarvisContext: int = 4096            # 2048 | 4096 | 8192
    JarvisKeepAlive: int = 10
    JarvisIdleUnload: int = 10
    JarvisWhisper: str = "small.en"      # "tiny.en" | "base.en" | "small.en" | "medium.en"
    JarvisWhisperDevice: str = "auto"    # "auto" | "cuda" | "cpu"
    JarvisMic: str = ""                  # "" = Windows default MME input

    # --- Stage 3: Identity, Naming & Personality (User Guide Sec 5.6-5.7 & 7) ---
    JarvisName: str = "Jarvis"           # "Jarvis" | "Clover" | custom name
    JarvisNameAliases: str = "jarvus,travis,gervais,service"
    JarvisCallMe: str = "Sir"            # "Sir" | "Ma'am" | custom name | ""
    JarvisPersonality: str = "playful"   # "playful" | "mirror" | "serious" | "brief"
    JarvisSeriousTopics: int = 1
    JarvisTalkLess: int = 0
    JarvisProfile: str = ""              # Path to Jarvis\about-me.md

    # --- Stage 4: Voice/TTS, Audition & Listening Behavior (User Guide Sec 5.4-5.10 & 7) ---
    JarvisVoice: str = r"Jarvis\voices\kokoro-v1.0.int8.onnx"
    JarvisKokoroVoice: str = "bm_lewis"  # "bm_lewis" | "bf_emma" | "am_michael" | "af_heart" | "default"
    JarvisVoiceRate: int = 1             # -5 .. +5
    JarvisVoiceSpeed: float = 1.00       # 0.80 .. 1.20
    JarvisFirstWords: int = 6            # Clause-aware first chunk threshold
    JarvisChime: int = 1
    JarvisChimeVolume: int = 25          # Scaled earcon volume (0-100%)
    JarvisMutedPopup: int = 1
    JarvisWakeWord: int = 1
    JarvisWakeModel: str = "hey_jarvis"  # "hey_jarvis" | "hey_clover.onnx" | custom
    JarvisWakeSensitivity: float = 0.50  # 0.20 (easier) .. 0.90 (stricter)
    JarvisWakeEasy: float = 0.50         # Two-part "Hey ... <Name>" support
    JarvisWakeHard: float = 0.35
    JarvisWakeGap: int = 5
    JarvisBargeIn: str = "wake"          # "wake" | "voice" (headphones) | "off"
    JarvisStopKey: str = "end"           # "end" | "off"
    JarvisTalkKey: str = "off"           # Optional Push-to-Talk hotkey ("rctrl", "f13", "off")
    JarvisDuck: int = 1
    JarvisDuckLevel: int = 30
    JarvisFollowUp: int = 1
    JarvisFollowUpWait: int = 3
    JarvisFollowNameWindow: int = 10
    JarvisSilence: float = 1.0           # 1.0s default (down from 2.0s in old Settings.inc)
    JarvisRoomAsk: int = 0               # 0 = stay quiet when unsure; 1 = ask ROOM_ASKS

    # --- Stage 5: Data Links, Notes, Diagnostics & Privacy (User Guide Sec 3, 5.8 & 7) ---
    ObsidianTodo: str = ""
    ReticleTodo: int = 1
    JarvisVault: str = ""
    JarvisSmartSearch: int = 1
    JarvisQuietCalendar: str = ""
    JarvisLearn: str = "auto"            # "auto" | "ask" | "off"
    JarvisRecall: str = "on"
    JarvisPrivacy: int = 0
    JarvisDiagnose: int = 1
    JarvisWatch: int = 1
    FirstRunComplete: int = 1


# ------------------------------------------------------------------------------
# PHONETIC ALIAS MAP: Automatically generated when the user names the system
# ------------------------------------------------------------------------------
DEFAULT_PHONETIC_ALIASES = {
    "jarvis": "jarvus,travis,gervais,service,charvis,jervis",
    "clover": "clova,grover,clever,clove,rover,glover",
    "friday": "fridays,freddie,faraday",
    "computer": "commuter,compute",
}

THEMES = {
    "1": ("CYAN",    "0,210,255",   "0,110,150",  "170,235,255"),
    "2": ("AMBER",   "255,176,40",  "150,95,20",  "255,225,170"),
    "3": ("EMERALD", "60,255,160",  "20,130,80",  "190,255,220"),
    "4": ("CRIMSON", "255,70,80",   "140,30,40",  "255,200,200"),
    "5": ("VIOLET",  "180,120,255", "90,60,150",  "225,205,255"),
    "6": ("ICE",     "210,235,255", "110,130,150", "240,248,255"),
}

KOKORO_VOICES = {
    "1": ("bm_lewis",   "Lewis (British Male - classic JARVIS cadence)"),
    "2": ("bf_emma",    "Emma (British Female - crisp, warm)"),
    "3": ("am_michael", "Michael (American Male - deep, calm)"),
    "4": ("af_heart",   "Heart (American Female - expressive, natural)"),
    "5": ("default",    "Default Blend (50% British Lewis + 50% American Michael)"),
}


def run_unified_setup(res_dir: str):
    # Executes the complete 5-stage setup in one interactive session, writing
    # all settings atomically to @Resources\Settings.inc and refreshing Rainmeter.
    cfg = UnifiedSetupConfig()
    settings_path = os.path.join(res_dir, "Settings.inc")
    jarvis_dir = os.path.join(res_dir, "Jarvis")

    print("======================================================================")
    print("  SPACESHIP HUD + JARVIS / CLOVER - UNIFIED ONE-TIME SETUP WIZARD")
    print("======================================================================")

    # ==========================================================================
    # STAGE 1: DISPLAY, WINDOWS GPU PREFERENCES, SENSORS & HUD THEME
    # ==========================================================================
    print("\n[STAGE 1/5] Display Calibration, GPU Power-Saving & HUD Theme")

    # 1A. Screen resolution auto-fit (replaces manual Control Center > LAYOUT > AUTO-FIT)
    screen_w, screen_h = detect_primary_screen_size()
    cfg.Scale = round(min(screen_w / 2560.0, screen_h / 1600.0), 4)
    cfg.OriginX = int((screen_w - 2560 * cfg.Scale) // 2)
    cfg.OriginY = int((screen_h - 1600 * cfg.Scale) // 2)
    print(f"  -> Auto-fitted HUD canvas (2560x1600) to {screen_w}x{screen_h} (Scale={cfg.Scale})")

    # 1B. Pin Rainmeter.exe to Integrated GPU (Power Saving) in Windows Registry
    #     Replaces manual: Settings > System > Display > Graphics > Rainmeter.exe > Power saving
    rainmeter_exe = find_rainmeter_exe()
    if rainmeter_exe and ask_yes_no("Pin Rainmeter.exe to the integrated GPU (saves battery & RTX VRAM)?", default=True):
        set_windows_gpu_preference(rainmeter_exe, preference=1)  # 1 = Power Saving (iGPU)
        print("  -> Registered Rainmeter.exe for Power Saving iGPU in DirectX UserGpuPreferences.")

    # 1C. Optional Desktop Icons & Taskbar alignment
    if ask_yes_no("Hide Windows desktop icons so they don't sit under the cockpit?", default=True):
        toggle_desktop_icons(visible=False)
    cfg.FrameBehindTaskbar = 1 if ask_yes_no("Extend cockpit frame behind a transparent taskbar?", default=True) else 0

    # 1D. Pick HUD Theme Color
    print("  Available Cockpit Themes: [1] CYAN  [2] AMBER  [3] EMERALD  [4] CRIMSON  [5] VIOLET  [6] ICE")
    theme_choice = prompt_choice("Select HUD Theme", valid=list(THEMES.keys()), default="1")
    _, cfg.ColorAccent, cfg.ColorDim, cfg.ColorText = THEMES[theme_choice]

    # 1E. Auto-detect HWiNFO64 Gadget sensors & Lenovo Legion Toolkit CLI
    hw_mapped = auto_detect_hwinfo_sensors(res_dir)
    print(f"  -> HWiNFO64 Sensor Auto-Detect: {hw_mapped}/12 sensors mapped.")
    llt_exe = r"C:\Program Files\LenovoLegionToolkit\llt.exe"
    if os.path.isfile(llt_exe):
        cfg.LltPath = llt_exe
        print(f"  -> Linked Lenovo Legion Toolkit CLI: {llt_exe}")

    # 1F. Trigger Start Menu App Scan & Icon Extraction in background
    start_background_powershell(os.path.join(res_dir, "Scripts", "scan-apps.ps1"))

    # ==========================================================================
    # STAGE 2: PYTHON VENV, CUDA, MICROPHONE CHECK & OLLAMA MODELS
    # ==========================================================================
    print("\n[STAGE 2/5] Local AI Engine, Microphone & Speech Recognition Setup")

    venv_py = ensure_python_and_venv(jarvis_dir)
    has_nvidia_gpu, vram_gb = probe_nvidia_gpu(venv_py)
    print(f"  -> GPU Probe: {'NVIDIA CUDA detected (' + str(vram_gb) + ' GB VRAM)' if has_nvidia_gpu else 'CPU mode'}")

    # 2A. Microphone Enumeration & Live Audio/VAD Verification
    mics = list_mme_microphones(venv_py)
    if not mics:
        print("  [!] No microphone detected. Opening Windows Microphone Privacy Settings...")
        os.system("start ms-settings:privacy-microphone")
        input("  Press Enter after enabling 'Let desktop apps access your microphone'...")
        mics = list_mme_microphones(venv_py)

    if mics:
        print("  Detected Microphones:")
        print("    [0] Windows Default Input")
        for idx, m_name in enumerate(mics, 1):
            print(f"    [{idx}] {m_name}")
        mic_idx = prompt_choice("Select Microphone", valid=[str(i) for i in range(len(mics) + 1)], default="0")
        cfg.JarvisMic = "" if mic_idx == "0" else mics[int(mic_idx) - 1]
        run_live_mic_test(venv_py, cfg.JarvisMic)

    # 2B. Whisper Speech-to-Text Model Selection & Pre-Download
    print("  Whisper Speech Recognition Size: [1] tiny.en (fastest)  [2] base.en  [3] small.en (recommended)  [4] medium.en")
    w_map = {"1": "tiny.en", "2": "base.en", "3": "small.en", "4": "medium.en"}
    cfg.JarvisWhisper = w_map[prompt_choice("Select Whisper Model", valid=["1", "2", "3", "4"], default="3")]
    cfg.JarvisWhisperDevice = "auto" if has_nvidia_gpu else "cpu"
    preload_whisper_model(venv_py, cfg.JarvisWhisper, cfg.JarvisWhisperDevice)

    # 2C. Ollama Installation & Dual-Model Provisioning (Primary + Fast Gaming Model)
    ensure_ollama_installed()
    rec_main = "llama3.1:8b" if vram_gb >= 8 else "llama3.2:3b"
    cfg.JarvisModel = prompt_text("Primary Ollama Model", default=rec_main)
    cfg.JarvisModelFast = prompt_text("Fast Model while gaming/GPU busy", default="llama3.2:3b")
    for mdl in {cfg.JarvisModel, cfg.JarvisModelFast}:
        if mdl:
            ensure_ollama_model_pulled(mdl)

    # ==========================================================================
    # STAGE 3: SYSTEM NAMING, USER TITLE & PERSONALITY (ALL IN ONE SPACE)
    # ==========================================================================
    print("\n[STAGE 3/5] Naming Your Assistant, User Title & Personality")

    # 3A. Name the Assistant + Auto-Configure Wake Model & STT Phonetic Aliases
    print("  Choose Assistant Name: [1] JARVIS  [2] CLOVER  [3] FRIDAY  [4] COMPUTER  [5] Custom Name")
    name_choice = prompt_choice("Select Assistant Name", valid=["1", "2", "3", "4", "5"], default="1")
    preset_names = {"1": "Jarvis", "2": "Clover", "3": "Friday", "4": "Computer"}
    if name_choice in preset_names:
        cfg.JarvisName = preset_names[name_choice]
    else:
        cfg.JarvisName = re.sub(r"[^A-Za-z0-9 -]", "", prompt_text("Enter Custom Assistant Name", default="Jarvis")).strip() or "Jarvis"

    low_name = cfg.JarvisName.lower()
    cfg.JarvisNameAliases = DEFAULT_PHONETIC_ALIASES.get(low_name, "")
    custom_aliases = prompt_text(
        f"Optional STT sound-alike aliases for '{cfg.JarvisName}' (comma-separated)",
        default=cfg.JarvisNameAliases
    )
    cfg.JarvisNameAliases = custom_aliases

    # Automatically link the matching wake-word model so UI Name and Wake Word match!
    wake_onnx_candidate = os.path.join(jarvis_dir, "wake", f"hey_{low_name}.onnx")
    if low_name == "jarvis":
        cfg.JarvisWakeModel = "hey_jarvis"
    elif os.path.isfile(wake_onnx_candidate):
        cfg.JarvisWakeModel = f"hey_{low_name}.onnx"
    else:
        # Uses Vosk grammar wake-word fallback or hey_jarvis with clear notice
        cfg.JarvisWakeModel = "hey_jarvis"
        print(f"  -> Note: No 'hey_{low_name}.onnx' found in Jarvis\\wake; wake phrase defaults to 'Hey Jarvis' "
              f"(or say '{cfg.JarvisName}' during the open-ear window).")

    # 3B. How the Assistant Addresses You (JarvisCallMe)
    cfg.JarvisCallMe = prompt_text(
        f"What should {cfg.JarvisName} call you? (e.g., Sir, Ma'am, Boss, your name, or leave blank)",
        default="Sir"
    )

    # 3C. Personality Mode & Conversation Style
    print(f"  How should {cfg.JarvisName} word answers?")
    print("    [1] PLAYFUL (warm, dry wit, 1-3 sentences - default)")
    print("    [2] MIRROR  (calm, jokes only when you do)")
    print("    [3] SERIOUS (precise, formal, no jokes)")
    print("    [4] BRIEF   (one short sentence)")
    p_map = {"1": "playful", "2": "mirror", "3": "serious", "4": "brief"}
    cfg.JarvisPersonality = p_map[prompt_choice("Select Personality", valid=["1", "2", "3", "4"], default="1")]
    cfg.JarvisSeriousTopics = 1 if ask_yes_no("Automatically switch to a serious tone on heavy topics (health, finances, grief)?", default=True) else 0
    cfg.JarvisTalkLess = 1 if ask_yes_no("Enable 'Talk Less' mode (shortest possible answers, zero small talk)?", default=False) else 0

    # 3D. Create or Link "About Me" Profile Note right in the wizard
    if ask_yes_no(f"Set up your 'About Me' profile note so {cfg.JarvisName} personalizes answers?", default=True):
        about_path = os.path.join(jarvis_dir, "about-me.md")
        bio_line = prompt_text("Write 1-2 sentences about yourself (role, projects, preferences) or press Enter to edit later", default="")
        write_about_me_note(about_path, jarvis_dir, bio_line)
        cfg.JarvisProfile = about_path

    # ==========================================================================
    # STAGE 4: SPEAKING FEATURES, INTERACTIVE VOICE AUDITION & WAKE TRAINING
    # ==========================================================================
    print(f"\n[STAGE 4/5] {cfg.JarvisName} Speaking Features, Voice Audition & Wake-Word Tuning")

    # 4A. Install Kokoro-82M Natural Voices & Audition Live in One Loop
    if ask_yes_no("Install & use Kokoro-82M natural neural voice (~400 MB, GPU-accelerated)?", default=True):
        ensure_kokoro_models(jarvis_dir)
        cfg.JarvisVoice = r"Jarvis\voices\kokoro-v1.0.int8.onnx"

        while True:
            print("\n  Choose a Kokoro Voice to Audition:")
            for k, (_, desc) in KOKORO_VOICES.items():
                print(f"    [{k}] {desc}")
            v_pick = prompt_choice("Select Voice [1-5]", valid=list(KOKORO_VOICES.keys()), default="1")
            cfg.JarvisKokoroVoice = KOKORO_VOICES[v_pick][0]

            speed_in = prompt_text("Speaking Speed Multiplier (0.80 = slow, 1.00 = normal, 1.20 = fast)", default=str(cfg.JarvisVoiceSpeed))
            try:
                cfg.JarvisVoiceSpeed = max(0.80, min(1.20, float(speed_in)))
            except ValueError:
                cfg.JarvisVoiceSpeed = 1.00

            sample_line = f"Hello{' ' + cfg.JarvisCallMe if cfg.JarvisCallMe else ''}. {cfg.JarvisName} is online and ready."
            print(f'  -> Playing sample: "{sample_line}" (voice={cfg.JarvisKokoroVoice}, speed={cfg.JarvisVoiceSpeed:.2f})...')
            audition_kokoro_voice(venv_py, os.path.join(res_dir, cfg.JarvisVoice), cfg.JarvisKokoroVoice, cfg.JarvisVoiceSpeed, sample_line)

            if ask_yes_no("Keep this voice and speed?", default=True):
                break
    else:
        cfg.JarvisVoice = ""  # Uses built-in Windows SAPI voice
        audition_windows_voice(f"Hello{' ' + cfg.JarvisCallMe if cfg.JarvisCallMe else ''}. {cfg.JarvisName} online.")

    # 4B. Wake Word, Barge-In, Stop Words (Vosk) & Interactive Voice Enrollment
    cfg.JarvisWakeWord = 1 if ask_yes_no(f"Enable hands-free wake word ('Hey {cfg.JarvisName}')?", default=True) else 0
    if cfg.JarvisWakeWord == 1:
        ensure_openwakeword_model(venv_py)
        sens = prompt_choice(
            "Wake-Word Sensitivity: [1] Easier (0.35 - soft voice)  [2] Balanced (0.50)  [3] Stricter (0.65 - noisy room)",
            valid=["1", "2", "3"], default="2"
        )
        cfg.JarvisWakeSensitivity = {"1": 0.35, "2": 0.50, "3": 0.65}[sens]

        if ask_yes_no(f"Run 90-second Personal Voice Training now so {cfg.JarvisName} learns your voice and 'Hey ... {cfg.JarvisName}'?", default=False):
            run_wake_word_training(venv_py, jarvis_dir, res_dir)

    if ask_yes_no("Install Vosk stop-word detector so saying 'stop' or 'be quiet' halts speech immediately (~41 MB)?", default=True):
        ensure_vosk_model(jarvis_dir)

    print("  Barge-In Mode while speaking: [1] WAKE ('Hey Jarvis' + stop words)  [2] VOICE (any speech - headphones only)  [3] OFF")
    b_map = {"1": "wake", "2": "voice", "3": "off"}
    cfg.JarvisBargeIn = b_map[prompt_choice("Select Barge-In Mode", valid=["1", "2", "3"], default="1")]

    # 4C. Listening Patience, Follow-Up Window & Audio Ducking
    cfg.JarvisFollowUp = 1 if ask_yes_no("Keep ear open for 3 seconds after each reply for wake-free follow-ups?", default=True) else 0
    cfg.JarvisDuck = 1 if ask_yes_no("Lower background music/PC audio to 30% while listening?", default=True) else 0
    sil_choice = prompt_choice(
        "End-of-speech pause before answering: [1] Fast (0.8s)  [2] Balanced (1.0s)  [3] Relaxed (1.5s - if you pause mid-thought)",
        valid=["1", "2", "3"], default="2"
    )
    cfg.JarvisSilence = {"1": 0.8, "2": 1.0, "3": 1.5}[sil_choice]

    # ==========================================================================
    # STAGE 5: DATA CONNECTIONS, PRIVACY & ATOMIC SAVE
    # ==========================================================================
    print("\n[STAGE 5/5] Notes, Calendar, Gmail & Privacy Preferences")

    # 5A. Obsidian To-Do Note & Vault + ChromaDB Semantic Search
    todo_path = prompt_text("Path to your Obsidian To-Do .md file (or press Enter to browse/skip)", default="")
    if todo_path and os.path.isfile(todo_path):
        cfg.ObsidianTodo = todo_path
        cfg.JarvisVault = os.path.dirname(todo_path)
    vault_path = prompt_text("Path to your Notes Vault folder for 'search my notes'", default=cfg.JarvisVault)
    if vault_path and os.path.isdir(vault_path):
        cfg.JarvisVault = vault_path

    if ask_yes_no("Enable Smart Meaning-Based Note Search (ChromaDB ~100 MB)?", default=True):
        cfg.JarvisSmartSearch = 1 if ensure_chromadb_warm(venv_py) else 0
    else:
        cfg.JarvisSmartSearch = 0

    # 5B. Optional Gmail & Calendar Setup via ShipCore.exe
    shipcore_exe = os.path.join(res_dir, "Bin", "ShipCore.exe")
    if os.path.isfile(shipcore_exe):
        if ask_yes_no("Connect Gmail unread count now (opens encrypted ShipCore Gmail window)?", default=False):
            subprocess.run([shipcore_exe, "setup-gmail", res_dir])
        if ask_yes_no("Connect Google/iCal Calendar links now (opens ShipCore Calendar window)?", default=False):
            subprocess.run([shipcore_exe, "setup-calendars", res_dir])

    # 5C. Memory & Privacy Controls
    print("  Automatic Fact Memory: [1] AUTO (saves facts quietly; 'undo' removes)  [2] ASK (asks first)  [3] OFF")
    cfg.JarvisLearn = {"1": "auto", "2": "ask", "3": "off"}[prompt_choice("Select Memory Mode", valid=["1", "2", "3"], default="1")]
    cfg.JarvisPrivacy = 1 if ask_yes_no("Strict Privacy Mode (model only sees counts of calendar/to-dos/apps, never titles)?", default=False) else 0

    # 5D. Atomic Write to Settings.inc + Save Preset 1 Backup + Start Service & Refresh HUD
    write_settings_atomic(settings_path, asdict(cfg))
    save_initial_preset_backup(res_dir, slot=1)
    refresh_rainmeter_and_start_jarvis(res_dir)

    print("\n======================================================================")
    print(f"  SETUP COMPLETE! {cfg.JarvisName.upper()} IS ONLINE AND CONFIGURED.")
    print("  All settings were saved to @Resources\\Settings.inc and backed up to Preset 1.")
    print("======================================================================")
```

### 2.4 Summary of What This Unified Setup Solves

| Before (Current `Setup-Jarvis.ps1` + Manual Guide Steps) | After (Unified 5-Stage `Setup-Jarvis` Wizard) |
| :--- | :--- |
| User must visit **8 separate tools/tabs** (Windows Graphics settings, HWiNFO64, `Settings.inc`, `LAYOUT`, `THEME`, `DATA`, `APPS`, and 36 rows in `CLOVER`). | All 8 setup areas are completed in **one sequential 5-stage wizard** with sensible defaults (`Enter` accepts recommended settings at every prompt). |
| `Setup-Jarvis.ps1` hardcodes `JarvisKokoroVoice=bm_lewis`, never asks for the assistant's name, never sets `JarvisCallMe`, and leaves `JarvisSilence=2` in `Settings.inc`. | Stage 3 & Stage 4 let the user **name the system**, auto-configure phonetic STT aliases + wake model, set `JarvisCallMe`, pick a persona, and **audition all 5 Kokoro voices + speeds live** in one space. |
| Renaming `CLOVER` to `JARVIS` in the Control Center does not update `JarvisNameAliases` or `JarvisWakeModel`, causing wake-word/name mismatch. | Naming the assistant automatically updates `JarvisName`, `JarvisNameAliases`, and `JarvisWakeModel` together, and writes a clean snapshot to `Presets\1\`. |
