-- Control Center (O_control, 1040 x 900). Aurum-style adjustability for the whole HUD.
local H, A, Z, G
local RES
local TABS = { 'MODULES', 'LAYOUT', 'THEME', 'APPS', 'SENSORS', 'PERF', 'SYSTEM', 'PRESETS', 'DATA', 'JARVIS' }
local tab, page, selMod = 1, 1, 1
local msg, msgAt = 'READY', 0
local armed, armedAt = nil, 0
local actions = {}
local slotCursor = {}

-- geometry inside the zone
local TX, TY, TW, TH = 22, 78, 170, 46
local CX, CW, RY, RH, NROWS = 214, 790, 74, 84, 9     -- roomier rows; the list scrolls
local scroll = {}                                     -- first visible row per tab
local BARHIT, NSLICE, barMax = 10 + NROWS * 4 + 1, 16, 1  -- the scroll bar's click area: NSLICE hits from spare H1_47; barMax = last first-row
local dragging = false                                    -- true between a bar mouse-down and the mouse-up
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
local saved = {}                  -- what State.inc already holds, so a click writes only what changed

function Initialize()
  RES = SKIN:GetVariable('@')
  H = dofile(RES .. 'Scripts\\lib.lua')
  A = dofile(RES .. 'Scripts\\apps.lua')
  Z = dofile(RES .. 'Data\\zones.lua')
  G = dofile(RES .. 'Scripts\\guard.lua')
  H.init()
  A.load()
  SKIN:Bang('!SetOption', 'Bounds', 'Shape', 'Rectangle 0,0,(#WW#*#Scale#),(#WH#*#Scale#) | Fill Color 0,0,0,1 | StrokeWidth 0')
  SKIN:Bang('!SetOption', 'Bounds', 'MouseScrollUpAction', '[!CommandMeasure mScript "OnScroll(1,0,-1)"]')
  SKIN:Bang('!SetOption', 'Bounds', 'MouseScrollDownAction', '[!CommandMeasure mScript "OnScroll(1,0,1)"]')
  SKIN:Bang('!SetOption', 'Bounds', 'LeftMouseUpAction', '[!CommandMeasure mScript "EndDrag()"]')
  SKIN:Bang('!SetOption', 'Bounds', 'MouseLeaveAction', '[!CommandMeasure mScript "EndDrag()"]')
  for i = 1, NSLICE do SKIN:Bang('!SetOption', 'H1_' .. (BARHIT + i - 1), 'LeftMouseDownAction', '[!CommandMeasure mScript "OnBarDown(' .. i .. ',$MouseY:%$)"]') end
  -- reopen on the tab / page / module you were on: most settings refresh every module, this one included
  tab = math.max(1, math.min(#TABS, math.floor(H.num('CtlTab', 1))))
  page = math.max(1, math.floor(H.num('CtlPage', 1)))
  selMod = math.max(1, math.min(#Z.modules, math.floor(H.num('CtlMod', 1))))
  saved = { CtlTab = tab, CtlPage = page, CtlMod = selMod }
end

-- remember the current view in State.inc so a refresh comes back to it
local function saveView()
  for k, v in pairs({ CtlTab = tab, CtlPage = page, CtlMod = selMod }) do
    if saved[k] ~= v then saved[k] = v; SKIN:Bang('!WriteKeyValue', 'Variables', k, v, RES .. 'State.inc') end
  end
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

-- a HUD-wide setting is saved at once but the HUD reloads later: on RELOAD or when the panel closes
local pending = false
local function later() pending = true end
local function flush()
  if not pending then return false end
  pending = false                 -- first, so the reload of this panel cannot repeat it
  SKIN:Bang('!RefreshGroup', 'Spaceship')
  return true
end
function Flush() flush() end      -- Control.ini OnCloseAction: closed from the menu instead of the X

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
  later()
end

local function bump(var, delta, lo, hi, file, refresh)
  local v = H.clamp((tonumber(SKIN:GetVariable(var, '0')) or 0) + delta, lo, hi)
  v = math.floor(v * 100 + 0.5) / 100
  writeVar(file or 'Settings.inc', var, v)
  say(var .. ' = ' .. v)
  if refresh then later() end
  return v
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
  SKIN:Bang('!RefreshGroup', 'Spaceship')      -- at once: the files changed under the panel
end

-- ---------------------------------------------------------------- tab contents
-- each row: { label, value, { {text, fn, on}, ... }, swatch }
local function rowsModules()
  local rows = {}
  rows[#rows + 1] = { 'ALL MODULES', 'Scroll for every module. Hold Ctrl and use Rainmeter Manage for anything else.', {
    { 'ALL ON', function() for _, m in ipairs(Z.modules) do setModule(m, true) end; say('ALL MODULES ON') end },
  } }
  for i = 1, #Z.modules do
    local m = Z.modules[i]
    local off = SKIN:GetVariable('Off_' .. m.key, '0') == '1'
    local ct = SKIN:GetVariable('CT_' .. m.key, '0') == '1'
    rows[#rows + 1] = { m.name, (off and 'OFF' or 'ON') .. (ct and '  /  CLICK-THROUGH' or ''), {
      { off and 'TURN ON' or 'TURN OFF', function() setModule(m, off) end, not off },
      { ct and 'CLICKABLE' or 'CLICK-THRU', function() setClick(m, not ct) end, ct },
      { 'ADJUST', function() selMod = i; tab = 2 end },
    } }
  end
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
        say(string.format('FIT TO %dx%d (SCALE %.3f)', w, h, s)); later() end } } },
    { 'RESET ALL OFFSETS', 'Every module back to the designed layout', { { armed == 'resetall' and 'CONFIRM' or 'RESET ALL', function()
      if arm('resetall') then
        for _, mm in ipairs(Z.modules) do writeVar('Offsets.inc', mm.key .. '_DX', 0); writeVar('Offsets.inc', mm.key .. '_DY', 0) end
        later(); say('ALL OFFSETS RESET') end end, armed == 'resetall' } } },
  }
end

local function rowsTheme()
  local rows = {}
  local cur = H.str('ColorAccent', '')
  for _, t in ipairs(THEMES) do
    rows[#rows + 1] = { t[1], t[2], { { cur == t[2] and 'ACTIVE' or 'APPLY', function() applyTheme(t) end, cur == t[2] } }, t[2] }
  end
  rows[#rows + 1] = { 'WINDOW TINT', tostring(H.num('GlassTint', 46)) .. ' / 255', { { '-10', function() bump('GlassTint', -10, 0, 255, nil, true) end }, { '+10', function() bump('GlassTint', 10, 0, 255, nil, true) end }, { 'CLEAR', function() writeVar('Settings.inc', 'GlassTint', 0); later() end } } }
  rows[#rows + 1] = { 'GLOW', string.format('strength %d   width %.1f', H.num('GlowAlpha', 52), H.num('GlowWidth', 3)), { { '-', function() bump('GlowAlpha', -8, 0, 160, nil, true) end }, { '+', function() bump('GlowAlpha', 8, 0, 160, nil, true) end }, { 'W-', function() bump('GlowWidth', -0.4, 1, 8, nil, true) end }, { 'W+', function() bump('GlowWidth', 0.4, 1, 8, nil, true) end } } }
  rows[#rows + 1] = { 'CORES / TEXT GLOW', string.format('cores %.1f (1 = white-hot)   text glow %d px', H.num('CoreWhite', 0.3), H.num('TextGlow', 4)), { { 'C-', function() bump('CoreWhite', -0.1, 0, 1, nil, true) end }, { 'C+', function() bump('CoreWhite', 0.1, 0, 1, nil, true) end }, { 'T-', function() bump('TextGlow', -1, 0, 12, nil, true) end }, { 'T+', function() bump('TextGlow', 1, 0, 12, nil, true) end } } }
  rows[#rows + 1] = { 'GLASS GLARE', tostring(H.num('GlassGlare', 12)) .. '  smudges + reflections', { { '-4', function() bump('GlassGlare', -4, 0, 60, nil, true) end }, { '+4', function() bump('GlassGlare', 4, 0, 60, nil, true) end }, { 'OFF', function() writeVar('Settings.inc', 'GlassGlare', 0); later() end } } }
  local scan = H.num('ScanLines', 1) == 1
  rows[#rows + 1] = { 'SCANLINES', (scan and 'ON' or 'OFF') .. '  darkness ' .. tostring(H.num('ScanAlpha', 14)), { { scan and 'OFF' or 'ON', function() writeVar('Settings.inc', 'ScanLines', scan and 0 or 1); later() end }, { '-4', function() bump('ScanAlpha', -4, 0, 14, nil, true) end }, { '+4', function() bump('ScanAlpha', 4, 0, 14, nil, true) end } } }
  -- transparency: the metal, the dark tints behind the HUD, and every HUD element
  -- hull: brightness (0 = black metal, 100 = as rendered) and opacity (lower = wallpaper shows through)
  rows[#rows + 1] = { 'HULL', string.format('brightness %d%%   opacity %d / 255', H.num('FrameBrightness', 25), H.num('HullAlpha', 255)), { { 'B-', function() bump('FrameBrightness', -5, 0, 100, nil, true) end }, { 'B+', function() bump('FrameBrightness', 5, 0, 100, nil, true) end }, { 'O-', function() bump('HullAlpha', -25, 0, 255, nil, true) end }, { 'O+', function() bump('HullAlpha', 25, 0, 255, nil, true) end } } }
  rows[#rows + 1] = { 'DARK TINTS', tostring(H.num('ShadeAlpha', 255)) .. ' / 255  (shading behind the HUD on the glass)', { { '-25', function() bump('ShadeAlpha', -25, 0, 255, nil, true) end }, { '+25', function() bump('ShadeAlpha', 25, 0, 255, nil, true) end }, { 'OFF', function() writeVar('Settings.inc', 'ShadeAlpha', 0); later() end } } }
  rows[#rows + 1] = { 'HUD OPACITY', tostring(H.num('HudAlpha', 255)) .. ' / 255  (every line and label)', { { '-25', function() bump('HudAlpha', -25, 40, 255, nil, true) end }, { '+25', function() bump('HudAlpha', 25, 40, 255, nil, true) end }, { 'FULL', function() writeVar('Settings.inc', 'HudAlpha', 255); later() end } } }
  local img, off = H.num('UseShipImage', 0) == 1, H.num('FrameOff', 0) == 1
  local function art(useImg, frameOff)
    return function()
      writeVar('Settings.inc', 'UseShipImage', useImg); writeVar('Settings.inc', 'FrameOff', frameOff)
      later()
    end
  end
  rows[#rows + 1] = { 'COCKPIT ART', off and 'OFF  no cockpit, window tint or glow - just the HUD'
      or (img and ('PICTURE  Images\\' .. H.str('ShipImage', 'ship.png')) or 'RENDERED  textured hull (Images\\hull.png)'),
    { { 'RENDERED', art(0, 0), not img and not off }, { 'PICTURE', art(1, 0), img and not off }, { 'OFF', art(0, 1), off } } }
  rows[#rows + 1] = { 'WARNING COLOUR', H.str('ColorWarn', ''), { { 'ORANGE', function() writeVar('Settings.inc', 'ColorWarn', '255,130,40'); later() end }, { 'YELLOW', function() writeVar('Settings.inc', 'ColorWarn', '255,220,60'); later() end } } }
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
    -- repoint the panel's own measure, so the reading beside the buttons follows without a reload
    local function map(d) return function()
      local n = bump(var, d, -1, 199, nil, true)
      SKIN:Bang('!SetOption', 'mHw' .. s, 'RegValue', 'ValueRaw' .. n)
      SKIN:Bang('!SetOption', 'mHw' .. s, 'Disabled', n < 0 and 1 or 0)
      SKIN:Bang('!UpdateMeasure', 'mHw' .. s)
    end end
    rows[#rows + 1] = { string.upper(s), idx < 0 and 'NOT MAPPED' or string.format('#%d   =   %s', idx, v and tostring(v) or '--'), {
      { '-', map(-1) }, { '+', map(1) } } }
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

local function core(cmd)
  SKIN:Bang('["' .. RES .. 'Bin\\ShipCore.exe" ' .. cmd .. ' "' .. RES .. '"]')
end

local function rowsSystem()
  local function go(cmd) return function() SKIN:Bang(cmd) end end
  return {
    { 'LOCK', 'Lock the PC', { { 'LOCK', go('["rundll32.exe" "user32.dll,LockWorkStation"]') } } },
    { 'SLEEP', 'Sleep the PC', { { 'SLEEP', function() core('sleep') end } } },
    { 'RESTART', 'Restart in 5 seconds', { { armed == 'restart' and 'CONFIRM' or 'RESTART', function() if arm('restart') then SKIN:Bang('["shutdown.exe" "/r /t 5"]') end end, armed == 'restart' } } },
    { 'SHUT DOWN', 'Power off in 5 seconds', { { armed == 'shutdown' and 'CONFIRM' or 'SHUT DOWN', function() if arm('shutdown') then SKIN:Bang('["shutdown.exe" "/s /t 5"]') end end, armed == 'shutdown' } } },
    { 'DISPLAY', 'Resolution, HDR, refresh', { { 'OPEN', go('["ms-settings:display"]') } } },
    { 'SOUND', 'Devices and volume', { { 'OPEN', go('["ms-settings:sound"]') } } },
    { 'NETWORK', 'Wi-Fi and VPN', { { 'WI-FI', go('["ms-settings:network-wifi"]') }, { 'BLUETOOTH', go('["ms-settings:bluetooth"]') } } },
    { 'BATTERY', 'Power mode and battery saver', { { 'OPEN', go('["ms-settings:batterysaver"]') } } },
    { 'TASKBAR', H.num('FrameBehindTaskbar', 0) == 1 and 'Cockpit runs behind the taskbar' or 'Cockpit stops at the taskbar',
      { { 'BEHIND', function() writeVar('Settings.inc', 'FrameBehindTaskbar', 1); SKIN:Bang('!Refresh', 'Spaceship\\Frame'); say('COCKPIT BEHIND TASKBAR') end, H.num('FrameBehindTaskbar', 0) == 1 },
        { 'ABOVE', function() writeVar('Settings.inc', 'FrameBehindTaskbar', 0); SKIN:Bang('!Refresh', 'Spaceship\\Frame'); say('COCKPIT STOPS AT TASKBAR') end, H.num('FrameBehindTaskbar', 0) ~= 1 },
        { 'SETTINGS', go('["ms-settings:taskbar"]') } } },
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

-- ---------------------------------------------------------------- DATA: links to your accounts and notes
-- key/value lines of a ShipCore data file (Data\<name>), plus its age in seconds
local function dataFile(name)
  local t, age = {}, nil
  local f = io.open(RES .. 'Data\\' .. name, 'r')
  if not f then return nil end
  for line in f:lines() do
    local k, v = string.match(line, '^(%u+) ?(.*)$')
    if k == 'T' then age = os.time() - (tonumber(v) or 0)
    elseif k == 'E' then t.E = t.E or v
    elseif k then t[k] = v end
  end
  f:close()
  t.age = age
  return t
end

local function touch(name)
  local f = io.open(RES .. 'Data\\' .. name, 'w')
  if f then f:write('1'); f:close() end
end

local function rowsData()
  local rows = {}
  local win = dataFile('windows.txt')
  local alive = win and win.age and win.age < 20
  -- Gmail
  local m = dataFile('mail.txt')
  local mailTxt = not m and 'helper not running yet' or (m.UNREAD and (m.UNREAD .. ' unread') or (m.OFF and 'not set up - SET UP signs in with a Gmail app password' or ('problem: ' .. (m.ERR or '?'))))
  rows[#rows + 1] = { 'GMAIL', mailTxt, { { 'SET UP', function() core('setup-gmail'); say('GMAIL SETUP WINDOW OPENED') end },
    { 'CHECK', function() touch('mail.refresh'); say('CHECKING GMAIL...') end },
    { 'OPEN', function() SKIN:Bang('["https://mail.google.com"]') end } } }
  -- calendars
  local c = dataFile('calendar.txt')
  local calTxt = 'none yet - MANAGE to add your calendar links'
  if c and c.C then
    local n, e = string.match(c.C, '(%d+) (%d+)')
    calTxt = (n or '0') .. ' on' .. ((tonumber(e) or 0) > 0 and ('   ' .. e .. ' failed') or '')
    if c.E then
      local st, title = string.match(c.E, '^(%d+)|%d+|%d|[^|]*|(.*)$')
      if st then calTxt = calTxt .. '   next: ' .. title .. ' ' .. os.date('%a %H:%M', tonumber(st)) end
    end
  end
  rows[#rows + 1] = { 'CALENDARS', calTxt, { { 'MANAGE', function() core('setup-calendars'); say('CALENDAR WINDOW OPENED') end },
    { 'SYNC', function() touch('calendar.refresh'); say('SYNCING CALENDARS...') end } } }
  -- Obsidian to-do note
  local note = H.str('ObsidianTodo', '')
  rows[#rows + 1] = { 'TO-DO NOTE', note ~= '' and note or 'not set - BROWSE to your Obsidian to-do note', {
    { 'BROWSE', function() core('pick-todo'); say('CHOOSE YOUR NOTE IN THE WINDOW') end },
    { 'OPEN', function() if note ~= '' then SKIN:Bang('["' .. note .. '"]') end end },
    { 'CLEAR', function() writeVar('Settings.inc', 'ObsidianTodo', ''); later(); say('TO-DO NOTE CLEARED') end } } }
  local rt = H.num('ReticleTodo', 1) == 1
  rows[#rows + 1] = { 'RETICLE TO-DOS', rt and 'ON - the reticle locks onto your next to-do (usage when the list is empty)' or 'OFF - the reticle always shows usage', {
    { 'ON', function() writeVar('Settings.inc', 'ReticleTodo', 1); SKIN:Bang('!Refresh', 'Spaceship\\Center\\Target'); say('RETICLE TO-DOS ON') end, rt },
    { 'OFF', function() writeVar('Settings.inc', 'ReticleTodo', 0); SKIN:Bang('!Refresh', 'Spaceship\\Center\\Target'); say('RETICLE TO-DOS OFF') end, not rt } } }
  local ipm = H.num('IpMask', 0) == 1
  rows[#rows + 1] = { 'IP ADDRESSES', ipm and 'MASKED in the network block' or 'SHOWN in the network block', {
    { 'SHOW', function() writeVar('Settings.inc', 'IpMask', 0); SKIN:Bang('!Refresh', 'Spaceship\\Right\\SysInfo') end, not ipm },
    { 'MASK', function() writeVar('Settings.inc', 'IpMask', 1); SKIN:Bang('!Refresh', 'Spaceship\\Right\\SysInfo') end, ipm } } }
  local sp = dataFile('speed.txt')
  local spTxt = string.format('%d down / %d up Mbps   %s', H.num('LinkDownMbps', 0), H.num('LinkUpMbps', 0), H.str('LastSpeedTest', 'never tested'))
  if sp and sp.STATE == 'testing' and (sp.age or 999) < 180 then spTxt = 'testing...' elseif sp and sp.STATE == 'error' then spTxt = 'last test failed: ' .. (sp.ERR or '?') end
  rows[#rows + 1] = { 'SPEED TEST', spTxt, { { 'RUN', function() core('speedtest'); say('SPEED TEST RUNNING (ABOUT 30 S)') end } } }
  rows[#rows + 1] = { 'HELPER', alive and 'ShipCore running - window states, Gmail, calendars, brightness, mic' or 'ShipCore not running - it starts with the HUD; RESTART to try now', {
    { 'RESTART', function() SKIN:Bang('!CommandMeasure', 'mCore', 'Run', 'Spaceship\\Controller'); say('STARTING SHIPCORE...') end },
    { 'LOG', function() SKIN:Bang('["' .. RES .. 'Data\\shipcore.log"]') end } } }
  rows[#rows + 1] = { 'PRIVACY', 'Gmail login and calendar links are stored encrypted in %LOCALAPPDATA%\\SpaceshipHUD, never in the skin', {} }
  return rows
end


-- ---------------------------------------------------------------- JARVIS tab
local JCOLORS = {
  { 'THEME', '' }, { 'CYAN', '0,210,255' }, { 'DEEP BLUE', '30,110,255' }, { 'ICE', '200,235,255' }, { 'VIOLET', '170,110,255' },
  { 'GOLD', '255,190,70' }, { 'EMERALD', '60,255,160' }, { 'CRIMSON', '255,70,90' }, { 'WHITE', '235,245,255' },
}
local WHISPERS = { 'tiny.en', 'base.en', 'small.en', 'medium.en' }

local function jset(key, value, quiet)
  if type(value) == 'string' then value = value:gsub('%c', '') end   -- a line break would write a second line into Settings.inc
  writeVar('Settings.inc', key, value)
  SKIN:Bang('!SetVariable', key, value, 'Spaceship\\Center\\Sphere')       -- the hologram picks it up live
  if not quiet then say(key .. ' = ' .. (value == '' and '(default)' or tostring(value))) end
end
local function jbump(key, delta, lo, hi, default)
  local v = H.clamp((tonumber(SKIN:GetVariable(key, '')) or default) + delta, lo, hi)
  jset(key, math.floor(v * 100 + 0.5) / 100)
end
local function jcall(fn) SKIN:Bang('!CommandMeasure', 'mScript', fn, 'Spaceship\\Center\\Sphere') end
local function cycle(list, cur, d)
  local idx = 1
  for i, v in ipairs(list) do if v == cur then idx = i end end
  return list[(idx - 1 + d) % #list + 1]
end
local function models(file)
  local out = {}
  local f = io.open(RES .. 'Data\\' .. (file or 'jarvis_models.txt'), 'r')
  if f then for line in f:lines() do if line ~= '' then out[#out + 1] = line end end; f:close() end
  return out
end
local function colorRow(label, key, default)
  local cur = H.str(key, '')
  local name = 'THEME'
  for _, c in ipairs(JCOLORS) do if c[2] == cur then name = c[1] end end
  local idx = 1
  for i, c in ipairs(JCOLORS) do if c[1] == name then idx = i end end
  local swatch = cur ~= '' and cur or default
  return { label, name == 'THEME' and 'follows the HUD theme' or (name .. '  ' .. cur), {
    { '<', function() jset(key, JCOLORS[(idx - 2) % #JCOLORS + 1][2]) end },
    { '>', function() jset(key, JCOLORS[idx % #JCOLORS + 1][2]) end },
    { 'RESET', function() jset(key, '') end, name == 'THEME' } }, swatch }
end

local function rowsJarvis()
  local rows = {}
  local j = dataFile('jarvis.txt')
  local alive = j and j.age and j.age < 8
  local status = not alive and 'OFFLINE - START it, or run SETUP first' or
    (((j.ERR or '') ~= '') and ('PROBLEM: ' .. j.ERR) or ('RUNNING - ' .. string.upper(j.STATE or 'idle')))
  rows[#rows + 1] = { 'SERVICE', status, {
    { 'START', function() jcall('StartService()'); say('STARTING JARVIS...') end, alive },
    { 'STOP', function() jcall('StopService()'); say('STOPPING JARVIS') end },
    { 'LOG', function() SKIN:Bang('["notepad.exe" "' .. RES .. 'Data\\jarvis.log"]') end } } }
  local en, au = H.num('JarvisEnabled', 1) == 1, H.num('JarvisAutoStart', 1) == 1
  rows[#rows + 1] = { 'JARVIS', (en and 'ON' or 'OFF') .. (au and '   starts with the HUD' or '   start it yourself'), {
    { 'ON', function() jset('JarvisEnabled', 1) end, en },
    { 'OFF', function() jset('JarvisEnabled', 0); jcall('StopService()') end, not en },
    { 'AUTO-START', function() jset('JarvisAutoStart', au and 0 or 1) end, au } } }
  local ms = models()
  local m, mf = H.str('JarvisModel', 'llama3.1:8b'), H.str('JarvisModelFast', '')
  rows[#rows + 1] = { 'MODEL', m .. (#ms == 0 and '   - start Jarvis once to list your installed models' or ('   - ' .. #ms .. ' installed, use < > to switch')), {
    { '<', function() if #ms > 0 then jset('JarvisModel', cycle(ms, m, -1)) end end },
    { '>', function() if #ms > 0 then jset('JarvisModel', cycle(ms, m, 1)) end end } } }
  local fl = { '' }
  for _, x in ipairs(ms) do fl[#fl + 1] = x end
  rows[#rows + 1] = { 'FAST MODEL', (mf == '' and 'same as MODEL' or mf) .. '   - a smaller model used while the GPU is busy (LITE / LOW tier), so he stays quick while you game', {
    { '<', function() jset('JarvisModelFast', cycle(fl, mf, -1)) end },
    { '>', function() jset('JarvisModelFast', cycle(fl, mf, 1)) end } } }
  -- the notes Jarvis reads: an "about me" note (personalises answers) and the Obsidian to-do note
  local prof = H.str('JarvisProfile', '')
  local function newProfile()
    local dst = RES .. 'Jarvis\\about-me.md'
    local f = io.open(dst, 'rb')
    if f then f:close() else
      local src = io.open(RES .. 'Jarvis\\about-me-template.md', 'rb')
      local body = src and src:read('*a') or '# About me (for Jarvis)\n'
      if src then src:close() end
      local o = io.open(dst, 'wb'); if o then o:write(body); o:close() end
    end
    jset('JarvisProfile', dst, true)
    SKIN:Bang('["' .. dst .. '"]')
    say('ABOUT-ME NOTE CREATED - WRITE A COUPLE OF PARAGRAPHS AND SAVE')
  end
  rows[#rows + 1] = { 'ABOUT ME', prof ~= '' and ('Read on every question: ' .. prof) or
    'Not set. A short note about you (a couple of paragraphs) that Jarvis reads to personalise his answers.', {
    { 'BROWSE', function() core('pick-profile'); say('CHOOSE YOUR NOTE IN THE WINDOW') end },
    { 'NEW', newProfile },
    { 'EDIT', function() if prof ~= '' then SKIN:Bang('["' .. prof .. '"]') else say('BROWSE OR NEW FIRST') end end },
    { 'CLEAR', function() jset('JarvisProfile', '') end } } }
  local todo = H.str('ObsidianTodo', '')
  rows[#rows + 1] = { 'TO-DO NOTE', todo ~= '' and ('Jarvis reads its open - [ ] items: ' .. todo) or
    'Not set. Jarvis (and the reticle) read the open - [ ] items of your Obsidian to-do note.', {
    { 'BROWSE', function() core('pick-todo'); say('CHOOSE YOUR NOTE IN THE WINDOW') end },
    { 'OPEN', function() if todo ~= '' then SKIN:Bang('["' .. todo .. '"]') end end } } }
  local vault = H.str('JarvisVault', '')
  local vshow = vault ~= '' and vault or (todo ~= '' and (string.match(todo, '^(.*)\\[^\\]*$') or '') .. '  (the to-do note\'s folder)' or 'not set')
  rows[#rows + 1] = { 'NOTES VAULT', 'Searched when you say "search my notes for ...": ' .. vshow, {
    { 'BROWSE', function() core('pick-vault'); say('CHOOSE YOUR VAULT FOLDER IN THE WINDOW') end },
    { 'DEFAULT', function() jset('JarvisVault', '') end, vault == '' } } }
  local smart = H.num('JarvisSmartSearch', 1) == 1
  rows[#rows + 1] = { 'NOTE SEARCH', smart and 'SMART - ChromaDB finds notes by meaning (keyword search if it is not installed)' or 'KEYWORD - exact words only', {
    { 'SMART', function() jset('JarvisSmartSearch', 1) end, smart }, { 'KEYWORD', function() jset('JarvisSmartSearch', 0) end, not smart },
    { 'REINDEX', function() H.cmd('REINDEX ' .. os.time()); say('REBUILDING THE NOTES INDEX') end } } }
  local wm, wd = H.str('JarvisWhisper', 'small.en'), string.lower(H.str('JarvisWhisperDevice', 'auto'))
  rows[#rows + 1] = { 'SPEECH RECOGNITION', wm .. ' on ' .. string.upper(wd) .. '   - bigger models are more accurate but slower; AUTO uses the GPU when it can', {
    { '<', function() jset('JarvisWhisper', cycle(WHISPERS, wm, -1)) end },
    { '>', function() jset('JarvisWhisper', cycle(WHISPERS, wm, 1)) end },
    { string.upper(wd), function() jset('JarvisWhisperDevice', cycle({ 'auto', 'cpu', 'cuda' }, wd, 1)) end } } }
  local voice = H.str('JarvisVoice', '')
  local function find(name)
    for _, dir in ipairs({ 'Jarvis\\kokoro\\', 'Jarvis\\voices\\' }) do      -- both voice folders
      local f = io.open(RES .. dir .. name, 'rb')
      if f then f:close(); return RES .. dir .. name end
    end
  end
  local kokoro = find('kokoro-v1.0.onnx') or find('kokoro-v1.0.int8.onnx')
  local piper = find('en_GB-alan-medium.onnx')
  local isKokoro = voice ~= '' and string.find(string.lower(voice), 'kokoro', 1, true) ~= nil
  local rate = H.num('JarvisVoiceRate', 1)
  local kv = H.str('JarvisKokoroVoice', 'bm_lewis')
  local engine = voice == '' and 'WINDOWS built-in' or (isKokoro and ('KOKORO (natural) - ' .. kv) or 'PIPER (natural)')
  local vbtn = { { 'WINDOWS', function() jset('JarvisVoice', '') end, voice == '' },
    { 'KOKORO', function() if kokoro then jset('JarvisVoice', kokoro) else say('RUN SETUP TO DOWNLOAD THE KOKORO VOICE FIRST') end end, isKokoro } }
  if piper then vbtn[#vbtn + 1] = { 'PIPER', function() jset('JarvisVoice', piper) end, voice ~= '' and not isKokoro } end
  rows[#rows + 1] = { 'VOICE', engine .. '   - if a voice ever fails, that sentence uses the Windows voice', vbtn }
  local KV = { 'bm_lewis', 'bf_emma', 'am_michael', 'af_heart' }   -- the four to choose from; any other Kokoro name still works in Settings.inc
  local KVNAME = { bm_lewis = 'LEWIS (British, male)', bf_emma = 'EMMA (British, female)',
    am_michael = 'MICHAEL (American, male)', af_heart = 'HEART (American, female)' }
  rows[#rows + 1] = { 'KOKORO VOICE', (KVNAME[kv] or kv) .. '   speed ' .. rate .. '   - < > switches voice', {
    { '<', function() jset('JarvisKokoroVoice', cycle(KV, kv, -1)) end },
    { '>', function() jset('JarvisKokoroVoice', cycle(KV, kv, 1)) end },
    { 'SLOWER', function() jbump('JarvisVoiceRate', -1, -5, 5, 1) end },
    { 'FASTER', function() jbump('JarvisVoiceRate', 1, -5, 5, 1) end } } }
  local mood = string.lower(H.str('JarvisPersonality', 'playful'))
  if mood ~= 'proper' and mood ~= 'brief' then mood = 'playful' end
  local callme = H.str('JarvisCallMe', '')
  rows[#rows + 1] = { 'CALL ME', (callme ~= '' and callme or 'NO NAME') .. '   - what he calls you at the end of greetings and goodbyes', {
    { 'CHANGE', function() SKIN:Bang('!CommandMeasure', 'mInput', 'ExecuteBatch 1') end },
    { 'CLEAR', function() jset('JarvisCallMe', '') end, callme == '' } } }
  rows[#rows + 1] = { 'TYPE TO HIM', 'Type instead of speaking - he answers in the log (and aloud unless muted); a spoken yes is not accepted for a typed ask', {
    { 'TYPE', function() SKIN:Bang('!CommandMeasure', 'mAsk', 'ExecuteBatch 1') end } } }
  rows[#rows + 1] = { 'PERSONALITY', string.upper(mood) .. '   - how he words his own answers; fixed lines like "Done." stay the same', {
    { 'PROPER', function() jset('JarvisPersonality', 'proper') end, mood == 'proper' },
    { 'PLAYFUL', function() jset('JarvisPersonality', 'playful') end, mood == 'playful' },
    { 'BRIEF', function() jset('JarvisPersonality', 'brief') end, mood == 'brief' } } }
  local ww, wsens = H.num('JarvisWakeWord', 1) == 1, H.num('JarvisWakeSensitivity', 0.5)
  rows[#rows + 1] = { 'WAKE WORD', (ww and 'ON - say "Hey Jarvis"' or 'OFF - click the hologram') .. string.format('   threshold %.2f (lower = hears you more easily, higher = fewer false wakes)', wsens), {
    { 'ON', function() jset('JarvisWakeWord', 1) end, ww }, { 'OFF', function() jset('JarvisWakeWord', 0) end, not ww },
    { 'EASIER', function() jbump('JarvisWakeSensitivity', -0.05, 0.2, 0.9, 0.5) end },
    { 'STRICTER', function() jbump('JarvisWakeSensitivity', 0.05, 0.2, 0.9, 0.5) end } } }
  rows[#rows + 1] = { 'WAKE TRAINING', 'Teaches him your "Hey Jarvis", "Hey" and "Jarvis" (about 2 minutes; he says what to do)', {
    { 'TRAIN', function() H.cmd('TRAINWAKE ' .. os.time()); say('JARVIS WILL TELL YOU WHAT TO SAY') end } } }
  local heyOn, gap = H.num('JarvisWakeEasy', 0.5) > 0, H.num('JarvisWakeGap', 5)
  rows[#rows + 1] = { 'HEY ... JARVIS', heyOn and string.format('ON - your trained "Hey", a pause, then "Jarvis" within %d s wakes him (needs TRAIN)', gap) or 'OFF - only "Hey Jarvis" said together wakes him', {
    { 'ON', function() jset('JarvisWakeEasy', 0.5) end, heyOn }, { 'OFF', function() jset('JarvisWakeEasy', 0) end, not heyOn },
    { '-', function() jbump('JarvisWakeGap', -1, 2, 10, 5) end }, { '+', function() jbump('JarvisWakeGap', 1, 2, 10, 5) end } } }
  local mic, mics = H.str('JarvisMic', ''), models('jarvis_mics.txt')   -- listed by jarvis.py at start
  local function nextMic(d)
    if #mics == 0 then say('START JARVIS ONCE TO LIST THE MICROPHONES') else jset('JarvisMic', cycle(mics, mic, d)) end
  end
  rows[#rows + 1] = { 'MICROPHONE', (mic ~= '' and mic or 'WINDOWS DEFAULT') .. '   - used for the wake word and when he listens', {
    { '<', function() nextMic(-1) end }, { '>', function() nextMic(1) end },
    { 'DEFAULT', function() jset('JarvisMic', '') end, mic == '' } } }
  local duck, dlevel = H.num('JarvisDuck', 1) == 1, H.num('JarvisDuckLevel', 30)
  rows[#rows + 1] = { 'DUCK MUSIC', (duck and 'ON' or 'OFF') .. string.format(' - other sound goes down to %d %% while he listens (the whole Windows volume)', dlevel), {
    { 'ON', function() jset('JarvisDuck', 1) end, duck }, { 'OFF', function() jset('JarvisDuck', 0) end, not duck },
    { '-', function() jbump('JarvisDuckLevel', -10, 10, 80, 30) end }, { '+', function() jbump('JarvisDuckLevel', 10, 10, 80, 30) end } } }
  local barge = string.lower(H.str('JarvisBargeIn', 'wake'))
  if barge ~= 'off' and barge ~= 'voice' then barge = 'wake' end
  local bargeText = { off = 'OFF - only a click or the stop key stops him', wake = 'WAKE - "Hey Jarvis" while he talks stops him and he listens; "stop" or "be quiet" just stops him',
    voice = 'VOICE - any speech stops him (HEADPHONES ONLY: on speakers his own voice would); "stop" too' }
  rows[#rows + 1] = { 'BARGE-IN', bargeText[barge], {
    { 'OFF', function() jset('JarvisBargeIn', 'off') end, barge == 'off' },
    { 'WAKE', function() jset('JarvisBargeIn', 'wake') end, barge == 'wake' },
    { 'VOICE', function() jset('JarvisBargeIn', 'voice') end, barge == 'voice' } } }
  local sk = string.lower(H.str('JarvisStopKey', 'end')) ~= 'off'
  rows[#rows + 1] = { 'STOP KEY', sk and 'END - stops him while he talks, thinks or rings; free for other apps when he is idle' or 'OFF', {
    { 'END', function() jset('JarvisStopKey', 'end') end, sk }, { 'OFF', function() jset('JarvisStopKey', 'off') end, not sk } } }
  local fu, fwait = H.num('JarvisFollowUp', 1) == 1, H.num('JarvisFollowUpWait', 3)
  rows[#rows + 1] = { 'FOLLOW-UP', fu and string.format('ON - after any answer his ear stays open %d s, no wake word needed; talk that is not for him is ignored or he asks', fwait) or 'OFF - every question needs the wake word or a click', {
    { 'ON', function() jset('JarvisFollowUp', 1) end, fu }, { 'OFF', function() jset('JarvisFollowUp', 0) end, not fu },
    { '-', function() jbump('JarvisFollowUpWait', -1, 3, 30, 3) end }, { '+', function() jbump('JarvisFollowUpWait', 1, 3, 30, 3) end } } }
  local sil, ctx = H.num('JarvisSilence', 1), H.num('JarvisContext', 2048)
  rows[#rows + 1] = { 'LISTENING', string.format('answers after %.1f s of silence   - longer lets you pause mid-sentence, shorter answers sooner', sil), {
    { 'SHORTER', function() jbump('JarvisSilence', -0.5, 0.5, 6, 1) end },
    { 'LONGER', function() jbump('JarvisSilence', 0.5, 0.5, 6, 1) end } } }
  rows[#rows + 1] = { 'MODEL MEMORY', ctx .. ' tokens   - smaller uses less RAM and starts answering sooner; older messages are dropped to fit', {
    { '2048', function() jset('JarvisContext', 2048) end, ctx == 2048 },
    { '4096', function() jset('JarvisContext', 4096) end, ctx == 4096 },
    { '8192', function() jset('JarvisContext', 8192) end, ctx == 8192 } } }
  local ch, bs = H.num('JarvisChime', 1) == 1, H.num('BootSound', 1) == 1
  rows[#rows + 1] = { 'SOUNDS', 'startup.wav' .. (ch and ': click' or '') .. (bs and (ch and ' + startup' or ': startup') or ''), {
    { 'CHIME', function() jset('JarvisChime', ch and 0 or 1) end, ch },
    { 'STARTUP', function() jset('BootSound', bs and 0 or 1) end, bs },
    { 'TEST', function() SKIN:Bang('[Play "' .. RES .. 'Sounds\\startup.wav"]') end } } }
  rows[#rows + 1] = colorRow('COLOUR - STANDBY', 'JarvisColorIdle', H.str('ColorAccent', '0,210,255'))
  rows[#rows + 1] = colorRow('COLOUR - LISTENING', 'JarvisColorListen', '0,140,232')
  rows[#rows + 1] = colorRow('COLOUR - SPEAKING', 'JarvisColorSpeak', H.str('ColorAccent', '0,210,255'))
  rows[#rows + 1] = { 'ORB', string.format('brightness %.2f   size %.2f', H.num('JarvisOrbBright', 1), H.num('JarvisOrbSize', 1)), {
    { 'B-', function() jbump('JarvisOrbBright', -0.1, 0.4, 1.6, 1) end }, { 'B+', function() jbump('JarvisOrbBright', 0.1, 0.4, 1.6, 1) end },
    { 'S-', function() jbump('JarvisOrbSize', -0.05, 0.8, 1.15, 1) end }, { 'S+', function() jbump('JarvisOrbSize', 0.05, 0.8, 1.15, 1) end } } }
  rows[#rows + 1] = { 'ORB TINT', string.format('%.2f   - 0 = the animation\'s own colours, higher = more of the state colour', H.num('JarvisTint', 0.22)), {
    { '-', function() jbump('JarvisTint', -0.05, 0, 0.8, 0.22) end }, { '+', function() jbump('JarvisTint', 0.05, 0, 0.8, 0.22) end },
    { 'NATURAL', function() jset('JarvisTint', 0) end } } }
  local sh, ob, dl, br = H.num('JarvisShell', 1) == 1, H.num('JarvisOrbits', 1) == 1, H.num('JarvisDial', 1) == 1, H.num('JarvisBars', 1) == 1
  rows[#rows + 1] = { 'LAYERS', '3D network shell, tilted orbit rings, dial rings, voice bars - click to turn each on or off', {
    { 'SHELL', function() jset('JarvisShell', sh and 0 or 1) end, sh }, { 'ORBITS', function() jset('JarvisOrbits', ob and 0 or 1) end, ob },
    { 'DIAL', function() jset('JarvisDial', dl and 0 or 1) end, dl }, { 'BARS', function() jset('JarvisBars', br and 0 or 1) end, br } } }
  rows[#rows + 1] = { 'MOTION', string.format('speed %.2f   (spin and animation)', H.num('JarvisSpeed', 1)), {
    { 'SLOWER', function() jbump('JarvisSpeed', -0.25, 0.25, 3, 1) end }, { 'FASTER', function() jbump('JarvisSpeed', 0.25, 0.25, 3, 1) end },
    { 'RESET', function() jset('JarvisSpeed', 1) end } } }
  local mp = H.num('JarvisMutedPopup', 1) == 1
  rows[#rows + 1] = { 'CONVERSATION', mp and 'With the speakers muted, answers appear in the pop-up. CLEAR empties this log, not his memory.' or 'With the speakers muted, answers are still spoken (silently). CLEAR empties this log, not his memory.', {
    { 'OPEN', function() SKIN:Bang('!ActivateConfig', 'Spaceship\\Overlay\\Jarvis', 'Jarvis.ini') end },
    { armed == 'jforget' and 'CONFIRM' or 'CLEAR', function() if arm('jforget') then jcall('Forget()'); say('CONVERSATION CLEARED') end end, armed == 'jforget' },
    { 'MUTED POP-UP', function() jset('JarvisMutedPopup', mp and 0 or 1) end, mp } } }
  rows[#rows + 1] = { 'SETUP', 'Checks / installs Python packages, the speech model, Ollama + a model and the natural voice, tests your mic', {
    { 'RUN SETUP', function() SKIN:Bang('["' .. RES .. 'Jarvis\\Run-Setup.cmd"]'); SKIN:Bang('!DeactivateConfig') end },
    { 'FOLDER', function() SKIN:Bang('["' .. RES .. 'Jarvis"]') end } } }
  -- 7-A7: settings that only jarvis.py read until now (same jset writer)
  local air = H.str('JarvisAIRouter', '1') ~= '0'
  rows[#rows + 1] = { 'AI ROUTER', air and 'ON - the model decides what an unclear request means (the fixed commands still run first)' or 'OFF - only the fixed commands and plain chat', {
    { 'ON', function() jset('JarvisAIRouter', 1) end, air }, { 'OFF', function() jset('JarvisAIRouter', 0) end, not air } } }
  local fw = H.num('JarvisFirstWords', 5)
  rows[#rows + 1] = { 'FIRST WORDS', string.format('he starts speaking after %d words of the reply   - fewer = sooner, more = smoother', fw), {
    { '-', function() jbump('JarvisFirstWords', -1, 0, 12, 5) end }, { '+', function() jbump('JarvisFirstWords', 1, 0, 12, 5) end } } }
  local gpu = string.lower(H.str('JarvisGPU', 'prefer')) == 'require'
  rows[#rows + 1] = { 'GPU', gpu and 'REQUIRE - no turn runs on the CPU; he says so if the RTX is off' or 'PREFER - the GPU when it is on, else the CPU', {
    { 'PREFER', function() jset('JarvisGPU', 'prefer') end, not gpu }, { 'REQUIRE', function() jset('JarvisGPU', 'require') end, gpu } } }
  local iu = H.num('JarvisIdleUnload', 10)
  rows[#rows + 1] = { 'IDLE UNLOAD', (iu > 0 and string.format('speech models are freed after %d min without a turn', iu) or 'OFF - the speech models stay loaded') .. '   (they load again on the next turn)', {
    { '-', function() jbump('JarvisIdleUnload', -5, 0, 120, 10) end }, { '+', function() jbump('JarvisIdleUnload', 5, 0, 120, 10) end },
    { 'OFF', function() jset('JarvisIdleUnload', 0) end, iu <= 0 } } }
  local wh = H.num('JarvisWakeHard', 0.35)
  rows[#rows + 1] = { 'WAKE STRICT', string.format('%.2f   - the wake-word score needed while he talks or music plays; higher = fewer false wakes', wh), {
    { '-', function() jbump('JarvisWakeHard', -0.05, 0.1, 0.9, 0.35) end }, { '+', function() jbump('JarvisWakeHard', 0.05, 0.1, 0.9, 0.35) end } } }
  local lrn = string.lower(H.str('JarvisLearn', 'ask'))
  local lon = lrn ~= 'off' and lrn ~= '0'
  rows[#rows + 1] = { 'LEARN FACTS', lon and 'ASK - after a chat he may offer to remember a fact about you (never a number or a secret)' or 'OFF - he never offers', {
    { 'ASK', function() jset('JarvisLearn', 'ask') end, lon }, { 'OFF', function() jset('JarvisLearn', 'off') end, not lon } } }
  local rc = string.lower(H.str('JarvisRecall', 'on'))
  local ron = rc ~= 'off' and rc ~= '0'
  rows[#rows + 1] = { 'RECALL', ron and 'ON - remembered facts about a topic are given to the model' or 'OFF - the model sees no remembered facts', {
    { 'ON', function() jset('JarvisRecall', 'on') end, ron }, { 'OFF', function() jset('JarvisRecall', 'off') end, not ron } } }
  local na = H.str('JarvisNameAliases', '')
  rows[#rows + 1] = { 'NAME ALIASES', (na ~= '' and na or 'none') .. '   - other ways Whisper writes "Jarvis" (comma separated). Edit JarvisNameAliases in Settings.inc', {
    { 'EDIT', function() SKIN:Bang('["' .. RES .. 'Settings.inc"]'); say('EDIT JarvisNameAliases, THEN RELOAD') end } } }
  local bn = models('jarvis_bt.txt')
  rows[#rows + 1] = { 'BLUETOOTH NAMES', (#bn > 0 and ('Paired: ' .. table.concat(bn, ', ')) or 'No list yet - say "connect my headphones" once with Bluetooth on') ..
    '   - name them as <Bluetooth name>=<what you say>;... in JarvisBtNames (Settings.inc)', {
    { 'EDIT', function() SKIN:Bang('["' .. RES .. 'Settings.inc"]'); say('EDIT JarvisBtNames, THEN RELOAD') end } } }
  local facts = models('jarvis_memory.txt')
  rows[#rows + 1] = { 'REMEMBERED FACTS', #facts .. ' remembered   - what he knows about you; OPEN to read or edit, FORGET ALL asks first', {
    { 'OPEN', function() SKIN:Bang('["notepad.exe" "' .. RES .. 'Data\\jarvis_memory.txt"]') end },
    { armed == 'jfacts' and 'CONFIRM' or 'FORGET ALL', function()
        if arm('jfacts') then
          local o = io.open(RES .. 'Data\\jarvis_memory.txt', 'wb')
          if o then o:close(); say('ALL REMEMBERED FACTS FORGOTTEN') else say('COULD NOT CLEAR THE MEMORY FILE') end
        end
      end, armed == 'jfacts' } } }
  -- 7e: group the rows under three headings (a heading is a row with no buttons); rows are only moved, never dropped,
  -- and a row not named here lands in SETTINGS
  local SECTION = { PERSONALITY = 2, ['ABOUT ME'] = 2, ['CALL ME'] = 2, VOICE = 2, ['KOKORO VOICE'] = 2, ['TO-DO NOTE'] = 2, ['NOTES VAULT'] = 2,
    ['NOTE SEARCH'] = 2, ['COLOUR - STANDBY'] = 2, ['COLOUR - LISTENING'] = 2, ['COLOUR - SPEAKING'] = 2, ORB = 2, ['ORB TINT'] = 2,
    LAYERS = 2, MOTION = 2, ['MODEL MEMORY'] = 3, CONVERSATION = 3, ['LEARN FACTS'] = 3, RECALL = 3, ['REMEMBERED FACTS'] = 3 }
  local HEAD = { { 'JARVIS SETTINGS', 'Service, models, listening, wake word and microphone.' },
    { 'JARVIS PERSONALIZATION', 'How he talks to you and how the hologram looks.' },
    { 'JARVIS MEMORY', 'What he remembers; CLEAR empties this log, not his memory.' } }
  local out = {}
  for s = 1, 3 do
    out[#out + 1] = { HEAD[s][1], HEAD[s][2], {} }
    for _, r in ipairs(rows) do if (SECTION[r[1]] or 1) == s then out[#out + 1] = r end end
  end
  return out
end

local BUILD = { rowsModules, rowsLayout, rowsTheme, rowsApps, rowsSensors, rowsPerf, rowsSystem, rowsPresets, rowsData, rowsJarvis }

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
  -- subtitle right-aligned before the close button, so it can never run into the wide title
  H.text(1, 2, z.w - 66, 30, 'SPACESHIP HUD  /  ' .. H.str('DeviceName', ''), { size = 10, align = 'RightCenter', color = D, clip = z.w - 560 })
  c:line(22, 62, z.w - 22, 62, D, 1, 200)
  c:line(z.w - 44, 18, z.w - 24, 38, A1, 1.8); c:line(z.w - 24, 18, z.w - 44, 38, A1, 1.8)
  H.hit(1, 1, z.w - 52, 10, 36, 36, 'Close')
  actions[1] = function() SKIN:Bang('!DeactivateConfig'); flush() end   -- leave the group first, then reload it
  -- tabs
  for i, name in ipairs(TABS) do
    local y = TY + (i - 1) * (TH + 6)
    local on = i == tab
    c:fillRect(TX, y, TW, TH, on and A1 or H.C.panel, on and 50 or 120)
    if on then c:line(TX, y, TX, y + TH, A1, 3) end
    c:rect(TX, y, TW, TH, on and A1 or D, 1)
    -- tabs 9 and 10 use spare text slots (T1_11 is the footer) and tab 10 a spare hit (H1_11.. are the rows)
    H.text(1, i <= 8 and (2 + i) or (i == 9 and 108 or 109), TX + 16, y + TH / 2, name, { size = 11, font = H.fontText, weight = 700, align = 'LeftCenter', color = on and T or D })
    local hid = i <= 9 and (1 + i) or 75
    H.hit(1, hid, TX, y, TW, TH, name)
    local ti = i
    actions[hid] = function() tab = ti; page = 1 end
  end
  -- rows: label + buttons on the first line, the description below at full width (wrapped, never clipped);
  -- the list scrolls (mouse wheel anywhere on the panel) with a bar on the right
  local rows = BUILD[tab]()
  local maxFirst = math.max(1, #rows - NROWS + 1)
  scroll[tab] = H.clamp(scroll[tab] or 1, 1, maxFirst)
  local first = scroll[tab]
  barMax = maxFirst
  local DS = 9.5                                                -- description text size
  local cw = DS * (DS < 9.5 and H.textSmall or H.textLarge) * 96 / 72 * 0.7   -- one character (monospace), with margin
  local function wrap(text, width)
    local out, line = {}, ''
    for word in string.gmatch(text or '', '%S+') do
      while #word > width do
        if line ~= '' then out[#out + 1] = line; line = '' end
        out[#out + 1] = string.sub(word, 1, width); word = string.sub(word, width + 1)
      end
      if line == '' then line = word elseif #line + 1 + #word <= width then line = line .. ' ' .. word else out[#out + 1] = line; line = word end
    end
    if line ~= '' then out[#out + 1] = line end
    return out
  end
  for r = 1, NROWS do
    local row = rows[first + r - 1]
    local y = RY + (r - 1) * RH
    local tl, td1, td2 = 11 + (r - 1) * 3 + 1, 11 + (r - 1) * 3 + 2, 11 + (r - 1) * 3 + 3
    if row then
      c:hair(CX, y + RH - 4, CX + CW, y + RH - 4, D, 1, 60)
      if row[4] then
        local col = {}
        for v in string.gmatch(row[4], '%d+') do col[#col + 1] = tonumber(v) end
        c:fillRect(CX, y + 8, 22, 22, col, 255, 4)
      end
      local lx = row[4] and CX + 32 or CX + 8
      -- buttons sized to their labels (right-aligned), so no label is clipped
      local bws, total = {}, 0
      for b, btn in ipairs(row[3]) do bws[b] = math.max(BW, #btn[1] * 11.5 + 22); total = total + bws[b] + BG end
      local bx0 = CX + CW - total
      H.text(1, tl, lx, y + 6, row[1], { size = 10.5, font = H.fontText, weight = 700, color = T })
      local lines = wrap(row[2] or '', math.max(20, math.floor((CX + CW - lx - 4) / cw)))
      if #lines > 2 then lines[2] = string.sub(lines[2], 1, math.max(1, math.floor((CX + CW - lx - 4) / cw) - 3)) .. '...' end
      H.text(1, td1, lx, y + 37, lines[1] or '', { size = DS, color = D })
      if lines[2] then H.text(1, td2, lx, y + 60, lines[2], { size = DS, color = D }) else H.hideText(1, td2) end
      for b = 1, 4 do
        local hi = 10 + (r - 1) * 4 + b
        local tb = 43 + (r - 1) * 4 + b
        local btn = row[3][b]
        if btn then
          local bx = bx0
          for q = 1, b - 1 do bx = bx + bws[q] + BG end
          local bw = bws[b]
          c:fillRect(bx, y + 4, bw, 30, btn[3] and A1 or H.C.panel, btn[3] and 70 or 140)
          c:rect(bx, y + 4, bw, 30, btn[3] and A1 or D, 1.2)
          H.text(1, tb, bx + bw / 2, y + 19, btn[1], { size = 9.5, weight = 700, align = 'CenterCenter', color = btn[3] and T or A1 })
          H.hit(1, hi, bx, y + 4, bw, 30, btn[1])
          actions[hi] = btn[2]
        else
          H.hideText(1, tb); H.hideHit(1, hi)
        end
      end
    else
      H.hideText(1, tl); H.hideText(1, td1); H.hideText(1, td2)
      for b = 1, 4 do H.hideText(1, 43 + (r - 1) * 4 + b); H.hideHit(1, 10 + (r - 1) * 4 + b) end
    end
  end
  -- scroll bar
  if #rows > NROWS then
    local top, bot = RY, RY + NROWS * RH - 8
    local barH = math.max(30, (bot - top) * NROWS / #rows)
    local pos = (bot - top - barH) * (first - 1) / (maxFirst - 1)
    c:line(z.w - 16, top, z.w - 16, bot, D, 1, 120)
    c:line(z.w - 16, top + pos, z.w - 16, top + pos + barH, A1, 3, 230)
    local sh = (bot - top) / NSLICE
    for i = 1, NSLICE do H.hit(1, BARHIT + i - 1, z.w - 28, top + (i - 1) * sh, 24, sh, 'Scroll') end     -- click or drag the track to jump there
  else
    for i = 0, NSLICE - 1 do H.hideHit(1, BARHIT + i) end
  end
  for i = 11 + NROWS * 3 + 1, 43 do H.hideText(1, i) end
  for i = 43 + NROWS * 4 + 1, 107 do H.hideText(1, i) end
  for i = BARHIT + NSLICE, 74 do H.hideHit(1, i) end
  -- footer status
  c:line(22, z.h - 50, z.w - 22, z.h - 50, D, 1, 200)
  H.text(1, 11, 28, z.h - 30, msg .. (pending and '   -   RELOAD OR CLOSE TO APPLY' or ''), { size = 10, font = H.fontNum, align = 'LeftCenter', color = (pending or os.time() - msgAt < 6) and H.C.warn or D, clip = z.w - 200 })
  -- RELOAD: lit while saved settings wait for the HUD to reload (spare meters T1_110 / H1_76)
  local rx = z.w - 132
  c:fillRect(rx, z.h - 45, 110, 30, pending and A1 or H.C.panel, pending and 70 or 140)
  c:rect(rx, z.h - 45, 110, 30, pending and A1 or D, 1.2)
  H.text(1, 110, rx + 55, z.h - 30, 'RELOAD', { size = 9.5, weight = 700, align = 'CenterCenter', color = pending and T or A1 })
  H.hit(1, 76, rx, z.h - 45, 110, 30, 'Reload the HUD')
  actions[76] = function() if not flush() then say('NOTHING TO APPLY') end end
  c:flush()
  return 0
end

function OnClick(zi, k)
  dragging = false                -- mouse-up on any hit (incl. a bar slice) ends a scroll-bar drag
  local fn = actions[k]
  if fn then fn() end
  saveView()                      -- for tab / page / module changes; the view before the click is already saved
  Update()
end
function OnRightClick(zi, k) end
function OnScroll(zi, k, d)
  scroll[tab] = (scroll[tab] or 1) + d      -- one row per wheel notch
  Update()
end
-- scroll bar: f = 0..1 down the track; OnBarDown(slice, p = 0..100 down that slice)
-- shortcut: drag = mouse-down plus hover over 16 track slices, so it steps in 1/16 jumps and ends if the pointer leaves the window; upgrade if a finer or captured drag is needed
local function barTo(f)
  local r = math.floor(1 + f * (barMax - 1) + 0.5)
  if r ~= scroll[tab] then scroll[tab] = r; Update() end
end
function OnBarDown(i, p)
  dragging = true
  barTo(((tonumber(i) or 1) - 1 + (tonumber(p) or 0) / 100) / NSLICE)
end
function EndDrag() dragging = false end
-- InputText (mInput) answer for the CALL ME row: keep it safe for one Settings.inc line
function SetCallMe(v)
  v = string.gsub(tostring(v or SKIN:GetVariable('CallMeIn', '')), "[%c=;%[%]#\"'%%]", '')
  v = string.sub(string.match(v, '^%s*(.-)%s*$'), 1, 30)
  jset('JarvisCallMe', v)
  Update()
end
-- InputText (mAsk) answer for the TYPE TO HIM row: one line, at most 500 characters; the service checks it again
function AskJarvis(v)
  v = string.gsub(tostring(v or SKIN:GetVariable('AskIn', '')), '%c', ' ')
  v = string.sub(string.match(v, '^%s*(.-)%s*$'), 1, 500)
  if v ~= '' then H.cmd('ASK ' .. os.time() .. ' ' .. v) end
end
function OnHover(zi, k, on)
  if dragging and on == 1 and k >= BARHIT and k < BARHIT + NSLICE then barTo((k - BARHIT + 0.5) / NSLICE) end
end
