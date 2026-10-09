; HWiNFO sensor values through its registry gadget (HWiNFO > Sensor settings > HWiNFO Gadget:
; tick "Enable reporting to Gadget" and "Report value in Gadget" for each sensor).
; A measure is disabled while its index is -1, so nothing runs until a sensor is mapped.
[mHwCpuTemp]
Measure=Registry
RegHKey=HKEY_CURRENT_USER
RegKey=SOFTWARE\HWiNFO64\VSB
RegValue=ValueRaw#HW_CpuTemp#
Disabled=(#HW_CpuTemp# < 0)

[mHwGpuTemp]
Measure=Registry
RegHKey=HKEY_CURRENT_USER
RegKey=SOFTWARE\HWiNFO64\VSB
RegValue=ValueRaw#HW_GpuTemp#
Disabled=(#HW_GpuTemp# < 0)

[mHwCpuPower]
Measure=Registry
RegHKey=HKEY_CURRENT_USER
RegKey=SOFTWARE\HWiNFO64\VSB
RegValue=ValueRaw#HW_CpuPower#
Disabled=(#HW_CpuPower# < 0)

[mHwGpuPower]
Measure=Registry
RegHKey=HKEY_CURRENT_USER
RegKey=SOFTWARE\HWiNFO64\VSB
RegValue=ValueRaw#HW_GpuPower#
Disabled=(#HW_GpuPower# < 0)

[mHwFan1]
Measure=Registry
RegHKey=HKEY_CURRENT_USER
RegKey=SOFTWARE\HWiNFO64\VSB
RegValue=ValueRaw#HW_Fan1#
Disabled=(#HW_Fan1# < 0)

[mHwFan2]
Measure=Registry
RegHKey=HKEY_CURRENT_USER
RegKey=SOFTWARE\HWiNFO64\VSB
RegValue=ValueRaw#HW_Fan2#
Disabled=(#HW_Fan2# < 0)

[mHwGpuClock]
Measure=Registry
RegHKey=HKEY_CURRENT_USER
RegKey=SOFTWARE\HWiNFO64\VSB
RegValue=ValueRaw#HW_GpuClock#
Disabled=(#HW_GpuClock# < 0)

[mHwChargeRate]
Measure=Registry
RegHKey=HKEY_CURRENT_USER
RegKey=SOFTWARE\HWiNFO64\VSB
RegValue=ValueRaw#HW_ChargeRate#
Disabled=(#HW_ChargeRate# < 0)

[mHwRemainCap]
Measure=Registry
RegHKey=HKEY_CURRENT_USER
RegKey=SOFTWARE\HWiNFO64\VSB
RegValue=ValueRaw#HW_RemainCap#
Disabled=(#HW_RemainCap# < 0)

[mHwFullCap]
Measure=Registry
RegHKey=HKEY_CURRENT_USER
RegKey=SOFTWARE\HWiNFO64\VSB
RegValue=ValueRaw#HW_FullCap#
Disabled=(#HW_FullCap# < 0)

[mHwWear]
Measure=Registry
RegHKey=HKEY_CURRENT_USER
RegKey=SOFTWARE\HWiNFO64\VSB
RegValue=ValueRaw#HW_Wear#
Disabled=(#HW_Wear# < 0)

[mHwSsdTemp]
Measure=Registry
RegHKey=HKEY_CURRENT_USER
RegKey=SOFTWARE\HWiNFO64\VSB
RegValue=ValueRaw#HW_SsdTemp#
Disabled=(#HW_SsdTemp# < 0)
