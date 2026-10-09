; Shared system measures (CPU, RAM, GPU, disk, network, battery) used by graphs, HUD and strip.
[mCPU]
Measure=CPU
Processor=0
UpdateDivider=#DataDivider#

[mRamUsed]
Measure=PhysicalMemory
UpdateDivider=#DataDivider#

[mRamTotal]
Measure=PhysicalMemory
Total=1
UpdateDivider=-1

[mGPU]
Measure=Plugin
Plugin=UsageMonitor
Alias=GPU
Index=0
UpdateDivider=#DataDivider#

[mVRAM]
Measure=Plugin
Plugin=UsageMonitor
Alias=VRAM
Index=0
UpdateDivider=#DataDivider#

[mDiskRead]
Measure=Plugin
Plugin=UsageMonitor
Category=LogicalDisk
Counter=Disk Read Bytes/sec
Name=_Total
UpdateDivider=#DataDivider#

[mDiskWrite]
Measure=Plugin
Plugin=UsageMonitor
Category=LogicalDisk
Counter=Disk Write Bytes/sec
Name=_Total
UpdateDivider=#DataDivider#

[mNetIn]
Measure=NetIn
UpdateDivider=#DataDivider#

[mNetOut]
Measure=NetOut
UpdateDivider=#DataDivider#

[mBattPct]
Measure=Plugin
Plugin=PowerPlugin
PowerState=PERCENT
UpdateDivider=#DataDivider#

[mAC]
Measure=Plugin
Plugin=PowerPlugin
PowerState=ACLINE
UpdateDivider=#DataDivider#

[mCpuPerf]
; % of base clock -> effective clock = CpuBaseMHz * value / 100
Measure=Plugin
Plugin=UsageMonitor
Category=Processor Information
Counter=% Processor Performance
Name=_Total
UpdateDivider=#DataDivider#