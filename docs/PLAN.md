# Spaceship HUD: Master Plan

A Rainmeter desktop for **Black-clover** (Lenovo Legion, Ryzen AI 9 465 + Radeon 880M, RTX 5070 Laptop 12 GB, 32 GB RAM, 954 GB SSD, one monitor). It is modelled closely on the cockpit reference image. Your animated space wallpaper (Lively) stays behind everything; the cockpit and all HUD widgets sit on top of it.

> **Status: built (v1.0.0).** All 32 modules, the frame art, the Control Center and the installer are in the repo. See the [README](../README.md) for install steps. This document is the design record.
> Rev 3 (build) changes:
> - Screen confirmed at 2560x1600.
> - Slots 1-8 can each be an app or a category; defaults are Chrome and File Explorer as single apps, the rest as categories.
> - Window tint now follows the theme colour.
> - Widgets stay above the taskbar band while the hull runs to the screen bottom.
> - Added: rocket-launch countdown, ISS on the sphere, and the MASTER kill switch.
>
> Rev 2 changes:
> - Target lock moved onto the reference ring.
> - Side rings removed; their info moved into the settings strip and sysinfo bar.
> - Network and mission tilted screens removed as widgets; they're now decorative frame pieces.
> - Added the bottom blocks of both side columns (`L_upkeep`, `R_dev`).
> - Bars, dividers, rails and glyphs are now part of the frame art, with cut-outs for the widgets.
> - The whole HUD is curved.
> - Aurum-style Control Center added (§5).
> The layout lives in [`layout/layout.json`](../layout/layout.json).
> `python tools/check_layout.py --preview docs/layout-preview.png` checks it for overlaps and draws [`layout-preview.png`](layout-preview.png).

---

## 1. Assumptions to confirm

| # | Assumption | Why it matters |
|---|---|---|
| A1 | Screen is **2560×1600** (16:10), at 100% or 150% scaling | The whole layout is drawn on a 2560×1600 base. `#Scale#` resizes it, but a different aspect ratio (16:9) needs the side columns nudged. Check *Settings → System → Display*. |
| A2 | Machine is a **Lenovo Legion** with **Legion Toolkit (LLT)** installed | GPU mode switching goes through LLT's hybrid-mode feature. |
| A3 | Default 8 pinned apps (left: SolidWorks, MATLAB, OpenRocket, RASAero II; right: Chrome, VS Code, Terminal, Obsidian) | You can change them in `Apps.inc`. |
| A4 | Default top-panel categories: left **Aircraft Design**, right **CFD & Analysis** | The page dots switch either panel to any other category. |

---

## 2. Screen map (what goes where)

Reference element → your widget. All coordinates are in [`layout.json`](../layout/layout.json).

The check runs on the *curved* shapes and passes with **0 problems**:
- 30 zones and 12 decor pieces
- 12 px minimum gap between zones
- struts treated as no-go areas
- decor never cuts into a widget

### Top console
| Zone | Reference element | Shows |
|---|---|---|
| `T_power` (top-left bar) | "H ─── C" bar | **Power draw** in W (CPU + GPU package, plus battery charge or discharge rate), with a colour-shifting fill |
| `T_settings` (top centre) | COMBAT / STARMAP / MINING / GROUND / OFF tabs, plus the RADR/IFCS and MISL/HEAT rows | **Row 1, GPU mode:** `ECO` (iGPU only) · `HYBRID` (both) · `AUTO` (iGPU on battery) · `dGPU` (MUX, needs a reboot) · `OFF` (hide HUD). **Row 2:** power mode (Quiet/Balanced/Perf) · refresh rate (60/165 Hz) · 80% charge limit · perf tier (shows the live tier; click to override) · dGPU state light (asleep/awake) · `CARGO` (all-apps drawer) · `⚙` (Control Center) |
| `T_battery` (top-right bar) | "PWR ───" bar | **Battery %**, plus **time to 80%** while charging or **time to empty** on battery |
| `T_alert` | ⚠ 1 triangle | Count of active warnings (CPU/GPU hot, disk over 90%, battery low, dGPU awake while on battery) |
| `G1_cpu` | OXYGEN LEVEL | **Fixed:** CPU usage history graph |
| `G2_select` | INTERNAL PRESSURE | **Selectable:** GPU load · GPU temp · VRAM · CPU temp · disk I/O · network · power |
| `G3_select` | HULL INTEGRITY | **Selectable:** same list as G2 |
| `G4_ram` | FUEL LEVEL | **Fixed:** RAM usage history graph |

Click a graph's title (G2 or G3) to cycle its source; right-click opens a list. The choice is saved.

### Left and right columns
| Zone | Reference element | Shows |
|---|---|---|
| `L_category` / `R_category` | OVR WEAP AVI… tabs + ship schematic / SUBSYS CARGO… + ship | **Tabs = app names** in the category. Selecting a tab swaps the big **hollow neon wireframe** to that app's graphic and shows its **LAUNCH** shortcut. |
| `L_location` | LAT / LON / VRT G-meter | **Your coordinates:** LAT, LON, and altitude or timezone, with the crosshair glyph. A mask toggle hides the digits for screenshots. |
| `R_sysinfo` | "VANDUUL SCYTHE / DREAD PIRATE ROBERTS / RN RV" | **BLACK-CLOVER** · Windows build · CPU · GPU · RAM · uptime · local IP. Device ID and Product ID are never shown. |
| `L_dots` / `R_dots` | • • • • paging dots | Switch which category that panel shows |
| `L_app1-4` / `R_app1-4` | Weapon slots 1–4 / target cards 1–4 | **The 8 most important apps:** hollow neon icon, name, a "running" pulse, and a slot number. Click launches the app. Right-click gives "Open file location" or "Run as admin". |
| `L_upkeep` (bottom of left column) | Small ship with ◇3 ⚙4 counters | **Upkeep:** pending Windows Updates, winget upgrades available, and Defender status. Click opens Windows Update. |
| `R_dev` (bottom of right column) | Small ship with "4" | **Dev status:** running Docker containers, WSL distros, and Ollama models loaded |

### Centre (canopy glass)
| Zone | Reference element | Shows |
|---|---|---|
| `C_target` | Orange lock ring "2 / 567m" | **Target lock:** the top process by CPU. Shows name, CPU %, and RAM in MB ("567m"). Click to cycle targets #1–5; right-click opens Task Manager. There is no kill button, on purpose. |
| `C_hud` | Speed ladders 350–370, centre pipper, "M/S THR 50" | Centre pipper + **clock/date**. Left tape: **CPU clock** (scrolling). Right tape: **GPU clock**. Readout: **fan speed**. |
| `C_sphere` | Holographic radar globe | Rotating **3D wireframe sphere**. Blips are the top 8 processes (distance from centre = CPU %, height = RAM). The locked target is orange. The equator ring pulses with network traffic. |

### Dashboard
| Zone | Reference element | Shows |
|---|---|---|
| `B_storage` (bottom-left screen) | "ENG / ATMOS / DMG" screen | **Storage:** C: 361/954 GB as a segmented ring, read/write bars, SSD temp and health, and any extra or USB drives. Click opens WinDirStat. |
| `B_audio` (bottom-right screen) | "TARGET SAR" waveform screen | **Audio:** output device (click to cycle), volume arc, mic-mute state, now playing (Spotify) with ⏮ ⏯ ⏭, and a live waveform |
| `B_strip` (bottom edge) | Icon row "1500 · 7 · 0% · 443 … 20 · 20" | **General info**, drawn along the dash arc: CPU °C · GPU °C · fan RPM ×2 · net ↑/↓ · ping · process count · battery wear · uptime |

### Transient overlay
- **`O_drawer` (CARGO):** drops down from the settings strip over the centre glass. It lists **every category as a drop-down** (Aircraft Design, CFD & Analysis, Electronics, Dev Extras, Creative, Computer Tools, Utilities, Media & Fun). While it is open, the target and HUD fade out. It closes when you launch something or after 10 s.
- **`O_control` (Control Center):** see §5.

These two overlays are the only elements that may cover others, and only while they are open.

---

## 3. The cockpit frame ("the rocket") and its cut-outs

The frame is the bottom layer. It's a single click-through skin (`Frame`) that shows the ship around all the widgets:

- **Curved canopy bezel:** heavy rounded corners (radius about 150 px on the base canvas). The top corners curve inward, as in the reference, so the glass looks curved.
- **Top header console:** the dark angular band that the top bars, settings strip and graphs sit on.
- **Two A-pillar struts:** run from the header down to the dashboard, with the round blue running lights from the reference.
- **Two lower console beams:** run from the side consoles to the dash, each with a blue light.
- **Dashboard:** the centre well under the sphere, the two side screens (storage and audio), the tilted corner screens, and the bottom strip.
- **Glass:** fully transparent, so the Lively space background shows through. A faint edge reflection and vignette sell the "inside a cockpit" look.
- **Baked-in detail (the `decor` list in `layout.json`):** the glowing parts of the reference that aren't live data are painted into the frame, so they cost nothing at runtime:
  - divider bars under the category panels and page dots, including the chevron on the right
  - the stepped bracket rails beside slots 1–4 (left) and the zig-zag target rails (right)
  - the bracket glyphs in the lower corners
  - the two small tilted dash screens (faint scan lines)
  - the header underglow and the strut lights
- **Cut-outs:** every widget sits in a recess cut into the frame art. Dash widgets get an 8 px inset screen bezel; glass widgets get a faint etched outline. The cut-outs are generated from `layout.json`, so the art and the layout always match.

**How it's built.** The frame is authored as layered **SVG** in `art/frame.svg` and exported to PNG at 1× and 1.5×:
- `frame_base.png`: metal, shading, bezel
- `frame_glow.png`: neon edge lines
- `frame_lights.png`: strut lights, which pulse in the FULL tier

The strut and beam shapes in the SVG come straight from the `keepouts` in `layout.json`, so the art and the overlap check can never disagree.

---

## 4. Curvature: making the whole thing look curved

Each zone is authored flat, then bent by its group's curve (`curves` in `layout.json`). Every bend is a single affine transform that maps 1:1 to Rainmeter's `TransformationMatrix` (`python tools/check_layout.py --matrices` prints them). Text stays crisp.

| Group | Curve | Effect |
|---|---|---|
| Top console | Frown arc (depth 30 px) | Outer bars and graphs sit lower and tilt down toward the edges, following the canopy |
| Left / right columns | Cylinder wrap (28 px) + 6% tilt | Panels at the top and bottom of each column lean inward, and rows dip toward the centre, like the slanted OVR/WEAP tabs in the reference |
| Dashboard | Smile arc (20 px) | The storage and audio screens rise toward the sides; the bottom strip is drawn along the same arc |
| Centre glass | Flat | The focal point stays square-on, like a real HUD |

Inside each widget, bars and graphs also use arcs (Shape `Arc`/`Curve` paths) rather than straight lines. The frame adds a curved bezel, curved glass reflections and a vignette.

---

## 5. Adjustable system (Control Center, modelled on Aurum)

This copies the ideas from your Aurum skins, not their code, and drops their heavy parts: no WebView2 and no custom DLL, just Rainmeter, Lua and PowerShell.

| Aurum idea | Spaceship version |
|---|---|
| `Settings.inc` shared by every skin | `@Resources/Settings.inc`: theme colours, glow strength, fonts, `Scale`, curve depths, perf thresholds |
| `ShowCPU=1` + `Disabled=(1-#ShowCPU#)` | `Show<Module>` flags. A hidden module's measures are **disabled**, so it costs zero CPU. |
| `Hardware.inc` from PC detection | First-run **Setup** detects resolution (sets `Scale`), the GPUs and battery, and whether HWiNFO shared memory and the LLT CLI are on. It writes `Hardware.inc` and lists anything missing. |
| `GPUHistory.inc` per-skin size + edge resize handles | `Modules/<Zone>.inc` holds each zone's offset, size and curve override. In **Edit mode**, handles appear on every zone so you can drag or resize it, with `SizeBy ±` buttons and **Reset to layout**. |
| `Interaction.inc` lock / click-through, hold Ctrl | Per-module **Lock** and **Click-through**. Glass widgets default to click-through, so the HUD never blocks the desktop; hold **Ctrl** to use one. |
| Workspace presets + undo | **Presets:** save or load snapshots of every `.inc` (theme, positions, sizes, modules, graph sources, pinned apps), 6 slots per page, plus **Undo last load**. Examples: *Default*, *Gaming (STEALTH)*, *Presentation (location masked)*. |
| Control Center window | `⚙` in the settings strip opens `O_control`. Tabs: **Modules · Layout · Theme · Apps · Performance · Presets**. Also on every skin's right-click menu. |

**Layout guard (new):** the overlap checker is ported to Lua. In Edit mode, a moved or resized zone that would overlap another, touch a strut or leave the safe area turns red and snaps back on release. A layout that breaks can't be saved.

Dash widgets can only move or resize inside their recess, because the frame art is fixed. Glass widgets can move anywhere the guard allows.

---

## 6. Visual language

| Token | Value | Use |
|---|---|---|
| `ColorPrimary` | `0,210,255` | Main neon cyan |
| `ColorDim` | `0,120,160` | Inactive tabs, grid lines |
| `ColorGlowA` | alpha 46 | Wide glow pass |
| `ColorAccent` | `255,120,40` | Target lock, selected items |
| `ColorAlert` | `255,60,60` | Warnings |
| Fonts | **Rajdhani** (labels), **Share Tech Mono** (numbers), **Orbitron** (titles) | All SIL OFL, bundled in `@Resources/Fonts` |

- **Glow technique** (same idea as your example HUD): every line is drawn twice, a wide low-alpha stroke and then a thin sharp stroke. The LOW tier drops the wide pass.
- **Hollow neon icons:** outline-only line art.
  - Brand apps (Chrome, VS Code, Discord, Spotify, Blender, KiCad…) start from Simple Icons SVGs (CC0), drawn as stroke with no fill.
  - Engineering apps get custom wireframes: an airfoil for XFOIL/XFLR5, an aircraft for OpenVSP, a rocket for OpenRocket/RASAero, a mesh for Gmsh, and so on.
  - A build script converts the SVG paths into Rainmeter `Shape` `Path` definitions. They stay true vector, scale cleanly, and recolour from `Settings.inc`.
- **Data as visuals, not numbers:** segmented bars, arcs, tapes and graphs carry the information. Numbers are small secondary labels.

---

## 7. Smart performance tiers (auto-lighten under GPU load)

An invisible **Controller** skin watches the GPU and broadcasts a tier to every skin with `!SetVariableGroup PerfTier n Spaceship` and `!UpdateGroup Spaceship`.

| Tier | When | What changes |
|---|---|---|
| **0 FULL** | GPU under 50%, on AC | Sphere at about 30 fps, strut-light pulses, both glow passes, tape scrolling animation |
| **1 LITE** | GPU over 50% for 5 s, **or on battery** | Sphere at 10 fps, no pulses |
| **2 LOW** | GPU over 75% for 5 s | Sphere frozen (drawn once), glow passes off, sensors every 2 s |
| **3 STEALTH** | GPU over 90% for 5 s, **or a fullscreen app/game in focus** | Only the frame and static labels remain; sensors every 5 s; sphere and graphs hidden |

- **Hysteresis:** the tier steps down one level only after 20 s below the threshold minus 15%, so it doesn't flicker.
- **Manual override:** Row 2 of the settings strip.
- **How:**
  - Update rates change through `UpdateDivider` on measures and meters (set with `!SetOption`).
  - Animations are `ActionTimer` loops that check `PerfTier` before each frame.
  - The sphere is its own skin, so only it runs a fast `Update`.

**Battery and dGPU hygiene** (important on a hybrid laptop):
1. In *Windows Settings → Display → Graphics*, set **Rainmeter.exe to "Power saving"**. The HUD then renders on the 880M and never wakes the RTX 5070.
2. GPU load comes from Windows' **GPU Engine performance counters** (UsageMonitor plugin), which don't wake a sleeping dGPU.
3. HWiNFO is used for temps, fans and battery. It's configured so dGPU sensors are only polled while the dGPU is already awake; otherwise the bars show "SLEEP". (Polling a sleeping NVIDIA GPU keeps it awake and drains the battery.)

---

## 8. Data sources

| Data | Source |
|---|---|
| CPU / RAM / per-process CPU / GPU engine load | Built-in measures + **UsageMonitor** plugin |
| Temps, fans, CPU/GPU power, clocks, battery charge rate, capacity, wear, SSD temp | **HWiNFO** (shared memory) + HWiNFO plugin |
| Time to 80% / to empty | Calc: `(0.80 × FullCap − Remaining) / ChargeRate` while charging, `Remaining / DischargeRate` otherwise. Smoothed over a 60 s rolling average. |
| Disk space / activity | `FreeDiskSpace` + UsageMonitor `LogicalDisk` |
| Network | `NetIn` / `NetOut`, `SysInfo` (IP), `PingPlugin`, WLAN plugin |
| Audio device / volume / mute | **Win7AudioPlugin** (bundled) |
| Waveform | **AudioLevel** plugin (bundled) |
| Now playing | Windows media-session plugin (one that reads Spotify desktop; chosen in phase 6) |
| Location | PowerShell `System.Device.Location` (Windows Location, needs location on), refreshed every 10 min. Falls back to IP geolocation (city-level) via WebParser. |
| GPU mode / power mode / refresh rate / charge limit | **Legion Toolkit CLI** (`llt.exe`, enable "CLI" in LLT settings). Exact command syntax to be confirmed on your machine with `llt.exe --help`. |
| Calendar (optional) | Google Calendar private ICS URL via WebParser |

### GPU mode mapping (your 3 modes + 1 extra)
| Button | LLT hybrid mode | What it does | Reboot |
|---|---|---|---|
| `ECO` | Hybrid-iGPU | **Integrated only**: dGPU is powered off | No* |
| `HYBRID` | Hybrid | **Both**: the dGPU wakes when an app needs it | No* |
| `AUTO` | Hybrid-Auto | Hybrid on AC, iGPU-only on battery | No* |
| `dGPU` | dGPU (MUX) | **Discrete only**: the panel is wired straight to the RTX 5070 | **Yes**, with a confirm dialog |

\*Switching away from or into dGPU mode always needs a reboot. Moving between the three hybrid variants does not, though apps using the dGPU are told to close first. If the CLI turns out not to cover a mode, the fallback is to open LLT on its GPU page. A secondary per-app option writes Windows' `UserGpuPreferences` registry key, so chosen apps always use one GPU.

---

## 9. File structure

```
Skins/Spaceship/
  @Resources/
    Settings.inc       theme, fonts, Scale, curve depths, perf thresholds, Show<Module> flags
    Hardware.inc       written by Setup (resolution, GPUs, battery, helpers found)
    Interaction.inc    per-module Lock / Click-through
    Layout.inc         GENERATED from layout/layout.json (position + TransformationMatrix per zone)
    Modules/*.inc      per-zone user offsets/sizes from Edit mode
    Presets/<name>/    snapshot copies of the .inc files
    Apps.inc           8 pinned apps + every category (name, target, icon)
    Styles.inc         shared MeterStyles (glow pass, sharp pass, labels)
    Fonts/  Icons/  Images/ (frame PNGs)
    Scripts/  sphere.lua  tabs.lua  tier.lua  tape.lua
              gpu-mode.ps1  location.ps1  apps-export.ps1
  Frame/Frame.ini          bottom layer, click-through
  Controller/Controller.ini  invisible: perf tier + alert counter
  Setup/Setup.ini            first-run detection + requirements
  Control/Control.ini        Control Center (modules, layout edit, theme, apps, presets)
  Top/      Power.ini  Battery.ini  Settings.ini  Graphs.ini  Alert.ini
  Left/     Category.ini  Location.ini  Apps.ini  Upkeep.ini
  Right/    Category.ini  SysInfo.ini  Apps.ini  Dev.ini
  Center/   Target.ini  HUD.ini  Sphere.ini
  Bottom/   Storage.ini  Audio.ini  Strip.ini
  Drawer/   Drawer.ini
art/frame.svg  art/icons/*.svg
layout/layout.json
tools/check_layout.py   tools/gen_layout_inc.py   tools/svg_to_shape.py
```

- **Why many small skins instead of one big one:** each skin has its own update rate. The sphere can run fast while everything else ticks once a second, which is the main performance win.
- **Positions:** each skin moves itself to its zone on load (`OnRefreshAction=[!Move ...]`), so nothing can drift out of place.
- **Load order:** a `.rmskin` layout loads everything in the right order: frame at the bottom, drawer on top.

---

## 10. Build phases

| Phase | Deliverable | Done when |
|---|---|---|
| **0** | Layout + overlap checker + this plan | ✅ this commit |
| **1** | Frame art with decor and cut-outs (SVG → PNG), `Settings.inc`, `Styles.inc`, generated `Layout.inc` with curve matrices, Controller skeleton | The curved frame shows over your Lively wallpaper with every zone drawn as a faint outline |
| **1b** | Setup + Control Center shell: modules on/off, lock/click-through, Edit mode with layout guard, presets + undo | You can move, resize, hide and save the outline zones |
| **2** | Top console: power bar, battery bar + time-to-80%, 4 graphs (2 selectable), alert triangle | Values match HWiNFO and Task Manager |
| **3** | Centre: HUD (tapes, pipper, clock), target lock, 3D sphere (Lua projection) | Sphere rotates smoothly at FULL and freezes at LOW |
| **4** | Settings strip: GPU modes via LLT, power mode, refresh rate, charge limit, tier override | Every button verified on your machine; dGPU switch asks for confirmation |
| **5** | Side columns: two category panels with tabs and wireframes, 8 app slots, location bar, sysinfo bar, upkeep and dev blocks, CARGO drawer | Every app launches; icons are hollow neon |
| **6** | Dashboard: storage, audio + waveform + now playing, curved bottom info strip | — |
| **7** | Performance tiers wired everywhere, plus battery/dGPU hygiene | Gaming in fullscreen drops the HUD to STEALTH; the RTX stays asleep on the desktop |
| **8** | Polish + packaging as an `.rmskin` | One-click install |

Testing: Rainmeter only runs on Windows and this repo is built in a Linux cloud environment. Each phase ends with you loading the skins and sending a screenshot, and fixes go into the next push.

---

## 11. Engineer extras (backlog, pick any)

- Git status of 2–3 main repos (branch, dirty files, ahead/behind) as a small slot
- Docker / WSL / Ollama status (running containers, models loaded)
- COM/USB device list for Arduino and Pi work (appears when a board is plugged in)
- Unit converter + quick calculator in the CARGO drawer
- Scratch notes panel that opens your Obsidian daily note
- World clocks (UTC is handy for launches and GMAT work), plus a focus/pomodoro timer in the HUD clock
- Clipboard history button (opens Ditto)
- "Mission mode" profiles: one click sets GPU mode, power mode, refresh rate and opens a group of apps (e.g. *CFD run* = dGPU + Performance + ParaView + Terminal)

---

## 12. Listing your installed apps

Run in **PowerShell**:

```powershell
# Every app in the Start menu, with the AppID Rainmeter can launch it by
Get-StartApps | Sort-Object Name | Export-Csv "$env:USERPROFILE\Desktop\apps.csv" -NoTypeInformation

# Everything winget knows about (includes versions)
winget list > "$env:USERPROFILE\Desktop\winget-apps.txt"
```

`Get-StartApps` is the useful one for the HUD. Any app in that list can be launched with
`explorer.exe shell:AppsFolder\<AppID>`, which works for Store apps too and doesn't break when an app updates its install path. Push `apps.csv` into this repo (or paste it) and `Apps.inc` will be generated from it.
