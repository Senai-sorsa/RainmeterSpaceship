; HWiNFO sensor values through its registry gadget (HWiNFO > Sensor settings > HWiNFO Gadget:
; tick "Enable reporting to Gadget" and "Report value in Gadget" for each sensor).
; A measure is disabled while its index is -1, so nothing runs until a sensor is mapped.
[mHwCpuTemp]
Measure=Registry
RegHKey=HKEY_CURRENT_USER
RegKey=SOFTWARE\HWiNFO64\VSB
RegValue=ValueRaw#HW_CpuTemp#
Disabled=(#HW_CpuTemp# < 0)
UpdateDivider=#DataDivider#

[mHwGpuTemp]
Measure=Registry
RegHKey=HKEY_CURRENT_USER
RegKey=SOFTWARE\HWiNFO64\VSB
RegValue=ValueRaw#HW_GpuTemp#
Disabled=(#HW_GpuTemp# < 0)
UpdateDivider=#DataDivider#

[mHwCpuPower]
Measure=Registry
RegHKey=HKEY_CURRENT_USER
RegKey=SOFTWARE\HWiNFO64\VSB
RegValue=ValueRaw#HW_CpuPower#
Disabled=(#HW_CpuPower# < 0)
UpdateDivider=#DataDivider#

[mHwGpuPower]
Measure=Registry
RegHKey=HKEY_CURRENT_USER
RegKey=SOFTWARE\HWiNFO64\VSB
RegValue=ValueRaw#HW_GpuPower#
Disabled=(#HW_GpuPower# < 0)
UpdateDivider=#DataDivider#

[mHwFan1]
Measure=Registry
RegHKey=HKEY_CURRENT_USER
RegKey=SOFTWARE\HWiNFO64\VSB
RegValue=ValueRaw#HW_Fan1#
Disabled=(#HW_Fan1# < 0)
UpdateDivider=#DataDivider#

[mHwFan2]
Measure=Registry
RegHKey=HKEY_CURRENT_USER
RegKey=SOFTWARE\HWiNFO64\VSB
RegValue=ValueRaw#HW_Fan2#
Disabled=(#HW_Fan2# < 0)
UpdateDivider=#DataDivider#

[mHwGpuClock]
Measure=Registry
RegHKey=HKEY_CURRENT_USER
RegKey=SOFTWARE\HWiNFO64\VSB
RegValue=ValueRaw#HW_GpuClock#
Disabled=(#HW_GpuClock# < 0)
UpdateDivider=#DataDivider#

[mHwChargeRate]
Measure=Registry
RegHKey=HKEY_CURRENT_USER
RegKey=SOFTWARE\HWiNFO64\VSB
RegValue=ValueRaw#HW_ChargeRate#
Disabled=(#HW_ChargeRate# < 0)
UpdateDivider=#DataDivider#

[mHwRemainCap]
Measure=Registry
RegHKey=HKEY_CURRENT_USER
RegKey=SOFTWARE\HWiNFO64\VSB
RegValue=ValueRaw#HW_RemainCap#
Disabled=(#HW_RemainCap# < 0)
UpdateDivider=#DataDivider#

[mHwFullCap]
Measure=Registry
RegHKey=HKEY_CURRENT_USER
RegKey=SOFTWARE\HWiNFO64\VSB
RegValue=ValueRaw#HW_FullCap#
Disabled=(#HW_FullCap# < 0)
UpdateDivider=#DataDivider#

[mHwWear]
Measure=Registry
RegHKey=HKEY_CURRENT_USER
RegKey=SOFTWARE\HWiNFO64\VSB
RegValue=ValueRaw#HW_Wear#
Disabled=(#HW_Wear# < 0)
UpdateDivider=#DataDivider#

[mHwSsdTemp]
Measure=Registry
RegHKey=HKEY_CURRENT_USER
RegKey=SOFTWARE\HWiNFO64\VSB
RegValue=ValueRaw#HW_SsdTemp#
Disabled=(#HW_SsdTemp# < 0)
UpdateDivider=#DataDivider#
