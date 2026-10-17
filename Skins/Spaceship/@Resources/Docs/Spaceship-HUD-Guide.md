# Spaceship HUD — Complete Guide

Your Rainmeter "Spaceship" cockpit: a full-screen HUD that turns the desktop into a ship's bridge, with live system telemetry, an app launcher, laptop hardware controls, your calendar, Gmail, Obsidian to-dos, network and audio, all in one themed interface.

This guide covers **everything the HUD can do**, **how to use every part of it**, and **everything it has access to** on your PC and online.

---

## Contents

1. [Quick start](#1-quick-start)
2. [Layout at a glance](#2-layout-at-a-glance)
3. [Universal controls](#3-universal-controls)
4. [Module reference](#4-module-reference)
5. [Control Center](#5-control-center)
6. [Startup sequence](#6-startup-sequence)
7. [Performance tiers and the MASTER switch](#7-performance-tiers-and-the-master-switch)
8. [The ShipCore helper](#8-the-shipcore-helper)
9. [Everything the HUD has access to](#9-everything-the-hud-has-access-to)
10. [Settings reference (Settings.inc)](#10-settings-reference-settingsinc)
11. [Customizing apps (Apps.ini)](#11-customizing-apps-appsini)
12. [Installing updates and undoing them](#12-installing-updates-and-undoing-them)
13. [Troubleshooting](#13-troubleshooting)
14. [File map](#14-file-map)

---

## 1. Quick start

| You want to… | Do this |
|---|---|
| Open the settings | Right-click any panel → **Control Center** |
| Launch an app | Click its slot, or its hologram/LAUNCH on a big category panel |
| Bring an open app to the front | Click it again — the HUD focuses the existing window instead of opening a duplicate |
| See every installed app | Right-click any panel → **App drawer (CARGO)**, or the **CARGO** button on the top console |
| Change volume | Scroll anywhere on the round audio panel (bottom right) |
| Change brightness / power mode / refresh rate | Use the round systems dial (bottom left): click a label, then scroll |
| Hide the whole HUD instantly | **MASTER** on the top console |
| Refresh everything | Right-click any panel → **Refresh HUD** |
| Replay the boot animation | Right-click any panel → **Play startup sequence** |
| Read what something is | Hover it — a caption appears at the bottom of the HUD |

---

## 2. Layout at a glance

```
┌────────────────────────────── TOP ───────────────────────────────┐
│ POWER bar   [ALERT]   ┌───────── CONSOLE ─────────┐   BATTERY bar  │
│                       │ GPU modes + quick toggles │                │
│        GRAPH CPU   GRAPH A   GRAPH B   GRAPH RAM                  │
├──── LEFT ─────┐                                   ┌──── RIGHT ────┤
│ CATEGORY      │          TARGET RETICLE (red)     │ CATEGORY      │
│ panel (big)   │                                   │ panel (big)   │
│ MISSION CLOCK │          CENTER FLIGHT HUD        │ NETWORK block │
│ SLOT 1        │      (S&P ladder · GPU ladder)    │ SLOT 5        │
│ SLOT 2        │                                   │ SLOT 6        │
│ SLOT 3        │          CLOVER CORE              │ SLOT 7        │
│ SLOT 4        │     (voice assistant hologram)    │ SLOT 8        │
│ UPKEEP block  │                                   │ DEV block     │
├──── BOTTOM ───┴───────────────────────────────────┴───────────────┤
│ tilted PILOT screen  SYSTEMS DIAL  [strip]  AUDIO REACTOR  tilted SHIP screen │
└───────────────────────────────────────────────────────────────────┘
```

Behind everything is the **Frame**: the cockpit hull, tinted window glass, scanlines and neon accent lines. It's click-through, so it never blocks your desktop.

---

## 3. Universal controls

These work on (almost) every panel:

- **Hover:** shows a caption with what the element is and what clicking does. Captions vanish after 6 seconds or when you move away. To get classic Windows tooltips instead, set `CaptionStyle=0`.
- **Right-click menu** (Rainmeter's own menu on any panel):
  - **Control Center**: all settings (section 5)
  - **App drawer (CARGO)**: every installed app
  - **Edit mode on / off**: shows module outlines for repositioning
  - **Refresh HUD**: reloads every module
  - **Play startup sequence**: replays the boot animation
- **Scroll:** on panels with lists or values, scrolling moves through them (apps, graph sources, volume, dial values).

---

## 4. Module reference

### Top row

#### Power bar (top left)
- Total power draw in watts: CPU + GPU package power from HWiNFO, or battery discharge when unplugged.
- **Click:** opens the Control Center.

#### Alert triangle
- Shows how many warnings are active right now. Hover for the list.
- Warnings it raises:
  - **CPU HOT** (above `WarnCpuTemp`, default 92 °C)
  - **GPU HOT** (above `WarnGpuTemp`, default 85 °C)
  - **Drive nearly full** (above `WarnDiskPct`, default 90 %)
  - **CPU SATURATED** (load 95 % or more)
  - low battery and similar system issues

#### Top console (center)
Laptop hardware control through **Lenovo Legion Toolkit**.

- **GPU mode tabs:**
  - **ECO**: integrated GPU only; the RTX 5070 is powered off
  - **HYBRID**: both GPUs; the RTX wakes when an app needs it
  - **AUTO**: hybrid on AC, integrated only on battery
  - **dGPU**: discrete only through the MUX. Needs a reboot; click twice to confirm.
  - **OFF**
- **Quick settings:**
  - **Power mode**: click to cycle Quiet → Balanced → Performance (plus Custom / God Mode if present)
  - **Refresh rate**: click to toggle 60 / 165 Hz
  - **Battery conservation**: hold the charge at 80 % to protect the battery
  - **Graphics tier**: the HUD's own performance tier (section 7)
  - **dGPU light**: shows whether the RTX is awake
  - **CARGO**: opens the app drawer
  - **MASTER**: kill switch that drops the whole HUD to STEALTH, or restores it
  - **CFG**: opens the Control Center

#### Battery bar (top right)
- Battery percentage, plus time to the charge limit (charging) or time to empty (on battery).
- **Click:** Windows battery settings.

#### Four history graphs
- **GRAPH CPU** and **GRAPH RAM** are fixed.
- **GRAPH A** and **GRAPH B** are selectable. **Click** the title for the next source, **right-click** for the previous, or **scroll**.
- Sources: CPU load, memory used, GPU load, video memory, CPU temp, GPU temp, power draw, disk I/O, net down, net up, battery level.

### Left column

#### Category panel (big, top left)
- A tab rail of apps in the current category, a large neon **wireframe hologram** of the selected app, and **LAUNCH**.
- Page dots underneath switch category: rocketry, engineering, CFD, dev, electronics, creative, comms, system tools, utilities, and more.
- **Click a tab** to select it, **click the hologram** to launch the app, **scroll** to move through apps.
- **Status line:**
  - **RUNNING**: the app has a window open
  - **BACKGROUND**: the app is running without a window
  - **READY**: the app isn't running
- Default category: `Top1=` in Apps.ini.

#### Mission clock
- Countdown ring to your **next calendar event**, plus the next three events with their times.
- Colors:
  - green: an event is in progress
  - orange: under 60 minutes away
  - red: under 15 minutes away
- **Click:** opens Google Calendar. **Right-click:** sync now.
- Only reads the calendars you switch on in Control Center → DATA → CALENDARS.

#### App slots 1–4
- Each slot holds **one app** or **a whole category**.
- **Click:**
  - a single app: launches it, or brings it to the front if it's already open
  - a category: opens a pop-up list of its apps
- **Scroll:** cycles through the apps in a category slot.
- Choose what each slot holds in Control Center → APPS, or with `Slot1=`…`Slot4=` in Apps.ini.

#### Upkeep block (bottom left)
- **Diamond:** number of pending Windows updates. **Click:** Windows Update.
- **Envelope:** Gmail unread count. **Click:** opens Gmail.
- **Shield / caption:** antivirus state, and how many winget app upgrades are available. **Click:** Windows Security.
- Checked about once an hour in the background.

### Center

#### Target reticle (bright red)
Roams the upper windscreen: it glides to a new spot, locks on with a pulse, then moves on. It has two modes:

- **TO-DO mode** (when `ReticleTodo=1` and your Obsidian note has open items):
  - Locks onto your next due task: `[n]` = number of open items, the readout = countdown, and the task name sits under the rings.
  - Upcoming items appear as blips, closer to the center the sooner they're due.
  - **Click:** opens the note in Obsidian.
  - Note format: `- [ ] Statics HW 4 📅 2026-10-14 @17:00` (time optional). Tasks-plugin dates and Dataview `[due:: 2026-10-14]` both work.
- **USAGE mode** (to-dos off, or none open):
  - Locks onto the busiest process and shows its rank, CPU share and memory (`567m` = 567 MB).
  - **Click:** cycles targets 1–5. **Scroll:** same.
- **Right-click** (either mode): Task Manager.

#### Center flight HUD
- **Left ladder:** S&P 500 change today in %, from Yahoo Finance every 5 minutes while the market is open. Shows **CLOSED** when it isn't. **Click the SPX readout** to open the S&P 500 page.
- **Right ladder:** GPU clock (if HWiNFO maps it) or GPU load %.
- **Pointer on the bracket:** CPU load.
- **Diamond pipper** in the middle, and a **THR** readout.
- **Click elsewhere:** Task Manager.

#### Clover core (replaces the globe)
- **The hologram:** your plasma-orb animation, inside a rotating 3D network shell, two tilted orbit rings with satellites, and a HUD dial with voice bars.
- **States:**
  - **STANDBY:** cyan
  - **LISTENING:** deeper blue
  - **THINKING:** fast spin with a white sweep
  - **SPEAKING:** a voice echo and the shell swell with his voice
  - **OFFLINE:** dimmed
- **Problems** show in orange under the name: SETUP NEEDED, NO MICROPHONE, NO OLLAMA, NO MODEL, START FAILED, CHECK LOG.
- **Click:** talk to Clover, or stop him mid-answer. If he's offline, clicking starts him.
- **Right-click:** opens or closes the conversation pop-up.
- See section 6b for the full Clover guide.

### Right column

#### Category panel (big, top right)
Same as the left one. Default category: `Top2=` in Apps.ini.

#### Network block
- **PING:** latency to `PingHost` (default 1.1.1.1). Orange when 150 ms or more; red **LOST** when there's no reply.
- **LAN:** this PC's local IP address.
- **WAN:** your public IP address, or **OFFLINE**.
- **MBPS:** live **download ▼ / upload ▲**, meaning how much you're using right now. It's measured on the adapter Windows actually routes internet through.
- **Wi-Fi rings:** signal strength.
- **Box:** last speed-test download in Mbps. **Click it** to run a new test.
- **Click LAN / WAN** to mask the IP addresses (`XX.XXX.XX.XX`). Click again to show them.
- **Click elsewhere:** network status settings. **Right-click:** Wi-Fi settings.

#### App slots 5–8
Same as slots 1–4 (`Slot5=`…`Slot8=`).

#### Dev block (bottom right)
- Shows WSL distros running, Ollama models loaded, Tailscale state and Docker containers running. Refreshed every 2 minutes; `-` means not installed.
- **Click WSL:** Windows Terminal. **Click Ollama:** `ollama ps` in Terminal. **Click Tailscale:** the Tailscale app.

### Bottom row

#### Systems dial (round, bottom left)
Six controls around a ring:

| Label | Controls | Through |
|---|---|---|
| **BRT** | Screen brightness | ShipCore (WMI) |
| **VOL** | System volume | Windows audio |
| **MIC** | Microphone level (shows MUTED) | ShipCore (Core Audio) |
| **PWR** | Power mode: Quiet / Balanced / Performance | Legion Toolkit |
| **HZ** | Refresh rate 60 / 165 | Legion Toolkit |
| **GLW** | HUD glow strength | Settings.inc |

- **Click a label** to select it; the glass wedge swings to it.
- **Scroll anywhere on the dial** to change the selected control.
- **Click a point on the ring** to jump straight to that value.
- Stepped controls (power mode, refresh rate) turn the ring into big segments.
- **Right-click:** the matching Windows settings page.

#### Audio reactor (round, bottom right)
- **Outer dashed ring:** volume. **Red ticks on top:** peak meter.
- **Thick cyan arc (lower left):** loudness.
- **Center ring:** a fine-grained 96-band waveform (bass at the bottom). It shimmers softly when silent.
- **Glowing core:** pulses with the sound. **Click it** to mute; a red X shows while muted.
- **Glass wedge (right):** previous / play-pause / next media keys.
- **Bottom readout:** volume % and the output device. **Click the device** to switch to the next output.
- **Scroll anywhere:** volume up or down. **Right-click:** sound settings.
- Slows to 2 fps when silent, and turns off completely in STEALTH.

#### Bottom strip (along the dash arc)
- **Left:** CPU temp, GPU temp, CPU load, fan RPM.
- **Right:** drive fill %, disk activity, ping, Wi-Fi signal.
- Cells turn orange or red when they cross the warning thresholds. **Click the drive cell** to open the drive; other cells open Task Manager.

#### Tilted screens (bottom corners)
- **Left, PILOT:**
  - Shows Windows user, date, time, week number, year progress, UTC offset, boot time, uptime and idle time.
  - **Click:** opens your calendar app.
- **Right, SHIP:**
  - Shows host name, Windows version, CPU, GPU, memory, display and refresh rate, and uptime.
  - **TERMINAL button:** left-click opens **Windows Terminal**, right-click opens **PowerShell**.
  - **Click elsewhere:** Windows "About" page.

### Overlays

#### App drawer (CARGO)
- **ALL INSTALLED APPS** (everything in your Start menu, A–Z), plus every category as a drop-down list.
- Click a category to open it, click an app to launch it, scroll to move.
- Closes itself after 20 seconds idle.

#### Control Center
See section 5.

---

## 5. Control Center

Open it from the right-click menu, the **CFG** button, or by clicking the power bar. It has 9 tabs.

| Tab | What's there |
|---|---|
| **MODULES** | Turn each module on/off and set click-through; ALL ON |
| **Scrolling** | Every tab scrolls with the mouse wheel; descriptions wrap instead of being cut off |
| **LAYOUT** | Pick a module and nudge it (±1 / ±10 px in X and Y); RESET MODULE; EDIT MODE; **LAYOUT GUARD → CHECK ALL** (checks every module against the struts, taskbar and each other); SCALE; AUTO-FIT to your display; RESET ALL OFFSETS |
| **THEME** | Color themes (APPLY); **WINDOW TINT**; **GLOW** strength and width; **CORES / TEXT GLOW**; **GLASS GLARE**; **SCANLINES**; **HULL** brightness (B−/B+, 0 = black, 100 = original) and opacity (O−/O+); **DARK TINTS**; **HUD OPACITY**; **COCKPIT ART** (rendered hull / your own picture / off); **WARNING COLOUR** |
| **APPS** | App catalog (RESCAN the Start menu, EDIT or RELOAD Apps.ini); choose what each slot and big panel shows (Top1, Top2, Slot1–8) with ‹ › ; how to add an app |
| **SENSORS** | HWiNFO sensor mapping: DETECT auto-maps sensors, open HWiNFO, how-to, manual ± adjustment |
| **PERF** | Current tier; mode AUTO / FULL / LITE / LOW; **MASTER SWITCH** (STEALTH); thresholds for LITE / LOW / STEALTH (GPU load %); the minimum tier on battery |
| **SYSTEM** | LOCK, SLEEP, RESTART, SHUT DOWN (restart and shut down need a second click to confirm, then run in 5 s); quick links to display, sound, Wi-Fi, Bluetooth and battery settings; **TASKBAR** (cockpit behind or above the taskbar); **HUD** refresh / open Rainmeter Manage |
| **PRESETS** | SAVE / LOAD your whole setup (theme, scale, tiers, sensors, positions, slot choices, app catalog); UNDO LAST LOAD |
| **DATA** | **GMAIL**: SET UP / CHECK / OPEN · **CALENDARS**: MANAGE / SYNC · **TO-DO NOTE**: BROWSE / OPEN / CLEAR · **RETICLE TO-DOS**: ON / OFF · **IP ADDRESSES**: SHOW / MASK · **SPEED TEST**: RUN · **HELPER**: ShipCore status |

### Setting up data links (DATA tab)

**Gmail unread count**
1. Turn on 2-Step Verification for your Google account, then create an **App Password** (Google Account → Security → App passwords).
2. DATA → GMAIL → **SET UP**, then enter your Gmail address and the app password.
3. The count appears on the envelope in the Upkeep block and refreshes every 2 minutes.

**Calendars (mission clock)**
1. In Google Calendar → Settings → your calendar → **Secret address in iCal format**, copy the link. This works for subscribed calendars too.
2. DATA → CALENDARS → **MANAGE**: paste each link, give it a label, and switch the ones you want on.
3. Calendars sync every 10 minutes. Right-click the mission clock to sync now.

**Obsidian to-dos (reticle)**
1. DATA → TO-DO NOTE → **BROWSE** and pick your to-do `.md` note.
2. RETICLE TO-DOS **ON**. With no open items, the reticle falls back to showing usage.

> Never paste your app password or calendar links into the skin files or share them. The HUD stores them encrypted for your Windows account only (section 9).

---

## 6. Startup sequence

When Rainmeter starts (at login, for example), a roughly 3-second boot sequence plays:

1. A **single thin glowing line** sweeps the screen top to bottom, and the frame fades in behind it.
2. The **panels fade in** one by one from right to left (opacity 0 → 100 %), and the two round dials **spin up** to their real values.
3. A **SYSTEM CHECK** panel lists CPU/GPU, memory, storage, network, audio and power with OK / CHECK / FAIL, then shows **ALL SYSTEMS NOMINAL** (or how many need attention) and fades out.

- It plays only when Rainmeter itself starts, not on every refresh.
- When it finishes, it **unloads itself**, so it costs nothing afterwards.
- **Replay:** right-click any panel → **Play startup sequence**.
- **Turn off:** set `BootAnim=0` in Settings.inc.
- If anything goes wrong mid-sequence, closing it always restores every panel.

---

## 6b. Clover

**What he does:**
1. You click the hologram. A chime plays and he starts listening; he stops by himself when you stop talking.
2. Speech recognition (Whisper) turns your words into text, on your PC.
3. Your local AI model (Ollama) writes the answer, using what the HUD knows:
   - time and date
   - calendar
   - unread Gmail
   - Obsidian to-dos
   - open apps
   - battery, memory and network
4. He speaks the answer sentence by sentence. He remembers the last few exchanges for 10 minutes.

**Conversation pop-up:** wide, above the hologram, with his reply appearing live as he writes it. It opens by itself when:
- your speakers are muted or at 0 % (then he answers in text instead of out loud)
- you ask "show me what you've said" / "open the transcript" ("close the log" closes it)
- something goes wrong (the reason shows as a SYSTEM line)

You can also right-click the hologram, or use Control Center → CLOVER → CONVERSATION → OPEN.

**Control Center → CLOVER tab:**

| Row | What it does |
|---|---|
| SERVICE | Status; START / STOP / LOG |
| CLOVER | On / off; start with the HUD |
| MODEL | Pick from your installed Ollama models |
| FAST MODEL | A smaller model used while the GPU is busy (LITE / LOW tier) |
| ABOUT ME | Link (BROWSE), create (NEW) or EDIT a short note about you that Clover reads with every question |
| NOTE SEARCH | SMART (ChromaDB, by meaning) or KEYWORD; REINDEX rebuilds the index |
| NOTES VAULT | The folder "search my notes" looks in (default: the to-do note's folder) |
| TO-DO NOTE | The Obsidian note whose open `- [ ]` items Clover (and the reticle) read |
| SPEECH RECOGNITION | tiny / base / small / medium; AUTO / CPU / GPU |
| VOICE | Windows built-in, Kokoro (natural) or Piper |
| KOKORO VOICE | Which Kokoro voice (British: Lewis or Emma; American: Michael or Heart) and speaking speed |
| PERSONALITY | How he words his own answers: PLAYFUL (default: funny, matches your banter, still answers real questions properly), PROPER (calm and dry) or BRIEF (one sentence). Fixed lines like "Done." never change |
| WAKE WORD | "Hey Jarvis" on/off and its threshold |
| FOLLOW-UP | ON (default): after a spoken answer he listens a few seconds more, so you can reply without "Hey Jarvis". OFF: every question needs the wake word or a click |
| LISTENING | Seconds of silence before he answers (default 3 s) |
| MODEL MEMORY | Context size: 2048 (least RAM, fastest), 4096 or 8192 tokens |
| SOUNDS | Chime on click, startup sound, TEST |
| COLOUR – STANDBY / LISTENING / SPEAKING | Theme, cyan, deep blue, ice, violet, gold, emerald, crimson, white |
| ORB | Brightness and size |
| ORB TINT | How much the state colour tints the animation (0 = original colours) |
| LAYERS | 3D shell, orbit rings, dial, voice bars on/off |
| MOTION | Animation / spin speed |
| CONVERSATION | Open the pop-up, clear the conversation, muted pop-up on/off |
| SETUP | Run the setup script, open the Jarvis folder |

**Smart note search:** with ChromaDB installed, "search my notes for…" finds passages by meaning. "What did I write about motor torque" finds your gimbal note even if it never says "torque". The index lives in `Data\notes_index` on your PC and only re-reads notes that changed (every 10 minutes, and before each search). If ChromaDB is missing or breaks, he uses the keyword search automatically.

**Wake word:** with WAKE WORD on, just say **"Hey Jarvis"** instead of clicking. It runs on your PC with openWakeWord, using about 1–3 % of one CPU core. The audio is checked in tiny pieces and never stored or sent anywhere. It pauses while Jarvis is busy and in STEALTH. If he wakes by accident, press **STRICTER**; if he misses you, press **EASIER**.

**Skills:**
- **"Search my notes for ..."** searches the notes in your vault. "Is MATLAB installed?" and "what apps are installed" check your Start menu. He says a short status line ("Searching your notes.") straight away while he looks.
- **Actions:**
  - **"Open ..."** (any installed app), **"mute"** and **"unmute"** happen straight away.
  - **Volume:** "set the volume to 30", "volume 30 percent", "turn it up", "turn it down", "louder", "quieter" (steps of 10). He says the level Windows reports back. Say the number as a figure from 0 to 100.
  - **Music and video:** "pause", "play", "resume", "pause the music", "next song", "skip", "previous track". These press the keyboard's media keys, so they work with whatever player is open. "Play" and "pause" are the same key, and he answers "Sent." because a key press cannot report whether anything was playing.
  - **"Close ..."** (an open app), **"lock my computer"**, **"go to sleep"**, **"restart the computer"** and **"shut down the computer"** need confirming. He asks, then listens for your "yes" (or "go ahead", "do it") for 15 seconds without another click. Anything else cancels.
  - Only commands count, not questions: "should I restart my computer?" just gets an answer.
- **HUD readings:** ask "what's my GPU temperature?", "how loud is it?", "how much disk space is left?" or "how hard is the CPU working?". He answers from the same sensors the HUD shows (temperatures, power, fans, CPU and GPU load, video memory, volume, brightness, free disk space). A sensor you have not mapped in `Settings.inc` is simply not known to him.
- **Timers and reminders:**
  - **Set:** "remind me to cook in 20 minutes", "remind me at 6:30 pm to call mum", "set a timer for 10 minutes", "ten minute timer for the pasta". He repeats what he set, so a mishearing is heard at once. With no time ("remind me to cook") he asks "When?" and listens.
  - **Times:** "in" takes seconds, minutes or hours, as figures or words ("twenty five minutes", "half an hour", "an hour and a half"). "At" takes a clock time in figures ("at 7", "at 6:30 pm", "at 18:30") and means the next time the clock shows it. From 5 seconds to 7 days ahead, 20 pending at most.
  - **Check and cancel:** "what reminders do I have", "list my timers", "cancel the cooking reminder", "cancel the timer", "cancel all reminders".
  - **When it is due:** a ding, then your own words back ("Time to cook."), repeated up to 10 times. Say **"stop"**, **"shush"**, **"shut up"**, "quiet", "enough", "okay" or "thanks" in the pause after the line, or click the core, and it stops.
  - **Snooze:** in the same pause say **"snooze"**, "later" or "not now" and it rings again in 1 minute. Or say how long: "snooze 5 minutes", "ten more minutes", "snooze half an hour" (1 minute to 2 hours). He answers "Snoozed for 5 minutes."
  - **Repeating:** "remind me every day at 9 am to take vitamins", "remind me every weekday at 8:30 to check mail", "remind me every Monday at 7 to put the bins out". A clock time is needed; say am or pm, or "at 9" means whichever 9 o'clock comes first. "Cancel the vitamins reminder" removes the whole series. Snoozing one delays only that day's ring. After days with the PC off it rings once as missed, then carries on. Timers do not repeat.
  - **Muted, at 0 % or in STEALTH:** no sound. The conversation pop-up opens with the line instead (unless the muted pop-up is switched off).
  - They are kept in `@Resources\Data\jarvis_reminders.txt` and survive a restart. One that came due while Clover was not running is read out as "Missed reminder from ..." when he next starts. They ring only while Clover runs: this is not a Windows alarm and will not wake a sleeping PC.
- **Things to remember:** "remember that my dentist is on Fridays" and he answers "Noted: ..." and knows it in every later answer. "What do you remember" reads the list, "forget the dentist" removes every entry with those words, "forget everything" asks first. 50 entries at most. They are kept as plain text in `@Resources\Data\jarvis_memory.txt` and go only to the local model, but he reads them out when asked: do not store passwords there.
- **Daily briefing:** "good morning" (or "good afternoon", "good evening", "brief me", "daily briefing", "what's my day look like") gets the time, your calendar, unread mail, open to-dos and pending reminders in a few sentences. Only when you ask.
- **Add a to-do:** "add buy milk to my to-do list", "put call the bank on my to-do list", "add a task: renew passport". He reads it back and asks; only a clear "yes" adds `- [ ] buy milk` at the end of your TO-DO NOTE. He never creates the note, and never ticks off or deletes a task.
- **Follow-up:** after a spoken answer the hologram goes back to listening for a few seconds, so you can reply without "Hey Jarvis". At most three in a row, not after fixed replies like "Timer set", and not while muted. Switch it off with FOLLOW-UP in the Control Center.
- **Guardrails:** nothing outside that list can ever run. Destructive or joke requests ("self-destruct", "delete system32") get an in-character reply only.

**Your notes:**
- **To-do note:** Clover reads the open `- [ ]` items of your Obsidian to-do note every time you ask something.
- **About-me note:** an optional short note about you (who you are, how you like answers, your usual week) that he reads with every question.
  - Keep it to a couple of paragraphs (under ~300 words); a longer note makes every answer slower.
  - **NEW** creates one from a template, and the template's hint lines are ignored.
  - Don't put passwords or account numbers in it.

**Privacy:** everything runs on your PC. Speech recognition, the AI model and the voice (Kokoro or Windows) are all local. The conversation is kept in `@Resources\Data\jarvis_log.txt` and the diagnostics in `jarvis.log`. Clover and the HUD talk through files, not a network port, so nothing else can trigger the microphone.

**Settings (Settings.inc):**
- **Notes:** `JarvisProfile` (about-me note), `ObsidianTodo`
- **Service and models:** `JarvisEnabled`, `JarvisAutoStart`, `JarvisModel`, `JarvisModelFast`, `JarvisKeepAlive` (minutes the model stays loaded)
- **Listening and voice:** `JarvisWhisper`, `JarvisWhisperDevice`, `JarvisSilence`, `JarvisVoice`, `JarvisKokoroVoice`, `JarvisVoiceRate`, `JarvisChime`, `JarvisMutedPopup`
- **Model memory:** `JarvisContext` (tokens; older messages are dropped to fit, never the HUD data or your note)
- **Look:** `JarvisColorIdle` / `Listen` / `Speak`, `JarvisOrbBright`, `JarvisOrbSize`, `JarvisTint`, `JarvisShell`, `JarvisOrbits`, `JarvisDial`, `JarvisBars`, `JarvisSpeed`
- **Frames:** `JarvisFrameRate`, `JarvisBlackBackground`
- **Startup sound:** `BootSound`

## 7. Performance tiers and the MASTER switch

The HUD scales its own CPU/GPU cost automatically, based on GPU load (the Controller checks every second, with hysteresis so it doesn't flicker between tiers).

| Tier | When (default) | Effect |
|---|---|---|
| **FULL** | GPU < 50 % | Everything animated, 20 fps, full glow |
| **LITE** | GPU ≥ 50 % | Animations at about 10 fps |
| **LOW** | GPU ≥ 75 % | About 7 fps, glow off, the reticle parks |
| **STEALTH** | GPU ≥ 90 % or MASTER | Globe and audio waveform hidden, everything at minimum |

- `BatteryMinTier` sets the minimum tier on battery (default LITE).
- `PerfOverride` pins a tier (-1 = automatic). You can also set this from the console or PERF tab.
- **MASTER** (top console) drops everything to STEALTH instantly, for gaming or presenting.

---

## 8. The ShipCore helper

**ShipCore** is a small background program that does what Rainmeter can't do on its own.

- **How it runs:**
  - The Controller compiles it on your PC from `Scripts\ShipCore.cs`, using the C# compiler built into Windows.
  - It starts hidden, and stops by itself when Rainmeter closes.
  - Updates that change it delete the old copy so it rebuilds automatically.
- **What it does:**

| Job | How often | Output |
|---|---|---|
| Which apps have windows / are running (RUNNING / BACKGROUND / READY) | ~1.5 s | `Data\windows.txt` |
| Live network speed on the real internet adapter | 1 s | `Data\net.txt` |
| Automatic speed test when the network is quiet | every `AutoSpeedTestHours` (6 h) | `Data\speed.txt` + Settings |
| Brightness and microphone level | 3 s | `Data\sys.txt` |
| Gmail unread (IMAP over TLS) | 2 min | `Data\mail.txt` |
| Calendar events | 10 min | `Data\calendar.txt` |
| Focus an already-open app when you click it | on click | – |
| Set brightness / mic level from the dial | on demand | – |
| Gmail / calendar setup windows, to-do note picker | on demand | – |

---

## 9. Everything the HUD has access to

A complete inventory of what the HUD reads, controls, connects to and stores.

### 9.1 Hardware and system data it reads (local only)

| Data | Source |
|---|---|
| CPU load (total and per-process), memory, process list, thread counts | Windows performance counters (UsageMonitor, Process plugins) |
| GPU load and video memory | Windows GPU performance counters |
| CPU / GPU temperature, CPU / GPU power, fan speeds, GPU clock, SSD temperature, battery charge rate, capacity and wear | **HWiNFO** values it reports to the Windows registry (HWiNFO Gadget). Only sensors you map are read |
| Battery level, AC/battery state, time remaining | Windows power API (PowerPlugin) |
| Disk free space and total (C:, D:), disk read/write rate | Windows |
| Network traffic, adapter, local IP, Wi-Fi signal quality | Windows network APIs, WiFiStatus plugin |
| Audio output level and spectrum (96 bands, RMS, peak), output devices, volume, mute | Windows audio loopback (AudioLevel, Win7AudioPlugin). It **only measures loudness / frequency**; nothing is recorded or saved. |
| Microphone level and mute | Windows Core Audio (through ShipCore). Level only. |
| Microphone audio (Clover) | Only after you click the hologram, until you stop talking; turned into text on your PC and never saved or sent anywhere |
| Screen brightness | WMI (through ShipCore) |
| Open windows and running programs (names only) | Windows window list (through ShipCore) |
| Windows user name, host name, Windows version, CPU/GPU model, display resolution and refresh, boot time, uptime, idle time | Windows system info |
| Pending Windows updates | Windows Update API (read-only search) |
| Available app upgrades | `winget upgrade` (read-only list) |
| Antivirus product and on/off state | Windows Security Center |
| WSL distros, Ollama models, Tailscale state, Docker containers | Their own command-line tools (read-only status commands) |
| GPU mode, power mode, refresh rate, battery mode | Lenovo Legion Toolkit CLI (`llt feature get …`) and Device Manager (NVIDIA GPU state) |
| Installed apps (Start menu) and their icons | Start-menu scan (first run + daily) and icon extraction |
| Your Obsidian to-do note | The single `.md` file you choose (read-only) |

### 9.2 Things it can change or run on your PC

| Action | Triggered by |
|---|---|
| Launch apps; bring open app windows to the front | Clicking slots, panels, drawer |
| Set system volume, mute, switch output device | Audio panel, systems dial |
| Media keys: previous / play-pause / next | Audio panel wedge |
| Set screen brightness and microphone level | Systems dial (ShipCore) |
| Change GPU mode, power mode, refresh rate, battery conservation | Top console, systems dial (Legion Toolkit CLI) |
| Lock, sleep, restart, shut down | Control Center → SYSTEM (restart/shut down need confirmation) |
| Open Windows Terminal, PowerShell, Task Manager, Settings pages, Windows Security, Windows Update | Various buttons |
| Open websites: Gmail, Google Calendar, Yahoo Finance S&P 500 page | Upkeep envelope, mission clock, HUD SPX readout |
| Open your to-do note in Obsidian | Clicking the reticle in to-do mode |
| Run the Ookla speed test | Network block box click, or automatically every 6 h when idle |
| Write its own settings, state and data files | Control Center, ShipCore (inside the skin folder only) |

It **does not** delete your files, install software, or change Windows settings beyond those listed.

### 9.3 Internet connections

| Destination | What for | How often |
|---|---|---|
| `api.ipify.org` | Your public (WAN) IP | every 5 min |
| `query1.finance.yahoo.com` | S&P 500 day change | every 5 min while the market is open |
| `imap.gmail.com` (TLS) | Gmail unread count, only if you set it up | every 2 min |
| Your Google Calendar secret iCal links | Upcoming events, only for calendars you switched on | every 10 min |
| Ookla Speedtest servers | Speed test | on click / every 6 h when idle |
| `127.0.0.1:11434` (Ollama, on your PC) | Clover's AI model - local only | when you talk to Jarvis |
| Hugging Face (one time, during setup) | Downloads the speech-recognition model and the optional Piper voice | setup only |
| `PingHost` (default `1.1.1.1`, Cloudflare) | Ping latency | every ~10 s |

No telemetry or usage data is sent anywhere. Each service above only receives the normal request for its own data.

### 9.4 Accounts and secrets

| Secret | Where it's stored | Protection |
|---|---|---|
| Gmail address + **app password** | `%LOCALAPPDATA%\SpaceshipHUD\` | Encrypted with Windows DPAPI, readable only by your Windows account |
| Google Calendar secret iCal links | `%LOCALAPPDATA%\SpaceshipHUD\` | Encrypted with DPAPI |

These never go into the skin folder, presets, backups or anything you'd share. An app password can only read mail through IMAP. Revoke it anytime in your Google Account. If a calendar link is ever exposed, reset it in Google Calendar and paste the new one in DATA → CALENDARS.

### 9.5 Files it writes

All inside your skin folder unless noted:

- `@Resources\Settings.inc`: your settings
- `@Resources\State.inc`: remembered selections (tabs, slots, dial selection)
- `@Resources\Offsets.inc`: module position nudges
- `@Resources\Data\`: live data files (windows, net, speed, sys, mail, calendar, Start-menu scan, icon queue, logs, Clover timers and reminders)
- `@Resources\Icons\`: extracted app icons
- `@Resources\Presets\`: saved presets
- `@Resources\Backups\`: copies made by the update installer
- `@Resources\Bin\ShipCore.exe`: the compiled helper
- `%LOCALAPPDATA%\SpaceshipHUD\`: encrypted secrets only

---

## 10. Settings reference (Settings.inc)

Most of these are adjustable in the Control Center. Edit the file directly for the rest, then **Refresh HUD**.

### Display and placement
| Key | Meaning |
|---|---|
| `Scale`, `OriginX`, `OriginY` | Size and position of the whole HUD (set by AUTO-FIT) |
| `HomeMonitor`, `HomeSize`, `AutoFit` | Which monitor the HUD lives on, and whether it auto-fits |
| `FrameBehindTaskbar` | 1 = cockpit runs behind the taskbar, 0 = stops above it |

### Look
| Key | Meaning |
|---|---|
| `ColorAccent`, `ColorDim`, `ColorText`, `ColorWarn`, `ColorAlert`, `ColorGood`, `ColorHighlight`, `ColorWhite`, `ColorPanel` | Theme colors (R,G,B) |
| `FrameBrightness` | Hull brightness 0 (black) – 100 (original). Default 25 |
| `HullAlpha` | Hull opacity 0–255 |
| `ShadeAlpha`, `HudAlpha`, `MistAlpha` | Dark tints, HUD element opacity, edge mist |
| `GlassTint`, `GlassGlare`, `ScanLines`, `ScanAlpha` | Window glass look |
| `UseShipImage`, `ShipImage`, `FrameOff` | Use your own cockpit picture / turn the cockpit off |
| `GlowAlpha`, `GlowWidth`, `CoreWhite`, `TextGlow`, `TextGlowAlpha` | Neon glow |
| `FontText`, `FontNum`, `FontTitle`, `TextScaleSmall`, `TextScaleLarge` | Fonts and text scaling |

### Behavior
| Key | Meaning |
|---|---|
| `BootAnim` | 1 = play the startup sequence when Rainmeter starts |
| `CaptionStyle` | 1 = HUD captions, 0 = Windows tooltips |
| `ReticleTodo`, `ObsidianTodo` | Reticle to-do mode, and the note path |
| `IpMask` | 1 = mask IP addresses |
| `GraphA_Source`, `GraphB_Source` | Selectable graph sources |
| `PingHost` | Host for ping (default 1.1.1.1) |
| `Drive1`, `Drive2` | Drives shown in the strip and alerts |
| `LocationEnabled`, `LocationMask` | Globe position on/off and masking |

### Performance
| Key | Meaning |
|---|---|
| `PerfOverride` | -1 auto, 0 FULL, 1 LITE, 2 LOW, 3 STEALTH |
| `TierLite`, `TierLow`, `TierStealth` | GPU-load thresholds (%) |
| `BatteryMinTier` | Minimum tier on battery |

### Warnings
| Key | Meaning |
|---|---|
| `WarnCpuTemp`, `WarnGpuTemp`, `WarnDiskPct`, `WarnBattery` | Alert thresholds |
| `ChargeLimit` | Charge limit shown on the battery bar |

### Network
| Key | Meaning |
|---|---|
| `LinkDownMbps`, `LinkUpMbps`, `LastSpeedTest` | Last speed test (written automatically) |
| `AutoSpeedTestHours` | Automatic speed test interval; 0 = off |

### Legion Toolkit
| Key | Meaning |
|---|---|
| `LltPath` | Path to `llt.exe` (auto-detected if wrong) |
| `LltHybrid*`, `LltPower*`, `LltRefresh*`, `LltBattery*` | Feature names and values for GPU mode, power modes, refresh rates, battery mode |

### Sensors
| Key | Meaning |
|---|---|
| `HW_*` | HWiNFO sensor indexes (set by SENSORS → DETECT) |

---

## 11. Customizing apps (Apps.ini)

- **Categories:** `[Category.<id>]` blocks with a name, icon and an `Apps=` list.
- **Apps:** `[App.<id>]` blocks with keys:
  - `Name`, `Short`, `Icon`, `Info`
  - `Target`: path to the exe, a Start-menu app, or a `cmd:` command
  - `Proc`: the process name, like `chrome.exe`, used for RUNNING status and for focusing the open window
- **Layout:** `Top1=` / `Top2=` set the big panels' default categories; `Slot1=`…`Slot8=` set the slots (an app id or a category id).
- **Add an app:** copy an `[App.x]` block, change it, add its id to a category's `Apps=` list, then Control Center → APPS → **RESCAN** (or **RELOAD**).
- Apps that aren't installed are skipped, and the HUD rescans the Start menu automatically (at most once a minute) so newly installed programs show up.

---

## 12. Installing updates and undoing them

Each update comes as a zip (Part A, B, C…). The latest zip always contains everything before it.

1. Extract the zip. Don't run anything from inside the zip.
2. In the extracted folder, right-click empty space → **Open in Terminal**, then run:
   ```
   powershell -ExecutionPolicy Bypass -File .\Apply-SpaceshipUpdate.ps1
   ```
   The installer:
   - finds every copy of your skin
   - backs up each file it replaces to `@Resources\Backups\<update>-<date>`
   - adds new settings without touching your existing values
   - refreshes Rainmeter
3. **Undo:** run the same command with `-Restore` on the end.

If you get "File not found" popups after updating, exit Rainmeter from the tray and start it again.

---

## 13. Troubleshooting

| Problem | Fix |
|---|---|
| Panels show "File not found" after an update | Exit Rainmeter (tray icon → Exit) and reopen it |
| Temperatures / power / fans show `--` | Run HWiNFO; in Sensor settings → **HWiNFO Gadget**, tick *Enable reporting to Gadget* and *Report value in Gadget* for the sensors; then Control Center → SENSORS → **DETECT** |
| Console GPU / power / refresh controls do nothing | Install Lenovo Legion Toolkit; check `LltPath` |
| Speed test says "not installed" | `winget install Ookla.Speedtest.CLI` |
| Gmail count missing | DATA → GMAIL → CHECK; recreate the app password if it was revoked |
| Mission clock empty | DATA → CALENDARS → MANAGE: make sure at least one calendar is switched on, then SYNC |
| Reticle shows usage instead of to-dos | Note path set? RETICLE TO-DOS ON? Open items formatted as `- [ ]`? |
| App status always READY / no focusing | ShipCore isn't running: DATA → HELPER, or Refresh HUD |
| Live MBPS reads 0.0 | Normal when idle: it's current usage. Start a download to check |
| HUD too heavy while gaming | **MASTER** on the console, or lower the tier thresholds in PERF |
| Something looks broken after changes | Control Center → PRESETS → UNDO LAST LOAD, or run the installer with `-Restore` |
| Text shows garbled symbols | Update to the latest part. Scripts now avoid characters Rainmeter can't display |

---

## 14. File map

```
Spaceship\
├─ Frame\                 cockpit hull, glass, accent lines (click-through)
├─ Controller\            invisible brain: tiers, app scan, helper, boot trigger
├─ Top\                   Power, Alert, Console, Battery, GraphCPU/A/B/RAM
├─ Left\                  Category, Location (mission clock), Slot1-4, Upkeep
├─ Right\                 Category, SysInfo (network), Slot5-8, Dev
├─ Center\                Target (reticle), HUD (ladders), Sphere (Clover core)
├─ Bottom\                Storage (systems dial), Audio (reactor), Strip, Panels
├─ Overlay\               Control (Control Center), Drawer (CARGO), Boot (startup), Jarvis (conversation)
└─ @Resources\
   ├─ Settings.inc        your settings
   ├─ Apps.ini            app catalog, categories, slot choices
   ├─ State.inc / Offsets.inc
   ├─ Scripts\            Lua logic, PowerShell helpers, ShipCore.cs
   ├─ Jarvis\             jarvis.py (the voice service), Setup-Jarvis.ps1, voices\
   ├─ Sounds\             startup.wav (and optional chime.wav)
   ├─ Data\               live data files written by ShipCore and scripts
   ├─ Icons\ Images\ Fonts\
   ├─ Presets\ Backups\
   └─ Bin\ShipCore.exe    compiled helper
```
