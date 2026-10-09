; =====================================================================================
;  SPACESHIP HUD - SETTINGS  (the Control Center writes here; safe to edit by hand too)
; =====================================================================================
[Variables]
; ---------------------------------------------------------------- fit to screen
; Designed on a 2560x1600 canvas. Control Center > LAYOUT > AUTO-FIT recomputes these.
Scale=1
OriginX=0
OriginY=0

; ---------------------------------------------------------------- theme
ColorAccent=0,210,255
ColorDim=0,110,150
ColorText=170,235,255
ColorWarn=255,130,40
ColorAlert=255,60,70
ColorGood=60,255,170
ColorPanel=0,30,45,90
; window tint strength in the theme colour (0 = clear glass, 255 = strongest)
GlassTint=46
; glow pass strength (0 = off) and width multiplier
GlowAlpha=46
GlowWidth=3.2
FontText=Rajdhani
FontNum=Share Tech Mono
FontTitle=Orbitron

; ---------------------------------------------------------------- performance tiers
; PerfOverride: -1 = automatic, 0 FULL, 1 LITE, 2 LOW, 3 STEALTH
PerfOverride=-1
; GPU load (%) that pushes the HUD down a tier (held 5 s); steps back up 15 % lower after 20 s
TierLite=50
TierLow=75
TierStealth=90
; lowest-detail tier allowed while on battery is at least this
BatteryMinTier=1
; runtime, broadcast by the Controller - do not edit
PerfTier=0
EditMode=0

; ---------------------------------------------------------------- graphs (top console)
; sources: cpu ram gpu vram cputemp gputemp power disk netdown netup battery
GraphA_Source=gpu
GraphB_Source=cputemp

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
