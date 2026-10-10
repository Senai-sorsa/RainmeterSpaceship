; =====================================================================================
;  SPACESHIP HUD - SETTINGS  (the Control Center writes here; safe to edit by hand too)
; =====================================================================================
[Variables]
; ---------------------------------------------------------------- fit to screen
; Designed on a 2560x1600 canvas. Control Center > LAYOUT > AUTO-FIT recomputes these.
Scale=0.6668
OriginX=0
OriginY=0
; which display the HUD lives on. The HUD is drawn for the laptop's own 2560x1600 panel: with an external
; monitor attached it stays on the laptop panel (wherever Windows places it, primary or not) and never
; spreads onto the other screen. If no display of HomeSize is connected (lid closed, external only) the
; HUD hides itself and comes back when the panel returns. HomeMonitor=auto finds it by size; a number
; (1, 2, ...) pins Rainmeter's monitor of that index instead.
HomeMonitor=auto
HomeSize=2560x1600
; AutoFit=1 rescales the HUD to the home display as Rainmeter sees it (Windows display scaling can make
; it look smaller to Rainmeter). 0 keeps Scale / OriginX / OriginY exactly as set.
AutoFit=1
; 1 = the cockpit continues behind a transparent taskbar (it can show over the taskbar if Windows reorders
; desktop windows); 0 = it stops at the top of the taskbar
FrameBehindTaskbar=1

; ---------------------------------------------------------------- theme
ColorAccent=0,210,255
ColorDim=0,110,150
ColorText=170,235,255
ColorWarn=255,130,40
ColorAlert=255,60,70
ColorGood=60,255,170
; reference pink highlight (LON value, card subtitles, warnings)
ColorHighlight=255,105,135
ColorWhite=215,240,255
ColorPanel=0,30,45,90
; transparency: hull picture opacity (255 = solid, lower lets the wallpaper through the metal) and the
; soft dark tints behind the HUD (0 = none)
HullAlpha=255
ShadeAlpha=180
; every HUD line and label (40-255)
HudAlpha=220
; neon mist off the window edges and corner cuts (0 = off, 255 = full)
MistAlpha=255
; window tint strength in the theme colour (0 = clear glass, 255 = strongest)
GlassTint=46
; faint diagonal reflections on the glass (0 = off)
GlassGlare=12
; scanlines over the windows (ScanLines 0/1, ScanAlpha = darkness 0-14)
ScanLines=1
ScanAlpha=14
; cockpit source: 0 = rendered hull (Images\hull.png, tools\ship_frame.py), 1 = your picture (tools\image_frame.py)
UseShipImage=0
; 1 = cockpit art off: no hull, corners, window tint, mist or glows - just the HUD (Control Center > THEME)
FrameOff=0
; hull metal tones baked into Images\hull.png by tools\ship_frame.py: shadow, body, lit ridge, edge highlight
HullDark=10,12,15
HullMid=20,25,30
HullLight=35,40,50
HullEdge=60,70,85
ShipImage=ship.png
; neon bloom: glow alpha (0 = off), glow width multiplier, how far line cores whiten (0-1)
GlowAlpha=60
GlowWidth=3.0
CoreWhite=0.3
; text glow: blur radius (px, 0 = off) and strength
TextGlow=4
TextGlowAlpha=150
; text size multipliers (small HUD labels / larger titles) relative to the authored sizes
TextScaleSmall=1.85
TextScaleLarge=1.45
FontText=B612 Mono
FontNum=B612 Mono
FontTitle=B612 Mono

; ---------------------------------------------------------------- performance tiers
; PerfOverride: -1 = automatic, 0 FULL, 1 LITE, 2 LOW, 3 STEALTH
PerfOverride=0
; GPU load (%) that pushes the HUD down a tier (held 5 s); steps back up 15 % lower after 20 s
TierLite=50
TierLow=75
TierStealth=90
; lowest-detail tier allowed while on battery is at least this
BatteryMinTier=1
; runtime, broadcast by the Controller - do not edit
PerfTier=0
; measures in fast-animating modules poll data every N updates
DataDivider=1
EditMode=0

; ---------------------------------------------------------------- graphs (top console)
; sources: cpu ram gpu vram cputemp gputemp power disk netdown netup battery
GraphA_Source=gpu
GraphB_Source=netdown

; ---------------------------------------------------------------- location bar
; 1 = look up approximate location from your public IP (ip-api.com) every 10 minutes
LocationEnabled=1
; 1 = mask digits (for screenshots / streaming)
LocationMask=0

; ---------------------------------------------------------------- network / storage
PingHost=1.1.1.1
Drive1=C:
Drive2=D:

; ---------------------------------------------------------------- warnings
WarnCpuTemp=92
WarnGpuTemp=85
WarnDiskPct=90
WarnBattery=20
ChargeLimit=80

; ---------------------------------------------------------------- Legion Toolkit (LLT) CLI
; Enable "CLI" in Legion Toolkit settings first. Check names with:  llt.exe feature list
LltPath=C:\Program Files\LenovoLegionToolkit\llt.exe
LltHybridFeature=hybrid-mode
LltHybridECO=on-igpu-only
LltHybridHYBRID=on
LltHybridAUTO=on-auto
LltHybridDGPU=off
LltPowerFeature=power-mode
LltPowerModes=quiet,balance,performance
LltRefreshFeature=refresh-rate
LltRefreshRates=60,165
LltBatteryFeature=battery
LltBatteryConserve=conservation
LltBatteryNormal=normal

; ---------------------------------------------------------------- HWiNFO sensor map
; Index of each sensor in HWiNFO's registry gadget (HKCU\Software\HWiNFO64\VSB), -1 = not mapped.
; Control Center > SENSORS > DETECT fills these in automatically.
HW_CpuTemp=-1
HW_GpuTemp=-1
HW_CpuPower=-1
HW_GpuPower=-1
HW_Fan1=-1
HW_Fan2=-1
HW_GpuClock=-1
HW_ChargeRate=-1
HW_RemainCap=-1
HW_FullCap=-1
HW_Wear=-1
HW_SsdTemp=-1
