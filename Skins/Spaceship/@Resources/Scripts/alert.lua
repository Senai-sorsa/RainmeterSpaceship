-- Warning triangle + count (reference: pink triangle "1" at 295,62).
local H
local blink = 0

function Initialize()
  H = dofile(SKIN:GetVariable('@') .. 'Scripts\\lib.lua')
  H.init()
end

local function alerts()
  local list = {}
  local ct, gt = H.hw('mHwCpuTemp'), H.hw('mHwGpuTemp')
  if ct and ct >= H.num('WarnCpuTemp', 92) then list[#list + 1] = string.format('CPU HOT %.0f C', ct) end
  if gt and gt >= H.num('WarnGpuTemp', 85) then list[#list + 1] = string.format('GPU HOT %.0f C', gt) end
  local tot = H.val('mDiskTotal', 0)
  if tot > 0 then
    local used = (tot - H.val('mDiskFree', 0)) / tot * 100
    if used >= H.num('WarnDiskPct', 90) then list[#list + 1] = string.format('C: %.0f%% FULL', used) end
  end
  if H.val('mAC', 1) == 0 and H.val('mBattPct', 100) <= H.num('WarnBattery', 20) then list[#list + 1] = string.format('BATTERY %d%%', H.val('mBattPct', 0)) end
  if H.val('mCPU', 0) >= 95 then list[#list + 1] = 'CPU SATURATED' end
  return list
end

function Update()
  H.refreshTier()
  blink = 1 - blink
  local z = H.zones[1]
  local c = H.canvas(1)
  local list = alerts()
  local n = #list
  local a = (n > 0 and blink == 1 and H.tier < 2) and 130 or 255
  local s = z.h * 0.62
  local cx, cy = s * 0.55 + 4, z.h / 2
  c:poly({ { cx + s * 0.5, cy }, { cx - s * 0.35, cy - s * 0.5 }, { cx - s * 0.35, cy + s * 0.5 } }, H.C.hi, 2, a, true)
  H.text(1, 1, z.w, cy, tostring(n), { size = 9, weight = 700, align = 'RightCenter', color = H.C.hi, alpha = a })
  H.hit(1, 1, 0, 0, z.w, z.h, n > 0 and table.concat(list, '  |  ') or 'All systems nominal')
  c:flush()
  return n
end

function OnClick(z, k) SKIN:Bang('!ActivateConfig', 'Spaceship\\Overlay\\Control', 'Control.ini') end
function OnRightClick(z, k) end
function OnScroll(z, k, d) end
function OnHover(z, k, on) end
