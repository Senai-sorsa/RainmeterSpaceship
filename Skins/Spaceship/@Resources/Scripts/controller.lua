-- Controller (invisible): performance tiers, MASTER switch, edit mode, app scan, HWiNFO auto-map.
local H, A
local RES
local tier, upSince, downSince = 0, nil, nil
local tick = 0
H = nil

function Initialize()
  RES = SKIN:GetVariable('@')
  H = dofile(RES .. 'Scripts\\lib.lua')
  A = dofile(RES .. 'Scripts\\apps.lua')
  H.init()
  tier = H.num('PerfTier', 0)
  if H.num('EditMode', 0) == 1 then H.save('EditMode', 0) end
end

local function setTier(t)
  if t ~= tier or tick < 3 then
    tier = t
    H.save('PerfTier', t)
    H.broadcast('PerfTier', t)
    -- STEALTH: hide the animated / heavy modules entirely
    for _, cfg in ipairs({ 'Spaceship\\Center\\Sphere', 'Spaceship\\Bottom\\Audio' }) do
      SKIN:Bang(t >= 3 and '!HideFade' or '!ShowFade', cfg)
    end
  end
end

local function wanted(gpu, ac)
  local lite, low, st = H.num('TierLite', 50), H.num('TierLow', 75), H.num('TierStealth', 90)
  local function level(g, margin)
    if g >= st - margin then return 3 end
    if g >= low - margin then return 2 end
    if g >= lite - margin then return 1 end
    return 0
  end
  local up = level(gpu, 0)
  local down = level(gpu, -15)
  local minT = ac and 0 or H.num('BatteryMinTier', 1)
  return math.max(up, minT), math.max(down, minT)
end

function Update()
  tick = tick + 1
  local ov = H.num('PerfOverride', -1)
  if ov >= 0 then
    setTier(ov)
  else
    local gpu = H.clamp(H.val('mGPU', 0), 0, 100)
    local ac = H.val('mAC', 1) > 0
    local up, down = wanted(gpu, ac)
    local now = os.time()
    if up > tier then
      upSince = upSince or now
      if now - upSince >= 5 then setTier(up); upSince = nil end
    else upSince = nil end
    if down < tier then
      downSince = downSince or now
      if now - downSince >= 20 then setTier(tier - 1); downSince = nil end
    else downSince = nil end
    if tick < 3 then setTier(tier) end
  end
  -- first run / daily Start-menu scan
  if tick == 2 then
    local last = tonumber(H.str('LastAppScan', '0')) or 0
    if not A.readLines(RES .. 'Data\\StartApps.txt') or os.time() - last > 86400 then Rescan() end
  end
  if tick % 3600 == 0 then Rescan() end
  return tier
end

function SetOverride(n)
  n = tonumber(n) or -1
  H.save('PerfOverride', n)
  if n >= 0 then setTier(n) end
end

function Master()
  local ov = H.num('PerfOverride', -1)
  if ov == 3 then
    SetOverride(tonumber(H.str('MasterPrev', '-1')) or -1)
  else
    H.save('MasterPrev', ov)
    SetOverride(3)
  end
  SKIN:Bang('!UpdateGroup', 'Spaceship')
end

function ToggleEdit()
  local e = 1 - H.num('EditMode', 0)
  H.save('EditMode', e)
  H.broadcast('EditMode', e)
  SKIN:Bang('!UpdateGroup', 'Spaceship')
end

function Rescan()
  SKIN:Bang('!CommandMeasure', 'mScan', 'Run')
end

function OnScan()
  H.save('LastAppScan', os.time(), RES .. 'State.inc')
  SKIN:Bang('!RefreshGroup', 'Spaceship')
end

function DetectSensors()
  SKIN:Bang('!CommandMeasure', 'mHwScan', 'Run')
end

-- label patterns (lower case, plain find) per HW_ variable; first match wins
local MAP = {
  { 'HW_CpuTemp', { 'tctl', 'cpu package temp', 'cpu temperature', 'cpu (tdie)' } },
  { 'HW_GpuTemp', { 'gpu temperature', 'gpu core temp' } },
  { 'HW_CpuPower', { 'cpu package power', 'cpu ppt', 'package power' } },
  { 'HW_GpuPower', { 'total board power', 'gpu power', 'gpu board power' } },
  { 'HW_Fan1', { 'cpu fan', 'fan1', 'fan 1' } },
  { 'HW_Fan2', { 'gpu fan', 'fan2', 'fan 2' } },
  { 'HW_GpuClock', { 'gpu clock', 'gpu core clock' } },
  { 'HW_ChargeRate', { 'charge rate' } },
  { 'HW_RemainCap', { 'remaining capacity' } },
  { 'HW_FullCap', { 'full charged capacity', 'full charge capacity' } },
  { 'HW_Wear', { 'wear level' } },
  { 'HW_SsdTemp', { 'drive temperature', 'ssd temperature' } },
}

function OnHwScan()
  local lines = A.readLines(RES .. 'Data\\HWiNFO.txt') or {}
  local found = 0
  for _, m in ipairs(MAP) do
    local idx = -1
    for _, pat in ipairs(m[2]) do
      for _, line in ipairs(lines) do
        local i, sensor, label = string.match(line, '^(%d+)|([^|]*)|([^|]*)|')
        if i and string.find(string.lower(label), pat, 1, true) then idx = tonumber(i); break end
      end
      if idx >= 0 then break end
    end
    if idx >= 0 then found = found + 1 end
    SKIN:Bang('!WriteKeyValue', 'Variables', m[1], idx, RES .. 'Settings.inc')
  end
  H.save('SensorStatus', #lines == 0 and 'NO HWINFO GADGET DATA - enable reporting in HWiNFO' or (found .. ' of ' .. #MAP .. ' sensors mapped from ' .. #lines), RES .. 'State.inc')
  SKIN:Bang('!RefreshGroup', 'Spaceship')
end
