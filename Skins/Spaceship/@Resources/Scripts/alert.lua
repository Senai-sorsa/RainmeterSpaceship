-- Warning triangle. Zone T_alert (40 x 40).
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
  if H.val('mAC', 1) == 0 and H.val('mBattPct', 100) <= H.num('WarnBattery', 20) then
    list[#list + 1] = string.format('BATTERY %d%%', H.val('mBattPct', 0))
  end
  if H.val('mCPU', 0) >= 95 then list[#list + 1] = 'CPU SATURATED' end
  return list
end

function Update()
  H.refreshTier()
  blink = 1 - blink
  local c = H.canvas(1)
  local list = alerts()
  local n = #list
  local col = n > 0 and H.C.warn or H.C.dim
  local a = (n > 0 and blink == 1 and H.tier < 2) and 255 or 200
  c:poly({ { 20, 4 }, { 37, 34 }, { 3, 34 } }, col, 1.8, a, true)
  H.text(1, 1, 20, 23, tostring(n), { size = 10, align = 'CenterCenter', font = H.fontNum, color = col })
  H.hit(1, 1, 0, 0, 40, 40, n > 0 and table.concat(list, '  |  ') or 'All systems nominal')
  c:flush()
  return n
end

function OnClick(z, k) SKIN:Bang('!ActivateConfig', 'Spaceship\\Overlay\\Control', 'Control.ini') end
function OnRightClick(z, k) end
function OnScroll(z, k, d) end
function OnHover(z, k, on) end
