-- Top-left bar: power draw. Zone T_power (240 x 40).
local H
local hist = {}

function Initialize()
  H = dofile(SKIN:GetVariable('@') .. 'Scripts\\lib.lua')
  H.init()
end

local function draw()
  local z = H.zones[1]
  local c = H.canvas(1)
  local cpu, gpu = H.hw('mHwCpuPower'), H.hw('mHwGpuPower')
  local rate = H.hw('mHwChargeRate')
  local watts
  if cpu or gpu then
    watts = (cpu or 0) + (gpu or 0)
  elseif rate and rate < 0 then
    watts = -rate
  end
  local scale = 160
  local v = watts and H.clamp(watts / scale, 0, 1) or 0
  H.text(1, 1, 0, 0, 'PWR', { size = 10, color = H.C.accent, font = H.fontTitle, weight = 700 })
  H.text(1, 2, z.w, 0, watts and string.format('%.0f W', watts) or '-- W', { size = 11, align = 'RightTop', font = H.fontNum })
  H.text(1, 3, 44, 0, H.val('mAC', 1) > 0 and 'AC' or 'BATT', { size = 9, color = H.C.dim })
  -- reference style: thin rail with an end cap and a lit segment run
  c:line(0, 33, z.w, 33, H.C.dim, 1, 160)
  c:line(0, 28, 0, 38, H.C.accent, 1.4)
  c:line(z.w, 28, z.w, 38, H.C.accent, 1.4)
  c:segBar(4, 22, z.w - 8, 8, v, 24, nil, 2)
  if not watts then
    H.hit(1, 1, 0, 0, z.w, z.h, 'Power needs HWiNFO sensors: Control Center > SENSORS > DETECT')
  else
    H.hit(1, 1, 0, 0, z.w, z.h, string.format('CPU %s W   GPU %s W', cpu and string.format('%.0f', cpu) or '--', gpu and string.format('%.0f', gpu) or '--'))
  end
  c:flush()
end

function Update()
  H.refreshTier()
  draw()
  return 0
end

function OnClick(z, k) SKIN:Bang('!ActivateConfig', 'Spaceship\\Overlay\\Control', 'Control.ini') end
function OnRightClick(z, k) end
function OnScroll(z, k, d) end
function OnHover(z, k, on) end
