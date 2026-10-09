; Shared system measures (CPU, RAM, GPU, disk, network, battery) used by graphs, HUD and strip.
[mCPU]
Measure=CPU
Processor=0

[mRamUsed]
Measure=PhysicalMemory

[mRamTotal]
Measure=PhysicalMemory
Total=1
UpdateDivider=-1

[mGPU]
Measure=Plugin
Plugin=UsageMonitor
Alias=GPU
Index=0

[mVRAM]
Measure=Plugin
Plugin=UsageMonitor
Alias=VRAM
Index=0

[mDiskRead]
Measure=Plugin
Plugin=UsageMonitor
Category=LogicalDisk
Counter=Disk Read Bytes/sec
Name=_Total

[mDiskWrite]
Measure=Plugin
Plugin=UsageMonitor
Category=LogicalDisk
Counter=Disk Write Bytes/sec
Name=_Total

[mNetIn]
Measure=NetIn

[mNetOut]
Measure=NetOut

[mBattPct]
Measure=Plugin
Plugin=PowerPlugin
PowerState=PERCENT

[mAC]
Measure=Plugin
Plugin=PowerPlugin
PowerState=ACLINE

[mCpuPerf]
; % of base clock -> effective clock = CpuBaseMHz * value / 100
Measure=Plugin
Plugin=UsageMonitor
Category=Processor Information
Counter=% Processor Performance
Name=_Total
