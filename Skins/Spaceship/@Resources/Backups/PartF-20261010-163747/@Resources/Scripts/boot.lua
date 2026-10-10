-- Startup sequence (Overlay\Boot). Started by the Controller when Rainmeter starts (BootAnim=1), or from the
-- right-click menu (Play startup sequence). About 3 seconds, then the skin unloads itself, so it costs nothing
-- the rest of the time.
--   1. a thin scanner line sweeps the screen top to bottom (~0.45 s) while the frame fades in behind it
--   2. the panels fade in (opacity 0 -> 100 %) one after another from right to left; the two bottom dials spin up
--   3. a system check lists CPU / GPU / memory / storage / network / audio / power, then the verdict
-- Every panel is hidden with !SetTransparencyGroup at the start and always restored at the end (and by the
-- skin's OnCloseAction), so the HUD can't get stuck invisible.
local RES
local f = 0                  -- frame counter (Update=16 ms, ~60 fps)
local order = {}             -- panel configs, right to left
local SCAN0, SCANN = 2, 28   -- scan starts at frame SCAN0 and takes SCANN frames
local P0, PSTEP, PFADE = 22, 0.7, 12   -- panels start at frame P0, one every PSTEP frames, each fades in over PFADE
local SPIN = { ['Spaceship\\Bottom\\Storage'] = true, ['Spaceship\\Bottom\\Audio'] = true }
local C0, VERDICT, FADE, DONE  -- frames: check starts, verdict, fade-out, unload
local rows, warns = nil, 0
local finished = false

local function bang(...) SKIN:Bang(...) end
local function color(name, a)
  local c = SKIN:GetVariable(name, '255,255,255')
  c = string.match(c, '^%s*(%d+%s*,%s*%d+%s*,%s*%d+)') or c
  return a and (c .. ',' .. a) or c
end

local function buildOrder()
  local ok, z = pcall(dofile, RES .. 'Data\\zones.lua')
  if not ok or type(z) ~= 'table' then return end
  for _, m in ipairs(z.modules or {}) do
    local sx, n = 0, 0
    for _, zone in ipairs(m.zones or {}) do
      for _, p in ipairs(zone) do sx = sx + p[1]; n = n + 1 end
    end
    if n > 0 then order[#order + 1] = { cfg = m.config, x = sx / n } end
  end
  table.sort(order, function(a, b) return a.x > b.x end)
end

function Initialize()
  RES = SKIN:GetVariable('@')
  buildOrder()
  bang('!SetTransparencyGroup', '0', 'Spaceship')
  local last = P0 + math.floor((#order - 1) * PSTEP) + PFADE
  C0 = last + 4
  VERDICT = C0 + 4 + 6 * 5 + 4
  FADE = VERDICT + 60
  DONE = FADE + 14
end

local function num(m) local x = SKIN:GetMeasure(m); return x and x:GetValue() or 0 end
local function rel(m) local x = SKIN:GetMeasure(m); return x and x:GetRelativeValue() or 0 end
local function str(m) local x = SKIN:GetMeasure(m); return x and x:GetStringValue() or '' end

-- the readings, taken once when the check starts: { label, value, ok(0) / warn(1) / alert(2) }
local function readings()
  local r = {}
  local cpu = num('mCPU')
  r[#r + 1] = { 'CPU', string.format('%d%%', cpu), cpu >= 90 and 1 or 0 }
  local gpu = num('mGPU')
  r[#r + 1] = { 'GPU', string.format('%d%%', gpu), gpu >= 90 and 1 or 0 }
  local ram = rel('mRAM') * 100
  r[#r + 1] = { 'MEMORY', string.format('%d%%', ram), ram >= 90 and 1 or 0 }
  local used = (1 - rel('mDisk')) * 100
  local drive = string.sub(SKIN:GetVariable('Drive1', 'C:'), 1, 2)
  local warnDisk = tonumber(SKIN:GetVariable('WarnDiskPct', '90')) or 90
  r[#r + 1] = { 'STORAGE', string.format('%s %d%%', drive, used), used >= warnDisk and 1 or 0 }
  local ip = str('mIP')
  local online = ip ~= '' and ip ~= '0.0.0.0' and not string.find(ip, '^127%.')
  r[#r + 1] = { 'NETWORK', online and 'ONLINE' or 'NO LINK', online and 0 or 2 }
  local dev = string.upper(string.gsub(str('mAudio'), '%s*%b()', ''))
  if string.len(dev) > 12 then dev = string.sub(dev, 1, 12) end
  r[#r + 1] = { 'AUDIO', dev ~= '' and dev or 'NO DEVICE', dev ~= '' and 0 or 1 }
  local ac, bat = num('mAC') > 0, num('mBat')
  r[#r + 1] = { 'POWER', string.format('%s %d%%', ac and 'AC' or 'BAT', bat), (not ac and bat < 20) and 1 or 0 }
  -- six rows on screen: GPU folds into the CPU row when both are fine
  if r[1][3] == 0 and r[2][3] == 0 then r[1] = { 'CPU / GPU', r[1][2] .. ' / ' .. r[2][2], 0 } end
  table.remove(r, 2)
  return r
end

local function finish()
  if finished then return end
  finished = true
  bang('!SetTransparencyGroup', '255', 'Spaceship')
  bang('!DisableMeasureGroup', 'Check')
  bang('!DeactivateConfig')
end

function Update()
  f = f + 1
  if finished then return 0 end
  -- 1. scanner: top to bottom in SCANN frames (slight ease), with a spark racing along it and live readouts
  if f <= SCAN0 + SCANN + 1 then
    local t = math.max(0, math.min(1, (f - SCAN0) / SCANN))
    local y = (t < 0.5 and 2 * t * t or 1 - (-2 * t + 2) ^ 2 / 2) * 0.35 * 1640 + t * 0.65 * 1640 - 20
    local done = f > SCAN0 + SCANN
    bang('!SetOption', 'Scanner', 'Y', string.format('%.1f', y - 40))
    bang('!SetOption', 'Flare', 'X', string.format('%.0f', (t * 2.6 % 1) * 2560 - 45))
    bang('!SetOption', 'Flare', 'Y', string.format('%.1f', y - 3.5))
    bang('!SetOption', 'ScanL', 'Y', string.format('%.1f', y - 12))
    bang('!SetOption', 'ScanL', 'Text', string.format('SCAN  %04d / 1600', math.max(0, math.min(1600, y))))
    bang('!SetOption', 'ScanR', 'Y', string.format('%.1f', y - 12))
    bang('!SetOption', 'ScanR', 'Text', string.format('HULL %3d%%   SYS INIT', math.floor(t * 100)))
    for _, m in ipairs({ 'Scanner', 'Flare', 'ScanL', 'ScanR' }) do
      if done then bang('!HideMeter', m) end
      bang('!UpdateMeter', m)
    end
    bang('!Redraw')
  end
  -- frame fades in behind the line
  if f >= SCAN0 + 2 and f <= SCAN0 + SCANN + 2 then
    bang('!SetTransparency', tostring(math.floor(255 * (f - SCAN0 - 2) / SCANN)), 'Spaceship\\Frame')
  end
  -- 2. panels fade in (opacity 0 -> 100 %), right to left
  for i, o in ipairs(order) do
    local d = f - (P0 + math.floor((i - 1) * PSTEP))
    if d >= 1 and d <= PFADE then bang('!SetTransparency', tostring(math.floor(255 * d / PFADE)), o.cfg) end
    if d == 1 and SPIN[o.cfg] then bang('!CommandMeasure', 'mScript', 'Spin()', o.cfg) end
  end
  -- 3. system check
  if f == C0 then
    rows = readings()
    bang('!ShowMeter', 'CheckBg'); bang('!ShowMeter', 'Title')
    bang('!Redraw')
  end
  if rows and f > C0 and f < VERDICT then
    local i = math.floor((f - C0 - 4) / 5) + 1
    if (f - C0 - 4) % 5 == 0 and rows[i] then
      local r = rows[i]
      local col = r[3] == 2 and color('ColorAlert') or r[3] == 1 and color('ColorWarn') or color('ColorGood')
      if r[3] > 0 then warns = warns + 1 end
      bang('!SetOption', 'L' .. i, 'Text', r[1])
      bang('!SetOption', 'V' .. i, 'Text', r[2])
      bang('!SetOption', 'V' .. i, 'FontColor', color('ColorWhite'))
      bang('!SetOption', 'S' .. i, 'Text', r[3] == 0 and 'OK' or (r[3] == 2 and 'FAIL' or 'CHECK'))
      bang('!SetOption', 'S' .. i, 'FontColor', col)
      for _, m in ipairs({ 'L', 'V', 'S' }) do bang('!ShowMeter', m .. i); bang('!UpdateMeter', m .. i) end
      bang('!Redraw')
    end
  end
  if f == VERDICT then
    bang('!SetOption', 'Verdict', 'Text', warns == 0 and 'ALL SYSTEMS NOMINAL' or string.format('%d SYSTEM%s NEED ATTENTION', warns, warns > 1 and 'S' or ''))
    bang('!SetOption', 'Verdict', 'FontColor', warns == 0 and color('ColorGood') or color('ColorWarn'))
    bang('!ShowMeter', 'Verdict'); bang('!UpdateMeter', 'Verdict'); bang('!Redraw')
  end
  -- fade the readout away, make sure everything is fully on, unload
  if f >= FADE and f < DONE then
    bang('!SetTransparency', tostring(math.floor(255 * (DONE - f) / 14)))
  end
  if f >= DONE then finish() end
  return f
end
