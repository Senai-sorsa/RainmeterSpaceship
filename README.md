# Spaceship HUD for Rainmeter

A full-screen starship cockpit for the desktop, laid out after a Star Citizen-style canopy reference. The cockpit hull, struts and dashboard frame the screen, and **tinted windows look out onto your own animated space wallpaper** (Lively).

The ship itself is **pure Rainmeter Shape meters**, about 2,000 of them. The left side is designed and mirrored to the right. The window shapes come from the owner's line drawing (`art/window-lines-right.png`). The rest takes its look from real sci-fi cockpit renders:

- gunmetal struts with rounded shading;
- window frames with gaskets, bolts and rim light;
- lit window sills, and side walls with grab handles and blue LED banks;
- a centre console with a hologram projector well;
- corrugated floor hoses;
- recessed housings behind every instrument that sits on the hull (the two category panels hang like monitors).

If you'd rather use a picture of the ship, an **image mode** cuts the windows out of any cockpit picture (see below). Every instrument is a live widget sitting where its counterpart sits in the reference:

- system telemetry
- GPU-mode control for the Legion laptop
- app launchers that hold a single app or a whole category
- a 3D radar sphere
- and more.

![Simulated render of the full HUD](docs/preview.jpg)

*Rendered offline by `tools/rmsim.py` with mock sensor data. The background is a stand-in starfield; on your PC it is your Lively wallpaper. Animated parts:*

- *the target lock rotates, breathes and zooms in on a new target*
- *the sphere spins, with an orange sweep and drifting blips*
- *the HUD ladders scroll smoothly*
- *the category wireframes have a scan line*
- *the waveform is live*
- *the warning triangle blinks*

## Install

1. Install [Rainmeter](https://www.rainmeter.net/) 4.5 or newer.
2. Download [`release/Spaceship_HUD_1.0.0.rmskin`](release/Spaceship_HUD_1.0.0.rmskin), double-click it and press **Install**. It loads the `Spaceship` layout.
3. Follow the one-time steps in [`SETUP.txt`](Skins/Spaceship/@Resources/Docs/SETUP.txt). The same guide opens from Control Center → SENSORS → HOW TO. The steps are:
   - Set Rainmeter to "Power saving" GPU.
   - Make the taskbar transparent or auto-hide.
   - Turn on HWiNFO gadget reporting.
   - Enable the Legion Toolkit CLI.

## What's where

| Area | Shows |
|---|---|
| Top-left / top-right bars | Power draw (W) · battery %, with time to the 80% limit or time to empty |
| Top console | GPU modes **ECO / HYBRID / AUTO / dGPU / OFF**, plus power mode, refresh rate, 80% charge limit, graphics tier, dGPU light, CARGO drawer, MASTER kill switch and Control Center |
| Four top graphs | CPU (fixed) · two selectable graphs (click the title to change the source) · RAM (fixed) |
| Side columns, top | Two **category panels** (Rocketry & Aero, Engineering & Analysis): app tabs, a hollow neon wireframe and LAUNCH. Page dots switch the category. |
| Side columns, middle | Location (LAT/LON) · ship identity card (BLACK-CLOVER specs, uptime, IP) |
| Side columns, slots 1-8 | Each slot is **one app or a category** with its own tab line. Chrome and File Explorer are single apps; the other six are categories. |
| Side columns, bottom | Upkeep (Windows Update, winget, antivirus) · dev status (WSL, Ollama, Tailscale) |
| Centre | Orange target lock on the busiest process · flight HUD (clock, CPU GHz tape, GPU tape, fan/throttle readout, network variometer, **next rocket launch countdown**) · 3D radar sphere (process blips, **ISS position**, your position) |
| Dash | Storage screen · audio screen (live waveform, volume, media keys) · info strip along the dash arc |
| Overlays | **CARGO** drawer (every category as a drop-down) · **Control Center** |

![Control Center](docs/preview-control.jpg)

## Adjusting it (Aurum-style)

The Control Center (the CFG button, or right-click any module) has these tabs:

- **MODULES:** turn any module on or off, and make it click-through.
- **LAYOUT:** nudge modules. A **layout guard** blocks any move that would overlap another module, a strut or the taskbar band. Also: edit mode, scale and auto-fit.
- **THEME:** colour presets, window tint, glow strength and width, line cores, text glow, glass glare, scanlines, and the cockpit art (vector or picture). The metal tones are `HullDark` / `HullMid` / `HullLight` / `HullEdge` in `Settings.inc`.
- **APPS:** reassign the 2 panels and 8 slots, rescan the Start menu, edit the catalog.
- **SENSORS:** auto-map HWiNFO sensors.
- **PERF:** performance-tier thresholds and the MASTER switch.
- **SYSTEM:** lock, sleep, restart and shut down (with confirmation), and Settings shortcuts.
- **PRESETS:** six save slots, with **undo**.

Apps live in [`Apps.ini`](Skins/Spaceship/@Resources/Apps.ini). Targets resolve against your Start menu, so apps that aren't installed yet stay hidden until they are. **Ansys** is already listed in Engineering and appears after a RESCAN once it's installed.

## Glow and look

Every line on the HUD, and the cockpit's own HUD lines, use the same three-layer neon bloom:

1. a wide, faint halo;
2. a glow in the theme colour;
3. the line itself, with a white-hot core (`CoreWhite`).

Bright dots get a soft halo. Text carries a blurred glow in its own colour (`TextGlow`, a zero-offset `InlineSetting=Shadow`). Every strength lives in `Settings.inc` and in Control Center → THEME. The glow switches itself off on the LOW and STEALTH performance tiers.

### Using a picture of the ship

The vector hull is clean and symmetric, but a real render has more surface detail than shapes can give. If you have a picture of the cockpit (ship only, or with space in the windows), run this to scale it to 2560×1600 and cut the windows out along the reference window shapes with a soft edge:

```
python tools/image_frame.py my-cockpit.png
```

Then pick Control Center → THEME → COCKPIT ART → PICTURE (`UseShipImage=1`). A PNG with its own transparent windows keeps them. The glass tint, glare, scanlines and HUD lines stay on top, and the vector hull and its detail hide.

## Performance

The HUD lowers its own detail as GPU load rises (**FULL → LITE → LOW → STEALTH**), with hysteresis and a minimum tier on battery:

- The sphere and waveform slow down, then freeze, then hide.
- The glow passes switch off.
- Each module is its own skin with its own update rate.
- Hidden modules stop running entirely.
- Telemetry uses Windows performance counters, which don't wake the sleeping RTX 5070.

## How it's built

```
tools/ref_layout.py     every zone, window and hull outline traced from the reference image -> layout.json
layout/layout.json      generated: zones (with slant quads), windows, decor, taskbar band
tools/check_layout.py   overlap / safe-area / taskbar checks on the slanted shapes (+ preview image)
art/window-lines-right.png   the owner's window drawing (right half; mirrored for the left)
tools/ship_frame.py     the symmetric cockpit: glass, shaded hull, frames, detail, housings, lights -> Frame/Parts/*.inc + Frame.ini order
tools/image_frame.py    image mode: cuts the windows out of a cockpit picture -> @Resources/Images/ship.png
tools/build.py          writes each module's Geometry.inc / Meters.inc and the guard data
tools/rmsim.py          offline Rainmeter simulator: runs the real Lua, renders, audits alignment
tools/package.py        builds the .rmskin installer and the Rainmeter layout
Skins/Spaceship/        the skin set (Lua in @Resources/Scripts, settings in @Resources/*.inc)
```

After editing the layout, run: `python tools/ref_layout.py && python tools/build.py && python tools/ship_frame.py && python tools/rmsim.py && python tools/package.py`.
The tools need `pip install lupa pillow shapely`.

The full design rationale is in [`docs/PLAN.md`](docs/PLAN.md).

## Credits

- Fonts: Rajdhani, Share Tech Mono and Orbitron (SIL Open Font License; the licences are in `@Resources/Fonts`).
- Ideas were drawn from public Rainmeter work: an F/A-18 cockpit skin (gauges as instruments, a kill switch), Sonder (rocket launches and ISS), Cockpit 1.5 (control panel and rotating target) and Aurum (presets, locks and per-module adjustment).
- Launch data: [The Space Devs](https://thespacedevs.com/). ISS position: [Open Notify](http://open-notify.org/).
