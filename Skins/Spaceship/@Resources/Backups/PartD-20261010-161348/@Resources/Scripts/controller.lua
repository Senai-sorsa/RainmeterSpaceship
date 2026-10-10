-- Controller (invisible): performance tiers, MASTER switch, edit mode, app scan, HWiNFO auto-map, and keeping
-- the HUD on the laptop's own display when other monitors are connected.
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

-- the laptop panel on the virtual desktop: HomeMonitor=auto -> the first monitor of HomeSize, a number -> that
-- monitor. Rainmeter's #SCREENAREA...@n# variables describe each monitor; a missing monitor leaves them unresolved.
local function findHome()
  local function mon(n)
    local function v(k) return tonumber(SKIN:ReplaceVariables('#' .. k .. '@' .. n .. '#')) end
    local w, h = v('SCREENAREAWIDTH'), v('SCREENAREAHEIGHT')
    if w and h then return { x = v('SCREENAREAX') or 0, y = v('SCREENAREAY') or 0, w = w, h = h } end
  end
  local pin = tonumber(H.str('HomeMonitor', 'auto'))
  if pin then return mon(pin) end
  local hw, hh = string.match(H.str('HomeSize', '2560x1600'), '(%d+)%s*[xX]%s*(%d+)')
  hw, hh = tonumber(hw) or 2560, tonumber(hh) or 1600
  local mons = {}
  for n = 1, 16 do mons[#mons + 1] = mon(n) end
  for _, m in ipairs(mons) do
    if m.w == hw and m.h == hh then return m end
  end
  -- Windows display scaling can make Rainmeter see the panel smaller (2560x1600 at 150% -> 1707x1067):
  -- accept a monitor with the panel's shape (16:10) and fit the HUD to it
  for _, m in ipairs(mons) do
    if math.abs(m.w / m.h - hw / hh) < 0.01 then return m end
  end
  return nil
end

-- AutoFit=1: scale the 2560x1600 design to the home display as Rainmeter sees it (centred if the shape differs)
local function fitTo(m)
  if H.num('AutoFit', 1) ~= 1 then return false end
  local s = math.min(m.w / 2560, m.h / 1600)
  local sx = string.format('%.4f', s)
  local ox, oy = math.floor((m.w - 2560 * s) / 2), math.floor((m.h - 1600 * s) / 2)
  if math.abs(H.num('Scale', 1) - s) < 0.0005 and H.num('OriginX', 0) == ox and H.num('OriginY', 0) == oy then return false end
  H.save('Scale', sx); H.save('OriginX', ox); H.save('OriginY', oy)
  print(string.format('Spaceship: fitted to a %dx%d display (scale %s)', m.w, m.h, sx))
  return true
end

local homeHidden = false
local function checkMonitor()
  local m = findHome()
  if not m then
    -- the laptop panel isn't connected (lid closed / external only): hide rather than draw on the wrong screen
    if not homeHidden then
      homeHidden = true
      print('Spaceship: the ' .. H.str('HomeSize', '2560x1600') .. ' display was not found - HUD hidden until it returns')
      SKIN:Bang('!HideGroup', 'Spaceship')
    end
    return
  end
  local refit = fitTo(m)
  if refit or m.x ~= H.num('MonX', 0) or m.y ~= H.num('MonY', 0) then
    -- the panel moved on the virtual desktop (a monitor was added, removed or made primary): follow it
    H.save('MonX', m.x, RES .. 'State.inc'); H.save('MonY', m.y, RES .. 'State.inc')
    homeHidden = false
    SKIN:Bang('!ShowGroup', 'Spaceship'); SKIN:Bang('!RefreshGroup', 'Spaceship')
  elseif homeHidden then
    homeHidden = false
    SKIN:Bang('!ShowGroup', 'Spaceship'); SKIN:Bang('!RefreshGroup', 'Spaceship')
  end
end

function Update()
  tick = tick + 1
  if tick == 1 or tick % 5 == 0 then checkMonitor() end
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
    if not A.readLines(RES .. 'Data\\StartApps.txt') or os.time() - last > 86400 then Rescan()
    elseif not A.readLines(RES .. 'Icons\\_index.txt') then StartIcons() end
  end
  if tick % 3600 == 0 then Rescan() end
  -- ShipCore helper: build if needed and (re)start it on load, then check on it every 10 minutes
  if tick == 3 or tick % 600 == 0 then SKIN:Bang('!CommandMeasure', 'mCore', 'Run') end
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

-- with the Start menu known, pull every app's own icon for the neon icons (Scripts\app-icons.ps1);
-- the group refresh waits for OnIcons, so the extraction is never cut short by a refresh of this skin
function StartIcons()
  A.load()
  if A.writeIconQueue() > 0 then SKIN:Bang('!CommandMeasure', 'mIcons', 'Run'); return true end
  return false
end

function OnScan()
  H.save('LastAppScan', os.time(), RES .. 'State.inc')
  if not StartIcons() then SKIN:Bang('!RefreshGroup', 'Spaceship') end
end

function OnIcons()
  SKIN:Bang('!RefreshGroup', 'Spaceship')
end

function OnCore()
  local out = H.sval('mCore', '')
  if string.find(out, 'core=build', 1, true) or string.find(out, 'core=nocompiler', 1, true) or string.find(out, 'core=error', 1, true) then
    print('Spaceship: ShipCore helper problem (' .. (string.match(out, 'core=(%w+)') or '?') .. ') - see @Resources\\Data\\shipcore.log. App cards use the plain process check meanwhile.')
  end
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
