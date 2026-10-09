-- Control Center (O_control, 1040 x 900). Aurum-style adjustability for the whole HUD.
local H, A, Z, G
local RES
local TABS = { 'MODULES', 'LAYOUT', 'THEME', 'APPS', 'SENSORS', 'PERF', 'SYSTEM', 'PRESETS' }
local tab, page, selMod = 1, 1, 1
local msg, msgAt = 'READY', 0
local armed, armedAt = nil, 0
local actions = {}
local slotCursor = {}

-- geometry inside the zone
local TX, TY, TW, TH = 22, 78, 170, 46
local CX, CW, RY, RH, NROWS = 214, 804, 78, 46, 16
local BW, BG = 92, 8

local THEMES = {
  { 'CYAN', '0,210,255', '0,110,150', '170,235,255' },
  { 'AMBER', '255,176,40', '150,95,20', '255,225,170' },
  { 'EMERALD', '60,255,160', '20,130,80', '190,255,220' },
  { 'CRIMSON', '255,70,80', '140,30,40', '255,200,200' },
  { 'VIOLET', '180,120,255', '90,60,150', '225,205,255' },
  { 'ICE', '210,235,255', '110,130,150', '240,248,255' },
}
local SENSORS = { 'CpuTemp', 'GpuTemp', 'CpuPower', 'GpuPower', 'Fan1', 'Fan2', 'GpuClock', 'ChargeRate', 'RemainCap', 'FullCap', 'Wear', 'SsdTemp' }
local PRESET_FILES = { 'Settings.inc', 'Offsets.inc', 'State.inc', 'Apps.ini' }

function Initialize()
  RES = SKIN:GetVariable('@')
  H = dofile(RES .. 'Scripts\\lib.lua')
  A = dofile(RES .. 'Scripts\\apps.lua')
  Z = dofile(RES .. 'Data\\zones.lua')
  G = dofile(RES .. 'Scripts\\guard.lua')
  H.init()
  A.load()
end

local function say(t) msg, msgAt = t, os.time() end

local function arm(id)
  if armed == id and os.time() - armedAt < 6 then armed = nil; return true end
  armed, armedAt = id, os.time()
  say('CLICK AGAIN TO CONFIRM')
  return false
end

local function offsets()
  local o = {}
  for _, m in ipairs(Z.modules) do
    o[m.key] = { tonumber(SKIN:GetVariable(m.key .. '_DX', '0')) or 0, tonumber(SKIN:GetVariable(m.key .. '_DY', '0')) or 0 }
  end
  return o
end

local function writeVar(file, key, value)
  SKIN:Bang('!SetVariable', key, value)
  SKIN:Bang('!WriteKeyValue', 'Variables', key, value, RES .. file)
end

local function copyFile(src, dst)
  local f = io.open(src, 'rb')
  if not f then return false end
  local data = f:read('*a')
  f:close()
  local g = io.open(dst, 'wb')
  if not g then return false end
  g:write(data)
  g:close()
  return true
end

local function readFirst(path)
  local f = io.open(path, 'r')
  if not f then return nil end
  local l = f:read('*l')
  f:close()
  return l
end

-- ---------------------------------------------------------------- actions
local function nudge(dx, dy)
  local m = Z.modules[selMod]
  local o = offsets()
  local cur = o[m.key]
  o[m.key] = { cur[1] + dx, cur[2] + dy }
  local ok, why = G.check(Z, m.key, o)
  if not ok then say('BLOCKED: ' .. m.name .. ' ' .. why); return end
  writeVar('Offsets.inc', m.key .. '_DX', o[m.key][1])
  writeVar('Offsets.inc', m.key .. '_DY', o[m.key][2])
  SKIN:Bang('!Refresh', m.config)
  say(m.name .. string.format(' MOVED TO %+d, %+d', o[m.key][1], o[m.key][2]))
end

local function setModule(m, on)
  if on then SKIN:Bang('!ActivateConfig', m.config, m.file) else SKIN:Bang('!DeactivateConfig', m.config) end
  writeVar('State.inc', 'Off_' .. m.key, on and 0 or 1)
end

local function setClick(m, ct)
  SKIN:Bang('!ClickThrough', ct and '1' or '0', m.config)
  writeVar('State.inc', 'CT_' .. m.key, ct and 1 or 0)
end

local function applyTheme(t)
  writeVar('Settings.inc', 'ColorAccent', t[2])
  writeVar('Settings.inc', 'ColorDim', t[3])
  writeVar('Settings.inc', 'ColorText', t[4])
  say('THEME ' .. t[1] .. ' APPLIED')
  SKIN:Bang('!RefreshGroup', 'Spaceship')
end

local function bump(var, delta, lo, hi, file, refresh)
  local v = H.clamp((tonumber(SKIN:GetVariable(var, '0')) or 0) + delta, lo, hi)
  v = math.floor(v * 100 + 0.5) / 100
  writeVar(file or 'Settings.inc', var, v)
  say(var .. ' = ' .. v)
  if refresh then SKIN:Bang('!RefreshGroup', 'Spaceship') end
end

local function slotIds()
  local ids = {}
  for _, id in ipairs(A.catOrder) do ids[#ids + 1] = id end
  local apps = {}
  for id in pairs(A.apps) do apps[#apps + 1] = id end
  table.sort(apps)
  for _, id in ipairs(apps) do ids[#ids + 1] = id end
  return ids
end

local function cycleSlot(key, dir)
  local ids = slotIds()
  local cur = A.layout[key] or ids[1]
  local idx = 1
  for i, id in ipairs(ids) do if id == cur then idx = i end end
  local nxt = ids[(idx - 1 + dir) % #ids + 1]
  A.layout[key] = nxt
  SKIN:Bang('!WriteKeyValue', 'Layout', key, nxt, RES .. 'Apps.ini')
  local n = tonumber(string.match(key, '%d+'))
  local cfg
  if string.sub(key, 1, 3) == 'Top' then
    cfg = n == 1 and 'Spaceship\\Left\\Category' or 'Spaceship\\Right\\Category'
    writeVar('State.inc', 'TopCat' .. n, '')
  else
    cfg = n <= 4 and ('Spaceship\\Left\\Slot' .. n) or ('Spaceship\\Right\\Slot' .. n)
  end
  SKIN:Bang('!Refresh', cfg)
  say(key .. ' > ' .. string.upper(nxt))
end

local function savePreset(n)
  local dir = RES .. 'Presets\\' .. n .. '\\'
  for _, f in ipairs(PRESET_FILES) do copyFile(RES .. f, dir .. f) end
  local s = io.open(dir .. 'stamp.txt', 'w')
  if s then s:write(os.date('%Y-%m-%d %H:%M')); s:close() end
  say('PRESET ' .. n .. ' SAVED')
end

local function loadPreset(n)
  local dir = RES .. 'Presets\\' .. n .. '\\'
  if not readFirst(dir .. 'stamp.txt') then say('PRESET ' .. n .. ' IS EMPTY'); return end
  for _, f in ipairs(PRESET_FILES) do copyFile(RES .. f, RES .. 'Presets\\_undo\\' .. f) end
  local s = io.open(RES .. 'Presets\\_undo\\stamp.txt', 'w')
  if s then s:write(os.date('%Y-%m-%d %H:%M')); s:close() end
  for _, f in ipairs(PRESET_FILES) do copyFile(dir .. f, RES .. f) end
  say('PRESET ' .. n .. ' LOADED')
  SKIN:Bang('!RefreshGroup', 'Spaceship')
end

-- ---------------------------------------------------------------- tab contents
-- each row: { label, value, { {text, fn, on}, ... }, swatch }
local function rowsModules()
  local rows = {}
  local per = 13
  local pages = math.ceil(#Z.modules / per)
  if page > pages then page = 1 end
  for i = (page - 1) * per + 1, math.min(#Z.modules, page * per) do
    local m = Z.modules[i]
    local off = SKIN:GetVariable('Off_' .. m.key, '0') == '1'
    local ct = SKIN:GetVariable('CT_' .. m.key, '0') == '1'
    rows[#rows + 1] = { m.name, (off and 'OFF' or 'ON') .. (ct and '  /  CLICK-THROUGH' or ''), {
      { off and 'TURN ON' or 'TURN OFF', function() setModule(m, off) end, not off },
      { ct and 'CLICKABLE' or 'CLICK-THRU', function() setClick(m, not ct) end, ct },
      { 'ADJUST', function() selMod = i; tab = 2 end },
    } }
  end
  rows[#rows + 1] = { string.format('PAGE %d / %d', page, pages), 'Hold Ctrl and use Rainmeter Manage for anything else', {
    { '< PREV', function() page = (page - 2) % pages + 1 end },
    { 'NEXT >', function() page = page % pages + 1 end },
    { 'ALL ON', function() for _, m in ipairs(Z.modules) do setModule(m, true) end; say('ALL MODULES ON') end },
  } }
  return rows
end

local function rowsLayout()
  local m = Z.modules[selMod]
  local o = offsets()[m.key]
  local edit = H.num('EditMode', 0) == 1
  local sc = H.num('Scale', 1)
  return {
    { 'MODULE', m.name, { { '<', function() selMod = (selMod - 2) % #Z.modules + 1 end }, { '>', function() selMod = selMod % #Z.modules + 1 end } } },
    { 'OFFSET X', string.format('%+d px', o[1]), { { '-10', function() nudge(-10, 0) end }, { '-1', function() nudge(-1, 0) end }, { '+1', function() nudge(1, 0) end }, { '+10', function() nudge(10, 0) end } } },
    { 'OFFSET Y', string.format('%+d px', o[2]), { { '-10', function() nudge(0, -10) end }, { '-1', function() nudge(0, -1) end }, { '+1', function() nudge(0, 1) end }, { '+10', function() nudge(0, 10) end } } },
    { 'RESET MODULE', 'Back to the designed position', { { 'RESET', function()
      writeVar('Offsets.inc', m.key .. '_DX', 0); writeVar('Offsets.inc', m.key .. '_DY', 0); SKIN:Bang('!Refresh', m.config); say(m.name .. ' RESET') end } } },
    { 'EDIT MODE', edit and 'ON - every zone shows its outline' or 'OFF', { { edit and 'TURN OFF' or 'TURN ON', function()
      SKIN:Bang('!CommandMeasure', 'mScript', 'ToggleEdit()', 'Spaceship\\Controller') end, edit } } },
    { 'LAYOUT GUARD', 'Checks every module against the struts, taskbar and each other', { { 'CHECK ALL', function()
      local bad = G.checkAll(Z, offsets())
      say(#bad == 0 and 'LAYOUT OK - NO OVERLAPS' or ('PROBLEM: ' .. bad[1])) end } } },
    { 'SCALE', string.format('%.2f', sc), { { '-0.05', function() writeVar('Settings.inc', 'AutoFit', 0); bump('Scale', -0.05, 0.4, 3, nil, true) end }, { '+0.05', function() writeVar('Settings.inc', 'AutoFit', 0); bump('Scale', 0.05, 0.4, 3, nil, true) end },
      { 'AUTO-FIT', function()
        local w, h = tonumber(SKIN:GetVariable('SCREENAREAWIDTH')) or 2560, tonumber(SKIN:GetVariable('SCREENAREAHEIGHT')) or 1600
        local s = math.min(w / 2560, h / 1600)
        writeVar('Settings.inc', 'Scale', string.format('%.4f', s))
        writeVar('Settings.inc', 'OriginX', math.floor((w - 2560 * s) / 2))
        writeVar('Settings.inc', 'OriginY', math.floor((h - 1600 * s) / 2))
        say(string.format('FIT TO %dx%d (SCALE %.3f)', w, h, s)); SKIN:Bang('!RefreshGroup', 'Spaceship') end } } },
    { 'RESET ALL OFFSETS', 'Every module back to the designed layout', { { armed == 'resetall' and 'CONFIRM' or 'RESET ALL', function()
      if arm('resetall') then
        for _, mm in ipairs(Z.modules) do writeVar('Offsets.inc', mm.key .. '_DX', 0); writeVar('Offsets.inc', mm.key .. '_DY', 0) end
        SKIN:Bang('!RefreshGroup', 'Spaceship'); say('ALL OFFSETS RESET') end end, armed == 'resetall' } } },
  }
end

local function rowsTheme()
  local rows = {}
  local cur = H.str('ColorAccent', '')
  for _, t in ipairs(THEMES) do
    rows[#rows + 1] = { t[1], t[2], { { cur == t[2] and 'ACTIVE' or 'APPLY', function() applyTheme(t) end, cur == t[2] } }, t[2] }
  end
  rows[#rows + 1] = { 'WINDOW TINT', tostring(H.num('GlassTint', 46)) .. ' / 255', { { '-10', function() bump('GlassTint', -10, 0, 255, nil, true) end }, { '+10', function() bump('GlassTint', 10, 0, 255, nil, true) end }, { 'CLEAR', function() writeVar('Settings.inc', 'GlassTint', 0); SKIN:Bang('!RefreshGroup', 'Spaceship') end } } }
  rows[#rows + 1] = { 'GLOW', string.format('strength %d   width %.1f', H.num('GlowAlpha', 52), H.num('GlowWidth', 3)), { { '-', function() bump('GlowAlpha', -8, 0, 160, nil, true) end }, { '+', function() bump('GlowAlpha', 8, 0, 160, nil, true) end }, { 'W-', function() bump('GlowWidth', -0.4, 1, 8, nil, true) end }, { 'W+', function() bump('GlowWidth', 0.4, 1, 8, nil, true) end } } }
  rows[#rows + 1] = { 'CORES / TEXT GLOW', string.format('cores %.1f (1 = white-hot)   text glow %d px', H.num('CoreWhite', 0.3), H.num('TextGlow', 4)), { { 'C-', function() bump('CoreWhite', -0.1, 0, 1, nil, true) end }, { 'C+', function() bump('CoreWhite', 0.1, 0, 1, nil, true) end }, { 'T-', function() bump('TextGlow', -1, 0, 12, nil, true) end }, { 'T+', function() bump('TextGlow', 1, 0, 12, nil, true) end } } }
  rows[#rows + 1] = { 'GLASS GLARE', tostring(H.num('GlassGlare', 12)) .. '  smudges + reflections', { { '-4', function() bump('GlassGlare', -4, 0, 60, nil, true) end }, { '+4', function() bump('GlassGlare', 4, 0, 60, nil, true) end }, { 'OFF', function() writeVar('Settings.inc', 'GlassGlare', 0); SKIN:Bang('!RefreshGroup', 'Spaceship') end } } }
  local scan = H.num('ScanLines', 1) == 1
  rows[#rows + 1] = { 'SCANLINES', (scan and 'ON' or 'OFF') .. '  darkness ' .. tostring(H.num('ScanAlpha', 14)), { { scan and 'OFF' or 'ON', function() writeVar('Settings.inc', 'ScanLines', scan and 0 or 1); SKIN:Bang('!RefreshGroup', 'Spaceship') end }, { '-4', function() bump('ScanAlpha', -4, 0, 14, nil, true) end }, { '+4', function() bump('ScanAlpha', 4, 0, 14, nil, true) end } } }
  -- transparency: the metal, the dark tints behind the HUD, and every HUD element
  rows[#rows + 1] = { 'HULL OPACITY', tostring(H.num('HullAlpha', 255)) .. ' / 255  (lower = wallpaper shows through the metal)', { { '-25', function() bump('HullAlpha', -25, 0, 255, nil, true) end }, { '+25', function() bump('HullAlpha', 25, 0, 255, nil, true) end }, { 'SOLID', function() writeVar('Settings.inc', 'HullAlpha', 255); SKIN:Bang('!RefreshGroup', 'Spaceship') end } } }
  rows[#rows + 1] = { 'DARK TINTS', tostring(H.num('ShadeAlpha', 255)) .. ' / 255  (shading behind the HUD on the glass)', { { '-25', function() bump('ShadeAlpha', -25, 0, 255, nil, true) end }, { '+25', function() bump('ShadeAlpha', 25, 0, 255, nil, true) end }, { 'OFF', function() writeVar('Settings.inc', 'ShadeAlpha', 0); SKIN:Bang('!RefreshGroup', 'Spaceship') end } } }
  rows[#rows + 1] = { 'HUD OPACITY', tostring(H.num('HudAlpha', 255)) .. ' / 255  (every line and label)', { { '-25', function() bump('HudAlpha', -25, 40, 255, nil, true) end }, { '+25', function() bump('HudAlpha', 25, 40, 255, nil, true) end }, { 'FULL', function() writeVar('Settings.inc', 'HudAlpha', 255); SKIN:Bang('!RefreshGroup', 'Spaceship') end } } }
  local img = H.num('UseShipImage', 0) == 1
  rows[#rows + 1] = { 'COCKPIT ART', img and ('PICTURE  Images\\' .. H.str('ShipImage', 'ship.png')) or 'RENDERED  textured hull (Images\\hull.png)', { { 'RENDERED', function() writeVar('Settings.inc', 'UseShipImage', 0); SKIN:Bang('!RefreshGroup', 'Spaceship') end, not img }, { 'PICTURE', function() writeVar('Settings.inc', 'UseShipImage', 1); SKIN:Bang('!RefreshGroup', 'Spaceship') end, img } } }
  rows[#rows + 1] = { 'WARNING COLOUR', H.str('ColorWarn', ''), { { 'ORANGE', function() writeVar('Settings.inc', 'ColorWarn', '255,130,40'); SKIN:Bang('!RefreshGroup', 'Spaceship') end }, { 'YELLOW', function() writeVar('Settings.inc', 'ColorWarn', '255,220,60'); SKIN:Bang('!RefreshGroup', 'Spaceship') end } } }
  return rows
end

local function rowsApps()
  local total, missing = 0, 0
  for _, app in pairs(A.apps) do total = total + 1; if app.missing then missing = missing + 1 end end
  local rows = {
    { 'CATALOG', string.format('%d apps, %d found, %d not installed - Start menu: %d entries', total, total - missing, missing, A.startCount or 0), {
      { 'RESCAN', function() SKIN:Bang('!CommandMeasure', 'mScript', 'Rescan()', 'Spaceship\\Controller'); say('SCANNING START MENU...') end },
      { 'EDIT', function() SKIN:Bang('["notepad.exe" "' .. RES .. 'Apps.ini"]') end },
      { 'RELOAD', function() SKIN:Bang('!RefreshGroup', 'Spaceship'); say('RELOADED') end } } },
  }
  local keys = { 'Top1', 'Top2', 'Slot1', 'Slot2', 'Slot3', 'Slot4', 'Slot5', 'Slot6', 'Slot7', 'Slot8' }
  for _, k in ipairs(keys) do
    local id = A.layout[k] or ''
    local e = A.entry(id)
    local desc = e and (e.kind == 'cat' and ('CATEGORY  ' .. e.cat.name) or ('APP  ' .. e.app.name)) or 'UNASSIGNED'
    local label = k == 'Top1' and 'TOP PANEL LEFT' or (k == 'Top2' and 'TOP PANEL RIGHT' or ('SLOT ' .. string.sub(k, 5) .. (tonumber(string.sub(k, 5)) <= 4 and '  (LEFT)' or '  (RIGHT)')))
    rows[#rows + 1] = { label, desc, { { '<', function() cycleSlot(k, -1) end }, { '>', function() cycleSlot(k, 1) end } } }
  end
  rows[#rows + 1] = { 'ADD AN APP', 'Copy an [App.x] block in Apps.ini, add its id to a category Apps= list, RESCAN', {} }
  return rows
end

local function rowsSensors()
  local rows = {
    { 'HWINFO', H.str('SensorStatus', 'NOT SCANNED'), {
      { 'DETECT', function() SKIN:Bang('!CommandMeasure', 'mScript', 'DetectSensors()', 'Spaceship\\Controller'); say('READING HWINFO GADGET...') end },
      { 'HWINFO', function() if A.apps.hwinfo then A.launch(A.apps.hwinfo) end end },
      { 'HOW TO', function() SKIN:Bang('["' .. RES .. 'Docs\\SETUP.txt"]') end } } },
  }
  for _, s in ipairs(SENSORS) do
    local var = 'HW_' .. s
    local idx = H.num(var, -1)
    local v = H.hw('mHw' .. s)
    rows[#rows + 1] = { string.upper(s), idx < 0 and 'NOT MAPPED' or string.format('#%d   =   %s', idx, v and tostring(v) or '--'), {
      { '-', function() bump(var, -1, -1, 199, nil, true) end }, { '+', function() bump(var, 1, -1, 199, nil, true) end } } }
  end
  return rows
end

local function rowsPerf()
  local names = { [-1] = 'AUTO', [0] = 'FULL', [1] = 'LITE', [2] = 'LOW', [3] = 'STEALTH' }
  local ov = H.num('PerfOverride', -1)
  local function setOv(n) return function() SKIN:Bang('!CommandMeasure', 'mScript', 'SetOverride(' .. n .. ')', 'Spaceship\\Controller'); writeVar('Settings.inc', 'PerfOverride', n); say('TIER ' .. names[n]) end end
  return {
    { 'NOW', string.format('TIER %s   /   GPU %d%%', names[H.num('PerfTier', 0)] or '?', H.clamp(H.val('mGPU', 0), 0, 100)), {} },
    { 'MODE', names[ov] or 'AUTO', { { 'AUTO', setOv(-1), ov == -1 }, { 'FULL', setOv(0), ov == 0 }, { 'LITE', setOv(1), ov == 1 }, { 'LOW', setOv(2), ov == 2 } } },
    { 'MASTER SWITCH', 'STEALTH hides the sphere + waveform and drops everything to minimum', { { 'STEALTH', setOv(3), ov == 3 } } },
    { 'LITE ABOVE', H.num('TierLite', 50) .. '% GPU', { { '-5', function() bump('TierLite', -5, 10, 95) end }, { '+5', function() bump('TierLite', 5, 10, 95) end } } },
    { 'LOW ABOVE', H.num('TierLow', 75) .. '% GPU', { { '-5', function() bump('TierLow', -5, 10, 98) end }, { '+5', function() bump('TierLow', 5, 10, 98) end } } },
    { 'STEALTH ABOVE', H.num('TierStealth', 90) .. '% GPU', { { '-5', function() bump('TierStealth', -5, 10, 100) end }, { '+5', function() bump('TierStealth', 5, 10, 100) end } } },
    { 'ON BATTERY', 'at least ' .. (names[H.num('BatteryMinTier', 1)] or '?'), { { '-', function() bump('BatteryMinTier', -1, 0, 3) end }, { '+', function() bump('BatteryMinTier', 1, 0, 3) end } } },
    { 'HOW IT WORKS', 'Steps down 5 s after the GPU crosses a line, back up 20 s after it is 15% lower', {} },
  }
end

local function rowsSystem()
  local function go(cmd) return function() SKIN:Bang(cmd) end end
  return {
    { 'LOCK', 'Lock the PC', { { 'LOCK', go('["rundll32.exe" "user32.dll,LockWorkStation"]') } } },
    { 'SLEEP', 'Suspend (hibernates if hibernation is on)', { { 'SLEEP', go('["rundll32.exe" "powrprof.dll,SetSuspendState 0,1,0"]') } } },
    { 'RESTART', 'Restart in 5 seconds', { { armed == 'restart' and 'CONFIRM' or 'RESTART', function() if arm('restart') then SKIN:Bang('["shutdown.exe" "/r /t 5"]') end end, armed == 'restart' } } },
    { 'SHUT DOWN', 'Power off in 5 seconds', { { armed == 'shutdown' and 'CONFIRM' or 'SHUT DOWN', function() if arm('shutdown') then SKIN:Bang('["shutdown.exe" "/s /t 5"]') end end, armed == 'shutdown' } } },
    { 'DISPLAY', 'Resolution, HDR, refresh', { { 'OPEN', go('["ms-settings:display"]') } } },
    { 'SOUND', 'Devices and volume', { { 'OPEN', go('["ms-settings:sound"]') } } },
    { 'NETWORK', 'Wi-Fi and VPN', { { 'WI-FI', go('["ms-settings:network-wifi"]') }, { 'BLUETOOTH', go('["ms-settings:bluetooth"]') } } },
    { 'BATTERY', 'Power mode and battery saver', { { 'OPEN', go('["ms-settings:batterysaver"]') } } },
    { 'TASKBAR', 'Auto-hide or TranslucentTB keeps the dash visible', { { 'OPEN', go('["ms-settings:taskbar"]') } } },
    { 'HUD', 'Reload every module', { { 'REFRESH', function() SKIN:Bang('!RefreshGroup', 'Spaceship') end }, { 'MANAGE', go('[!Manage]') } } },
  }
end

local function rowsPresets()
  local rows = {}
  for n = 1, 6 do
    local stamp = readFirst(RES .. 'Presets\\' .. n .. '\\stamp.txt')
    rows[#rows + 1] = { 'PRESET ' .. n, stamp and ('saved ' .. stamp) or 'empty', {
      { 'SAVE', function() savePreset(n) end }, { 'LOAD', function() loadPreset(n) end } } }
  end
  local u = readFirst(RES .. 'Presets\\_undo\\stamp.txt')
  rows[#rows + 1] = { 'UNDO LAST LOAD', u and ('state from ' .. u) or 'nothing to undo', { { 'UNDO', function()
    if not u then say('NOTHING TO UNDO'); return end
    for _, f in ipairs(PRESET_FILES) do copyFile(RES .. 'Presets\\_undo\\' .. f, RES .. f) end
    say('UNDONE'); SKIN:Bang('!RefreshGroup', 'Spaceship') end } } }
  rows[#rows + 1] = { 'WHAT IS SAVED', 'Theme, scale, tiers, sensors, positions, slot choices and app catalog', {} }
  return rows
end

local BUILD = { rowsModules, rowsLayout, rowsTheme, rowsApps, rowsSensors, rowsPerf, rowsSystem, rowsPresets }

-- ---------------------------------------------------------------- draw
function Update()
  H.refreshTier()
  local z = H.zones[1]
  local c = H.canvas(1)
  local A1, D, T = H.C.accent, H.C.dim, H.C.text
  actions = {}
  if armed and os.time() - armedAt > 6 then armed = nil end
  -- panel
  c:fillPoly({ { 24, 0 }, { z.w, 0 }, { z.w, z.h - 24 }, { z.w - 24, z.h }, { 0, z.h }, { 0, 24 } }, { 3, 9, 16 }, 238)
  c:chamfer(0, 0, z.w, z.h, 24, A1, 1.6)
  H.text(1, 1, 28, 18, 'CONTROL CENTER', { size = 16, font = H.fontTitle, weight = 700, color = A1 })
  H.text(1, 2, 330, 24, 'SPACESHIP HUD  /  ' .. H.str('DeviceName', ''), { size = 10, color = D })
  c:line(22, 62, z.w - 22, 62, D, 1, 200)
  c:line(z.w - 44, 18, z.w - 24, 38, A1, 1.8); c:line(z.w - 24, 18, z.w - 44, 38, A1, 1.8)
  H.hit(1, 1, z.w - 52, 10, 36, 36, 'Close')
  actions[1] = function() SKIN:Bang('!DeactivateConfig') end
  -- tabs
  for i, name in ipairs(TABS) do
    local y = TY + (i - 1) * (TH + 6)
    local on = i == tab
    c:fillRect(TX, y, TW, TH, on and A1 or H.C.panel, on and 50 or 120)
    if on then c:line(TX, y, TX, y + TH, A1, 3) end
    c:rect(TX, y, TW, TH, on and A1 or D, 1)
    H.text(1, 2 + i, TX + 16, y + TH / 2, name, { size = 11, font = H.fontText, weight = 700, align = 'LeftCenter', color = on and T or D })
    H.hit(1, 1 + i, TX, y, TW, TH, name)
    local ti = i
    actions[1 + i] = function() tab = ti; page = 1 end
  end
  -- rows
  local rows = BUILD[tab]()
  for r = 1, NROWS do
    local row = rows[r]
    local y = RY + (r - 1) * RH
    local tl, tv = 11 + (r - 1) * 2 + 1, 11 + (r - 1) * 2 + 2
    if row then
      c:hair(CX, y + RH - 4, CX + CW, y + RH - 4, D, 1, 60)
      if row[4] then
        local col = {}
        for v in string.gmatch(row[4], '%d+') do col[#col + 1] = tonumber(v) end
        c:fillRect(CX, y + 8, 26, 26, col, 255, 4)
      end
      local lx = row[4] and CX + 36 or CX + 8
      H.text(1, tl, lx, y + 4, row[1], { size = 10.5, font = H.fontText, weight = 700, color = T, clip = 260 })
      local nb = #row[3]
      local bx0 = CX + CW - nb * (BW + BG)
      H.text(1, tv, lx, y + 23, row[2] or '', { size = 9.5, color = D, clip = bx0 - lx - 10 })
      for b = 1, 4 do
        local hi = 10 + (r - 1) * 4 + b
        local tb = 43 + (r - 1) * 4 + b
        local btn = row[3][b]
        if btn then
          local bx = bx0 + (b - 1) * (BW + BG)
          c:fillRect(bx, y + 6, BW, 30, btn[3] and A1 or H.C.panel, btn[3] and 70 or 140)
          c:rect(bx, y + 6, BW, 30, btn[3] and A1 or D, 1.2)
          H.text(1, tb, bx + BW / 2, y + 21, btn[1], { size = 9.5, weight = 700, align = 'CenterCenter', color = btn[3] and T or A1, clip = BW - 6 })
          H.hit(1, hi, bx, y + 6, BW, 30, btn[1])
          actions[hi] = btn[2]
        else
          H.hideText(1, tb); H.hideHit(1, hi)
        end
      end
    else
      H.hideText(1, tl); H.hideText(1, tv)
      for b = 1, 4 do H.hideText(1, 43 + (r - 1) * 4 + b); H.hideHit(1, 10 + (r - 1) * 4 + b) end
    end
  end
  -- footer status
  c:line(22, z.h - 50, z.w - 22, z.h - 50, D, 1, 200)
  H.text(1, 11, 28, z.h - 30, msg, { size = 10, font = H.fontNum, align = 'LeftCenter', color = os.time() - msgAt < 6 and H.C.warn or D, clip = z.w - 60 })
  c:flush()
  return 0
end

function OnClick(zi, k)
  local fn = actions[k]
  if fn then fn() end
  Update()
end
function OnRightClick(zi, k) end
function OnScroll(zi, k, d)
  if tab == 1 then page = math.max(1, page + d); Update() end
end
function OnHover(zi, k, on) end
