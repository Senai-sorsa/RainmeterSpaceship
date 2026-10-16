"""
JARVIS - voice assistant service for the Spaceship HUD.

Click the hologram -> chime -> it listens (stops when you stop talking) -> Whisper turns your speech into text
-> your local Ollama model answers, knowing what the HUD knows (time, calendar, Gmail, to-dos, open apps,
battery, memory, network) -> it speaks the answer sentence by sentence while the hologram moves with its voice.

Talks to the HUD through two small files in @Resources\\Data (no network port, so nothing else can trigger it):
  jarvis.txt      written here:   T <unix> | STATE idle|listening|thinking|speaking | LEVEL <0-1> | SAY | ERR |
                                  POP <n> open|close  (ask the HUD to open / close the conversation pop-up)
  jarvis_cmd.txt  written by HUD: WAKE <unix> <tier>  |  ASK <unix> <text>  |  CANCEL <unix>  |  FORGET <unix>  |  TRAINWAKE <unix>  |  QUIT <unix>
  jarvis_env.txt  written by HUD: MUTED 0|1  - with the speakers muted Jarvis answers in the pop-up, not out loud
  jarvis_log.txt / jarvis_live.txt  the conversation (and the reply in progress) for the pop-up

Started by the HUD (pyw.exe jarvis.py "<@Resources>"); one copy at a time; exits by itself when Rainmeter closes.
Needs:  Python 3.10+,  pip install faster-whisper sounddevice numpy,  Ollama with a model pulled.
Voices: Kokoro-82M (pip install kokoro-onnx + kokoro-v1.0.onnx and voices-v1.0.bin in the same folder - the old
kokoro-v0_19.onnx is NOT supported; default voice bm_lewis), a Piper
voice (.onnx), or the built-in Windows voice as the always-available fallback.
Settings (Settings.inc, all adjustable in Control Center > JARVIS): JarvisModel, JarvisModelFast (used while the HUD
is on its LITE / LOW tiers, i.e. the GPU is busy), JarvisWhisper, JarvisWhisperDevice, JarvisVoice, JarvisVoiceRate,
JarvisKokoroVoice, JarvisChime, JarvisMutedPopup, JarvisKeepAlive, JarvisContext (model memory in tokens),
JarvisSilence (seconds of silence before he answers, default 1), JarvisFirstWords (he starts speaking after this many
words, default 5; 0 = wait for a whole sentence), ObsidianTodo (open to-dos), JarvisProfile ("about me" note),
JarvisVault (Obsidian vault folder for "search my notes" - default: the to-do note's folder).
JarvisSmartSearch (1 = ChromaDB meaning-based note search, falls back to keywords), JarvisWakeWord (default 1 = say "Hey Jarvis" instead of clicking; 0 = off), JarvisWakeSensitivity (0.2-0.9, lower = more sensitive), JarvisIdleUnload (minutes without a turn before the speech models are freed, default 10; 0 = keep them loaded).
JarvisMic (part of the microphone's name; empty = the Windows default), JarvisDuck (default 1 = other sound goes down
while he listens; 0 = off), JarvisDuckLevel (how far down, % of the volume it was, 10-80, default 30).
JarvisBargeIn (off | wake = "Hey Jarvis" stops him mid-sentence, the default | voice = any speech stops him, headphones
only), JarvisStopKey (end = the End key stops him while he is busy, the default; off).
Skills: instant status phrases while searching, a whitelist of actions (risky ones need a spoken "yes"), and
guardrails - nothing outside the whitelist is ever executed.
Every problem is logged to Data\\jarvis.log, shown on the hologram (ERR) and added to the conversation pop-up.
"""
import ctypes
import gc
import os
import re
import sys
import threading
import time
import urllib.error
import urllib.request
import wave
from collections import namedtuple
from datetime import datetime
from jarvislib import hearing
from jarvislib.base import (CMD_FILE, CONVO_FILE, DATA, DUCK_FILE, ENV_FILE, JARVIS_WORD, LIVE_FILE, LOG_FILE,
    MEMORYSTATUSEX, MICS_FILE, MODELS_FILE, NO_WINDOW, OLLAMA, RES, S, STATE_FILE, SYSTEM_POWER_STATUS, State, WAKE_OFF,
    busy, cancel, convo_add, live, log, mic, missing_packages, name_until, problem, rainmeter_running, read_kv,
    setting, settings, single_instance, stop_now, todo_note, write_atomic)
from jarvislib.stopwords import STOP_PHRASES, StopWords, far, far_add, saying, stop_heard
from jarvislib.gpu import cpu_in_use, cpu_threads, gpu
from jarvislib.hearing import (HINT, PHANTOM, _cuda_dlls, _decode, _gpu_try, _load_whisper, _whisper_dev,
    _whisper_lock, _whisper_to_gpu, gpu_watch, heard_score, no_loops, no_repeats, real_words, transcribe, whisper)
from jarvislib.tts import (_broken, _engines, _kokoro, _kokoro_last, _piper, _resolved, _voice_dev, _voice_gpu_off,
    _wav_to_array, _windows, resolve_voice, synth_audio, voice_rate)
from jarvislib.llm import (_moved, chat_json, chat_stream, chat_to_gpu, ctx_tokens, ensure_ollama, http_json,
    installed_models, keep_alive, ollama_on_cpu, pick_model, warm)
from jarvislib.audio import _com, mic_volume, speakers, speakers_mute
from jarvislib import quiet as quiet_talk
from jarvislib.mic import (_listen, _mic_missing, duck, follow_name_wait, follow_wait, list_mics, listen, mic_device,
                           onset, unduck)
from jarvislib.notes import STOP, search_notes, vault_dir
from jarvislib.speech import (FILLERS, HIDE_LOG, SHOW_LOG, _filler_audio, _filler_thread, _filler_voice, _speak_queue,
    filler, filler_done, first_words, muted, play_samples, prepare_fillers, say_text_only, sentences_from, speak_all)
from jarvislib.calc import (MONTHS, ONES, TENS, UNITS, UNIT_ROWS, WEEKDAYS, _num, _remind_bad, amount, calc,
    clock, convert, fact_answer, for_ear, on_day, unit)
from jarvislib.actions import (MEDIA_KEYS, act_close, act_lock, act_open, act_sleep, act_volume, best_app, done_line,
    open_windows, press_key, run_ok, POWER_NAMES, bluetooth_radio, bt_devices, power_key, power_plans, running_window, screen_brightness, start_apps, theme_mode)
from jarvislib.confirm import DANGER, NAMES, YES, confirmed, is_yes
from jarvislib.stopkey import STOP_KEYS, stop_key_loop
from jarvislib.turnstate import DID, DID_ASK, UNDO_FOR, did, did_add, last, offer, recent, undo
from jarvislib.todo import act_todo
from jarvislib.reminders import (ALARM_CAP, ALARM_SAY, DAYS, NAME_ONLY, REMIND_FILE, RINGS, SNOOZE, STOP_WORDS,
    describe, due_reminders, duration, find_items, load_reminders, next_due, rang, reminder_cmd, repeats, ring_line,
    save_reminders, snooze_for, snoozed, span, split_time, when)
from jarvislib.diag import HW_LINES, cpu_times, diagnose, hw_value, is_protected, prompt_findings, sensors
from jarvislib.meaning import MEANING_BLOCK, MEANING_TALK, STAMP, _embed, _vecs, closeness, meaning, vec
from jarvislib.search import _chroma, _chroma_lock, _chunks, _reindexing, chroma_index, smart_search
from jarvislib.memory import (ACTIVE_TTL, EARLIER, FOLLOW_START, GIST_AGE, GIST_FILE, GIST_PROMPT, GIST_SCHEMA,
    MEMORY_BAD, MEMORY_FILE, NO_TALK, RECALL_FLOOR, SECRET, TALK_STOP, TOPICS_BAD, TOPICS_FILE, ask_gist, compact,
    fact_save, facts_about, file_talk, gist_day, gist_for, gist_ok, gisting, keywords, load_gist, load_memory,
    load_topics, recall, recall_on, recompact, related, save_gist, save_memory, save_topics, talk_forget, talk_list,
    topic_text, topics_about)
from jarvislib.routing import (ACTION_TABLE, ACTIONS, AI_CUES, AI_NOT, AI_PROMPT, AI_SCHEMA, AI_WORDS, CANT, CLAIM, CLAIM_LINE,
    CMD_WORDS, FILLER, KEEP, NEAR_MISS, ORDINALS, PHRASES, REFER, SOUNDALIKE, UNBUILT, UNBUILT_ASK, UNBUILT_CAPS,
    _words, as_said, ask_ai, fix_route, holds_words, interpret, no_claims, pick_last, route, strip_name, tidy)
from jarvislib.prompt import (ABOUT_ME, ASKING, BLOCKS, BLOCK_EXAMPLES, BRIEFING, INFO_PROMPT, MOODS, SYSTEM,
    about_me, context, info_blocks, lane_of, no_data, system_prompt, wants)

def load_meaning():
    try:
        from chromadb.utils.embedding_functions import ONNXMiniLM_L6_V2
        # CPU only: the default tries TensorRT / CUDA, fails and retries on every call (330 ms a sentence, not 30)
        ef = ONNXMiniLM_L6_V2(preferred_providers=["CPUExecutionProvider"])
        ef(["warm up"])
        _embed[0] = ef
        for examples in BLOCK_EXAMPLES.values():               # ready before the first question
            for e in examples:
                vec(e)
        try:
            for t in load_topics():                            # M2: each filed topic once, so recall doesn't wait
                vec(topic_text(t))
        except (OSError, ValueError):
            pass
        try:
            for f in load_memory():                            # M4a: each saved fact once, for the same reason
                vec(f)
            for _, g in load_gist()[0]:                        # M3: and each gist line
                vec(g)
        except (OSError, ValueError):
            pass
        log("meaning match: ready")
    except Exception as e:
        _embed[0] = None
        log(f"meaning match off, words only: {e!r}")


ACTIONS_LOGGED = ("close", "open", "volume", "media")           # targets that are app names or levels, never your words


def run_action(action, target, pending=None):
    """Run one table action. An "ask" row runs only when the caller passes the pending action the user said yes to."""
    row = ACTION_TABLE.get(action)
    if row and row.risk == "ask" and pending != (action, target):
        log(f"action {action} refused: needs a confirmed yes")
        return False
    try:
        before = (speakers() if action in ("volume", "mute", "unmute") else mic_volume() if action.startswith("mic_") else setting("JarvisMic", "") if action == "micdev" else screen_brightness() if action == "brightness" else theme_mode() if action == "theme" else bluetooth_radio() if action in ("bluetooth", "bluetooth_off") else (target[0], target[2], next((d[2] for d in bt_devices() if d[0] == target[0]), None)) if action == "btlink" else power_plans()[0] if action == "power" else target if action in ("replace_fact", "forget_facts")
                  else None)
        if action == "forget_all":                             # what was there, so "undo that" can put it back
            try:
                before = load_memory()
            except (OSError, ValueError):
                pass                                           # an unreadable file is still cleared, only not undoable
        ACTIONS[action](target)
        log(f"action: {action} {target if target and action in ACTIONS_LOGGED else ''}")   # your words stay out of the log
        did_add(action, target)
        can_undo(action, before)                               # anything else (lock, close, a key...) cannot be put back
        if action in ("open", "close"):                        # M1b: "close it", "open it again"
            last.update(kind="app", items=[target], when=time.time())
        return True
    except Exception as e:
        did_add(action, target, False)
        log(f"action {action} failed: {e!r}")
        problem(f"Couldn't {action}: {str(e)[:80]}")
        return False


def reply_line(text, quiet):
    """Speak (or show) a short fixed reply and log it."""
    recent["me"] = text
    filler_done()
    if quiet:
        S.set(pop="open")
        live(text)
        time.sleep(min(3.0, 0.06 * len(text)))
        live("")
    else:
        speak_all([text])
    convo_add("J", text)                                       # after: while spoken, the live line types it


def hear(**opts):
    """Listen once more inside a turn and return the words ("" for silence or a click). `opts` go to listen()."""
    audio = listen(**opts) if not cancel.is_set() else None
    return strip_name(transcribe(audio)) if audio is not None else ""   # the "Jarvis" hotword can put the name before a "yes"


def can_undo(what, before=None):
    """Keep the one change "undo that" reverses; before=None marks a change that cannot be put back."""
    undo[:] = [time.time() + UNDO_FOR, what, before]
    if what in ("fact", "forget", "cancel", "move", "flip", "reminder"):   # run_action records its own
        did_add(what, before)


def undo_last():
    """Put the last change back if it is under 2 minutes old, and say what is true now."""
    if not undo or time.time() > undo[0]:
        undo.clear()
        return "There's nothing to undo."
    _, what, before = undo
    undo.clear()
    if before is None:
        return "I can't undo that."
    if what == "multi":                                        # newest first; each step says what it did
        said = []
        for step in reversed(before):
            undo[:] = step
            said.append(undo_last())
        undo.clear()
        return " ".join(said)
    if what in ("bluetooth", "bluetooth_off"):                 # back to what was read before
        ok = (run_action("bluetooth", "on") if before == "on"
              else run_action("bluetooth_off", None, ("bluetooth_off", None)) if before == "off" else False)
        undo.clear()
        return f"Bluetooth back {bluetooth_radio()}." if ok else "That didn't work."
    if what == "btlink":                                       # the device as it was: connected or not
        addr, name, was = before
        ok = was is not None and run_action("btlink", (addr, was, name), ("btlink", (addr, was, name)))
        undo.clear()
        return f"{'Connected to' if was else 'Disconnected from'} {name} again." if ok else "That didn't work."
    if what == "power":                                        # the plan that was active, if it is one we may switch to
        ok = bool(before) and power_key(before) and run_action("power", before, ("power", before))
        undo.clear()
        return f"Power mode back to {POWER_NAMES.get(power_key(before))}." if ok else "That didn't work."
    if what == "theme":
        ok = before != "mixed" and run_action("theme", before)
        undo.clear()
        return f"Back to {theme_mode()} mode." if ok else "That didn't work."
    if what == "brightness":
        ok = run_action("brightness", ("set", before))
        undo.clear()
        return f"Brightness back at {screen_brightness()} percent." if ok else "That didn't work."
    if what == "micdev":                                       # the microphone setting as it was
        ok = run_action("micdev", before, ("micdev", before))
        undo.clear()
        return f"Back to {before}." if ok and before else "Back to the Windows default microphone." if ok else "That didn't work."
    if what.startswith("mic_"):                                # 7a: put the microphone back as it was read before
        was_muted, percent = before
        ok = (run_action("mic_level", ("set", percent)) if what == "mic_level"
              else run_action("mic_mute", None, ("mic_mute", None)) if what == "mic_unmute" else run_action("mic_unmute", None))
        undo.clear()
        if not ok:
            return "That didn't work."
        return f"Microphone back at {mic_volume()[1]} percent." if what == "mic_level" else "Microphone muted." if was_muted else "Microphone unmuted."
    if what in ("volume", "mute", "unmute"):
        ok = run_action("volume", ("set", before[1])) if what == "volume" else run_action("mute" if before[0] else "unmute", None)
        undo.clear()                                           # an undo is not itself undone
        if not ok:
            return "That didn't work."
        return f"Volume back at {speakers()[1]} percent." if what == "volume" else "Muted." if before[0] else "Unmuted."
    try:
        if what in ("forget", "forget_all", "forget_facts"):   # put back what was forgotten, if not already back
            facts = load_memory()
            back = [f for f in before if f not in facts]
            if not back:
                return "It's already back."
            save_memory(facts + back)
            did_add("undo")
            log(f"fact put back by undo ({len(back)})")
            return "Put back: " + "; ".join(back) + "."
        if what == "replace_fact":                             # before = (old, new): the old words go back where the new are
            facts = load_memory()
            if before[1] not in facts:
                return "It's already gone."
            save_memory([before[0] if f == before[1] else f for f in facts])
            did_add("undo")
            log("fact replaced back by undo")
            return f"Put back: {before[0]}."
        if what == "fact":
            facts = load_memory()
            if before not in facts:
                return "It's already gone."
            save_memory([f for f in facts if f != before])
            did_add("undo")
            log("fact removed by undo")
            return f"Forgotten: {before}."
        items, now = load_reminders(), time.time()
        if what == "cancel":                                   # put back what was cancelled, if it has not rung yet
            back = [r for r in before if r[0] > now and r not in items]
            if not back:
                return "It's too late to put that back." if any(r[0] <= now for r in before) else "It's already back."
            save_reminders(items + back)
            did_add("undo")
            log(f"reminder put back by undo ({len(back)})")
            return "Put back: " + "; ".join(describe(r, now) for r in back) + "."
        if what == "flip":                                     # before = (old rows, new rows) after "no, AM": back to the old half of the day
            pairs = [(o, n) for o, n in zip(*before) if n in items]
            if not pairs:
                return "It's already gone."
            back = [(o, n) for o, n in pairs if o[0] > now]
            if not back:
                return "It's too late to put that back."
            save_reminders([r for r in items if r not in [n for _, n in back]] + [o for o, _ in back])
            did_add("undo")
            log("reminder flip put back by undo")
            return "Put back: " + "; ".join(describe(o, now) for o, _ in back) + "."
        if what == "move":                                     # back to its old time, if that has not passed
            old, new = before
            if new not in items:
                return "It's already gone."
            if old[0] <= now:
                return "It's too late to put that back."
            save_reminders([r for r in items if r != new] + [old])
            did_add("undo")
            log("reminder moved back by undo")
            return "Put back: " + describe(old, now) + "."
        gone = [r for r in items if (round(r[0]), round(r[1]), r[2], r[3]) in before]
        if not gone:
            return "It's already gone."
        save_reminders([r for r in items if r not in gone])
        did_add("undo")
        log(f"reminder removed by undo ({len(gone)})")
        noun = "alarm" if gone[0][2:] == ("reminder", "alarm") else "timer" if gone[0][2] == "timer" else "reminder"
        return f"Removed that {noun}." if len(gone) == 1 else f"Removed those {len(gone)} {noun}s."
    except (OSError, ValueError):
        return "I can't read that file, so I left it alone."


# M4a-3: a lasting fact about you said in a chat turn; he offers to remember it, and only a yes saves it.
# shortcut: fixed patterns, not the model, so unusual wording is missed; let the model propose if they miss too much
LEARN = re.compile(r"\b(?:my (?:(?:sister|brother|mum|mom|mother|dad|father|wife|husband|partner|girlfriend|boyfriend|son|"
                   r"daughter|best friend|friend|dog|cat|teacher|boss)(?:'s)? (?:name |birthday )?is|(?:name|birthday|school|"
                   r"job|favou?rite \w+) is)|i'?m allergic to|i am allergic to|i work (?:at|as|for|in)|i live in|"
                   r"i(?:'m| am) (?:a )?(?:vegetarian|vegan)|i study|i have an? \w+ (?:called|named)) \w", re.I)
NO_LEARN = re.compile(r"password|passcode|\bpin\b|code|card|account|bank|social security|\d{3,}", re.I)


def learnable(text):
    """The sentence of a chat turn worth offering to remember, or "": never a question, a number or a secret,
    never one already saved, never with JarvisLearn=off."""
    if setting("JarvisLearn", "ask").strip().lower() in ("off", "0"):
        return ""
    for part in re.split(r"(?<=[.!?])\s+", strip_name(text)):
        part = re.sub(r"^(?:(?:and|so|oh|well|also|by the way),? )+", "", part.strip(), flags=re.I).rstrip(".!")
        if LEARN.search(part) and not part.endswith("?") and not SECRET.search(part) and not NO_LEARN.search(part):
            try:
                if part.lower() in (f.lower() for f in load_memory()):
                    return ""
            except (OSError, ValueError):
                return ""
            return part[:200]
    return ""


def memory_reply(op, text):
    """Carry out a save / list / forget and return what to say. Only counts reach the log, never the facts."""
    try:
        facts = load_memory()
    except (OSError, ValueError):
        return MEMORY_BAD
    if op == "list":
        if not facts:
            return "You haven't asked me to remember anything."
        return f"I remember {len(facts)} thing{'s' if len(facts) != 1 else ''}: {'; '.join(facts)}."
    if op == "forget":                                         # every fact that holds all the words said
        gone = [f for f in facts if holds_words(f, text)]
        if not gone:
            return "I don't have that."
        save_memory([f for f in facts if f not in gone])
        log(f"fact forgotten ({len(gone)})")
        can_undo("forget", gone)
        return "Forgotten: " + "; ".join(gone) + "."
    fact = " ".join(text.split())[:200]
    if fact not in facts:
        if len(facts) >= 50:
            return "You've told me 50 things. Forget one first."
        save_memory(facts + [fact])
        log(f"fact saved ({len(facts) + 1} stored)")
        can_undo("fact", fact)
    return f"Noted: {fact}."


def remind_reply(op, args, quiet):
    """Carry out a list / cancel / set and return what to say. Runs inside a turn, so there is one writer at a time."""
    now, kind = time.time(), args[0]
    try:
        items = load_reminders()
    except (OSError, ValueError):
        return "I can't read the reminders file, so I left it alone."
    # alarms and reminders are one schedule (an alarm is a reminder labelled "alarm"); timers are kept apart
    is_alarm = lambda r: r[2] == "reminder" and r[3] == "alarm"
    pool = [r for r in items if (r[2] == "timer") == (kind == "timer")]
    if op == "list":
        if not pool:
            return "You have no timers." if kind == "timer" else "You have no alarms or reminders."
        n = sum(map(is_alarm, pool))
        counts = (" and ".join(f"{k} {w}{'s' if k != 1 else ''}" for k, w in ((n, "alarm"), (len(pool) - n, "reminder")) if k)
                  if kind != "timer" else f"{len(pool)} timer{'s' if len(pool) != 1 else ''}")
        last.update(kind=kind, items=pool, when=now)          # M1b: "cancel the second one" means this order
        return f"You have {counts}: {'; '.join(describe(r, now) for r in pool)}."
    if op == "snooze":                                         # "snooze" said after the ringing stopped
        if not rang or now - rang[0] > 300:
            return "Nothing is ringing right now."
        if not args[1]:
            return "I can snooze it for 1 minute to 2 hours."
        save_reminders(sorted(items + snoozed(rang[1], now + args[1])))
        did_add("snooze")
        rang.clear()
        log(f"reminder snoozed ({args[1]:.0f}s, after it rang)")
        return f"Snoozed for {span(args[1])}."
    if op == "cancel" and len(args) > 2:                     # M1b: the item was picked from the last list, by code
        key = lambda r: (round(r[0]), round(r[1]), r[2], r[3])
        gone, words = [r for r in pool if key(r) == key(args[2])], []
    elif op in ("cancel", "move"):
        gone, words = find_items(pool, args[1], kind, now)
    if op in ("cancel", "move"):
        if len(gone) > 1 and (op == "move" or not words and not args[1].startswith("all")):   # "turn off my alarm" with 2
            name = lambda r: clock(r[0], now) if is_alarm(r) else describe(r, now)
            log(f"reminder {op}: {len(gone)} match - asked which")
            reply_line(f"You have {len(gone)} {kind}s: {' and '.join(map(name, gone))}. Which one?", quiet)
            S.set(state="listening", level=0.0)
            answer = hear()
            if answer:
                convo_add("U", answer)
            answer = answer.strip().lower().rstrip(".!?")
            if not (op == "cancel" and re.search(r"\b(?:both|all|every|them)\b", answer)):
                pick, said = find_items(gone, answer, kind, now) if answer else ([], [])
                if not said or not pick or (op == "move" and len(pick) > 1):
                    log(f"reminder {op}: no clear pick - left them")
                    return "Okay, I left them."
                gone = pick
        if not gone:
            log(f"reminder {op}: none matched")
            others = "; ".join(describe(r, now) for r in items)
            return f"I don't see {'an' if kind == 'alarm' else 'a'} {kind} like that." + (f" You have: {others}." if others else "")
        if op == "move":
            old, (due, plus) = gone[0], args[2:]
            due = old[0] + plus if plus else next_due(due, old[2], now) if repeats(old[2], now) else due
            if not 5 <= due - now <= 7 * 86400:
                return "I can set that from 5 seconds to 7 days ahead."
            new = (round(due), round(old[1] if plus else now), old[2], old[3])   # as the file stores it
            save_reminders([r for r in items if r != old] + [new])
            log(f"reminder moved ({due - old[0]:.0f}s)")
            can_undo("move", (old, new))
            if kind == "timer":
                return f"The timer now has {span(due - now)} left."
            return f"Moved your {clock(old[0], now)} {'alarm' if is_alarm(old) else 'reminder'} to {clock(due, now)}."
        save_reminders([r for r in items if r not in gone])
        log(f"reminder cancelled ({len(gone)})")
        can_undo("cancel", gone)
        return "Cancelled: " + "; ".join(describe(r, now) for r in gone) + "."
    if op == "flip":                                           # "no, AM": what was just set moves to the other half of the day
        live = bool(undo) and now < undo[0] and undo[1] in ("reminder", "flip")   # a flip can be flipped again
        prev = (undo[2] if undo[1] == "reminder" else [(round(r[0]), round(r[1]), r[2], r[3]) for r in undo[2][1]]) if live else []
        old = [r for r in items if live and r[2] != "timer" and (round(r[0]), round(r[1]), r[2], r[3]) in prev]
        if not old:
            return "There's no alarm to change."
        # shortcut: 12 hours in seconds, an hour off across a daylight-saving change; use the wall clock if that matters
        new = [(min(t for t in (r[0] - 43200, r[0] + 43200) if t > now)          # the sooner of the two, never past
                if (datetime.fromtimestamp(r[0]).hour < 12) != (args[1] == "am") else r[0],) + r[1:] for r in old]
        save_reminders([r for r in items if r not in old] + new)
        log(f"reminder moved 12 hours ({len(new)})")
        can_undo("flip", (old, new))
        return ("Changed to " if new != old else "It's already set for ") + " and ".join(clock(r[0], now) for r in new) + "."
    _, due, label, said = args
    alarm_set, kind = kind == "alarm", "reminder" if kind == "alarm" else kind
    if repeats(kind, now) and (due is None or said.startswith("in ")):
        return "A repeating reminder needs a clock time, like every day at 9."
    if due is None:                                            # no time heard: ask once and listen, like a confirmation
        reply_line("How long?" if kind == "timer" else "When?", quiet)
        S.set(state="listening", level=0.0)
        answer = hear()
        if answer:
            convo_add("U", answer)
        now, answer = time.time(), answer.strip().lower().rstrip(".!?")
        if re.fullmatch(r"no|nope|never ?mind|cancel(?: that| it)?|forget (?:it|that)|nothing|stop|don'?t", answer):
            return f"Okay, no {args[0]}."
        for said in (answer, "at " + answer, "in " + answer):     # "at" first: "1900 hours" is a time, not a wait
            due = when(said, now)
            if due is not None:
                break
        else:
            return "I didn't catch the time."
    dues = sorted(due) if isinstance(due, list) else [due]     # "alarms for 7 and 8": a list
    if not all(5 <= d - now <= 7 * 86400 for d in dues):
        return "I can set that from 5 seconds to 7 days ahead."
    if len(items) + len(dues) > 20:
        return "You already have 20 pending. Cancel one first."
    label = re.sub(r"[\s|]+", " ", label)
    if kind != "timer":                                        # the same alarm or reminder twice would ring twice
        same = [d for d in dues if any(r[2:] == (kind, label) and abs(r[0] - d) < 60 for r in items)]
        dues = [d for d in dues if d not in same]
        if not dues:
            return f"You already have {'an alarm' if alarm_set else 'that reminder'} for {clock(same[0], now)}."
    save_reminders(items + [(d, now, kind, label) for d in dues])
    log(f"reminder set ({'alarm' if alarm_set else kind}, {dues[0] - now:.0f}s ahead, {len(dues)})")
    can_undo("reminder", [(round(d), round(now), kind, label) for d in dues])   # as the file stores it
    last.update(kind="timer" if kind == "timer" else "alarm" if alarm_set else "reminder",
                items=[(d, now, kind, label) for d in dues], when=now)        # M1b: "cancel it"
    if len(dues) > 1:
        return f"Alarms set for {' and '.join(clock(d, now) for d in dues)}."
    due = dues[0]
    if alarm_set:
        return f"Alarm set for {clock(due, now)}" + (f", {span(due - now)} from now." if said.startswith("in ") else ".")
    if kind == "timer":
        return f"Timer set for {span(due - now)}" + (f", for {label}." if label else ".")
    return f"I'll remind you {label} ".replace("  ", " ") + (
        f"in {span(due - now)}." if said.startswith("in ") else f"{repeats(kind, due)}at {clock(due, due if repeats(kind, due) else now)}.")


def ding():
    """Two falling notes, made here so there is no sound file; played like the voice, so the hologram moves with it."""
    import numpy as np
    rate = 24000
    t = np.arange(int(rate * 0.45)) / rate
    return np.concatenate([0.4 * np.sin(2 * np.pi * hz * t) * np.exp(-6 * t) for hz in (1318.5, 1046.5)]).astype(np.float32), rate


def alarm():
    """Ring for everything that is due, as one alarm: ding, say it, listen for a stop word, repeat. It holds the turn
    lock, so it waits for a running turn, the wake word lets go of the microphone, and a click stops it."""
    with busy:
        cancel.clear()
        turn_id[0] = time.time()                               # counts as activity: the voice is not unloaded mid-ring
        try:
            now = time.time()
            items = load_reminders()
            due = [r for r in items if r[0] <= now]
            if not due:
                return
            # gone before it rings: a crash here cannot ring forever. A repeating one goes back in for its next time
            # (once, however many were missed while the PC was off)
            ahead = [(next_due(r[0], r[2], now), now, r[2], r[3]) for r in due if repeats(r[2], now)]
            save_reminders(sorted(items[len(due):] + ahead))
            log(f"reminder fired ({len(due)})")
            log(f"timing: due -> ring {now - due[-1][0]:.1f}s")
            text = " ".join(ring_line(r, now) for r in due)
            convo_add("J", text)
            audio = None if muted() or hud_tier() >= 3 else synth_audio(text)     # made once, replayed each round
            if audio is None:                                  # muted, STEALTH or no voice: shown like a muted reply
                if setting("JarvisMutedPopup", "1") == "1":
                    S.set(pop="open")
                rang[:] = [time.time(), due]
                return
            # an alarm in the batch: ding every ~2 s until answered (cap ALARM_CAP); timers and reminders: RINGS rounds
            alarm_at = next((r[0] for r in due if r[2] != "timer" and r[3] == "alarm"), None)
            start, said, rounds = time.time(), None, 0
            while time.time() - start < ALARM_CAP if alarm_at else rounds < RINGS:
                rounds += 1
                S.set(state="speaking", say=text)
                play_samples(*ding())
                if not cancel.is_set() and (not alarm_at or said is None or time.time() - said >= ALARM_SAY):
                    play_samples(*audio)
                    said = time.time()
                S.set(state="listening", level=0.0)
                # matched and dropped, never kept; an alarm's gap is short, and Whisper runs only if someone speaks
                heard = hear(patience=1.5) if alarm_at else hear()
                nap = snooze_for(heard)                        # before the stop words: "okay, snooze" snoozes
                if nap and not cancel.is_set():                # rings again once; a repeating one keeps its own series
                    again = time.time() + nap
                    save_reminders(sorted(load_reminders() + snoozed(due, again)))
                    did_add("snooze")
                    rang.clear()
                    log(f"reminder snoozed ({nap:.0f}s)")
                    reply_line(f"Snoozed until {clock(again)}." if alarm_at else f"Snoozed for {span(nap)}.", False)
                    return
                if cancel.is_set() or (nap is None and (STOP_WORDS.search(heard) or alarm_at and NAME_ONLY.fullmatch(heard))):
                    convo_add("J", "(stopped)")
                    rang[:] = [time.time(), due]               # "snooze" in the next 5 minutes still works
                    return
            rang[:] = [time.time(), due]
            if alarm_at:                                       # nobody answered it: a line in the pop-up
                log(f"alarm missed (rang {ALARM_CAP // 60} min)")
                convo_add("J", f"Missed alarm from {clock(alarm_at)}.")
                if setting("JarvisMutedPopup", "1") == "1":
                    S.set(pop="open")
        except Exception as e:
            log(f"alarm failed: {type(e).__name__}")
            problem("A reminder could not ring")
        finally:
            S.set(state="idle", level=0.0)


def index_loop():
    load_meaning()                                             # here, so chromadb is imported by one thread only
    while True:
        try:
            chroma_index(force=True)
        except Exception as e:
            log(f"index loop: {e!r}")
        time.sleep(600)


# ------------------------------------------------------------------ one conversation turn
history = []          # the active window (M1): the last 2 exchanges, kept while the talk stays on them
last_turn = 0.0


def compact_due(now, since):
    """Once a day, 10 minutes after the last turn, with no turn running and the HUD on FULL (no game)."""
    return (gist_day[0] != f"{datetime.fromtimestamp(now):%Y-%m-%d}" and now - since >= 600
            and not busy.locked() and hud_tier() == 0 and not gisting.locked())


def daily_memory():
    with gisting:
        stop = lambda: busy.locked() or hud_tier() > 0
        if compact(time.time(), stop) and not stop():
            recompact(time.time(), stop)
            gist_day[0] = f"{datetime.now():%Y-%m-%d}"


def file_active():
    """Unlinked, timed out or "new topic": the window is filed (topic memory, M2) and emptied."""
    file_talk(history)
    history.clear()


def active(text):
    """The window to send with this question. It is kept when the question is related to it (related()), starts
    like a follow-up, or is 3 words or fewer; otherwise (or after ACTIVE_TTL) it is filed first."""
    file_talk(history[:-4])                                    # talk that drops off the window is filed too
    del history[:-4]
    plain = " ".join(re.sub(r"[^a-z' ]", " ", text.lower().replace("’", "'")).split())
    if history and (time.time() - last_turn > ACTIVE_TTL or not (
            len(plain.split()) <= 3 or FOLLOW_START.match(plain) or related(text, [m["content"] for m in history]))):
        file_active()
    return list(history)


def fit_context(system, past, user):
    """Drop the oldest exchanges until everything fits the context window (with room left for the answer), so the
    system prompt - the HUD data and your note - is never the part the model loses."""
    budget = ctx_tokens() - 400
    est = lambda msgs: sum(len(m["content"]) for m in msgs) // 3 + 8 * len(msgs)   # ~3 characters per token
    past = list(past)
    while past and est(system + past + [user]) > budget:
        past = past[2:]
    return system + past + [user]


def chime():
    """The click sound, through the voice's own player so JarvisChimeVolume (percent, default 25) can scale it."""
    if setting("JarvisChime", "1") != "1" or quiet_talk.now():
        return 0.0
    for name in ("chime.wav", "startup.wav"):
        p = os.path.join(RES, "Sounds", name)
        if os.path.exists(p):
            try:
                import numpy as np
                with wave.open(p, "rb") as wf:
                    rate, ch = wf.getframerate(), wf.getnchannels()
                    raw = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16)
                try:
                    vol = max(0.0, min(100.0, float(setting("JarvisChimeVolume", "25")))) / 100
                except ValueError:
                    vol = 0.25
                a = (raw.astype(np.float32) / 32768 * vol).reshape(-1, ch)
                threading.Thread(target=play_samples, args=(a, rate), daemon=True).start()
                return min(len(a) / rate, 0.8)
            except Exception:
                return 0.0
    return 0.0


def watchdog(started):
    """A turn that hangs (stuck microphone, frozen model) is cancelled after 3 minutes."""
    while busy.locked() and started == turn_id[0]:
        if time.time() - started > 180:
            log("watchdog: turn took over 3 minutes - cancelling")
            cancel.set()
            return
        time.sleep(2)


turn_id = [0.0]
NO_FOLLOW = re.compile(r"(?:Okay, never mind|Okay, no \w+|Okay, I left (?:them|it)|Cancelled)\.$")   # he was told to drop it: no follow-up
# a whole reply that means "stop" / "we're done", in any turn: he stops without answering (FR6 L1). Also Whisper's
# stock "Thank you." on noise (FR6 L4): a real thanks needs no answer either
_END = (r"(?:(?:ok|okay|alright|great|cool|perfect|no|nah|oh) )?(?:thanks|thank you(?: so much)?|that's all|that's it|"
        r"no thanks|no thank you|nope|no|goodbye|bye|i'm good|i'm fine|nothing|stop(?: it| talking)?|all good|cheers|"
        r"(?:be )?quiet|shut up|shush|hush|never mind|(?:that's )?enough)(?: jarvis)?")
ENDERS = re.compile(rf"{_END}(?: {_END})*")
# courtesy: a whole reply that is only manners gets a short proper answer from code, no model, no follow-up.
# "{name}" becomes ", <JarvisCallMe>" (nothing when that setting is empty)
_OK = r"(?:(?:ok|okay|alright|great|cool|perfect|oh) )?"
COURTESY = ((re.compile(rf"(?:{_OK}(?:thanks|thank you|thank you so much|thank you very much|thanks a lot|cheers|"
                        r"much appreciated)(?: jarvis)? ?)+"), "You're welcome."),
            (re.compile(r"(?:hello|hi|hey|hiya|howdy|greetings)(?: there)?(?: jarvis)?"), "Hello{name}."),
            (re.compile(rf"{_OK}(?:goodbye|bye|bye bye|see you|see you later)(?: jarvis)?"), "Goodbye{name}."),
            (re.compile(rf"{_OK}good ?night(?: jarvis)?"), "Good night{name}."),
            (re.compile(r"(?:oh )?(?:sorry|my bad)(?: jarvis)?"), "No problem."))
ROOM_ASKS = ("Are you talking to me, sir?", "Was that for me, sir?", "Sorry, were you speaking to me, sir?")
_asked_room = [0]
HEARD_ASK = re.compile(r"(?:what|who|where|when|why|how|which|is|are|am|was|were|can|could|would|will|do|does|did|should|"
                       r"shall|have|has|tell|show|give|play|stop|read|find|search|check|open|close|make|put|set|turn|"
                       r"remind|cancel|add|remove|undo|repeat|say|explain|help|what's|how's|where's|who's|let's)\b")


def room_ask():
    """S2-10: the "not for me?" question, in turn so it doesn't sound canned."""
    _asked_room[0] += 1
    return ROOM_ASKS[_asked_room[0] % len(ROOM_ASKS)]


def directed(text, answering):
    """S2-10, decided by code (the model never decides): was speech in the open-ear window for him? "yes": run it;
    "ask": unsure, ask; "no": a fragment or noise, stay quiet. answering: he just asked something or offered."""
    said = strip_name(text)
    words = re.findall(r"[a-z']+", said.lower().replace("’", "'"))
    if not words:
        return "no"
    if said != text or "jarvis" in words or answering:
        return "yes"
    r = route(said)
    if r[0] != "chat":                                         # a command, a guard, a fixed reply: it was meant for him
        return "yes"
    plain = " ".join(words)
    if ENDERS.fullmatch(plain) or any(rx.fullmatch(plain) for rx, _ in COURTESY):   # "thanks" / "no": answered as before
        return "yes"
    if "?" in text or {"you", "your", "you're", "yourself", "yours"} & set(words) or HEARD_ASK.match(plain):
        return "yes"
    return "ask" if len(words) >= 3 else "no"


def ear_wait():
    """S2-10: the open-ear window after a reply: JarvisFollowUpWait (3 s); 8 s when he asked or offered something."""
    asked = (recent["me"] or "").rstrip().endswith("?") or time.time() < offer.get("expires", 0)
    return max(follow_wait(), 8.0) if asked else follow_wait()


def room_talk(text):
    """FR5 N3: long talk with no question, no "you" and not his name: likely meant for someone else in the room."""
    words = re.findall(r"[a-z']+", text.lower().replace("’", "'"))
    return len(words) >= 25 and "?" not in text and not {"you", "your", "you're", "jarvis"} & set(words)


NEW_TOPIC = re.compile(r"(?:(?:ok|okay|alright),? )?(?:let'?s )?(?:(?:start|have) )?(?:a )?(?:new |change (?:the )?)(?:topic|subject)(?:[,.!?:;-]+\s*|\s*$)", re.I)


# REDESIGN slice B: what the turn means, decided once. via: rule, context or ai-reread
Decision = namedtuple("Decision", "kind action target prompt via")
LEVEL = re.compile(r"(?:(?:about|around|roughly|maybe|like|make it|to|at|um|uh|so|and)\s+)*(.+?)\s*(%| ?percent)?")
VOLUME_DID = ("changed the volume", "muted the sound", "unmuted the sound")


def level_fix(text):
    """L2: a lone level ("About 20%.") is a half-heard volume command. Right after a volume change it sets it;
    otherwise only "N percent" counts, and he asks first. None: not a lone level."""
    m = LEVEL.fullmatch(" ".join(re.sub(r"[^a-z0-9% ]", " ", text.lower()).split()))
    n = m and _num(m.group(1))
    if n is None or n > 100:
        return None
    if did and did[-1][1] in VOLUME_DID and time.time() - did[-1][0] <= ACTIVE_TTL:
        return Decision("act", "volume", ("set", int(n)), None, "context")
    if m.group(2):
        return Decision("act", "volume", ("set", int(n)), f"Did you mean the volume at {int(n)} percent?", "context")
    return None


def understand(text, model, quiet, room):
    """Rules first, then the last exchange, then the model only on a miss. kind "room": likely not for him."""
    kind, action, target, prompt = fix_route(text, route(text))
    via = "rule"
    if kind == "chat":
        lone = level_fix(strip_name(text))
        if lone:                                               # still asked back below if Whisper was unsure
            kind, action, target, prompt, via = lone
        elif text != room and room_talk(text):
            return Decision("room", None, None, None, "rule")
    if ask_ai(text, (kind, action, target, prompt)):           # a missed command: the AI's reading, checked, or as before
        filler("confirm_wait", quiet)                          # "One moment." while the model reads it; the answer waits for it
        read = interpret(model, text)
        if read:
            kind, action, target, prompt = read
            via = "ai-reread"
    changes = ((kind == "act" and prompt is None) or kind == "multi"           # D1: every command that changes something
               or (kind == "remind" and action in ("set", "cancel", "move", "flip", "snooze"))
               or (kind == "memory" and action in ("save", "forget")))
    if changes and heard_score[0] < -1.0:                      # Whisper was unsure: never act on a guess
        prompt = f"Did you say: {text}?"
    return Decision(kind, action, target, prompt, via)


def command_reply(kind, action, target, prompt, quiet):
    """Carry out a command that needs no confirmation and return what to say; None if it is not one."""
    if kind in ("say", "fact"):
        return prompt
    if kind == "undo":
        return undo_last()
    if kind == "level":
        is_muted, percent = speakers()
        return f"The volume is at {percent} percent" + (", muted." if is_muted else ".")
    if kind == "remind":
        try:
            return remind_reply(action, target, quiet)
        except OSError as e:                                   # save_reminders writes atomically: the old file is still there
            log(f"reminder {action}: save failed ({e!r})")
            return "I couldn't save the reminders file, so nothing changed."
    if kind == "memory":
        return memory_reply(action, target)
    if kind == "act" and prompt is None:
        return done_line(action, target) if run_action(action, target) else "That didn't work."
    return None


def ask_yes(prompt, quiet):
    """Every confirmation: ask, listen up to 15 s, and True only for a plain yes (the shared YES set)."""
    reply_line(prompt, quiet)
    if typed_turn[0]:                                          # 8d: a typed ask is never confirmed by the microphone (other channel)
        log("confirm: typed turn - not confirmed, ask out loud")
        return False
    if not quiet:
        time.sleep(0.3)                                        # 8-A1: let the tail of his own voice die before the mic opens
    pending = {"expires": time.time() + 15}                    # counted from the end of the spoken prompt
    S.set(state="listening", level=0.0)
    answer = hear()
    heard = set(re.findall(r"[a-z']+", (answer or "").lower()))
    if len(heard) >= 3 and heard <= set(re.findall(r"[a-z']+", prompt.lower())):   # his own prompt coming back through the mic
        log("confirm: heard only the prompt's own words - ignored")
        answer = ""
    if answer:
        convo_add("U", answer)
    # a yes Whisper was unsure of (a cough read as "Okay.") never confirms
    return confirmed(pending, answer, time.time()) and heard_score[0] >= -1.0 and not cancel.is_set()


def ask_text(raw):
    """8d: the text of an `ASK <unix> <text>` line: one line, at most 500 characters, or "" when there is none."""
    bits = raw.split(None, 2)
    return " ".join(bits[2].split())[:500] if len(bits) > 2 else ""


typed_turn = [False]                                           # 8d: the running turn came from the text box


def turn(tier, follow=0, woke=False, typed=None):
    """One exchange, then follow-ups without the wake word (JarvisFollowUp) for as long as you keep answering
    (D2, no cap): S2-10, after any reply his ear stays open (ear_wait) and directed() decides if it was for him.
    A loop, not recursion, so a long talk never grows the stack. `woke`: started by the wake word."""
    mode = None
    while True:
        left = {}                                              # exchange() fills "again"; survives its early returns
        exchange(tier, follow, woke, mode, left, typed)
        mode = left.get("again")
        if typed is not None or not mode or setting("JarvisFollowUp", "1") != "1" or cancel.is_set():
            return
        follow, woke = follow + 1, False


def exchange(tier, follow, woke, mode, left, typed=None):
    """One turn. mode: None, or what the last one left open ("ear"); what this one leaves open goes in
    left["again"] (a dict, not a return value: a `return` inside the try below would drop it)."""
    global history, last_turn
    if not busy.acquire(blocking=False):
        return
    way = {}                                                   # 6j: which path answered; logged once in finally
    cancel.clear()
    typed_turn[0] = typed is not None
    turn_id[0] = time.time()
    threading.Thread(target=watchdog, args=(turn_id[0],), daemon=True).start()
    try:
        if tier >= 3:
            return
        t_click = time.time()
        miss = missing_packages()
        if miss:
            problem("Setup needed - missing " + ", ".join(miss) + ". Run Control Center > JARVIS > SETUP")
            return
        if setting("JarvisGPU", "prefer").lower() == "require" and not gpu():   # never a turn on the CPU
            S.set(err="RTX is off - switch the laptop to hybrid graphics (JarvisGPU=require)")
            reply_line("My graphics card is off.", muted())
            return
        S.set(state="listening", level=0.0, err="")
        try:                                                   # 7a: a click is how a muted microphone comes back
            if typed is None and mic_volume()[0]:
                mic_volume(mute=False)
                log("microphone: unmuted by the click")
        except Exception as e:
            log(f"microphone check failed ({type(e).__name__})")
        if not ensure_ollama():
            problem("Ollama isn't running or installed - run Control Center > JARVIS > SETUP")
            return
        model = pick_model(tier)
        if not model:
            want = setting("JarvisModel", "llama3.1:8b")
            problem(f"Model {want} is not downloaded (Control Center > JARVIS > MODEL, or: ollama pull {want})")
            return
        if follow:
            time.sleep(0.3)                                    # let the last of his own voice fade before the microphone opens
        else:
            warm(model)
            threading.Thread(target=prepare_fillers, daemon=True).start()   # cheap if nothing changed
            if typed is None:
                time.sleep(chime())                            # don't record the chime
        log(f"timing: click -> listening {time.time() - t_click:.2f}s")
        t_listen = time.time()
        hud = []
        reading = threading.Thread(target=lambda: hud.append(sensors()), daemon=True)
        reading.start()                                        # read while you speak, so it costs the reply nothing
        audio = None if typed is not None else listen(patience=max(ear_wait(), follow_name_wait()), dim_after=ear_wait()) if follow else listen()
        if (audio is None and typed is None) or cancel.is_set():
            return
        t_spoke = way["t"] = time.time()
        log(f"timing: listening -> end of speech {t_spoke - t_listen:.2f}s")
        S.set(state="thinking", level=0.0)
        try:
            text = typed if typed is not None else transcribe(audio)
        except ImportError:
            problem("Speech recognition isn't installed - run Control Center > JARVIS > SETUP")
            return
        log(f"timing: end of speech -> text {time.time() - t_spoke:.2f}s")
        log(f"you: {len(text.split())} words")                # counts only: the words stay in the pop-up log
        way.update(kind="silence", via="rule", result="nothing said")   # replaced below once words came
        if not text and woke:                                  # FR6 L9: likely a false wake - end quietly
            way.update(kind="false_wake")
            log("transcript: nothing after the wake word - ended quietly")
            return
        if not text and not follow and not cancel.is_set():   # spoke but nothing came out: ask once (silence on a follow-up just ends)
            way.update(result="asked again")
            quiet = muted()
            reply_line("Sorry, I didn't catch that.", quiet)
            left["again"] = not quiet and "ear"
            return
        if not text or cancel.is_set():
            return
        if follow and onset[0] > ear_wait() and strip_name(text) == text:   # 8a: late in the open ear and no name: room talk
            way.update(kind="ear", result="late, no name - dropped")
            log("ear: started late without his name - dropped")
            return
        answering = time.time() < offer.get("expires", 0) or (recent["me"] or "").rstrip().endswith("?")
        heard_as = directed(text, answering) if mode == "ear" else "yes"
        if heard_as != "yes":
            way.update(kind="ear", result="not for me - quiet" if heard_as == "no" else "asked if for me")
        if heard_as == "no":                                   # a fragment or room noise: no answer, the window ends
            log("ear: not for me - stayed quiet")
            return
        if heard_as == "ask":                                  # unsure: ask once; "yes" answers what was said
            log("ear: unsure - asked")
            convo_add("U", text)
            reply_line(room_ask(), muted())
            offer.clear()
            offer.update(room=text, expires=time.time() + 30 + follow_wait())
            left["again"] = not muted() and "ear"
            return
        convo_add("U", text)
        quiet = muted()
        for k in ("kind", "via", "result"):                   # words came: each path below sets its own
            way.pop(k)

        def fixed(reply):
            """Say a fixed reply, keep it in the chat history, and listen once more unless he was told to drop it."""
            global history, last_turn
            way["result"] = ("refused - not built" if reply == CANT else "refused - unclear command" if reply == NEAR_MISS
                             else way.get("result") or "said")
            reply_line(reply, quiet)
            active(text)
            # stamped, so "7:00 AM tomorrow" in the reply still means the right day after midnight
            history += [{"role": "user", "content": f"[{datetime.now():%a %d %b, %I:%M %p}] {text}"},
                        {"role": "assistant", "content": reply}]
            last_turn = time.time()
            # S2-10: after any reply the ear stays open ("undo" is just one thing it can hear); not after "Cancelled."
            left["again"] = not quiet and not cancel.is_set() and not NO_FOLLOW.match(reply) and "ear"
        S.set(err="")
        fact = offer.pop("fact", None) if time.time() < offer.get("expires", 0) else None
        room = offer.pop("room", None) if time.time() < offer.get("expires", 0) else None
        closing = offer.pop("close", None) if time.time() < offer.get("expires", 0) else None
        offer.clear()
        plain = " ".join(re.sub(r"[^a-z]+", " ", strip_name(text).lower()).split())
        if room and is_yes(text):                              # "Are you talking to me, sir?" "Yes": answer what was said
            text = room
        if closing and is_yes(text):                           # 9e: the yes to "Want me to close it?" is the confirmation
            way.update(kind="act", action="close", via="rule", lane="command")
            ok = run_action("close", closing, pending=("close", closing))
            way["result"] = "done" if ok else "failed"
            fixed("Done." if ok else "That didn't work.")
            return
        if fact and (is_yes(text) or re.fullmatch(r"(?:yes )?(?:please )?(?:remember|save|note) (?:that|it)(?: please)?", plain)):
            way.update(kind="memory", action="save", via="rule", lane="command")
            fixed(memory_reply("save", fact))
            return
        said = " ".join(re.sub(r"[^a-z' ]", " ", strip_name(text).lower().replace("’", "'")).split())
        polite = text != room and next((r for rx, r in COURTESY if rx.fullmatch(said)), None)
        if polite and not (woke and heard_score[0] < -1.0):  # a weak "Thank you." after a wake is Whisper's noise phrase
            way.update(kind="courtesy", via="rule")
            name = setting("JarvisCallMe", "").strip()
            reply_line(polite.replace("{name}", f", {name}" if name else ""), quiet)
            left["again"] = not quiet and polite.startswith("Hello") and "ear"   # a hello is the start of a talk
            return
        if text != room and (polite or ENDERS.fullmatch(said)):
            way.update(kind="control", via="rule")             # control check before any routing: never reaches the model
            log("control: ended by you")
            return
        m = NEW_TOPIC.match(strip_name(text))
        way.update(kind="new_topic", via="rule")               # replaced below unless it was "new topic" alone
        if m:                                                  # files the window; "new topic, <question>" goes on without it
            file_active()
            last.clear()                                       # M1b: "cancel it" no longer points back
            text = strip_name(text)[m.end():].strip()
            if not text:
                fixed("Okay.")
                history.clear()                                # "new topic" / "Okay." is not talk to keep
                return
        if quiet_talk.TALK.fullmatch(said) and quiet_talk.talk():   # 8c: "you can talk" ends QUIET for this class only
            way.update(kind="quiet", via="rule")
            quiet = muted()
            fixed("Okay, I can talk." if not quiet else "Okay.")
            return
        # "show me what you've said" / "close the log": handled here, no model needed
        way["kind"] = "log"
        if HIDE_LOG.search(text):
            S.set(pop="close")
            reply = "Closing the log."
            convo_add("J", reply)
            if not quiet:
                speak_all([reply])
            return
        if SHOW_LOG.search(text):
            S.set(pop="open")
            reply = "Here's everything we've said."
            convo_add("J", reply)
            if not quiet:
                speak_all([reply])
            return
        kind, action, target, prompt, via = understand(text, model, quiet, room)
        way.update(kind=kind, action=action, via=via)
        if kind == "room":                                     # asked once; a "yes" answers it in full
            log("transcript: not for me? asked")
            reply_line(room_ask(), quiet)
            offer.update(room=text, expires=time.time() + 30 + follow_wait())
            left["again"] = not quiet and "ear"
            return
        if kind == "heard":
            fixed(f"I heard: {recent['you']}" if recent["you"] else "I haven't heard anything yet.")
            return
        if kind == "again":
            fixed(recent["me"] or "I haven't said anything yet.")
            return
        if cancel.is_set():                                    # stopped while the model read it: nothing runs
            return
        blocks = info_blocks(text) if kind == "chat" else set()
        lane = way["lane"] = lane_of(kind, blocks)
        empty = no_data(text, blocks)
        if empty:                                              # no data, no model
            fixed(empty)
            return
        # shortcut: reminders and alarms are not read back (he says the time back and "undo" exists), add if needed
        recent["you"] = text
        extra, close_offer = "", None
        if kind in ("remind", "memory", "multi") and prompt and prompt.startswith("Did you say: "):
            if not ask_yes(prompt, quiet):                     # an act asks below, with the same prompt
                way["result"] = "left - no yes"
                log(f"{kind} {action} not confirmed (Whisper unsure)")
                fixed("Cancelled.")
                return
            prompt = None
        if kind == "multi":                                    # "set an alarm for 7 and a timer for 10 minutes": in order
            replies, steps = [], []
            for part in target:                                # each part records its own undo: keep them all
                seen = list(undo)
                replies.append(command_reply(*part, quiet))
                if undo and list(undo) != seen:
                    steps.append(list(undo))
            if len(steps) > 1:
                undo[:] = [min(s[0] for s in steps), "multi", steps]
            quiet = muted()
            fixed(" ".join(replies))
            return
        if kind == "diag":                                     # 9a: code finds; it words the answer itself or hands over findings only
            if setting("JarvisDiagnose", "1") != "1":
                fixed("Diagnosis is off.")
                return
            filler("diag", quiet)
            line, items = diagnose(action, target, _whisper_dev[0] == "cpu" or ollama_on_cpu(model))
            top = items[0] if items else None                  # only the worst finding, and only when it is what was asked about
            asked = {"cpu": "of the CPU", "memory": "of memory", "gpu": "the GPU"}.get(action, "")
            exe = (top and top["closable"] and asked in top["text"] and running_window(top["app"])) or None
            exe = None if exe and is_protected(exe) else exe
            if line:
                fixed(line + (" Want me to close it?" if exe else ""))
                if exe:
                    offer.update(close=exe, expires=time.time() + 30 + follow_wait())
                return
            extra, close_offer = prompt_findings(items), exe
        if kind != "act" or prompt is None:
            reply = command_reply(kind, action, target, prompt, quiet)
            if reply is not None:
                if action in ("mute", "unmute", "volume"):     # the reply follows the new state: shown if now silent
                    quiet = muted()
                fixed(reply)
                return
        if kind == "act":
            # two-phase: ask, and listen for the answer (15 s) without another click
            if ask_yes(prompt, quiet):
                ok = run_action(action, target, pending=(action, target))
                way["result"] = "done" if ok else "failed"
                unsure = prompt.startswith("Did you say: ")    # then say what really happened, as an unasked command does
                fixed(("Added." if action == "todo" else done_line(action, target) if unsure or action == "sleep" else "Done.") if ok else "That didn't work.")
            else:
                way["result"] = "left - no yes"
                log(f"action {action} not confirmed")
                fixed(memory_reply("save", target[1]) + " I kept the old one too." if action == "replace_fact" else "Cancelled.")
            return
        if kind == "notes":
            filler("notes", quiet)
            hits = smart_search(target or text)
            if hits is None:                                   # no ChromaDB: keyword search
                root, hits = search_notes(target or text)
            else:
                root = vault_dir()
            if not root:
                extra = "\nNOTE SEARCH: no vault is set (Control Center > JARVIS > NOTES VAULT)."
            elif hits:
                extra = "\nNOTE SEARCH RESULTS (from the user's vault - answer from these):\n" + "\n".join(
                    f"- {name}: {snip}" for _, name, snip in hits)
            else:
                extra = f"\nNOTE SEARCH: nothing in the vault matched '{target}'."
        elif kind == "apps":
            filler("apps", quiet)
            apps = start_apps()
            names = sorted({n for n, _ in apps or []})
            if apps is None:
                extra = "\nINSTALLED APPS: the app list isn't ready yet (the HUD is still scanning)."
            elif target:
                app = best_app(target)
                extra = f"\nINSTALLED APP CHECK: '{target}' -> " + (f"yes, installed as {app[0]}." if app else "not found in the Start menu.")
            else:
                extra = f"\nINSTALLED APPS ({len(names)}): " + ", ".join(names[:120])
        elif kind == "guard":
            extra = ("\nGUARDRAIL: this request is destructive or a joke. Nothing will be executed - you have no ability to "
                     "run commands. Play along in character with dry wit if it's clearly playful, or decline politely if "
                     "it's serious. Never claim to have actually done it.")
            log("guardrail: request handled in persona only")
        elif kind == "brief":
            extra = "\n" + BRIEFING
        apart = kind in ("brief", "notes")                     # these neither send nor file the window
        past = [] if apart else active(text)
        reading.join(1.5)                                      # a stuck sensor never holds the reply: its lines are left out
        # the question and the one before it pick the blocks, so "and tomorrow?" after a calendar question still has it
        ask = text + (" " + past[-2]["content"] if len(past) >= 2 else "")
        readings = "\n".join(h for h in hud if h).splitlines()
        want = wants(ask, kind)
        if "pc" not in want:                                   # not a PC question: at most the schedule, and only if it's about time
            readings = [r.replace("Pending:", "Pending (don't bring it up unless asked about alarms, reminders or timers):", 1)
                        for r in readings if r.startswith("Pending:") and "pending" in want]
        extra += "" if apart else recall(text)                # M2: an earlier talk, only when the question is about it
        extra += INFO_PROMPT if lane == "info" else ""
        messages = fit_context([{"role": "system", "content": system_prompt(ask, kind) + "".join("\n" + r for r in readings) + extra}],
                               past, {"role": "user", "content": text})
        collected, spoke = [], None
        way["via"] = "model"
        log(f"timing: end of speech -> reply start {time.time() - t_spoke:.2f}s")
        stream = chat_stream(model, messages, 0 if lane == "info" else 0.5)
        if quiet and setting("JarvisMutedPopup", "1") == "1":
            say_text_only(no_claims(sentences_from(stream, collected), collected), collected)
        else:
            spoke = speak_all(no_claims(sentences_from(stream, collected), collected))
        reply = "".join(collected).strip()
        if spoke is not None and cancel.is_set():              # 8-A2: talked over: keep only what he got to say
            reply = spoke
        convo_add("J", reply)                                  # at once: the live line was just cleared (empty: no-op)
        S.set(state="idle", level=0.0)                        # done talking: the HUD doesn't wait for the GPU check
        if ollama_on_cpu(model):
            chat_to_gpu(model)
        else:
            _moved.discard(model)
        log(f"timing: end of speech -> reply done {time.time() - t_spoke:.2f}s ({model})")
        if not reply and not cancel.is_set():
            problem(f"{model} gave no answer - try again, or pick another model in Control Center > JARVIS")
            return
        log(f"jarvis: {len(reply)} characters")
        way["result"] = "answered"
        recent["me"] = reply
        if not apart and reply:
            history += [{"role": "user", "content": text}, {"role": "assistant", "content": reply}]
            last_turn = time.time()
        S.set(say=reply)
        fact = learnable(text) if kind == "chat" and not cancel.is_set() else ""
        if fact:                                               # M4a-3: one offer; the next turn's yes saves it
            reply_line("Want me to remember that?", quiet)
            offer.update(fact=fact, expires=time.time() + 30 + follow_wait())
        if close_offer and reply and not cancel.is_set():      # 9e: one offer; the next turn's yes closes it
            reply_line("Want me to close it?", quiet)
            offer.update(close=close_offer, expires=time.time() + 30 + follow_wait())
        left["again"] = not quiet and not cancel.is_set() and "ear"   # fixed replies set it in fixed()
    except urllib.error.URLError as e:
        problem(f"Lost the connection to Ollama ({e.reason}) - is it still running?")
        live("")
    except Exception as e:
        way["result"] = "error"
        log(f"turn failed: {e!r}")
        problem(str(e).split("\n")[0][:110])
        live("")
    finally:
        if "kind" in way:                                      # only names from the code, never words you said
            act = way.get("action")
            act = f" {act}" if isinstance(act, str) and re.fullmatch(r"[a-z_]+", act) else ""
            tag = f"{way['lane']}." if "lane" in way else ""
            done = "stopped" if cancel.is_set() else way.get("result", "said")
            log(f"route: {tag}{way['kind']}{act} via {way['via']}, total {time.time() - way['t']:.2f}s -> {done}")
        S.set(state="idle", level=0.0)
        busy.release()


# ------------------------------------------------------------------ wake word ("Hey Jarvis")
# JarvisWakeWord=1: a small background thread listens for "Hey Jarvis" with openWakeWord (runs on your PC, about
# 1-3 % of one CPU core; audio is checked in 80 ms pieces and never stored or sent anywhere). When it hears it, it
# starts a turn exactly like a click. It pauses while Jarvis is busy, while the HUD is on STEALTH, and when turned off.
def hud_tier():
    try:
        return int(float(setting("PerfTier", "0")))
    except ValueError:
        return 0


def barge_in():
    """JarvisBargeIn: off | wake ("Hey Jarvis" stops him mid-sentence, the default) | voice (any speech, headphones only)."""
    v = setting("JarvisBargeIn", "wake").strip().lower()
    return v if v in ("off", "wake", "voice") else "wake"


def barge_turn(follow):
    """The turn after he was talked over: waits for the stopped one to let go (up to 5 s), then listens once."""
    end = time.time() + 5
    while busy.locked():
        if time.time() > end:
            log("barge-in: the stopped turn didn't end - not listening")
            return
        time.sleep(0.05)
    turn(hud_tier(), follow, True)


# ------------------------------------------------------------------ wake word training (plan R5-6, step 6a)
# Your own "Hey Jarvis", "Hey" and "Jarvis" become small checks next to the normal score (Fix Round 5 N1).
# The recordings stay in memory and are never written; only the checks are saved, as Data\wake_<style>.pkl.
WAKE_STYLES = (("hey_jarvis", "Hey Jarvis", 'say "Hey Jarvis"'),
               ("hey", "Hey", 'say just "Hey"'),
               ("jarvis", "bare Jarvis", 'say just "Jarvis"'))
WAKE_FLOOR = 0.1                       # the lowest normal score a moment needs to count as an example
WORD_STYLES = ("hey", "jarvis")        # single words: examples are the moments with speech, not a normal score
                                       # (the normal model knows only the whole phrase, a bare "Hey" may never score)


def heard_speech(oww):
    """The speech filter heard speech 0.4-0.56 s ago, the same frames openWakeWord itself checks."""
    vad = list(getattr(getattr(oww, "vad", None), "prediction_buffer", []))[-7:-4]
    return bool(vad) and max(vad) >= 0.5


def speech_feats(clip, oww):
    """The openWakeWord features of every 80 ms moment of `clip` in which the speech filter hears speech."""
    import numpy as np
    out = []
    oww.reset()
    if hasattr(oww, "vad"):
        oww.vad.prediction_buffer.clear()             # reset() keeps it: the last clip's speech would count here
    for i in range(0, len(clip) - 1280, 1280):
        oww.predict(clip[i:i + 1280])
        if heard_speech(oww):
            out.append(oww.preprocessor.get_features(oww.model_inputs["hey_jarvis"]))
    return np.vstack(out) if out else np.empty((0, oww.model_inputs["hey_jarvis"], 96))


# shortcut: a click stops it only between clips (at most 15 s late); a stoppable recorder if that ever matters
def record(sec):
    """`sec` seconds from the microphone as 16 kHz int16, the form openWakeWord reads."""
    import sounddevice as sd
    if not mic.acquire(timeout=3):
        raise RuntimeError("The microphone is busy - try again")
    try:
        a = sd.rec(int(16000 * sec), samplerate=16000, channels=1, dtype="int16", device=mic_device())
        sd.wait()
        return a[:, 0]
    finally:
        mic.release()


def train_wake():
    """Control Center WAKE WORD > TRAIN: each style six times after a ding, then 15 s of normal talk as the
    "not Jarvis" examples. Holds the turn lock, so the wake word lets go of the microphone; a click stops it."""
    import pickle
    import numpy as np
    from openwakeword.model import Model
    from openwakeword.custom_verifier_model import get_reference_clip_features, train_verifier_model
    with busy:
        cancel.clear()
        turn_id[0] = time.time()
        try:
            clips = {}
            for name, _, how in WAKE_STYLES:
                reply_line(f"After each ding, {how}. Six times.", False)
                clips[name] = []
                for _ in range(6):
                    S.set(state="listening", level=0.0)        # not "speaking": the wake word would keep the microphone
                    play_samples(*ding())
                    if cancel.is_set():
                        return
                    clips[name].append(record(3))
            reply_line("Now talk normally for fifteen seconds, about anything, without my name.", False)
            S.set(state="listening", level=0.0)
            neg = record(15)
            if cancel.is_set():
                return
            try:                                               # the speech filter picks the moments of a bare word
                oww = Model(wakeword_models=["hey_jarvis"], inference_framework="onnx", vad_threshold=0.5)
            except Exception as e:
                log(f"train: without the speech filter ({type(e).__name__}) - Hey and bare Jarvis stay off")
                oww = Model(wakeword_models=["hey_jarvis"], inference_framework="onnx")
            pad = np.zeros(16000, dtype=np.int16)              # the model scores 0 for its first frames
            oww.reset()
            negf = get_reference_clip_features(np.concatenate([pad, neg]), oww, "hey_jarvis", threshold=0.0, N=1)
            word = {n: np.vstack([speech_feats(np.concatenate([pad, c]), oww) for c in clips[n]]) for n in WORD_STYLES}
            made = 0
            old = os.path.join(DATA, "wake_hey_pause.pkl")     # the dropped "Hey ... Jarvis" style
            if os.path.exists(old):
                os.remove(old)
            for name, label, _ in WAKE_STYLES:
                path = os.path.join(DATA, f"wake_{name}.pkl")
                peak, pos = 0.0, []
                for c in clips[name]:
                    c = np.concatenate([pad, c])
                    oww.reset()
                    peak = max([peak] + [oww.predict(c[i:i + 1280])["hey_jarvis"] for i in range(0, len(c) - 1280, 1280)])
                    if name not in WORD_STYLES:
                        oww.reset()
                        pos.append(get_reference_clip_features(c, oww, "hey_jarvis", threshold=WAKE_FLOOR, N=3))
                pos = word[name] if name in WORD_STYLES else np.vstack(pos)
                log(f"train: {label} " + (f"from {len(pos)} word samples" if name in WORD_STYLES
                                          else f"peaks {peak:.2f} ({len(pos)} examples)"))
                if len(pos) == 0:                              # never reached the floor / no speech heard: that way stays off
                    if os.path.exists(path):
                        os.remove(path)                        # an older check must not outlive this training
                    continue
                # "Hey" learns that your "Jarvis" is not it, and the other way round
                other = [word[o] for o in WORD_STYLES if o != name and name in WORD_STYLES]
                neg_all = np.vstack([negf] + other)
                check = train_verifier_model(np.vstack([pos, neg_all]), np.array([1] * len(pos) + [0] * len(neg_all)))
                with open(path + ".tmp", "wb") as f:
                    pickle.dump(check, f)
                os.replace(path + ".tmp", path)
                made += 1
            reply_line(f"Done. I learned {made} of the 3 ways." + ("" if made == 3 else " The log says which."), False)
        except Exception as e:
            log(f"wake training failed: {e!r}")
            problem("Wake word training failed")
        finally:
            S.set(state="idle", level=0.0)


def wake_way(score, held, mine, now, hey_until, need, easy, hard, gap):
    """Which way wakes him on this 80 ms moment (or None), and until when a "Hey" waits for "Jarvis".
    score: the normal "Hey Jarvis" score; held: it was >= need on the moment before too; mine: your trained checks'
    scores by style (only while speech is heard). "Hey" alone never wakes him."""
    if score >= need and held:                                 # W0, the backup: 2 moments in a row
        return "W0", 0.0
    if score >= WAKE_FLOOR and mine.get("hey_jarvis", 0.0) >= 0.5:   # HV: a soft "Hey Jarvis" in your voice
        return "HV", 0.0
    if now <= hey_until and mine.get("jarvis", 0.0) >= hard:   # HJ: your "Jarvis" within `gap` s of your "Hey"
        return "HJ", 0.0
    if easy > 0 and mine.get("hey", 0.0) >= easy and now > hey_until:
        hey_until = now + gap
    return None, hey_until


def wake_checks():
    """Your trained checks from Data\\wake_<style>.pkl; a missing or broken one leaves that way off."""
    import pickle
    checks = {}
    for name, _, _ in WAKE_STYLES:
        path = os.path.join(DATA, f"wake_{name}.pkl")
        if os.path.exists(path):
            try:
                with open(path, "rb") as f:
                    checks[name] = pickle.load(f)
            except Exception as e:
                log(f"wake: check {name} not loaded ({type(e).__name__})")
    return checks


def wake_loop():
    import numpy as np
    model, stream, warned = None, None, False
    off, mic_bad, best, minute = None, False, 0.0, time.time()   # why it is off (logged once per change); top score this minute
    heard_talk, no_vad = 0, False                              # 80 ms blocks heard while he speaks; "voice" without a VAD logged
    spot = None                                                # the stop words (StopWords); False: not available
    checks, last_score, hey_until = None, 0.0, 0.0             # your trained checks (loaded with the model); FR5 N1

    def load(**vad):
        import openwakeword
        from openwakeword.model import Model
        try:
            return Model(wakeword_models=["hey_jarvis"], inference_framework="onnx", **vad)
        except ImportError:
            raise
        except Exception:
            openwakeword.utils.download_models(model_names=["hey_jarvis"])   # first run: fetch the model
            return Model(wakeword_models=["hey_jarvis"], inference_framework="onnx", **vad)

    def drop():
        """Close the microphone and hand it back."""
        nonlocal stream
        if stream is not None:
            try:
                stream.close()
            except Exception:
                pass
            stream = None
            mic.release()
    while True:
        try:
            tier = hud_tier()
            why = ("turned off" if setting("JarvisWakeWord", "1") != "1" else "Jarvis off"
                   if setting("JarvisEnabled", "1") != "1" else f"HUD tier {tier}" if tier >= 3 else None)
            if why != off:
                off = why
                WAKE_OFF[0] = why
                log(f"wake off: {why}" if why else "wake on")
            barge = barge_in()
            talking = busy.locked() and getattr(S, "state", "") == "speaking" and barge != "off"
            heard_talk = heard_talk if talking else 0
            if why or (busy.locked() and not talking):         # mic kept only while he speaks: listen() gets it at once
                drop()
                time.sleep(0.05 if barge != "off" and busy.locked() and not why else 0.5)   # catch him starting to speak
                continue
            if model is None:
                try:
                    model = load(vad_threshold=0.5)                # Silero VAD: no wake on music or a TV without speech
                except ImportError:
                    raise
                except Exception as e:
                    log(f"wake word: without the speech filter ({type(e).__name__})")
                    model = load()
                log("wake word ready - say 'Hey Jarvis'")
            if stream is None:
                import sounddevice as sd
                if not mic.acquire(timeout=0.5):               # a turn is recording
                    continue
                try:
                    stream = sd.InputStream(samplerate=16000, channels=1, dtype="int16", blocksize=1280, device=mic_device())
                    stream.start()
                    model.reset()
                    mic_bad = False
                    found = wake_checks() if getattr(model, "vad", None) is not None else {}   # re-read: a training may
                    if checks is None or set(found) != set(checks):                               # have just ended
                        log(f"wake: your checks: {', '.join(found) or 'none (train in Control Center)'}")
                    checks, last_score, hey_until = found, 0.0, 0.0
                except Exception as e:
                    if stream is None:
                        mic.release()
                    drop()
                    if not mic_bad:                            # once per outage, not every 5 s
                        mic_bad = True
                        problem(f"Wake word: no microphone ({str(e).splitlines()[0][:60]})", popup=False)
                    time.sleep(5)
                    continue
            data, _ = stream.read(1280)
            if talking and spot is not False:
                try:
                    if spot is None:
                        spot = StopWords()
                        log("stop words ready")
                    hit = spot.feed(data[:, 0], fresh=heard_talk == 0)
                except Exception as e:                         # no vosk / model: stop by "Hey Jarvis" or a click as before
                    spot, hit = False, None
                    log(f"stop words off ({type(e).__name__}: {str(e)[:80]})")
                if hit:
                    log(f"stop word heard ({hit})")
                    stop_now("stop word")
                    drop()
                    model.reset()
                    heard_talk = 0
                    continue
            scores = model.predict(np.asarray(data[:, 0], dtype=np.int16))
            try:
                need = max(0.2, min(0.9, float(setting("JarvisWakeSensitivity", "0.5"))))
            except ValueError:
                need = 0.5
            best = max(best, max(scores.values()))
            if time.time() - minute >= 60:                     # a near miss shows what sensitivity would have worked
                if best >= 0.1:
                    log(f"wake: best {best:.2f} this minute")
                best, minute = 0.0, time.time()
            follow = None                                      # set when he is talked over: 0 = "Hey Jarvis", 1 = any voice
            if talking:
                heard_talk += 1
                if barge == "voice" and getattr(model, "vad", None) is None and not no_vad:
                    no_vad = True
                    log("barge-in: no speech filter loaded - only 'Hey Jarvis' stops him")
                vad = list(getattr(getattr(model, "vad", None), "prediction_buffer", []))[-7:]
                if barge == "voice" and heard_talk >= 7 and len(vad) == 7 and min(vad) >= 0.5:   # 0.56 s of speech
                    follow = 1                                 # a follow-up: "stop" ends it, anything else is a command
                need = min(need + 0.2, 0.95)                   # his own voice is in the room too
                if follow is None and time.time() < name_until[0]:   # he is saying "Jarvis" himself
                    continue
            score, held, last_score, way = max(scores.values()), last_score >= need, max(scores.values()), None
            if follow is None and talking and score >= need:   # over his voice: the normal score alone, as before
                follow = 0
            elif follow is None and not talking:
                mine = {}
                if checks and heard_speech(model):             # silence costs nothing
                    feats = model.preprocessor.get_features(model.model_inputs["hey_jarvis"])
                    mine = {n: float(c.predict_proba(feats)[0][-1]) for n, c in checks.items()}
                try:
                    easy, hard = (float(setting("JarvisWakeEasy", "0.5")), float(setting("JarvisWakeHard", "0.35")))
                    gap = float(setting("JarvisWakeGap", "5"))
                except ValueError:
                    easy, hard, gap = 0.5, 0.35, 5.0
                way, hey_until = wake_way(score, held, mine, time.time(), hey_until, need, easy, hard, gap)
                follow = 0 if way else None
            if follow is not None:
                last_score, hey_until = 0.0, 0.0
                log(f"wake word heard ({score:.2f}, {way})" if not talking else f"barge-in ({'voice' if follow else 'wake'})")
                if talking:
                    stop_now("barge-in")
                drop()
                model.reset()
                if talking:
                    threading.Thread(target=barge_turn, args=(follow,), daemon=True).start()
                else:
                    threading.Thread(target=turn, args=(hud_tier(), 0, True), daemon=True).start()
                time.sleep(1.0)                                # let the turn take the microphone
        except ImportError as e:
            if not warned:
                missing_mod = getattr(e, "name", None) or str(e)
                log(f"wake word: missing module - {e}")
                problem(f"Wake word needs {missing_mod} - run: py -m pip install openwakeword", popup=False)
                warned = True
            time.sleep(10)
        except Exception as e:
            drop()
            if model is None and not warned:                   # no model: shown in the Control Center, once
                warned = True
                problem(f"Wake word: the model didn't load ({type(e).__name__})", popup=False)
            else:
                log(f"wake word: {e!r}")
            time.sleep(5)


# ------------------------------------------------------------------ main loop: watch the command file
owner = False


def preload_ollama():
    """Load the chat model into memory at startup (it stays for JarvisKeepAlive minutes)."""
    if ensure_ollama():
        m = pick_model(0)
        if m:
            warm(m)


def preload_whisper():
    """Load the speech-recognition model at startup, so the first thing you say isn't waiting on it."""
    try:
        whisper()
    except Exception as e:
        log(f"whisper preload failed: {e!r}")


def unload_idle(now, since):
    """Free the speech models after JarvisIdleUnload minutes without a turn; they load again on the next one."""
    try:
        mins = float(setting("JarvisIdleUnload", "10"))
    except ValueError:
        mins = 10.0
    if mins <= 0 or busy.locked() or now - since < mins * 60 or not (hearing._whisper or _engines):
        return False
    hearing._whisper = None                        # the model lives in jarvislib\hearing.py
    _engines.clear()
    gc.collect()
    log(f"idle for {mins:g} min - speech models unloaded")
    return True


def main():
    global owner
    if not single_instance():
        return
    owner = True
    started = time.time()
    log(f"started ({RES}), Python {sys.version.split()[0]}")
    unduck()                                                   # a crash while he listened left the volume down
    miss = missing_packages()
    S.set(state="idle", level=0.0, err=("Setup needed - missing " + ", ".join(miss)) if miss else "")
    threading.Thread(target=preload_ollama, daemon=True).start()
    threading.Thread(target=stop_key_loop, daemon=True).start()
    if not miss:
        # one at a time, here: imported at once by the threads below, numpy half-loaded broke the others (wake word, voice)
        for name in ("numpy", "onnxruntime", "faster_whisper", "openwakeword", "sounddevice"):
            try:
                __import__(name)
            except Exception as e:
                log(f"start-up import of {name} failed ({type(e).__name__})")
        list_mics()
        threading.Thread(target=preload_whisper, daemon=True).start()
        threading.Thread(target=prepare_fillers, daemon=True).start()
        threading.Thread(target=wake_loop, daemon=True).start()
        threading.Thread(target=index_loop, daemon=True).start()
    last_mtime = os.path.getmtime(CMD_FILE) if os.path.exists(CMD_FILE) else 0
    beat, missing, checked, ringing = 0.0, 0, 0.0, None
    while True:
        try:
            time.sleep(0.1)
            now = time.time()
            if now - beat >= 2:
                beat = now
                S.expire_err(now)                              # 9-L1: a pop-up-less error is gone after 60 s
                S.set()                                        # heartbeat
                unload_idle(now, max(turn_id[0], started))
                if compact_due(now, max(turn_id[0], started)):  # M3: old talk into checked facts, once a day
                    threading.Thread(target=daily_memory, daemon=True).start()
                gpu_watch(now)
                missing = 0 if rainmeter_running() else missing + 1
                if missing >= 15:                              # Rainmeter gone for 30 s: quit
                    log("Rainmeter closed - exiting")
                    return
            if now - checked >= 1 and not (ringing and ringing.is_alive()):   # one alarm at a time
                checked = now
                if due_reminders(now):
                    ringing = threading.Thread(target=alarm, daemon=True)
                    ringing.start()
            try:
                mt = os.path.getmtime(CMD_FILE)
            except OSError:
                continue
            if mt == last_mtime:
                continue
            last_mtime = mt
            with open(CMD_FILE, "r", encoding="utf-8", errors="ignore") as f:
                raw = f.read()
            parts = raw.split()
            if len(parts) < 2 or abs(now - float(parts[1])) > 30:
                continue
            if parts[0] == "WAKE":
                tier = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 0
                threading.Thread(target=turn, args=(tier,), daemon=True).start()
            elif parts[0] == "ASK":                            # 8d: typed text goes through the same turn as speech
                text = ask_text(raw)
                if not text:
                    pass
                elif busy.locked():
                    reply_line("One moment, I'm busy.", muted())
                else:
                    threading.Thread(target=turn, args=(0,), kwargs={"typed": text}, daemon=True).start()
            elif parts[0] == "CANCEL":
                stop_now("click")
            elif parts[0] == "REINDEX":
                _chroma.update(seen={}, last=0.0, failed=False)
                threading.Thread(target=chroma_index, kwargs={"force": True}, daemon=True).start()
                log("notes index: rebuilding")
            elif parts[0] == "FORGET":
                history.clear()
                log("conversation memory cleared")
            elif parts[0] == "TRAINWAKE":
                threading.Thread(target=train_wake, daemon=True).start()
            elif parts[0] == "QUIT":
                log("stopped from the Control Center")
                cancel.set()
                return
        except Exception as e:                                 # one bad read never kills the service
            log(f"main loop: {e!r}")
            time.sleep(1)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log(f"crashed: {e!r}")
        raise
    finally:
        if owner:                                              # tell the HUD we're gone (shows OFFLINE)
            unduck()                                           # QUIT while he listened: put the volume back now
            try:
                write_atomic(STATE_FILE, "T 0\nSTATE idle\n")
            except OSError:
                pass
