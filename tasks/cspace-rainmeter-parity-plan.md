# CSpace ⇄ Rainmeter parity plan (2026-10-26)

What Rainmeter does, segment by segment, what CSpace needs from it, and the slices that close the gaps.
Each slice ends with: build + tests, efficiency pass (noted in the commit), republish, relaunch, screenshot.

## 1. Segment comparison

| Rainmeter feature | Its purpose | CSpace needs? | CSpace today | Slice |
|---|---|---|---|---|
| Single process, many skins (configs) | one host, each skin loads/unloads alone | yes (a version) | one WebView2, `?module=` list | — (have) |
| `Rainmeter.ini` Active=0/1 per config | which skins are on | yes | `Off_*` settings, not seeded from Rainmeter.ini | R6 |
| `!ZPos -2` (on desktop) + Show Desktop handling | stay under windows, survive Win+D | yes | forces HWND_BOTTOM on every WM_WINDOWPOSCHANGING; no Win+D | R3 |
| Skins are never hidden when covered; drawing just costs less | no flicker on window changes | yes | hides the window on fullscreen bounds → flicker | R2 |
| Fullscreen detection (exclusion rules: cloaked, tool, transparent windows) | hide only for real fullscreen apps | yes | bounds test only | R2 |
| Mouse actions incl. double-click, X buttons, wheel, modifiers | full input | yes | single clicks + wheel only, no modifiers, cursor forced to arrow | R4 |
| `Update=` per skin / `UpdateDivider` | update only what changes | yes | one rAF loop every vsync | R5 |
| Measures: CPU, RAM bytes, disk, net, battery + time left, uptime, Wi-Fi | real values | yes | %, no bytes, no time left, no Wi-Fi | R6 |
| Audio plugin (device, volume, mute) | dial | yes | none | R6 |
| SysInfo measure (host, OS, CPU/GPU names, display) | right panel | yes | none | R6 |
| WebParser / RunCommand (upkeep, calendar) | external data | yes | upkeep yes; calendar.txt no | R6 |
| `!Refresh` / Refresh all | recover from bad state | yes | tray Reload resets nothing | R1 |
| Second launch focuses the running app | app behaviour | yes | exits silently | R1 |
| Log window (Rainmeter About > Log) | debug | yes (folder) | none | R1 |
| Safe start after crash loop | never brick the desktop | yes | 3 restarts then gives up silently | R1 |
| Kill chord | panic exit | yes | throws (kills own tree) | R1 |
| DPI / work-area / taskbar change refresh | layout stays right | yes | partial | R3 |
| Skin installer / .rmskin, update checks, fade-on-hover, per-pixel hit test | packaging / nicety | no | — | skip |
| Edit mode, layouts, Manage window | editing | later | — | needs user go |
| Bang commands that change the OS (power, registry) | actions | later | — | needs user go |

## 2. Slices

- **R1 lifecycle**: fix the kill chord (kill children, then self); second launch → `control.open` in the running copy; tray Reload resets failures; tray "Open log folder"; balloon when giving up.
- **R2 occlusion**: fullscreen test with Rainmeter's exclusion rules (cloaked / invisible / iconic / tool / transparent windows skipped); covered → page pauses, window never hides. Hide stays for lock screen, presentation mode, exam browser.
- **R3 z-order**: no forced HWND_BOTTOM; Win+D lifts the HUD; TaskbarCreated, resume, WM_SETTINGCHANGE, WM_DPICHANGED → rehome.
- **R4 input**: double-clicks, X buttons, horizontal wheel, MK_ modifiers, real cursors.
- **R5 efficiency**: scheduler sleeps to the next due job instead of every vsync; drop costly SVG filters/animations. Target < 10 % of one core, < 1 GB.
- **R6 data + defaults**: real app catalog (Apps.ini export + host StartApps), calendar.txt, Rainmeter Active flags as defaults (Center\Target, Center\HUD off), RAM bytes, audio, brightness, system info, battery time left, Wi-Fi, drives/thresholds from settings, `app.launch` only for catalog ids. Personal data lives in gitignored `src/generated/` only.
- **R7 UI fidelity**: CLOVER label + orb base rings, frame lamp glows, calendar clock ring, centre light bar, jet/engine wireframes; each checked against the Rainmeter screenshot.

## 3. Not doing (and why)

Installer/autostart/push/registry and power writes need the user's go. Fade-on-hover, update checks and per-pixel hit testing add cost for little value.
