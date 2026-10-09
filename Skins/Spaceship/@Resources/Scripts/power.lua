-- Top-left "H ---- C" bar (reference 335-432 x 24-44): power draw.
local H

function Initialize()
  H = dofile(SKIN:GetVariable('@') .. 'Scripts\\lib.lua')
  H.init()
end

function Update()
  H.refreshTier()
  local z = H.zones[1]
  local c = H.canvas(1)
  local cpu, gpu = H.hw('mHwCpuPower'), H.hw('mHwGpuPower')
  local rate = H.hw('mHwChargeRate')
  local watts
  if cpu or gpu then watts = (cpu or 0) + (gpu or 0) elseif rate and rate < 0 then watts = -rate end
  local v = watts and H.clamp(watts / 160, 0, 1) or 0
  local y = z.h * 0.5
  local x0, x1 = 22, z.w - 26
  -- letter, thin rail, hot segment, end tick, letter (reference: H ==== ' C)
  H.text(1, 1, 0, y, 'P', { size = 8.5, weight = 700, align = 'LeftCenter', color = H.C.white })
  c:line(x0, y, x1, y, H.C.white, 1.3, 210)
  if v > 0 then c:line(x0, y, x0 + (x1 - x0) * v, y, H.C.hi, 2.6) end
  c:line(x0 + (x1 - x0) * v, y - 6, x0 + (x1 - x0) * v, y + 2, H.C.white, 1.3)
  H.text(1, 2, z.w, y, watts and string.format('%.0fW', watts) or 'W', { size = 8.5, weight = 700, align = 'RightCenter', color = H.C.white })
  H.hit(1, 1, 0, 0, z.w, z.h, watts and string.format('Power draw %.0f W  (CPU %s, GPU %s)', watts, cpu and string.format('%.0f', cpu) or '--', gpu and string.format('%.0f', gpu) or '--')
    or 'Power draw needs HWiNFO: Control Center > SENSORS > DETECT')
  c:flush()
  return watts or 0
end

function OnClick(z, k) SKIN:Bang('!ActivateConfig', 'Spaceship\\Overlay\\Control', 'Control.ini') end
function OnRightClick(z, k) end
function OnScroll(z, k, d) end
function OnHover(z, k, on) end
